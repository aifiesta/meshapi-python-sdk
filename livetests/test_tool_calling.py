"""Live tests: function/tool calling round-trip — POST /v1/chat/completions.

Tool calling is the single most-used advanced feature at hackathons. This
exercises the full round-trip:

    1. send a request with tools + a forced tool_choice,
    2. assert the assistant returns a well-formed tool_calls array,
    3. feed a tool result back as a `role="tool"` message,
    4. assert the model produces a final natural-language answer.

The forced-tool test is deterministic (it does not depend on the model
*choosing* to call the tool); a second test covers the realistic `auto` path
without flaking.
"""

from __future__ import annotations

import json

import pytest
from meshapi import (
    ChatCompletionParams,
    ChatMessage,
    MeshAPI,
    MeshAPIError,
    Tool,
    ToolChoiceFunction,
    ToolChoiceObject,
    ToolFunction,
)

WEATHER_TOOL = Tool(
    type="function",
    function=ToolFunction(
        name="get_weather",
        description="Get the current weather for a city.",
        parameters={
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    ),
)


def _skip_if_unsupported(exc: MeshAPIError) -> None:
    if exc.status in (400, 501) and "capab" in (exc.error_code or "").lower():
        pytest.skip(f"model does not support tool calling: {exc.error_code}")
    if exc.status in (400, 501) and exc.error_code in ("not_implemented", "model_capability_not_supported"):
        pytest.skip(f"model does not support tool calling: {exc.error_code}")


def test_tool_call_round_trip(client: MeshAPI, model: str) -> None:
    messages = [ChatMessage(role="user", content="What is the weather in Paris?")]

    try:
        resp = client.chat.completions.create(
            ChatCompletionParams(
                model=model,
                messages=messages,
                tools=[WEATHER_TOOL],
                # Force the call so the round-trip is deterministic.
                tool_choice=ToolChoiceObject(
                    type="function", function=ToolChoiceFunction(name="get_weather")
                ),
                max_tokens=100,
            )
        )
    except MeshAPIError as exc:
        _skip_if_unsupported(exc)
        raise

    msg = resp.choices[0].message
    assert msg.tool_calls, "forced tool_choice must produce a tool_calls array"
    call = msg.tool_calls[0]
    assert call.id, "tool call must have an id"
    assert call.type == "function"
    assert call.function.name == "get_weather"
    args = json.loads(call.function.arguments)  # arguments must be valid JSON
    assert "city" in args, f"expected a 'city' argument, got {args!r}"

    # Feed the tool result back and expect a final natural-language answer.
    messages.append(ChatMessage(role="assistant", content=msg.content, tool_calls=msg.tool_calls))
    messages.append(
        ChatMessage(
            role="tool",
            tool_call_id=call.id,
            content='{"temperature": 22, "unit": "celsius", "description": "Sunny"}',
        )
    )
    final = client.chat.completions.create(
        ChatCompletionParams(model=model, messages=messages, tools=[WEATHER_TOOL], max_tokens=100)
    )
    final_content = final.choices[0].message.content
    assert final_content, "expected a final assistant answer after the tool result"


def test_tool_choice_auto_is_well_formed(client: MeshAPI, model: str) -> None:
    """With tool_choice='auto', any tool_calls the model returns must be valid."""
    try:
        resp = client.chat.completions.create(
            ChatCompletionParams(
                model=model,
                messages=[ChatMessage(role="user", content="What is the weather in Tokyo?")],
                tools=[WEATHER_TOOL],
                tool_choice="auto",
                max_tokens=100,
            )
        )
    except MeshAPIError as exc:
        _skip_if_unsupported(exc)
        raise

    msg = resp.choices[0].message
    if msg.tool_calls:
        for call in msg.tool_calls:
            assert call.id and call.function.name
            json.loads(call.function.arguments)  # must be valid JSON
    else:
        assert msg.content, "if no tool was called, the model must reply with content"
