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

    def create(
        self, params: ResponsesParams, *, request_id: Optional[str] = None
    ) -> ResponsesResponse:
        body = params.model_dump(exclude_none=True)
        if body.get("stream"):
            raise ValueError("Use stream() for streaming responses requests.")
        data = self._http.post("/v1/responses", body, request_id=request_id)
        return ResponsesResponse.model_validate(data)

    def stream(
        self, params: ResponsesParams, *, request_id: Optional[str] = None
    ) -> Iterator[ResponsesStreamEvent]:
        body = params.model_dump(exclude_none=True)
        body["stream"] = True
        return self._http.stream_json(
            "/v1/responses", body, ResponsesStreamEvent, request_id=request_id
        )

    def list(
        self,
        *,
        after: Optional[str] = None,
        limit: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> ResponsesListResponse:
        params: dict = {}
        if after is not None:
            params["after"] = after
        if limit is not None:
            params["limit"] = limit
        data = self._http.get("/v1/responses", params=params or None, request_id=request_id)
        return ResponsesListResponse.model_validate(data)

    def get(self, response_id: str, *, request_id: Optional[str] = None) -> ResponsesResponse:
        data = self._http.get(f"/v1/responses/{response_id}", request_id=request_id)
        return ResponsesResponse.model_validate(data)


class AsyncResponsesResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def create(
        self, params: ResponsesParams, *, request_id: Optional[str] = None
    ) -> ResponsesResponse:
        body = params.model_dump(exclude_none=True)
        if body.get("stream"):
            raise ValueError("Use stream() for streaming responses requests.")
        data = await self._http.post("/v1/responses", body, request_id=request_id)
        return ResponsesResponse.model_validate(data)

    def stream(
        self, params: ResponsesParams, *, request_id: Optional[str] = None
    ) -> AsyncIterator[ResponsesStreamEvent]:
        body = params.model_dump(exclude_none=True)
        body["stream"] = True
        return self._http.stream_json(
            "/v1/responses", body, ResponsesStreamEvent, request_id=request_id
        )

    async def list(
        self,
        *,
        after: Optional[str] = None,
        limit: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> ResponsesListResponse:
        params: dict = {}
        if after is not None:
            params["after"] = after
        if limit is not None:
            params["limit"] = limit
        data = await self._http.get("/v1/responses", params=params or None, request_id=request_id)
        return ResponsesListResponse.model_validate(data)

    async def get(
        self, response_id: str, *, request_id: Optional[str] = None
    ) -> ResponsesResponse:
        data = await self._http.get(f"/v1/responses/{response_id}", request_id=request_id)
        return ResponsesResponse.model_validate(data)
