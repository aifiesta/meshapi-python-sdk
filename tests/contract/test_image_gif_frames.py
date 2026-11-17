"""Contract tests for the animated GIF frame fields on image requests.

`frame_count` (2-16) and `frame_duration_ms` (>= 20) are optional and only
meaningful with `output_format="gif"`. Both must be omitted from the request
body when unset, so existing callers send exactly what they sent before.
"""

from meshapi._types import ImageGenerationRequest, ImageOptions

GIF_MODEL = "openai/gpt-image-2.6-flare"


def test_image_generation_request_declares_frame_fields() -> None:
    fields = ImageGenerationRequest.model_fields
    assert "frame_count" in fields
    assert "frame_duration_ms" in fields


def test_image_options_declares_frame_fields() -> None:
    fields = ImageOptions.model_fields
    assert "frame_count" in fields
    assert "frame_duration_ms" in fields


def test_frame_fields_serialise_when_set() -> None:
    req = ImageGenerationRequest(
        model=GIF_MODEL,
        prompt="a bouncing ball",
        output_format="gif",
        frame_count=4,
        frame_duration_ms=120,
    )
    body = req.model_dump(exclude_none=True)
    assert body["output_format"] == "gif"
    assert body["frame_count"] == 4
    assert body["frame_duration_ms"] == 120


def test_frame_fields_omitted_by_default() -> None:
    req = ImageGenerationRequest(model=GIF_MODEL, prompt="a bouncing ball")
    body = req.model_dump(exclude_none=True)
    assert "frame_count" not in body
    assert "frame_duration_ms" not in body


def test_image_options_frame_fields_roundtrip() -> None:
    opts = ImageOptions(frame_count=8, frame_duration_ms=50)
    body = opts.model_dump(exclude_none=True)
    assert body["frame_count"] == 8
    assert body["frame_duration_ms"] == 50
