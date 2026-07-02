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
    data: Optional[str] = None
    uri: Optional[str] = None
    url: Optional[str] = None
    format: Literal["wav", "mp3", "aiff", "aac", "ogg", "flac", "m4a", "pcm16", "pcm24"]


class ContentPartAudio(BaseModel):
    model_config = ConfigDict(extra="ignore")
    type: Literal["input_audio"]
    input_audio: InputAudio


class VideoUrl(BaseModel):
    model_config = ConfigDict(extra="ignore")
    url: str


class ContentPartVideo(BaseModel):
    model_config = ConfigDict(extra="ignore")
    type: Literal["video_url"]
    video_url: VideoUrl
    fps: Optional[str] = None


ContentPart = Union[ContentPartText, ContentPartImage, ContentPartAudio, ContentPartVideo]


class ToolCallFunction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    arguments: str  # JSON-encoded string


class ToolCall(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    type: Literal["function"]
    function: ToolCallFunction
    thought_signature: Optional[str] = None


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
    reasoning_details: Optional[List[Dict[str, Any]]] = None


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

    # Spec fields: cache, transforms, reasoning_effort
    cache: Optional[bool] = None
    transforms: Optional[List[str]] = None
    reasoning_effort: Optional[Literal["high", "medium", "low", "none"]] = None


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
    # Required by spec (nullable)
    prompt_usd_per_1k: Optional[str] = None
    completion_usd_per_1k: Optional[str] = None
    # Optional spec fields (all str|null, values are strings per spec)
    pricing_unit: Optional[str] = None
    prompt_usd_per_1m: Optional[str] = None
    completion_usd_per_1m: Optional[str] = None
    image_output_usd_per_image: Optional[str] = None
    request_usd: Optional[str] = None
    long_context_input_usd_per_1m: Optional[str] = None
    long_context_output_usd_per_1m: Optional[str] = None
    cache_read_input_usd_per_1m: Optional[str] = None
    cache_write_input_usd_per_1m: Optional[str] = None
    cache_read_audio_input_usd_per_1m: Optional[str] = None
    long_context_cache_read_input_usd_per_1m: Optional[str] = None
    long_context_cache_write_input_usd_per_1m: Optional[str] = None
    batch_input_usd_per_1m: Optional[str] = None
    batch_output_usd_per_1m: Optional[str] = None
    training_usd_per_1m: Optional[str] = None
    fine_tuned_input_usd_per_1m: Optional[str] = None
    fine_tuned_output_usd_per_1m: Optional[str] = None
    audio_input_usd_per_1m: Optional[str] = None
    audio_output_usd_per_1m: Optional[str] = None
    transcription_usd_per_1m: Optional[str] = None
    cached_audio_input_usd_per_1m: Optional[str] = None
    cached_text_input_usd_per_1m: Optional[str] = None
    cache_hit_usd_per_1m: Optional[str] = None
    output_with_audio_usd_per_1m: Optional[str] = None
    output_with_video_usd_per_1m: Optional[str] = None
    image_input_usd_per_image: Optional[str] = None
    image_output_size: Optional[str] = None
    effective_date: Optional[str] = None
    deprecated_date: Optional[str] = None
    notes: Optional[str] = None
    source_url: Optional[str] = None
    discount_pct: Optional[str] = None


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
    # Additional spec fields
    brand: Optional[str] = None
    provider: Optional[str] = None
    supports_realtime: Optional[bool] = None
    supports_embeddings: Optional[bool] = None
    supports_tools: Optional[bool] = None
    supports_structured_output: Optional[bool] = None
    supports_system_prompt: Optional[bool] = None
    supports_batching: Optional[bool] = None
    supports_background_response: Optional[bool] = None
    supports_video_generation: Optional[bool] = None
    supports_image_edit: Optional[bool] = None
    supports_image_inpaint: Optional[bool] = None
    supports_image_outpaint: Optional[bool] = None
    supports_image_mix: Optional[bool] = None
    supports_image_reframe: Optional[bool] = None
    supports_image_upscale: Optional[bool] = None
    supports_image_remove_background: Optional[bool] = None
    supports_image_reference: Optional[bool] = None
    context_window: Optional[int] = None
    standard_context_threshold: Optional[int] = None
    realtime_session_max_tokens: Optional[int] = None
    realtime_max_concurrent_per_owner: Optional[int] = None
    is_composite: bool = False
    composite_models: Optional[List[str]] = None


class ListModelsParams(BaseModel):
    model_config = ConfigDict(extra="ignore")
    free: Optional[bool] = None
    type: Optional[Literal["text", "embedding", "image", "audio", "video"]] = None
    provider: Optional[str] = None


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
    team_id: Optional[str] = None


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


# Multimodal embedding input types
class ImageEmbeddingUrl(BaseModel):
    model_config = ConfigDict(extra="ignore")
    url: str


class VideoEmbeddingUrl(BaseModel):
    model_config = ConfigDict(extra="ignore")
    url: str


class MultimodalEmbeddingInput(BaseModel):
    model_config = ConfigDict(extra="ignore")
    type: Literal["text", "image_url", "video_url"]
    text: Optional[str] = None
    image_url: Optional[ImageEmbeddingUrl] = None
    video_url: Optional[VideoEmbeddingUrl] = None


class EmbeddingsParams(BaseModel):
    model_config = ConfigDict(extra="ignore")
    model: Optional[str] = None
    input: Union[str, List[str], List[int], List[List[int]], List[MultimodalEmbeddingInput]]
    dimensions: Optional[int] = Field(default=None, ge=1)
    encoding_format: Optional[Literal["float", "base64"]] = None
    input_type: Optional[str] = None
    provider: Optional[Union[str, ProviderPreferences]] = None
    user: Optional[str] = Field(default=None, max_length=256)
    instructions: Optional[str] = None
    sparse_embedding: Optional[Dict[str, Any]] = None


class EmbeddingItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    object: str
    index: int
    embedding: Union[List[float], str]


class EmbeddingsUsage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    prompt_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    byok_used: Optional[bool] = None
    fallback_triggered: Optional[bool] = None


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
    # Additional spec fields (second-pass findings)
    previous_response_id: Optional[str] = None
    instructions: Optional[str] = None
    thinking: Optional[Dict[str, Any]] = None
    caching: Optional[Dict[str, Any]] = None
    store: Optional[bool] = None
    include: Optional[List[Any]] = None
    expire_at: Optional[int] = None
    max_tool_calls: Optional[int] = Field(default=None, ge=1, le=10)
    context_management: Optional[Dict[str, Any]] = None
    plugins: Optional[List[Any]] = None


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
    results: Optional[List[Dict[str, Any]]] = None
    errors_detail: Optional[List[Dict[str, Any]]] = None
    error_file_id: Optional[str] = None
    request_counts: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


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
    # Additional spec fields (previously missing — silently dropped due to extra="ignore")
    aspect_ratio: Optional[str] = None
    resolution: Optional[str] = None
    output_compression: Optional[int] = Field(default=None, ge=0, le=100)
    background: Optional[Literal["transparent", "opaque", "auto"]] = None
    moderation: Optional[Literal["low", "auto"]] = None
    partial_images: Optional[int] = Field(default=None, ge=0, le=3)
    image: Optional[Union[str, List[str]]] = None
    seed: Optional[int] = Field(default=None, ge=-1, le=2147483647)
    sequential_image_generation: Optional[Literal["auto", "disabled"]] = None
    sequential_image_generation_options: Optional[Dict[str, Any]] = None
    guidance_scale: Optional[float] = Field(default=None, ge=1, le=10)
    watermark: Optional[bool] = None
    optimize_prompt_options: Optional[Dict[str, Any]] = None


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
# Video
# ---------------------------------------------------------------------------


class VideoContentItem(BaseModel):
    """A single item in the content array (text, image_url, video_url, audio_url)."""
    model_config = ConfigDict(extra="ignore")
    type: str
    text: Optional[str] = None
    image_url: Optional[Dict[str, Any]] = None
    video_url: Optional[Dict[str, Any]] = None
    audio_url: Optional[Dict[str, Any]] = None
    draft_task: Optional[Dict[str, Any]] = None
    role: Optional[str] = None


class VideoGenerationParams(BaseModel):
    """Request body for POST /v1/video/generations."""
    model_config = ConfigDict(extra="ignore")
    model: str
    content: List[VideoContentItem]
    callback_url: Optional[str] = None
    return_last_frame: Optional[bool] = None
    service_tier: Optional[str] = None
    execution_expires_after: Optional[int] = None
    generate_audio: Optional[bool] = None
    draft: Optional[bool] = None
    resolution: Optional[str] = None
    ratio: Optional[str] = None
    duration: Optional[int] = None
    frames: Optional[int] = None
    seed: Optional[int] = None
    camera_fixed: Optional[bool] = None
    watermark: Optional[bool] = None
    safety_identifier: Optional[str] = None
    priority: Optional[int] = None


class CreateVideoGenerationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str


class VideoTaskError(BaseModel):
    model_config = ConfigDict(extra="ignore")
    code: str
    message: str


class VideoTaskContent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    video_url: Optional[str] = None
    last_frame_url: Optional[str] = None


class VideoTaskUsage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    completion_tokens: int
    total_tokens: int


class VideoTaskResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    status: str
    model: Optional[str] = None
    error: Optional[VideoTaskError] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None
    content: Optional[VideoTaskContent] = None
    seed: Optional[int] = None
    resolution: Optional[str] = None
    ratio: Optional[str] = None
    duration: Optional[int] = None
    frames: Optional[int] = None
    framespersecond: Optional[int] = None
    generate_audio: Optional[bool] = None
    safety_identifier: Optional[str] = None
    priority: Optional[int] = None
    draft: Optional[bool] = None
    draft_task_id: Optional[str] = None
    service_tier: Optional[str] = None
    execution_expires_after: Optional[int] = None
    usage: Optional[VideoTaskUsage] = None


class ListVideoGenerationsParams(BaseModel):
    model_config = ConfigDict(extra="ignore")
    status: Optional[str] = None
    model: Optional[str] = None
    created_after: Optional[str] = None
    created_before: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


class VideoTaskListResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    object: Optional[str] = None
    data: List[VideoTaskResponse]
    has_more: bool
    total: int
    limit: int
    offset: int


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
# Audio
# ---------------------------------------------------------------------------


class VoiceSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    stability: Optional[float] = None
    similarity_boost: Optional[float] = None
    style: Optional[float] = None
    use_speaker_boost: Optional[bool] = None
    speed: Optional[float] = None


class PronunciationDictionaryLocator(BaseModel):
    model_config = ConfigDict(extra="ignore")
    pronunciation_dictionary_id: str
    version_id: str


class SpeechParams(BaseModel):
    model_config = ConfigDict(extra="ignore")
    input: str
    model: Optional[str] = None
    voice: Optional[str] = None
    stream: Optional[bool] = None
    response_format: Optional[str] = None
    language_code: Optional[str] = None
    voice_settings: Optional[VoiceSettings] = None
    pronunciation_dictionary_locators: Optional[List[PronunciationDictionaryLocator]] = None
    seed: Optional[int] = None
    previous_text: Optional[str] = None
    next_text: Optional[str] = None
    previous_request_ids: Optional[List[str]] = None
    next_request_ids: Optional[List[str]] = None
    apply_text_normalization: Optional[str] = None
    apply_language_text_normalization: Optional[bool] = None
    use_pvc_as_ivc: Optional[bool] = None
    enable_logging: Optional[bool] = None
    optimize_streaming_latency: Optional[int] = None
    speaker: Optional[str] = None
    target_language_code: Optional[str] = None
    pitch: Optional[float] = None
    pace: Optional[float] = None
    loudness: Optional[float] = None
    speech_sample_rate: Optional[int] = None
    enable_preprocessing: Optional[bool] = None


class TranscriptionParams(BaseModel):
    model_config = ConfigDict(extra="ignore")
    model: str
    language_code: Optional[str] = None
    tag_audio_events: Optional[bool] = None
    num_speakers: Optional[int] = None
    timestamps_granularity: Optional[str] = None
    diarize: Optional[bool] = None
    diarization_threshold: Optional[float] = None
    additional_formats: Optional[str] = None
    file_format: Optional[str] = None
    cloud_storage_url: Optional[str] = None
    source_url: Optional[str] = None
    webhook: Optional[bool] = None
    webhook_id: Optional[str] = None
    temperature: Optional[float] = None
    seed: Optional[int] = None
    use_multi_channel: Optional[bool] = None
    webhook_metadata: Optional[str] = None
    entity_detection: Optional[str] = None
    no_verbatim: Optional[bool] = None
    detect_speaker_roles: Optional[bool] = None
    entity_redaction: Optional[str] = None
    entity_redaction_mode: Optional[str] = None
    keyterms: Optional[List[str]] = None
    with_timestamps: Optional[bool] = None
    debug_mode: Optional[bool] = None


class TranscriptionTranslateParams(BaseModel):
    model_config = ConfigDict(extra="ignore")
    model: Optional[str] = None
    prompt: Optional[str] = None


class AudioTranslationsParams(BaseModel):
    """Params for POST /v1/audio/translations (standalone translation endpoint).

    Distinct from TranscriptionTranslateParams which targets
    POST /v1/audio/transcriptions/translate.
    """

    model_config = ConfigDict(extra="ignore")
    model: str
    prompt: Optional[str] = None
    response_format: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)


class TranscriptionResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    text: str


class ListVoicesParams(BaseModel):
    model_config = ConfigDict(extra="ignore")
    next_page_token: Optional[str] = None
    page_size: Optional[int] = None
    search: Optional[str] = None
    sort: Optional[str] = None
    sort_direction: Optional[str] = None
    voice_type: Optional[str] = None
    category: Optional[str] = None
    include_total_count: Optional[bool] = None
    voice_ids: Optional[List[str]] = None


class Voice(BaseModel):
    model_config = ConfigDict(extra="ignore")
    voice_id: str
    name: str
    # Optional: minimal voice objects (id + name only) must not fail validation.
    category: Optional[str] = None
    description: Optional[str] = None
    preview_url: Optional[str] = None
    # Label values are provider-defined and not always strings.
    labels: Dict[str, Any] = Field(default_factory=dict)


class VoicesResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    voices: List[Voice]
    # Optional so a response that omits has_more / total_count is not rejected,
    # and an absent pagination flag is distinguishable from a real False.
    has_more: Optional[bool] = None
    total_count: Optional[int] = None
    next_page_token: Optional[str] = None


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


# ---------------------------------------------------------------------------
# Moderations — POST /v1/moderations
# ---------------------------------------------------------------------------


class ModerationImageUrl(BaseModel):
    model_config = ConfigDict(extra="ignore")
    url: str


class ModerationInputItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    type: Literal["text", "image_url"]
    text: Optional[str] = None
    image_url: Optional[ModerationImageUrl] = None


class ModerationParams(BaseModel):
    model_config = ConfigDict(extra="ignore")
    input: Union[str, List[str], List[ModerationInputItem]]
    model: str = "omni-moderation-latest"


class ModerationResult(BaseModel):
    model_config = ConfigDict(extra="allow")
    flagged: bool
    categories: Dict[str, bool] = Field(default_factory=dict)
    category_scores: Dict[str, float] = Field(default_factory=dict)


class ModerationResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: Optional[str] = None
    model: Optional[str] = None
    results: List[ModerationResult] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Web search — POST /v1/web/search
# ---------------------------------------------------------------------------


class WebSearchParams(BaseModel):
    model_config = ConfigDict(extra="ignore")
    query: str = Field(..., min_length=1, max_length=2000)
    model: Optional[str] = None
    provider: Optional[Literal["native", "tavily"]] = None
    max_results: int = Field(default=5, ge=1, le=20)
    search_depth: Literal["basic", "advanced"] = "basic"
    include_domains: Optional[List[str]] = None
    exclude_domains: Optional[List[str]] = None
    include_answer: bool = False


class WebSearchResultItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: str
    url: str
    content: str = ""
    score: Optional[float] = None
    published_date: Optional[str] = None


class WebSearchResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    query: str
    answer: Optional[str] = None
    results: List[WebSearchResultItem] = Field(default_factory=list)
    # `provider` is always one of native|tavily today, but typed as str so an
    # added engine never breaks response parsing for existing SDK versions.
    provider: str
    request_id: str = ""


# ---------------------------------------------------------------------------
# Router select — POST /v1/router/select
# ---------------------------------------------------------------------------


class RouterSelectParams(BaseModel):
    model_config = ConfigDict(extra="ignore")
    messages: List[ChatMessage] = Field(..., min_length=1)
    api_type: Literal["completions", "responses", "embeddings"] = "completions"
    exclude_models: Optional[List[str]] = None


class AutoRouterMeta(BaseModel):
    model_config = ConfigDict(extra="ignore")
    fallback_used: bool = False
    fallback_reason: Optional[str] = None


class RouterSelectResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    model: str
    auto_router: AutoRouterMeta
    reasoning_effort: Optional[str] = None


# ---------------------------------------------------------------------------
# Models — GET /v1/models/search (paginated catalog search)
# ---------------------------------------------------------------------------


class ModelSearchParams(BaseModel):
    model_config = ConfigDict(extra="ignore")
    q: Optional[str] = None
    free: Optional[bool] = None
    discounted: Optional[bool] = None
    input_modality: Optional[List[str]] = None
    output_modality: Optional[List[str]] = None
    brand: Optional[List[str]] = None
    sort: Optional[Literal["brand", "name", "id", "context_length"]] = None
    order: Optional[Literal["asc", "desc"]] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


