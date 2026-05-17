"""Images resource — POST /v1/images/generations."""

from __future__ import annotations

from .._http import AsyncHttpClient, SyncHttpClient
from .._types import ImageGenerationParams, ImageGenerationResponse


class ImagesResource:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def generate(self, params: ImageGenerationParams) -> ImageGenerationResponse:
        data = self._http.post("/v1/images/generations", params.model_dump(exclude_none=True))
        return ImageGenerationResponse.model_validate(data)


class AsyncImagesResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def generate(self, params: ImageGenerationParams) -> ImageGenerationResponse:
        data = await self._http.post("/v1/images/generations", params.model_dump(exclude_none=True))
        return ImageGenerationResponse.model_validate(data)
