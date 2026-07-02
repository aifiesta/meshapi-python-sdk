"""Live tests for /v1/video/generations endpoints."""

from __future__ import annotations

import os

import pytest
from meshapi import MeshAPI, VideoGenerationParams, VideoContentItem, ListVideoGenerationsParams

# No hardcoded fallback: video generation is costly, so the generate test only
# runs when a model is explicitly configured (skipped in CI by default).
VIDEO_MODEL = os.environ.get("MESHAPI_VIDEO_GEN_MODEL")


def test_video_list(client: MeshAPI) -> None:
    listing = client.videos.list(ListVideoGenerationsParams(limit=5))
    assert listing.data is not None
    print(f"[PASS] videos.list -> total={listing.total}, items={len(listing.data)}")


def test_video_generate_and_retrieve(client: MeshAPI) -> None:
    if not VIDEO_MODEL:
        pytest.skip("set MESHAPI_VIDEO_GEN_MODEL to run video generation (costly; skipped in CI by default)")
    params = VideoGenerationParams(
        model=VIDEO_MODEL,
        content=[VideoContentItem(type="text", text="A serene mountain lake at sunrise")],
    )
    resp = client.videos.generate(params)
    assert resp.id
    print(f"[PASS] videos.generate -> task_id={resp.id}")

    task = client.videos.retrieve(resp.id)
    assert task.id == resp.id
    assert task.status
    print(f"[PASS] videos.retrieve -> status={task.status}")
