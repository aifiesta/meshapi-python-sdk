from meshapi._cost_types import CostBreakdownOut, CostLineOut


def test_token_line_parses():
    line = CostLineOut.model_validate(
        {"tokens": 1200, "rate_per_1m_usd": "0.15", "charged": True}
    )
    assert line.tokens == 1200
    assert line.rate_per_1m_usd == "0.15"
    assert line.charged is True


def test_non_token_line_allows_null_tokens_and_rate():
    line = CostLineOut.model_validate(
        {
            "tokens": None,
            "rate_per_1m_usd": None,
            "quantity": 2,
            "unit": "per_image",
            "rate_usd": "0.04",
            "modifiers": {"resolution": "2048x2048"},
        }
    )
    assert line.tokens is None
    assert line.rate_per_1m_usd is None
    assert line.quantity == 2
    assert line.unit == "per_image"
    assert line.rate_usd == "0.04"


def test_line_without_token_fields_parses():
    line = CostLineOut.model_validate({"quantity": 5, "unit": "per_second"})
    assert line.tokens is None
    assert line.rate_per_1m_usd is None


def test_breakdown_rounding():
    breakdown = CostBreakdownOut.model_validate(
        {"lines": [{"tokens": 10, "rate_per_1m_usd": "1"}], "rounding_usd": "0.000001"}
    )
    assert breakdown.rounding_usd == "0.000001"
    assert len(breakdown.lines) == 1


def test_unknown_fields_are_kept():
    line = CostLineOut.model_validate({"tokens": 1, "future_field": "x"})
    assert line.model_dump()["future_field"] == "x"
