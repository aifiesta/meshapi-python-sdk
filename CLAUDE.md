# MeshAPI Python SDK

Official Python client for the MeshAPI AI model gateway.

- **Package**: `meshapi`
- **Python**: 3.9+
- **Runtime dependencies**: `httpx>=0.27`, `pydantic>=2`
- **Build backend**: hatchling

## Project layout

```
python/
├── meshapi/
│   ├── __init__.py        # MeshAPI, AsyncMeshAPI, all public exports
│   ├── _types.py          # All Pydantic request/response models
│   ├── _http.py           # SyncHttpClient / AsyncHttpClient (httpx-based)
│   ├── _errors.py         # MeshAPIError exception
│   └── resources/
│       ├── chat.py        # /v1/chat/completions
│       ├── responses.py   # /v1/responses
│       ├── embeddings.py  # /v1/embeddings
│       ├── compare.py     # /v1/compare
│       ├── files.py       # /v1/files (batch file objects)
│       ├── rag.py         # /v1/files RAG endpoints (upload, embed, search)
│       ├── batches.py     # /v1/batches
│       ├── models.py      # /v1/models
│       ├── templates.py   # /v1/templates
│       └── images.py      # /v1/images/generations
├── tests/
│   ├── unit/              # Fast, no-network tests
│   ├── contract/          # Pydantic model parsing against local fixtures
│   └── integration/       # Full-stack tests against a running backend
├── livetests/             # Live tests against a real backend
└── pyproject.toml
```

## Common tasks

### Set up development environment

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Unit and contract tests (no network)

```bash
pytest tests/unit/ tests/contract/ -v
```

### Integration tests (requires a running backend)

```bash
MESHAPI_BASE_URL=http://localhost:8000 MESHAPI_TOKEN=rsk_... pytest tests/integration/ -v
```

### Adding a new resource

1. Add Pydantic models to `_types.py` under a clearly labelled section.
2. Create `resources/<name>.py` with `<Name>Resource` and `Async<Name>Resource` classes.
3. Both classes take their respective `SyncHttpClient` / `AsyncHttpClient` in `__init__`.
4. Wire the resource into both `MeshAPI` and `AsyncMeshAPI` in `__init__.py`.
5. Import the new types and resource classes in `__init__.py` and add them to `__all__`.
6. Follow the pattern in `resources/templates.py`.

---

## Live tests

Live tests hit a real MeshAPI backend and live in `livetests/`. They use pytest with a shared `client` fixture from `conftest.py`.

### Prerequisites

- A running MeshAPI instance (default `http://localhost:8000`), **or** point at the dev API.
- A valid data-plane API key (`rsk_...`).

### Environment variables

Create `python/.env.livetest` (read automatically by the test harness) or export the variables in your shell before running tests.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MESHAPI_BASE_URL` | No | `http://localhost:8000` | Base URL of the MeshAPI gateway |
| `MESHAPI_TOKEN` | **Yes** | hardcoded dev key | Data-plane API key (`rsk_...`) |
| `MESHAPI_MODEL` | No | `openai/gpt-4o-mini` | Primary model used in chat/stream tests |
| `MESHAPI_SECOND_MODEL` | No | `anthropic/claude-haiku-4.5` | Second model for compare tests |
| `MESHAPI_EMBEDDINGS_MODEL` | No | `openai/text-embedding-3-small` | Model used in embeddings tests |
| `MESHAPI_IMAGE_GEN_MODEL` | No | _(skipped if unset)_ | Image generation model; test skipped if blank |
| `MESHAPI_IMAGE_URL` | No | _(skipped if unset)_ | Publicly accessible image URL for vision tests |
| `MESHAPI_INPUT_AUDIO_B64` | No | _(skipped if unset)_ | Base64-encoded audio for audio-input tests |
| `MESHAPI_INPUT_AUDIO_FORMAT` | No | `wav` | Format of the base64 audio (`wav`, `mp3`, etc.) |
| `MESHAPI_AUDIO_OUT_MODEL` | No | _(skipped if unset)_ | Model for audio-output tests; skipped if blank |
| `MESHAPI_REALTIME_MODEL` | No | `openai/gpt-realtime-mini` | Realtime-capable model used in WebSocket live tests |

Example `python/.env.livetest`:

```env
MESHAPI_BASE_URL=https://api-dev.meshapi.ai
MESHAPI_TOKEN=rsk_your_key_here
MESHAPI_MODEL=openai/gpt-4o-mini
MESHAPI_EMBEDDINGS_MODEL=openai/text-embedding-3-small
```

### Install dependencies

```bash
# From the python/ directory
pip install -e ".[dev]"
pip install httpx   # required by the RAG live test for direct signed-URL PUT
```

### Run all live tests

```bash
cd livetests
pytest -v
```

### Run a single live test file

```bash
cd livetests
pytest test_rag.py -v
```

### Run a specific test function

```bash
cd livetests
pytest test_rag.py::test_rag_upload_embed_search -v
```

### Available live test files

| File | What it tests |
|------|---------------|
| `test_chat.py` | Chat completions (basic, tools, multi-turn) |
| `test_stream.py` | Streaming chat and responses |
| `test_models.py` | Model listing |
| `test_templates.py` | Template CRUD lifecycle |
| `test_inference_resources.py` | Embeddings, responses |
| `test_errors.py` | 401/404 error handling |
| `test_feature_matrix.py` | Cross-model feature matrix |
| `test_rag.py` | RAG upload → embed → list → search |
| `test_realtime.py` | WebSocket connect/close, session.created, session.update, error envelopes, iterator API, async variants |

### RAG live test notes

`test_rag_upload_embed_search` does the following:
1. Calls `client.rag.init_upload` with `embed=False`.
2. PUTs the file bytes directly to the returned `signed_url` via `httpx.put`.
3. Waits up to 30 s for `upload_status=ready`.
4. Calls `client.rag.embed` to trigger embedding.
5. Polls up to 90 s for `embedding_status=ready`.
6. Calls `client.rag.list` and asserts the file appears.
7. Calls `client.rag.search` scoped to the file ID and asserts non-empty results.
