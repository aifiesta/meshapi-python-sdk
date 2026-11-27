"""Unit tests for types added in API spec v1.0.439."""

from meshapi._spec_additions import (
    ORG_PERMISSIONS_V1_0_439,
    McpTool,
    WebSearchImage,
    WebSearchImages,
)


def test_mcp_tool_serialises_for_responses_tools():
    tool = McpTool(server_label="docs")
    assert tool.to_request_dict() == {
        "type": "mcp",
        "server_label": "docs",
        "require_approval": "never",
    }


def test_mcp_tool_keeps_allowed_tools_and_extra_keys():
    tool = McpTool(server_label="docs", allowed_tools=["search"], headers={"x": "y"})
    data = tool.to_request_dict()
    assert data["allowed_tools"] == ["search"]
    assert data["headers"] == {"x": "y"}


def test_web_search_images_absent_is_none():
    parsed = WebSearchImages.model_validate({})
    assert parsed.images is None


def test_web_search_images_empty_list():
    parsed = WebSearchImages.model_validate({"images": []})
    assert parsed.images == []


def test_web_search_images_parse_items():
    parsed = WebSearchImages.model_validate(
        {
            "images": [
                {"url": "https://example.com/a.png", "title": "A", "description": "An image"},
                {"url": "https://example.com/b.png"},
            ]
        }
    )
    assert parsed.images is not None
    first, second = parsed.images
    assert isinstance(first, WebSearchImage)
    assert first.title == "A"
    assert first.description == "An image"
    assert second.title is None
    assert second.description is None


def test_org_permissions_include_mcp_servers():
    assert "mcp_servers:read" in ORG_PERMISSIONS_V1_0_439
    assert "mcp_servers:write" in ORG_PERMISSIONS_V1_0_439
