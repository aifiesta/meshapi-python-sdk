# Changelog

## [Unreleased]

### API version

- **This release targets MeshAPI version `2026-08`.** Every request now sends
  `X-Mesh-Version: 2026-08`, exported as `meshapi.MESH_API_VERSION`.
- Override per client with `MeshAPI(api_version="2026-09")`, or pass
  `api_version=None` to send no header and be served the gateway's baseline
  (the pre-`0.1.12` behaviour).
- Why it matters: an unpinned client is served whatever the gateway defaults to, so
  it never states which response shape it can parse. Pinning means a future version
  that changes a shape cannot change it underneath this release.

### Fixed

- `ModelPricing` now declares `input_usd_per_unit` / `output_usd_per_unit`. These
  were being **discarded** (`extra="ignore"`), so for models that are not
  token-priced — per-second video, per-image, per-1k-chars — where the per-1M
  fields are null by design, the SDK reported a priced model as having no price.
- `ModelPricing.prompt_usd_per_1k` / `completion_usd_per_1k` are documented as
  retired: the gateway stopped returning them in `v1.0.135`, so they now always
  read `None`. They remain declared for backwards compatibility.

## [0.1.0] — Initial release

- `MeshAPI` (sync) and `AsyncMeshAPI` (async) via httpx
- Chat completions: non-streaming (`create`) and streaming (`stream`)
- Models: `list`, `free`, `paid`
- Templates: `create`, `list`, `get`, `update`, `delete`
- `MeshAPIError` with `status`, `error_code`, `request_id`, `details`, `retry_after_seconds`
- Retry with exponential backoff (default 3 retries, codes 429/502/503/504)
- SSE remainder-buffer parser for robust TCP fragmentation handling
- Streaming fail-fast: no automatic reconnect (documented)
- `X-MeshAPI-SDK: python/0.1.0` header on every request
