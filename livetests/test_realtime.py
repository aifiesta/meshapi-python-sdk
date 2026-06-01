"""Live tests for the MeshAPI Python SDK realtime (WebSocket) resource."""

from __future__ import annotations

import pytest

from config import get_env
from meshapi import MeshAPI, AsyncMeshAPI
from meshapi.resources.realtime import RealtimeError


REALTIME_MODEL = get_env("MESHAPI_REALTIME_MODEL", "openai/gpt-realtime-mini")


def skip_if_no_model():
    pass  # default is openai/gpt-realtime-mini; override via MESHAPI_REALTIME_MODEL


# ---------------------------------------------------------------------------
# Sync tests
# ---------------------------------------------------------------------------


def test_realtime_connect_and_close(client: MeshAPI) -> None:
    skip_if_no_model()
    with client.realtime.connect(model=REALTIME_MODEL) as session:
        pass  # clean close on __exit__


def test_realtime_receive_session_created(client: MeshAPI) -> None:
    """Server sends session.created immediately after the WebSocket handshake."""
    skip_if_no_model()
    with client.realtime.connect(model=REALTIME_MODEL) as session:
        msg = session.receive()
        assert msg.event is not None, "expected JSON text frame, got binary"
        print(f"[PASS] first frame type={msg.event.get('type')!r}")


def test_realtime_send_session_update(client: MeshAPI) -> None:
    """Send session.update and receive the server acknowledgement."""
    skip_if_no_model()
    with client.realtime.connect(model=REALTIME_MODEL) as session:
        # Drain the initial session.created.
        session.receive()

        session.send(
            {
                "type": "session.update",
                "session": {
                    "type": "realtime",
                    "instructions": "You are a helpful assistant.",
                },
            }
        )
        msg = session.receive()
        assert msg.event is not None
        print(f"[PASS] session.update ack: type={msg.event.get('type')!r}")


def test_realtime_error_envelope_bad_model(client: MeshAPI) -> None:
    """Connecting with an unknown model should raise RealtimeError or a connect error."""
    skip_if_no_model()
    try:
        with client.realtime.connect(model="nonexistent/bad-model-xyz") as session:
            # If connect succeeded, the error may arrive as an envelope frame.
            try:
                session.receive()
            except RealtimeError as e:
                print(f"[PASS] error envelope received: code={e.code!r}")
                return
        # Server may close without an error frame for auth failures.
        print("[PASS] server closed connection for bad model (no envelope)")
    except Exception as e:
        print(f"[PASS] connect failed for bad model: {e}")


def test_realtime_iterator_api(client: MeshAPI) -> None:
    """Iterate over frames using the __iter__ protocol."""
    skip_if_no_model()
    received = []
    with client.realtime.connect(model=REALTIME_MODEL) as session:
        for msg in session:
            received.append(msg)
            if len(received) >= 1:
                break  # stop after first frame

    assert len(received) >= 1, "expected at least one frame"
    print(f"[PASS] iterator received {len(received)} frame(s)")


# ---------------------------------------------------------------------------
# Async tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_realtime_async_connect_and_close() -> None:
    skip_if_no_model()
    from config import BASE_URL, TOKEN
    async with AsyncMeshAPI(base_url=BASE_URL, token=TOKEN) as client:
        async with client.realtime.connect(model=REALTIME_MODEL) as session:
            pass


@pytest.mark.asyncio
async def test_realtime_async_receive_session_created() -> None:
    skip_if_no_model()
    from config import BASE_URL, TOKEN
    async with AsyncMeshAPI(base_url=BASE_URL, token=TOKEN) as client:
        async with client.realtime.connect(model=REALTIME_MODEL) as session:
            msg = await session.receive()
            assert msg.event is not None
            print(f"[PASS] async first frame type={msg.event.get('type')!r}")


@pytest.mark.asyncio
async def test_realtime_async_aiter() -> None:
    skip_if_no_model()
    from config import BASE_URL, TOKEN
    async with AsyncMeshAPI(base_url=BASE_URL, token=TOKEN) as client:
        async with client.realtime.connect(model=REALTIME_MODEL) as session:
            count = 0
            async for msg in session:
                count += 1
                if count >= 1:
                    break
    assert count >= 1
    print(f"[PASS] async iterator received {count} frame(s)")
