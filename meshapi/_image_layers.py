"""Layer decomposition options for image generation requests.

Models that support layer decomposition can split an input image into a
base image plus a set of PNG layers. Enable it by sending
``layer_decomposition`` and, optionally, ``layer_decomposition_options`` in
the body of ``POST /v1/images/generations``, or in ``ImageOptions`` when
images are produced through ``POST /v1/chat/completions``.

A decomposition requested on a model that does not support it is rejected by
the API with a 400. An explicit ``layer_decomposition=False`` has no effect,
so :func:`layer_decomposition_params` omits it from the payload.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

__all__ = ["LayerDecompositionOptions", "layer_decomposition_params"]


class LayerDecompositionOptions(BaseModel):
    """Options for ``layer_decomposition_options``.

    Attributes:
        max_images: Upper bound on the number of images returned for the
            decomposition. Omit to use the provider default.
        text_recognition: Ask the provider to recognise text in each layer.
    """

    model_config = ConfigDict(extra="allow")

    max_images: Optional[int] = Field(default=None, ge=1)
    text_recognition: Optional[bool] = None

    def to_payload(self) -> Dict[str, Any]:
        """Return the JSON-ready dict, dropping unset fields."""
        return self.model_dump(exclude_none=True)


OptionsInput = Union[LayerDecompositionOptions, Mapping[str, Any], None]


def layer_decomposition_params(
    enabled: Optional[bool] = True,
    options: OptionsInput = None,
) -> Dict[str, Any]:
    """Build the ``layer_decomposition`` fields for an image request body.

    Merge the result into the keyword arguments or ``extra_body`` of an image
    generation call, or into an ``ImageOptions`` payload.

    Args:
        enabled: Whether to request layer decomposition. ``False`` or
            ``None`` returns an empty dict, because the field is inert.
        options: A :class:`LayerDecompositionOptions` or an equivalent mapping.

    Returns:
        A dict with ``layer_decomposition`` and, when given,
        ``layer_decomposition_options``.

    Raises:
        ValueError: If ``options`` is given while decomposition is disabled.
    """
    if not enabled:
        if options is not None:
            raise ValueError(
                "layer_decomposition_options requires layer_decomposition=True"
            )
        return {}

    params: Dict[str, Any] = {"layer_decomposition": True}
    if options is not None:
        if not isinstance(options, LayerDecompositionOptions):
            options = LayerDecompositionOptions.model_validate(dict(options))
        payload = options.to_payload()
        if payload:
            params["layer_decomposition_options"] = payload
    return params
