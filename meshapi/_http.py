"""HTTP client (sync + async) with retry/backoff and SSE parser."""

from __future__ import annotations

import asyncio
import json
import math
import random
import re
import time
from dataclasses import dataclass, field
from typing import (
    Any,
    AsyncIterator,
    Dict,
    Iterator,
    Optional,
    Set,
    Type,
    TypeVar,
    Union,
)

import httpx

from ._errors import MeshAPIError
from ._types import ChatCompletionChunk

T = TypeVar("T")

_RETRY_STATUS_CODES: Set[int] = {429, 502, 503, 504}
_DEFAULT_TIMEOUT = 60.0
_DEFAULT_MAX_RETRIES = 3
_BACKOFF_BASE_MS = 500
_BACKOFF_MAX_MS = 30_000

_SDK_VERSION_HEADER = "X-MeshAPI-SDK"
_SDK_VERSION_VALUE = "python/0.1.11"

_REQUEST_ID_HEADER = "X-Request-Id"
_RESPONSE_REQUEST_ID_HEADER = "x-request-id"
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")


def validate_request_id(request_id: str) -> str:
    """Validate a caller-supplied request id.

    The backend only honours ids matching ``^[A-Za-z0-9._:-]{1,64}$`` and
    silently ignores anything else — so the SDK fails fast instead.
    """
    if not isinstance(request_id, str) or not _REQUEST_ID_PATTERN.match(request_id):
        raise ValueError(
            "Invalid request_id: must be 1-64 characters from [A-Za-z0-9._:-], "
            f"got {request_id!r}. The backend silently ignores invalid ids, so "
            "the SDK rejects them up front."
        )
    return request_id


class _DictPayload(dict):
    """A dict that can carry the server request id alongside the JSON payload."""

    meshapi_request_id: Optional[str] = None


class _ListPayload(list):
    """A list that can carry the server request id alongside the JSON payload."""

    meshapi_request_id: Optional[str] = None


def _attach_request_id(parsed: Any, response: httpx.Response) -> Any:
    """Wrap a parsed JSON payload so the X-Request-Id response header travels
    with it. ``MeshModel.model_validate`` picks it up and sets ``_request_id``
    on the resulting model. Top-level list elements are wrapped too so
    list-returning endpoints (e.g. models.list) also expose it per item."""
    server_request_id = response.headers.get(_RESPONSE_REQUEST_ID_HEADER)
    if server_request_id is None:
        return parsed
    if isinstance(parsed, dict):
        wrapped = _DictPayload(parsed)
        wrapped.meshapi_request_id = server_request_id
        return wrapped
    if isinstance(parsed, list):
        wrapped_items = _ListPayload(
            _attach_request_id(item, response) if isinstance(item, dict) else item
            for item in parsed
        )
        wrapped_items.meshapi_request_id = server_request_id
        return wrapped_items
    return parsed


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


def _extract_sse_data(frame: str) -> Optional[str]:
    data_lines = []
    for line in frame.splitlines():
        if line.startswith("data: "):
            data_lines.append(line[len("data: ") :])
    if not data_lines:
        return None
    return "\n".join(data_lines)


def _extract_sse_event(frame: str) -> Optional[str]:
    for line in frame.splitlines():
        if line.startswith("event: "):
            return line[len("event: ") :]
    return None


def _try_parse_sse_frame(frame: str) -> "Optional[Union[ChatCompletionChunk, object]]":
    """Parse one SSE frame string.

    Returns:
        ChatCompletionChunk on success
        _DONE_SENTINEL when [DONE] is received (caller should stop iteration)
        None for empty / comment-only frames
    Raises:
        MeshAPIError on mid-stream error frames
    """
    data_line = _extract_sse_data(frame)
    if data_line is None or data_line.strip() == "":
        return None
    if data_line.strip() == "[DONE]":
        return _DONE_SENTINEL
    try:
        parsed = json.loads(data_line)
    except json.JSONDecodeError:
        return None

    if isinstance(parsed, dict) and parsed.get("error") is not None:
        err = parsed["error"]
        if isinstance(err, dict):
            raise MeshAPIError(
                err.get("message", "upstream error"),
                status=0,
                error_code=err.get("code", "upstream_error"),
                request_id="",
            )
        else:
            raise MeshAPIError(
                str(err),
                status=0,
                error_code="upstream_error",
                request_id="",
            )

    sse_event = _extract_sse_event(frame)
    if isinstance(parsed, dict) and sse_event is not None:
        parsed["event"] = sse_event

    return ChatCompletionChunk.model_validate(parsed)


