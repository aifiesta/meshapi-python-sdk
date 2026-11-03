"""Unit tests for the top-level ``speed`` field on ``SpeechRequest``.

``POST /v1/audio/speech`` accepts an optional ``speed`` between 0.25 and 4.0.
The gateway forwards the value as sent and never clamps it.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from meshapi._types import SpeechRequest


def _blank() -> SpeechRequest:
    # Build an instance without requiring a model id so the test stays
    # independent of the live model catalog.
    return SpeechRequest.model_construct()


def _assign_speed(instance: SpeechRequest, value: object) -> SpeechRequest:
    return SpeechRequest.__pydantic_validator__.validate_assignment(
        instance, "speed", value
    )


def test_speed_field_is_declared_and_optional() -> None:
    field = SpeechRequest.model_fields.get("speed")
    assert field is not None
    assert not field.is_required()
    assert field.default is None


def test_speed_absent_stays_absent() -> None:
    instance = _blank()
    assert instance.model_dump(include={"speed"}, exclude_none=True) == {}


@pytest.mark.parametrize("value", [0.25, 1.0, 1.5, 4.0])
def test_speed_in_range_is_accepted_and_serialised(value: float) -> None:
    instance = _assign_speed(_blank(), value)
    assert instance.speed == value
    assert instance.model_dump(include={"speed"}, exclude_none=True) == {
        "speed": value
    }


@pytest.mark.parametrize("value", [0.0, 0.24, 4.01, 10.0, -1.0])
def test_speed_out_of_range_is_rejected(value: float) -> None:
    with pytest.raises(ValidationError):
        _assign_speed(_blank(), value)
