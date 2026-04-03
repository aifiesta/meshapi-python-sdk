"""RouterSVC Python SDK."""

from __future__ import annotations

from typing import Any

from ._errors import RouterSvcApiError
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
    ContentPart,
    ContentPartImage,
    ContentPartText,
    CreateTemplateParams,
    ImageDetail,
    ListModelsParams,
    ModelInfo,
    ModelPricing,
    TemplateSummary,
    Tool,
    ToolCall,
    ToolCallFunction,
    ToolChoice,
    ToolChoiceFunction,
    ToolChoiceObject,
    ToolFunction,
    UpdateTemplateParams,
    UsageInfo,
)
from .resources.chat import AsyncChatResource, ChatResource
from .resources.models import AsyncModelsResource, ModelsResource
from .resources.templates import AsyncTemplatesResource, TemplatesResource

__version__ = "0.1.0"
__all__ = [
    "__version__",
    "MeshAPI",
    "AsyncMeshAPI",
    "MeshAPIConfig",
    "RouterSvcApiError",
    # types
    "ChatRole",
    "ChatMessage",
    "ContentPart",
    "ContentPartText",
    "ContentPartImage",
    "ImageDetail",
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
    "CreateTemplateParams",
    "UpdateTemplateParams",
    "TemplateSummary",
    "ApiErrorBody",
    "ApiErrorEnvelope",
]


class MeshAPI:
    """Synchronous RouterSVC client.

    One instance = one auth realm. Use separate instances for different tokens
    (e.g., ``rsk_`` key for inference, JWT for template management).

    Example::

        from routersvc import MeshAPI, ChatCompletionParams, ChatMessage

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
        self.models = ModelsResource(http)
        self.templates = TemplatesResource(http)
        self._http = http

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "MeshAPI":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class AsyncMeshAPI:
    """Asynchronous RouterSVC client.

    Example::

        import asyncio
        from routersvc import AsyncMeshAPI, ChatCompletionParams, ChatMessage

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
        self.models = AsyncModelsResource(http)
        self.templates = AsyncTemplatesResource(http)
        self._http = http

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "AsyncMeshAPI":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()
