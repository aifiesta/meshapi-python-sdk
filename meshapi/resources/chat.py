"""Chat completions resource — POST /v1/chat/completions."""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Iterator, Type, TypeVar, overload

from pydantic import BaseModel, ValidationError

from .._errors import StructuredOutputError
from .._http import AsyncHttpClient, SyncHttpClient
from .._structured import (
    build_response_format,
    correction_prompt,
    extract_content,
    parse_content,
    structured_output_error_message,
)
from .._types import ChatCompletionChunk, ChatCompletionParams, ChatCompletionResponse

_T = TypeVar("_T", bound=BaseModel)


class CompletionsResource:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def create(self, params: ChatCompletionParams) -> ChatCompletionResponse:
        """Non-streaming completion. Returns the full response."""
        body = params.model_dump(exclude_none=True)
        body["stream"] = False
        data = self._http.post("/v1/chat/completions", body)
        return ChatCompletionResponse.model_validate(data)

    def stream(self, params: ChatCompletionParams) -> Iterator[ChatCompletionChunk]:
        """Streaming completion. Returns an iterator of SSE chunks.

        Streams do NOT retry on failure. Catch MeshAPIApiError and
        restart a new request if reconnection is needed.
        """
        body = params.model_dump(exclude_none=True)
        body["stream"] = True
        yield from self._http.stream("/v1/chat/completions", body)

    @overload
    def parse(self, params: ChatCompletionParams, response_format: Type[_T],
              *, max_retries: int = 0) -> _T: ...
    @overload
    def parse(self, params: ChatCompletionParams, response_format: Dict[str, Any],
              *, max_retries: int = 0) -> Dict[str, Any]: ...
    @overload
    def parse(self, params: ChatCompletionParams, response_format: Any,
              *, max_retries: int = 0) -> Any: ...

    def parse(self, params, response_format, *, max_retries=0):
        """Structured (JSON-schema-constrained) completion.

        ``response_format`` may be a Pydantic model class (-> typed instance),
        a TypedDict/dataclass (-> validated object), or a raw JSON-schema dict
        (-> parsed ``dict``, unvalidated). Non-streaming only.

        With ``max_retries > 0``, a response that fails validation is fed back to
        the model with the validation error appended, up to ``max_retries`` times.
        Each retry is a billed inference call.
        """
        body = params.model_dump(exclude_none=True)
        body["stream"] = False
        body["response_format"] = build_response_format(response_format)
        attempt = 0
        while True:
            data = self._http.post("/v1/chat/completions", body)
            resp = ChatCompletionResponse.model_validate(data)
            content = extract_content(resp)
            try:
                return parse_content(response_format, content)
            except (ValidationError, ValueError) as exc:  # ValueError covers JSONDecodeError
                if attempt >= max_retries:
                    raise StructuredOutputError(
                        structured_output_error_message(params.model, exc)
                    ) from exc
                attempt += 1
                body["messages"] = list(body["messages"]) + [
                    {"role": "assistant", "content": content},
                    {"role": "user", "content": correction_prompt(exc)},
                ]


class ChatResource:
    def __init__(self, http: SyncHttpClient) -> None:
        self.completions = CompletionsResource(http)


class AsyncCompletionsResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def create(self, params: ChatCompletionParams) -> ChatCompletionResponse:
        """Non-streaming completion."""
        body = params.model_dump(exclude_none=True)
        body["stream"] = False
        data = await self._http.post("/v1/chat/completions", body)
        return ChatCompletionResponse.model_validate(data)

    async def stream(self, params: ChatCompletionParams) -> AsyncIterator[ChatCompletionChunk]:
        """Streaming completion. Returns an async iterator of SSE chunks.

        Streams do NOT retry on failure. Catch MeshAPIApiError and
        restart a new request if reconnection is needed.
        """
        body = params.model_dump(exclude_none=True)
        body["stream"] = True
        async for chunk in self._http.stream("/v1/chat/completions", body):
            yield chunk

    @overload
    async def parse(self, params: ChatCompletionParams, response_format: Type[_T],
                    *, max_retries: int = 0) -> _T: ...
    @overload
    async def parse(self, params: ChatCompletionParams, response_format: Dict[str, Any],
                    *, max_retries: int = 0) -> Dict[str, Any]: ...
    @overload
    async def parse(self, params: ChatCompletionParams, response_format: Any,
                    *, max_retries: int = 0) -> Any: ...

    async def parse(self, params, response_format, *, max_retries=0):
        """Async structured completion. See ``CompletionsResource.parse``."""
        body = params.model_dump(exclude_none=True)
        body["stream"] = False
        body["response_format"] = build_response_format(response_format)
        attempt = 0
        while True:
            data = await self._http.post("/v1/chat/completions", body)
            resp = ChatCompletionResponse.model_validate(data)
            content = extract_content(resp)
            try:
                return parse_content(response_format, content)
            except (ValidationError, ValueError) as exc:
                if attempt >= max_retries:
                    raise StructuredOutputError(
                        structured_output_error_message(params.model, exc)
                    ) from exc
                attempt += 1
                body["messages"] = list(body["messages"]) + [
                    {"role": "assistant", "content": content},
                    {"role": "user", "content": correction_prompt(exc)},
                ]


class AsyncChatResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self.completions = AsyncCompletionsResource(http)
