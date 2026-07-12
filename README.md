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
| **Moderations** | Classify text/image content for policy violations via `moderations.create`. |
| **Web search** | Live web search with native + Tavily engines via `web.search`. |
| **Router select** | Ask the Auto Router which model it would pick, without running inference. |
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

## Structured outputs

Constrain the model to a JSON schema and get a parsed, typed result back.
Pass a Pydantic model, a `TypedDict`/dataclass, or a raw JSON-schema `dict`.

```python
from pydantic import BaseModel
from meshapi import MeshAPI, ChatCompletionParams, ChatMessage

class Country(BaseModel):
    country: str
    capital: str
    population_millions: float

client = MeshAPI(base_url="https://api.meshapi.ai", token="rsk_...")

country = client.chat.completions.parse(
    ChatCompletionParams(
        model="openai/gpt-4o-mini",
        messages=[ChatMessage(role="user", content="Give me structured facts about France.")],
    ),
    response_format=Country,
)
print(country.capital, country.population_millions)  # typed, with IDE autocomplete
```

`parse()` returns the parsed object directly:

| `response_format` | Returns |
|---|---|
| Pydantic `BaseModel` subclass | an instance of that model |
| `TypedDict` / dataclass | the validated object |
| raw JSON-schema `dict` | the parsed JSON value — a `dict`, `list`, or scalar (`json.loads`, unvalidated) |

> **Python < 3.12 and `TypedDict`:** import it from `typing_extensions`
> (`from typing_extensions import TypedDict`), not `typing`. pydantic cannot
> build a schema from stdlib `typing.TypedDict` before 3.12, so `parse()` will
> raise a `TypeError` pointing you here.

### Auto-retry on validation failure (opt-in)

Some providers only best-effort the schema. Set `max_retries` to feed a failed
response back to the model with the validation error appended. Each retry is a
billed call; the default is `0` (no retry).

```python
country = client.chat.completions.parse(params, Country, max_retries=3)
```

`parse()` is non-streaming. Use `create()` when you need the raw string content
plus `usage`/cost metadata. `AsyncMeshAPI` exposes the same `await client.chat.completions.parse(...)`.

### When the model doesn't support structured output

If parsing fails after any retries, `parse()` raises `StructuredOutputError`
(a `MeshAPIError` subclass; the underlying `pydantic.ValidationError` /
`json.JSONDecodeError` is on `__cause__`). When the model returned plain text
instead of JSON — usually because it doesn't support `response_format` — the
message points you at the model's structured-output support:

```python
from meshapi import StructuredOutputError

try:
    country = client.chat.completions.parse(params, Country)
except StructuredOutputError as e:
    print(e)  # "... the model returned text that is not valid JSON ... Check
              #  the model's support on the Models page (https://app.meshapi.ai/...)"
```

Check a model's `supports_structured_output` flag via `GET /v1/models`, or on the
Models page in your dashboard.

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

# List background response jobs, or fetch a persisted/background response by id.
# Synchronous create responses are not guaranteed to be retrievable via get().
jobs = client.responses.list(limit=20)
job = client.responses.get("resp_abc123")
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
from meshapi import (
    AudioTranslationsParams,
    ListVoicesParams,
    SpeechParams,
    TranscriptionParams,
)

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

# Speech-to-text — send raw audio bytes with a filename hint
with open("audio.wav", "rb") as f:
    file_bytes = f.read()

result = client.audio.transcribe(
    file_bytes,
    TranscriptionParams(
        model="sarvam/saaras:v3",
        # Optional: language_code is model-specific (e.g. Sarvam expects "en-IN", not "en").
    ),
    filename="audio.wav",
)
print(result.text)

# Translate audio directly to English
translated = client.audio.audio_translate(
    file_bytes,
    AudioTranslationsParams(model="openai/whisper-large-v3"),
    filename="audio.wav",
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

### Editing an image

`image` (and optional `mask` / `reference_images`) take a base64 or
`data:` URL — remote http(s) URLs are rejected by this endpoint.

```python
from meshapi import ImageEditParams

edited = client.images.edit(
    ImageEditParams(
        model="openai/gpt-image-1",
        image="data:image/png;base64,<...>",
        prompt="Replace the background with a beach at sunset",
        operation="edit",  # or inpaint / outpaint / mix / reframe / upscale / remove_background
    )
)
print(edited.data[0].url or edited.data[0].b64_json[:32])
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
with client.realtime.connect(model="openai/gpt-realtime-mini") as session:
    session.send({
        "type": "session.update",
        "session": {
            "type": "realtime",
            "output_modalities": ["audio"],
            "instructions": "You are a helpful assistant.",
            "audio": {
                "input": {"format": {"type": "audio/pcm", "rate": 24000}},
                "output": {"format": {"type": "audio/pcm", "rate": 24000}, "voice": "alloy"},
            },
        },
    })
    session.send_audio(pcm_bytes)          # PCM16 24kHz; sent as base64 input_audio_buffer.append

    for msg in session:                    # iterate until connection closes
        if msg.audio:                      # decoded from response.output_audio.delta
            process_audio(msg.audio)
        elif msg.event and msg.event["type"] == "response.done":
            break

# Async — identical API with await
from meshapi import AsyncMeshAPI

async with AsyncMeshAPI(base_url="...", token="rsk_...") as client:
    async with client.realtime.connect(model="openai/gpt-realtime-mini") as session:
        await session.send({"type": "session.update", "session": {"type": "realtime", "output_modalities": ["text"]}})
        async for msg in session:
            print(msg.event["type"])
```

`RealtimeError` is raised for server-sent error envelopes (e.g. `insufficient_quota`, `idle_timeout`). Requires `websockets>=12.0` (included as a dependency).

## Models

```python
from meshapi import ModelSearchParams

all_models = client.models.list()
free = client.models.free()
paid = client.models.paid()

# Paginated catalog search (DB-only, no model cost)
page = client.models.search(ModelSearchParams(q="gpt", free=False, sort="name", limit=10))
print(page.total, page.brands)

# Fetch one model's detail
gpt4o = client.models.get("openai/gpt-4o")
```

## Moderations

```python
from meshapi import ModerationParams

result = client.moderations.create(ModerationParams(input="text to classify"))
if result.results[0].flagged:
    print("flagged:", result.results[0].categories)

# Batch several inputs in one call
client.moderations.create(ModerationParams(input=["first text", "second text"]))
```

## Web search

Gated server-side by `WEB_SEARCH_ENABLED`. Native-first with Tavily fallback;
inspect `response.provider` to see which engine served the request.

```python
from meshapi import WebSearchParams

res = client.web.search(
    WebSearchParams(query="latest news on Mars rovers", max_results=5, include_answer=True)
)
print(res.provider, res.answer)
for hit in res.results:
    print(hit.title, hit.url)
```

## Router select

Gated server-side by `AUTO_ROUTER_ENABLED`. Returns the model the Auto Router
*would* pick — without running inference — so you can run it on your own path.

```python
from meshapi import RouterSelectParams, ChatMessage

sel = client.router.select(
    RouterSelectParams(messages=[ChatMessage(role="user", content="Prove that 2+2=4.")])
)
print(sel.model, sel.auto_router.fallback_used)
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
    SpeechParams, TranscriptionParams, AudioTranslationsParams,
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
print(meshapi.__version__)  # "0.1.11"
```

## About Mesh API

[Mesh API](https://meshapi.ai) is an AI model gateway that gives you instant access to 300+ LLMs through a single, unified API.

Documentation: [developers.meshapi.ai](https://developers.meshapi.ai)

## License

[MIT](LICENSE)
