"""Unit tests for the optional top-level ``speed`` field on ``SpeechRequest``.

``POST /v1/audio/speech`` accepts ``speed`` in the range 0.25-4.0. The value
is forwarded as sent and is never clamped. Whether it changes the output
depends on the model that serves the request.
"""

from __future__ import annotations

import pytest

from meshapi._types import SpeechRequest

_BASE = {
    "model": "test-tts-model",
    "input": "Hello there.",
    "voice": "alloy",
}


def _dump(req: SpeechRequest) -> dict:
    return req.model_dump(exclude_none=True)


def test_speed_field_is_declared() -> None:
    assert "speed" in SpeechRequest.model_fields


@pytest.mark.parametrize("speed", [0.25, 1.0, 1.5, 4.0])
def test_speed_is_serialized_when_set(speed: float) -> None:
    req = SpeechRequest.model_validate({**_BASE, "speed": speed})
    assert _dump(req)["speed"] == speed


def test_speed_is_absent_when_unset() -> None:
    req = SpeechRequest.model_validate(_BASE)
    assert "speed" not in _dump(req)


def test_speed_round_trips_through_json() -> None:
    req = SpeechRequest.model_validate({**_BASE, "speed": 0.75})
    parsed = SpeechRequest.model_validate_json(req.model_dump_json(exclude_none=True))
    assert parsed.speed == 0.75
