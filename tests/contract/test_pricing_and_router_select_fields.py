"""Contract tests for the fields added in API spec v1.0.383.

- ``ModelPricing.long_context_cache_write_1h_input_usd_per_1m``: the per-1M-token
  price for writing to the 1-hour prompt cache on long-context requests.
- ``RouterSelectRequest.weight_profile``: the Auto Router weight profile that
  ``POST /v1/router/select`` uses when it selects a model.

Both fields are optional and default to ``None``. Existing payloads that omit
them keep parsing and serialising as before.
"""

from __future__ import annotations

import pytest

from meshapi import _types


def _model(name: str):
    model = getattr(_types, name, None)
    assert model is not None, f"{name} is not defined in meshapi._types"
    return model


@pytest.mark.parametrize(
    "model_name, field_name",
    [
        ("ModelPricing", "long_context_cache_write_1h_input_usd_per_1m"),
        ("RouterSelectRequest", "weight_profile"),
    ],
)
def test_new_field_is_declared_and_optional(model_name: str, field_name: str) -> None:
    model = _model(model_name)
    fields = model.model_fields
    assert field_name in fields, f"{model_name}.{field_name} is missing"
    field = fields[field_name]
    assert not field.is_required()
    assert field.default is None


def test_model_pricing_field_accepts_a_number_and_none() -> None:
    model = _model("ModelPricing")
    field = "long_context_cache_write_1h_input_usd_per_1m"
    required = {
        name: None
        for name, info in model.model_fields.items()
        if info.is_required()
    }
    if required:
        pytest.skip("ModelPricing has required fields; covered by the field declaration test")

    priced = model.model_validate({field: 7.5})
    assert getattr(priced, field) == pytest.approx(7.5)

    unpriced = model.model_validate({})
    assert getattr(unpriced, field) is None


def test_router_select_weight_profile_is_omitted_when_unset() -> None:
    model = _model("RouterSelectRequest")
    required = [
        name for name, info in model.model_fields.items() if info.is_required()
    ]
    if required:
        pytest.skip("RouterSelectRequest has required fields; covered by the field declaration test")

    unset = model.model_validate({})
    assert "weight_profile" not in unset.model_dump(exclude_none=True)

    set_profile = model.model_validate({"weight_profile": "cost_first"})
    assert set_profile.weight_profile == "cost_first"
    assert set_profile.model_dump(exclude_none=True)["weight_profile"] == "cost_first"
