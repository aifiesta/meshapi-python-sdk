# meshapi

Official Python SDK for [Mesh API](https://meshapi.ai), an AI model gateway that gives you instant access to 300+ LLMs through a single OpenAI-compatible API.

Code once with the chat completions signature you already know. Switch between OpenAI, Anthropic, Google, Meta, Mistral, DeepSeek, xAI, Alibaba and the rest by changing a model string. Streaming, tool calling, vision, embeddings, multi-model compare, batch jobs, RAG and prompt templates from a single client.

```python
from meshapi import MeshAPI, ChatCompletionParams, ChatMessage

client = MeshAPI(base_url="https://api.meshapi.ai", token="rsk_...")

reply = client.chat.completions.create(
    ChatCompletionParams(
        model="anthropic/claude-sonnet-4.5",
        messages=[ChatMessage(role="user", content="Write a haiku about Python.")],
    )
)

print(reply.choices[0].message.content)
```

Python 3.9+. Built on `httpx` and Pydantic v2. Sync and async clients with first-class type hints.

## Install

```bash
pip install meshapi
# or
uv add meshapi
# or
poetry add meshapi
```

Get a key at [meshapi.ai](https://meshapi.ai). Data-plane keys are prefixed `rsk_`.

## What you get

| | |
|---|---|
| **One Universal API** | Code once. A single `chat.completions.create` call works across 300+ base models. |
| **Sync and async** | Pick `MeshAPI` for scripts, `AsyncMeshAPI` for servers. Same surface, same params. |
| **Streaming + tool calling** | SSE streaming via `Iterator` / `AsyncIterator`, function calling, vision and audio content parts. |
| **Reasoning models** | First-class `responses` API with `reasoning.effort` and `max_output_tokens`. |
| **Embeddings** | Drop-in OpenAI-compatible embeddings endpoint. |
| **Multi-model compare** | Fire one prompt at N models in parallel and stream their replies side by side. |
| **Audio** | Text-to-speech, speech-to-text, transcription translation, and voice listing. |
| **Video** | Submit and poll async video generation tasks. |
| **RAG** | Upload files, embed them, and run vector search — all through the same client. |
| **Batches** | Async bulk inference jobs at discounted rates with inline request submission. |
| **Prompt templates** | Server-stored prompts with `{{variable}}` slots. Update prompts without redeploying. |
| **Provider fallbacks** | If a provider experiences downtime, the gateway falls back to another supported model. |
| **Structured errors** | `MeshAPIError` with `error_code`, `status`, `request_id`, `retry_after_seconds`. |
| **Type-safe** | Every request and response is a Pydantic v2 model. |

## Authentication

```python
client = MeshAPI(base_url="https://api.meshapi.ai", token="rsk_...")
```

## Chat completions

```python
from meshapi import MeshAPI, ChatCompletionParams, ChatMessage

reply = client.chat.completions.create(
    ChatCompletionParams(
        model="openai/gpt-4o-mini",
        messages=[
            ChatMessage(role="system", content="You are a concise assistant."),
            ChatMessage(role="user", content="What is the capital of France?"),
        ],
        temperature=0.7,
        max_tokens=256,
    )
)
print(reply.choices[0].message.content)
```

### Async

```python
import asyncio
from meshapi import AsyncMeshAPI, ChatCompletionParams, ChatMessage

async def main():
    async with AsyncMeshAPI(base_url="https://api.meshapi.ai", token="rsk_...") as client:
        reply = await client.chat.completions.create(
            ChatCompletionParams(
                model="openai/gpt-4o-mini",
                messages=[ChatMessage(role="user", content="Hello!")],
            )
        )
        print(reply.choices[0].message.content)

asyncio.run(main())
```

### Streaming

```python
for chunk in client.chat.completions.stream(
    ChatCompletionParams(
        model="openai/gpt-4o-mini",
        messages=[ChatMessage(role="user", content="Write a haiku about Python.")],
    )
):
    if chunk.choices and chunk.choices[0].delta:
        print(chunk.choices[0].delta.content or "", end="", flush=True)
```

### Tool calling

```python
from meshapi import Tool, ToolFunction

params = ChatCompletionParams(
    model="openai/gpt-4o",
    messages=[ChatMessage(role="user", content="What is the weather in Paris?")],
    tools=[
        Tool(
            type="function",
            function=ToolFunction(
                name="get_weather",
                description="Get current weather for a city",
                parameters={
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"],
                },
            ),
        )
    ],
    tool_choice="auto",
)
```

## Responses API (reasoning models)

```python
from meshapi import ResponsesParams

reply = client.responses.create(
    ResponsesParams(
        model="openai/o4-mini",
        input="Explain the halting problem in two sentences.",
        reasoning={"effort": "medium"},
        max_output_tokens=512,
    )
)
```

## Embeddings

```python
from meshapi import EmbeddingsParams

result = client.embeddings.create(
    EmbeddingsParams(
        model="openai/text-embedding-3-small",
        input=["hello world", "goodbye world"],
    )
)
print(len(result.data[0].embedding))
```

## Audio (TTS, STT, voices)

```python
from meshapi import SpeechParams, TranscriptionParams, ListVoicesParams

# Text-to-speech — returns raw audio bytes
audio_bytes = client.audio.synthesize(
    SpeechParams(
        input="Hello from MeshAPI.",
        model="sarvam/bulbul:v2",
        voice="meera",
    )
)
with open("output.wav", "wb") as f:
    f.write(audio_bytes)

# Speech-to-text — submit transcription job
result = client.audio.transcribe(
    TranscriptionParams(
        model="sarvam/saaras:v3",
        file=open("audio.wav", "rb").read(),
        file_name="audio.wav",
        language="en",
    )
)
print(result.text)

# Translate audio to English
translated = client.audio.translate(
    TranscriptionParams(
        model="sarvam/saaras:v3",
        file=open("audio.wav", "rb").read(),
        file_name="audio.wav",
    )
)
print(translated.text)

# List available voices
voices = client.audio.list_voices(ListVoicesParams(page_size=10))

# Get a specific voice
voice = client.audio.get_voice("voice-id")
```

### Async audio

```python
audio_bytes = await client.audio.synthesize(SpeechParams(input="Hello!", model="sarvam/bulbul:v2"))
voices = await client.audio.list_voices(ListVoicesParams())
```

## Video generation

```python
from meshapi import VideoGenerationParams, VideoContentItem, ListVideoGenerationsParams
import time

# Submit a video generation task
task = client.videos.generate(
    VideoGenerationParams(
        model="byteplus/dreamina-seedance-2-0",
        content=[VideoContentItem(type="text", text="A serene mountain lake at sunrise")],
    )
)
print(f"Task ID: {task.id}")

# Poll until complete
while True:
    status = client.videos.retrieve(task.id)
    if status.status in ("succeeded", "failed"):
        break
    time.sleep(5)

# List past generation tasks
listing = client.videos.list(ListVideoGenerationsParams(limit=20))
print(f"{listing.total} total tasks")
```

### Async video

```python
task = await client.videos.generate(VideoGenerationParams(...))
status = await client.videos.retrieve(task.id)
```

## Image generation

```python
from meshapi import ImageGenerationParams

result = client.images.generate(
    ImageGenerationParams(
        model="openai/gpt-image-1",
        prompt="A watercolor of a fox in a snowy forest",
        n=1, size="1024x1024", quality="high", output_format="webp",
    )
)
print(result.data[0].url)
```

## Compare (multi-model fanout)

```python
from meshapi import CompareParams, ChatMessage

for event in client.compare.stream(
    CompareParams(
        models=["openai/gpt-4o-mini", "anthropic/claude-sonnet-4.5"],
        messages=[ChatMessage(role="user", content="Summarise this in one sentence: ...")],
    )
):
    if event.event == "delta":
        print(event.data)
```

## Batches

Batch jobs accept inline requests — no separate file upload step required.

```python
from meshapi import CreateBatchParams, BatchRequestItem

batch = client.batches.create(
    CreateBatchParams(
        requests=[
            BatchRequestItem(
                custom_id="req-1",
                body={"model": "openai/gpt-5-nano",
                      "messages": [{"role": "user", "content": "Say hi."}]},
            ),
            BatchRequestItem(
                custom_id="req-2",
                body={"model": "openai/gpt-5-nano",
                      "messages": [{"role": "user", "content": "Say bye."}]},
            ),
        ],
        metadata={"job": "my-batch"},
    )
)

# Poll
status = client.batches.get(batch.id)
print(status.status)

# Cancel
client.batches.cancel(batch.id)
```

## RAG (Retrieval-Augmented Generation)

Upload files, embed them, and run vector search.

```python
from meshapi import InitUploadRequest, BulkEmbedRequest, SearchRequest
import httpx, time

# 1. Initialise upload — get a signed URL
upload = client.rag.init_upload(
    InitUploadRequest(file_name="handbook.pdf", mime_type="application/pdf")
)

# 2a. PUT file bytes to the signed URL yourself…
httpx.put(upload.signed_url, content=pdf_bytes,
          headers={"Content-Type": "application/pdf"}).raise_for_status()

# 2b. …or use the convenience wrapper that does both steps:
upload = client.rag.upload_file(
    file_name="handbook.pdf",
    mime_type="application/pdf",
    content=pdf_bytes,
)

# 3. Trigger embedding
client.rag.embed(BulkEmbedRequest(file_ids=[upload.file_id]))

# 4. Poll until ready
while True:
    s = client.rag.get(upload.file_id)
    if s.embedding_status == "ready":
        break
    time.sleep(3)

# 5. Search
results = client.rag.search(
    SearchRequest(query="onboarding process", top_k=5)
)
for r in results.results:
    print(f"{r.score:.4f}  {r.text}")

# List files (paginated)
page = client.rag.list(limit=50)
print(f"{page.total} total files")
```

## Realtime (Speech-to-Speech WebSocket)

```python
from meshapi import MeshAPI

client = MeshAPI(base_url="...", token="rsk_...")

# Sync — use as a context manager
with client.realtime.connect(model="openai/gpt-4o-realtime-preview") as session:
    session.send({
        "type": "session.update",
        "session": {"instructions": "You are a helpful assistant."},
    })
    session.send_audio(pcm_bytes)          # binary audio frame

    for msg in session:                    # iterate until connection closes
        print(msg.event["type"])           # "session.created", "response.done", …
        if msg.audio:                      # binary audio frame from server
            process_audio(msg.audio)
        if msg.event and msg.event["type"] == "response.done":
            break

# Async — identical API with await
from meshapi import AsyncMeshAPI

async with AsyncMeshAPI(base_url="...", token="rsk_...") as client:
    async with client.realtime.connect(model="openai/gpt-4o-realtime-preview") as session:
        await session.send({"type": "session.update", "session": {...}})
        async for msg in session:
            print(msg.event["type"])
```

`RealtimeError` is raised for server-sent error envelopes (e.g. `insufficient_quota`, `idle_timeout`). Requires `websockets>=12.0` (included as a dependency).

## Models

```python
all_models = client.models.list()
free = client.models.free()
paid = client.models.paid()
```

## Prompt templates

```python
from meshapi import CreateTemplateParams, UpdateTemplateParams

client.templates.create(
    CreateTemplateParams(
        name="support-agent",
        system="You are a support agent for {{company}}. Be concise and friendly.",
        model="openai/gpt-4o-mini",
        variables=["company"],
    )
)

# Use via chat
reply = client.chat.completions.create(
    ChatCompletionParams(
        messages=[ChatMessage(role="user", content="How do I reset my password?")],
        template="support-agent",
        variables={"company": "Acme Corp"},
    )
)

# CRUD
templates = client.templates.list()
client.templates.update(template_id, UpdateTemplateParams(model="openai/gpt-4o"))
client.templates.delete(template_id)
```

## Error handling

```python
from meshapi import MeshAPIError

try:
    client.chat.completions.create(params)
except MeshAPIError as e:
    print(f"[{e.status}] {e.error_code}: {e}")
    print("Request ID:", e.request_id)
    if e.error_code == "rate_limit_exceeded":
        print(f"Retry after {e.retry_after_seconds}s")
```

| Code | HTTP | Meaning |
|---|---|---|
| `unauthorized` | 401 | Invalid or missing key |
| `forbidden` | 403 | Key suspended |
| `not_found` / `model_not_found` | 404 | Resource or model not found |
| `spend_limit_exceeded` | 402 | Account balance at zero |
| `validation_error` | 422 | Bad request body |
| `rate_limit_exceeded` | 429 | RPM or RPD limit hit |
| `upstream_error` | 500 | Upstream or server error |
| `stream_interrupted` | n/a | Mid-stream connection dropped |

## Retry and backoff

Retries on 429/502/503/504 with exponential backoff (default 3 retries, 500 ms base, 30 s max). **Streams do not retry.**

```python
client = MeshAPI(base_url="...", token="rsk_...", max_retries=5, timeout=30.0)
```

## Type hints

```python
from meshapi import (
    MeshAPI, AsyncMeshAPI, MeshAPIError,
    # chat
    ChatCompletionParams, ChatCompletionResponse, ChatCompletionChunk,
    ChatMessage, Tool, ToolFunction, ToolCall,
    # responses
    ResponsesParams, ResponsesResponse,
    # embeddings
    EmbeddingsParams, EmbeddingsResponse,
    # compare
    CompareParams, CompareStreamEvent,
    # batches
    BatchRequestItem, CreateBatchParams, BatchObject,
    # RAG
    InitUploadRequest, InitUploadResponse, UploadFileParams,
    RagFileStatus, RagFileListResponse,
    BulkEmbedRequest, BulkEmbedResponse,
    SearchRequest, SearchResponse, SearchResult,
    # audio
    SpeechParams, TranscriptionParams, TranscriptionTranslateParams,
    TranscriptionResponse, ListVoicesParams,
    # video
    VideoGenerationParams, VideoContentItem,
    CreateVideoGenerationResponse, VideoTaskResponse, VideoTaskListResponse,
    ListVideoGenerationsParams,
    # models
    ModelInfo, ModelPricing,
    # templates
    CreateTemplateParams, UpdateTemplateParams, TemplateSummary,
)
```

## Versioning

```python
import meshapi
print(meshapi.__version__)  # "0.1.0"
```

## About Mesh API

[Mesh API](https://meshapi.ai) is an AI model gateway that gives you instant access to 300+ LLMs through a single, unified API.

Documentation: [developers.meshapi.ai](https://developers.meshapi.ai)

## License

[MIT](LICENSE)
