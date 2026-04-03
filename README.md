# routersvc-python-sdk

Python SDK for the RouterSVC AI model gateway.

## Requirements

- Python ≥ 3.9
- `httpx` ≥ 0.27
- `pydantic` ≥ 2.0

## Installation

```bash
pip install routersvc-python-sdk
# or from source:
pip install -e ".[dev]"
```

## Quick Start

### Sync client

```python
from routersvc import MeshAPI, ChatCompletionParams, ChatMessage

client = MeshAPI(base_url="http://localhost:8000", token="rsk_...")

# Non-streaming
resp = client.chat.completions.create(
    ChatCompletionParams(
        model="openai/gpt-4o-mini",
        messages=[ChatMessage(role="user", content="What is 2+2?")],
    )
)
print(resp.choices[0].message.content)  # "4"

# Streaming
for chunk in client.chat.completions.stream(
    ChatCompletionParams(
        model="openai/gpt-4o-mini",
        messages=[ChatMessage(role="user", content="Count to 5.")],
    )
):
    if chunk.choices and chunk.choices[0].delta:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### Async client

```python
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

asyncio.run(main())
```

### Models

```python
models = client.models.list()           # all models
free   = client.models.free()           # free-tier only
paid   = client.models.paid()           # paid-tier only
filtered = client.models.list(free=True)
```

### Templates

```python
from routersvc import CreateTemplateParams, UpdateTemplateParams

tmpl = client.templates.create(CreateTemplateParams(
    name="my-assistant",
    system="You are a helpful assistant.",
))
print(tmpl.id)

templates = client.templates.list()
tmpl = client.templates.get(tmpl.id)
tmpl = client.templates.update(tmpl.id, UpdateTemplateParams(description="Updated"))
client.templates.delete(tmpl.id)
```

## Error Handling

```python
from routersvc import RouterSvcApiError

try:
    resp = client.chat.completions.create(...)
except RouterSvcApiError as e:
    print(e.status)            # HTTP status code (0 for stream errors)
    print(e.error_code)        # "unauthorized", "rate_limit_exceeded", etc.
    print(e.request_id)        # req_<ULID> for support tracing
    print(e.retry_after_seconds)  # set on 429 responses
```

## Retry / Backoff

The client automatically retries `GET` and non-streaming `POST`/`PATCH` requests on
status codes `429`, `502`, `503`, `504` with exponential backoff (default: 3 retries,
base delay 500 ms, max 30 s, ±20% jitter). The `Retry-After` header is respected on
429 responses.

Configure via constructor:

```python
client = MeshAPI(
    base_url="...",
    token="...",
    max_retries=5,    # 0 to disable
    timeout=30.0,
)
```

## Streaming Failure Recovery

**Streams do not retry.** If a connection drops mid-stream, a `RouterSvcApiError`
with `error_code="stream_interrupted"` is raised. Catch it and restart a new request:

```python
try:
    for chunk in client.chat.completions.stream(params):
        process(chunk)
except RouterSvcApiError as e:
    if e.error_code == "stream_interrupted":
        # restart from scratch
        ...
```

## Auth Strategy

One client instance = one auth realm.

```python
# Inference (rsk_ key)
inference_client = MeshAPI(base_url=BASE_URL, token="rsk_...")

# Template management (Supabase JWT)
mgmt_client = MeshAPI(base_url=BASE_URL, token="<jwt>")
```

## Running Tests

```bash
# Unit + contract tests (no server needed)
pytest tests/unit/ tests/contract/ -v

# Integration tests (requires localhost:8000)
ROUTERSVC_BASE_URL=http://localhost:8000 \
ROUTERSVC_TOKEN=rsk_... \
pytest tests/integration/ -v

# Build wheel (tests excluded)
pip install build
python -m build
```

## Versioning

This SDK follows [SemVer 2.0](https://semver.org/). Pre-1.0 releases may have
breaking changes between minor versions.

```python
import routersvc
print(routersvc.__version__)  # "0.1.0"
```
