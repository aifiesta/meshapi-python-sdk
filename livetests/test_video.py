"""Live tests: BytePlus Seedance video generation."""

from __future__ import annotations

import time

import pytest

from meshapi import MeshAPI, VideoGenerationParams, VideoContentItem


def _video_model(request_env: callable) -> str | None:
    return request_env("MESHAPI_VIDEO_GEN_MODEL")


def test_video_create_and_poll(client: MeshAPI, request) -> None:
    video_model = request.config.getoption("--video-gen-model", default=None) or \
        __import__("os").environ.get("MESHAPI_VIDEO_GEN_MODEL")
    if not video_model:
        pytest.skip("MESHAPI_VIDEO_GEN_MODEL not set")

    params = VideoGenerationParams(
        model=video_model,
        content=[VideoContentItem(type="text", text="A calm ocean wave at sunset.")],
        duration=4,
        resolution="480p",
        ratio="16:9",
    )

    # Create task
    task = client.videos.create(params)
    assert task.id, "expected task id"

    # Poll up to 3 minutes
    deadline = time.time() + 180
    while time.time() < deadline:
        result = client.videos.get(task.id)
        assert result.id == task.id

        if result.status in ("succeeded", "failed", "expired", "cancelled"):
            break
        time.sleep(10)

    assert result.status == "succeeded", (
        f"expected status=succeeded, got {result.status} "
        f"(error={result.error})"
    )
    assert result.content is not None, "expected content on succeeded task"
    assert result.content.video_url, "expected video_url on succeeded task"


async def test_video_create_and_poll_async(client: MeshAPI, request) -> None:
    """Same lifecycle test using the async client."""
    from meshapi import AsyncMeshAPI
    from config import BASE_URL, TOKEN

    video_model = __import__("os").environ.get("MESHAPI_VIDEO_GEN_MODEL")
    if not video_model:
        pytest.skip("MESHAPI_VIDEO_GEN_MODEL not set")

    async with AsyncMeshAPI(base_url=BASE_URL, token=TOKEN) as aclient:
        params = VideoGenerationParams(
            model=video_model,
            content=[VideoContentItem(type="text", text="A calm ocean wave at sunset.")],
            duration=4,
            resolution="480p",
            ratio="16:9",
        )

        task = await aclient.videos.create(params)
        assert task.id, "expected task id"

        deadline = time.time() + 180
        while time.time() < deadline:
            result = await aclient.videos.get(task.id)
            if result.status in ("succeeded", "failed", "expired", "cancelled"):
                break
            time.sleep(10)

        assert result.status == "succeeded", f"expected succeeded, got {result.status}"
        assert result.content and result.content.video_url
