"""Contract tests for findings fixed in this batch.

Covers:
  - EmbeddingsUsage optional fields / BYOK response (finding #11/16)
  - Documents response shapes (finding #1/2)
  - RouterSelectParams api_type widened enum (finding #9)
  - ImageGenerationParams new fields (finding #4/5)
  - ContentPartVideo / video_url part (finding #10)
  - ToolCall thought_signature (finding #10)
  - Multimodal embedding input types (finding #3/8)
  - ModelInfo / ModelPricing extended fields (finding #7)
  - BatchObject declared fields (finding #14)
"""

import json
from pathlib import Path

import pytest

from meshapi._types import (
    BatchObject,
    ContentPartVideo,
    DocumentListResponse,
    DocumentResponse,
    EmbeddingsParams,
    EmbeddingsResponse,
    EmbeddingsUsage,
    GenerateDocumentRequest,
    ImageEmbeddingUrl,
    ImageGenerationParams,
    ListDocumentsParams,
    ModelInfo,
    ModelPricing,
    MultimodalEmbeddingInput,
    RouterSelectParams,
    ToolCall,
    ToolCallFunction,
    ChatMessage,
    VideoEmbeddingUrl,
    VideoUrl,
)

FIXTURES = Path(__file__).parent.parent / "fixtures"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


# ---------------------------------------------------------------------------
# EmbeddingsUsage — BYOK responses can omit token counts (finding #11/16)
# ---------------------------------------------------------------------------


def test_embeddings_usage_byok_no_tokens():
    """EmbeddingsUsage must accept a usage dict with no prompt_tokens/total_tokens."""
    usage = EmbeddingsUsage.model_validate({"byok_used": True, "fallback_triggered": False})
    assert usage.prompt_tokens is None
    assert usage.total_tokens is None
    assert usage.byok_used is True
    assert usage.fallback_triggered is False


def test_embeddings_response_byok_fixture():
    data = load("embeddings_byok_usage.json")
    resp = EmbeddingsResponse.model_validate(data)
    assert resp.usage is not None
    assert resp.usage.prompt_tokens is None
    assert resp.usage.total_tokens is None
    assert resp.usage.byok_used is True


def test_embeddings_usage_normal_tokens_still_work():
    usage = EmbeddingsUsage.model_validate({"prompt_tokens": 10, "total_tokens": 10})
    assert usage.prompt_tokens == 10
    assert usage.total_tokens == 10


# ---------------------------------------------------------------------------
# Documents (finding #1/2)
# ---------------------------------------------------------------------------


def test_document_response_full():
    data = load("document_response.json")
    doc = DocumentResponse.model_validate(data)
    assert doc.document_id == "doc_abc123"
    assert doc.status == "completed"
    assert doc.format == "pdf"
    assert doc.model == "google/gemini-2.5-flash-lite"
    assert doc.title == "My Report"
    assert doc.size_bytes == 102400
    assert doc.prompt_tokens == 150
    assert doc.total_tokens == 2150
    assert doc.failure_reason is None


def test_document_response_minimal():
    """A pending document with only required fields must parse without error."""
    data = {
        "document_id": "doc_xyz",
        "status": "pending",
        "format": "xlsx",
        "model": "google/gemini-2.5-flash-lite",
    }
    doc = DocumentResponse.model_validate(data)
    assert doc.document_id == "doc_xyz"
    assert doc.title is None
    assert doc.download_url is None
    assert doc.size_bytes is None


def test_document_list_response():
    data = load("document_list_response.json")
    result = DocumentListResponse.model_validate(data)
    assert result.total == 2
    assert result.limit == 50
    assert result.offset == 0
    assert len(result.documents) == 2
    completed = result.documents[0]
    assert completed.document_id == "doc_abc123"
    assert completed.status == "completed"
    pending = result.documents[1]
    assert pending.status == "pending"
    assert pending.title is None


def test_generate_document_request_valid():
    req = GenerateDocumentRequest(format="pdf", prompt="Write a report about AI.")
    assert req.format == "pdf"
    assert req.model is None
    assert req.metadata is None


def test_generate_document_request_with_model():
    req = GenerateDocumentRequest(
        format="docx",
        prompt="Summarise Q1 results",
        model="google/gemini-2.5-flash-lite",
        metadata={"source": "finance"},
    )
    dumped = req.model_dump(exclude_none=True)
    assert dumped["format"] == "docx"
    assert dumped["model"] == "google/gemini-2.5-flash-lite"
    assert dumped["metadata"] == {"source": "finance"}


