"""Unit tests for request-id support (set + read).

Verifies:
- The per-call ``request_id`` option is sent as the ``X-Request-Id`` header
  (plain JSON, streaming/SSE, and multipart paths).
- An invalid ``request_id`` raises ValueError before any request is made.
- ``response._request_id`` is populated from the ``x-request-id`` response
  header on success (sync + async).
- ``model_dump()`` / ``model_dump_json()`` never include ``_request_id``.
"""

from __future__ import annotations

import json
from typing import List

import httpx
import pytest

from meshapi import AsyncMeshAPI, ChatCompletionParams, ChatMessage, MeshAPI
from meshapi._http import validate_request_id
from meshapi._types import ChatCompletionResponse

SERVER_REQUEST_ID = "req_01JZZZZZZZZZZZZZZZZZZZZZZZ"

CHAT_COMPLETION_BODY = {
    "id": "chatcmpl-1",
    "object": "chat.completion",
    "created": 1712345678,
    "model": "openai/gpt-4o-mini",
    "choices": [
        {
            "index": 0,
            "message": {"role": "assistant", "content": "Paris"},
            "finish_reason": "stop",
        }
    ],
}

CHAT_PARAMS = ChatCompletionParams(
    model="openai/gpt-4o-mini",
    messages=[ChatMessage(role="user", content="hi")],
)


def _make_sync_client(handler) -> MeshAPI:
    transport = httpx.MockTransport(handler)
    httpx_client = httpx.Client(transport=transport, base_url="http://testserver")
    return MeshAPI(base_url="http://testserver", token="rsk_test", httpx_client=httpx_client)


def _make_async_client(handler) -> AsyncMeshAPI:
    transport = httpx.MockTransport(handler)
    httpx_client = httpx.AsyncClient(transport=transport, base_url="http://testserver")
    return AsyncMeshAPI(
        base_url="http://testserver", token="rsk_test", async_httpx_client=httpx_client
    )


def _json_response(request: httpx.Request, body: dict) -> httpx.Response:
    return httpx.Response(
        200, json=body, headers={"X-Request-Id": SERVER_REQUEST_ID}, request=request
    )


# ── request_id option sends the X-Request-Id header ──────────────────────────


def test_request_id_option_sends_header_sync():
    seen_headers: List[httpx.Headers] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.append(request.headers)
        return _json_response(request, CHAT_COMPLETION_BODY)

    client = _make_sync_client(handler)
    client.chat.completions.create(CHAT_PARAMS, request_id="my-trace-id.1")
    assert len(seen_headers) == 1
    assert seen_headers[0]["x-request-id"] == "my-trace-id.1"


def test_no_request_id_option_sends_no_header():
    seen_headers: List[httpx.Headers] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.append(request.headers)
        return _json_response(request, CHAT_COMPLETION_BODY)

    client = _make_sync_client(handler)
    client.chat.completions.create(CHAT_PARAMS)
    assert "x-request-id" not in seen_headers[0]


async def test_request_id_option_sends_header_async():
    seen_headers: List[httpx.Headers] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.append(request.headers)
        return _json_response(request, CHAT_COMPLETION_BODY)

    client = _make_async_client(handler)
    await client.chat.completions.create(CHAT_PARAMS, request_id="async-trace:42")
    assert seen_headers[0]["x-request-id"] == "async-trace:42"


