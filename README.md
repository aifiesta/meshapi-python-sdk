# meshapi

Official Python SDK for [Mesh API](https://meshapi.ai), an AI model gateway that gives you instant access to 300+ LLMs through a single OpenAI-compatible API.

Code once with the chat completions signature you already know. Switch between OpenAI, Anthropic, Google, Meta, Mistral, DeepSeek, xAI, Alibaba and the rest by changing a model string. Streaming, tool calling, vision, embeddings, multi-model compare, batch jobs and prompt templates from a single client.

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
| **Streaming + tool calling** | SSE streaming via `Iterator` / `AsyncIterator`, function calling with structured tool definitions, vision and audio content parts. |
| **Reasoning models** | First-class `responses` API with `reasoning.effort` and `max_output_tokens` for o-series and similar models. |
| **Embeddings** | Drop-in OpenAI-compatible embeddings endpoint. |
| **Multi-model compare** | Fire one prompt at N models in parallel and stream their replies side by side. |
| **Batches + Files** | Async bulk inference jobs at discounted rates with file upload, download and lifecycle management. |
| **Prompt templates** | Server-stored prompts with `{{variable}}` slots. Update prompts without redeploying. |
| **Provider fallbacks** | If a provider experiences downtime, the gateway falls back to another supported model so your inference stays up. |
| **Built-in rate limiting** | Per-key RPM and RPD limits to prevent runaway costs. HTTP 429 with `retry_after` surfaced as `MeshAPIError.retry_after_seconds`. |
| **Unified billing** | One account balance covers every model. No juggling subscriptions. |
| **Structured errors** | `MeshAPIError` with `error_code`, `status`, `request_id`, `retry_after_seconds`, and provider error details. |
| **Type-safe** | Every request and response is a Pydantic v2 model. Autocomplete in your editor, validation at the boundary. |

## Authentication

The SDK requires a Mesh API key (prefixed with `rsk_`) for all requests. You can obtain a key at [meshapi.ai](https://meshapi.ai).

```python
client = MeshAPI(base_url="https://api.meshapi.ai", token="rsk_...")
```

This key provides access to all resources: `chat`, `responses`, `embeddings`, `compare`, `files`, `batches`, `models`, and `templates`.

## Chat completions

```python
from meshapi import MeshAPI, ChatCompletionParams, ChatMessage

client = MeshAPI(base_url="https://api.meshapi.ai", token="rsk_...")

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
print(f"Tokens: {reply.usage.total_tokens}")
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

`stream()` is a separate method from `create()`. It returns an iterator (sync) or async iterator (async) of chunks.

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

Async streaming:

```python
async for chunk in client.chat.completions.stream(params):
    if chunk.choices and chunk.choices[0].delta:
        print(chunk.choices[0].delta.content or "", end="", flush=True)
```

### Tool calling

```python
from meshapi import ChatCompletionParams, ChatMessage, Tool, ToolFunction

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

for chunk in client.chat.completions.stream(params):
    delta = chunk.choices[0].delta if chunk.choices else None
    if delta and delta.tool_calls:
        print("tool call:", delta.tool_calls)
    elif delta and delta.content:
        print(delta.content, end="", flush=True)
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

print(reply.output)
```

Streaming works the same way via `client.responses.stream(params)`.

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

## Image Generation

```python
from meshapi import ImageGenerationParams

result = client.images.generate(
    ImageGenerationParams(
        model="openai/dall-e-3",
        prompt="A cute baby sea otter",
        n=1,
        size="1024x1024",
    )
)

print(result.data[0].url)

# Streaming (Keep-alive pseudo-streaming)
for chunk in client.images.stream(
    ImageGenerationParams(
        model="openai/dall-e-3",
        prompt="A cute baby sea otter",
        n=1,
        size="1024x1024",
    )
):
    if chunk.status == "processing":
        print("Generating...")
    elif chunk.data:
        print("Done:", chunk.data[0].url)

```

## Compare (multi-model fanout)

Fire one prompt at several models and stream their replies in parallel.

```python
from meshapi import CompareParams, ChatMessage

stream = client.compare.stream(
    CompareParams(
        models=[
            "openai/gpt-4o-mini",
            "anthropic/claude-sonnet-4.5",
            "google/gemini-2.5-flash",
        ],
        messages=[ChatMessage(role="user", content="Summarize this paragraph in one sentence: ...")],
        stream=True,
    )
)

for event in stream:
    if event.event == "delta":
        print(event.data)
```

Use `client.compare.create(params)` for a non-streaming side-by-side response with an optional judge-model comparison via `comparison_model`.

## Files and Batches

Upload a list of requests, kick off a batch, poll until done. Batch jobs run at discounted pricing.

```python
from meshapi import (
    UploadBatchFileParams,
    BatchRequestItem,
    CreateBatchParams,
)

# 1. Upload the batch input
file = client.files.upload(
    UploadBatchFileParams(
        purpose="batch",
        requests=[
            BatchRequestItem(
                custom_id="req-1",
                body={
                    "model": "openai/gpt-4o-mini",
                    "messages": [{"role": "user", "content": "Say hi."}],
                },
            ),
            BatchRequestItem(
                custom_id="req-2",
                body={
                    "model": "openai/gpt-4o-mini",
                    "messages": [{"role": "user", "content": "Say bye."}],
                },
            ),
        ],
    )
)

# 2. Create the batch
batch = client.batches.create(
    CreateBatchParams(
        input_file_id=file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
    )
)

# 3. Poll later
status = client.batches.get(batch.id)
if status.status == "completed" and status.output_file_id:
    output_bytes = client.files.content(status.output_file_id)
    # output_bytes is JSONL
```

## Models

```python
all_models = client.models.list()
free = client.models.free()
paid = client.models.paid()

for m in paid[:5]:
    print(
        f"{m.id}: prompt ${m.pricing.prompt_usd_per_1k}/1k, "
        f"completion ${m.pricing.completion_usd_per_1k}/1k"
    )
```

Free models (`is_free=True`) cost $0 for both prompt and completion, useful for testing and light tasks. Paid models charge per token against your account balance.

## Prompt templates

Server-stored prompts with `{{variable}}` interpolation. Reference them by name from `chat.completions` to skip re-sending system prompts every request.

```python
from meshapi import MeshAPI, CreateTemplateParams, ChatCompletionParams, ChatMessage

# Manage templates with either a data-plane key or control-plane JWT
client = MeshAPI(base_url="https://api.meshapi.ai", token="rsk_...")

client.templates.create(
    CreateTemplateParams(
        name="support-agent",
        system="You are a support agent for {{company}}. Be concise and friendly.",
        model="openai/gpt-4o-mini",
        variables=["company"],
    )
)

reply = client.chat.completions.create(
    ChatCompletionParams(
        messages=[ChatMessage(role="user", content="How do I reset my password?")],
        template="support-agent",
        variables={"company": "Acme Corp"},
    )
)
```

CRUD:

```python
from meshapi import UpdateTemplateParams

templates = ctrl.templates.list()
t = ctrl.templates.get(template_id)
ctrl.templates.update(template_id, UpdateTemplateParams(model="openai/gpt-4o"))
ctrl.templates.delete(template_id)
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
    elif e.error_code == "spend_limit_exceeded":
        print("Account balance exhausted. Top up to continue.")
    elif e.error_code == "unauthorized":
        print("Invalid API key.")
    elif e.error_code == "model_not_found":
        print("Model not supported.")
    elif e.error_code == "upstream_error":
        print("Provider error:", e.provider_error)
    elif e.error_code == "validation_error":
        print("Invalid request:", e.details)
```

| Code | HTTP | Meaning |
|---|---|---|
| `unauthorized` | 401 | Invalid or missing key |
| `forbidden` | 403 | Key suspended |
| `not_found` / `model_not_found` | 404 | Resource or model not found |
| `spend_limit_exceeded` | 402 | Account balance at zero. Top up to continue. |
| `validation_error` / `unprocessable_entity` | 422 | Bad request body |
| `rate_limit_exceeded` | 429 | RPM or RPD limit hit |
| `upstream_error` / `gateway_timeout` / `internal_error` | 500 | Upstream or server error |
| `parse_error` | n/a | SDK could not parse response body |
| `stream_interrupted` | n/a | Mid-stream connection dropped |

Mid-stream errors (sent as SSE frames before `[DONE]`) raise the same `MeshAPIError` from inside the iterator.

## Retry and backoff

The client automatically retries `GET` and non-streaming `POST` / `PATCH` requests on status codes `429`, `502`, `503`, `504` with exponential backoff (default: 3 retries, base delay 500 ms, max 30 s, with jitter). The `Retry-After` header is respected on 429 responses.

```python
client = MeshAPI(
    base_url="https://api.meshapi.ai",
    token="rsk_...",
    max_retries=5,   # 0 to disable
    timeout=30.0,
)
```

## Streaming failure recovery

**Streams do not retry.** If a connection drops mid-stream, a `MeshAPIError` with `error_code="stream_interrupted"` is raised. Catch it and restart a new request:

```python
try:
    for chunk in client.chat.completions.stream(params):
        process(chunk)
except MeshAPIError as e:
    if e.error_code == "stream_interrupted":
        # restart from scratch
        ...
```

## Type hints

Every request and response is a Pydantic v2 model. Import what you need:

```python
from meshapi import (
    MeshAPI,
    AsyncMeshAPI,
    MeshAPIConfig,
    MeshAPIError,
    # chat
    ChatCompletionParams,
    ChatCompletionResponse,
    ChatCompletionChunk,
    ChatMessage,
    Tool,
    ToolFunction,
    ToolCall,
    # responses
    ResponsesParams,
    ResponsesResponse,
    # embeddings
    EmbeddingsParams,
    EmbeddingsResponse,
    # compare
    CompareParams,
    CompareStreamEvent,
    # batches + files
    UploadBatchFileParams,
    BatchRequestItem,
    CreateBatchParams,
    BatchObject,
    FileObject,
    # models
    ModelInfo,
    ModelPricing,
    # templates
    CreateTemplateParams,
    UpdateTemplateParams,
    TemplateSummary,
)
```

## Versioning

This SDK follows [SemVer 2.0](https://semver.org/). Pre-1.0 releases may have breaking changes between minor versions.

```python
import meshapi
print(meshapi.__version__)  # "0.1.0"
```

## About Mesh API

[Mesh API](https://meshapi.ai) is an AI model gateway that gives you instant access to a massive variety of LLMs through a single, unified API. Enjoy the developer experience you already know, upgraded with universal model access.

| | |
|---|---|
| **One Universal API** | A single `chat.completions.create` request works across 300+ base models. |
| **Unified Billing** | Deposit funds into one account and consume any model. No juggling provider subscriptions. |
| **Free Tier** | Free models (`is_free=True`) cost $0 for both prompt and completion. Test and ship light workloads without funding. |
| **Provider Fallbacks** | If a model or provider goes down, the gateway routes to another supported model so your inference stays up. |
| **Built-in Rate Limiting** | Robust per-key limits prevent runaway costs. |
| **Prompt Templates** | Manage, version and share prompts via a secure templating system. |

Documentation lives at [developers.meshapi.ai](https://developers.meshapi.ai).

Built by the founders of [TagMango](https://tagmango.com) (YC W20) and [AI Fiesta](https://aifiesta.ai) (1M+ users).

## Related

- [`meshapi-node-sdk`](https://github.com/aifiesta/meshapi-node-sdk): official TypeScript SDK with the same surface
- [`meshapi-code`](https://github.com/aifiesta/meshapi-code): terminal chat REPL with tool calling

## License

[MIT](LICENSE)
