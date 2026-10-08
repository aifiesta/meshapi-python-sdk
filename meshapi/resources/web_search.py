"""Web search resource — POST /v1/web/search.

Gated server-side by ``WEB_SEARCH_ENABLED``; when disabled the endpoint returns
an error rather than a result. The native engine is tried first and failover to
another engine is opaque — inspect ``response.provider`` to see which one served.
Pinning ``provider`` turns failover off.

Set ``include_page_content`` to get each result's extracted page text alongside
the snippet. It is honoured by the tinyfish engine only, so pin that engine when
you need it — see ``WebSearchParams``.
"""

from __future__ import annotations

from .._http import AsyncHttpClient, SyncHttpClient
from .._types import WebSearchParams, WebSearchResponse


class WebResource:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def search(self, params: WebSearchParams) -> WebSearchResponse:
        data = self._http.post("/v1/web/search", params.model_dump(exclude_none=True))
        return WebSearchResponse.model_validate(data)


class AsyncWebResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def search(self, params: WebSearchParams) -> WebSearchResponse:
        data = await self._http.post("/v1/web/search", params.model_dump(exclude_none=True))
        return WebSearchResponse.model_validate(data)
