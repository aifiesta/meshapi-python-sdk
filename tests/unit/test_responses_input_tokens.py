"""Unit tests for ResponsesResource.input_tokens (no network)."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Tuple

from meshapi._types import ResponsesParams
from meshapi.resources.responses import (
    AsyncResponsesResource,
    ResponsesInputTokensResponse,
    ResponsesResource,
)

PAYLOAD = {"object": "response.input_tokens", "input_tokens": 12}


class _FakeHttp:
    def __init__(self) -> None:
        self.calls: List[Tuple[str, Dict[str, Any]]] = []

    def post(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        self.calls.append((path, body))
        return PAYLOAD


class _FakeAsyncHttp:
    def __init__(self) -> None:
        self.calls: List[Tuple[str, Dict[str, Any]]] = []

    async def post(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        self.calls.append((path, body))
        return PAYLOAD


def _params() -> ResponsesParams:
    return ResponsesParams(model="openai/gpt-4o-mini", input="Hello")


def test_input_tokens_posts_to_count_endpoint() -> None:
    http = _FakeHttp()
    result = ResponsesResource(http).input_tokens(_params())  # type: ignore[arg-type]

    assert isinstance(result, ResponsesInputTokensResponse)
    assert result.input_tokens == 12
    assert result.object == "response.input_tokens"
    path, body = http.calls[0]
    assert path == "/v1/responses/input_tokens"
    assert body["model"] == "openai/gpt-4o-mini"
    assert "stream" not in body


def test_input_tokens_tolerates_extra_fields() -> None:
    parsed = ResponsesInputTokensResponse.model_validate({"input_tokens": 3, "extra": 1})
    assert parsed.input_tokens == 3


def test_async_input_tokens_posts_to_count_endpoint() -> None:
    http = _FakeAsyncHttp()
    result = asyncio.run(
        AsyncResponsesResource(http).input_tokens(_params())  # type: ignore[arg-type]
    )

    assert result.input_tokens == 12
    assert http.calls[0][0] == "/v1/responses/input_tokens"
