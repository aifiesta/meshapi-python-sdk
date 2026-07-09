"""Live tests: resilience (retry / fallback / observability).

Mirrors the Node SDK's livetests/test-resilience.js scenarios.
"""

from __future__ import annotations

import pytest
from config import BASE_URL, TOKEN
from meshapi import (
    ChatCompletionParams,
    ChatMessage,
    FallbackConfig,
    FallbackEvent,
    GatewayRoutingEvent,
    MeshAPI,
    RetryEvent,
    RetryPolicy,
)


def test_healthy_call_with_logger_no_spurious_events(model: str) -> None:
    """Successful call with a logger attached — no spurious events;
    gateway-routing only from headers."""
    events: list = []
    client = MeshAPI(base_url=BASE_URL, token=TOKEN, logger=events.append)

    resp = client.chat.completions.create(
        ChatCompletionParams(
            model=model,
            messages=[ChatMessage(role="user", content="Reply with the word: ok")],
            max_tokens=10,
        )
    )

    assert resp.choices[0].message
    # No client-side retry/fallback should have happened on a healthy call.
    assert [e for e in events if isinstance(e, RetryEvent)] == []
    assert [e for e in events if isinstance(e, FallbackEvent)] == []
    # gateway-routing appears IFF the key has an active routing_policy; when
    # it does, the shape must be sane.
    for e in events:
        if isinstance(e, GatewayRoutingEvent):
            assert e.attempts >= 1
            assert isinstance(e.fallback, bool)


def test_per_call_fallback_models_is_client_side_only(
    client: MeshAPI, model: str, second_model: str
) -> None:
    """Per-call fallback_models is client-side only — the server still serves
    the primary."""
    resp = client.chat.completions.create(
        ChatCompletionParams(
            model=model,
            messages=[ChatMessage(role="user", content="Reply with the word: ok")],
            max_tokens=10,
        ),
        fallback_models=[second_model],
    )
    # The request validated server-side (fallback_models was stripped) and the
    # primary model answered.
    assert resp.model, "expected a model on the response"
    assert resp.choices[0].message


def test_unreachable_gateway_retry_events_and_chain(model: str, second_model: str) -> None:
    """Unreachable gateway: retry events fire, the chain advances, and the
    last error propagates."""
    events: list = []
    client = MeshAPI(
        # A privileged, never-bound localhost port — connect fails instantly with
        # ECONNREFUSED (a network error, NOT a timeout), which is what we want to
        # exercise: retryable + fallback-eligible. TEST-NET-1 (192.0.2.x) is unroutable
        # but on networks that silently drop its packets the connect would instead time
        # out, and timeouts are deliberately never retried — making this test flaky.
        base_url="http://127.0.0.1:1",
        token=TOKEN,
        timeout=2.0,
        retry=RetryPolicy(
            max_retries=1,
            backoff_base_ms=10,
            backoff_max_ms=20,
            retry_on_network_error=True,
        ),
        fallback=FallbackConfig(models=[second_model]),
        logger=events.append,
    )

    with pytest.raises(Exception):
        client.chat.completions.create(
            ChatCompletionParams(
                model=model,
                messages=[ChatMessage(role="user", content="hello")],
            )
        )

    # Each model attempt retried once on the network error…
    network_retries = [
        e for e in events if isinstance(e, RetryEvent) and e.reason == "network-error"
    ]
    assert network_retries, f"expected network-error retry events, got: {events!r}"
    # …and the chain advanced to the fallback model before giving up.
    fb = next((e for e in events if isinstance(e, FallbackEvent)), None)
    assert fb is not None, "expected a fallback event"
    assert fb.from_model == model
    assert fb.to_model == second_model
