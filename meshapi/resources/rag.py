"""RAG resource — /v1/files endpoints for retrieval-augmented generation."""

from __future__ import annotations

from typing import Optional

from .._http import AsyncHttpClient, SyncHttpClient
from .._types import (
    BulkEmbedRequest,
    BulkEmbedResponse,
    InitUploadRequest,
    InitUploadResponse,
    RagFileListResponse,
    RagFileStatus,
    SearchRequest,
    SearchResponse,
)


class RagResource:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def init_upload(self, params: InitUploadRequest) -> InitUploadResponse:
        data = self._http.post("/v1/files", params.model_dump(exclude_none=True))
        return InitUploadResponse.model_validate(data)

    def list(self, limit: Optional[int] = None, offset: Optional[int] = None) -> RagFileListResponse:
        query: dict = {}
        if limit is not None:
            query["limit"] = limit
        if offset is not None:
            query["offset"] = offset
        data = self._http.get("/v1/files", params=query if query else None)
        return RagFileListResponse.model_validate(data)

    def get(self, file_id: str) -> RagFileStatus:
        data = self._http.get(f"/v1/files/{file_id}")
        return RagFileStatus.model_validate(data)

    def embed(self, params: BulkEmbedRequest) -> BulkEmbedResponse:
        data = self._http.post("/v1/files/embed", params.model_dump(exclude_none=True))
        return BulkEmbedResponse.model_validate(data)

    def search(self, params: SearchRequest) -> SearchResponse:
        data = self._http.post("/v1/files/search", params.model_dump(exclude_none=True))
        return SearchResponse.model_validate(data)


class AsyncRagResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def init_upload(self, params: InitUploadRequest) -> InitUploadResponse:
        data = await self._http.post("/v1/files", params.model_dump(exclude_none=True))
        return InitUploadResponse.model_validate(data)

    async def list(self, limit: Optional[int] = None, offset: Optional[int] = None) -> RagFileListResponse:
        query: dict = {}
        if limit is not None:
            query["limit"] = limit
        if offset is not None:
            query["offset"] = offset
        data = await self._http.get("/v1/files", params=query if query else None)
        return RagFileListResponse.model_validate(data)

    async def get(self, file_id: str) -> RagFileStatus:
        data = await self._http.get(f"/v1/files/{file_id}")
        return RagFileStatus.model_validate(data)

    async def embed(self, params: BulkEmbedRequest) -> BulkEmbedResponse:
        data = await self._http.post("/v1/files/embed", params.model_dump(exclude_none=True))
        return BulkEmbedResponse.model_validate(data)

    async def search(self, params: SearchRequest) -> SearchResponse:
        data = await self._http.post("/v1/files/search", params.model_dump(exclude_none=True))
        return SearchResponse.model_validate(data)
