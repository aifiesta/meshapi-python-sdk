"""Pydantic models for MCP tools on ``/v1/responses``.

These models describe the ``McpTool`` member of ``ResponsesRequest.tools``.
It was added to the public spec in v1.0.434.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict

__all__ = ["McpTool", "OrgPermissionMcp"]


OrgPermissionMcp = Literal["mcp_servers:read", "mcp_servers:write"]
"""Organization permissions that govern access to registered MCP servers."""


class McpTool(BaseModel):
    """A tool entry that points a Responses request at a registered MCP server.

    Pass it in ``tools`` on ``client.responses.create``. The gateway lists the
    server's tools, runs the calls, and returns the model's final answer.

    Args:
        server_label: Label of an MCP server registered for your organization.
        require_approval: Must be ``"never"``; the gateway runs calls without
            asking for approval.
        allowed_tools: Optional subset of the server's tool names to expose.

    Example:
        >>> tool = McpTool(server_label="docs")
        >>> tool.model_dump(exclude_none=True)
        {'type': 'mcp', 'server_label': 'docs', 'require_approval': 'never'}
    """

    model_config = ConfigDict(extra="allow")

    type: Literal["mcp"] = "mcp"
    server_label: str
    require_approval: Literal["never"] = "never"
    allowed_tools: Optional[List[str]] = None

    def to_request(self) -> Dict[str, Any]:
        """Return the JSON-ready dict for the ``tools`` array."""
        return self.model_dump(exclude_none=True)
