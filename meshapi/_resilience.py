"""Resilience: retry policy, fallback chain, and observability events.

Two independent layers, mirroring the gateway's design:

 1. TRANSPORT RETRY (SyncHttpClient / AsyncHttpClient): re-send the same
    request on transient failures (429/502/503/504, optionally network
    errors). Configured via ``MeshAPIConfig.retry``. Streaming requests are
    never retried.

 2. MODEL FALLBACK (chat.completions.create): after the transport gives up,
    try the same request against the next model in a configured chain.
    Configured via ``MeshAPIConfig.fallback`` or the per-call
    ``fallback_models`` argument. Client-side only — the gateway additionally
    does its own server-side retry + cross-provider fallback when the API
    key's ``routing_policy`` enables it; that outcome is reported back via
    ``X-Mesh-Routing-*`` response headers and surfaced as a
    ``gateway-routing`` event.

Every retry, fallback hop, and gateway-routing outcome is observable through
``MeshAPIConfig.logger`` (structured events) and/or ``debug=True`` (readable
stderr lines), so it is always clear which requests were retried and which
were served by a fallback.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, FrozenSet, List, Literal, Optional, Sequence, Tuple, Union

DEFAULT_RETRY_STATUS_CODES: Tuple[int, ...] = (429, 502, 503, 504)
DEFAULT_FALLBACK_STATUS_CODES: Tuple[int, ...] = (502, 503, 504)


@dataclass
class RetryPolicy:
    """Transport-level retry policy. Unset fields keep the defaults."""

    #: Maximum number of retries after the initial attempt.
    max_retries: int = 3

    #: HTTP status codes that trigger a retry of the same request.
    retry_on_status: Sequence[int] = DEFAULT_RETRY_STATUS_CODES

    #: Base delay for exponential backoff (doubles per attempt, ±20% jitter).
    backoff_base_ms: float = 500

    #: Upper bound on a single backoff delay.
    backoff_max_ms: float = 30_000

    #: Honour the server's ``Retry-After`` response header when present.
    respect_retry_after: bool = True

    #: Also retry when the request fails before any response arrives (DNS
    #: failure, connection refused/reset). Off by default: a network error is
    #: ambiguous — the request may have reached the server, and POST bodies
    #: are not idempotent. Timeouts/cancellation are never retried.
    retry_on_network_error: bool = False


@dataclass
class ResolvedRetryPolicy:
    """Retry policy with every field populated and the status set frozen."""

    max_retries: int
    retry_on_status: FrozenSet[int]
    backoff_base_ms: float
    backoff_max_ms: float
    respect_retry_after: bool
    retry_on_network_error: bool


def resolve_retry_policy(
    policy: Optional[RetryPolicy],
    legacy_max_retries: Optional[int],
) -> ResolvedRetryPolicy:
    """Resolve the effective transport retry policy.

    ``retry.max_retries`` wins over the deprecated top-level ``max_retries``:
    when a ``RetryPolicy`` is supplied it is used as-is (its own defaults
    included); the legacy alias only applies when no policy is configured.
    """
    if policy is not None:
        return ResolvedRetryPolicy(
            max_retries=policy.max_retries,
            retry_on_status=frozenset(policy.retry_on_status),
            backoff_base_ms=policy.backoff_base_ms,
            backoff_max_ms=policy.backoff_max_ms,
            respect_retry_after=policy.respect_retry_after,
            retry_on_network_error=policy.retry_on_network_error,
        )
    return ResolvedRetryPolicy(
        max_retries=legacy_max_retries if legacy_max_retries is not None else 3,
        retry_on_status=frozenset(DEFAULT_RETRY_STATUS_CODES),
        backoff_base_ms=500,
        backoff_max_ms=30_000,
        respect_retry_after=True,
        retry_on_network_error=False,
    )


@dataclass
class FallbackConfig:
    """Client-side model-fallback chain for ``chat.completions.create``
    (non-streaming).
    """

    #: Ordered list of models to try when the primary model's request fails.
    #: Distinct from the ``models`` request param (a server-side,
    #: provider-handled fallback list): this chain is driven by the SDK, so it
    #: works regardless of provider and is visible in your logs hop by hop.
    models: List[str] = field(default_factory=list)

    #: Error statuses eligible for advancing to the next model. Terminal
    #: errors (auth, validation, billing) never advance the chain.
    on_status: Sequence[int] = DEFAULT_FALLBACK_STATUS_CODES


# ── Observability events ──────────────────────────────────────────────────────


@dataclass
class RetryEvent:
    """The same request is being re-sent after a transient failure."""

    method: str
    path: str
    #: 1-based attempt that just failed; the next send is ``attempt + 1``.
    attempt: int
    max_retries: int
    delay_ms: float
    reason: Literal["status", "network-error"]
    #: HTTP status that triggered the retry; ``None`` for a network error.
    status: Optional[int] = None
    #: Gateway request id of the failed attempt, when a response was received.
    request_id: Optional[str] = None
    type: Literal["retry"] = field(default="retry", init=False)


@dataclass
class FallbackEvent:
    """The chat fallback chain is advancing to the next model."""

    from_model: str
    to_model: str
    #: 0-based index of ``to_model`` within the configured chain.
    chain_index: int
    chain_length: int
    status: Optional[int] = None
    error_code: Optional[str] = None
    request_id: Optional[str] = None
    type: Literal["fallback"] = field(default="fallback", init=False)


@dataclass
class GatewayRoutingEvent:
    """The GATEWAY retried or fell back server-side while serving this
    request — parsed from the ``X-Mesh-Routing-*`` response headers (present
    when the API key's ``routing_policy`` is active). ``fallback=True`` means
    a different provider than the primary served the request.
    """

    path: str
    attempts: int
    fallback: bool
    served_provider: Optional[str] = None
    request_id: Optional[str] = None
    type: Literal["gateway-routing"] = field(default="gateway-routing", init=False)


ResilienceEvent = Union[RetryEvent, FallbackEvent, GatewayRoutingEvent]

#: Structured event sink. Receives every retry, fallback hop, and
#: gateway-routing outcome.
ResilienceLogger = Callable[[ResilienceEvent], None]


# ── Built-in debug printer ────────────────────────────────────────────────────


def format_resilience_event(event: ResilienceEvent) -> str:
    """Render an event as a single readable line, e.g.

    ``retrying POST /v1/chat/completions (attempt 1/3 failed: 503, next in 512ms) [req_abc]``
    ``falling back openai/gpt-4o → anthropic/claude-sonnet-5 (1/2: 503 provider_not_available)``
    ``gateway served /v1/chat/completions via bedrock (2 attempts, provider fallback) [req_abc]``
    """
    rid = f" [{event.request_id}]" if event.request_id else ""
    if isinstance(event, RetryEvent):
        why = "network error" if event.reason == "network-error" else str(event.status)
        # Match JS Math.round (half-up) so debug lines are identical across SDKs.
        delay = math.floor(event.delay_ms + 0.5)
        return (
            f"retrying {event.method} {event.path} "
            f"(attempt {event.attempt}/{event.max_retries + 1} failed: {why}, "
            f"next in {delay}ms){rid}"
        )
    if isinstance(event, FallbackEvent):
        why = " ".join(str(part) for part in (event.status, event.error_code) if part)
        return (
            f"falling back {event.from_model} → {event.to_model} "
            f"({event.chain_index + 1}/{event.chain_length}: {why or 'network error'}){rid}"
        )
    served = f" via {event.served_provider}" if event.served_provider else ""
    detail = (
        f"{event.attempts} attempts, provider fallback"
        if event.fallback
        else f"{event.attempts} attempts"
    )
    return f"gateway served {event.path}{served} ({detail}){rid}"
