"""Moderations resource — POST /v1/moderations."""

from __future__ import annotations

from .._http import AsyncHttpClient, SyncHttpClient
from .._types import ModerationParams, ModerationResponse


class ModerationsResource:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def create(self, params: ModerationParams) -> ModerationResponse:
        data = self._http.post("/v1/moderations", params.model_dump(exclude_none=True))
        return ModerationResponse.model_validate(data)


class AsyncModerationsResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def create(self, params: ModerationParams) -> ModerationResponse:
        data = await self._http.post("/v1/moderations", params.model_dump(exclude_none=True))
        return ModerationResponse.model_validate(data)
