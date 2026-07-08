"""Live tests: Structured output (response_format with JSON schema)."""

from __future__ import annotations

import json

import pytest
from pydantic import BaseModel
from meshapi import MeshAPI, ChatCompletionParams, ChatMessage

MODELS = [
    "openai/gpt-4o-mini",
    "google/gemini-3-flash-preview",
]

_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "country_info",
        "schema": {
            "type": "object",
            "properties": {
                "capital": {"type": "string"},
                "country": {"type": "string"},
            },
            "required": ["capital", "country"],
            "additionalProperties": False,
        },
    },
}


@pytest.mark.parametrize("so_model", MODELS)
def test_structured_output_fields(client: MeshAPI, so_model: str) -> None:
    resp = client.chat.completions.create(
        ChatCompletionParams(
            model=so_model,
            messages=[ChatMessage(role="user", content="What is the capital of France? Use the provided schema.")],
            response_format=_SCHEMA,
            max_tokens=1000,
            temperature=0,
        )
    )
    assert resp.choices, "expected choices"
    content = resp.choices[0].message.content
    assert content, "expected non-empty content"

    data = json.loads(content)
    assert "capital" in data, f"missing 'capital' field: {data}"
    assert "country" in data, f"missing 'country' field: {data}"
    assert isinstance(data["capital"], str), f"'capital' must be a string: {data}"
    assert isinstance(data["country"], str), f"'country' must be a string: {data}"
    assert "paris" in data["capital"].lower(), f"expected Paris as capital, got: {data}"


@pytest.mark.parametrize("so_model", MODELS)
def test_structured_output_finish_reason(client: MeshAPI, so_model: str) -> None:
    resp = client.chat.completions.create(
        ChatCompletionParams(
            model=so_model,
            messages=[ChatMessage(role="user", content="Name any planet in our solar system. Use the provided schema.")],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "planet_info",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "position_from_sun": {"type": "integer"},
                        },
                        "required": ["name", "position_from_sun"],
                        "additionalProperties": False,
                    },
                },
            },
            max_tokens=1000,
            temperature=0,
        )
    )
    assert resp.choices[0].finish_reason == "stop", (
        f"expected finish_reason 'stop', got {resp.choices[0].finish_reason!r}"
    )
    data = json.loads(resp.choices[0].message.content)
    assert "name" in data
    assert "position_from_sun" in data
    assert isinstance(data["position_from_sun"], int), f"expected integer position: {data}"


# ---------------------------------------------------------------------------
# .parse() ergonomic API (MESH-363)
# ---------------------------------------------------------------------------

class CountryLT(BaseModel):
    country: str
    capital: str


@pytest.mark.parametrize("so_model", MODELS)
def test_parse_pydantic_live(client: MeshAPI, so_model: str) -> None:
    out = client.chat.completions.parse(
        ChatCompletionParams(
            model=so_model,
            messages=[ChatMessage(role="user", content="What is the capital of France?")],
            temperature=0,
            max_tokens=1000,
        ),
        response_format=CountryLT,
    )
    assert isinstance(out, CountryLT)
    assert "paris" in out.capital.lower()


@pytest.mark.parametrize("so_model", MODELS)
def test_parse_raw_dict_live(client: MeshAPI, so_model: str) -> None:
    out = client.chat.completions.parse(
        ChatCompletionParams(
            model=so_model,
            messages=[ChatMessage(role="user", content="Name any planet. Use the schema.")],
            temperature=0,
            max_tokens=1000,
        ),
        response_format={
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
            "additionalProperties": False,
        },
    )
    assert isinstance(out, dict) and "name" in out
