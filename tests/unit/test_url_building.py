"""Unit tests for URL building and query string construction."""

import pytest

from routersvc._http import MeshAPIConfig, SyncHttpClient


def make_client(base_url: str = "http://localhost:8000") -> SyncHttpClient:
    cfg = MeshAPIConfig(base_url=base_url, token="rsk_test")
    return SyncHttpClient(cfg)


def test_base_url_trailing_slash_stripped():
    cfg = MeshAPIConfig(base_url="http://localhost:8000/", token="tok")
    assert cfg.base_url == "http://localhost:8000"


def test_base_url_no_trailing_slash_unchanged():
    cfg = MeshAPIConfig(base_url="http://localhost:8000", token="tok")
    assert cfg.base_url == "http://localhost:8000"


def test_headers_contain_bearer():
    client = make_client()
    headers = client._headers()
    assert headers["Authorization"] == "Bearer rsk_test"


def test_headers_content_type():
    client = make_client()
    headers = client._headers()
    assert headers["Content-Type"] == "application/json"


def test_headers_sdk_version():
    client = make_client()
    headers = client._headers()
    assert "X-RouterSVC-SDK" in headers
    assert headers["X-RouterSVC-SDK"].startswith("python/")


def test_models_free_query_param():
    """Verify free=True serialises to 'true' (lowercase), not 'True'."""
    from routersvc.resources.models import ModelsResource
    from unittest.mock import MagicMock, patch

    mock_http = MagicMock()
    mock_http.get.return_value = []
    resource = ModelsResource(mock_http)
    resource.list(free=True)
    mock_http.get.assert_called_once_with("/v1/models", params={"free": "true"})


def test_models_paid_query_param():
    from routersvc.resources.models import ModelsResource
    from unittest.mock import MagicMock

    mock_http = MagicMock()
    mock_http.get.return_value = []
    resource = ModelsResource(mock_http)
    resource.list(free=False)
    mock_http.get.assert_called_once_with("/v1/models", params={"free": "false"})


def test_models_no_filter_no_params():
    from routersvc.resources.models import ModelsResource
    from unittest.mock import MagicMock

    mock_http = MagicMock()
    mock_http.get.return_value = []
    resource = ModelsResource(mock_http)
    resource.list()
    mock_http.get.assert_called_once_with("/v1/models", params=None)


def test_template_get_path():
    from routersvc.resources.templates import TemplatesResource
    from unittest.mock import MagicMock
    from routersvc._types import TemplateSummary

    mock_http = MagicMock()
    mock_http.get.return_value = {
        "id": "abc", "name": "t", "owner": "u",
        "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-01T00:00:00Z"
    }
    resource = TemplatesResource(mock_http)
    resource.get("abc")
    mock_http.get.assert_called_once_with("/v1/templates/abc")


def test_template_delete_path():
    from routersvc.resources.templates import TemplatesResource
    from unittest.mock import MagicMock

    mock_http = MagicMock()
    resource = TemplatesResource(mock_http)
    resource.delete("xyz")
    mock_http.delete.assert_called_once_with("/v1/templates/xyz")
