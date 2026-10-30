"""Unit tests for POST /v1/responses/input_tokens (no network)."""

from __future__ import annotations

import asyncio
from typing import Any, List, Tuple

from meshapi.resources.responses import (
    AsyncResponsesResource,
    ResponsesInputTokensResponse,
    ResponsesResource,
)

MODEL = "openai/gpt-4o-mini"


class _Params:
    """Minimal stand-in exposing the ``model_dump`` surface the resource uses."""

    def __init__(self, **fields: Any) -> None:
        self._fields = fields

    def model_dump(self, exclude_none: bool = False) -> dict:
        if exclude_none:
            return {k: v for k, v in self._fields.items() if v is not None}
        return dict(self._fields)


class _SyncHttp:
    def __init__(self, response: dict) -> None:
        self.response = response
        self.calls: List[Tuple[str, dict]] = []

    def post(self, path: str, body: dict) -> dict:
        self.calls.append((path, body))
        return self.response


class _AsyncHttp:
    def __init__(self, response: dict) -> None:
        self.response = response
        self.calls: List[Tuple[str, dict]] = []

    async def post(self, path: str, body: dict) -> dict:
        self.calls.append((path, body))
        return self.response


_PAYLOAD = {"object": "response.input_tokens", "input_tokens": 11}


def test_input_tokens_posts_to_count_route() -> None:
    http = _SyncHttp(_PAYLOAD)
    resource = ResponsesResource(http)  # type: ignore[arg-type]

    result = resource.input_tokens(_Params(model=MODEL, input="Hello", instructions=None))  # type: ignore[arg-type]

    assert isinstance(result, ResponsesInputTokensResponse)
    assert result.input_tokens == 11
    assert result.object == "response.input_tokens"
    path, body = http.calls[0]
    assert path == "/v1/responses/input_tokens"
    assert body == {"model": MODEL, "input": "Hello"}


def test_input_tokens_drops_stream_flag() -> None:
    http = _SyncHttp(_PAYLOAD)
    resource = ResponsesResource(http)  # type: ignore[arg-type]

    resource.input_tokens(_Params(model=MODEL, input="Hi", stream=True))  # type: ignore[arg-type]

    _, body = http.calls[0]
    assert "stream" not in body


def test_input_tokens_tolerates_extra_fields() -> None:
    http = _SyncHttp({"input_tokens": 3, "extra": "x"})
    resource = ResponsesResource(http)  # type: ignore[arg-type]

    result = resource.input_tokens(_Params(model=MODEL, input="Hi"))  # type: ignore[arg-type]

    assert result.input_tokens == 3
    assert result.object is None


def test_async_input_tokens_posts_to_count_route() -> None:
    http = _AsyncHttp(_PAYLOAD)
    resource = AsyncResponsesResource(http)  # type: ignore[arg-type]

    result = asyncio.run(
        resource.input_tokens(_Params(model=MODEL, input="Hello", stream=True))  # type: ignore[arg-type]
    )

    assert result.input_tokens == 11
    path, body = http.calls[0]
    assert path == "/v1/responses/input_tokens"
    assert body == {"model": MODEL, "input": "Hello"}
