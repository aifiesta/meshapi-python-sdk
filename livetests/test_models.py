"""Live tests: Models endpoints."""

from __future__ import annotations

from meshapi import MeshAPI, ModelSearchParams


def test_models_list(client: MeshAPI) -> None:
    models = client.models.list()
    assert isinstance(models, list), "expected a list"
    assert models, "expected at least one model"
    m = models[0]
    assert m.id, "model should have an id"
    assert m.name, "model should have a name"


def test_models_free(client: MeshAPI) -> None:
    free = client.models.free()
    assert isinstance(free, list)
    paid_in_free = [m for m in free if not m.is_free]
    assert not paid_in_free, f"paid models found in free list: {[m.id for m in paid_in_free]}"


def test_models_paid(client: MeshAPI) -> None:
    paid = client.models.paid()
    assert isinstance(paid, list)
    free_in_paid = [m for m in paid if m.is_free]
    assert not free_in_paid, f"free models found in paid list: {[m.id for m in free_in_paid]}"


def test_models_list_filter_free(client: MeshAPI) -> None:
    filtered = client.models.list(free=True)
    assert all(m.is_free for m in filtered), "list(free=True) returned non-free models"


def test_models_list_filter_paid(client: MeshAPI) -> None:
    filtered = client.models.list(free=False)
    assert all(not m.is_free for m in filtered), "list(free=False) returned free models"


def test_models_search_paginated(client: MeshAPI) -> None:
    page = client.models.search(ModelSearchParams(limit=5))
    assert page.total >= 0, "expected a non-negative total"
    assert page.limit == 5, "page should echo the requested limit"
    assert len(page.items) <= 5, "page must not exceed the limit"
    assert isinstance(page.brands, list), "expected a brands facet list"
    for m in page.items:
        assert m.id and m.name


def test_models_search_query_filter(client: MeshAPI) -> None:
    page = client.models.search(ModelSearchParams(q="gpt", limit=10))
    # Fuzzy match over id/name/brand — every returned model should relate to the query.
    for m in page.items:
        haystack = f"{m.id} {m.name}".lower()
        assert "gpt" in haystack, f"unexpected model {m.id!r} for q='gpt'"


def test_models_get_by_id(client: MeshAPI) -> None:
    listed = client.models.list()
    assert listed, "need at least one model to fetch by id"
    target = listed[0].id
    model = client.models.get(target)
    assert model.id == target, f"get({target!r}) returned {model.id!r}"
    assert model.name
