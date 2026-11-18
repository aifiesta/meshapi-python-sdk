"""Unit tests for the animated GIF frame fields on image requests.

Covers `frame_count` and `frame_duration_ms` on `ImageGenerationRequest`
and `ImageOptions`. Both fields are optional and must be omitted from the
request body when unset.
"""

from __future__ import annotations

import pytest

from meshapi._types import ImageGenerationRequest, ImageOptions

GIF_MODEL = "openai/gpt-image-2.6-flare"


def test_generation_request_serialises_frame_fields() -> None:
    req = ImageGenerationRequest(
        model=GIF_MODEL,
        prompt="a bouncing ball",
        output_format="gif",
        frame_count=4,
        frame_duration_ms=100,
    )
    body = req.model_dump(exclude_none=True)
    assert body["frame_count"] == 4
    assert body["frame_duration_ms"] == 100
    assert body["output_format"] == "gif"


def test_generation_request_omits_frame_fields_when_unset() -> None:
    req = ImageGenerationRequest(model=GIF_MODEL, prompt="a still image")
    body = req.model_dump(exclude_none=True)
    assert "frame_count" not in body
    assert "frame_duration_ms" not in body


def test_image_options_serialises_frame_fields() -> None:
    opts = ImageOptions(output_format="gif", frame_count=8, frame_duration_ms=50)
    body = opts.model_dump(exclude_none=True)
    assert body["frame_count"] == 8
    assert body["frame_duration_ms"] == 50


def test_image_options_omits_frame_fields_when_unset() -> None:
    body = ImageOptions().model_dump(exclude_none=True)
    assert "frame_count" not in body
    assert "frame_duration_ms" not in body


@pytest.mark.parametrize("cls", [ImageGenerationRequest, ImageOptions])
def test_frame_fields_default_to_none(cls: type) -> None:
    fields = cls.model_fields
    assert "frame_count" in fields
    assert "frame_duration_ms" in fields
    assert fields["frame_count"].default is None
    assert fields["frame_duration_ms"].default is None
