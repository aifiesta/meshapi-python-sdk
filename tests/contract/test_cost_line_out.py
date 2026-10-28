from meshapi._usage_types import CostBreakdownOut, CostLineOut


def test_token_line_parses():
    line = CostLineOut.model_validate({"tokens": 1200, "rate_per_1m_usd": "0.15"})
    assert line.tokens == 1200
    assert line.rate_per_1m_usd == "0.15"
    assert line.unit is None


def test_non_token_line_allows_null_tokens_and_rate():
    line = CostLineOut.model_validate(
        {
            "tokens": None,
            "rate_per_1m_usd": None,
            "quantity": 5,
            "unit": "per_second",
            "rate_usd": "0.10",
            "charged": True,
            "modifiers": ["with_audio"],
        }
    )
    assert line.tokens is None
    assert line.rate_per_1m_usd is None
    assert line.quantity == 5
    assert line.unit == "per_second"
    assert line.modifiers == ["with_audio"]


def test_line_without_tokens_key_parses():
    line = CostLineOut.model_validate({"quantity": 2, "unit": "per_image"})
    assert line.tokens is None


def test_uncharged_line():
    line = CostLineOut.model_validate({"tokens": 10, "charged": False})
    assert line.charged is False


def test_breakdown_rounding():
    bd = CostBreakdownOut.model_validate(
        {"lines": [{"tokens": 1, "rate_per_1m_usd": "1"}], "rounding_usd": "0.0000001"}
    )
    assert bd.rounding_usd == "0.0000001"
    assert bd.lines is not None and bd.lines[0].tokens == 1
