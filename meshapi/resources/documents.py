"""Documents resource — /v1/documents endpoints."""

from __future__ import annotations

from typing import Optional
from urllib.parse import quote

from .._http import AsyncHttpClient, SyncHttpClient
from .._types import (
    DocumentListResponse,
    DocumentResponse,
    GenerateDocumentRequest,
    ListDocumentsParams,
)


class DocumentsResource:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def generate(self, params: GenerateDocumentRequest) -> DocumentResponse:
        """POST /v1/documents/generate — generate a document."""
        data = self._http.post("/v1/documents/generate", params.model_dump(exclude_none=True))
        return DocumentResponse.model_validate(data)

    def list(self, params: Optional[ListDocumentsParams] = None) -> DocumentListResponse:
        """GET /v1/documents — list documents."""
        query = None
        if params is not None:
            query = {k: str(v) for k, v in params.model_dump(exclude_none=True).items()} or None
        data = self._http.get("/v1/documents", params=query)
        return DocumentListResponse.model_validate(data)

    def retrieve(self, document_id: str) -> DocumentResponse:
        """GET /v1/documents/{document_id} — get a document."""
        data = self._http.get(f"/v1/documents/{quote(document_id, safe='')}")
        return DocumentResponse.model_validate(data)


class AsyncDocumentsResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def generate(self, params: GenerateDocumentRequest) -> DocumentResponse:
        """POST /v1/documents/generate — generate a document."""
        data = await self._http.post("/v1/documents/generate", params.model_dump(exclude_none=True))
        return DocumentResponse.model_validate(data)

    async def list(self, params: Optional[ListDocumentsParams] = None) -> DocumentListResponse:
        """GET /v1/documents — list documents."""
        query = None
        if params is not None:
            query = {k: str(v) for k, v in params.model_dump(exclude_none=True).items()} or None
        data = await self._http.get("/v1/documents", params=query)
        return DocumentListResponse.model_validate(data)

    async def retrieve(self, document_id: str) -> DocumentResponse:
        """GET /v1/documents/{document_id} — get a document."""
        data = await self._http.get(f"/v1/documents/{quote(document_id, safe='')}")
        return DocumentResponse.model_validate(data)
