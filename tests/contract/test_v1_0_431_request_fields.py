"""Contract checks for request fields added in API spec v1.0.431.

These tests confirm that the request models in ``meshapi._types`` declare the
new optional fields. They also confirm that each field serialises under its
wire name and is left out when unset.

Fields covered:

- ``ImageGenerationRequest.frame_count`` / ``frame_duration_ms``
- ``ImageOptions.frame_count`` / ``frame_duration_ms``
- ``SearchRequest.mode``
- ``VideoEditRequest.width`` / ``height``
- ``VideoGenerateRequest.width`` / ``height``
- ``VideoGenerationRequest.width`` / ``height``
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import pytest

from meshapi import _types

# (model name, field name, sample value)
NEW_FIELDS: List[Tuple[str, str, Any]] = [
    ("ImageGenerationRequest", "frame_count", 4),
    ("ImageGenerationRequest", "frame_duration_ms", 120),
    ("ImageOptions", "frame_count", 4),
    ("ImageOptions", "frame_duration_ms", 120),
    ("SearchRequest", "mode", "vector"),
    ("VideoEditRequest", "width", 1080),
    ("VideoEditRequest", "height", 1920),
    ("VideoGenerateRequest", "width", 1080),
    ("VideoGenerateRequest", "height", 1920),
    ("VideoGenerationRequest", "width", 1080),
    ("VideoGenerationRequest", "height", 1920),
]


def _model(name: str) -> Any:
    model = getattr(_types, name, None)
    if model is None:
        pytest.skip(f"{name} is not exposed by meshapi._types")
    return model


@pytest.mark.parametrize("model_name, field, _value", NEW_FIELDS)
def test_field_is_declared(model_name: str, field: str, _value: Any) -> None:
    model = _model(model_name)
    assert field in model.model_fields, f"{model_name}.{field} is missing"


@pytest.mark.parametrize("model_name, field, _value", NEW_FIELDS)
def test_field_is_optional(model_name: str, field: str, _value: Any) -> None:
    model = _model(model_name)
    info = model.model_fields.get(field)
    assert info is not None, f"{model_name}.{field} is missing"
    assert not info.is_required(), f"{model_name}.{field} must be optional"


@pytest.mark.parametrize("model_name, field, value", NEW_FIELDS)
def test_field_serialises_when_set(model_name: str, field: str, value: Any) -> None:
    model = _model(model_name)
    if field not in model.model_fields:
        pytest.fail(f"{model_name}.{field} is missing")
    instance = model.model_construct(**{field: value})
    dumped: Dict[str, Any] = instance.model_dump(by_alias=True, exclude_unset=True)
    assert dumped.get(field) == value


@pytest.mark.parametrize("model_name, field, _value", NEW_FIELDS)
def test_field_omitted_when_unset(model_name: str, field: str, _value: Any) -> None:
    model = _model(model_name)
    if field not in model.model_fields:
        pytest.fail(f"{model_name}.{field} is missing")
    instance = model.model_construct()
    dumped: Dict[str, Any] = instance.model_dump(by_alias=True, exclude_none=True)
    assert field not in dumped
