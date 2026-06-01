"""Realtime resource — WSS /v1/realtime (bidirectional WebSocket session)."""

from __future__ import annotations

import json
from typing import Any, AsyncIterator, Iterator
from urllib.parse import quote

from .._errors import MeshAPIError
from .._http import MeshAPIConfig

_SDK_VERSION_HEADER = "X-MeshAPI-SDK"
_SDK_VERSION_VALUE = "python/0.1.0"


class RealtimeError(MeshAPIError):
    """Raised when the server sends a JSON error envelope over the WebSocket."""

    def __init__(self, code: str, message: str, param: str | None = None, request_id: str | None = None) -> None:
        # MeshAPIError takes message positionally and error_code as a keyword arg.
        super().__init__(message, status=0, error_code=code, request_id=request_id or "")
        self.code = code  # convenience alias matching the wire field name
        self.param = param

    def __str__(self) -> str:
        return f"realtime[{self.code}]: {self.args[0]}"


class RealtimeMessage:
    """A single frame received from the server.

    Exactly one of ``text`` or ``audio`` is set per message.
    ``event`` holds the parsed JSON map for text frames.
    """

    __slots__ = ("text", "audio", "event")

    def __init__(
        self,
        *,
        text: str | None = None,
        audio: bytes | None = None,
        event: dict[str, Any] | None = None,
    ) -> None:
        self.text = text
        self.audio = audio
        self.event = event

    def __repr__(self) -> str:
        if self.audio is not None:
            return f"RealtimeMessage(audio={len(self.audio)}B)"
        return f"RealtimeMessage(type={self.event.get('type')!r})" if self.event else "RealtimeMessage(text=...)"


def _ws_url(base_url: str, model: str) -> str:
    base = base_url.rstrip("/")
    base = base.replace("https://", "wss://", 1).replace("http://", "ws://", 1)
    return f"{base}/v1/realtime?model={quote(model)}"


def _parse_frame(data: str | bytes) -> RealtimeMessage | None:
    """Parse one WebSocket frame into a RealtimeMessage, or return None on error."""
    if isinstance(data, (bytes, bytearray, memoryview)):
        return RealtimeMessage(audio=bytes(data))
    try:
        evt: dict[str, Any] = json.loads(data)
    except (json.JSONDecodeError, ValueError):
        return RealtimeMessage(text=data)
    return RealtimeMessage(text=data, event=evt)


def _check_error_envelope(msg: RealtimeMessage) -> None:
    """Raise RealtimeError if *msg* carries a server error envelope."""
    if msg.event and msg.event.get("type") == "error":
        err = msg.event.get("error") or {}
        raise RealtimeError(
            code=err.get("code", "unknown"),
            message=err.get("message", "realtime error"),
            param=err.get("param"),
            request_id=msg.event.get("request_id"),
        )


# ---------------------------------------------------------------------------
# Async session + resource
# ---------------------------------------------------------------------------


class AsyncRealtimeSession:
    """Active async WebSocket session with the MeshAPI realtime endpoint.

    Use as an async context manager::

        async with client.realtime.connect(model="openai/gpt-4o-realtime-preview") as session:
            await session.send({"type": "session.update", "session": {...}})
            async for msg in session:
                print(msg.event)

    Or await it to get the session directly::

        session = await client.realtime.connect(model=...)
        try:
            ...
        finally:
            await session.close()
    """

    def __init__(self, ws: Any) -> None:
        self._ws = ws

    async def __aenter__(self) -> "AsyncRealtimeSession":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def send(self, event: dict[str, Any]) -> None:
        """Marshal *event* as JSON and send it as a text WebSocket frame."""
        await self._ws.send(json.dumps(event))

    async def send_audio(self, audio: bytes) -> None:
        """Send raw audio *bytes* as a binary WebSocket frame."""
        await self._ws.send(audio)

    async def receive(self) -> RealtimeMessage:
        """Read the next frame from the server.

        Raises :class:`RealtimeError` when the server sends an error envelope.
        Raises ``websockets.exceptions.ConnectionClosed`` on a normal close.
        """
        data = await self._ws.recv()
        msg = _parse_frame(data)
        if msg is None:
            raise RuntimeError("failed to parse frame")
        _check_error_envelope(msg)
        return msg

    def __aiter__(self) -> AsyncIterator[RealtimeMessage]:
        return self._aiter()

    async def _aiter(self) -> AsyncIterator[RealtimeMessage]:
        try:
            while True:
                yield await self.receive()
        except Exception:  # noqa: BLE001 — connection closed or error envelope
            return

    async def close(self) -> None:
        """Close the WebSocket connection."""
        try:
            await self._ws.close()
        except Exception:  # noqa: BLE001
            pass


