"""Unit tests for the per-request `timeout` field.

Verifies:
- ChatCompletionParams serialises `timeout` into the JSON body sent to the backend.
- ResponsesParams does the same.
- When `timeout` is omitted the key is absent from the serialised body (no noise).
- The SSE parser raises MeshAPIError with error_code="gateway_timeout" when the
  server emits the gateway_timeout error frame (the scenario the customer hit).
- The SSE parser preserves partial content before the timeout error frame.
"""

import json

import pytest

from meshapi._errors import MeshAPIError
from meshapi._http import _try_parse_sse_frame, _iter_sse
from meshapi._types import ChatCompletionParams, ResponsesParams


# ── ChatCompletionParams serialisation ────────────────────────────────────────


def test_chat_timeout_serialised_into_body():
    params = ChatCompletionParams(
        messages=[{"role": "user", "content": "hi"}],
        model="openai/gpt-4o-mini",
        timeout=600.0,
    )
    body = params.model_dump(exclude_none=True)
    assert body["timeout"] == 600.0


def test_chat_timeout_absent_when_not_set():
    params = ChatCompletionParams(
        messages=[{"role": "user", "content": "hi"}],
        model="openai/gpt-4o-mini",
    )
    body = params.model_dump(exclude_none=True)
    assert "timeout" not in body


def test_chat_timeout_rejected_when_zero_or_negative():
    with pytest.raises(Exception):
        ChatCompletionParams(
            messages=[{"role": "user", "content": "hi"}],
            timeout=0.0,
        )
    with pytest.raises(Exception):
        ChatCompletionParams(
            messages=[{"role": "user", "content": "hi"}],
            timeout=-1.0,
        )


# ── ResponsesParams serialisation ─────────────────────────────────────────────


def test_responses_timeout_serialised_into_body():
    params = ResponsesParams(input="hello", timeout=900.0)
    body = params.model_dump(exclude_none=True)
    assert body["timeout"] == 900.0


def test_responses_timeout_absent_when_not_set():
    params = ResponsesParams(input="hello")
    body = params.model_dump(exclude_none=True)
    assert "timeout" not in body


# ── SSE parser: gateway_timeout error frame ───────────────────────────────────


def _make_sse_frame(payload: dict) -> bytes:
    return f"data: {json.dumps(payload)}\n\n".encode()


def _make_done_frame() -> bytes:
    return b"data: [DONE]\n\n"


def _make_chunk(content: str) -> dict:
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion.chunk",
        "created": 1712345678,
        "model": "openai/gpt-4o-mini",
        "choices": [{"index": 0, "delta": {"content": content}, "finish_reason": None}],
    }


def test_parse_gateway_timeout_frame_raises():
    """The backend emits this frame when the upstream provider takes > 300 s."""
    error_payload = {
        "error": {"code": "gateway_timeout", "message": "Upstream provider did not respond in time."}
    }
    frame = f"data: {json.dumps(error_payload)}"
    with pytest.raises(MeshAPIError) as exc_info:
        _try_parse_sse_frame(frame)
    err = exc_info.value
    assert err.error_code == "gateway_timeout"
    assert "respond in time" in str(err)


def test_iter_sse_gateway_timeout_after_partial_content():
    """Partial tokens arrive, then the server emits a gateway_timeout error frame.

    The customer scenario: request runs >5 min, the stream is mid-flight
    when the backend times out. The SDK must raise MeshAPIError, not silently end.
    """
    chunk1 = _make_chunk("Hello ")
    chunk2 = _make_chunk("world")
    error_payload = {
        "error": {
            "code": "gateway_timeout",
            "message": "Upstream provider did not respond in time.",
        }
    }
    raw = (
        _make_sse_frame(chunk1)
        + _make_sse_frame(chunk2)
        + _make_sse_frame(error_payload)
        + _make_done_frame()
    )

    from unittest.mock import MagicMock

    mock_resp = MagicMock()
    mock_resp.iter_bytes.return_value = iter([raw])

    gen = _iter_sse(mock_resp)
    first = next(gen)
    assert first.choices[0].delta.content == "Hello "

    second = next(gen)
    assert second.choices[0].delta.content == "world"

    with pytest.raises(MeshAPIError) as exc_info:
        next(gen)
    err = exc_info.value
    assert err.error_code == "gateway_timeout"


def test_iter_sse_gateway_timeout_no_prior_content():
    """Timeout fires before any content is streamed (e.g. slow upstream start)."""
    error_payload = {
        "error": {
            "code": "gateway_timeout",
            "message": "Upstream provider did not respond in time.",
        }
    }
    raw = _make_sse_frame(error_payload) + _make_done_frame()

    from unittest.mock import MagicMock

    mock_resp = MagicMock()
    mock_resp.iter_bytes.return_value = iter([raw])

    gen = _iter_sse(mock_resp)
    with pytest.raises(MeshAPIError) as exc_info:
        next(gen)
    assert exc_info.value.error_code == "gateway_timeout"
