"""RAG resource — /v1/files endpoints for retrieval-augmented generation."""

from __future__ import annotations

from typing import Any, Dict, Optional
from urllib.parse import quote

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

    def init_upload(
        self, params: InitUploadRequest, *, request_id: Optional[str] = None
    ) -> InitUploadResponse:
        data = self._http.post(
            "/v1/files", params.model_dump(exclude_none=True), request_id=request_id
        )
        return InitUploadResponse.model_validate(data)

    def list(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        *,
        request_id: Optional[str] = None,
    ) -> RagFileListResponse:
        query: dict = {}
        if limit is not None:
            query["limit"] = limit
        if offset is not None:
            query["offset"] = offset
        data = self._http.get(
            "/v1/files", params=query if query else None, request_id=request_id
        )
        return RagFileListResponse.model_validate(data)

    def get(self, file_id: str, *, request_id: Optional[str] = None) -> RagFileStatus:
        data = self._http.get(
            f"/v1/files/{quote(file_id, safe='')}", request_id=request_id
        )
        return RagFileStatus.model_validate(data)

    def embed(
        self, params: BulkEmbedRequest, *, request_id: Optional[str] = None
    ) -> BulkEmbedResponse:
        data = self._http.post(
            "/v1/files/embed", params.model_dump(exclude_none=True), request_id=request_id
        )
        return BulkEmbedResponse.model_validate(data)

    def search(
        self, params: SearchRequest, *, request_id: Optional[str] = None
    ) -> SearchResponse:
        data = self._http.post(
            "/v1/files/search", params.model_dump(exclude_none=True), request_id=request_id
        )
        return SearchResponse.model_validate(data)

    def upload_file(
        self,
        *,
        file_name: str,
        mime_type: str,
        content: bytes,
        embed: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> InitUploadResponse:
        """Convenience wrapper: calls init_upload then PUTs the file content to
        the signed URL in one step. Returns the InitUploadResponse with file_id."""
        upload = self.init_upload(
            InitUploadRequest(file_name=file_name, mime_type=mime_type, embed=embed, metadata=metadata),
            request_id=request_id,
        )
        # Use the configured httpx client so proxy/transport/TLS settings are honoured.
        # Signed URLs are absolute — httpx accepts them even when base_url is set.
        # Do NOT send Authorization header (the signed URL is pre-authenticated).
        resp = self._http._client.put(
            upload.signed_url,
            content=content,
            headers={"Content-Type": mime_type},
            timeout=self._http._config.timeout,
        )
        resp.raise_for_status()
        return upload


class AsyncRagResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def init_upload(
        self, params: InitUploadRequest, *, request_id: Optional[str] = None
    ) -> InitUploadResponse:
        data = await self._http.post(
            "/v1/files", params.model_dump(exclude_none=True), request_id=request_id
        )
        return InitUploadResponse.model_validate(data)

    async def list(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        *,
        request_id: Optional[str] = None,
    ) -> RagFileListResponse:
        query: dict = {}
        if limit is not None:
            query["limit"] = limit
        if offset is not None:
            query["offset"] = offset
        data = await self._http.get(
            "/v1/files", params=query if query else None, request_id=request_id
        )
        return RagFileListResponse.model_validate(data)

    async def get(self, file_id: str, *, request_id: Optional[str] = None) -> RagFileStatus:
        data = await self._http.get(
            f"/v1/files/{quote(file_id, safe='')}", request_id=request_id
        )
        return RagFileStatus.model_validate(data)

    async def embed(
        self, params: BulkEmbedRequest, *, request_id: Optional[str] = None
    ) -> BulkEmbedResponse:
        data = await self._http.post(
            "/v1/files/embed", params.model_dump(exclude_none=True), request_id=request_id
        )
        return BulkEmbedResponse.model_validate(data)

    async def search(
        self, params: SearchRequest, *, request_id: Optional[str] = None
    ) -> SearchResponse:
        data = await self._http.post(
            "/v1/files/search", params.model_dump(exclude_none=True), request_id=request_id
        )
        return SearchResponse.model_validate(data)

    async def upload_file(
        self,
        *,
        file_name: str,
        mime_type: str,
        content: bytes,
        embed: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> InitUploadResponse:
        """Convenience wrapper: calls init_upload then PUTs the file content to
        the signed URL in one step. Returns the InitUploadResponse with file_id."""
        upload = await self.init_upload(
            InitUploadRequest(file_name=file_name, mime_type=mime_type, embed=embed, metadata=metadata),
            request_id=request_id,
        )
        # Use the configured async httpx client so proxy/transport/TLS settings are honoured.
        # Signed URLs are absolute — httpx accepts them even when base_url is set.
        # Do NOT send Authorization header (the signed URL is pre-authenticated).
        resp = await self._http._client.put(
            upload.signed_url,
            content=content,
            headers={"Content-Type": mime_type},
            timeout=self._http._config.timeout,
        )
        resp.raise_for_status()
        return upload
