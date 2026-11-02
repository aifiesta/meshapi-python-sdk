"""Contract checks for the fields added in API spec v1.0.374.

All fields in this release are additive and optional. These tests check that
each field is declared on its model, is not required, and parses and
serialises under its wire name.
"""

from __future__ import annotations

import pytest

from meshapi import _types

NEW_FIELDS = {
    "ChatPromptTokensDetails": ["cache_write_12h_tokens"],
    "ModelPricing": [
        "cache_write_12h_input_usd_per_1m",
        "flex_cache_write_12h_input_usd_per_1m",
        "flex_long_context_cache_write_12h_input_usd_per_1m",
        "long_context_cache_write_12h_input_usd_per_1m",
    ],
    "SpeechRequest": ["emotion", "vol"],
}


def _model(name: str):
    model = getattr(_types, name, None)
    if model is None:
        pytest.fail(f"meshapi._types.{name} is missing")
    return model


@pytest.mark.parametrize(
    "model_name,field",
    [(m, f) for m, fields in NEW_FIELDS.items() for f in fields],
)
def test_new_field_is_declared_and_optional(model_name: str, field: str) -> None:
    model = _model(model_name)
    assert field in model.model_fields, f"{model_name}.{field} is not declared"
    assert not model.model_fields[field].is_required()


def test_prompt_tokens_details_parses_cache_write_12h_tokens() -> None:
    model = _model("ChatPromptTokensDetails")
    parsed = model.model_validate({"cached_tokens": 0, "cache_write_12h_tokens": 512})
    assert parsed.cache_write_12h_tokens == 512


def test_prompt_tokens_details_defaults_cache_write_12h_tokens_to_none() -> None:
    model = _model("ChatPromptTokensDetails")
    parsed = model.model_validate({"cached_tokens": 0})
    assert parsed.cache_write_12h_tokens is None


def test_model_pricing_carries_12h_cache_write_rates() -> None:
    model = _model("ModelPricing")
    values = {
        "cache_write_12h_input_usd_per_1m": 2.5,
        "flex_cache_write_12h_input_usd_per_1m": 1.25,
        "flex_long_context_cache_write_12h_input_usd_per_1m": 2.5,
        "long_context_cache_write_12h_input_usd_per_1m": 5.0,
    }
    pricing = model.model_construct(**values)
    dumped = pricing.model_dump(exclude_none=True, by_alias=True)
    for key, value in values.items():
        assert dumped[key] == value


def test_speech_request_serialises_vol_and_emotion() -> None:
    model = _model("SpeechRequest")
    req = model.model_construct(vol=2.0, emotion="happy")
    dumped = req.model_dump(exclude_none=True, by_alias=True)
    assert dumped["vol"] == 2.0
    assert dumped["emotion"] == "happy"


def test_speech_request_omits_vol_and_emotion_when_unset() -> None:
    model = _model("SpeechRequest")
    req = model.model_construct()
    dumped = req.model_dump(exclude_none=True, by_alias=True)
    assert "vol" not in dumped
    assert "emotion" not in dumped
