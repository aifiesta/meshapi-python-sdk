"""Unit tests for ``SearchRequest.mode`` added in spec v1.0.429.

``mode`` selects the retrieval strategy for ``POST /v1/files/search``
(for example ``"vector"``, ``"graph"`` or ``"agentic"``). It is optional:
omitting it keeps the default retrieval behaviour.
"""

from __future__ import annotations

from meshapi._types import SearchRequest


def test_mode_is_declared():
    assert "mode" in SearchRequest.model_fields


def test_mode_is_optional_and_defaults_to_none():
    info = SearchRequest.model_fields["mode"]
    assert info.is_required() is False
    assert info.default is None
