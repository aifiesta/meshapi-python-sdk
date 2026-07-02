"""Models resource — GET /v1/models[/free|/paid|/search|/{model_id}]."""

from __future__ import annotations

from typing import List, Literal, Optional
from urllib.parse import quote

from .._http import AsyncHttpClient, SyncHttpClient
from .._types import ModelInfo, ModelSearchParams, ModelsPage


class ModelsResource:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def list(
        self,
        *,
        free: Optional[bool] = None,
        type: Optional[Literal["text", "embedding", "image", "audio", "video"]] = None,
        provider: Optional[str] = None,
    ) -> List[ModelInfo]:
        params = {}
        if free is not None:
            params["free"] = str(free).lower()
        if type is not None:
            params["type"] = type
        if provider is not None:
            params["provider"] = provider
        data = self._http.get("/v1/models", params=params or None)
        return [ModelInfo.model_validate(m) for m in (data or [])]

    def free(self) -> List[ModelInfo]:
        data = self._http.get("/v1/models/free")
        return [ModelInfo.model_validate(m) for m in (data or [])]

    def paid(self) -> List[ModelInfo]:
        data = self._http.get("/v1/models/paid")
        return [ModelInfo.model_validate(m) for m in (data or [])]

    def search(self, params: Optional[ModelSearchParams] = None) -> ModelsPage:
        qs = (params or ModelSearchParams()).model_dump(exclude_none=True)
        data = self._http.get("/v1/models/search", params=qs or None)
        return ModelsPage.model_validate(data)

    def get(self, model_id: str) -> ModelInfo:
        # Encode special chars but keep "/" — the backend route is
        # /v1/models/{model_id:path}, so provider-prefixed ids like
        # "openai/gpt-4o" stay a single path parameter.
        data = self._http.get(f"/v1/models/{quote(model_id, safe='/')}")
        return ModelInfo.model_validate(data)


class AsyncModelsResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def list(
        self,
        *,
        free: Optional[bool] = None,
        type: Optional[Literal["text", "embedding", "image", "audio", "video"]] = None,
        provider: Optional[str] = None,
    ) -> List[ModelInfo]:
        params = {}
        if free is not None:
            params["free"] = str(free).lower()
        if type is not None:
            params["type"] = type
        if provider is not None:
            params["provider"] = provider
        data = await self._http.get("/v1/models", params=params or None)
        return [ModelInfo.model_validate(m) for m in (data or [])]

    async def free(self) -> List[ModelInfo]:
        data = await self._http.get("/v1/models/free")
        return [ModelInfo.model_validate(m) for m in (data or [])]

    async def paid(self) -> List[ModelInfo]:
        data = await self._http.get("/v1/models/paid")
        return [ModelInfo.model_validate(m) for m in (data or [])]

    async def search(self, params: Optional[ModelSearchParams] = None) -> ModelsPage:
        qs = (params or ModelSearchParams()).model_dump(exclude_none=True)
        data = await self._http.get("/v1/models/search", params=qs or None)
        return ModelsPage.model_validate(data)

    async def get(self, model_id: str) -> ModelInfo:
        # See sync get(): keep "/" for the {model_id:path} route.
        data = await self._http.get(f"/v1/models/{quote(model_id, safe='/')}")
        return ModelInfo.model_validate(data)
