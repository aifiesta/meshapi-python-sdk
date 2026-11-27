"""Types added in API spec v1.0.439.

These models are additive and do not change any existing request or response
shape. They are defined here so they can be imported directly while they are
wired into ``meshapi._types`` and the public ``meshapi`` namespace.

Additions covered:

- ``McpTool``: a tool entry for ``ResponsesRequest.tools`` that names a
  registered MCP server. The gateway runs the server's tools and returns the
  final answer.
- ``WebSearchImage``: an item of ``WebSearchResponse.images``, returned when
  ``include_images`` is set on a web search request.
- ``ORG_PERMISSIONS_V1_0_439``: the ``OrgPermission`` values added in this
  release (``mcp_servers:read`` and ``mcp_servers:write``).
- Field name constants for new optional request fields on image, video and
  search requests.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

try:  # Python 3.9 lacks typing.Literal in older patch releases only via typing_extensions
    from typing import Literal
except ImportError:  # pragma: no cover
    from typing_extensions import Literal  # type: ignore


# ---------------------------------------------------------------------------
# Responses: MCP tool
# ---------------------------------------------------------------------------


class McpTool(BaseModel):
    """A tool entry that exposes a registered MCP server to ``/v1/responses``.

    The gateway lists the server's tools, runs any calls the model makes and
    sends the results back until the model answers.

    Attributes:
        type: Always ``"mcp"``.
        server_label: Label of an MCP server registered for your organization.
        require_approval: Approval mode. The gateway currently requires
            ``"never"``.
        allowed_tools: Optional subset of the server's tool names to expose.
    """

    model_config = ConfigDict(extra="allow")

    type: Literal["mcp"] = "mcp"
    server_label: str
    require_approval: Optional[str] = "never"
    allowed_tools: Optional[List[str]] = None

    def to_request_dict(self) -> Dict[str, Any]:
        """Return the JSON-ready dict for ``ResponsesRequest.tools``."""
        return self.model_dump(exclude_none=True)


# ---------------------------------------------------------------------------
# Web search: images
# ---------------------------------------------------------------------------


class WebSearchImage(BaseModel):
    """An image returned in ``WebSearchResponse.images``.

    ``images`` is ``None`` when images were not requested and an empty list
    when none were found.

    Attributes:
        url: Image URL.
        title: Image title, when the search provider returns one.
        description: Image description, returned when
            ``include_image_descriptions`` is set.
    """

    model_config = ConfigDict(extra="allow")

    url: str
    title: Optional[str] = None
    description: Optional[str] = None


class WebSearchImages(BaseModel):
    """Helper for reading the ``images`` field of a web search response."""

    model_config = ConfigDict(extra="allow")

    images: Optional[List[WebSearchImage]] = Field(default=None)


# ---------------------------------------------------------------------------
# Organization permissions
# ---------------------------------------------------------------------------

ORG_PERMISSIONS_V1_0_439 = ("mcp_servers:read", "mcp_servers:write")
"""``OrgPermission`` values added in v1.0.439."""


# ---------------------------------------------------------------------------
# New optional request fields
# ---------------------------------------------------------------------------

IMAGE_REQUEST_FIELDS_V1_0_439 = ("frame_count", "frame_duration_ms")
"""Optional fields added to ``ImageGenerationRequest`` and ``ImageOptions``."""

VIDEO_REQUEST_FIELDS_V1_0_439 = ("width", "height")
"""Optional fields added to video generate, generation and edit requests."""

SEARCH_REQUEST_FIELDS_V1_0_439 = ("mode",)
"""Optional field added to ``SearchRequest``."""

WEB_SEARCH_REQUEST_FIELDS_V1_0_439 = ("include_images", "include_image_descriptions")
"""Optional fields added to ``WebSearchRequest``."""


__all__ = [
    "McpTool",
    "WebSearchImage",
    "WebSearchImages",
    "ORG_PERMISSIONS_V1_0_439",
    "IMAGE_REQUEST_FIELDS_V1_0_439",
    "VIDEO_REQUEST_FIELDS_V1_0_439",
    "SEARCH_REQUEST_FIELDS_V1_0_439",
    "WEB_SEARCH_REQUEST_FIELDS_V1_0_439",
]
