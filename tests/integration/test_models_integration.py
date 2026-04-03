"""Integration tests — models endpoints.

These tests import from the installed package (pip install -e .)
and run against a live RouterSVC server.

Run: pytest tests/integration/ -v --base-url=http://localhost:8000 --token=rsk_...
     or set env vars ROUTERSVC_BASE_URL and ROUTERSVC_TOKEN.
"""

import os

import pytest

# Import from the installed package, not raw source
from routersvc import MeshAPI
from routersvc._types import ModelInfo


BASE_URL = os.getenv("ROUTERSVC_BASE_URL", "http://localhost:8000")
TOKEN = os.getenv("ROUTERSVC_TOKEN", "rsk_01KN96KQWDPF2X1E9CP8567JY4")


@pytest.fixture(scope="module")
def client():
    with MeshAPI(base_url=BASE_URL, token=TOKEN) as c:
        yield c


def test_models_list_returns_list(client: MeshAPI):
    models = client.models.list()
    assert isinstance(models, list)
    for m in models:
        assert isinstance(m, ModelInfo)
        assert isinstance(m.id, str)
        assert isinstance(m.is_free, bool)


def test_models_free_returns_only_free(client: MeshAPI):
    models = client.models.free()
    assert isinstance(models, list)
    for m in models:
        assert m.is_free is True


def test_models_paid_returns_only_paid(client: MeshAPI):
    models = client.models.paid()
    assert isinstance(models, list)
    for m in models:
        assert m.is_free is False


def test_models_list_with_free_filter(client: MeshAPI):
    free_models = client.models.list(free=True)
    paid_models = client.models.list(free=False)
    for m in free_models:
        assert m.is_free is True
    for m in paid_models:
        assert m.is_free is False