class _AsyncConnectionManager:
    """Returned by :meth:`AsyncRealtimeResource.connect`.

    Supports both ``async with`` and ``await`` so callers can choose::

        # context manager style (recommended)
        async with client.realtime.connect(model=...) as session:
            ...

        # manual style
        session = await client.realtime.connect(model=...)
        try:
            ...
        finally:
            await session.close()
    """

    def __init__(self, cfg: MeshAPIConfig, model: str) -> None:
        self._cfg = cfg
        self._model = model
        self._session: AsyncRealtimeSession | None = None

    async def _do_connect(self) -> AsyncRealtimeSession:
        try:
            from websockets.asyncio.client import connect  # type: ignore[import]
        except ImportError:
            try:
                from websockets.legacy.client import connect  # type: ignore[import]
            except ImportError as exc:
                raise ImportError(
                    "websockets>=12.0 is required for realtime support. "
                    "Install it with: pip install 'websockets>=12.0'"
                ) from exc

        ws_url = _ws_url(self._cfg.base_url, self._model)
        extra_headers = {_SDK_VERSION_HEADER: _SDK_VERSION_VALUE}
        ws = await connect(
            ws_url,
            additional_headers=extra_headers,
            # Auth is carried in the subprotocol list: "openai-realtime, Bearer <token>".
            # Passing it as a separate Sec-WebSocket-Protocol header conflicts with the
            # subprotocols parameter — the library overwrites the header, dropping the token.
            subprotocols=["openai-realtime", f"Bearer {self._cfg.token}"],
        )
        return AsyncRealtimeSession(ws)

    def __await__(self):  # type: ignore[override]
        return self._do_connect().__await__()

    async def __aenter__(self) -> AsyncRealtimeSession:
        self._session = await self._do_connect()
        return self._session

    async def __aexit__(self, *_: Any) -> None:
        if self._session is not None:
            await self._session.close()


class AsyncRealtimeResource:
    """Async access to the MeshAPI realtime endpoint."""

    def __init__(self, cfg: MeshAPIConfig) -> None:
        self._cfg = cfg

    def connect(self, *, model: str) -> _AsyncConnectionManager:
        """Return a connection manager for *model*.

        Use as ``async with`` or ``await``::

            async with client.realtime.connect(model=...) as session:
                ...

            session = await client.realtime.connect(model=...)
        """
        return _AsyncConnectionManager(self._cfg, model)


# ---------------------------------------------------------------------------
# Sync session + resource (uses websockets.sync.client, requires websockets>=12)
# ---------------------------------------------------------------------------


class RealtimeSession:
    """Active synchronous WebSocket session with the MeshAPI realtime endpoint.

    Use as a context manager::

        with client.realtime.connect(model="openai/gpt-4o-realtime-preview") as session:
            session.send({"type": "session.update", "session": {...}})
            for msg in session:
                print(msg.event)
    """

    def __init__(self, ws: Any) -> None:
        self._ws = ws

    def __enter__(self) -> "RealtimeSession":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def send(self, event: dict[str, Any]) -> None:
        """Marshal *event* as JSON and send it as a text WebSocket frame."""
        self._ws.send(json.dumps(event))

    def send_audio(self, audio: bytes) -> None:
        """Send raw audio *bytes* as a binary WebSocket frame."""
        self._ws.send(audio)

    def receive(self) -> RealtimeMessage:
        """Read the next frame from the server.

        Raises :class:`RealtimeError` when the server sends an error envelope.
        Raises ``websockets.exceptions.ConnectionClosed`` on a normal close.
        """
        data = self._ws.recv()
        msg = _parse_frame(data)
        if msg is None:
            raise RuntimeError("failed to parse frame")
        _check_error_envelope(msg)
        return msg

    def __iter__(self) -> Iterator[RealtimeMessage]:
        try:
            while True:
                yield self.receive()
        except Exception:  # noqa: BLE001 — connection closed or error envelope
            return

    def close(self) -> None:
        """Close the WebSocket connection."""
        try:
            self._ws.close()
        except Exception:  # noqa: BLE001
            pass


class RealtimeResource:
    """Sync access to the MeshAPI realtime endpoint."""

    def __init__(self, cfg: MeshAPIConfig) -> None:
        self._cfg = cfg

    def connect(self, *, model: str) -> RealtimeSession:
        """Open a synchronous WebSocket session for *model*.

        Returns a :class:`RealtimeSession` usable as a context manager.

        Requires ``websockets>=12.0``::

            pip install 'websockets>=12.0'
        """
        try:
            from websockets.sync.client import connect  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "websockets>=12.0 is required for realtime support. "
                "Install it with: pip install 'websockets>=12.0'"
            ) from exc

        ws_url = _ws_url(self._cfg.base_url, model)
        extra_headers = {_SDK_VERSION_HEADER: _SDK_VERSION_VALUE}
        ws = connect(
            ws_url,
            additional_headers=extra_headers,
            subprotocols=["openai-realtime", f"Bearer {self._cfg.token}"],
        )
        return RealtimeSession(ws)
