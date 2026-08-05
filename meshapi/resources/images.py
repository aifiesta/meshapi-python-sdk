"""Images resource — POST /v1/images/generations, POST /v1/images/edits."""

from __future__ import annotations

from typing import AsyncIterator, Iterator, Optional

from .._http import AsyncHttpClient, SyncHttpClient
from .._types import (
    ImageEditParams,
    ImageGenerationChunk,
    ImageGenerationParams,
    ImageGenerationResponse,
)


class ImagesResource:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def generate(
        self, params: ImageGenerationParams, *, request_id: Optional[str] = None
    ) -> ImageGenerationResponse:
        data = self._http.post(
            "/v1/images/generations", params.model_dump(exclude_none=True), request_id=request_id
        )
        return ImageGenerationResponse.model_validate(data)

    def edit(
        self, params: ImageEditParams, *, request_id: Optional[str] = None
    ) -> ImageGenerationResponse:
        data = self._http.post(
            "/v1/images/edits", params.model_dump(exclude_none=True), request_id=request_id
        )
        return ImageGenerationResponse.model_validate(data)

    def stream(
        self, params: ImageGenerationParams, *, request_id: Optional[str] = None
    ) -> Iterator[ImageGenerationChunk]:
        body = params.model_dump(exclude_none=True)
        body["stream"] = True
        return self._http.stream_json(
            "/v1/images/generations", body, ImageGenerationChunk, request_id=request_id
        )


class AsyncImagesResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def generate(
        self, params: ImageGenerationParams, *, request_id: Optional[str] = None
    ) -> ImageGenerationResponse:
        data = await self._http.post(
            "/v1/images/generations", params.model_dump(exclude_none=True), request_id=request_id
        )
        return ImageGenerationResponse.model_validate(data)

    async def edit(
        self, params: ImageEditParams, *, request_id: Optional[str] = None
    ) -> ImageGenerationResponse:
        data = await self._http.post(
            "/v1/images/edits", params.model_dump(exclude_none=True), request_id=request_id
        )
        return ImageGenerationResponse.model_validate(data)

    def stream(
        self, params: ImageGenerationParams, *, request_id: Optional[str] = None
    ) -> AsyncIterator[ImageGenerationChunk]:
        body = params.model_dump(exclude_none=True)
        body["stream"] = True
        return self._http.stream_json(
            "/v1/images/generations", body, ImageGenerationChunk, request_id=request_id
        )

