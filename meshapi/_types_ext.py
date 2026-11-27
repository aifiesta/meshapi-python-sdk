"""Pydantic models added for API spec v1.0.437.

These models cover the additive changes in this spec version:

- ``frame_count`` / ``frame_duration_ms`` on image generation requests and
  image options, for animated (multi-frame) image output.
- ``width`` / ``height`` on video generation and video edit requests.
- ``McpTool``, a new member of the ``ResponsesRequest.tools`` union.
- ``include_images`` / ``include_image_descriptions`` on web search requests,
  and ``images`` on web search responses.
- ``mode`` on search requests.
- ``mcp_servers:read`` / ``mcp_servers:write`` organisation permissions.

All new fields are optional. Existing requests serialise exactly as before.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ORG_PERMISSION_MCP_SERVERS_READ",
    "ORG_PERMISSION_MCP_SERVERS_WRITE",
    "McpOrgPermission",
    "ImageFrameOptions",
    "VideoDimensions",
    "McpTool",
    "WebSearchImageOptions",
    "WebSearchImage",
    "WebSearchImagesResult",
    "SearchModeOptions",
    "drop_none",
]


# ---------------------------------------------------------------------------
# Organisation permissions
# ---------------------------------------------------------------------------

ORG_PERMISSION_MCP_SERVERS_READ = "mcp_servers:read"
"""Permission to list and read an organisation's registered MCP servers."""

ORG_PERMISSION_MCP_SERVERS_WRITE = "mcp_servers:write"
"""Permission to create, update and delete an organisation's MCP servers."""

McpOrgPermission = Literal["mcp_servers:read", "mcp_servers:write"]
"""The ``OrgPermission`` values added for MCP server management."""


# ---------------------------------------------------------------------------
# Images: multi-frame output
# ---------------------------------------------------------------------------


class ImageFrameOptions(BaseModel):
    """Frame settings shared by ``ImageGenerationRequest`` and ``ImageOptions``.

    Attributes:
        frame_count: Number of frames to generate for animated output.
        frame_duration_ms: Display time of each frame, in milliseconds.
    """

    model_config = ConfigDict(extra="allow")

    frame_count: Optional[int] = Field(default=None, ge=1)
    frame_duration_ms: Optional[int] = Field(default=None, ge=1)


# ---------------------------------------------------------------------------
# Video: output dimensions
# ---------------------------------------------------------------------------


class VideoDimensions(BaseModel):
    """Output size for ``VideoGenerateRequest``, ``VideoGenerationRequest`` and
    ``VideoEditRequest``.

    Attributes:
        width: Output width in pixels.
        height: Output height in pixels.
    """

    model_config = ConfigDict(extra="allow")

    width: Optional[int] = Field(default=None, ge=1)
    height: Optional[int] = Field(default=None, ge=1)


# ---------------------------------------------------------------------------
# Responses: MCP tool
# ---------------------------------------------------------------------------


class McpTool(BaseModel):
    """An MCP tool entry for ``ResponsesRequest.tools``.

    Names a server registered for your organisation by ``server_label``. The
    gateway lists that server's tools, runs the calls and returns the final
    answer.

    Attributes:
        type: Always ``"mcp"``.
        server_label: Label of a registered MCP server.
        require_approval: Approval policy. The gateway currently requires
            ``"never"``.
        allowed_tools: Optional subset of the server's tool names to expose.
    """

    model_config = ConfigDict(extra="allow")

    type: Literal["mcp"] = "mcp"
    server_label: str
    require_approval: Optional[Union[str, Dict[str, Any]]] = "never"
    allowed_tools: Optional[List[str]] = None


# ---------------------------------------------------------------------------
# Web search: images
# ---------------------------------------------------------------------------


class WebSearchImageOptions(BaseModel):
    """Image options for ``WebSearchRequest``.

    Attributes:
        include_images: Return related images alongside results.
        include_image_descriptions: Add a description to each image. Requires
            ``include_images``.
    """

    model_config = ConfigDict(extra="allow")

    include_images: Optional[bool] = None
    include_image_descriptions: Optional[bool] = None


class WebSearchImage(BaseModel):
    """One image in ``WebSearchResponse.images``."""

    model_config = ConfigDict(extra="allow")

    url: str
    title: Optional[str] = None
    description: Optional[str] = None


class WebSearchImagesResult(BaseModel):
    """The ``images`` field of ``WebSearchResponse``.

    ``images`` is ``None`` when images were not requested and an empty list
    when none were found.
    """

    model_config = ConfigDict(extra="allow")

    images: Optional[List[WebSearchImage]] = None


# ---------------------------------------------------------------------------
# Search: mode
# ---------------------------------------------------------------------------


class SearchModeOptions(BaseModel):
    """The ``mode`` field of ``SearchRequest``."""

    model_config = ConfigDict(extra="allow")

    mode: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def drop_none(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Return ``payload`` without keys whose value is ``None``.

    Used so unset optional fields are never sent on the wire.
    """
    return {k: v for k, v in payload.items() if v is not None}
