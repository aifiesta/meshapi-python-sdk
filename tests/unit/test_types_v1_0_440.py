from meshapi._types_v1_0_440 import (
    MCP_SERVERS_READ,
    MCP_SERVERS_WRITE,
    McpTool,
    WebSearchImage,
)


def test_mcp_tool_serializes_with_defaults():
    tool = McpTool(server_label="docs")
    assert tool.model_dump(exclude_none=True) == {
        "type": "mcp",
        "server_label": "docs",
        "require_approval": "never",
    }


def test_mcp_tool_parses_from_dict():
    tool = McpTool.model_validate(
        {"type": "mcp", "server_label": "docs", "require_approval": "never"}
    )
    assert tool.server_label == "docs"


def test_web_search_image_optional_fields():
    image = WebSearchImage.model_validate({"url": "https://example.com/a.png"})
    assert image.url == "https://example.com/a.png"
    assert image.title is None
    assert image.description is None


def test_web_search_image_full():
    image = WebSearchImage.model_validate(
        {"url": "https://example.com/a.png", "title": "A", "description": "An image"}
    )
    assert image.title == "A"
    assert image.description == "An image"


def test_org_permission_values():
    assert MCP_SERVERS_READ == "mcp_servers:read"
    assert MCP_SERVERS_WRITE == "mcp_servers:write"
