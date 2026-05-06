"""Compare resource — POST /v1/chat/compare."""

from __future__ import annotations

from typing import AsyncIterator, Iterator

from .._http import AsyncHttpClient, SyncHttpClient
from .._types import CompareParams, CompareResponse, CompareStreamEvent


class CompareResource:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def create(self, params: CompareParams) -> CompareResponse:
        body = params.model_dump(exclude_none=True)
        if body.get("stream"):
            raise ValueError("Use stream() for streaming compare requests.")
        data = self._http.post("/v1/chat/compare", body)
        return CompareResponse.model_validate(data)

    def stream(self, params: CompareParams) -> Iterator[CompareStreamEvent]:
        body = params.model_dump(exclude_none=True)
        body["stream"] = True
        yield from self._http.stream_json("/v1/chat/compare", body, CompareStreamEvent)


class AsyncCompareResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def create(self, params: CompareParams) -> CompareResponse:
        body = params.model_dump(exclude_none=True)
        if body.get("stream"):
            raise ValueError("Use stream() for streaming compare requests.")
        data = await self._http.post("/v1/chat/compare", body)
        return CompareResponse.model_validate(data)

    async def stream(self, params: CompareParams) -> AsyncIterator[CompareStreamEvent]:
        body = params.model_dump(exclude_none=True)
        body["stream"] = True
        async for event in self._http.stream_json("/v1/chat/compare", body, CompareStreamEvent):
            yield event
