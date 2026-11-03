"""Unit tests for the top-level ``speed`` field on ``SpeechRequest``.

``POST /v1/audio/speech`` accepts an optional ``speed`` between 0.25 and 4.0.
The value is forwarded as sent and is never clamped. When it is omitted, it
must stay out of the serialised request body.
"""

from __future__ import annotations

from typing import Any, Dict

import pytest
from pydantic import ValidationError

from meshapi import SpeechRequest


def _minimal(**overrides: Any) -> Dict[str, Any]:
    """Build the smallest valid payload by filling every required field.

    This avoids hard-coding a model id or voice in a serialisation test.
    """
    payload: Dict[str, Any] = {}
    for name, field in SpeechRequest.model_fields.items():
        if field.is_required():
            payload[field.alias or name] = "test-value"
    payload.update(overrides)
    return payload


def test_speed_is_serialised_when_set() -> None:
    req = SpeechRequest.model_validate(_minimal(speed=1.5))
    assert req.speed == 1.5
    assert req.model_dump(exclude_none=True)["speed"] == 1.5


def test_speed_absent_stays_absent() -> None:
    req = SpeechRequest.model_validate(_minimal())
    assert req.speed is None
    assert "speed" not in req.model_dump(exclude_none=True)


@pytest.mark.parametrize("value", [0.25, 1.0, 4.0])
def test_speed_accepts_bounds(value: float) -> None:
    req = SpeechRequest.model_validate(_minimal(speed=value))
    assert req.speed == value


@pytest.mark.parametrize("value", [0.0, 0.24, 4.01, -1.0])
def test_speed_rejects_out_of_range(value: float) -> None:
    with pytest.raises(ValidationError):
        SpeechRequest.model_validate(_minimal(speed=value))
