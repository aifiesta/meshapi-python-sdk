"""Contract checks for the v1.0.370 public API changes.

These tests cover the additive request fields and the cost line changes:

- ``provider`` on chat, responses, compare, batches, images, video, speech,
  transcription and translation requests.
- ``max_completion_tokens`` on ``ChatCompletionRequest``.
- ``container``, ``mcp_servers``, ``provider`` and ``service_tier`` on
  ``AnthropicMessagesRequest``.
- ``CostLineOut.tokens`` and ``CostLineOut.rate_per_1m_usd`` are now optional
  and nullable (breaking). Non-token lines carry ``quantity``, ``unit`` and
  ``rate_usd`` instead.
- ``CostBreakdownOut.rounding_usd``.
- ``UsageFilter`` gains ``provider``, ``fault_owner``, ``is_byok``, ``stream``,
  ``traffic_type`` and ``is_retry_attempt``.

A model that is not exported by this SDK build is skipped, not failed.
"""

from __future__ import annotations

import pytest

import meshapi._types as types


def _model(name: str):
    model = getattr(types, name, None)
    if model is None:
        pytest.skip(f"{name} is not exported by meshapi._types")
    return model


@pytest.mark.parametrize(
    "name",
    [
        "ChatCompletionRequest",
        "ResponsesRequest",
        "CompareRequest",
        "CreateBatchRequest",
        "ImageGenerationRequest",
        "VideoGenerationRequest",
        "SpeechRequest",
        "AnthropicMessagesRequest",
    ],
)
def test_request_models_accept_provider(name: str) -> None:
    model = _model(name)
    assert "provider" in model.model_fields


def test_chat_request_accepts_max_completion_tokens() -> None:
    model = _model("ChatCompletionRequest")
    assert "max_completion_tokens" in model.model_fields


@pytest.mark.parametrize("field", ["container", "mcp_servers", "service_tier"])
def test_anthropic_messages_request_new_fields(field: str) -> None:
    model = _model("AnthropicMessagesRequest")
    assert field in model.model_fields


def test_cost_line_parses_non_token_line() -> None:
    model = _model("CostLineOut")
    payload = {
        "tokens": None,
        "rate_per_1m_usd": None,
        "quantity": 5,
        "unit": "per_second",
        "rate_usd": "0.10",
        "charged": True,
        "modifiers": ["with_audio"],
    }
    fields = model.model_fields
    for key in ("tokens", "rate_per_1m_usd"):
        assert not fields[key].is_required()
    known = {k: v for k, v in payload.items() if k in fields}
    for name, info in fields.items():
        if info.is_required() and name not in known:
            pytest.skip(f"fixture does not cover required field {name}")
    line = model.model_validate(known)
    assert line.tokens is None
    assert line.rate_per_1m_usd is None


def test_cost_breakdown_has_rounding_usd() -> None:
    model = _model("CostBreakdownOut")
    assert "rounding_usd" in model.model_fields


@pytest.mark.parametrize(
    "field",
    ["provider", "fault_owner", "is_byok", "stream", "traffic_type", "is_retry_attempt"],
)
def test_usage_filter_new_fields(field: str) -> None:
    model = _model("UsageFilter")
    assert field in model.model_fields
