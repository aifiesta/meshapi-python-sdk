"""Unit tests for the animated GIF frame options on image generation.

``frame_count`` and ``frame_duration_ms`` are optional fields on
``ImageGenerationRequest`` and ``ImageOptions``. They apply when
``output_format`` is ``"gif"``. ``frame_count`` accepts 2-16 frames and
``frame_duration_ms`` accepts 20 ms or more per frame.
"""

from __future__ import annotations

import pytest

from meshapi._types import ImageGenerationRequest, ImageOptions


@pytest.mark.parametrize("model_cls", [ImageGenerationRequest, ImageOptions])
def test_frame_fields_are_declared(model_cls):
    fields = model_cls.model_fields
    assert "frame_count" in fields
    assert "frame_duration_ms" in fields


@pytest.mark.parametrize("model_cls", [ImageGenerationRequest, ImageOptions])
def test_frame_fields_default_to_none(model_cls):
    fields = model_cls.model_fields
    assert fields["frame_count"].default is None
    assert fields["frame_duration_ms"].default is None


@pytest.mark.parametrize("model_cls", [ImageGenerationRequest, ImageOptions])
def test_frame_fields_serialise_when_set(model_cls):
    obj = model_cls.model_construct(
        output_format="gif", frame_count=4, frame_duration_ms=120
    )
    body = obj.model_dump(exclude_none=True)
    assert body["frame_count"] == 4
    assert body["frame_duration_ms"] == 120
    assert body["output_format"] == "gif"


@pytest.mark.parametrize("model_cls", [ImageGenerationRequest, ImageOptions])
def test_frame_fields_omitted_when_unset(model_cls):
    obj = model_cls.model_construct()
    body = obj.model_dump(exclude_none=True)
    assert "frame_count" not in body
    assert "frame_duration_ms" not in body
