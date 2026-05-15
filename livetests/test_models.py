"""Live tests: Models endpoints."""

from __future__ import annotations

from meshapi import MeshAPI


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
