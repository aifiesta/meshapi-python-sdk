"""HTTP client (sync + async) with retry/backoff and SSE parser."""

from __future__ import annotations

import asyncio
import json
import math
import random
import time
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, Iterator, Optional, Set, Type, TypeVar, Union

import httpx

from ._errors import RouterSvcApiError
from ._types import ChatCompletionChunk

T = TypeVar("T")

_RETRY_STATUS_CODES: Set[int] = {429, 502, 503, 504}
_DEFAULT_TIMEOUT = 60.0
_DEFAULT_MAX_RETRIES = 3
_BACKOFF_BASE_MS = 500
_BACKOFF_MAX_MS = 30_000

_SDK_VERSION_HEADER = "X-RouterSVC-SDK"
_SDK_VERSION_VALUE = "python/0.1.0"


@dataclass
class MeshAPIConfig:
    base_url: str
    token: str
    timeout: float = _DEFAULT_TIMEOUT
    max_retries: int = _DEFAULT_MAX_RETRIES
    httpx_client: Optional[httpx.Client] = field(default=None, repr=False)
    async_httpx_client: Optional[httpx.AsyncClient] = field(default=None, repr=False)

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip("/")


# ---------------------------------------------------------------------------
# SSE helpers
# ---------------------------------------------------------------------------


_DONE_SENTINEL = object()  # returned by _try_parse_sse_frame when [DONE] is seen


def _try_parse_sse_frame(frame: str) -> "Optional[Union[ChatCompletionChunk, object]]":
    """Parse one SSE frame string.

    Returns:
        ChatCompletionChunk on success
        _DONE_SENTINEL when [DONE] is received (caller should stop iteration)
        None for empty / comment-only frames
    Raises:
        RouterSvcApiError on mid-stream error frames
    """
    data_line: Optional[str] = None
    for line in frame.splitlines():
        if line.startswith("data: "):
            data_line = line[len("data: "):]
    if data_line is None or data_line.strip() == "":
        return None
    if data_line.strip() == "[DONE]":
        return _DONE_SENTINEL
    try:
        parsed = json.loads(data_line)
    except json.JSONDecodeError:
        return None

    if isinstance(parsed, dict) and "error" in parsed:
        err = parsed["error"]
        raise RouterSvcApiError(
            err.get("message", "upstream error"),
            status=0,
            error_code=err.get("code", "upstream_error"),
            request_id="",
        )

    return ChatCompletionChunk.model_validate(parsed)


def _iter_sse(response: httpx.Response) -> Iterator[ChatCompletionChunk]:
    """Sync SSE iterator with remainder-buffer handling. Stops on [DONE]."""
    remainder = ""
    try:
        for raw_bytes in response.iter_bytes():
            try:
                remainder += raw_bytes.decode("utf-8", errors="replace")
            except Exception:
                continue
            frames = remainder.split("\n\n")
            remainder = frames.pop()
            for frame in frames:
                if not frame.strip():
                    continue
                result = _try_parse_sse_frame(frame)
                if result is _DONE_SENTINEL:
                    return
                if result is not None:
                    yield result  # type: ignore[misc]
    except httpx.RemoteProtocolError as exc:
        raise RouterSvcApiError.stream_interrupted(str(exc)) from exc
    except httpx.StreamError as exc:
        raise RouterSvcApiError.stream_interrupted(str(exc)) from exc


async def _aiter_sse(response: httpx.Response) -> AsyncIterator[ChatCompletionChunk]:
    """Async SSE iterator with remainder-buffer handling. Stops on [DONE]."""
    remainder = ""
    try:
        async for raw_bytes in response.aiter_bytes():
            try:
                remainder += raw_bytes.decode("utf-8", errors="replace")
            except Exception:
                continue
            frames = remainder.split("\n\n")
            remainder = frames.pop()
            for frame in frames:
                if not frame.strip():
                    continue
                result = _try_parse_sse_frame(frame)
                if result is _DONE_SENTINEL:
                    return
                if result is not None:
                    yield result  # type: ignore[misc]
    except httpx.RemoteProtocolError as exc:
        raise RouterSvcApiError.stream_interrupted(str(exc)) from exc
    except httpx.StreamError as exc:
        raise RouterSvcApiError.stream_interrupted(str(exc)) from exc


# ---------------------------------------------------------------------------
# Retry helpers
# ---------------------------------------------------------------------------


def _compute_delay_s(attempt: int, retry_after: Optional[int]) -> float:
    """Exponential backoff with jitter, capped at _BACKOFF_MAX_MS."""
    if retry_after is not None:
        base = retry_after * 1000
    else:
        base = _BACKOFF_BASE_MS * (2 ** attempt)
    capped = min(base, _BACKOFF_MAX_MS)
    jittered = capped * (0.8 + random.random() * 0.4)  # ±20%
    return jittered / 1000.0


