# Changelog

## [0.1.0] — Initial release

- `MeshAPI` (sync) and `AsyncMeshAPI` (async) via httpx
- Chat completions: non-streaming (`create`) and streaming (`stream`)
- Models: `list`, `free`, `paid`
- Templates: `create`, `list`, `get`, `update`, `delete`
- `RouterSvcApiError` with `status`, `error_code`, `request_id`, `details`, `retry_after_seconds`
- Retry with exponential backoff (default 3 retries, codes 429/502/503/504)
- SSE remainder-buffer parser for robust TCP fragmentation handling
- Streaming fail-fast: no automatic reconnect (documented)
- `X-RouterSVC-SDK: python/0.1.0` header on every request