class ModelsPage(BaseModel):
    model_config = ConfigDict(extra="allow")
    items: List[ModelInfo] = Field(default_factory=list)
    total: int
    limit: int
    offset: int
    brands: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Responses — GET /v1/responses (list background jobs) + GET /v1/responses/{id}
# ---------------------------------------------------------------------------


class ResponsesListItem(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    object: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[int] = None
    completed_at: Optional[int] = None
    usage_synced: Optional[bool] = None


class ResponsesListResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    object: Optional[str] = None
    data: List[ResponsesListItem] = Field(default_factory=list)
    has_more: bool = False
    first_id: Optional[str] = None
    last_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Images — POST /v1/images/edits (edit / inpaint / outpaint / upscale / …)
# ---------------------------------------------------------------------------


class ImageRef(BaseModel):
    """An image reference for the edits endpoint: a data URL or bare base64.

    ``url`` must be ``data:image/<fmt>;base64,<b64>`` or a bare base64 string —
    remote http(s) URLs are rejected by this endpoint. You may also pass the
    string directly instead of wrapping it in ImageRef.
    """

    model_config = ConfigDict(extra="ignore")
    url: str


class ImageEditParams(BaseModel):
    """Request body for POST /v1/images/edits (JSON/base64 mode).

    ``image`` (and ``mask`` / ``reference_images``) accept a base64 / data-URL
    string or an :class:`ImageRef`. ``prompt`` is required for the ``edit``,
    ``outpaint`` and ``mix`` operations.
    """

    model_config = ConfigDict(extra="ignore")
    model: str
    image: Union[str, ImageRef]
    prompt: str = ""
    operation: Literal[
        "edit", "inpaint", "outpaint", "mix", "reframe", "upscale", "remove_background"
    ] = "edit"
    mask: Optional[Union[str, ImageRef]] = None
    reference_images: Optional[List[Union[str, ImageRef]]] = None
    n: Optional[int] = None
    size: Optional[str] = None
    response_format: Optional[Literal["url", "b64_json"]] = None
    background: Optional[str] = None
    upscale_factor: Optional[str] = None
    quality_tier: Optional[str] = None
    aspect_ratio: Optional[str] = None
    resolution: Optional[str] = None
    expand_factor: Optional[Union[str, float]] = None
    mask_feather: Optional[int] = None


# ---------------------------------------------------------------------------
# Documents — GET /v1/documents, POST /v1/documents/generate,
#             GET /v1/documents/{document_id}
# ---------------------------------------------------------------------------


class GenerateDocumentRequest(BaseModel):
    """Request body for POST /v1/documents/generate."""

    model_config = ConfigDict(extra="ignore")

    format: Literal["pdf", "docx", "pptx", "csv", "xlsx"]
    prompt: str
    model: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ListDocumentsParams(BaseModel):
    """Query params for GET /v1/documents."""

    model_config = ConfigDict(extra="ignore")

    limit: Optional[int] = Field(default=None, ge=1, le=200)
    offset: Optional[int] = Field(default=None, ge=0)


class DocumentResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    document_id: str
    status: str
    format: str
    model: str
    title: Optional[str] = None
    download_url: Optional[str] = None
    expires_at: Optional[str] = None
    size_bytes: Optional[int] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    failure_reason: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class DocumentListResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    documents: List[DocumentResponse]
    total: int
    limit: int
    offset: int
