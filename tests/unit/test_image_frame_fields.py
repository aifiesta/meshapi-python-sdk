"""Unit tests for the animated-image frame fields added in spec v1.0.429.

``frame_count`` and ``frame_duration_ms`` are optional on both
``ImageGenerationRequest`` and ``ImageOptions``. Omitting them keeps the
previous single-frame behaviour, so neither field may be required and both
must default to ``None``.
"""

from __future__ import annotations

import typing

import pytest

from meshapi._types import ImageGenerationRequest, ImageOptions

FRAME_FIELDS = ("frame_count", "frame_duration_ms")
MODELS = (ImageGenerationRequest, ImageOptions)


def _accepts_int(annotation: typing.Any) -> bool:
    if annotation is int:
        return True
    return int in typing.get_args(annotation)


@pytest.mark.parametrize("model", MODELS, ids=lambda m: m.__name__)
@pytest.mark.parametrize("field", FRAME_FIELDS)
def test_frame_field_is_declared(model, field):
    assert field in model.model_fields


@pytest.mark.parametrize("model", MODELS, ids=lambda m: m.__name__)
@pytest.mark.parametrize("field", FRAME_FIELDS)
def test_frame_field_is_optional_and_defaults_to_none(model, field):
    info = model.model_fields[field]
    assert info.is_required() is False
    assert info.default is None


@pytest.mark.parametrize("model", MODELS, ids=lambda m: m.__name__)
@pytest.mark.parametrize("field", FRAME_FIELDS)
def test_frame_field_accepts_integers(model, field):
    assert _accepts_int(model.model_fields[field].annotation)
