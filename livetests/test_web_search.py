"""Live tests: web search — POST /v1/web/search.

Gated server-side by WEB_SEARCH_ENABLED. When the feature is disabled the
endpoint returns 403/404, in which case these tests skip (deployment config),
not fail.
"""

from __future__ import annotations

import pytest
from meshapi import MeshAPI, MeshAPIError, WebSearchParams


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
    assert resp.provider in ("native", "tavily"), f"unexpected provider {resp.provider!r}"
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
