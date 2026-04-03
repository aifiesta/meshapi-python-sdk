"""Models resource — GET /v1/models, /v1/models/free, /v1/models/paid."""

from __future__ import annotations

from typing import List, Optional

from .._http import AsyncHttpClient, SyncHttpClient
from .._types import ModelInfo


class ModelsResource:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def list(self, *, free: Optional[bool] = None) -> List[ModelInfo]:
        params = {}
        if free is not None:
            params["free"] = str(free).lower()
        data = self._http.get("/v1/models", params=params or None)
        return [ModelInfo.model_validate(m) for m in (data or [])]

    def free(self) -> List[ModelInfo]:
        data = self._http.get("/v1/models/free")
        return [ModelInfo.model_validate(m) for m in (data or [])]

    def paid(self) -> List[ModelInfo]:
        data = self._http.get("/v1/models/paid")
        return [ModelInfo.model_validate(m) for m in (data or [])]


class AsyncModelsResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def list(self, *, free: Optional[bool] = None) -> List[ModelInfo]:
        params = {}
        if free is not None:
            params["free"] = str(free).lower()
        data = await self._http.get("/v1/models", params=params or None)
        return [ModelInfo.model_validate(m) for m in (data or [])]

    async def free(self) -> List[ModelInfo]:
        data = await self._http.get("/v1/models/free")
        return [ModelInfo.model_validate(m) for m in (data or [])]

    async def paid(self) -> List[ModelInfo]:
        data = await self._http.get("/v1/models/paid")
        return [ModelInfo.model_validate(m) for m in (data or [])]
