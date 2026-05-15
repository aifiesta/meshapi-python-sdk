"""Live tests: Chat completions (streaming)."""

from __future__ import annotations

import pytest
from meshapi import MeshAPI, ChatCompletionParams, ChatMessage, MeshAPIError


def test_stream_basic(client: MeshAPI, model: str) -> None:
    chunks_received = 0
    full_content = ""

    for chunk in client.chat.completions.stream(
        ChatCompletionParams(
            model=model,
            messages=[ChatMessage(role="user", content="Count exactly from 1 to 3.")],
        )
    ):
        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content is not None:
            full_content += chunk.choices[0].delta.content
            chunks_received += 1

    assert chunks_received > 0, "expected at least one content chunk"
    assert full_content.strip(), "expected non-empty accumulated content"


def test_stream_chunk_structure(client: MeshAPI, model: str) -> None:
    chunks = list(
        client.chat.completions.stream(
            ChatCompletionParams(
                model=model,
                messages=[ChatMessage(role="user", content="Say hi.")],
                max_tokens=10,
            )
        )
    )
    assert chunks, "expected at least one chunk"
    first = chunks[0]
    assert first.id, "first chunk should have an id"
    assert first.model, "first chunk should have a model field"
    for chunk in chunks:
        assert chunk.choices is not None, "each chunk should have choices"


def test_stream_early_stop(client: MeshAPI, model: str) -> None:
    seen = 0
    for chunk in client.chat.completions.stream(
        ChatCompletionParams(
            model=model,
            messages=[ChatMessage(role="user", content="Count slowly from 1 to 100.")],
        )
    ):
        seen += 1
        if seen >= 3:
            break

    assert seen >= 1, "expected to receive at least one chunk before stopping"


def test_stream_auth_error(client: MeshAPI, model: str) -> None:
    from meshapi import MeshAPI as _MeshAPI
    from config import BASE_URL

    bad_client = _MeshAPI(base_url=BASE_URL, token="rsk_INVALID_TOKEN")
    with pytest.raises(MeshAPIError) as exc_info:
        for _ in bad_client.chat.completions.stream(
            ChatCompletionParams(
                model=model,
                messages=[ChatMessage(role="user", content="hello")],
            )
        ):
            pass
    assert exc_info.value.status == 401
