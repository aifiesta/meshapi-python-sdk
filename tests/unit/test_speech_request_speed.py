"""Unit tests for ``SpeechRequest.speed`` on ``POST /v1/audio/speech``.

``speed`` is an optional top-level playback rate, bounded 0.25 to 4.0. The
gateway forwards it as sent and never clamps it; providers that do not read a
rate control ignore it.
"""

import pytest
from pydantic import ValidationError

from meshapi._types import SpeechRequest

# Serialisation-only fixture value; no request is sent in these tests.
_MODEL = "test/tts-model"


def _request(**overrides: object) -> SpeechRequest:
    params: dict = {"model": _MODEL, "input": "Hello there.", "voice": "alloy"}
    params.update(overrides)
    return SpeechRequest(**params)


def test_speed_is_serialised_when_set() -> None:
    body = _request(speed=1.5).model_dump(exclude_none=True)
    assert body["speed"] == 1.5


def test_speed_absent_stays_absent() -> None:
    body = _request().model_dump(exclude_none=True)
    assert "speed" not in body


@pytest.mark.parametrize("value", [0.25, 1.0, 4.0])
def test_speed_accepts_bounds(value: float) -> None:
    assert _request(speed=value).speed == value


@pytest.mark.parametrize("value", [0.0, 0.24, 4.01, -1.0])
def test_speed_rejects_out_of_range(value: float) -> None:
    with pytest.raises(ValidationError):
        _request(speed=value)
