"""Unit tests for resilience: configurable transport retry, the chat
client-side model-fallback chain, and observability events (retry /
fallback / gateway-routing) via logger + debug.

Mirrors the Node SDK's tests/resilience.test.ts behavioural contract.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Union

import httpx
import pytest

from meshapi import (
    AsyncMeshAPI,
    ChatCompletionParams,
    ChatMessage,
    FallbackConfig,
    FallbackEvent,
    GatewayRoutingEvent,
    MeshAPI,
    MeshAPIError,
    RetryEvent,
    RetryPolicy,
    format_resilience_event,
)
from meshapi._resilience import resolve_retry_policy

# ── Helpers ───────────────────────────────────────────────────────────────────

OK_CHAT_BODY: Dict[str, Any] = {
    "id": "chatcmpl-1",
    "object": "chat.completion",
    "created": 0,
    "model": "openai/gpt-4o-mini",
    "choices": [
        {
            "index": 0,
            "message": {"role": "assistant", "content": "hi"},
            "finish_reason": "stop",
        }
    ],
    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
}


def ok_response(headers: Optional[Dict[str, str]] = None) -> httpx.Response:
    return httpx.Response(200, json=OK_CHAT_BODY, headers=headers or {})


def error_response(
    status: int, code: str = "provider_not_available", request_id: str = "req_err"
) -> httpx.Response:
    return httpx.Response(
        status,
        json={"error": {"code": code, "message": "boom"}, "request_id": request_id},
    )


class FetchQueue:
    """A transport handler fed by a queue of responses / exceptions; records
    request bodies so tests can assert what went over the wire."""

    def __init__(self, items: List[Union[httpx.Response, Exception]]) -> None:
        self.items = list(items)
        self.calls: List[Dict[str, Any]] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode()) if request.content else None
        self.calls.append({"url": str(request.url), "body": body})
        if not self.items:
            raise AssertionError("fetch queue exhausted")
        nxt = self.items.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        return nxt


# Zero-backoff default so tests never sleep.
ZERO_BACKOFF = dict(backoff_base_ms=0, backoff_max_ms=0)


def make_client(
    queue: List[Union[httpx.Response, Exception]], **config: Any
) -> "tuple[MeshAPI, List[Dict[str, Any]], list]":
    q = FetchQueue(queue)
    events: list = []
    config.setdefault("retry", RetryPolicy(max_retries=2, **ZERO_BACKOFF))
    client = MeshAPI(
        base_url="https://gw.test",
        token="rsk_test",
        httpx_client=httpx.Client(
            transport=httpx.MockTransport(q.handler), base_url="https://gw.test"
        ),
        logger=events.append,
        **config,
    )
    return client, q.calls, events


def make_async_client(
    queue: List[Union[httpx.Response, Exception]], **config: Any
) -> "tuple[AsyncMeshAPI, List[Dict[str, Any]], list]":
    q = FetchQueue(queue)
    events: list = []
    config.setdefault("retry", RetryPolicy(max_retries=2, **ZERO_BACKOFF))
    client = AsyncMeshAPI(
        base_url="https://gw.test",
        token="rsk_test",
        async_httpx_client=httpx.AsyncClient(
            transport=httpx.MockTransport(q.handler), base_url="https://gw.test"
        ),
        logger=events.append,
        **config,
    )
    return client, q.calls, events


def chat_params() -> ChatCompletionParams:
    return ChatCompletionParams(
        model="openai/gpt-4o-mini",
        messages=[ChatMessage(role="user", content="hello")],
    )


def retries(events: list) -> List[RetryEvent]:
    return [e for e in events if isinstance(e, RetryEvent)]


def fallbacks(events: list) -> List[FallbackEvent]:
    return [e for e in events if isinstance(e, FallbackEvent)]


def gateway_routings(events: list) -> List[GatewayRoutingEvent]:
    return [e for e in events if isinstance(e, GatewayRoutingEvent)]


# ── resolve_retry_policy ──────────────────────────────────────────────────────


def test_resolve_retry_policy_defaults() -> None:
    p = resolve_retry_policy(None, None)
    assert p.max_retries == 3
    assert p.retry_on_status == frozenset({429, 502, 503, 504})
    assert p.backoff_base_ms == 500
    assert p.backoff_max_ms == 30_000
    assert p.respect_retry_after is True
    assert p.retry_on_network_error is False


def test_retry_max_retries_wins_over_deprecated_alias() -> None:
    assert resolve_retry_policy(RetryPolicy(max_retries=5), 1).max_retries == 5
    assert resolve_retry_policy(None, 1).max_retries == 1


# ── Transport retry ───────────────────────────────────────────────────────────


def test_retries_503_then_succeeds_emitting_retry_event() -> None:
    client, calls, events = make_client([error_response(503), ok_response()])

    res = client.chat.completions.create(chat_params())

    assert res.choices[0].message.content == "hi"
    assert len(calls) == 2
    rs = retries(events)
    assert len(rs) == 1
    assert rs[0].status == 503
    assert rs[0].attempt == 1
    assert rs[0].reason == "status"
    assert rs[0].request_id is None  # no x-request-id header on the mock


async def test_async_retries_503_then_succeeds_emitting_retry_event() -> None:
    client, calls, events = make_async_client([error_response(503), ok_response()])

    res = await client.chat.completions.create(chat_params())

    assert res.choices[0].message.content == "hi"
    assert len(calls) == 2
    rs = retries(events)
    assert len(rs) == 1
    assert rs[0].status == 503
    assert rs[0].reason == "status"


def test_honours_custom_retry_on_status_set() -> None:
    # 500 is not retryable by default; opt in explicitly.
    client, calls, _ = make_client(
        [error_response(500), ok_response()],
        retry=RetryPolicy(max_retries=2, retry_on_status=[500], **ZERO_BACKOFF),
    )

    client.chat.completions.create(chat_params())
    assert len(calls) == 2


def test_gives_up_after_max_retries_and_raises_api_error() -> None:
    client, calls, events = make_client(
        [error_response(503), error_response(503), error_response(503)]
    )

    with pytest.raises(MeshAPIError) as exc_info:
        client.chat.completions.create(chat_params())

    assert exc_info.value.status == 503
    assert len(calls) == 3  # 1 initial + 2 retries
    assert len(retries(events)) == 2


def test_does_not_retry_network_errors_by_default() -> None:
    client, calls, _ = make_client([httpx.ConnectError("fetch failed")])

    with pytest.raises(httpx.ConnectError, match="fetch failed"):
        client.chat.completions.create(chat_params())
    assert len(calls) == 1


def test_retries_network_errors_when_opted_in() -> None:
    client, calls, events = make_client(
        [httpx.ConnectError("fetch failed"), ok_response()],
        retry=RetryPolicy(max_retries=2, retry_on_network_error=True, **ZERO_BACKOFF),
    )

    client.chat.completions.create(chat_params())
    assert len(calls) == 2
    rs = retries(events)
    assert len(rs) == 1
    assert rs[0].reason == "network-error"
    assert rs[0].status is None


async def test_async_retries_network_errors_when_opted_in() -> None:
    client, calls, events = make_async_client(
        [httpx.ConnectError("fetch failed"), ok_response()],
        retry=RetryPolicy(max_retries=2, retry_on_network_error=True, **ZERO_BACKOFF),
    )

    await client.chat.completions.create(chat_params())
    assert len(calls) == 2
    assert retries(events)[0].reason == "network-error"


def test_never_retries_a_timeout() -> None:
    client, calls, _ = make_client(
        [httpx.ReadTimeout("timed out")],
        retry=RetryPolicy(max_retries=3, retry_on_network_error=True, **ZERO_BACKOFF),
    )

    with pytest.raises(httpx.ReadTimeout, match="timed out"):
        client.chat.completions.create(chat_params())
    assert len(calls) == 1


# ── Chat model-fallback chain ─────────────────────────────────────────────────


def test_advances_to_next_model_after_retries_exhaust() -> None:
    client, calls, events = make_client(
        [
            error_response(503),  # primary attempt 1
            error_response(503),  # primary retry 1
            ok_response(),  # fallback model
        ],
        retry=RetryPolicy(max_retries=1, **ZERO_BACKOFF),
        fallback=FallbackConfig(models=["anthropic/claude-sonnet-5"]),
    )

    res = client.chat.completions.create(chat_params())

    assert res.choices[0].message.content == "hi"
    assert len(calls) == 3
    assert calls[2]["body"]["model"] == "anthropic/claude-sonnet-5"
    fbs = fallbacks(events)
    assert len(fbs) == 1
    assert fbs[0].from_model == "openai/gpt-4o-mini"
    assert fbs[0].to_model == "anthropic/claude-sonnet-5"
    assert fbs[0].status == 503
    assert fbs[0].chain_index == 0
    assert fbs[0].chain_length == 1


async def test_async_advances_to_next_model_after_retries_exhaust() -> None:
    client, calls, events = make_async_client(
        [error_response(503), error_response(503), ok_response()],
        retry=RetryPolicy(max_retries=1, **ZERO_BACKOFF),
        fallback=FallbackConfig(models=["anthropic/claude-sonnet-5"]),
    )

    res = await client.chat.completions.create(chat_params())

    assert res.choices[0].message.content == "hi"
    assert len(calls) == 3
    assert calls[2]["body"]["model"] == "anthropic/claude-sonnet-5"
    fbs = fallbacks(events)
    assert len(fbs) == 1
    assert fbs[0].to_model == "anthropic/claude-sonnet-5"


def test_per_call_fallback_models_overrides_config_and_never_hits_the_wire() -> None:
    client, calls, _ = make_client(
        [error_response(502), ok_response()],
        retry=RetryPolicy(max_retries=0, **ZERO_BACKOFF),
        fallback=FallbackConfig(models=["ignored/config-model"]),
    )

    client.chat.completions.create(
        chat_params(), fallback_models=["mistral/mistral-large"]
    )

    assert calls[1]["body"]["model"] == "mistral/mistral-large"
    for call in calls:
        assert "fallback_models" not in call["body"], "fallback_models leaked to the wire"
        assert "fallbackModels" not in call["body"], "fallbackModels leaked to the wire"


def test_terminal_errors_never_advance_the_chain() -> None:
    client, calls, events = make_client(
        [error_response(401, "unauthorized")],
        retry=RetryPolicy(max_retries=0, **ZERO_BACKOFF),
        fallback=FallbackConfig(models=["anthropic/claude-sonnet-5"]),
    )

    with pytest.raises(MeshAPIError) as exc_info:
        client.chat.completions.create(chat_params())

    assert exc_info.value.status == 401
    assert len(calls) == 1
    assert fallbacks(events) == []


def test_exhausting_the_whole_chain_raises_the_last_error() -> None:
    client, calls, _ = make_client(
        [
            error_response(503),
            error_response(503),
            error_response(504, "gateway_timeout", "req_last"),
        ],
        retry=RetryPolicy(max_retries=0, **ZERO_BACKOFF),
        fallback=FallbackConfig(models=["m/a", "m/b"]),
    )

    with pytest.raises(MeshAPIError) as exc_info:
        client.chat.completions.create(chat_params())

    assert exc_info.value.status == 504
    assert exc_info.value.request_id == "req_last"
    assert len(calls) == 3


def test_skips_the_primary_model_when_it_also_appears_in_the_chain() -> None:
    client, calls, _ = make_client(
        [error_response(503), ok_response()],
        retry=RetryPolicy(max_retries=0, **ZERO_BACKOFF),
        fallback=FallbackConfig(models=["openai/gpt-4o-mini", "m/b"]),
    )

    client.chat.completions.create(chat_params())
    assert len(calls) == 2
    assert calls[1]["body"]["model"] == "m/b"


def test_custom_fallback_on_status_controls_eligibility() -> None:
    # 429 not in the default fallback set — opt in.
    client, calls, _ = make_client(
        [error_response(429, "rate_limit_exceeded"), ok_response()],
        retry=RetryPolicy(max_retries=0, **ZERO_BACKOFF),
        fallback=FallbackConfig(models=["m/b"], on_status=[429]),
    )

    client.chat.completions.create(chat_params())
    assert len(calls) == 2


# ── Gateway routing observability ─────────────────────────────────────────────


def test_parses_x_mesh_routing_headers_into_gateway_routing_event() -> None:
    client, _, events = make_client(
        [
            ok_response(
                headers={
                    "x-mesh-routing-attempts": "2",
                    "x-mesh-routing-fallback": "true",
                    "x-mesh-served-provider": "bedrock",
                    "x-request-id": "req_routed",
                }
            )
        ]
    )

    client.chat.completions.create(chat_params())

    gws = gateway_routings(events)
    assert len(gws) == 1
    assert gws[0].attempts == 2
    assert gws[0].fallback is True
    assert gws[0].served_provider == "bedrock"
    assert gws[0].request_id == "req_routed"


def test_emits_nothing_when_routing_headers_are_absent() -> None:
    client, _, events = make_client([ok_response()])
    client.chat.completions.create(chat_params())
    assert gateway_routings(events) == []


# ── Debug formatting ──────────────────────────────────────────────────────────


def test_format_retry_line() -> None:
    line = format_resilience_event(
        RetryEvent(
            method="POST",
            path="/v1/chat/completions",
            attempt=1,
            max_retries=3,
            status=503,
            request_id="req_1",
            delay_ms=512.4,
            reason="status",
        )
    )
    assert line == (
        "retrying POST /v1/chat/completions (attempt 1/4 failed: 503, next in 512ms) [req_1]"
    )


def test_format_fallback_line() -> None:
    line = format_resilience_event(
        FallbackEvent(
            from_model="openai/gpt-4o",
            to_model="anthropic/claude-sonnet-5",
            chain_index=0,
            chain_length=2,
            status=503,
            error_code="provider_not_available",
        )
    )
    assert line == (
        "falling back openai/gpt-4o → anthropic/claude-sonnet-5 (1/2: 503 provider_not_available)"
    )


def test_format_gateway_routing_line() -> None:
    line = format_resilience_event(
        GatewayRoutingEvent(
            path="/v1/chat/completions",
            attempts=2,
            fallback=True,
            served_provider="bedrock",
            request_id="req_2",
        )
    )
    assert line == (
        "gateway served /v1/chat/completions via bedrock (2 attempts, provider fallback) [req_2]"
    )
