"""Responses resource — POST/GET /v1/responses, GET /v1/responses/{id},
POST /v1/responses/input_tokens."""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Iterator, Optional

from pydantic import BaseModel, ConfigDict

from .._http import AsyncHttpClient, SyncHttpClient
from .._types import (
    ResponsesListResponse,
    ResponsesParams,
    ResponsesResponse,
    ResponsesStreamEvent,
)


class ResponsesInputTokensResponse(BaseModel):
    """Result of ``POST /v1/responses/input_tokens``.

    Attributes:
        object: Object type, ``"response.input_tokens"``.
        input_tokens: Number of input tokens the request would consume.
    """

    model_config = ConfigDict(extra="allow")

    object: Optional[str] = None
    input_tokens: int


def _input_tokens_body(params: ResponsesParams) -> Dict[str, Any]:
    body = params.model_dump(exclude_none=True)
    # Counting never streams; the field has no meaning on this endpoint.
    body.pop("stream", None)
    return body


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

    def input_tokens(self, params: ResponsesParams) -> ResponsesInputTokensResponse:
        """Count the input tokens of a Responses request without running it.

        Sends the same body ``create()`` would send to
        ``POST /v1/responses/input_tokens``. No inference runs and nothing is
        billed. The count is provider-accurate where the provider offers a
        native counter and a local estimate otherwise.

        Args:
            params: The Responses request to count.

        Returns:
            The input token count.
        """
        data = self._http.post("/v1/responses/input_tokens", _input_tokens_body(params))
        return ResponsesInputTokensResponse.model_validate(data)

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

    async def input_tokens(self, params: ResponsesParams) -> ResponsesInputTokensResponse:
        """Count the input tokens of a Responses request without running it.

        Async variant of :meth:`ResponsesResource.input_tokens`. No inference
        runs and nothing is billed.

        Args:
            params: The Responses request to count.

        Returns:
            The input token count.
        """
        data = await self._http.post(
            "/v1/responses/input_tokens", _input_tokens_body(params)
        )
        return ResponsesInputTokensResponse.model_validate(data)

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
