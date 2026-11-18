"""Unit tests for the GIF frame options on image generation.

Spec v1.0.428 adds two optional fields to both ``ImageGenerationRequest`` and
``ImageOptions``:

- ``frame_count``: number of frames in a GIF result (2-16).
- ``frame_duration_ms``: display time of each frame in milliseconds (>= 20).

Both only apply when ``output_format`` is ``"gif"``. The server validates
ranges and model support. The SDK forwards the values unchanged and omits
them when unset.
"""

from __future__ import annotations

import pytest

from meshapi._types import ImageGenerationRequest, ImageOptions


@pytest.mark.parametrize("model_cls", [ImageGenerationRequest, ImageOptions])
@pytest.mark.parametrize("field", ["frame_count", "frame_duration_ms"])
def test_frame_fields_are_declared(model_cls, field):
    assert field in model_cls.model_fields


@pytest.mark.parametrize("model_cls", [ImageGenerationRequest, ImageOptions])
@pytest.mark.parametrize("field", ["frame_count", "frame_duration_ms"])
def test_frame_fields_are_optional(model_cls, field):
    info = model_cls.model_fields[field]
    assert not info.is_required()
    assert info.default is None


@pytest.mark.parametrize("model_cls", [ImageGenerationRequest, ImageOptions])
def test_frame_fields_serialise_when_set(model_cls):
    obj = model_cls.model_construct(frame_count=4, frame_duration_ms=120)
    dumped = obj.model_dump(exclude_none=True)
    assert dumped["frame_count"] == 4
    assert dumped["frame_duration_ms"] == 120


@pytest.mark.parametrize("model_cls", [ImageGenerationRequest, ImageOptions])
def test_frame_fields_omitted_when_unset(model_cls):
    obj = model_cls.model_construct(frame_count=None, frame_duration_ms=None)
    dumped = obj.model_dump(exclude_none=True)
    assert "frame_count" not in dumped
    assert "frame_duration_ms" not in dumped
