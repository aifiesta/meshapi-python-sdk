import pytest
from pydantic import ValidationError

from meshapi._image_layers import (
    LayerDecompositionOptions,
    layer_decomposition_params,
)


def test_enabled_without_options():
    assert layer_decomposition_params() == {"layer_decomposition": True}


def test_enabled_with_model_options():
    opts = LayerDecompositionOptions(max_images=5, text_recognition=True)
    assert layer_decomposition_params(True, opts) == {
        "layer_decomposition": True,
        "layer_decomposition_options": {"max_images": 5, "text_recognition": True},
    }


def test_enabled_with_mapping_options_drops_unset():
    assert layer_decomposition_params(True, {"max_images": 3}) == {
        "layer_decomposition": True,
        "layer_decomposition_options": {"max_images": 3},
    }


def test_empty_options_are_omitted():
    assert layer_decomposition_params(True, LayerDecompositionOptions()) == {
        "layer_decomposition": True
    }


@pytest.mark.parametrize("enabled", [False, None])
def test_disabled_is_omitted(enabled):
    assert layer_decomposition_params(enabled) == {}


def test_options_without_enabled_raise():
    with pytest.raises(ValueError):
        layer_decomposition_params(False, {"max_images": 2})


def test_max_images_must_be_positive():
    with pytest.raises(ValidationError):
        LayerDecompositionOptions(max_images=0)


def test_options_parse_from_json():
    opts = LayerDecompositionOptions.model_validate(
        {"max_images": 10, "text_recognition": False}
    )
    assert opts.max_images == 10
    assert opts.text_recognition is False


def test_unknown_option_fields_are_kept():
    opts = LayerDecompositionOptions.model_validate({"future_flag": 1})
    assert opts.to_payload() == {"future_flag": 1}