def _try_parse_json_sse_frame(
    frame: str, model_cls: Type[T]
) -> Optional[Union[T, object]]:
    data_line = _extract_sse_data(frame)
    if data_line is None or data_line.strip() == "":
        return None
    if data_line.strip() == "[DONE]":
        return _DONE_SENTINEL
    try:
        parsed = json.loads(data_line)
    except json.JSONDecodeError:
        return None
    if isinstance(parsed, dict) and parsed.get("error") is not None:
        err = parsed["error"]
        if isinstance(err, dict):
            raise MeshAPIError(
                err.get("message", "upstream error"),
                status=0,
                error_code=err.get("code", "upstream_error"),
                request_id="",
            )
        else:
            raise MeshAPIError(
                str(err),
                status=0,
                error_code="upstream_error",
                request_id="",
            )

    sse_event = _extract_sse_event(frame)
    if isinstance(parsed, dict) and sse_event is not None:
        parsed["event"] = sse_event

    return model_cls.model_validate(parsed)


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
        raise MeshAPIError.stream_interrupted(str(exc)) from exc
    except httpx.StreamError as exc:
        raise MeshAPIError.stream_interrupted(str(exc)) from exc


def _iter_json_sse(response: httpx.Response, model_cls: Type[T]) -> Iterator[T]:
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
                result = _try_parse_json_sse_frame(frame, model_cls)
                if result is _DONE_SENTINEL:
                    return
                if result is not None:
                    yield result
    except httpx.RemoteProtocolError as exc:
        raise MeshAPIError.stream_interrupted(str(exc)) from exc
    except httpx.StreamError as exc:
        raise MeshAPIError.stream_interrupted(str(exc)) from exc


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
        raise MeshAPIError.stream_interrupted(str(exc)) from exc
    except httpx.StreamError as exc:
        raise MeshAPIError.stream_interrupted(str(exc)) from exc


async def _aiter_json_sse(
    response: httpx.Response, model_cls: Type[T]
) -> AsyncIterator[T]:
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
                result = _try_parse_json_sse_frame(frame, model_cls)
                if result is _DONE_SENTINEL:
                    return
                if result is not None:
                    yield result
    except httpx.RemoteProtocolError as exc:
        raise MeshAPIError.stream_interrupted(str(exc)) from exc
    except httpx.StreamError as exc:
        raise MeshAPIError.stream_interrupted(str(exc)) from exc


# ---------------------------------------------------------------------------
# Retry helpers
# ---------------------------------------------------------------------------


