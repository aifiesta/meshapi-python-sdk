"""Contract tests for ``ModelPricing.long_context_cache_write_1h_input_usd_per_1m``.

``GET /v1/models`` publishes the long-context rate for a 1-hour cache write.
The field is additive and nullable: a pricing row without it parses as before.
"""

from __future__ import annotations

from meshapi._types import ModelPricing

FIELD = "long_context_cache_write_1h_input_usd_per_1m"


def test_field_is_declared_and_optional() -> None:
    field = ModelPricing.model_fields.get(FIELD)
    assert field is not None
    assert not field.is_required()
    assert field.default is None


def test_field_parses_a_rate() -> None:
    pricing = ModelPricing.__pydantic_validator__.validate_assignment(
        ModelPricing.model_construct(), FIELD, 1.0
    )
    assert getattr(pricing, FIELD) == 1.0


def test_field_accepts_null() -> None:
    pricing = ModelPricing.__pydantic_validator__.validate_assignment(
        ModelPricing.model_construct(), FIELD, None
    )
    assert getattr(pricing, FIELD) is None


def test_field_round_trips_through_dump() -> None:
    pricing = ModelPricing.__pydantic_validator__.validate_assignment(
        ModelPricing.model_construct(), FIELD, 0.625
    )
    assert pricing.model_dump(include={FIELD}) == {FIELD: 0.625}
