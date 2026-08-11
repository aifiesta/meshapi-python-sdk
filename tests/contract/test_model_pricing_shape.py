"""`ModelPricing` must describe the pricing object the gateway actually returns.

Found during the MESH-472 versioning audit: this SDK declares
`prompt_usd_per_1k` / `completion_usd_per_1k`, which prod stopped returning in
`v1.0.135` (they now have **zero** references anywhere in the gateway), and it does
not declare `input_usd_per_unit` / `output_usd_per_unit`, which are what replaced
them. So the SDK advertises two fields that are always `None` and hides the two that
carry the rate.

That mattered more than a cosmetic drift, because `extra="ignore"` means the missing
fields were not merely undocumented — they were *discarded*. A caller reading pricing
off a non-token-priced model (per_second video, per_image, per_1k_chars) had no field
to read at all: the per-1M pair is `None` by design for those rows, and the raw rate
was being dropped.

The pre-existing `model_list.json` fixture cannot catch this: it encodes the old
shape, so it asserts the SDK parses a response the gateway no longer sends.
`model_list_current.json` is the shape prod sends today.
"""

from __future__ import annotations

import json
from pathlib import Path

from meshapi import ModelInfo, ModelPricing

_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def _load(name: str):
    return json.loads((_FIXTURES / name).read_text())


class TestTheCurrentShape:
    def test_a_token_priced_row_exposes_the_per_unit_rate(self):
        """For token rows the per-unit rate equals the per-1M rate, so both are
        readable and a caller can use either."""
        models = [ModelInfo.model_validate(m) for m in _load("model_list_current.json")]
        gpt = next(m for m in models if m.id == "openai/gpt-4o-mini")

        assert gpt.pricing is not None
        assert gpt.pricing.pricing_unit == "per_1m_tokens"
        assert gpt.pricing.prompt_usd_per_1m == "0.15000000"
        assert gpt.pricing.input_usd_per_unit == "0.15000000"
        assert gpt.pricing.output_usd_per_unit == "0.60000000"

    def test_a_non_token_row_has_its_rate_only_in_per_unit(self):
        """The case the missing fields actually broke. A per-second video model has
        `None` for both per-1M fields — a per-1M-token figure is meaningless for it —
        so `input_usd_per_unit` is the *only* place the rate exists. Without these
        fields declared, `extra="ignore"` dropped it and the SDK reported a priced
        model as having no price.
        """
        models = [ModelInfo.model_validate(m) for m in _load("model_list_current.json")]
        video = next(m for m in models if m.id == "bytedance/seedance-2-5")

        assert video.pricing is not None
        assert video.pricing.pricing_unit == "per_second"
        assert video.pricing.prompt_usd_per_1m is None
        assert video.pricing.completion_usd_per_1m is None
        assert video.pricing.input_usd_per_unit == "10.70000000"
        assert video.pricing.output_usd_per_unit == "6.40000000"

    def test_the_rate_is_only_interpretable_alongside_pricing_unit(self):
        """`input_usd_per_unit` is a bare number; `pricing_unit` is what makes it a
        price. A response carrying one without the other is not usable, so both have
        to survive parsing together."""
        pricing = ModelPricing.model_validate(
            {"pricing_unit": "per_1k_chars", "input_usd_per_unit": "0.00030000"}
        )

        assert (pricing.pricing_unit, pricing.input_usd_per_unit) == (
            "per_1k_chars",
            "0.00030000",
        )


class TestTheRetiredShape:
    def test_the_legacy_per_1k_fields_still_parse(self):
        """Kept, not removed. They are dead on the wire, but they are part of this
        SDK's published surface — deleting the attributes would break any caller that
        still reads them (with an `AttributeError`, not a `None`). They stay declared
        and default to `None`, which is exactly what the gateway now sends.
        """
        models = [ModelInfo.model_validate(m) for m in _load("model_list.json")]

        assert models[0].pricing is not None
        assert models[0].pricing.prompt_usd_per_1k == "0.000150"

    def test_a_current_response_leaves_them_none(self):
        """The honest outcome of the drift: against a real gateway these read `None`
        forever. A caller branching on them silently sees "unpriced"."""
        models = [ModelInfo.model_validate(m) for m in _load("model_list_current.json")]

        assert models[0].pricing is not None
        assert models[0].pricing.prompt_usd_per_1k is None
        assert models[0].pricing.completion_usd_per_1k is None