def _retry_after_from_response(response: httpx.Response) -> Optional[int]:
    val = response.headers.get("retry-after")
    if val is not None:
        try:
            return int(math.ceil(float(val)))
        except (ValueError, TypeError):
            pass
    return None


def _raise_for_status(response: httpx.Response) -> None:
    if response.status_code < 400:
        return
    raise RouterSvcApiError.from_response(response)


# ---------------------------------------------------------------------------
# Sync HTTP client
# ---------------------------------------------------------------------------


class SyncHttpClient:
    def __init__(self, config: MeshAPIConfig) -> None:
        self._config = config
        self._client = config.httpx_client or httpx.Client(
            base_url=config.base_url,
            timeout=config.timeout,
        )

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._config.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            _SDK_VERSION_HEADER: _SDK_VERSION_VALUE,
        }

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Any] = None,
        stream: bool = False,
    ) -> httpx.Response:
        kwargs: Dict[str, Any] = {
            "headers": self._headers(),
            "params": params,
        }
        if json_body is not None:
            kwargs["json"] = json_body

        for attempt in range(self._config.max_retries + 1):
            if stream:
                # Streaming: no retry, open the stream and return immediately
                req = self._client.request(method, path, **kwargs)
                _raise_for_status(req)
                return req

            response = self._client.request(method, path, **kwargs)
            if response.status_code in _RETRY_STATUS_CODES and attempt < self._config.max_retries:
                delay = _compute_delay_s(attempt, _retry_after_from_response(response))
                time.sleep(delay)
                continue
            _raise_for_status(response)
            return response

        # Should never reach here
        raise RuntimeError("unreachable")

    def get(self, path: str, *, params: Optional[Dict[str, Any]] = None) -> Any:
        response = self._request("GET", path, params=params)
        if response.status_code == 204:
            return None
        return response.json()

    def post(self, path: str, body: Any) -> Any:
        response = self._request("POST", path, json_body=body)
        if response.status_code == 204:
            return None
        return response.json()

    def patch(self, path: str, body: Any) -> Any:
        response = self._request("PATCH", path, json_body=body)
        if response.status_code == 204:
            return None
        return response.json()

    def delete(self, path: str) -> None:
        response = self._request("DELETE", path)
        if response.status_code == 204:
            return
        response.json()  # consume body; _raise_for_status already ran

    def stream(self, path: str, body: Any) -> Iterator[ChatCompletionChunk]:
        with self._client.stream("POST", path, json=body, headers=self._headers()) as response:
            _raise_for_status(response)
            yield from _iter_sse(response)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "SyncHttpClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


# ---------------------------------------------------------------------------
# Async HTTP client
# ---------------------------------------------------------------------------


class AsyncHttpClient:
    def __init__(self, config: MeshAPIConfig) -> None:
        self._config = config
        self._client = config.async_httpx_client or httpx.AsyncClient(
            base_url=config.base_url,
            timeout=config.timeout,
        )

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._config.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            _SDK_VERSION_HEADER: _SDK_VERSION_VALUE,
        }

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Any] = None,
    ) -> httpx.Response:
        kwargs: Dict[str, Any] = {
            "headers": self._headers(),
            "params": params,
        }
        if json_body is not None:
            kwargs["json"] = json_body

        for attempt in range(self._config.max_retries + 1):
            response = await self._client.request(method, path, **kwargs)
            if response.status_code in _RETRY_STATUS_CODES and attempt < self._config.max_retries:
                delay = _compute_delay_s(attempt, _retry_after_from_response(response))
                await asyncio.sleep(delay)
                continue
            _raise_for_status(response)
            return response

        raise RuntimeError("unreachable")

    async def get(self, path: str, *, params: Optional[Dict[str, Any]] = None) -> Any:
        response = await self._request("GET", path, params=params)
        if response.status_code == 204:
            return None
        return response.json()

    async def post(self, path: str, body: Any) -> Any:
        response = await self._request("POST", path, json_body=body)
        if response.status_code == 204:
            return None
        return response.json()

    async def patch(self, path: str, body: Any) -> Any:
        response = await self._request("PATCH", path, json_body=body)
        if response.status_code == 204:
            return None
        return response.json()

    async def delete(self, path: str) -> None:
        response = await self._request("DELETE", path)
        if response.status_code == 204:
            return

    async def stream(self, path: str, body: Any) -> AsyncIterator[ChatCompletionChunk]:
        async with self._client.stream(
            "POST", path, json=body, headers=self._headers()
        ) as response:
            _raise_for_status(response)
            async for chunk in _aiter_sse(response):
                yield chunk

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncHttpClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()
