"""Unit tests for the animated GIF frame options on image requests.

Spec v1.0.425 adds two optional fields to ``ImageGenerationRequest`` and
``ImageOptions``:

- ``frame_count``: number of frames in a GIF result (2-16).
- ``frame_duration_ms``: display time of each frame in milliseconds (>= 20).

Both only apply when ``output_format`` is ``"gif"``. These tests check the
model shape without building a full request, so they need no model id and
no network access.
"""

from __future__ import annotations

import pytest

from meshapi._types import ImageGenerationRequest, ImageOptions

NEW_FIELDS = ("frame_count", "frame_duration_ms")


@pytest.mark.parametrize("model_cls", [ImageGenerationRequest, ImageOptions])
@pytest.mark.parametrize("field", NEW_FIELDS)
def test_gif_frame_field_is_declared(model_cls, field):
    assert field in model_cls.model_fields, (
        f"{model_cls.__name__} is missing `{field}`"
    )


@pytest.mark.parametrize("model_cls", [ImageGenerationRequest, ImageOptions])
@pytest.mark.parametrize("field", NEW_FIELDS)
def test_gif_frame_field_is_optional(model_cls, field):
    info = model_cls.model_fields[field]
    assert not info.is_required()
    assert info.default is None


def test_image_options_serialises_frame_fields():
    opts = ImageOptions.model_validate({"frame_count": 4, "frame_duration_ms": 120})
    dumped = opts.model_dump(exclude_none=True)
    assert dumped["frame_count"] == 4
    assert dumped["frame_duration_ms"] == 120


def test_image_options_omits_unset_frame_fields():
    opts = ImageOptions.model_validate({})
    dumped = opts.model_dump(exclude_none=True)
    assert "frame_count" not in dumped
    assert "frame_duration_ms" not in dumped
