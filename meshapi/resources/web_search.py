"""Web search resource — POST /v1/web/search.

Gated server-side by ``WEB_SEARCH_ENABLED``; when disabled the endpoint returns
an error rather than a result. Failover between the native engine and Tavily is
opaque — inspect ``response.provider`` to see which engine served the request.
"""

from __future__ import annotations

from typing import Optional

from .._http import AsyncHttpClient, SyncHttpClient
from .._types import WebSearchParams, WebSearchResponse


class WebResource:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def search(
        self, params: WebSearchParams, *, request_id: Optional[str] = None
    ) -> WebSearchResponse:
        data = self._http.post(
            "/v1/web/search", params.model_dump(exclude_none=True), request_id=request_id
        )
        return WebSearchResponse.model_validate(data)


class AsyncWebResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def search(
        self, params: WebSearchParams, *, request_id: Optional[str] = None
    ) -> WebSearchResponse:
        data = await self._http.post(
            "/v1/web/search", params.model_dump(exclude_none=True), request_id=request_id
        )
        return WebSearchResponse.model_validate(data)
