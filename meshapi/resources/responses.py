"""Responses resource — POST /v1/responses."""

from __future__ import annotations

from typing import AsyncIterator, Iterator

from .._http import AsyncHttpClient, SyncHttpClient
from .._types import ChatCompletionChunk, ResponsesParams, ResponsesResponse


class ResponsesResource:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def create(self, params: ResponsesParams) -> ResponsesResponse:
        """Non-streaming response. Returns the full response.

        Example::

            response = client.responses.create(
                ResponsesParams(
                    model="openai/o4-mini",
                    input="Explain the halting problem simply.",
                    reasoning=ReasoningConfig(effort="medium"),
                )
            )
            print(response.choices[0].message.content)
        """
        body = params.model_dump(exclude_none=True)
        body["stream"] = False
        data = self._http.post("/v1/responses", body)
        return ResponsesResponse.model_validate(data)

    def stream(self, params: ResponsesParams) -> Iterator[ChatCompletionChunk]:
        """Streaming response. Returns an iterator of SSE chunks.

        The chunk format is identical to chat/completions streaming.

        Streams do NOT retry on failure. Catch MeshAPIError and restart
        a new request if reconnection is needed.

        Example::

            for chunk in client.responses.stream(
                ResponsesParams(
                    model="openai/o4-mini",
                    input=[ChatMessage(role="user", content="Tell me a story.")],
                )
            ):
                print(chunk.choices[0].delta.content or "", end="", flush=True)
        """
        body = params.model_dump(exclude_none=True)
        body["stream"] = True
        yield from self._http.stream("/v1/responses", body)


class AsyncResponsesResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def create(self, params: ResponsesParams) -> ResponsesResponse:
        """Non-streaming response.

        Example::

            response = await client.responses.create(
                ResponsesParams(
                    model="openai/o4-mini",
                    input="Explain the halting problem simply.",
                    reasoning=ReasoningConfig(effort="medium"),
                )
            )
            print(response.choices[0].message.content)
        """
        body = params.model_dump(exclude_none=True)
        body["stream"] = False
        data = await self._http.post("/v1/responses", body)
        return ResponsesResponse.model_validate(data)

    async def stream(self, params: ResponsesParams) -> AsyncIterator[ChatCompletionChunk]:
        """Streaming response. Returns an async iterator of SSE chunks.

        Example::

            async for chunk in client.responses.stream(
                ResponsesParams(
                    model="openai/o4-mini",
                    input=[ChatMessage(role="user", content="Tell me a story.")],
                )
            ):
                print(chunk.choices[0].delta.content or "", end="", flush=True)
        """
        body = params.model_dump(exclude_none=True)
        body["stream"] = True
        async for chunk in self._http.stream("/v1/responses", body):
            yield chunk
