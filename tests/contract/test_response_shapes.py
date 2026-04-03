"""Contract tests — verify SDK types parse all documented API response shapes.

These tests use golden JSON fixtures (recorded from the real API) and verify
that the SDK's Pydantic models accept them without errors. No live server needed.

If a fixture fails to parse, the API contract has drifted from the SDK types.
"""

import json
from pathlib import Path

import pytest

from meshapi._types import (
    ChatCompletionChunk,
    ChatCompletionResponse,
    ModelInfo,
    TemplateSummary,
)
from meshapi._errors import MeshAPIError

FIXTURES = Path(__file__).parent.parent / "fixtures"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


# ---------------------------------------------------------------------------
# Chat completion response shapes
# ---------------------------------------------------------------------------


def test_chat_completion_response():
    data = load("chat_completion_response.json")
    resp = ChatCompletionResponse.model_validate(data)
    assert resp.id == "chatcmpl-abc123"
    assert resp.model == "openai/gpt-4o-mini"
    assert len(resp.choices) == 1
    choice = resp.choices[0]
    assert choice.message is not None
    assert choice.message.role == "assistant"
    assert choice.message.content == "2 + 2 equals 4."
    assert choice.finish_reason == "stop"
    assert resp.usage is not None
    assert resp.usage.total_tokens == 21


def test_chat_completion_chunk():
    data = load("chat_completion_chunk.json")
    chunk = ChatCompletionChunk.model_validate(data)
    assert chunk.id == "chatcmpl-abc123"
    assert len(chunk.choices) == 1
    assert chunk.choices[0].delta is not None
    assert chunk.choices[0].delta.content == "Hello"
    assert chunk.choices[0].delta.role == "assistant"
    assert chunk.choices[0].finish_reason is None


def test_chat_completion_chunk_usage():
    """Final usage chunk has empty choices[] and a usage field."""
    data = load("chat_completion_chunk_usage.json")
    chunk = ChatCompletionChunk.model_validate(data)
    assert chunk.choices == []
    assert chunk.usage is not None
    assert chunk.usage.prompt_tokens == 14
    assert chunk.cost == "0.0000021"


def test_null_optional_fields_are_handled():
    """system_fingerprint=null should not raise."""
    data = load("chat_completion_response.json")
    assert data.get("system_fingerprint") is None
    resp = ChatCompletionResponse.model_validate(data)
    assert resp.system_fingerprint is None


# ---------------------------------------------------------------------------
# Model shapes
# ---------------------------------------------------------------------------


def test_model_list():
    data = load("model_list.json")
    models = [ModelInfo.model_validate(m) for m in data]
    assert len(models) == 2
    paid = next(m for m in models if not m.is_free)
    free = next(m for m in models if m.is_free)
    assert paid.id == "openai/gpt-4o-mini"
    assert paid.pricing is not None
    assert paid.pricing.prompt_usd_per_1k == "0.000150"
    assert free.pricing is not None
    assert free.pricing.prompt_usd_per_1k == "0"
    assert free.description is None


# ---------------------------------------------------------------------------
# Template shapes
# ---------------------------------------------------------------------------


def test_template_summary():
    data = load("template_summary.json")
    tmpl = TemplateSummary.model_validate(data)
    assert tmpl.id == "550e8400-e29b-41d4-a716-446655440000"
    assert tmpl.name == "pirate-assistant"
    assert tmpl.system == "You are a helpful assistant who speaks like a pirate."
    assert tmpl.variables == ["topic"]
    assert tmpl.created_at == "2024-04-01T12:00:00Z"


def test_template_list():
    data = load("template_list.json")
    templates = [TemplateSummary.model_validate(t) for t in data]
    assert len(templates) == 1
    assert templates[0].messages is None
    assert templates[0].params is None


# ---------------------------------------------------------------------------
# Error envelope shapes
# ---------------------------------------------------------------------------


def test_error_401_parses():
    data = load("error_401.json")
    err_body = data["error"]
    assert err_body["code"] == "unauthorized"
    assert data["request_id"] == "req_01HZXYZ"


def test_error_422_has_details():
    data = load("error_422.json")
    details = data["error"].get("details", [])
    assert len(details) == 1
    assert details[0]["type"] == "missing"


def test_error_429_has_retry_after():
    data = load("error_429.json")
    assert data["error"]["retry_after_seconds"] == 5


def test_all_error_codes_map_to_meshapi_api_error():
    """MeshAPIError.from_response handles every documented error code."""
    from unittest.mock import MagicMock

    codes = [
        ("error_401.json", 401),
        ("error_422.json", 422),
        ("error_429.json", 429),
    ]
    for fname, status in codes:
        data = load(fname)
        mock = MagicMock()
        mock.status_code = status
        mock.headers = {"content-type": "application/json", "x-request-id": ""}
        mock.json.return_value = data
        mock.text = json.dumps(data)
        err = MeshAPIError.from_response(mock)
        assert isinstance(err, MeshAPIError)
        assert err.status == status
        assert err.error_code == data["error"]["code"]
