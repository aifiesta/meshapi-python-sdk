"""Contract tests for ``ModelPricing.long_context_cache_write_1h_input_usd_per_1m``.

``GET /v1/models`` publishes the 1-hour cache-write input price that applies
once a prompt crosses the model's long-context threshold. The field is
additive: a pricing row without it must still parse, and the value reads
back as ``None``.
"""

from meshapi._types import ModelPricing


def test_parses_long_context_cache_write_1h_price() -> None:
    pricing = ModelPricing.model_validate(
        {"long_context_cache_write_1h_input_usd_per_1m": 1.0}
    )

    assert pricing.long_context_cache_write_1h_input_usd_per_1m == 1.0


def test_field_defaults_to_none_when_absent() -> None:
    pricing = ModelPricing.model_validate({})

    assert pricing.long_context_cache_write_1h_input_usd_per_1m is None


def test_field_accepts_explicit_null() -> None:
    pricing = ModelPricing.model_validate(
        {"long_context_cache_write_1h_input_usd_per_1m": None}
    )

    assert pricing.long_context_cache_write_1h_input_usd_per_1m is None


def test_field_round_trips_through_model_dump() -> None:
    pricing = ModelPricing.model_validate(
        {"long_context_cache_write_1h_input_usd_per_1m": 1.0}
    )

    dumped = pricing.model_dump()

    assert dumped["long_context_cache_write_1h_input_usd_per_1m"] == 1.0
