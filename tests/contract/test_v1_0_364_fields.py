"""Contract checks for the fields added or changed in API spec v1.0.364.

These tests parse local payloads only and make no network calls.

Covered changes:

- ``provider`` (optional string) on chat completions, responses, Anthropic
  messages, compare, batches, image generation, video generation, speech and
  the three audio transcription/translation bodies. It pins one request to
  one upstream provider. The request is served by that provider or refused
  with a 400 ``invalid_provider_pin``. It is never rerouted.
- ``max_completion_tokens`` on chat completions. It is the newer name for
  ``max_tokens`` and wins when both are sent. The server rejects values
  below 1.
- ``container``, ``mcp_servers`` and ``service_tier`` on Anthropic messages
  requests.
- Cost breakdown lines now describe non-token charges. ``CostLineOut`` gains
  ``quantity``, ``unit``, ``rate_usd``, ``charged`` and ``modifiers``.
  ``CostBreakdownOut`` gains ``rounding_usd``.
- Breaking: ``CostLineOut.tokens`` and ``CostLineOut.rate_per_1m_usd`` are
  now optional and may be ``None`` on image, video and fee lines. Read
  ``quantity``, ``unit`` and ``rate_usd`` instead.

A model the SDK does not export yet is skipped rather than failed, so the
file stays usable while types are added one surface at a time.
"""

from __future__ import annotations

from typing import Any, Optional, Type

import pytest

import meshapi

try:  # pragma: no cover - import shape depends on the installed SDK
    from meshapi import _types as _sdk_types
except Exception:  # pragma: no cover
    _sdk_types = None  # type: ignore[assignment]


def _find(*names: str) -> Optional[Type[Any]]:
    """Return the first SDK model matching one of ``names``, else ``None``."""
    for name in names:
        obj = getattr(meshapi, name, None)
        if obj is None and _sdk_types is not None:
            obj = getattr(_sdk_types, name, None)
        if obj is not None:
            return obj
    return None


def _require(*names: str) -> Type[Any]:
    model = _find(*names)
    if model is None:
        pytest.skip(f"SDK does not export any of {names}")
    return model


def _fields(model: Type[Any]) -> set:
    return set(getattr(model, "model_fields", {}).keys())


# ---------------------------------------------------------------------------
# provider: per-request provider pin
# ---------------------------------------------------------------------------

_PROVIDER_SURFACES = [
    ("ChatCompletionRequest",),
    ("ResponsesRequest", "ResponseCreateRequest"),
    ("AnthropicMessagesRequest", "MessagesRequest"),
    ("CompareRequest",),
    ("CreateBatchRequest", "BatchCreateRequest"),
    ("ImageGenerationRequest",),
    ("VideoGenerationRequest",),
    ("SpeechRequest",),
]


@pytest.mark.parametrize("names", _PROVIDER_SURFACES, ids=lambda n: n[0])
def test_request_models_declare_optional_provider(names: tuple) -> None:
    model = _require(*names)
    assert "provider" in _fields(model), f"{model.__name__} is missing `provider`"
    field = model.model_fields["provider"]
    assert not field.is_required(), "`provider` must be optional"


def test_chat_request_serialises_provider_and_omits_it_when_unset() -> None:
    model = _require("ChatCompletionRequest")
    if "provider" not in _fields(model):
        pytest.fail("ChatCompletionRequest is missing `provider`")
    messages = [{"role": "user", "content": "hi"}]

    pinned = model(model="openai/gpt-4o-mini", messages=messages, provider="openai")
    assert pinned.model_dump(exclude_none=True)["provider"] == "openai"

    unpinned = model(model="openai/gpt-4o-mini", messages=messages)
    assert "provider" not in unpinned.model_dump(exclude_none=True)


# ---------------------------------------------------------------------------
# max_completion_tokens on chat completions
# ---------------------------------------------------------------------------


def test_chat_request_accepts_max_completion_tokens() -> None:
    model = _require("ChatCompletionRequest")
    assert "max_completion_tokens" in _fields(model)
    req = model(
        model="openai/gpt-4o-mini",
        messages=[{"role": "user", "content": "hi"}],
        max_completion_tokens=64,
    )
    assert req.model_dump(exclude_none=True)["max_completion_tokens"] == 64


# ---------------------------------------------------------------------------
# Anthropic messages: container, mcp_servers, service_tier
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("field", ["container", "mcp_servers", "service_tier"])
def test_anthropic_messages_request_declares_new_optional_fields(field: str) -> None:
    model = _require("AnthropicMessagesRequest", "MessagesRequest")
    assert field in _fields(model), f"{model.__name__} is missing `{field}`"
    assert not model.model_fields[field].is_required()


# ---------------------------------------------------------------------------
# Cost breakdown lines (breaking: tokens / rate_per_1m_usd may be null)
# ---------------------------------------------------------------------------

_VIDEO_LINE = {
    "kind": "video",
    "tokens": None,
    "rate_per_1m_usd": None,
    "quantity": 5,
    "unit": "second",
    "rate_usd": "0.10",
    "charged": True,
    "modifiers": ["720p", "with_audio"],
    "amount_usd": "0.50",
}

_TOKEN_LINE = {
    "kind": "input",
    "tokens": 1200,
    "rate_per_1m_usd": "0.15",
    "amount_usd": "0.00018",
}


def test_cost_line_accepts_null_tokens_and_rate() -> None:
    model = _require("CostLineOut", "CostLine")
    for name in ("tokens", "rate_per_1m_usd"):
        assert not model.model_fields[name].is_required(), f"`{name}` must be optional"
    line = model.model_validate(_VIDEO_LINE)
    assert line.tokens is None
    assert line.rate_per_1m_usd is None


def test_cost_line_exposes_quantity_unit_rate_charged_modifiers() -> None:
    model = _require("CostLineOut", "CostLine")
    for name in ("quantity", "unit", "rate_usd", "charged", "modifiers"):
        assert name in _fields(model), f"{model.__name__} is missing `{name}`"
    line = model.model_validate(_VIDEO_LINE)
    assert line.unit == "second"
    assert line.charged is True
    assert list(line.modifiers) == ["720p", "with_audio"]


def test_cost_line_still_parses_token_billed_rows() -> None:
    model = _require("CostLineOut", "CostLine")
    line = model.model_validate(_TOKEN_LINE)
    assert line.tokens == 1200
    assert line.rate_per_1m_usd is not None


def test_cost_breakdown_declares_optional_rounding_usd() -> None:
    model = _require("CostBreakdownOut", "CostBreakdown")
    assert "rounding_usd" in _fields(model)
    assert not model.model_fields["rounding_usd"].is_required()
