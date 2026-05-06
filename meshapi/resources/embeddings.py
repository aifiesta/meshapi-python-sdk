"""Embeddings resource — POST /v1/embeddings."""

from __future__ import annotations

from .._http import AsyncHttpClient, SyncHttpClient
from .._types import EmbeddingsParams, EmbeddingsResponse


class EmbeddingsResource:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def create(self, params: EmbeddingsParams) -> EmbeddingsResponse:
        data = self._http.post("/v1/embeddings", params.model_dump(exclude_none=True))
        return EmbeddingsResponse.model_validate(data)


class AsyncEmbeddingsResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def create(self, params: EmbeddingsParams) -> EmbeddingsResponse:
        data = await self._http.post("/v1/embeddings", params.model_dump(exclude_none=True))
        return EmbeddingsResponse.model_validate(data)
