"""Live tests: router select — POST /v1/router/select.

Gated server-side by AUTO_ROUTER_ENABLED. When disabled the endpoint returns
403/404, in which case these tests skip (deployment config), not fail.
"""

from __future__ import annotations

import pytest
from meshapi import ChatMessage, MeshAPI, MeshAPIError, RouterSelectParams


def _select(client: MeshAPI, params: RouterSelectParams):
    try:
        return client.router.select(params)
    except MeshAPIError as exc:
        if exc.status in (403, 404, 501):
            pytest.skip(f"auto router disabled on this deployment (AUTO_ROUTER_ENABLED): {exc.error_code}")
        raise


def test_router_select_returns_a_model(client: MeshAPI) -> None:
    resp = _select(
        client,
        RouterSelectParams(
            messages=[ChatMessage(role="user", content="Write a Python function to reverse a string.")]
        ),
    )
    assert resp.model, "router must always return a model (fail-soft)"
    assert resp.auto_router is not None


def test_router_select_honors_exclusions(client: MeshAPI) -> None:
    excluded = "openai/gpt-4o-mini"
    resp = _select(
        client,
        RouterSelectParams(
            messages=[ChatMessage(role="user", content="Explain the theory of relativity simply.")],
            exclude_models=[excluded],
        ),
    )
    assert resp.model, "router must return a model even with exclusions"
    # Unless it fell back to the configured default, the excluded model must not be picked.
    if not resp.auto_router.fallback_used:
        assert resp.model != excluded, "excluded model should not be selected"
