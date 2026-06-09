"""Videos resource — /v1/video/generations endpoints."""

from __future__ import annotations

from typing import Optional

from .._http import AsyncHttpClient, SyncHttpClient
from .._types import (
    CreateVideoGenerationResponse,
    ListVideoGenerationsParams,
    VideoGenerationParams,
    VideoTaskListResponse,
    VideoTaskResponse,
)


class VideosResource:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def generate(self, params: VideoGenerationParams) -> CreateVideoGenerationResponse:
        """POST /v1/video/generations — submit a video generation task."""
        data = self._http.post("/v1/video/generations", params.model_dump(exclude_none=True))
        return CreateVideoGenerationResponse.model_validate(data)

    def list(self, params: Optional[ListVideoGenerationsParams] = None) -> VideoTaskListResponse:
        """GET /v1/video/generations — list video generation tasks."""
        query = None
        if params is not None:
            query = {k: str(v) for k, v in params.model_dump(exclude_none=True).items()} or None
        data = self._http.get("/v1/video/generations", params=query)
        return VideoTaskListResponse.model_validate(data)

    def retrieve(self, task_id: str) -> VideoTaskResponse:
        """GET /v1/video/generations/{task_id} — get a video generation task."""
        data = self._http.get(f"/v1/video/generations/{task_id}")
        return VideoTaskResponse.model_validate(data)


class AsyncVideosResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def generate(self, params: VideoGenerationParams) -> CreateVideoGenerationResponse:
        data = await self._http.post("/v1/video/generations", params.model_dump(exclude_none=True))
        return CreateVideoGenerationResponse.model_validate(data)

    async def list(self, params: Optional[ListVideoGenerationsParams] = None) -> VideoTaskListResponse:
        query = None
        if params is not None:
            query = {k: str(v) for k, v in params.model_dump(exclude_none=True).items()} or None
        data = await self._http.get("/v1/video/generations", params=query)
        return VideoTaskListResponse.model_validate(data)

    async def retrieve(self, task_id: str) -> VideoTaskResponse:
        data = await self._http.get(f"/v1/video/generations/{task_id}")
        return VideoTaskResponse.model_validate(data)
