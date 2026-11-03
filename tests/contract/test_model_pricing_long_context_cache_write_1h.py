"""Contract tests for ``ModelPricing.long_context_cache_write_1h_input_usd_per_1m``.

``GET /v1/models`` publishes the long-context 1-hour cache-write rate in USD
per million input tokens. The field is additive and nullable: a pricing row
without it must still parse, and the value must read as ``None``.
"""

from __future__ import annotations

from meshapi import ModelPricing

FIELD = "long_context_cache_write_1h_input_usd_per_1m"


def test_field_is_declared() -> None:
    assert FIELD in ModelPricing.model_fields


def test_parses_when_present() -> None:
    pricing = ModelPricing.model_validate({FIELD: 1.0})
    assert pricing.long_context_cache_write_1h_input_usd_per_1m == 1.0


def test_parses_when_null() -> None:
    pricing = ModelPricing.model_validate({FIELD: None})
    assert pricing.long_context_cache_write_1h_input_usd_per_1m is None


def test_defaults_to_none_when_absent() -> None:
    pricing = ModelPricing.model_validate({})
    assert pricing.long_context_cache_write_1h_input_usd_per_1m is None


def test_round_trips_through_dump() -> None:
    pricing = ModelPricing.model_validate({FIELD: 0.625})
    assert pricing.model_dump(exclude_none=True)[FIELD] == 0.625
