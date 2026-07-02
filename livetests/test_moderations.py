"""Live tests: moderations — POST /v1/moderations."""

from __future__ import annotations

import pytest
from meshapi import MeshAPI, MeshAPIError, ModerationParams


def test_moderation_flags_harmful_text(client: MeshAPI) -> None:
    try:
        resp = client.moderations.create(
            ModerationParams(input="I want to hurt and kill someone right now.")
        )
    except MeshAPIError as exc:
        if exc.status in (403, 404, 501, 503):
            pytest.skip(f"moderations unavailable on this deployment: {exc.error_code}")
        raise

    assert resp.results, "expected at least one moderation result"
    result = resp.results[0]
    assert result.flagged is True, "expected harmful text to be flagged"
    assert result.categories, "expected category booleans"
    assert result.category_scores, "expected category scores"


def test_moderation_passes_benign_text(client: MeshAPI) -> None:
    try:
        resp = client.moderations.create(ModerationParams(input="I love sunny days at the park."))
    except MeshAPIError as exc:
        if exc.status in (403, 404, 501, 503):
            pytest.skip(f"moderations unavailable on this deployment: {exc.error_code}")
        raise

    assert resp.results
    assert resp.results[0].flagged is False, "expected benign text not to be flagged"


def test_moderation_batch_input(client: MeshAPI) -> None:
    try:
        resp = client.moderations.create(
            ModerationParams(input=["hello friend", "have a nice day"])
        )
    except MeshAPIError as exc:
        if exc.status in (403, 404, 501, 503):
            pytest.skip(f"moderations unavailable on this deployment: {exc.error_code}")
        raise

    assert len(resp.results) == 2, "expected one result per input"
