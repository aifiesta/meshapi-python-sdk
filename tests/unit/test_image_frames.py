"""Unit tests for animated GIF frame options on image requests.

Covers the optional ``frame_count`` and ``frame_duration_ms`` fields added to
``ImageGenerationRequest`` and ``ImageOptions`` in API spec v1.0.419. Both
fields apply when ``output_format`` is ``"gif"``. The server accepts
``frame_count`` from 2 to 16 and ``frame_duration_ms`` of 20 or more.
"""

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


def test_image_options_serialises_frame_fields():
    opts = ImageOptions(output_format="gif", frame_count=4, frame_duration_ms=120)
    body = opts.model_dump(exclude_none=True)
    assert body["output_format"] == "gif"
    assert body["frame_count"] == 4
    assert body["frame_duration_ms"] == 120


def test_image_options_omits_unset_frame_fields():
    body = ImageOptions().model_dump(exclude_none=True)
    assert "frame_count" not in body
    assert "frame_duration_ms" not in body


def test_image_options_parses_frame_fields_from_json():
    opts = ImageOptions.model_validate({"frame_count": 8, "frame_duration_ms": 40})
    assert opts.frame_count == 8
    assert opts.frame_duration_ms == 40
