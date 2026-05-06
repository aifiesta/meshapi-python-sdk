"""Responses resource — POST /v1/responses."""

from __future__ import annotations

from typing import AsyncIterator, Iterator

from .._http import AsyncHttpClient, SyncHttpClient
from .._types import ResponsesParams, ResponsesResponse, ResponsesStreamEvent


class ResponsesResource:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def create(self, params: ResponsesParams) -> ResponsesResponse:
        body = params.model_dump(exclude_none=True)
        if body.get("stream"):
            raise ValueError("Use stream() for streaming responses requests.")
        data = self._http.post("/v1/responses", body)
        return ResponsesResponse.model_validate(data)

    def stream(self, params: ResponsesParams) -> Iterator[ResponsesStreamEvent]:
        body = params.model_dump(exclude_none=True)
        body["stream"] = True
        yield from self._http.stream_json("/v1/responses", body, ResponsesStreamEvent)


class AsyncResponsesResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def create(self, params: ResponsesParams) -> ResponsesResponse:
        body = params.model_dump(exclude_none=True)
        if body.get("stream"):
            raise ValueError("Use stream() for streaming responses requests.")
        data = await self._http.post("/v1/responses", body)
        return ResponsesResponse.model_validate(data)

    async def stream(self, params: ResponsesParams) -> AsyncIterator[ResponsesStreamEvent]:
        body = params.model_dump(exclude_none=True)
        body["stream"] = True
        async for event in self._http.stream_json("/v1/responses", body, ResponsesStreamEvent):
            yield event
