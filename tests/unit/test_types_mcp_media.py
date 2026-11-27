"""Serialisation tests for the models added in API spec v1.0.438."""

import pytest
from pydantic import ValidationError

from meshapi._types_mcp_media import (
    MCP_ORG_PERMISSIONS,
    MCP_SERVERS_READ,
    MCP_SERVERS_WRITE,
    ImageFrameOptions,
    McpTool,
    SearchModeOptions,
    VideoDimensions,
    WebSearchImageOptions,
    WebSearchImages,
)


def test_mcp_tool_serialises_with_type_and_label():
    tool = McpTool(server_label="docs")
    assert tool.model_dump(exclude_none=True) == {
        "type": "mcp",
        "server_label": "docs",
        "require_approval": "never",
    }


def test_mcp_tool_requires_server_label():
    with pytest.raises(ValidationError):
        McpTool()  # type: ignore[call-arg]


def test_mcp_tool_rejects_other_type():
    with pytest.raises(ValidationError):
        McpTool(type="function", server_label="docs")  # type: ignore[arg-type]


def test_image_frame_options_round_trip():
    opts = ImageFrameOptions(frame_count=8, frame_duration_ms=120)
    assert opts.model_dump(exclude_none=True) == {"frame_count": 8, "frame_duration_ms": 120}
    assert ImageFrameOptions().model_dump(exclude_none=True) == {}


def test_image_frame_options_reject_zero():
    with pytest.raises(ValidationError):
        ImageFrameOptions(frame_count=0)


def test_video_dimensions_round_trip():
    dims = VideoDimensions(width=1280, height=720)
    assert dims.model_dump(exclude_none=True) == {"width": 1280, "height": 720}


def test_search_mode_passes_through():
    assert SearchModeOptions(mode="fast").model_dump(exclude_none=True) == {"mode": "fast"}


def test_web_search_image_options():
    opts = WebSearchImageOptions(include_images=True, include_image_descriptions=True)
    assert opts.model_dump(exclude_none=True) == {
        "include_images": True,
        "include_image_descriptions": True,
    }


def test_web_search_images_parse_null_empty_and_items():
    assert WebSearchImages.model_validate({"images": None}).images is None
    assert WebSearchImages.model_validate({"images": []}).images == []
    parsed = WebSearchImages.model_validate(
        {"images": [{"url": "https://example.com/a.png", "title": "A", "description": "An image"}]}
    )
    assert parsed.images is not None
    assert parsed.images[0].url == "https://example.com/a.png"
    assert parsed.images[0].title == "A"
    assert parsed.images[0].description == "An image"


def test_org_permission_values():
    assert MCP_SERVERS_READ == "mcp_servers:read"
    assert MCP_SERVERS_WRITE == "mcp_servers:write"
    assert set(MCP_ORG_PERMISSIONS) == {"mcp_servers:read", "mcp_servers:write"}
