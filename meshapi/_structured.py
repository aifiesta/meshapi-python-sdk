"""Structured-output helpers: schema detection, wire-format build, parse.

Pure and HTTP-free so both the sync and async ``parse()`` methods share one
implementation. The gateway forwards ``response_format`` to each provider and
translates it to that provider's native structured-output mechanism, so the
SDK's only jobs are (1) build the ``json_schema`` request field and (2) parse
and validate the reply.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Literal

from pydantic import BaseModel, TypeAdapter

from ._types import ChatCompletionResponse

SchemaKind = Literal["model", "adapter", "raw"]


def detect_kind(response_format: Any) -> SchemaKind:
    """Route by how the caller declared the schema.

    - ``dict``                        -> "raw"  (escape hatch, unvalidated)
    - ``BaseModel`` subclass          -> "model"
    - anything else usable by pydantic (TypedDict, dataclass, ...) -> "adapter"
    """
    if isinstance(response_format, dict):
        return "raw"
    if isinstance(response_format, type) and issubclass(response_format, BaseModel):
        return "model"
    return "adapter"


def _schema_name(response_format: Any) -> str:
    return getattr(response_format, "__name__", "response")


def build_response_format(response_format: Any) -> Dict[str, Any]:
    """Build the OpenAI-style ``response_format`` request field."""
    kind = detect_kind(response_format)
    if kind == "raw":
        # Already a full wrapper? pass through. Otherwise treat as a bare schema.
        if response_format.get("type") == "json_schema":
            return response_format
        return {
            "type": "json_schema",
            "json_schema": {"name": "response", "schema": response_format},
        }
    if kind == "model":
        schema = response_format.model_json_schema()
    else:  # adapter
        schema = TypeAdapter(response_format).json_schema()
    return {
        "type": "json_schema",
        "json_schema": {"name": _schema_name(response_format), "schema": schema},
    }


def parse_content(response_format: Any, content: str) -> Any:
    """Parse model output back into the caller's requested type.

    Raises ``pydantic.ValidationError`` (model/adapter paths) or
    ``json.JSONDecodeError`` (raw path) on a mismatch — both drive the retry loop.
    """
    kind = detect_kind(response_format)
    if kind == "model":
        return response_format.model_validate_json(content)
    if kind == "adapter":
        return TypeAdapter(response_format).validate_json(content)
    return json.loads(content)


def correction_prompt(exc: Exception) -> str:
    return (
        "Your previous response failed schema validation: "
        f"{exc}. Return ONLY a JSON object that matches the requested schema, "
        "with no prose, markdown, or code fences."
    )


def extract_content(resp: ChatCompletionResponse) -> str:
    """Pull the assistant text out of the first choice. Empty string if absent
    (so downstream validation fails and can be retried, rather than crashing)."""
    if not resp.choices:
        return ""
    msg = resp.choices[0].message
    content = msg.content if msg else None
    return content if isinstance(content, str) else ""
