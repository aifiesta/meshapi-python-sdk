"""Usage and cost models added in API spec v1.0.368.

These models describe the itemised cost breakdown attached to usage rows and
the filter body accepted by the usage events, count, summary and CSV export
endpoints.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict

__all__ = ["CostLineOut", "CostBreakdownOut", "UsageFilter"]


# ---------------------------------------------------------------------------
# Cost breakdown
# ---------------------------------------------------------------------------


class CostLineOut(BaseModel):
    """One line item of a request's charge.

    Token-billed lines carry ``tokens`` and ``rate_per_1m_usd``. Lines billed in
    other units (seconds of video, images, a platform fee) carry ``quantity``,
    ``unit`` and ``rate_usd`` instead, so ``tokens`` and ``rate_per_1m_usd`` may
    be ``None``.

    Attributes:
        tokens: Token count for token-billed lines, else ``None``.
        rate_per_1m_usd: Decimal string rate per 1M tokens, else ``None``.
        quantity: Billed quantity in ``unit`` (for example ``5`` seconds).
        unit: Billing unit of ``quantity`` (for example ``per_second``).
        rate_usd: Decimal string rate per ``unit``.
        charged: ``False`` when the line is shown for transparency but not
            billed (for example model cost on a BYOK request).
        modifiers: Rate-card modifiers that applied (for example
            ``long_context``, ``flex``, ``with_audio``).
    """

    model_config = ConfigDict(extra="allow")

    tokens: Optional[int] = None
    rate_per_1m_usd: Optional[str] = None
    quantity: Optional[Union[int, float, str]] = None
    unit: Optional[str] = None
    rate_usd: Optional[str] = None
    charged: Optional[bool] = None
    modifiers: Optional[List[str]] = None


class CostBreakdownOut(BaseModel):
    """Itemised breakdown of a request's charge.

    Attributes:
        lines: The individual line items.
        rounding_usd: Decimal string adjustment from rounding the line totals
            to the charged amount, if any.
    """

    model_config = ConfigDict(extra="allow")

    lines: Optional[List[CostLineOut]] = None
    rounding_usd: Optional[str] = None


# ---------------------------------------------------------------------------
# Usage filter
# ---------------------------------------------------------------------------


class UsageFilter(BaseModel):
    """Filter body for usage events, counts, summaries and CSV export.

    Only fields that are set are sent.

    Attributes:
        provider: Provider slug(s) that served the request.
        fault_owner: Who a failure is attributed to.
        is_byok: Restrict to requests served on your own provider key.
        stream: Restrict to streaming or non-streaming requests.
        traffic_type: Traffic class(es) to include.
        is_retry_attempt: Omit for the served attempt only; pass
            ``[True, False]`` to include retry attempts.
    """

    model_config = ConfigDict(extra="allow")

    provider: Optional[Union[str, List[str]]] = None
    fault_owner: Optional[Union[str, List[str]]] = None
    is_byok: Optional[bool] = None
    stream: Optional[bool] = None
    traffic_type: Optional[Union[str, List[str]]] = None
    is_retry_attempt: Optional[List[bool]] = None

    def to_payload(self) -> Dict[str, Any]:
        """Return the JSON body, omitting unset fields."""
        return self.model_dump(exclude_none=True)
