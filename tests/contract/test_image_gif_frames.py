"""Contract tests for animated GIF frame controls on image requests.

Spec v1.0.417 adds two optional fields to both ``ImageGenerationRequest``
and ``ImageOptions``:

- ``frame_count``: number of frames in a GIF result (server accepts 2-16).
- ``frame_duration_ms``: display time per frame in milliseconds (server
  accepts values of 20 or more).

Both fields only apply when ``output_format`` is ``"gif"``. They are
optional and must be omitted from the wire payload when unset.
"""

from __future__ import annotations

import pytest

from meshapi import ImageGenerationRequest, ImageOptions

NEW_FIELDS = ("frame_count", "frame_duration_ms")


@pytest.mark.parametrize("model_cls", [ImageGenerationRequest, ImageOptions])
@pytest.mark.parametrize("field", NEW_FIELDS)
def test_frame_fields_are_declared(model_cls, field):
    assert field in model_cls.model_fields


@pytest.mark.parametrize("model_cls", [ImageGenerationRequest, ImageOptions])
@pytest.mark.parametrize("field", NEW_FIELDS)
def test_frame_fields_are_optional_and_default_to_none(model_cls, field):
    info = model_cls.model_fields[field]
    assert not info.is_required()
    assert info.default is None


def test_image_options_accepts_frame_fields():
    opts = ImageOptions.model_validate(
        {"output_format": "gif", "frame_count": 4, "frame_duration_ms": 120}
    )
    assert opts.frame_count == 4
    assert opts.frame_duration_ms == 120


def test_image_options_serialises_frame_fields():
    opts = ImageOptions.model_validate(
        {"output_format": "gif", "frame_count": 8, "frame_duration_ms": 50}
    )
    payload = opts.model_dump(exclude_none=True)
    assert payload["frame_count"] == 8
    assert payload["frame_duration_ms"] == 50


def test_image_options_omits_unset_frame_fields():
    payload = ImageOptions.model_validate({}).model_dump(exclude_none=True)
    for field in NEW_FIELDS:
        assert field not in payload


def test_image_generation_request_serialises_frame_fields():
    req = ImageGenerationRequest.model_construct(
        prompt="a spinning cube",
        output_format="gif",
        frame_count=6,
        frame_duration_ms=80,
    )
    payload = req.model_dump(exclude_none=True)
    assert payload["frame_count"] == 6
    assert payload["frame_duration_ms"] == 80


def test_image_generation_request_omits_unset_frame_fields():
    req = ImageGenerationRequest.model_construct(prompt="a still cube")
    payload = req.model_dump(exclude_none=True)
    for field in NEW_FIELDS:
        assert field not in payload
