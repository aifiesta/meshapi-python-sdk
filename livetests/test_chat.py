"""Live tests: Chat completions (non-streaming)."""

from __future__ import annotations

import pytest
from meshapi import MeshAPI, ChatCompletionParams, ChatMessage
from meshapi._types import CreateTemplateParams


def test_chat_basic(client: MeshAPI, model: str) -> None:
    resp = client.chat.completions.create(
        ChatCompletionParams(
            model=model,
            messages=[ChatMessage(role="user", content="What is the capital of France? Reply in one word.")],
            max_tokens=10,
            temperature=0,
        )
    )
    content = resp.choices[0].message.content
    role = resp.choices[0].message.role
    assert role == "assistant", f"expected role 'assistant', got {role!r}"
    assert content, "expected non-empty content"


def test_chat_multi_turn(client: MeshAPI, model: str) -> None:
    resp = client.chat.completions.create(
        ChatCompletionParams(
            model=model,
            messages=[
                ChatMessage(role="user", content="My favourite color is blue. Remember this."),
                ChatMessage(role="assistant", content="Got it! Your favourite color is blue."),
                ChatMessage(role="user", content="What is my favourite color? Reply in 3 words max."),
            ],
            max_tokens=20,
            temperature=0,
        )
    )
    content = resp.choices[0].message.content
    assert content, "expected non-empty content in multi-turn response"
    assert resp.choices[0].finish_reason in ("stop", "length")


def test_chat_with_template(client: MeshAPI, model: str) -> None:
    import uuid

    name = f"py-livetest-chat-{uuid.uuid4().hex[:8]}"
    tmpl = client.templates.create(
        CreateTemplateParams(
            name=name,
            system="You are a {{role}}. Always reply in exactly one sentence.",
            variables=["role"],
        )
    )
    try:
        resp = client.chat.completions.create(
            ChatCompletionParams(
                model=model,
                messages=[ChatMessage(role="user", content="Introduce yourself.")],
                template=tmpl.name,
                variables={"role": "friendly pirate"},
                max_tokens=80,
                temperature=0,
            )
        )
        content = resp.choices[0].message.content
        assert content, "expected non-empty templated chat response"
    finally:
        client.templates.delete(tmpl.id)


def test_chat_response_fields(client: MeshAPI, model: str) -> None:
    resp = client.chat.completions.create(
        ChatCompletionParams(
            model=model,
            messages=[ChatMessage(role="user", content="Say hello.")],
            max_tokens=10,
        )
    )
    assert resp.id, "response should have an id"
    assert resp.model, "response should have a model field"
    assert resp.usage is not None, "response should include usage"
    assert resp.choices, "response should have choices"
    assert resp.choices[0].message.role == "assistant"
