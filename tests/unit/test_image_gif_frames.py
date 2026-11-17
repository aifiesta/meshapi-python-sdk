"""Unit tests for animated GIF frame options on image requests.

Covers the optional ``frame_count`` and ``frame_duration_ms`` fields on
``ImageGenerationRequest`` and ``ImageOptions``. Both fields only apply when
``output_format`` is ``"gif"``. The server enforces the ranges
(``frame_count`` 2-16, ``frame_duration_ms`` >= 20), so these tests only
check serialisation and parsing.
"""

from meshapi import ImageGenerationRequest, ImageOptions

GIF_MODEL = "openai/gpt-image-2.6-flare"


def test_generation_request_serialises_frame_fields() -> None:
    req = ImageGenerationRequest(
        model=GIF_MODEL,
        prompt="a spinning cube",
        output_format="gif",
        frame_count=8,
        frame_duration_ms=120,
    )
    body = req.model_dump(exclude_none=True)
    assert body["output_format"] == "gif"
    assert body["frame_count"] == 8
    assert body["frame_duration_ms"] == 120


def test_generation_request_omits_unset_frame_fields() -> None:
    req = ImageGenerationRequest(model=GIF_MODEL, prompt="a spinning cube")
    body = req.model_dump(exclude_none=True)
    assert "frame_count" not in body
    assert "frame_duration_ms" not in body


def test_generation_request_frame_fields_default_to_none() -> None:
    req = ImageGenerationRequest(model=GIF_MODEL, prompt="a spinning cube")
    assert req.frame_count is None
    assert req.frame_duration_ms is None


def test_generation_request_parses_frame_fields() -> None:
    req = ImageGenerationRequest.model_validate(
        {
            "model": GIF_MODEL,
            "prompt": "a spinning cube",
            "output_format": "gif",
            "frame_count": 4,
            "frame_duration_ms": 50,
        }
    )
    assert req.frame_count == 4
    assert req.frame_duration_ms == 50


def test_image_options_serialises_frame_fields() -> None:
    opts = ImageOptions(output_format="gif", frame_count=6, frame_duration_ms=80)
    body = opts.model_dump(exclude_none=True)
    assert body["frame_count"] == 6
    assert body["frame_duration_ms"] == 80


def test_image_options_omits_unset_frame_fields() -> None:
    opts = ImageOptions()
    body = opts.model_dump(exclude_none=True)
    assert "frame_count" not in body
    assert "frame_duration_ms" not in body
