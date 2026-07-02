"""Live tests: Model Compare API."""

from __future__ import annotations

from meshapi import MeshAPI, CompareParams, ChatMessage, ModelOverride


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


def test_compare_with_synthesis(client: MeshAPI, model: str, second_model: str) -> None:
    """Exercise the synthesis path (skip_comparison=False) — previously never tested."""
    result = client.compare.create(
        CompareParams(
            models=[model, second_model],
            messages=[ChatMessage(role="user", content="In one sentence, what is TCP?")],
            comparison_instructions="Briefly state which answer is clearer.",
            skip_comparison=False,
            max_tokens=60,
        )
    )
    assert result.comparison_id
    assert len(result.results) == 2
    # When at least one per-model answer succeeded and the comparison model did
    # not fall back, a synthesized comparison must be present with usage.
    if any(r.content for r in result.results) and not result.comparison_fallback_used:
        assert result.comparison, "expected a synthesized comparison when skip_comparison=False"
        assert result.comparison_model, "expected comparison_model to be reported"
        assert result.comparison_usage is not None, "expected comparison_usage to be populated"


def test_compare_model_overrides(client: MeshAPI, model: str, second_model: str) -> None:
    """Per-model overrides (temperature/max_tokens) — previously untested."""
    result = client.compare.create(
        CompareParams(
            models=[model, second_model],
            messages=[ChatMessage(role="user", content="Say hi in one word.")],
            model_overrides=[ModelOverride(model=model, temperature=0.0, max_tokens=10)],
            skip_comparison=True,
            max_tokens=20,
        )
    )
    assert len(result.results) == 2, "overrides must not drop any model from the fan-out"
