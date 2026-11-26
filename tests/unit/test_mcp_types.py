from typing import get_args

import pytest
from pydantic import ValidationError

from meshapi._mcp_types import McpTool, OrgPermissionMcp


def test_mcp_tool_defaults_serialise() -> None:
    tool = McpTool(server_label="docs")
    assert tool.to_request() == {
        "type": "mcp",
        "server_label": "docs",
        "require_approval": "never",
    }


def test_mcp_tool_allowed_tools() -> None:
    tool = McpTool(server_label="docs", allowed_tools=["search"])
    assert tool.to_request()["allowed_tools"] == ["search"]


def test_mcp_tool_rejects_other_approval_modes() -> None:
    with pytest.raises(ValidationError):
        McpTool(server_label="docs", require_approval="always")  # type: ignore[arg-type]


def test_mcp_tool_requires_label() -> None:
    with pytest.raises(ValidationError):
        McpTool()  # type: ignore[call-arg]


def test_mcp_tool_parses_from_dict() -> None:
    tool = McpTool.model_validate({"type": "mcp", "server_label": "x"})
    assert tool.server_label == "x"


def test_org_permission_values() -> None:
    assert set(get_args(OrgPermissionMcp)) == {"mcp_servers:read", "mcp_servers:write"}
