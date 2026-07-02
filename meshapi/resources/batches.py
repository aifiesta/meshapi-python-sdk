"""Batch resource — /v1/batches endpoints."""

from __future__ import annotations

from urllib.parse import quote

from .._http import AsyncHttpClient, SyncHttpClient
from .._types import BatchListResponse, BatchObject, CreateBatchParams


class BatchesResource:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def create(self, params: CreateBatchParams) -> BatchObject:
        data = self._http.post("/v1/batches", params.model_dump(exclude_none=True))
        return BatchObject.model_validate(data)

    def list(self, *, after: str | None = None, limit: int | None = None) -> BatchListResponse:
        query = {}
        if after is not None:
            query["after"] = after
        if limit is not None:
            query["limit"] = str(limit)
        data = self._http.get("/v1/batches", params=query or None)
        return BatchListResponse.model_validate(data)

    def get(self, batch_id: str) -> BatchObject:
        data = self._http.get(f"/v1/batches/{quote(batch_id, safe='')}")
        return BatchObject.model_validate(data)

    def cancel(self, batch_id: str) -> BatchObject:
        data = self._http.post(f"/v1/batches/{quote(batch_id, safe='')}/cancel", {})
        return BatchObject.model_validate(data)


class AsyncBatchesResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def create(self, params: CreateBatchParams) -> BatchObject:
        data = await self._http.post("/v1/batches", params.model_dump(exclude_none=True))
        return BatchObject.model_validate(data)

    async def list(
        self, *, after: str | None = None, limit: int | None = None
    ) -> BatchListResponse:
        query = {}
        if after is not None:
            query["after"] = after
        if limit is not None:
            query["limit"] = str(limit)
        data = await self._http.get("/v1/batches", params=query or None)
        return BatchListResponse.model_validate(data)

    async def get(self, batch_id: str) -> BatchObject:
        data = await self._http.get(f"/v1/batches/{quote(batch_id, safe='')}")
        return BatchObject.model_validate(data)

    async def cancel(self, batch_id: str) -> BatchObject:
        data = await self._http.post(f"/v1/batches/{quote(batch_id, safe='')}/cancel", {})
        return BatchObject.model_validate(data)