def test_list_documents_params_serialises():
    params = ListDocumentsParams(limit=10, offset=20)
    query = {k: str(v) for k, v in params.model_dump(exclude_none=True).items()}
    assert query == {"limit": "10", "offset": "20"}


def test_list_documents_params_empty():
    params = ListDocumentsParams()
    assert params.model_dump(exclude_none=True) == {}


# ---------------------------------------------------------------------------
# DocumentsResource — path / method wiring (finding #1/2)
# ---------------------------------------------------------------------------


def test_documents_resource_generate_calls_post():
    from meshapi.resources.documents import DocumentsResource
    from unittest.mock import MagicMock

    mock_http = MagicMock()
    mock_http.post.return_value = {
        "document_id": "doc_1",
        "status": "pending",
        "format": "pdf",
        "model": "google/gemini-2.5-flash-lite",
    }
    resource = DocumentsResource(mock_http)
    req = GenerateDocumentRequest(format="pdf", prompt="Hello")
    resp = resource.generate(req)
    mock_http.post.assert_called_once_with(
        "/v1/documents/generate",
        {"format": "pdf", "prompt": "Hello"},
    )
    assert resp.document_id == "doc_1"


def test_documents_resource_list_no_params():
    from meshapi.resources.documents import DocumentsResource
    from unittest.mock import MagicMock

    mock_http = MagicMock()
    mock_http.get.return_value = {"documents": [], "total": 0, "limit": 50, "offset": 0}
    resource = DocumentsResource(mock_http)
    resource.list()
    mock_http.get.assert_called_once_with("/v1/documents", params=None)


def test_documents_resource_list_with_params():
    from meshapi.resources.documents import DocumentsResource
    from unittest.mock import MagicMock

    mock_http = MagicMock()
    mock_http.get.return_value = {"documents": [], "total": 0, "limit": 10, "offset": 5}
    resource = DocumentsResource(mock_http)
    resource.list(ListDocumentsParams(limit=10, offset=5))
    mock_http.get.assert_called_once_with("/v1/documents", params={"limit": "10", "offset": "5"})


def test_documents_resource_retrieve_quotes_path():
    from meshapi.resources.documents import DocumentsResource
    from unittest.mock import MagicMock

    mock_http = MagicMock()
    mock_http.get.return_value = {
        "document_id": "doc/special",
        "status": "completed",
        "format": "pdf",
        "model": "google/gemini-2.5-flash-lite",
    }
    resource = DocumentsResource(mock_http)
    resource.retrieve("doc/special")
    mock_http.get.assert_called_once_with("/v1/documents/doc%2Fspecial")


# ---------------------------------------------------------------------------
# RouterSelectParams api_type widened (finding #9)
# ---------------------------------------------------------------------------


def test_router_select_params_completions():
    params = RouterSelectParams(
        messages=[ChatMessage(role="user", content="Hello")],
        api_type="completions",
    )
    assert params.api_type == "completions"


def test_router_select_params_responses():
    params = RouterSelectParams(
        messages=[ChatMessage(role="user", content="Hello")],
        api_type="responses",
    )
    assert params.api_type == "responses"


def test_router_select_params_embeddings():
    params = RouterSelectParams(
        messages=[ChatMessage(role="user", content="Embed this")],
        api_type="embeddings",
    )
    assert params.api_type == "embeddings"


def test_router_select_params_default_is_completions():
    params = RouterSelectParams(messages=[ChatMessage(role="user", content="Hi")])
    assert params.api_type == "completions"


# ---------------------------------------------------------------------------
# ImageGenerationParams missing fields (finding #4/5)
# ---------------------------------------------------------------------------


def test_image_generation_params_all_new_fields():
    params = ImageGenerationParams(
        prompt="A cat",
        seed=42,
        background="transparent",
        moderation="low",
        partial_images=2,
        image="data:image/png;base64,abc",
        aspect_ratio="16:9",
        resolution="1920x1080",
        output_compression=80,
        sequential_image_generation="auto",
        sequential_image_generation_options={"key": "val"},
        guidance_scale=7.5,
        watermark=False,
        optimize_prompt_options={"enhance": True},
    )
    dumped = params.model_dump(exclude_none=True)
    assert dumped["seed"] == 42
    assert dumped["background"] == "transparent"
    assert dumped["moderation"] == "low"
    assert dumped["partial_images"] == 2
    assert dumped["image"] == "data:image/png;base64,abc"
    assert dumped["aspect_ratio"] == "16:9"
    assert dumped["guidance_scale"] == 7.5
    assert dumped["watermark"] is False
    assert dumped["optimize_prompt_options"] == {"enhance": True}


