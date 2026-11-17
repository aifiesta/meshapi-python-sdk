"""Unit tests for the animated GIF frame fields on image requests.

`ImageGenerationRequest` and `ImageOptions` accept two optional fields used
with `output_format="gif"`:

- `frame_count`: number of frames in the GIF (2-16).
- `frame_duration_ms`: display time of each frame in milliseconds (>= 20).

Both fields are optional and default to `None`, so existing requests are
unchanged.
"""

from __future__ import annotations

import typing

import pytest

from meshapi import _types

GIF_FIELDS = ("frame_count", "frame_duration_ms")
MODELS_WITH_GIF_FIELDS = ("ImageGenerationRequest", "ImageOptions")


def _model(name: str):
    model = getattr(_types, name, None)
    assert model is not None, f"meshapi._types.{name} is missing"
    return model


@pytest.mark.parametrize("model_name", MODELS_WITH_GIF_FIELDS)
@pytest.mark.parametrize("field", GIF_FIELDS)
def test_gif_field_is_declared(model_name: str, field: str) -> None:
    model = _model(model_name)
    assert field in model.model_fields, f"{model_name}.{field} is not declared"


@pytest.mark.parametrize("model_name", MODELS_WITH_GIF_FIELDS)
@pytest.mark.parametrize("field", GIF_FIELDS)
def test_gif_field_is_optional_and_defaults_to_none(model_name: str, field: str) -> None:
    info = _model(model_name).model_fields[field]
    assert info.is_required() is False
    assert info.default is None


@pytest.mark.parametrize("model_name", MODELS_WITH_GIF_FIELDS)
@pytest.mark.parametrize("field", GIF_FIELDS)
def test_gif_field_accepts_int(model_name: str, field: str) -> None:
    annotation = _model(model_name).model_fields[field].annotation
    args = typing.get_args(annotation)
    assert annotation is int or int in args, f"{model_name}.{field} should be Optional[int]"


@pytest.mark.parametrize("model_name", MODELS_WITH_GIF_FIELDS)
def test_gif_fields_serialise_when_set(model_name: str) -> None:
    model = _model(model_name)
    instance = model.model_construct(frame_count=4, frame_duration_ms=120)
    assert instance.frame_count == 4
    assert instance.frame_duration_ms == 120


@pytest.mark.parametrize("model_name", MODELS_WITH_GIF_FIELDS)
def test_gif_fields_unset_by_default(model_name: str) -> None:
    model = _model(model_name)
    instance = model.model_construct()
    assert getattr(instance, "frame_count", None) is None
    assert getattr(instance, "frame_duration_ms", None) is None
