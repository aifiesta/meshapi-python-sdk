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


class InputAudio(BaseModel):
    model_config = ConfigDict(extra="ignore")
    data: str
    format: Literal["wav", "mp3", "aiff", "aac", "ogg", "flac", "m4a", "pcm16", "pcm24"]


class ContentPartAudio(BaseModel):
    model_config = ConfigDict(extra="ignore")
    type: Literal["input_audio"]
    input_audio: InputAudio


ContentPart = Union[ContentPartText, ContentPartImage, ContentPartAudio]


class ToolCallFunction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    arguments: str  # JSON-encoded string


class ToolCall(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    type: Literal["function"]
    function: ToolCallFunction


class ToolCallFunctionChunk(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = None
    arguments: Optional[str] = None


class ToolCallChunk(BaseModel):
    model_config = ConfigDict(extra="ignore")
    index: int
    id: Optional[str] = None
    type: Optional[Literal["function"]] = None
    function: Optional[ToolCallFunctionChunk] = None


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


class AudioOutputOptions(BaseModel):
    model_config = ConfigDict(extra="ignore")
    voice: str = "alloy"
    format: Literal["wav", "mp3", "flac", "opus", "pcm16"] = "wav"


class ImageOptions(BaseModel):
    model_config = ConfigDict(extra="ignore")
    n: int = Field(default=1, ge=1, le=10)
    size: str = "1024x1024"
    quality: str = "high"
    response_format: Literal["url", "b64_json"] = "url"


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
    response_format: Optional[Dict[str, Any]] = None

    user: Optional[str] = None
    modality: Optional[Literal["text", "image"]] = None
    image: Optional[ImageOptions] = None
    async_mode: Optional[bool] = None
    modalities: Optional[List[Literal["text", "audio"]]] = None
    audio: Optional[AudioOutputOptions] = None

    # MeshAPI extension — overrides the server's 300 s upstream-provider timeout.
    # Set this when your request may take longer than 5 minutes (e.g. long reasoning
    # chains). The SDK-level timeout (MeshAPI(timeout=…)) is a separate HTTP-client
    # timeout and does not affect this value.
    timeout: Optional[float] = Field(default=None, gt=0)


class UsageInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    prompt_tokens_details: Optional[Dict[str, Any]] = None
    completion_tokens_details: Optional[Dict[str, Any]] = None
    classifier_prompt_tokens: Optional[int] = None
    classifier_completion_tokens: Optional[int] = None
    classifier_tokens: Optional[int] = None


class ChatCompletionMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    role: str
    content: Optional[Union[str, List[ContentPart]]] = None
    tool_calls: Optional[List[ToolCall]] = None
    audio: Optional[Dict[str, Any]] = None


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
    tool_calls: Optional[List[ToolCallChunk]] = None
    audio: Optional[Dict[str, Any]] = None


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
    supports_thinking: Optional[bool] = None
    supports_completions_api: Optional[bool] = None
    supports_responses_api: Optional[bool] = None
    model_type: Optional[str] = None
    input_modalities: Optional[List[str]] = None
    output_modalities: Optional[List[str]] = None


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
    owner: Optional[str] = None
    is_global: bool
    description: Optional[str] = None
    system: Optional[str] = None
    messages: Optional[List[Dict[str, Any]]] = None
    model: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    variables: Optional[List[str]] = None
    created_at: str
    updated_at: str


# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------


class ProviderPreferences(BaseModel):
    model_config = ConfigDict(extra="ignore")
    order: Optional[List[str]] = None
    allow_fallbacks: Optional[bool] = None
    require_parameters: Optional[bool] = None
    data_collection: Optional[Literal["allow", "deny"]] = None


class EmbeddingsParams(BaseModel):
    model_config = ConfigDict(extra="ignore")
    model: Optional[str] = None
    input: Union[str, List[str], List[int], List[List[int]]]
    dimensions: Optional[int] = Field(default=None, ge=1)
    encoding_format: Optional[Literal["float", "base64"]] = None
    input_type: Optional[str] = None
    provider: Optional[Union[str, ProviderPreferences]] = None
    user: Optional[str] = Field(default=None, max_length=256)


class EmbeddingItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    object: str
    index: int
    embedding: Union[List[float], str]


class EmbeddingsUsage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    prompt_tokens: int
    total_tokens: int


class EmbeddingsResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    object: str
    data: List[EmbeddingItem]
    model: str
    usage: Optional[EmbeddingsUsage] = None


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


class BuiltinTool(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: Literal[
        "image_generation",
        "web_search_preview",
        "web_search_preview_2025_03_11",
        "file_search",
        "computer_use_preview",
        "code_interpreter",
    ]


class ResponsesFunctionTool(BaseModel):
    model_config = ConfigDict(extra="ignore")
    type: Literal["function"] = "function"
    name: str
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    strict: Optional[bool] = None


class ResponsesParams(BaseModel):
    model_config = ConfigDict(extra="ignore")
    model: Optional[str] = None
    input: Union[str, List[Any]]
    template: Optional[str] = None
    variables: Optional[Dict[str, str]] = None
    session_id: Optional[str] = None
    stream: bool = False
    max_output_tokens: Optional[int] = Field(default=None, ge=1)
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    seed: Optional[int] = None
    reasoning: Optional[Dict[str, Any]] = None
    tools: Optional[List[Union[ResponsesFunctionTool, BuiltinTool]]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None
    response_format: Optional[Dict[str, Any]] = None
    user: Optional[str] = Field(default=None, max_length=256)
    timeout: Optional[float] = Field(default=None, gt=0)


class ResponsesUsage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    prompt_tokens_details: Optional[Dict[str, Any]] = None
    completion_tokens_details: Optional[Dict[str, Any]] = None
    classifier_tokens: Optional[int] = None


class ResponsesResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: Optional[str] = None
    object: Optional[str] = None
    model: Optional[str] = None
    output: Optional[List[Any]] = None
    usage: Optional[ResponsesUsage] = None
    status: Optional[str] = None


class ResponsesStreamEvent(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: Optional[str] = None
    response: Optional[Dict[str, Any]] = None
    usage: Optional[ResponsesUsage] = None


# ---------------------------------------------------------------------------
# Compare
# ---------------------------------------------------------------------------


class ModelOverride(BaseModel):
    model_config = ConfigDict(extra="ignore")
    model: str
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    system_prompt: Optional[str] = None


class CompareParams(BaseModel):
    model_config = ConfigDict(extra="ignore")
    models: List[str]
    messages: List[ChatMessage]
    model_overrides: Optional[List[ModelOverride]] = None
    comparison_model: Optional[str] = None
    comparison_instructions: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    stream: bool = False
    template: Optional[str] = None
    variables: Optional[Dict[str, str]] = None
    skip_comparison: bool = False


class TokenUsage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


class ModelCompareResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    model: str
    response_body: Optional[Dict[str, Any]] = None
    content: Optional[str] = None
    latency_ms: int
    error: Optional[str] = None
    error_code: Optional[str] = None
    usage: Optional[TokenUsage] = None
    request_id: str


class CompareResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    comparison_id: str
    object: str
    created: int
    models: List[str]
    results: List[ModelCompareResult]
    comparison: Optional[str] = None
    comparison_model: Optional[str] = None
    comparison_usage: Optional[TokenUsage] = None
    comparison_fallback_used: bool = False
    total_latency_ms: int
    partial: bool = False
    skip_comparison: bool = False


class CompareStreamEvent(BaseModel):
    model_config = ConfigDict(extra="allow")
    event: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

    # Common fields flattened from various compare event types
    delta: Optional[str] = None
    model: Optional[str] = None
    comparison_id: Optional[str] = None
    comparison_model: Optional[str] = None
    models: Optional[List[str]] = None
    latency_ms: Optional[int] = None
    total_latency_ms: Optional[int] = None
    finish_reason: Optional[str] = None
    error: Optional[Any] = None
    error_code: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None
    skip_comparison: Optional[bool] = None
    partial: Optional[bool] = None
    comparison_fallback_used: Optional[bool] = None


# ---------------------------------------------------------------------------
# Files / Batches
# ---------------------------------------------------------------------------


class BatchRequestItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    custom_id: str
    method: str = "POST"
    url: str = "/v1/chat/completions"
    body: Dict[str, Any]


class CreateBatchParams(BaseModel):
    model_config = ConfigDict(extra="ignore")
    requests: List[BatchRequestItem]
    completion_window: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BatchObject(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    object: Optional[str] = None
    endpoint: Optional[str] = None
    input_file_id: Optional[str] = None
    output_file_id: Optional[str] = None
    status: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    created_at: Optional[int] = None
    completed_at: Optional[int] = None
    usage_synced: Optional[bool] = None


class BatchListResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    object: str
    data: List[BatchObject]
    has_more: bool
    first_id: Optional[str] = None
    last_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Images
# ---------------------------------------------------------------------------


class ImageGenerationParams(BaseModel):
    """Request body for POST /v1/images/generations."""

    model_config = ConfigDict(extra="ignore")

    prompt: str
    model: Optional[str] = None
    n: Optional[int] = None
    size: Optional[str] = None
    quality: Optional[str] = None
    response_format: Optional[Literal["url", "b64_json"]] = None
    output_format: Optional[Literal["png", "jpeg", "webp"]] = None
    stream: Optional[bool] = None


class ImageItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    url: Optional[str] = None
    b64_json: Optional[str] = None
    revised_prompt: Optional[str] = None


class ImageUsage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    input_tokens_details: Optional[Dict[str, Any]] = None
    output_tokens_details: Optional[Dict[str, Any]] = None


class ImageGenerationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    created: int
    data: List[ImageItem]
    background: Optional[str] = None
    output_format: Optional[str] = None
    quality: Optional[str] = None
    size: Optional[str] = None
    usage: Optional[ImageUsage] = None


class ImageGenerationChunk(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: Optional[str] = None
    object: Optional[str] = "image.chunk"
    created: int
    data: List[ImageItem] = []
    status: Optional[str] = None
    model: Optional[str] = None


# ---------------------------------------------------------------------------

# Error wire format
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# RAG (Retrieval-Augmented Generation)
# ---------------------------------------------------------------------------


class InitUploadRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    file_name: str
    mime_type: str
    embed: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class InitUploadResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    file_id: str
    signed_url: str
    expires_at: str


class RagFileStatus(BaseModel):
    model_config = ConfigDict(extra="ignore")
    file_id: str
    upload_status: str
    file_name: str
    file_type: str
    mime_type: str
    size_bytes: Optional[int] = None
    asset_url: Optional[str] = None
    signed_url: Optional[str] = None
    signed_url_expires_at: Optional[str] = None
    embedding_status: str
    created_at: str
    updated_at: str
    total_tokens: Optional[int] = None
    total_cost_usd: Optional[float] = None
    last_error_code: Optional[str] = None


class RagFileListResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    files: List[RagFileStatus]
    total: int
    limit: int
    offset: int


class BulkEmbedRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    file_ids: List[str] = Field(..., min_length=1, max_length=100)
    wait: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class BulkEmbedResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    file_id: str
    embedding_status: str
    chunk_count: Optional[int] = None
    error: Optional[str] = None


class BulkEmbedResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    results: List[BulkEmbedResult]


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    query: str
    top_k: Optional[int] = None
    file_ids: Optional[List[str]] = None
    filter: Optional[Dict[str, Any]] = None
    date_from: Optional[int] = None
    date_to: Optional[int] = None


class SearchResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    score: float
    text: str
    parent_text: str
    file_id: Optional[str] = None
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    mime_type: Optional[str] = None
    chunk_index: Optional[int] = None
    created_at: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    results: List[SearchResult]


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
