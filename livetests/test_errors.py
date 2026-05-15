"""Live tests: error handling and exception types."""

from __future__ import annotations

import pytest
from meshapi import MeshAPI, MeshAPIError, ChatCompletionParams, ChatMessage
from config import BASE_URL


def test_error_unauthorized_chat(model: str) -> None:
    bad = MeshAPI(base_url=BASE_URL, token="rsk_INVALID_TOKEN")
    with pytest.raises(MeshAPIError) as exc_info:
        bad.chat.completions.create(
            ChatCompletionParams(
                model=model,
                messages=[ChatMessage(role="user", content="hello")],
            )
        )
    err = exc_info.value
    assert err.status == 401
    assert err.error_code, "expected an error_code in the response"


def test_error_unauthorized_models() -> None:
    bad = MeshAPI(base_url=BASE_URL, token="rsk_INVALID_TOKEN")
    with pytest.raises(MeshAPIError) as exc_info:
        bad.models.list()
    assert exc_info.value.status == 401


def test_error_not_found_template(client: MeshAPI) -> None:
    with pytest.raises(MeshAPIError) as exc_info:
        client.templates.get("tmpl_nonexistent_id_000000")
    assert exc_info.value.status == 404


def test_error_is_exception(model: str) -> None:
    bad = MeshAPI(base_url=BASE_URL, token="rsk_INVALID_TOKEN")
    with pytest.raises(Exception):
        bad.chat.completions.create(
            ChatCompletionParams(
                model=model,
                messages=[ChatMessage(role="user", content="hello")],
            )
        )
