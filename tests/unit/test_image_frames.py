"""Unit tests for the animated GIF frame fields added in spec v1.0.420.

`ImageGenerationRequest` and `ImageOptions` gain two optional fields:

- `frame_count`: number of frames in an animated GIF (2-16).
- `frame_duration_ms`: display time of each frame in milliseconds (>= 20).

Both are only meaningful with `output_format="gif"` and are omitted from the
request body when unset.
"""

from __future__ import annotations

import pytest

from meshapi import _types

FRAME_FIELDS = ("frame_count", "frame_duration_ms")
MODELS = ("ImageGenerationRequest", "ImageOptions")


@pytest.mark.parametrize("model_name", MODELS)
@pytest.mark.parametrize("field_name", FRAME_FIELDS)
def test_frame_field_is_declared(model_name: str, field_name: str) -> None:
    model = getattr(_types, model_name)
    assert field_name in model.model_fields


@pytest.mark.parametrize("model_name", MODELS)
@pytest.mark.parametrize("field_name", FRAME_FIELDS)
def test_frame_field_is_optional(model_name: str, field_name: str) -> None:
    model = getattr(_types, model_name)
    field = model.model_fields[field_name]
    assert not field.is_required()
    assert field.default is None
