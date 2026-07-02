"""Images resource — POST /v1/images/generations, POST /v1/images/edits."""

from __future__ import annotations

from typing import AsyncIterator, Iterator

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

    def generate(self, params: ImageGenerationParams) -> ImageGenerationResponse:
        data = self._http.post("/v1/images/generations", params.model_dump(exclude_none=True))
        return ImageGenerationResponse.model_validate(data)

    def edit(self, params: ImageEditParams) -> ImageGenerationResponse:
        data = self._http.post("/v1/images/edits", params.model_dump(exclude_none=True))
        return ImageGenerationResponse.model_validate(data)

    def stream(self, params: ImageGenerationParams) -> Iterator[ImageGenerationChunk]:
        body = params.model_dump(exclude_none=True)
        body["stream"] = True
        yield from self._http.stream_json("/v1/images/generations", body, ImageGenerationChunk)


class AsyncImagesResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def generate(self, params: ImageGenerationParams) -> ImageGenerationResponse:
        data = await self._http.post("/v1/images/generations", params.model_dump(exclude_none=True))
        return ImageGenerationResponse.model_validate(data)

    async def edit(self, params: ImageEditParams) -> ImageGenerationResponse:
        data = await self._http.post("/v1/images/edits", params.model_dump(exclude_none=True))
        return ImageGenerationResponse.model_validate(data)

    async def stream(self, params: ImageGenerationParams) -> AsyncIterator[ImageGenerationChunk]:
        body = params.model_dump(exclude_none=True)
        body["stream"] = True
        async for event in self._http.stream_json("/v1/images/generations", body, ImageGenerationChunk):
            yield event