def _compute_delay_s(attempt: int, retry_after: Optional[int]) -> float:
    """Exponential backoff with jitter, capped at _BACKOFF_MAX_MS."""
    if retry_after is not None:
        base = retry_after * 1000
    else:
        base = _BACKOFF_BASE_MS * (2**attempt)
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
    raise MeshAPIError.from_response(response)


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

    def _headers(self, request_id: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self._config.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            _SDK_VERSION_HEADER: _SDK_VERSION_VALUE,
        }
        if request_id is not None:
            headers[_REQUEST_ID_HEADER] = validate_request_id(request_id)
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Any] = None,
        stream: bool = False,
        request_id: Optional[str] = None,
    ) -> httpx.Response:
        kwargs: Dict[str, Any] = {
            "headers": self._headers(request_id),
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
            if (
                response.status_code in _RETRY_STATUS_CODES
                and attempt < self._config.max_retries
            ):
                delay = _compute_delay_s(attempt, _retry_after_from_response(response))
                time.sleep(delay)
                continue
            _raise_for_status(response)
            return response

        # Should never reach here
        raise RuntimeError("unreachable")

    def get(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> Any:
        response = self._request("GET", path, params=params, request_id=request_id)
        if response.status_code == 204:
            return None
        return _attach_request_id(response.json(), response)

    def post(self, path: str, body: Any, *, request_id: Optional[str] = None) -> Any:
        response = self._request("POST", path, json_body=body, request_id=request_id)
        if response.status_code == 204:
            return None
        return _attach_request_id(response.json(), response)

    def patch(self, path: str, body: Any, *, request_id: Optional[str] = None) -> Any:
        response = self._request("PATCH", path, json_body=body, request_id=request_id)
        if response.status_code == 204:
            return None
        return _attach_request_id(response.json(), response)

    def delete(self, path: str, *, request_id: Optional[str] = None) -> None:
        response = self._request("DELETE", path, request_id=request_id)
        if response.status_code == 204:
            return
        response.json()  # consume body; _raise_for_status already ran

    def get_bytes(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> bytes:
        response = self._request("GET", path, params=params, request_id=request_id)
        return response.content

    def post_bytes(self, path: str, body: Any, *, request_id: Optional[str] = None) -> bytes:
        response = self._request("POST", path, json_body=body, request_id=request_id)
        return response.content

    def post_multipart(self, path: str, fields: Dict[str, Any], file_data: Optional[tuple] = None, file_field: str = "file", request_id: Optional[str] = None) -> Any:
        headers = {k: v for k, v in self._headers(request_id).items() if k != "Content-Type"}
        files = None
        data = None
        if file_data is not None:
            files = {file_field: file_data}
            data = {k: str(v) for k, v in fields.items() if v is not None}
        else:
            data = {k: str(v) for k, v in fields.items() if v is not None}
        response = self._client.post(path, headers=headers, data=data, files=files)
        _raise_for_status(response)
        return _attach_request_id(response.json(), response)

    def stream(
        self, path: str, body: Any, *, request_id: Optional[str] = None
    ) -> Iterator[ChatCompletionChunk]:
        # Headers are built eagerly so an invalid request_id raises ValueError
        # before the stream generator is first iterated.
        headers = self._headers(request_id)
        return self._stream_frames(path, body, headers)

    def _stream_frames(
        self, path: str, body: Any, headers: Dict[str, str]
    ) -> Iterator[ChatCompletionChunk]:
        with self._client.stream(
            "POST", path, json=body, headers=headers
        ) as response:
            if response.status_code >= 400:
                response.read()
            _raise_for_status(response)
            yield from _iter_sse(response)

    def stream_json(
        self, path: str, body: Any, model_cls: Type[T], *, request_id: Optional[str] = None
    ) -> Iterator[T]:
        headers = self._headers(request_id)
        return self._stream_json_frames(path, body, model_cls, headers)

    def _stream_json_frames(
        self, path: str, body: Any, model_cls: Type[T], headers: Dict[str, str]
    ) -> Iterator[T]:
        with self._client.stream(
            "POST", path, json=body, headers=headers
        ) as response:
            if response.status_code >= 400:
                response.read()
            _raise_for_status(response)
            yield from _iter_json_sse(response, model_cls)

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

    def _headers(self, request_id: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self._config.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            _SDK_VERSION_HEADER: _SDK_VERSION_VALUE,
        }
        if request_id is not None:
            headers[_REQUEST_ID_HEADER] = validate_request_id(request_id)
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Any] = None,
        request_id: Optional[str] = None,
    ) -> httpx.Response:
        kwargs: Dict[str, Any] = {
            "headers": self._headers(request_id),
            "params": params,
        }
        if json_body is not None:
            kwargs["json"] = json_body

        for attempt in range(self._config.max_retries + 1):
            response = await self._client.request(method, path, **kwargs)
            if (
                response.status_code in _RETRY_STATUS_CODES
                and attempt < self._config.max_retries
            ):
                delay = _compute_delay_s(attempt, _retry_after_from_response(response))
                await asyncio.sleep(delay)
                continue
            _raise_for_status(response)
            return response

        raise RuntimeError("unreachable")

    async def get(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> Any:
        response = await self._request("GET", path, params=params, request_id=request_id)
        if response.status_code == 204:
            return None
        return _attach_request_id(response.json(), response)

    async def post(self, path: str, body: Any, *, request_id: Optional[str] = None) -> Any:
        response = await self._request("POST", path, json_body=body, request_id=request_id)
        if response.status_code == 204:
            return None
        return _attach_request_id(response.json(), response)

    async def patch(self, path: str, body: Any, *, request_id: Optional[str] = None) -> Any:
        response = await self._request("PATCH", path, json_body=body, request_id=request_id)
        if response.status_code == 204:
            return None
        return _attach_request_id(response.json(), response)

    async def delete(self, path: str, *, request_id: Optional[str] = None) -> None:
        response = await self._request("DELETE", path, request_id=request_id)
        if response.status_code == 204:
            return

    async def get_bytes(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> bytes:
        response = await self._request("GET", path, params=params, request_id=request_id)
        return response.content

    async def post_bytes(self, path: str, body: Any, *, request_id: Optional[str] = None) -> bytes:
        response = await self._request("POST", path, json_body=body, request_id=request_id)
        return response.content

    async def post_multipart(self, path: str, fields: Dict[str, Any], file_data: Optional[tuple] = None, file_field: str = "file", request_id: Optional[str] = None) -> Any:
        headers = {k: v for k, v in self._headers(request_id).items() if k != "Content-Type"}
        files = None
        data = None
        if file_data is not None:
            files = {file_field: file_data}
            data = {k: str(v) for k, v in fields.items() if v is not None}
        else:
            data = {k: str(v) for k, v in fields.items() if v is not None}
        response = await self._client.post(path, headers=headers, data=data, files=files)
        _raise_for_status(response)
        return _attach_request_id(response.json(), response)

    def stream(
        self, path: str, body: Any, *, request_id: Optional[str] = None
    ) -> AsyncIterator[ChatCompletionChunk]:
        # Headers are built eagerly so an invalid request_id raises ValueError
        # before the async stream generator is first iterated.
        headers = self._headers(request_id)
        return self._stream_frames(path, body, headers)

    async def _stream_frames(
        self, path: str, body: Any, headers: Dict[str, str]
    ) -> AsyncIterator[ChatCompletionChunk]:
        async with self._client.stream(
            "POST", path, json=body, headers=headers
        ) as response:
            if response.status_code >= 400:
                await response.aread()
            _raise_for_status(response)
            async for chunk in _aiter_sse(response):
                yield chunk

    def stream_json(
        self, path: str, body: Any, model_cls: Type[T], *, request_id: Optional[str] = None
    ) -> AsyncIterator[T]:
        headers = self._headers(request_id)
        return self._stream_json_frames(path, body, model_cls, headers)

    async def _stream_json_frames(
        self, path: str, body: Any, model_cls: Type[T], headers: Dict[str, str]
    ) -> AsyncIterator[T]:
        async with self._client.stream(
            "POST", path, json=body, headers=headers
        ) as response:
            if response.status_code >= 400:
                await response.aread()
            _raise_for_status(response)
            async for item in _aiter_json_sse(response, model_cls):
                yield item

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncHttpClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()