def test_request_id_option_sends_header_streaming():
    seen_headers: List[httpx.Headers] = []
    sse = (
        "data: "
        + json.dumps(
            {
                "id": "chatcmpl-1",
                "object": "chat.completion.chunk",
                "created": 1712345678,
                "model": "openai/gpt-4o-mini",
                "choices": [{"index": 0, "delta": {"content": "hi"}, "finish_reason": None}],
            }
        )
        + "\n\ndata: [DONE]\n\n"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.append(request.headers)
        return httpx.Response(
            200,
            content=sse.encode(),
            headers={"Content-Type": "text/event-stream", "X-Request-Id": SERVER_REQUEST_ID},
            request=request,
        )

    client = _make_sync_client(handler)
    chunks = list(client.chat.completions.stream(CHAT_PARAMS, request_id="stream-id-7"))
    assert len(chunks) == 1
    assert seen_headers[0]["x-request-id"] == "stream-id-7"


def test_request_id_option_sends_header_multipart():
    from meshapi._types import TranscriptionParams

    seen_headers: List[httpx.Headers] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.append(request.headers)
        return _json_response(request, {"text": "hello"})

    client = _make_sync_client(handler)
    result = client.audio.transcribe(
        b"fake-bytes",
        TranscriptionParams(model="openai/whisper-1"),
        request_id="upload-id-9",
    )
    assert seen_headers[0]["x-request-id"] == "upload-id-9"
    assert result._request_id == SERVER_REQUEST_ID


# ── invalid request_id raises ValueError before any request ──────────────────


@pytest.mark.parametrize(
    "bad_request_id",
    ["", "a" * 65, "has space", "emoji-❤", "new\nline", "slash/x", "q?y"],
)
def test_invalid_request_id_raises_value_error(bad_request_id):
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("no request should be made for an invalid request_id")

    client = _make_sync_client(handler)
    with pytest.raises(ValueError, match="request_id"):
        client.chat.completions.create(CHAT_PARAMS, request_id=bad_request_id)


def test_invalid_request_id_raises_before_stream_iteration():
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("no request should be made for an invalid request_id")

    client = _make_sync_client(handler)
    # Must raise at call time, NOT on first next() — no generator is returned.
    with pytest.raises(ValueError, match="request_id"):
        client.chat.completions.stream(CHAT_PARAMS, request_id="bad id")


async def test_invalid_request_id_raises_value_error_async():
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("no request should be made for an invalid request_id")

    client = _make_async_client(handler)
    with pytest.raises(ValueError, match="request_id"):
        await client.chat.completions.create(CHAT_PARAMS, request_id="bad id")
    # Async streaming also validates eagerly, before iteration.
    with pytest.raises(ValueError, match="request_id"):
        client.chat.completions.stream(CHAT_PARAMS, request_id="bad id")


def test_validate_request_id_accepts_full_charset():
    assert validate_request_id("aA0._:-") == "aA0._:-"
    assert validate_request_id("x" * 64) == "x" * 64


# ── _request_id populated from the response header ───────────────────────────


def test_response_request_id_populated_sync():
    def handler(request: httpx.Request) -> httpx.Response:
        return _json_response(request, CHAT_COMPLETION_BODY)

    client = _make_sync_client(handler)
    resp = client.chat.completions.create(CHAT_PARAMS)
    assert resp._request_id == SERVER_REQUEST_ID


async def test_response_request_id_populated_async():
    def handler(request: httpx.Request) -> httpx.Response:
        return _json_response(request, CHAT_COMPLETION_BODY)

    client = _make_async_client(handler)
    resp = await client.chat.completions.create(CHAT_PARAMS)
    assert resp._request_id == SERVER_REQUEST_ID


def test_response_request_id_populated_on_list_items():
    """Top-level list endpoints (e.g. models.list) expose it per item."""

    def handler(request: httpx.Request) -> httpx.Response:
        return _json_response(
            request,
            # ModelInfo requires only a handful of fields; extra="ignore".
            [{"id": "openai/gpt-4o-mini", "name": "gpt-4o-mini", "is_free": False}],
        )

    # httpx.Response(json=...) requires dict/list — list works fine.
    client = _make_sync_client(handler)
    models = client.models.list()
    assert models[0]._request_id == SERVER_REQUEST_ID


def test_response_request_id_defaults_to_none():
    """A model parsed outside the HTTP layer must default to None, not raise."""
    resp = ChatCompletionResponse.model_validate(CHAT_COMPLETION_BODY)
    assert resp._request_id is None


def test_response_request_id_none_when_header_missing():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=CHAT_COMPLETION_BODY, request=request)

    client = _make_sync_client(handler)
    resp = client.chat.completions.create(CHAT_PARAMS)
    assert resp._request_id is None


# ── serialisation round-trips are unaffected ─────────────────────────────────


def test_model_dump_excludes_request_id():
    def handler(request: httpx.Request) -> httpx.Response:
        return _json_response(request, CHAT_COMPLETION_BODY)

    client = _make_sync_client(handler)
    resp = client.chat.completions.create(CHAT_PARAMS)
    assert resp._request_id == SERVER_REQUEST_ID

    dumped = resp.model_dump()
    assert "_request_id" not in dumped
    assert "request_id" not in dumped
    assert "_request_id" not in resp.model_dump_json()

    # And the round-trip re-validates cleanly.
    revalidated = ChatCompletionResponse.model_validate(dumped)
    assert revalidated.id == resp.id
    assert revalidated._request_id is None
