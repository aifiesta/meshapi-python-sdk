"""Templates resource — CRUD on /v1/templates."""

from __future__ import annotations

from typing import List, Optional

from .._http import AsyncHttpClient, SyncHttpClient
from .._types import CreateTemplateParams, TemplateSummary, UpdateTemplateParams


class TemplatesResource:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def create(
        self, params: CreateTemplateParams, *, request_id: Optional[str] = None
    ) -> TemplateSummary:
        data = self._http.post(
            "/v1/templates", params.model_dump(exclude_none=True), request_id=request_id
        )
        return TemplateSummary.model_validate(data)

    def list(self, *, request_id: Optional[str] = None) -> List[TemplateSummary]:
        data = self._http.get("/v1/templates", request_id=request_id)
        return [TemplateSummary.model_validate(t) for t in (data or [])]

    def get(self, template_id: str, *, request_id: Optional[str] = None) -> TemplateSummary:
        data = self._http.get(f"/v1/templates/{template_id}", request_id=request_id)
        return TemplateSummary.model_validate(data)

    def update(
        self,
        template_id: str,
        params: UpdateTemplateParams,
        *,
        request_id: Optional[str] = None,
    ) -> TemplateSummary:
        data = self._http.patch(
            f"/v1/templates/{template_id}", params.model_dump(exclude_none=True),
            request_id=request_id,
        )
        return TemplateSummary.model_validate(data)

    def delete(self, template_id: str, *, request_id: Optional[str] = None) -> None:
        self._http.delete(f"/v1/templates/{template_id}", request_id=request_id)


class AsyncTemplatesResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def create(
        self, params: CreateTemplateParams, *, request_id: Optional[str] = None
    ) -> TemplateSummary:
        data = await self._http.post(
            "/v1/templates", params.model_dump(exclude_none=True), request_id=request_id
        )
        return TemplateSummary.model_validate(data)

    async def list(self, *, request_id: Optional[str] = None) -> List[TemplateSummary]:
        data = await self._http.get("/v1/templates", request_id=request_id)
        return [TemplateSummary.model_validate(t) for t in (data or [])]

    async def get(
        self, template_id: str, *, request_id: Optional[str] = None
    ) -> TemplateSummary:
        data = await self._http.get(f"/v1/templates/{template_id}", request_id=request_id)
        return TemplateSummary.model_validate(data)

    async def update(
        self,
        template_id: str,
        params: UpdateTemplateParams,
        *,
        request_id: Optional[str] = None,
    ) -> TemplateSummary:
        data = await self._http.patch(
            f"/v1/templates/{template_id}", params.model_dump(exclude_none=True),
            request_id=request_id,
        )
        return TemplateSummary.model_validate(data)

    async def delete(self, template_id: str, *, request_id: Optional[str] = None) -> None:
        await self._http.delete(f"/v1/templates/{template_id}", request_id=request_id)
