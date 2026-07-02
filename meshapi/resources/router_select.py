"""Router resource — POST /v1/router/select.

Select-only Auto Router: returns the model the Auto Router *would* pick for a
prompt without running inference, so the caller can run inference on its own
path. Gated server-side by ``AUTO_ROUTER_ENABLED``. Fail-soft: on classification
failure the router returns the configured default model with
``auto_router.fallback_used = True`` rather than erroring.
"""

from __future__ import annotations

from .._http import AsyncHttpClient, SyncHttpClient
from .._types import RouterSelectParams, RouterSelectResponse


class RouterResource:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def select(self, params: RouterSelectParams) -> RouterSelectResponse:
        data = self._http.post("/v1/router/select", params.model_dump(exclude_none=True))
        return RouterSelectResponse.model_validate(data)


class AsyncRouterResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def select(self, params: RouterSelectParams) -> RouterSelectResponse:
        data = await self._http.post("/v1/router/select", params.model_dump(exclude_none=True))
        return RouterSelectResponse.model_validate(data)
