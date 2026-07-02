"""Live tests: responses list/get — GET /v1/responses, GET /v1/responses/{id}.

(POST /v1/responses create/stream is covered in test_inference_resources.py.)
"""

from __future__ import annotations

import pytest
from meshapi import MeshAPI, MeshAPIError


def test_responses_list_shape(client: MeshAPI) -> None:
    page = client.responses.list(limit=5)
    # OpenAI list envelope; data may be empty if the account has no background jobs.
    if page.object is not None:
        assert page.object == "list"
    assert isinstance(page.data, list)
    assert len(page.data) <= 5
    for item in page.data:
        assert item.id, "each job must have an id"


def test_responses_get_unknown_id_404(client: MeshAPI) -> None:
    """get() on a non-existent id should raise a structured 404 (exercises the path)."""
    with pytest.raises(MeshAPIError) as excinfo:
        client.responses.get("resp_does_not_exist_000000000000")
    assert excinfo.value.status in (400, 404), f"unexpected status {excinfo.value.status}"
