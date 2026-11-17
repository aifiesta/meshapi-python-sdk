"""Unit tests for animated GIF frame options on image generation.

Covers ``ImageGenerationRequest.frame_count`` / ``frame_duration_ms`` and the
matching ``ImageOptions`` fields used by the chat image path. Both fields are
optional and must be omitted from the wire body when unset.
"""

from __future__ import annotations

import pytest

from meshapi import ImageGenerationRequest, ImageOptions

GIF_MODEL = "openai/gpt-image-2.6-flare"


def _dump(model) -> dict:
    return model.model_dump(exclude_none=True)


class TestImageGenerationRequestFrames:
    def test_frame_fields_serialise_when_set(self) -> None:
        req = ImageGenerationRequest(
            model=GIF_MODEL,
            prompt="A bouncing ball",
            output_format="gif",
            frame_count=4,
            frame_duration_ms=120,
        )
        body = _dump(req)
        assert body["output_format"] == "gif"
        assert body["frame_count"] == 4
        assert body["frame_duration_ms"] == 120

    def test_frame_fields_default_to_none_and_are_omitted(self) -> None:
        req = ImageGenerationRequest(model=GIF_MODEL, prompt="A still lake")
        assert req.frame_count is None
        assert req.frame_duration_ms is None
        body = _dump(req)
        assert "frame_count" not in body
        assert "frame_duration_ms" not in body

    @pytest.mark.parametrize("frame_count", [2, 8, 16])
    def test_frame_count_accepts_documented_range(self, frame_count: int) -> None:
        req = ImageGenerationRequest(
            model=GIF_MODEL,
            prompt="A spinning top",
            output_format="gif",
            frame_count=frame_count,
        )
        assert req.frame_count == frame_count

    def test_frame_fields_round_trip_from_dict(self) -> None:
        req = ImageGenerationRequest.model_validate(
            {
                "model": GIF_MODEL,
                "prompt": "A waving flag",
                "output_format": "gif",
                "frame_count": 6,
                "frame_duration_ms": 40,
            }
        )
        assert req.frame_count == 6
        assert req.frame_duration_ms == 40


class TestImageOptionsFrames:
    def test_frame_fields_serialise_when_set(self) -> None:
        opts = ImageOptions(output_format="gif", frame_count=3, frame_duration_ms=200)
        body = _dump(opts)
        assert body["frame_count"] == 3
        assert body["frame_duration_ms"] == 200

    def test_frame_fields_omitted_when_unset(self) -> None:
        opts = ImageOptions()
        body = _dump(opts)
        assert "frame_count" not in body
        assert "frame_duration_ms" not in body
