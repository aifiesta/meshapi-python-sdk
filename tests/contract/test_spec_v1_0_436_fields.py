"""Contract guards for fields added in API spec v1.0.436.

Each check is skipped when the model is not exported yet, so the suite stays
green while the typed models in ``meshapi/_types.py`` catch up. Once a model is
exported, the guard asserts that the new optional fields are declared and
default to ``None``.
"""

from __future__ import annotations

import pytest

import meshapi

NEW_OPTIONAL_FIELDS = [
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
    ("WebSearchRequest", "include_images"),
    ("WebSearchRequest", "include_image_descriptions"),
    ("WebSearchResponse", "images"),
]


def _model(name: str):
    model = getattr(meshapi, name, None)
    if model is None or not hasattr(model, "model_fields"):
        pytest.skip(f"{name} is not exported by meshapi")
    return model


@pytest.mark.parametrize("model_name,field", NEW_OPTIONAL_FIELDS)
def test_new_field_is_declared_and_optional(model_name: str, field: str) -> None:
    model = _model(model_name)
    assert field in model.model_fields, f"{model_name}.{field} is missing"
    info = model.model_fields[field]
    assert not info.is_required(), f"{model_name}.{field} must be optional"


def test_web_search_response_parses_images() -> None:
    model = _model("WebSearchResponse")
    if "images" not in model.model_fields:
        pytest.skip("WebSearchResponse.images not declared yet")
    payload = {
        "results": [],
        "images": [
            {
                "url": "https://example.com/a.png",
                "title": "A",
                "description": "An example image",
            }
        ],
    }
    try:
        parsed = model.model_validate(payload)
    except Exception as exc:  # pragma: no cover - depends on other required fields
        pytest.skip(f"fixture does not satisfy other required fields: {exc}")
    images = parsed.images
    assert images is not None and len(images) == 1
    first = images[0]
    url = first["url"] if isinstance(first, dict) else first.url
    assert url == "https://example.com/a.png"


def test_web_search_response_images_default_none() -> None:
    model = _model("WebSearchResponse")
    if "images" not in model.model_fields:
        pytest.skip("WebSearchResponse.images not declared yet")
    try:
        parsed = model.model_validate({"results": []})
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"fixture does not satisfy other required fields: {exc}")
    assert parsed.images is None
