"""Responses resource — POST/GET /v1/responses, GET /v1/responses/{id}."""

from __future__ import annotations

from typing import AsyncIterator, Iterator, Optional

from .._http import AsyncHttpClient, SyncHttpClient
from .._types import (
    ResponsesListResponse,
    ResponsesParams,
    ResponsesResponse,
    ResponsesStreamEvent,
)


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

    def list(
        self, *, after: Optional[str] = None, limit: Optional[int] = None
    ) -> ResponsesListResponse:
        params: dict = {}
        if after is not None:
            params["after"] = after
        if limit is not None:
            params["limit"] = limit
        data = self._http.get("/v1/responses", params=params or None)
        return ResponsesListResponse.model_validate(data)

    def get(self, response_id: str) -> ResponsesResponse:
        data = self._http.get(f"/v1/responses/{response_id}")
        return ResponsesResponse.model_validate(data)


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

    async def list(
        self, *, after: Optional[str] = None, limit: Optional[int] = None
    ) -> ResponsesListResponse:
        params: dict = {}
        if after is not None:
            params["after"] = after
        if limit is not None:
            params["limit"] = limit
        data = await self._http.get("/v1/responses", params=params or None)
        return ResponsesListResponse.model_validate(data)

    async def get(self, response_id: str) -> ResponsesResponse:
        data = await self._http.get(f"/v1/responses/{response_id}")
        return ResponsesResponse.model_validate(data)
