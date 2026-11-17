"""Unit tests for animated GIF frame controls on image requests.

Covers the ``frame_count`` and ``frame_duration_ms`` fields on
``ImageGenerationRequest`` (``POST /v1/images/generations`` and
``POST /v1/images/edits``) and on ``ImageOptions`` (the chat image path).
Both fields are optional and only apply when ``output_format`` is ``"gif"``.
"""

from __future__ import annotations

from meshapi import ImageGenerationRequest, ImageOptions

GIF_MODEL = "openai/gpt-image-2.6-flare"


def test_generation_request_serialises_frame_fields() -> None:
    req = ImageGenerationRequest(
        model=GIF_MODEL,
        prompt="A paper boat drifting on a pond",
        output_format="gif",
        frame_count=8,
        frame_duration_ms=120,
    )
    body = req.model_dump(exclude_none=True)
    assert body["output_format"] == "gif"
    assert body["frame_count"] == 8
    assert body["frame_duration_ms"] == 120


def test_generation_request_omits_frame_fields_by_default() -> None:
    req = ImageGenerationRequest(model=GIF_MODEL, prompt="A lighthouse")
    assert req.frame_count is None
    assert req.frame_duration_ms is None
    body = req.model_dump(exclude_none=True)
    assert "frame_count" not in body
    assert "frame_duration_ms" not in body


def test_generation_request_parses_frame_fields_from_json() -> None:
    req = ImageGenerationRequest.model_validate(
        {
            "model": GIF_MODEL,
            "prompt": "A spinning top",
            "output_format": "gif",
            "frame_count": 2,
            "frame_duration_ms": 20,
        }
    )
    assert req.frame_count == 2
    assert req.frame_duration_ms == 20


def test_image_options_serialises_frame_fields() -> None:
    opts = ImageOptions(frame_count=16, frame_duration_ms=40)
    body = opts.model_dump(exclude_none=True)
    assert body["frame_count"] == 16
    assert body["frame_duration_ms"] == 40


def test_image_options_omits_frame_fields_by_default() -> None:
    opts = ImageOptions()
    body = opts.model_dump(exclude_none=True)
    assert "frame_count" not in body
    assert "frame_duration_ms" not in body
