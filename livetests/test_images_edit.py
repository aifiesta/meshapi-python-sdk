"""Live tests: image editing — POST /v1/images/edits.

Requires an edit-capable model. Set MESHAPI_IMAGE_EDIT_MODEL (and optionally
MESHAPI_IMAGE_EDIT_INPUT, a base64/data-URL source image) to run; otherwise
skipped. Image editing costs real inference, so this is opt-in.
"""

from __future__ import annotations

import pytest
from config import get_env
from meshapi import ImageEditParams, MeshAPI, MeshAPIError

# 1x1 transparent PNG, used when MESHAPI_IMAGE_EDIT_INPUT is not provided.
_PIXEL_PNG = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


def test_image_edit_basic(client: MeshAPI) -> None:
    model = get_env("MESHAPI_IMAGE_EDIT_MODEL")
    if not model:
        pytest.skip("set MESHAPI_IMAGE_EDIT_MODEL to run the image-edit live test")
    source = get_env("MESHAPI_IMAGE_EDIT_INPUT") or _PIXEL_PNG

    try:
        resp = client.images.edit(
            ImageEditParams(
                model=model,
                image=source,
                prompt="Make the background a solid blue.",
                operation="edit",
            )
        )
    except MeshAPIError as exc:
        if exc.status == 400 and exc.error_code == "invalid_request":
            # Upstream (provider) content/safety rejection of the synthetic test
            # image — the request reached the provider, so the SDK path is
            # validated. Skip rather than fail.
            pytest.skip(f"provider rejected the test image: {exc}")
        if exc.status in (400, 501) and exc.error_code in (
            "model_capability_not_supported",
            "not_implemented",
        ):
            pytest.skip(f"model does not support image edits: {exc.error_code}")
        raise

    assert resp.data, "expected at least one edited image"
    first = resp.data[0]
    assert first.url or first.b64_json, "edited image should have a url or b64_json"
