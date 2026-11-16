"""Pydantic models for the API key introspection endpoint.

Covers ``GET /v1/keys/{key_id}``. The response never carries the key secret
or its hash; only metadata such as the masked key, scopes and model access.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict

__all__ = ["ApiKeyDetails"]


# ---------------------------------------------------------------------------
# Keys
# ---------------------------------------------------------------------------


class ApiKeyDetails(BaseModel):
    """Introspection view of a single API key.

    Returned by ``GET /v1/keys/{key_id}``. Unknown fields are preserved so
    newer server versions do not break parsing.

    Attributes:
        id: The key id.
        org_id: The organization that owns the key.
        label: Human-readable label, if one was set.
        masked_key: A masked form of the key (never the full secret).
        scopes: Scopes granted to the key.
        allowed_models: Model ids the key may call, if restricted.
        blocked_models: Model ids the key may not call.
        model_limits: Per-model limits configured on the key.
        effective_limits: The limits that apply after combining every tier
            (the smallest limit at each tier wins).
    """

    model_config = ConfigDict(extra="allow")

    id: str
    org_id: Optional[str] = None
    label: Optional[str] = None
    masked_key: Optional[str] = None
    scopes: List[str] = []
    allowed_models: Optional[List[str]] = None
    blocked_models: Optional[List[str]] = None
    model_limits: Optional[Any] = None
    effective_limits: Optional[Dict[str, Any]] = None
