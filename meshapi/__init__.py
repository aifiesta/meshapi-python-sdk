"""MeshAPI Python SDK."""

from __future__ import annotations

from typing import Any

from ._errors import MeshAPIError
from ._http import AsyncHttpClient, MeshAPIConfig, SyncHttpClient
from ._types import (
    ApiErrorBody,
    ApiErrorEnvelope,
    ChatCompletionChunk,
    ChatCompletionChunkChoice,
    ChatCompletionChunkDelta,
    ChatCompletionChoice,
    ChatCompletionMessage,
    ChatCompletionParams,
    ChatCompletionResponse,
    ChatMessage,
    ChatRole,
    CompareParams,
    CompareResponse,
    CompareStreamEvent,
    ContentPart,
    ContentPartAudio,
    ContentPartImage,
    ContentPartText,
    CreateBatchParams,
    CreateTemplateParams,
    EmbeddingItem,
    EmbeddingsParams,
    EmbeddingsResponse,
    EmbeddingsUsage,
    FileObject,
    ImageDetail,
    ImageGenerationParams,
    ImageGenerationResponse,
    ImageItem,
    ImageOptions,
    ImageUsage,
    InputAudio,
    ListModelsParams,
    ModelOverride,
    ModelInfo,
    ModelPricing,
    BatchListResponse,
    BatchObject,
    BatchRequestItem,
    ProviderPreferences,
    ResponsesFunctionTool,
    ResponsesParams,
    ResponsesResponse,
    ResponsesStreamEvent,
    ResponsesUsage,
    TemplateSummary,
    TokenUsage,
    Tool,
    ToolCall,
    ToolCallFunction,
    ToolChoice,
    ToolChoiceFunction,
    ToolChoiceObject,
    ToolFunction,
    UploadBatchFileParams,
    AudioOutputOptions,
    BuiltinTool,
    UpdateTemplateParams,
    UsageInfo,
)
from .resources.batches import AsyncBatchesResource, BatchesResource
from .resources.chat import AsyncChatResource, ChatResource
from .resources.compare import AsyncCompareResource, CompareResource
from .resources.embeddings import AsyncEmbeddingsResource, EmbeddingsResource
from .resources.images import AsyncImagesResource, ImagesResource
from .resources.files import AsyncFilesResource, FilesResource
from .resources.models import AsyncModelsResource, ModelsResource
from .resources.responses import AsyncResponsesResource, ResponsesResource
from .resources.templates import AsyncTemplatesResource, TemplatesResource

__version__ = "0.1.0"
__all__ = [
    "__version__",
    "MeshAPI",
    "AsyncMeshAPI",
    "MeshAPIConfig",
    "MeshAPIError",
    # types
    "ChatRole",
    "ChatMessage",
    "ContentPart",
    "ContentPartAudio",
    "ContentPartText",
    "ContentPartImage",
    "ImageDetail",
    "InputAudio",
    "ImageOptions",
    "ImageGenerationParams",
    "ImageGenerationResponse",
    "ImageItem",
    "ImageUsage",
    "AudioOutputOptions",
    "ToolFunction",
    "Tool",
    "ToolCall",
    "ToolCallFunction",
    "ToolChoice",
    "ToolChoiceFunction",
    "ToolChoiceObject",
    "ChatCompletionParams",
    "ChatCompletionResponse",
    "ChatCompletionChoice",
    "ChatCompletionMessage",
    "ChatCompletionChunk",
    "ChatCompletionChunkChoice",
    "ChatCompletionChunkDelta",
    "UsageInfo",
    "ModelPricing",
    "ModelInfo",
    "ListModelsParams",
    "EmbeddingsParams",
    "EmbeddingItem",
    "EmbeddingsUsage",
    "EmbeddingsResponse",
    "ResponsesFunctionTool",
    "BuiltinTool",
    "ResponsesParams",
    "ResponsesUsage",
    "ResponsesResponse",
    "ResponsesStreamEvent",
    "ModelOverride",
    "CompareParams",
    "TokenUsage",
    "CompareResponse",
    "CompareStreamEvent",
    "BatchRequestItem",
    "UploadBatchFileParams",
    "FileObject",
    "CreateBatchParams",
    "BatchObject",
    "BatchListResponse",
    "ProviderPreferences",
    "CreateTemplateParams",
    "UpdateTemplateParams",
    "TemplateSummary",
    "ApiErrorBody",
    "ApiErrorEnvelope",
]


class MeshAPI:
    """Synchronous MeshAPI client.

    One instance = one auth realm. Use separate instances for different tokens
    (e.g., ``rsk_`` key for inference, JWT for template management).

    Example::

        from meshapi import MeshAPI, ChatCompletionParams, ChatMessage

        client = MeshAPI(base_url="http://localhost:8000", token="rsk_...")
        resp = client.chat.completions.create(
            ChatCompletionParams(
                model="openai/gpt-4o-mini",
                messages=[ChatMessage(role="user", content="Hello!")],
            )
        )
        print(resp.choices[0].message.content)
    """

    def __init__(
        self,
        *,
        base_url: str,
        token: str,
        timeout: float = 60.0,
        max_retries: int = 3,
        httpx_client: Any = None,
    ) -> None:
        config = MeshAPIConfig(
            base_url=base_url,
            token=token,
            timeout=timeout,
            max_retries=max_retries,
            httpx_client=httpx_client,
        )
        http = SyncHttpClient(config)
        self.chat = ChatResource(http)
        self.responses = ResponsesResource(http)
        self.embeddings = EmbeddingsResource(http)
        self.compare = CompareResource(http)
        self.files = FilesResource(http)
        self.batches = BatchesResource(http)
        self.models = ModelsResource(http)
        self.templates = TemplatesResource(http)
        self.images = ImagesResource(http)
        self._http = http

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "MeshAPI":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class AsyncMeshAPI:
    """Asynchronous MeshAPI client.

    Example::

        import asyncio
        from meshapi import AsyncMeshAPI, ChatCompletionParams, ChatMessage

        async def main():
            async with AsyncMeshAPI(base_url="http://localhost:8000", token="rsk_...") as client:
                resp = await client.chat.completions.create(
                    ChatCompletionParams(
                        model="openai/gpt-4o-mini",
                        messages=[ChatMessage(role="user", content="Hello!")],
                    )
                )
                print(resp.choices[0].message.content)
    """

    def __init__(
        self,
        *,
        base_url: str,
        token: str,
        timeout: float = 60.0,
        max_retries: int = 3,
        async_httpx_client: Any = None,
    ) -> None:
        config = MeshAPIConfig(
            base_url=base_url,
            token=token,
            timeout=timeout,
            max_retries=max_retries,
            async_httpx_client=async_httpx_client,
        )
        http = AsyncHttpClient(config)
        self.chat = AsyncChatResource(http)
        self.responses = AsyncResponsesResource(http)
        self.embeddings = AsyncEmbeddingsResource(http)
        self.compare = AsyncCompareResource(http)
        self.files = AsyncFilesResource(http)
        self.batches = AsyncBatchesResource(http)
        self.models = AsyncModelsResource(http)
        self.templates = AsyncTemplatesResource(http)
        self.images = AsyncImagesResource(http)
        self._http = http

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "AsyncMeshAPI":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()
