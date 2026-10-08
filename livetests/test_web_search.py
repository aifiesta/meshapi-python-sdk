"""Live tests: web search — POST /v1/web/search.

Gated server-side by WEB_SEARCH_ENABLED. When the feature is disabled the
endpoint returns 403/404, in which case these tests skip (deployment config),
not fail.
"""

from __future__ import annotations

import pytest
from meshapi import MeshAPI, MeshAPIError, WebSearchParams


ENGINES = ("native", "tavily", "tinyfish")


def _search(client: MeshAPI, params: WebSearchParams):
    try:
        return client.web.search(params)
    except MeshAPIError as exc:
        if exc.status in (403, 404, 501):
            pytest.skip(f"web search disabled on this deployment (WEB_SEARCH_ENABLED): {exc.error_code}")
        raise


def test_web_search_basic(client: MeshAPI) -> None:
    resp = _search(client, WebSearchParams(query="what is the capital of France", max_results=3))
    assert resp.query
    assert resp.provider in ENGINES, f"unexpected provider {resp.provider!r}"
    assert len(resp.results) <= 3
    if resp.results:
        first = resp.results[0]
        assert first.title and first.url, "each result should have a title and url"


def test_web_search_with_answer(client: MeshAPI) -> None:
    resp = _search(
        client,
        WebSearchParams(query="who wrote the book Dune", max_results=5, include_answer=True),
    )
    assert resp.query
    # `answer` is best-effort — assert the field is reachable, not that it is non-null.
    assert resp.answer is None or isinstance(resp.answer, str)


def test_web_search_without_page_content_leaves_the_fields_unset(client: MeshAPI) -> None:
    """The hard half: not asking must never produce page text, on any engine."""
    resp = _search(client, WebSearchParams(query="what is the capital of France", max_results=3))
    for hit in resp.results:
        assert hit.page_content is None, f"page text arrived unasked-for from {resp.provider!r}"
        assert hit.page_content_truncated is False


def test_web_search_page_content(client: MeshAPI) -> None:
    """Page text is tinyfish-only, so the engine is pinned rather than hoped for."""
    try:
        resp = client.web.search(
            WebSearchParams(
                query="James Webb telescope earliest galaxy",
                provider="tinyfish",
                include_page_content=True,
                max_results=2,
            )
        )
    except MeshAPIError as exc:
        # 403/404/501 = web search off; 400/422/503 = this deployment has no
        # tinyfish credential, so the engine is not registered. Both are
        # deployment configuration, not a defect in the SDK.
        if exc.status in (400, 403, 404, 422, 501, 503):
            pytest.skip(f"tinyfish engine unavailable on this deployment: {exc.error_code}")
        raise

    assert resp.provider == "tinyfish", f"pinning was ignored, served by {resp.provider!r}"
    assert resp.results, "expected at least one result"

    for hit in resp.results:
        assert isinstance(hit.page_content_truncated, bool)
        if hit.page_content is not None:
            assert hit.page_content, "page_content should be None, never empty string"
        # The snippet is a separate field and page text never replaces it.
        assert hit.title and hit.url

    if not any(hit.page_content for hit in resp.results):
        # A per-URL fetch failing upstream is normal and silent, so this is a
        # skip rather than a failure — the shape above is what this SDK owns.
        pytest.skip("upstream returned no page text for any result on this run")
