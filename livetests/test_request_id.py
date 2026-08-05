"""Live tests: request-id support (set + read).

The backend sets an ``X-Request-Id`` header (format ``req_<ULID>``) on every
response and echoes a client-supplied id when it matches
``^[A-Za-z0-9._:-]{1,64}$``. The SDK sends the per-call ``request_id`` option
as that header and surfaces the response header as ``response._request_id``.
"""

from __future__ import annotations

import uuid

import pytest

from meshapi import ChatCompletionParams, ChatMessage, MeshAPI, MeshAPIError


def _chat_params(model: str) -> ChatCompletionParams:
    return ChatCompletionParams(
        model=model,
        messages=[ChatMessage(role="user", content="Reply with the single word: ok")],
        max_tokens=5,
        temperature=0,
    )


def test_default_request_id_starts_with_req(client: MeshAPI, model: str) -> None:
    resp = client.chat.completions.create(_chat_params(model))
    assert resp._request_id, "expected _request_id to be populated from X-Request-Id"
    assert resp._request_id.startswith("req_"), (
        f"expected server-minted id like req_<ULID>, got {resp._request_id!r}"
    )


def test_custom_request_id_is_echoed_exactly(client: MeshAPI, model: str) -> None:
    custom_id = f"py-sdk-livetest-{uuid.uuid4().hex}"
    resp = client.chat.completions.create(_chat_params(model), request_id=custom_id)
    assert resp._request_id == custom_id, (
        f"expected backend to echo {custom_id!r}, got {resp._request_id!r}"
    )


def test_custom_request_id_on_models_list(client: MeshAPI) -> None:
    """Non-inference surface: models.list carries the id per item."""
    custom_id = f"py-sdk-livetest-{uuid.uuid4().hex}"
    models = client.models.list(request_id=custom_id)
    assert models, "expected at least one model"
    assert models[0]._request_id == custom_id


def test_invalid_request_id_raises_locally(client: MeshAPI, model: str) -> None:
    """Invalid ids fail fast in the SDK — the backend would silently ignore them."""
    with pytest.raises(ValueError):
        client.chat.completions.create(_chat_params(model), request_id="has spaces!")


def test_error_response_still_exposes_request_id(client: MeshAPI) -> None:
    """Errors carry the id via MeshAPIError.request_id (pre-existing behaviour)."""
    custom_id = f"py-sdk-livetest-{uuid.uuid4().hex}"
    with pytest.raises(MeshAPIError) as exc_info:
        client.chat.completions.create(
            ChatCompletionParams(
                model="nonexistent/definitely-not-a-model",
                messages=[ChatMessage(role="user", content="hi")],
            ),
            request_id=custom_id,
        )
    assert exc_info.value.request_id == custom_id


def test_model_dump_never_contains_request_id(client: MeshAPI, model: str) -> None:
    resp = client.chat.completions.create(_chat_params(model))
    assert resp._request_id
    assert "_request_id" not in resp.model_dump()
    assert "_request_id" not in resp.model_dump_json()
