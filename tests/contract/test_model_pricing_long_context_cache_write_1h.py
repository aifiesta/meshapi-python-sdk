"""Contract tests for ``ModelPricing.long_context_cache_write_1h_input_usd_per_1m``.

The field is published by ``GET /v1/models`` and carries the per-million-token
price of a 1-hour cache write on a prompt past the model's long-context
threshold. It is optional: models without a long-context 1h write rate omit it
or send ``null``.
"""

from meshapi._types import ModelPricing


def test_parses_long_context_cache_write_1h_rate() -> None:
    pricing = ModelPricing.model_validate(
        {"long_context_cache_write_1h_input_usd_per_1m": 1.0}
    )
    assert pricing.long_context_cache_write_1h_input_usd_per_1m == 1.0


def test_null_long_context_cache_write_1h_rate_is_none() -> None:
    pricing = ModelPricing.model_validate(
        {"long_context_cache_write_1h_input_usd_per_1m": None}
    )
    assert pricing.long_context_cache_write_1h_input_usd_per_1m is None


def test_missing_long_context_cache_write_1h_rate_defaults_to_none() -> None:
    pricing = ModelPricing.model_validate({})
    assert pricing.long_context_cache_write_1h_input_usd_per_1m is None


def test_long_context_cache_write_1h_rate_round_trips() -> None:
    pricing = ModelPricing.model_validate(
        {"long_context_cache_write_1h_input_usd_per_1m": 1.0}
    )
    dumped = pricing.model_dump(exclude_none=True)
    assert dumped["long_context_cache_write_1h_input_usd_per_1m"] == 1.0
