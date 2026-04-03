"""Integration tests — chat completions (non-streaming + streaming)."""

import os

import pytest

from meshapi import MeshAPI
from meshapi._types import (
    ChatCompletionChunk,
    ChatCompletionParams,
    ChatCompletionResponse,
    ChatMessage,
)

BASE_URL = os.getenv("MESHAPI_BASE_URL", "http://localhost:8000")
TOKEN = os.getenv("MESHAPI_TOKEN", "rsk_01KN96KQWDPF2X1E9CP8567JY4")
MODEL = "openai/gpt-4o-mini"


@pytest.fixture(scope="module")
def client():
    with MeshAPI(base_url=BASE_URL, token=TOKEN) as c:
        yield c


def test_chat_non_streaming(client: MeshAPI):
    params = ChatCompletionParams(
        model=MODEL,
        messages=[ChatMessage(role="user", content="Say 'pong' and nothing else.")],
        max_tokens=5,
    )
    resp = client.chat.completions.create(params)
    assert isinstance(resp, ChatCompletionResponse)
    assert resp.id
    assert len(resp.choices) > 0
    choice = resp.choices[0]
    assert choice.message is not None
    assert choice.message.content is not None


def test_chat_streaming(client: MeshAPI):
    params = ChatCompletionParams(
        model=MODEL,
        messages=[ChatMessage(role="user", content="Count from 1 to 3.")],
        max_tokens=20,
    )
    chunks = list(client.chat.completions.stream(params))
    assert len(chunks) > 0
    for chunk in chunks:
        assert isinstance(chunk, ChatCompletionChunk)

    # Reconstruct text from deltas
    text = "".join(
        (c.choices[0].delta.content or "")
        for c in chunks
        if c.choices and c.choices[0].delta
    )
    assert len(text) > 0
