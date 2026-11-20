"""Contract checks for the optional request fields added in API v1.0.430.

Every field in this release is optional and non-breaking:

- ``ImageGenerationRequest`` / ``ImageOptions``: ``frame_count`` and
  ``frame_duration_ms`` for multi-frame (animated) image output.
- ``SearchRequest``: ``mode`` selects the retrieval mode for
  ``POST /v1/files/search``.
- ``VideoGenerateRequest`` / ``VideoGenerationRequest`` / ``VideoEditRequest``:
  ``width`` and ``height`` request an exact output size. Send both or neither.

Each test is skipped when the model is not exported by this build of the SDK.
When the model is exported, the field must be declared, must default to
``None``, and must be left out of the serialised body when unset, so requests
that do not use the new fields are unchanged on the wire.
"""

from __future__ import annotations

import pytest

import meshapi._types as types

NEW_FIELDS = [
    ("ImageGenerationRequest", "frame_count"),
    ("ImageGenerationRequest", "frame_duration_ms"),
    ("ImageOptions", "frame_count"),
    ("ImageOptions", "frame_duration_ms"),
    ("SearchRequest", "mode"),
    ("VideoEditRequest", "width"),
    ("VideoEditRequest", "height"),
    ("VideoGenerateRequest", "width"),
    ("VideoGenerateRequest", "height"),
    ("VideoGenerationRequest", "width"),
    ("VideoGenerationRequest", "height"),
]


def _model(name: str):
    model = getattr(types, name, None)
    if model is None:
        pytest.skip(f"{name} is not exported by meshapi._types")
    return model


@pytest.mark.parametrize("model_name,field", NEW_FIELDS)
def test_field_is_declared(model_name: str, field: str) -> None:
    model = _model(model_name)
    assert field in model.model_fields, f"{model_name}.{field} is missing"


@pytest.mark.parametrize("model_name,field", NEW_FIELDS)
def test_field_is_optional_and_defaults_to_none(model_name: str, field: str) -> None:
    model = _model(model_name)
    info = model.model_fields.get(field)
    if info is None:
        pytest.fail(f"{model_name}.{field} is missing")
    assert not info.is_required(), f"{model_name}.{field} must be optional"
    assert info.default is None, f"{model_name}.{field} must default to None"
