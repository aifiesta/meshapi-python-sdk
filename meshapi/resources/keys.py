"""API key introspection: ``GET /v1/keys/{key_id}``."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from .._types_keys import ApiKeyDetails

__all__ = ["KeysResource", "AsyncKeysResource"]


def _key_path(key_id: str) -> str:
    if not isinstance(key_id, str) or not key_id.strip():
        raise ValueError("key_id must be a non-empty string")
    return f"/v1/keys/{quote(key_id, safe='')}"


def _to_dict(data: Any) -> Any:
    # The HTTP client may hand back parsed JSON or a response object.
    if hasattr(data, "json") and callable(data.json):
        return data.json()
    return data


class KeysResource:
    """Synchronous access to API key introspection."""

    def __init__(self, http: Any) -> None:
        self._http = http

    def retrieve(self, key_id: str) -> ApiKeyDetails:
        """Fetch a key's org, scopes, model access and effective limits.

        A data-plane key (``rsk_...``) can read only itself; any other id
        returns 404. An admin key or user session with ``keys:read`` can read
        any key within its scope; an out-of-scope key returns 403.

        Args:
            key_id: The id of the key to read.

        Returns:
            The key details. The secret and its hash are never returned.

        Raises:
            ValueError: If ``key_id`` is empty.
            MeshAPIError: On a non-2xx response (for example 403 or 404).
        """
        data = self._http.get(_key_path(key_id))
        return ApiKeyDetails.model_validate(_to_dict(data))


class AsyncKeysResource:
    """Asynchronous access to API key introspection."""

    def __init__(self, http: Any) -> None:
        self._http = http

    async def retrieve(self, key_id: str) -> ApiKeyDetails:
        """Fetch a key's org, scopes, model access and effective limits.

        See :meth:`KeysResource.retrieve` for access rules.

        Args:
            key_id: The id of the key to read.

        Returns:
            The key details. The secret and its hash are never returned.

        Raises:
            ValueError: If ``key_id`` is empty.
            MeshAPIError: On a non-2xx response (for example 403 or 404).
        """
        data = await self._http.get(_key_path(key_id))
        return ApiKeyDetails.model_validate(_to_dict(data))
