"""Cost breakdown and usage filter models.

These models describe the per-request cost breakdown returned on usage
rows and the filter accepted by the usage endpoints.
"""

from __future__ import annotations

from typing import Any, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

__all__ = ["CostLineOut", "CostBreakdownOut", "UsageFilter"]


# ---------------------------------------------------------------------------
# Cost breakdown
# ---------------------------------------------------------------------------


class CostLineOut(BaseModel):
    """One line item of a charge.

    Token-billed lines carry ``tokens`` and ``rate_per_1m_usd``. Lines billed
    in other units, such as images or seconds of video, carry ``quantity``,
    ``unit`` and ``rate_usd`` instead, and leave ``tokens`` and
    ``rate_per_1m_usd`` as ``None``.

    Breaking change: ``tokens`` and ``rate_per_1m_usd`` are now optional and
    may be ``None``. Check for ``None`` before using them, or read
    ``quantity`` and ``rate_usd``, which are set on every line.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    tokens: Optional[int] = None
    """Token count for token-billed lines; ``None`` for other units."""

    rate_per_1m_usd: Optional[str] = None
    """Rate per 1M tokens as a decimal string; ``None`` for other units."""

    quantity: Optional[Union[int, float, str]] = None
    """Billed quantity, expressed in ``unit``."""

    unit: Optional[str] = None
    """Unit the quantity is measured in, for example ``per_image``."""

    rate_usd: Optional[str] = None
    """Rate per unit as a decimal string."""

    charged: Optional[bool] = None
    """``False`` when the line is shown for reference but not billed."""

    modifiers: Optional[Any] = None
    """Rate-card details that applied to this line, such as a resolution tier."""


class CostBreakdownOut(BaseModel):
    """Itemised cost of a request."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    lines: List[CostLineOut] = Field(default_factory=list)
    """Line items that make up the charge."""

    rounding_usd: Optional[str] = None
    """Rounding adjustment applied to the total, as a decimal string."""


# ---------------------------------------------------------------------------
# Usage filter
# ---------------------------------------------------------------------------


class UsageFilter(BaseModel):
    """Filter for usage events, counts, summaries and CSV exports.

    Every field is optional; omitted fields do not narrow the result. Pass
    ``is_retry_attempt=[True, False]`` to include retry attempts alongside
    the served attempt.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    provider: Optional[Union[str, List[str]]] = None
    """Provider slug or slugs that served the request."""

    fault_owner: Optional[Union[str, List[str]]] = None
    """Who a failed request is attributed to."""

    is_byok: Optional[Union[bool, List[bool]]] = None
    """Restrict to requests served on your own provider key."""

    stream: Optional[Union[bool, List[bool]]] = None
    """Restrict to streaming or non-streaming requests."""

    traffic_type: Optional[Union[str, List[str]]] = None
    """Traffic class or classes to include."""

    is_retry_attempt: Optional[Union[bool, List[bool]]] = None
    """Retry attempts to include; omitted returns the served attempt only."""

    def to_body(self) -> dict:
        """Serialise the filter, dropping unset fields."""
        return self.model_dump(exclude_none=True)
