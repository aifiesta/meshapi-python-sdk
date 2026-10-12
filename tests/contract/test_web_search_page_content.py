"""Contract tests for web-search page content.

Covers the two halves that can drift independently: what the SDK puts on the
wire, and what it accepts back. The wire half matters because this is an
additive flag — an existing caller who never sets it must send exactly the
bytes it sent before.
"""

import pytest
from pydantic import ValidationError

from meshapi._types import WebSearchParams, WebSearchResponse, WebSearchResultItem


# ---------------------------------------------------------------------------
# Request — what goes on the wire
# ---------------------------------------------------------------------------


def test_unset_page_content_is_absent_from_the_payload():
    """The flag must not appear at all when the caller did not set it."""
    dumped = WebSearchParams(query="mars rovers").model_dump(exclude_none=True)
    assert "include_page_content" not in dumped


def test_requesting_page_content_sends_the_flag():
    dumped = WebSearchParams(
        query="mars rovers", include_page_content=True
    ).model_dump(exclude_none=True)
    assert dumped["include_page_content"] is True


def test_declining_page_content_explicitly_is_still_sent():
    """False is a choice the caller made, so it is not silently dropped."""
    dumped = WebSearchParams(
        query="mars rovers", include_page_content=False
    ).model_dump(exclude_none=True)
    assert dumped["include_page_content"] is False


@pytest.mark.parametrize("engine", ["native", "tavily", "tinyfish"])
def test_every_documented_engine_can_be_pinned(engine):
    """tinyfish was a valid API value the Literal used to reject."""
    assert WebSearchParams(query="q", provider=engine).provider == engine


def test_an_unknown_engine_is_still_rejected():
    with pytest.raises(ValidationError):
        WebSearchParams(query="q", provider="not-an-engine")


# ---------------------------------------------------------------------------
# Response — what comes back
# ---------------------------------------------------------------------------


def test_page_content_and_truncation_flag_are_parsed():
    resp = WebSearchResponse.model_validate(
        {
            "query": "mars rovers",
            "provider": "tinyfish",
            "request_id": "req_01J",
            "results": [
                {
                    "title": "Perseverance",
                    "url": "https://example.com/p",
                    "content": "a short snippet",
                    "score": 0.9,
                    "page_content": "the full extracted page text",
                    "page_content_truncated": True,
                }
            ],
        }
    )
    item = resp.results[0]
    assert item.page_content == "the full extracted page text"
    assert item.page_content_truncated is True
    # The snippet is a separate field and page text never replaces it.
    assert item.content == "a short snippet"


def test_null_page_content_stays_none_rather_than_empty_string():
    """None (no text) and "" (empty text) are different answers; keep them apart."""
    item = WebSearchResultItem.model_validate(
        {
            "title": "t",
            "url": "https://example.com",
            "content": "snippet",
            "page_content": None,
            "page_content_truncated": False,
        }
    )
    assert item.page_content is None
    assert item.page_content != ""


def test_a_response_without_the_new_keys_still_parses():
    """An older gateway omits them entirely; that must not be a parse error."""
    item = WebSearchResultItem.model_validate(
        {"title": "t", "url": "https://example.com", "content": "snippet"}
    )
    assert item.page_content is None
    assert item.page_content_truncated is False
