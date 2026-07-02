"""Live tests: Model Compare API."""

from __future__ import annotations

import pytest
from meshapi import MeshAPI, CompareParams, ChatMessage


def test_compare_nonstreaming(client: MeshAPI, model: str, second_model: str) -> None:
    result = client.compare.create(
        CompareParams(
            models=[model, second_model],
            messages=[ChatMessage(role="user", content="What is 2+2? Reply in one word.")],
            skip_comparison=True,
            max_tokens=20,
        )
    )
    assert result.comparison_id, "expected comparison_id"
    assert len(result.results) == 2, f"expected 2 results, got {len(result.results)}"
    found_models = {r.model for r in result.results}
    assert model in found_models, f"expected {model} in results"
    assert second_model in found_models, f"expected {second_model} in results"
    for r in result.results:
        assert r.content or r.error, f"result for {r.model} has neither content nor error"


def test_compare_streaming(client: MeshAPI, model: str, second_model: str) -> None:
    events = list(
        client.compare.stream(
            CompareParams(
                models=[model, second_model],
                messages=[ChatMessage(role="user", content="Tell me a joke.")],
                skip_comparison=True,
                max_tokens=50,
            )
        )
    )
    assert len(events) > 0, "expected at least one streaming event"
