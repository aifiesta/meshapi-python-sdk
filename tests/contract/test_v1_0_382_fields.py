"""Contract tests for fields added in API spec v1.0.382.

- ``ModelPricing.long_context_cache_write_1h_input_usd_per_1m``: the price of a
  1-hour cache write on a prompt past the model's long-context threshold, in USD
  per 1M tokens. ``None`` when the model publishes no such price.
- ``RouterSelectRequest.weight_profile``: the Auto Router weight profile to apply
  to a ``POST /v1/router/select`` call (for example ``"balanced"`` or
  ``"cost_first"``). Omit it to use the key, template or org default.

Both fields are optional and additive, so payloads without them must still parse.
"""

from __future__ import annotations

import pytest

import meshapi._types as types


def _model(name: str):
    cls = getattr(types, name, None)
    if cls is None:
        pytest.skip(f"{name} is not modelled in this SDK build")
    return cls


# ---------------------------------------------------------------------------
# ModelPricing.long_context_cache_write_1h_input_usd_per_1m
# ---------------------------------------------------------------------------


def test_model_pricing_declares_long_context_cache_write_1h_field():
    ModelPricing = _model("ModelPricing")
    assert "long_context_cache_write_1h_input_usd_per_1m" in ModelPricing.model_fields


def test_model_pricing_parses_long_context_cache_write_1h_price():
    ModelPricing = _model("ModelPricing")
    pricing = ModelPricing.model_validate(
        {"long_context_cache_write_1h_input_usd_per_1m": 1.0}
    )
    assert pricing.long_context_cache_write_1h_input_usd_per_1m == 1.0


def test_model_pricing_accepts_null_long_context_cache_write_1h_price():
    ModelPricing = _model("ModelPricing")
    pricing = ModelPricing.model_validate(
        {"long_context_cache_write_1h_input_usd_per_1m": None}
    )
    assert pricing.long_context_cache_write_1h_input_usd_per_1m is None


def test_model_pricing_defaults_long_context_cache_write_1h_price_to_none():
    ModelPricing = _model("ModelPricing")
    pricing = ModelPricing.model_validate({})
    assert pricing.long_context_cache_write_1h_input_usd_per_1m is None


# ---------------------------------------------------------------------------
# RouterSelectRequest.weight_profile
# ---------------------------------------------------------------------------


def test_router_select_request_declares_weight_profile_field():
    RouterSelectRequest = _model("RouterSelectRequest")
    assert "weight_profile" in RouterSelectRequest.model_fields


def test_router_select_request_serialises_weight_profile():
    RouterSelectRequest = _model("RouterSelectRequest")
    field = RouterSelectRequest.model_fields["weight_profile"]
    assert not field.is_required()
    required = {
        name: f for name, f in RouterSelectRequest.model_fields.items() if f.is_required()
    }
    if required:
        pytest.skip("RouterSelectRequest has other required fields; covered by unit tests")
    req = RouterSelectRequest(weight_profile="cost_first")
    dumped = req.model_dump(exclude_none=True)
    assert dumped["weight_profile"] == "cost_first"


def test_router_select_request_omits_unset_weight_profile():
    RouterSelectRequest = _model("RouterSelectRequest")
    required = [
        name for name, f in RouterSelectRequest.model_fields.items() if f.is_required()
    ]
    if required:
        pytest.skip("RouterSelectRequest has other required fields; covered by unit tests")
    req = RouterSelectRequest()
    assert "weight_profile" not in req.model_dump(exclude_none=True)
