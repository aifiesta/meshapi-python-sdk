"""Domain types for MeshAPI SDK — all Pydantic v2 models."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------

ChatRole = Literal["system", "user", "assistant", "tool"]


class ImageDetail(BaseModel):
    model_config = ConfigDict(extra="ignore")
    url: str
    detail: Optional[Literal["auto", "low", "high"]] = None


class ContentPartText(BaseModel):
    model_config = ConfigDict(extra="ignore")
    type: Literal["text"]
    text: str


class ContentPartImage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    type: Literal["image_url"]
    image_url: ImageDetail


ContentPart = Union[ContentPartText, ContentPartImage]


class ToolCallFunction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    arguments: str  # JSON-encoded string


class ToolCall(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    type: Literal["function"]
    function: ToolCallFunction


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    role: ChatRole
    content: Optional[Union[str, List[ContentPart]]] = None
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None


class ToolFunction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class Tool(BaseModel):
    model_config = ConfigDict(extra="ignore")
    type: Literal["function"]
    function: ToolFunction


class ToolChoiceFunction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str


class ToolChoiceObject(BaseModel):
    model_config = ConfigDict(extra="ignore")
    type: Literal["function"]
    function: ToolChoiceFunction


ToolChoice = Union[Literal["auto", "none", "required"], ToolChoiceObject]


# ---------------------------------------------------------------------------
# Chat Completions
# ---------------------------------------------------------------------------


class ChatCompletionParams(BaseModel):
    """Request body for POST /v1/chat/completions."""

    model_config = ConfigDict(extra="ignore")

    messages: List[ChatMessage]
    model: Optional[str] = None
    stream: Optional[bool] = None

    # MeshAPI extensions
    template: Optional[str] = None
    variables: Optional[Dict[str, str]] = None
    session_id: Optional[str] = None

    # Inference params
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stop: Optional[Union[str, List[str]]] = None
    seed: Optional[int] = None
    tools: Optional[List[Tool]] = None
    tool_choice: Optional[ToolChoice] = None

    # OpenRouter-specific
    transforms: Optional[List[str]] = None
    models: Optional[List[str]] = None

    user: Optional[str] = None


class UsageInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    prompt_tokens_details: Optional[Dict[str, Any]] = None


class ChatCompletionMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None


class ChatCompletionChoice(BaseModel):
    model_config = ConfigDict(extra="ignore")
    index: int
    message: Optional[ChatCompletionMessage] = None
    finish_reason: Optional[str] = None
    logprobs: Optional[Any] = None


class ChatCompletionResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    object: str
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Optional[UsageInfo] = None
    system_fingerprint: Optional[str] = None


class ChatCompletionChunkDelta(BaseModel):
    model_config = ConfigDict(extra="ignore")
    role: Optional[str] = None
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None


class ChatCompletionChunkChoice(BaseModel):
    model_config = ConfigDict(extra="ignore")
    index: int
    delta: Optional[ChatCompletionChunkDelta] = None
    finish_reason: Optional[str] = None


class ChatCompletionChunk(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    object: str
    created: int
    model: str
    choices: List[ChatCompletionChunkChoice]
    usage: Optional[UsageInfo] = None
    cost: Optional[str] = None


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class ModelPricing(BaseModel):
    model_config = ConfigDict(extra="ignore")
    prompt_usd_per_1k: Optional[str] = None
    completion_usd_per_1k: Optional[str] = None
    image_usd_per_image: Optional[str] = None
    discount_pct: Optional[str] = None
    prompt_usd_per_1k_discounted: Optional[str] = None
    completion_usd_per_1k_discounted: Optional[str] = None


class ModelInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    context_length: Optional[int] = None
    is_free: bool
    pricing: Optional[ModelPricing] = None
    description: Optional[str] = None


class ListModelsParams(BaseModel):
    model_config = ConfigDict(extra="ignore")
    free: Optional[bool] = None


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------


class TemplateMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    role: str
    content: str


class CreateTemplateParams(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    description: Optional[str] = None
    system: Optional[str] = None
    messages: Optional[List[Dict[str, Any]]] = None
    model: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    variables: Optional[List[str]] = None


class UpdateTemplateParams(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = None
    description: Optional[str] = None
    system: Optional[str] = None
    messages: Optional[List[Dict[str, Any]]] = None
    model: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    variables: Optional[List[str]] = None


class TemplateSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    owner: str
    description: Optional[str] = None
    system: Optional[str] = None
    messages: Optional[List[Dict[str, Any]]] = None
    model: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    variables: Optional[List[str]] = None
    created_at: str
    updated_at: str


# ---------------------------------------------------------------------------
# Error wire format
# ---------------------------------------------------------------------------


class ApiErrorBody(BaseModel):
    model_config = ConfigDict(extra="ignore")
    code: str
    message: str
    details: Optional[List[Any]] = None
    provider_error: Optional[Dict[str, Any]] = None
    retry_after_seconds: Optional[int] = None


class ApiErrorEnvelope(BaseModel):
    model_config = ConfigDict(extra="ignore")
    error: ApiErrorBody
    request_id: str
