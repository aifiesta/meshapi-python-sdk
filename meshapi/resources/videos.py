"""Videos resource — POST /v1/video/generations, GET /v1/video/generations/{task_id}."""

from __future__ import annotations

from .._http import AsyncHttpClient, SyncHttpClient
from .._types import (
    VideoGenerationParams,
    VideoTaskResponse,
    CreateVideoGenerationResponse,
)


class VideosResource:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def create(self, params: VideoGenerationParams) -> CreateVideoGenerationResponse:
        """Submit a video generation task. Returns the task ID immediately."""
        data = self._http.post("/v1/video/generations", params.model_dump(exclude_none=True))
        return CreateVideoGenerationResponse.model_validate(data)

    def get(self, task_id: str) -> VideoTaskResponse:
        """Retrieve the current status (and result) of a video generation task."""
        data = self._http.get(f"/v1/video/generations/{task_id}")
        return VideoTaskResponse.model_validate(data)


class AsyncVideosResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def create(self, params: VideoGenerationParams) -> CreateVideoGenerationResponse:
        """Submit a video generation task. Returns the task ID immediately."""
        data = await self._http.post("/v1/video/generations", params.model_dump(exclude_none=True))
        return CreateVideoGenerationResponse.model_validate(data)

    async def get(self, task_id: str) -> VideoTaskResponse:
        """Retrieve the current status (and result) of a video generation task."""
        data = await self._http.get(f"/v1/video/generations/{task_id}")
        return VideoTaskResponse.model_validate(data)
