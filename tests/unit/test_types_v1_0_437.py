"""Unit tests for the models added in spec v1.0.437."""

import pytest
from pydantic import ValidationError

from meshapi._types_ext import (
    ORG_PERMISSION_MCP_SERVERS_READ,
    ORG_PERMISSION_MCP_SERVERS_WRITE,
    ImageFrameOptions,
    McpTool,
    SearchModeOptions,
    VideoDimensions,
    WebSearchImageOptions,
    WebSearchImagesResult,
    drop_none,
)


def test_image_frame_options_serialise():
    opts = ImageFrameOptions(frame_count=4, frame_duration_ms=120)
    assert opts.model_dump(exclude_none=True) == {
        "frame_count": 4,
        "frame_duration_ms": 120,
    }


def test_image_frame_options_default_to_unset():
    assert ImageFrameOptions().model_dump(exclude_none=True) == {}


def test_image_frame_count_must_be_positive():
    with pytest.raises(ValidationError):
        ImageFrameOptions(frame_count=0)


def test_video_dimensions_serialise():
    dims = VideoDimensions(width=1280, height=720)
    assert dims.model_dump(exclude_none=True) == {"width": 1280, "height": 720}


def test_mcp_tool_defaults():
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


def test_web_search_image_options():
    opts = WebSearchImageOptions(include_images=True, include_image_descriptions=True)
    assert opts.model_dump(exclude_none=True) == {
        "include_images": True,
        "include_image_descriptions": True,
    }


def test_web_search_images_parse():
    result = WebSearchImagesResult.model_validate(
        {"images": [{"url": "https://example.com/a.png", "title": "A", "description": None}]}
    )
    assert result.images is not None
    assert result.images[0].url == "https://example.com/a.png"
    assert result.images[0].title == "A"


def test_web_search_images_null_and_empty():
    assert WebSearchImagesResult.model_validate({"images": None}).images is None
    assert WebSearchImagesResult.model_validate({"images": []}).images == []
    assert WebSearchImagesResult.model_validate({}).images is None


def test_search_mode():
    assert SearchModeOptions(mode="fast").model_dump() == {"mode": "fast"}


def test_mcp_permission_values():
    assert ORG_PERMISSION_MCP_SERVERS_READ == "mcp_servers:read"
    assert ORG_PERMISSION_MCP_SERVERS_WRITE == "mcp_servers:write"


def test_drop_none():
    assert drop_none({"a": 1, "b": None}) == {"a": 1}