def test_image_generation_params_image_list():
    params = ImageGenerationParams(
        prompt="Mix",
        image=["data:image/png;base64,a", "data:image/png;base64,b"],
    )
    dumped = params.model_dump(exclude_none=True)
    assert isinstance(dumped["image"], list)
    assert len(dumped["image"]) == 2


# ---------------------------------------------------------------------------
# ContentPartVideo / video_url (finding #10)
# ---------------------------------------------------------------------------


def test_content_part_video_validates():
    part = ContentPartVideo.model_validate(
        {"type": "video_url", "video_url": {"url": "https://example.com/video.mp4"}}
    )
    assert part.type == "video_url"
    assert part.video_url.url == "https://example.com/video.mp4"
    assert part.fps is None


def test_content_part_video_with_fps():
    part = ContentPartVideo.model_validate(
        {"type": "video_url", "video_url": {"url": "https://example.com/v.mp4"}, "fps": "30"}
    )
    assert part.fps == "30"


def test_chat_message_with_video_url_part():
    msg = ChatMessage.model_validate({
        "role": "user",
        "content": [
            {"type": "video_url", "video_url": {"url": "https://example.com/clip.mp4"}}
        ],
    })
    assert msg.role == "user"
    assert len(msg.content) == 1  # type: ignore[arg-type]
    part = msg.content[0]  # type: ignore[index]
    assert isinstance(part, ContentPartVideo)


# ---------------------------------------------------------------------------
# ToolCall thought_signature (finding #10)
# ---------------------------------------------------------------------------


def test_tool_call_with_thought_signature():
    tc = ToolCall.model_validate({
        "id": "call_abc",
        "type": "function",
        "function": {"name": "my_tool", "arguments": "{}"},
        "thought_signature": "sig_xyz",
    })
    assert tc.thought_signature == "sig_xyz"


def test_tool_call_without_thought_signature():
    tc = ToolCall.model_validate({
        "id": "call_abc",
        "type": "function",
        "function": {"name": "my_tool", "arguments": "{}"},
    })
    assert tc.thought_signature is None


def test_tool_call_thought_signature_in_dump():
    tc = ToolCall(
        id="call_1",
        type="function",
        function=ToolCallFunction(name="fn", arguments="{}"),
        thought_signature="some_sig",
    )
    dumped = tc.model_dump(exclude_none=True)
    assert dumped["thought_signature"] == "some_sig"


# ---------------------------------------------------------------------------
# Multimodal embedding input types (finding #3/8)
# ---------------------------------------------------------------------------


def test_multimodal_embedding_input_text():
    item = MultimodalEmbeddingInput.model_validate({"type": "text", "text": "Hello"})
    assert item.type == "text"
    assert item.text == "Hello"


def test_multimodal_embedding_input_image_url():
    item = MultimodalEmbeddingInput.model_validate(
        {"type": "image_url", "image_url": {"url": "https://img.example.com/photo.jpg"}}
    )
    assert item.type == "image_url"
    assert isinstance(item.image_url, ImageEmbeddingUrl)
    assert item.image_url.url == "https://img.example.com/photo.jpg"


def test_multimodal_embedding_input_video_url():
    item = MultimodalEmbeddingInput.model_validate(
        {"type": "video_url", "video_url": {"url": "https://vid.example.com/clip.mp4"}}
    )
    assert item.type == "video_url"
    assert isinstance(item.video_url, VideoEmbeddingUrl)


def test_embeddings_params_with_multimodal_input():
    params = EmbeddingsParams(
        model="byteplus/doubao-embedding-vision",
        input=[
            MultimodalEmbeddingInput(type="text", text="Hello"),
            MultimodalEmbeddingInput(
                type="image_url",
                image_url=ImageEmbeddingUrl(url="https://img.example.com/photo.jpg"),
            ),
        ],
    )
    assert len(params.input) == 2  # type: ignore[arg-type]


def test_embeddings_params_instructions_and_sparse():
    params = EmbeddingsParams(
        input="Hello",
        instructions="Represent this as a search query",
        sparse_embedding={"format": "lexical"},
    )
    dumped = params.model_dump(exclude_none=True)
    assert dumped["instructions"] == "Represent this as a search query"
    assert dumped["sparse_embedding"] == {"format": "lexical"}


# ---------------------------------------------------------------------------
# ModelInfo / ModelPricing extended fields (finding #7)
# ---------------------------------------------------------------------------


