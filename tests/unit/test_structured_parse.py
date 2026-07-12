"""Unit tests for structured-output helpers and chat.completions.parse()."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel, ValidationError
from typing_extensions import TypedDict  # 3.9-safe TypedDict for tests

from meshapi import _structured as S
from meshapi import StructuredOutputError
from meshapi._types import (
    ChatCompletionChoice,
    ChatCompletionMessage,
    ChatCompletionParams,
    ChatCompletionResponse,
    ChatMessage,
)
from meshapi.resources.chat import AsyncCompletionsResource, CompletionsResource


class Address(BaseModel):
    city: str
    zip: str


class Person(BaseModel):
    name: str
    age: int
    address: Address  # nested — AC#3


class PersonTD(TypedDict):
    name: str
    age: int


def _resp(content) -> ChatCompletionResponse:
    return ChatCompletionResponse(
        id="c1", object="chat.completion", created=0, model="m",
        choices=[ChatCompletionChoice(
            index=0,
            message=ChatCompletionMessage(role="assistant", content=content),
            finish_reason="stop",
        )],
    )


def _payload(content: str) -> dict:
    return {
        "id": "c1", "object": "chat.completion", "created": 0, "model": "m",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content},
                     "finish_reason": "stop"}],
    }


def _params():
    return ChatCompletionParams(model="m", messages=[ChatMessage(role="user", content="hi")])


# ---------------------------------------------------------------------------
# detect_kind
# ---------------------------------------------------------------------------

def test_detect_kind_model():
    assert S.detect_kind(Person) == "model"

def test_detect_kind_adapter_for_typeddict():
    assert S.detect_kind(PersonTD) == "adapter"

def test_detect_kind_raw_for_dict():
    assert S.detect_kind({"type": "object"}) == "raw"


# ---------------------------------------------------------------------------
# build_response_format
# ---------------------------------------------------------------------------

def test_build_response_format_model_wraps_schema():
    rf = S.build_response_format(Person)
    assert rf["type"] == "json_schema"
    assert rf["json_schema"]["name"] == "Person"
    assert rf["json_schema"]["schema"]["properties"]["name"]["type"] == "string"

def test_build_response_format_raw_bare_schema_gets_wrapped():
    rf = S.build_response_format({"type": "object", "properties": {}})
    assert rf["type"] == "json_schema"
    assert rf["json_schema"]["schema"]["type"] == "object"

def test_build_response_format_raw_full_wrapper_passes_through():
    wrapper = {"type": "json_schema", "json_schema": {"name": "x", "schema": {}}}
    assert S.build_response_format(wrapper) == wrapper


def test_build_response_format_unschemable_adapter_hints_typing_extensions():
    """A type pydantic can't schema-build (e.g. stdlib TypedDict on <3.12, or an
    arbitrary class) raises a clear TypeError pointing at typing_extensions."""
    class NotSchemable:  # arbitrary class -> adapter path, no pydantic schema
        pass

    with pytest.raises(TypeError) as ei:
        S.build_response_format(NotSchemable)
    assert "typing_extensions" in str(ei.value)


# ---------------------------------------------------------------------------
# parse_content
# ---------------------------------------------------------------------------

def test_parse_content_model_returns_instance_nested():
    content = json.dumps({"name": "A", "age": 3, "address": {"city": "NYC", "zip": "10001"}})
    out = S.parse_content(Person, content)
    assert isinstance(out, Person)
    assert isinstance(out.address, Address)  # deep nesting parsed — AC#3
    assert out.address.city == "NYC"

def test_parse_content_typeddict_returns_dict():
    out = S.parse_content(PersonTD, json.dumps({"name": "A", "age": 3}))
    assert out == {"name": "A", "age": 3}

def test_parse_content_raw_returns_dict_unvalidated():
    out = S.parse_content({"type": "object"}, json.dumps({"anything": 1}))
    assert out == {"anything": 1}

def test_parse_content_raw_returns_non_dict_json():
    """Raw path returns whatever JSON the model emitted — list or scalar, not
    only a dict (honest typing: the raw overload returns Any)."""
    assert S.parse_content({"type": "array"}, json.dumps([1, 2, 3])) == [1, 2, 3]
    assert S.parse_content({"type": "integer"}, json.dumps(7)) == 7

def test_parse_content_model_bad_raises_validation_error():
    with pytest.raises(ValidationError):
        S.parse_content(Person, json.dumps({"name": "A"}))  # missing age/address

def test_parse_content_raw_bad_json_raises():
    with pytest.raises(json.JSONDecodeError):
        S.parse_content({"type": "object"}, "not json")


# ---------------------------------------------------------------------------
# extract_content
# ---------------------------------------------------------------------------

def test_extract_content_returns_string():
    assert S.extract_content(_resp("hello")) == "hello"

def test_extract_content_none_returns_empty_string():
    assert S.extract_content(_resp(None)) == ""


# ---------------------------------------------------------------------------
# correction_prompt
# ---------------------------------------------------------------------------

def test_correction_prompt_asks_for_valid_json_not_object():
    """A raw schema may be a non-object (array/scalar); the retry prompt must not
    demand a JSON *object*, only valid JSON."""
    prompt = S.correction_prompt(ValueError("boom"))
    assert "valid JSON" in prompt
    assert "JSON object" not in prompt
    assert "boom" in prompt


# ---------------------------------------------------------------------------
# sync parse()
# ---------------------------------------------------------------------------

def test_parse_pydantic_returns_instance_and_sends_schema():
    http = MagicMock()
    http.post.return_value = _payload(json.dumps(
        {"name": "A", "age": 3, "address": {"city": "NYC", "zip": "10001"}}))
    out = CompletionsResource(http).parse(_params(), Person)
    assert isinstance(out, Person) and out.address.city == "NYC"
    path, body = http.post.call_args.args
    assert path == "/v1/chat/completions"
    assert body["stream"] is False
    assert body["response_format"]["json_schema"]["name"] == "Person"


def test_parse_typeddict_returns_dict():
    http = MagicMock()
    http.post.return_value = _payload(json.dumps({"name": "A", "age": 3}))
    out = CompletionsResource(http).parse(_params(), PersonTD)
    assert out == {"name": "A", "age": 3}


def test_parse_raw_dict_returns_dict():
    http = MagicMock()
    http.post.return_value = _payload(json.dumps({"x": 1}))
    out = CompletionsResource(http).parse(_params(), {"type": "object"})
    assert out == {"x": 1}


def test_parse_default_no_retry_raises_on_bad():
    http = MagicMock()
    http.post.return_value = _payload(json.dumps({"name": "A"}))  # valid JSON, wrong shape
    with pytest.raises(StructuredOutputError) as ei:
        CompletionsResource(http).parse(_params(), Person)
    assert http.post.call_count == 1
    # underlying error preserved; shape-mismatch wording (not the "not JSON" hint)
    assert isinstance(ei.value.__cause__, ValidationError)
    assert "did not match the requested schema" in str(ei.value)


def test_parse_non_json_hints_model_support():
    """Model returns prose (doesn't support structured output) -> the error
    tells the caller to check model support + links the Models page."""
    http = MagicMock()
    http.post.return_value = _payload("Sure! The capital of France is Paris.")
    with pytest.raises(StructuredOutputError) as ei:
        CompletionsResource(http).parse(_params(), Person)
    msg = str(ei.value)
    assert "does not support structured outputs" in msg
    assert "app.meshapi.ai" in msg and "/models" in msg
    assert ei.value.error_code == "structured_output_parse_error"


def test_parse_raw_dict_non_json_hints_model_support():
    http = MagicMock()
    http.post.return_value = _payload("not json at all")
    with pytest.raises(StructuredOutputError) as ei:
        CompletionsResource(http).parse(_params(), {"type": "object"})
    assert "does not support structured outputs" in str(ei.value)
    assert isinstance(ei.value.__cause__, json.JSONDecodeError)


def test_parse_retry_recovers_and_appends_correction():
    http = MagicMock()
    http.post.side_effect = [
        _payload(json.dumps({"name": "A"})),  # bad
        _payload(json.dumps({"name": "A", "age": 3, "address": {"city": "X", "zip": "1"}})),  # good
    ]
    out = CompletionsResource(http).parse(_params(), Person, max_retries=1)
    assert isinstance(out, Person)
    assert http.post.call_count == 2
    _, second_body = http.post.call_args.args
    roles = [m["role"] for m in second_body["messages"]]
    assert roles == ["user", "assistant", "user"]  # original + bad output + correction


def test_parse_retry_exhausted_raises():
    http = MagicMock()
    http.post.side_effect = [_payload(json.dumps({"name": "A"}))] * 3
    with pytest.raises(StructuredOutputError) as ei:
        CompletionsResource(http).parse(_params(), Person, max_retries=1)
    assert http.post.call_count == 2  # initial + 1 retry
    assert isinstance(ei.value.__cause__, ValidationError)


# ---------------------------------------------------------------------------
# async parse()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_async_parse_pydantic_and_retry():
    http = MagicMock()
    http.post = AsyncMock(side_effect=[
        _payload(json.dumps({"name": "A"})),  # bad
        _payload(json.dumps({"name": "A", "age": 3, "address": {"city": "X", "zip": "1"}})),
    ])
    out = await AsyncCompletionsResource(http).parse(_params(), Person, max_retries=1)
    assert isinstance(out, Person)
    assert http.post.await_count == 2
