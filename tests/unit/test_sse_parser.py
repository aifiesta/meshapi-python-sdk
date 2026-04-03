"""Unit tests for the SSE parser.

Tests verify:
- Correct chunk parsing from well-formed frames
- Remainder-buffer handling across TCP-fragmented input
- [DONE] sentinel terminates iteration
- Mid-stream error frames raise MeshAPIError
"""

import json
from typing import List
from unittest.mock import MagicMock, patch

import pytest

from meshapi._errors import MeshAPIError
from meshapi._http import _try_parse_sse_frame, _iter_sse
from meshapi._types import ChatCompletionChunk


def make_chunk(content: str, index: int = 0) -> dict:
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion.chunk",
        "created": 1712345678,
        "model": "openai/gpt-4o-mini",
        "choices": [{"index": index, "delta": {"content": content}, "finish_reason": None}],
    }


def make_sse_frame(payload: dict) -> bytes:
    return f"data: {json.dumps(payload)}\n\n".encode()


def make_done_frame() -> bytes:
    return b"data: [DONE]\n\n"


# ---------------------------------------------------------------------------
# _try_parse_sse_frame
# ---------------------------------------------------------------------------


def test_parse_valid_chunk():
    chunk_dict = make_chunk("Hello")
    frame = f"data: {json.dumps(chunk_dict)}"
    result = _try_parse_sse_frame(frame)
    assert result is not None
    assert isinstance(result, ChatCompletionChunk)
    assert result.choices[0].delta is not None
    assert result.choices[0].delta.content == "Hello"


def test_parse_done_frame_returns_sentinel():
    from meshapi._http import _DONE_SENTINEL
    assert _try_parse_sse_frame("data: [DONE]") is _DONE_SENTINEL


def test_parse_empty_frame_returns_none():
    assert _try_parse_sse_frame("") is None
    assert _try_parse_sse_frame("   ") is None


def test_parse_invalid_json_returns_none():
    assert _try_parse_sse_frame("data: {not valid json}") is None


def test_parse_error_frame_raises():
    error_payload = {"error": {"code": "upstream_error", "message": "Provider failed"}}
    frame = f"data: {json.dumps(error_payload)}"
    with pytest.raises(MeshAPIError) as exc_info:
        _try_parse_sse_frame(frame)
    err = exc_info.value
    assert err.error_code == "upstream_error"
    assert "Provider failed" in str(err)


# ---------------------------------------------------------------------------
# _iter_sse (integration of the full iterator with mock response)
# ---------------------------------------------------------------------------


def build_mock_response(byte_chunks: List[bytes]):
    """Build a mock httpx Response whose iter_bytes() yields the given chunks."""
    mock_resp = MagicMock()
    mock_resp.iter_bytes.return_value = iter(byte_chunks)
    return mock_resp


def test_iter_sse_single_frame():
    chunk = make_chunk("Hi")
    raw = make_sse_frame(chunk)
    mock_resp = build_mock_response([raw])
    result = list(_iter_sse(mock_resp))
    assert len(result) == 1
    assert result[0].choices[0].delta.content == "Hi"


def test_iter_sse_multiple_frames():
    chunks = [make_chunk(c) for c in ["A", " ", "B"]]
    raw = b"".join(make_sse_frame(c) for c in chunks) + make_done_frame()
    mock_resp = build_mock_response([raw])
    result = list(_iter_sse(mock_resp))
    assert len(result) == 3
    contents = [r.choices[0].delta.content for r in result]
    assert contents == ["A", " ", "B"]


def test_iter_sse_done_terminates():
    """[DONE] must stop iteration; frames after it must not be yielded."""
    chunk = make_chunk("Hello")
    raw = make_sse_frame(chunk) + make_done_frame() + make_sse_frame(make_chunk("NEVER"))
    mock_resp = build_mock_response([raw])
    result = list(_iter_sse(mock_resp))
    # Only the frame before [DONE] should be emitted
    assert len(result) == 1
    assert result[0].choices[0].delta.content == "Hello"


def test_iter_sse_tcp_fragmented():
    """Simulate a SSE frame split across two TCP packets."""
    chunk = make_chunk("Fragmented")
    full_frame = make_sse_frame(chunk)
    mid = len(full_frame) // 2
    part1 = full_frame[:mid]
    part2 = full_frame[mid:] + make_done_frame()
    mock_resp = build_mock_response([part1, part2])
    result = list(_iter_sse(mock_resp))
    assert len(result) == 1
    assert result[0].choices[0].delta.content == "Fragmented"


def test_iter_sse_mid_stream_error():
    """An error frame in the middle of a stream raises MeshAPIError."""
    chunk1 = make_chunk("Part 1")
    error_payload = {"error": {"code": "upstream_error", "message": "Server died"}}
    raw = make_sse_frame(chunk1) + make_sse_frame(error_payload)
    mock_resp = build_mock_response([raw])

    gen = _iter_sse(mock_resp)
    first = next(gen)
    assert first.choices[0].delta.content == "Part 1"

    with pytest.raises(MeshAPIError) as exc_info:
        next(gen)
    assert exc_info.value.error_code == "upstream_error"


def test_iter_sse_chunked_across_multiple_packets():
    """Three separate SSE frames each delivered as individual byte packets."""
    chunks = [make_chunk(c) for c in ["X", "Y", "Z"]]
    packets = [make_sse_frame(c) for c in chunks]
    packets.append(make_done_frame())
    mock_resp = build_mock_response(packets)
    result = list(_iter_sse(mock_resp))
    assert [r.choices[0].delta.content for r in result] == ["X", "Y", "Z"]
