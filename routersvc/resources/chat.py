"""Chat completions resource — POST /v1/chat/completions."""

from __future__ import annotations

from typing import AsyncIterator, Iterator

from .._http import AsyncHttpClient, SyncHttpClient
from .._types import ChatCompletionChunk, ChatCompletionParams, ChatCompletionResponse


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

        Streams do NOT retry on failure. Catch RouterSvcApiError and
        restart a new request if reconnection is needed.
        """
        body = params.model_dump(exclude_none=True)
        body["stream"] = True
        yield from self._http.stream("/v1/chat/completions", body)


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

        Streams do NOT retry on failure. Catch RouterSvcApiError and
        restart a new request if reconnection is needed.
        """
        body = params.model_dump(exclude_none=True)
        body["stream"] = True
        async for chunk in self._http.stream("/v1/chat/completions", body):
            yield chunk


class AsyncChatResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self.completions = AsyncCompletionsResource(http)