def test_model_info_new_fields():
    data = {
        "id": "test/model",
        "name": "Test Model",
        "is_free": False,
        "pricing": {"prompt_usd_per_1k": "0.001", "completion_usd_per_1k": "0.002"},
        "brand": "TestCo",
        "provider": "test-provider",
        "supports_realtime": True,
        "supports_tools": True,
        "supports_structured_output": False,
        "supports_system_prompt": True,
        "supports_batching": True,
        "supports_background_response": False,
        "supports_video_generation": False,
        "supports_embeddings": False,
        "context_window": 128000,
        "is_composite": False,
        "composite_models": None,
    }
    model = ModelInfo.model_validate(data)
    assert model.brand == "TestCo"
    assert model.provider == "test-provider"
    assert model.supports_realtime is True
    assert model.supports_tools is True
    assert model.context_window == 128000
    assert model.is_composite is False
    assert model.composite_models is None


def test_model_pricing_new_fields():
    data = {
        "prompt_usd_per_1k": "0.001",
        "completion_usd_per_1k": "0.002",
        "pricing_unit": "per_1m_tokens",
        "prompt_usd_per_1m": "1.00",
        "completion_usd_per_1m": "2.00",
        "cache_read_input_usd_per_1m": "0.50",
        "batch_input_usd_per_1m": "0.25",
        "batch_output_usd_per_1m": "0.50",
        "effective_date": "2024-01-01",
        "notes": "Standard pricing",
        "source_url": "https://example.com/pricing",
        "discount_pct": "0",
    }
    pricing = ModelPricing.model_validate(data)
    assert pricing.pricing_unit == "per_1m_tokens"
    assert pricing.prompt_usd_per_1m == "1.00"
    assert pricing.cache_read_input_usd_per_1m == "0.50"
    assert pricing.batch_input_usd_per_1m == "0.25"
    assert pricing.effective_date == "2024-01-01"
    assert pricing.notes == "Standard pricing"
    assert pricing.discount_pct == "0"


def test_model_pricing_phantom_fields_dropped():
    """Old phantom fields (image_usd_per_image etc.) in server response are silently ignored."""
    data = {
        "prompt_usd_per_1k": "0.001",
        "completion_usd_per_1k": "0.002",
        "image_usd_per_image": None,
        "prompt_usd_per_1k_discounted": None,
        "completion_usd_per_1k_discounted": None,
    }
    pricing = ModelPricing.model_validate(data)
    assert pricing.prompt_usd_per_1k == "0.001"
    # Phantom fields no longer declared but extra="ignore" means no crash
    assert not hasattr(pricing, "prompt_usd_per_1k_discounted") or \
        getattr(pricing, "prompt_usd_per_1k_discounted", "ABSENT") == "ABSENT"


# ---------------------------------------------------------------------------
# BatchObject declared fields (finding #14)
# ---------------------------------------------------------------------------


def test_batch_object_declared_results_field():
    data = {
        "id": "batch_abc",
        "status": "completed",
        "results": [{"custom_id": "req_1", "response": {"status_code": 200, "body": {}}}],
        "errors_detail": [],
        "request_counts": {"total": 1, "completed": 1, "failed": 0},
        "metadata": {"job": "nightly"},
    }
    obj = BatchObject.model_validate(data)
    assert obj.id == "batch_abc"
    assert obj.results is not None
    assert len(obj.results) == 1
    assert obj.results[0]["custom_id"] == "req_1"
    assert obj.errors_detail == []
    assert obj.request_counts == {"total": 1, "completed": 1, "failed": 0}
    assert obj.metadata == {"job": "nightly"}


# ---------------------------------------------------------------------------
# Models list() type and provider params (finding #6)
# ---------------------------------------------------------------------------


def test_models_list_type_param():
    from meshapi.resources.models import ModelsResource
    from unittest.mock import MagicMock

    mock_http = MagicMock()
    mock_http.get.return_value = []
    resource = ModelsResource(mock_http)
    resource.list(type="image")
    mock_http.get.assert_called_once_with("/v1/models", params={"type": "image"})


def test_models_list_provider_param():
    from meshapi.resources.models import ModelsResource
    from unittest.mock import MagicMock

    mock_http = MagicMock()
    mock_http.get.return_value = []
    resource = ModelsResource(mock_http)
    resource.list(provider="openai")
    mock_http.get.assert_called_once_with("/v1/models", params={"provider": "openai"})


def test_models_list_combined_params():
    from meshapi.resources.models import ModelsResource
    from unittest.mock import MagicMock

    mock_http = MagicMock()
    mock_http.get.return_value = []
    resource = ModelsResource(mock_http)
    resource.list(free=True, type="text", provider="anthropic")
    mock_http.get.assert_called_once_with(
        "/v1/models",
        params={"free": "true", "type": "text", "provider": "anthropic"},
    )


