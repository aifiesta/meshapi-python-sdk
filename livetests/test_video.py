"""Live tests for /v1/video/generations endpoints."""

from __future__ import annotations

import os

from meshapi import MeshAPI, VideoGenerationParams, VideoContentItem, ListVideoGenerationsParams

VIDEO_MODEL = os.environ.get("MESHAPI_VIDEO_GEN_MODEL", "byteplus/dreamina-seedance-2-0")


def test_video_list(client: MeshAPI) -> None:
    listing = client.videos.list(ListVideoGenerationsParams(limit=5))
    assert listing.data is not None
    print(f"[PASS] videos.list -> total={listing.total}, items={len(listing.data)}")


def test_video_generate_and_retrieve(client: MeshAPI) -> None:
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
