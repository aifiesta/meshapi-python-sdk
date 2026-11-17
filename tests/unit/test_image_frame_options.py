"""Unit tests for the animated GIF frame options added in spec v1.0.421.

``ImageGenerationRequest`` and ``ImageOptions`` gain two optional fields:

- ``frame_count``: number of frames in a GIF result (2-16).
- ``frame_duration_ms``: display time of each frame in milliseconds (>= 20).

Both fields are optional and default to ``None``, so existing callers are
unaffected and nothing extra is sent on the wire unless the caller sets them.
"""

from __future__ import annotations

import pytest

from meshapi import _types

NEW_FIELDS = ("frame_count", "frame_duration_ms")


@pytest.mark.parametrize("model_name", ["ImageGenerationRequest", "ImageOptions"])
@pytest.mark.parametrize("field", NEW_FIELDS)
def test_frame_field_is_declared(model_name: str, field: str) -> None:
    model = getattr(_types, model_name)
    assert field in model.model_fields, f"{model_name}.{field} is missing"


@pytest.mark.parametrize("model_name", ["ImageGenerationRequest", "ImageOptions"])
@pytest.mark.parametrize("field", NEW_FIELDS)
def test_frame_field_is_optional_and_defaults_to_none(model_name: str, field: str) -> None:
    model = getattr(_types, model_name)
    info = model.model_fields[field]
    assert not info.is_required(), f"{model_name}.{field} must be optional"
    assert info.default is None