# ---------------------------------------------------------------------------
# Batches URL encoding (finding #15)
# ---------------------------------------------------------------------------


def test_batches_get_quotes_batch_id():
    from meshapi.resources.batches import BatchesResource
    from unittest.mock import MagicMock

    mock_http = MagicMock()
    mock_http.get.return_value = {"id": "batch/123", "object": "batch"}
    resource = BatchesResource(mock_http)
    resource.get("batch/123")
    mock_http.get.assert_called_once_with("/v1/batches/batch%2F123")


def test_batches_cancel_quotes_batch_id():
    from meshapi.resources.batches import BatchesResource
    from unittest.mock import MagicMock

    mock_http = MagicMock()
    mock_http.post.return_value = {"id": "batch/123", "object": "batch", "status": "cancelling"}
    resource = BatchesResource(mock_http)
    resource.cancel("batch/123")
    mock_http.post.assert_called_once_with("/v1/batches/batch%2F123/cancel", {})


# ---------------------------------------------------------------------------
# InputAudio optional data + new uri/url fields (finding #10)
# ---------------------------------------------------------------------------


def test_input_audio_with_uri():
    from meshapi._types import InputAudio
    audio = InputAudio.model_validate({"uri": "gs://bucket/audio.wav", "format": "wav"})
    assert audio.uri == "gs://bucket/audio.wav"
    assert audio.data is None
    assert audio.url is None


def test_input_audio_with_url():
    from meshapi._types import InputAudio
    audio = InputAudio.model_validate({"url": "https://cdn.example.com/audio.mp3", "format": "mp3"})
    assert audio.url == "https://cdn.example.com/audio.mp3"


def test_input_audio_with_data():
    from meshapi._types import InputAudio
    audio = InputAudio.model_validate({"data": "base64data==", "format": "wav"})
    assert audio.data == "base64data=="


# ---------------------------------------------------------------------------
# MeshAPI / AsyncMeshAPI expose documents attribute (finding #1/2)
# ---------------------------------------------------------------------------


def test_meshapi_has_documents():
    import meshapi
    assert hasattr(meshapi.MeshAPI, "__init__")
    # Verify DocumentsResource is in __all__
    assert "DocumentsResource" in meshapi.__all__
    assert "AsyncDocumentsResource" in meshapi.__all__
    assert "DocumentResponse" in meshapi.__all__
    assert "DocumentListResponse" in meshapi.__all__
    assert "GenerateDocumentRequest" in meshapi.__all__
    assert "ListDocumentsParams" in meshapi.__all__


def test_meshapi_sync_client_has_documents():
    from meshapi import MeshAPI
    from meshapi.resources.documents import DocumentsResource
    client = MeshAPI(base_url="http://localhost:9999", token="test")
    assert hasattr(client, "documents")
    assert isinstance(client.documents, DocumentsResource)


def test_meshapi_async_client_has_documents():
    from meshapi import AsyncMeshAPI
    from meshapi.resources.documents import AsyncDocumentsResource
    client = AsyncMeshAPI(base_url="http://localhost:9999", token="test")
    assert hasattr(client, "documents")
    assert isinstance(client.documents, AsyncDocumentsResource)


# ---------------------------------------------------------------------------
# ImageGenerationChunk export (finding #12)
# ---------------------------------------------------------------------------


def test_image_generation_chunk_exported():
    import meshapi
    assert "ImageGenerationChunk" in meshapi.__all__
    assert hasattr(meshapi, "ImageGenerationChunk")


# ---------------------------------------------------------------------------
# ContentPartVideo and VideoUrl exported (finding #10)
# ---------------------------------------------------------------------------


def test_content_part_video_exported():
    import meshapi
    assert "ContentPartVideo" in meshapi.__all__
    assert "VideoUrl" in meshapi.__all__
    assert hasattr(meshapi, "ContentPartVideo")
    assert hasattr(meshapi, "VideoUrl")


# ---------------------------------------------------------------------------
# Multimodal embedding types exported (finding #3/8)
# ---------------------------------------------------------------------------


def test_multimodal_embedding_types_exported():
    import meshapi
    for name in ("ImageEmbeddingUrl", "VideoEmbeddingUrl", "MultimodalEmbeddingInput"):
        assert name in meshapi.__all__, f"{name} not in __all__"
        assert hasattr(meshapi, name), f"{name} not importable from meshapi"
