"""Pydantic models added for API spec v1.0.440.

These models are kept in a separate module so they can be merged into
``_types.py`` without overwriting existing definitions. Re-export them from
``meshapi/__init__.py`` and add them to ``__all__``.
"""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict

__all__ = [
    "McpTool",
    "WebSearchImage",
    "MCP_SERVERS_READ",
    "MCP_SERVERS_WRITE",
    "NEW_ORG_PERMISSIONS",
]


# ---------------------------------------------------------------------------
# Responses: MCP tool
# ---------------------------------------------------------------------------


class McpTool(BaseModel):
    """A tool entry for ``ResponsesRequest.tools`` that names a registered MCP server.

    The gateway runs the server's tools on your behalf and returns the final
    answer. ``require_approval`` must be ``"never"``.

    Example::

        McpTool(server_label="docs")
    """

    model_config = ConfigDict(extra="allow")

    type: Literal["mcp"] = "mcp"
    server_label: str
    require_approval: Literal["never"] = "never"
    allowed_tools: Optional[List[str]] = None


# ---------------------------------------------------------------------------
# Web search: images
# ---------------------------------------------------------------------------


class WebSearchImage(BaseModel):
    """An image returned in ``WebSearchResponse.images``.

    ``images`` is ``None`` when ``include_images`` was not requested and an
    empty list when no images were found. ``description`` is set only when
    ``include_image_descriptions`` is true.
    """

    model_config = ConfigDict(extra="allow")

    url: str
    title: Optional[str] = None
    description: Optional[str] = None


# ---------------------------------------------------------------------------
# Organization permissions
# ---------------------------------------------------------------------------

MCP_SERVERS_READ = "mcp_servers:read"
"""Org permission to list and read registered MCP servers."""

MCP_SERVERS_WRITE = "mcp_servers:write"
"""Org permission to register, update and delete MCP servers."""

NEW_ORG_PERMISSIONS = (MCP_SERVERS_READ, MCP_SERVERS_WRITE)
