"""Moderations resource — POST /v1/moderations."""

from __future__ import annotations

from typing import Optional

from .._http import AsyncHttpClient, SyncHttpClient
from .._types import ModerationParams, ModerationResponse


class ModerationsResource:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def create(
        self, params: ModerationParams, *, request_id: Optional[str] = None
    ) -> ModerationResponse:
        data = self._http.post(
            "/v1/moderations", params.model_dump(exclude_none=True), request_id=request_id
        )
        return ModerationResponse.model_validate(data)


class AsyncModerationsResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def create(
        self, params: ModerationParams, *, request_id: Optional[str] = None
    ) -> ModerationResponse:
        data = await self._http.post(
            "/v1/moderations", params.model_dump(exclude_none=True), request_id=request_id
        )
        return ModerationResponse.model_validate(data)
