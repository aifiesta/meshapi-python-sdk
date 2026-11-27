"""Request and response models added in API spec v1.0.438.

Covers:

* ``McpTool``: a tool entry for ``ResponsesRequest.tools`` that names a
  registered MCP server.
* Animated image options (``frame_count``, ``frame_duration_ms``) for
  ``ImageGenerationRequest`` and ``ImageOptions``.
* Output dimensions (``width``, ``height``) for video generate and edit
  requests.
* Image results for web search (``include_images``,
  ``include_image_descriptions`` and ``WebSearchResponse.images``).
* ``SearchRequest.mode``.
* The ``mcp_servers:read`` and ``mcp_servers:write`` organisation
  permissions.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

try:  # Python 3.8+ has Literal in typing; kept explicit for clarity.
    from typing import Literal
except ImportError:  # pragma: no cover
    from typing_extensions import Literal  # type: ignore


# ---------------------------------------------------------------------------
# Organisation permissions
# ---------------------------------------------------------------------------

MCP_SERVERS_READ = "mcp_servers:read"
"""Permission to list and read the organisation's registered MCP servers."""

MCP_SERVERS_WRITE = "mcp_servers:write"
"""Permission to register, update and delete the organisation's MCP servers."""

MCP_ORG_PERMISSIONS = (MCP_SERVERS_READ, MCP_SERVERS_WRITE)
"""``OrgPermission`` values added for MCP server management."""


# ---------------------------------------------------------------------------
# Responses: MCP tool
# ---------------------------------------------------------------------------


class McpTool(BaseModel):
    """A ``ResponsesRequest.tools`` entry that exposes a registered MCP server.

    The gateway runs the server's tools for you and returns the final answer.
    ``server_label`` must match a server registered for your organisation, and
    ``require_approval`` must be ``"never"`` on ``/v1/responses``.

    Example::

        McpTool(server_label="docs", require_approval="never")
    """

    model_config = ConfigDict(extra="allow")

    type: Literal["mcp"] = "mcp"
    server_label: str
    require_approval: Optional[str] = "never"
    allowed_tools: Optional[List[str]] = None


# ---------------------------------------------------------------------------
# Images: animated output
# ---------------------------------------------------------------------------


class ImageFrameOptions(BaseModel):
    """Animated-image fields shared by ``ImageGenerationRequest`` and ``ImageOptions``.

    Attributes:
        frame_count: Number of frames to generate for an animated image.
        frame_duration_ms: Display time of each frame, in milliseconds.
    """

    model_config = ConfigDict(extra="allow")

    frame_count: Optional[int] = Field(default=None, ge=1)
    frame_duration_ms: Optional[int] = Field(default=None, ge=1)


# ---------------------------------------------------------------------------
# Video: output dimensions
# ---------------------------------------------------------------------------


class VideoDimensions(BaseModel):
    """Output size fields for ``VideoGenerationRequest``, ``VideoGenerateRequest``
    and ``VideoEditRequest``.

    Attributes:
        width: Output width in pixels.
        height: Output height in pixels.
    """

    model_config = ConfigDict(extra="allow")

    width: Optional[int] = Field(default=None, ge=1)
    height: Optional[int] = Field(default=None, ge=1)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


class SearchModeOptions(BaseModel):
    """The ``SearchRequest.mode`` field.

    Attributes:
        mode: Search mode to use. Unknown values are passed through unchanged;
            an unsupported mode is rejected by the API.
    """

    model_config = ConfigDict(extra="allow")

    mode: Optional[str] = None


class WebSearchImageOptions(BaseModel):
    """Image fields for ``WebSearchRequest``.

    Attributes:
        include_images: Return images related to the query in ``images``.
        include_image_descriptions: Add a ``description`` to each image.
            Requires ``include_images``.
    """

    model_config = ConfigDict(extra="allow")

    include_images: Optional[bool] = None
    include_image_descriptions: Optional[bool] = None


class WebSearchImage(BaseModel):
    """One entry of ``WebSearchResponse.images``."""

    model_config = ConfigDict(extra="allow")

    url: str
    title: Optional[str] = None
    description: Optional[str] = None


class WebSearchImages(BaseModel):
    """The ``WebSearchResponse.images`` field.

    ``images`` is ``None`` when images were not requested and an empty list
    when none were found.
    """

    model_config = ConfigDict(extra="allow")

    images: Optional[List[WebSearchImage]] = None


__all__ = [
    "MCP_SERVERS_READ",
    "MCP_SERVERS_WRITE",
    "MCP_ORG_PERMISSIONS",
    "McpTool",
    "ImageFrameOptions",
    "VideoDimensions",
    "SearchModeOptions",
    "WebSearchImageOptions",
    "WebSearchImage",
    "WebSearchImages",
]
