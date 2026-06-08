"""Live tests: RAG upload, embed, and vector search."""

from __future__ import annotations

import time

import httpx
import pytest
from meshapi import MeshAPI
from meshapi._types import BulkEmbedRequest, InitUploadRequest, SearchRequest

# Document uploaded in every RAG live test.
# Contains a unique phrase used to verify vector search results.
RAG_TEST_CONTENT = (
    "MeshAPI SDK live test document.\n"
    "This file is used to verify RAG upload, embedding, and vector search.\n"
    'The document contains the unique phrase "meshapi rag livetest py" '
    "so search results are deterministic.\n"
)
MIME_TYPE = "text/plain"
MAX_EMBED_WAIT = 90  # seconds


def _put_file(signed_url: str, content: bytes, mime_type: str) -> None:
    """PUT raw bytes to a signed URL."""
    resp = httpx.put(signed_url, content=content, headers={"Content-Type": mime_type}, timeout=30.0)
    resp.raise_for_status()


def _poll_embedding(client: MeshAPI, file_id: str, max_wait: int = MAX_EMBED_WAIT) -> None:
    """Wait until embedding_status reaches 'ready', fail on 'failed' or timeout."""
    deadline = time.monotonic() + max_wait
    while time.monotonic() < deadline:
        status = client.rag.get(file_id)
        if status.embedding_status == "ready":
            return
        if status.embedding_status == "failed":
            pytest.fail(f"embedding failed for {file_id}: error_code={status.last_error_code!r}")
        time.sleep(3)
    pytest.fail(f"embedding did not reach 'ready' within {max_wait}s for {file_id}")


def _find_file_in_list(client: MeshAPI, file_id: str) -> bool:
    """Paginate through all RAG files until file_id is found or the list is exhausted."""
    page_size = 50
    offset = 0
    while True:
        page = client.rag.list(limit=page_size, offset=offset)
        if any(f.file_id == file_id for f in page.files):
            return True
        if not page.files or offset + len(page.files) >= page.total:
            return False
        offset += len(page.files)


def test_rag_upload_embed_search(client: MeshAPI) -> None:
    file_name = f"py-livetest-{int(time.time())}.txt"
    content = RAG_TEST_CONTENT.encode()

    # ── Step 1: InitUpload (embed=False to test the embed endpoint explicitly) ──
    upload = client.rag.init_upload(
        InitUploadRequest(file_name=file_name, mime_type=MIME_TYPE, embed=False)
    )
    assert upload.file_id, "expected file_id"
    assert upload.signed_url, "expected signed_url"
    print(f"[PASS] rag.init_upload → file_id={upload.file_id!r}")

    # Note: the RAG API has no DELETE endpoint, so uploaded files cannot be
    # cleaned up programmatically. Each test run leaves one file in the account.

    # ── Step 2: PUT file content to signed URL ──
    _put_file(upload.signed_url, content, MIME_TYPE)
    print("[PASS] PUT file content to signed URL")

    # ── Step 3: Poll until upload_status=ready ──
    deadline = time.monotonic() + 30
    upload_ready = False
    while time.monotonic() < deadline:
        s = client.rag.get(upload.file_id)
        if s.upload_status == "ready":
            upload_ready = True
            print(f"[PASS] rag.get → upload_status={s.upload_status!r} embedding_status={s.embedding_status!r}")
            break
        time.sleep(2)
    assert upload_ready, "upload_status did not reach 'ready' within 30s"

    # ── Step 4: Embed ──
    embed_resp = client.rag.embed(BulkEmbedRequest(file_ids=[upload.file_id]))
    assert embed_resp.results, "embed returned no results"
    print(f"[PASS] rag.embed → status={embed_resp.results[0].embedding_status!r}")

    # ── Step 5: Poll until embedding_status=ready ──
    _poll_embedding(client, upload.file_id)
    print(f"[PASS] embedding complete for {upload.file_id!r}")

    # ── Step 6: List — paginate until file is found or all pages exhausted ──
    assert _find_file_in_list(client, upload.file_id), (
        f"uploaded file {upload.file_id!r} not found in list"
    )
    print(f"[PASS] rag.list → uploaded file present")

    # ── Step 7: Search ──
    search_resp = client.rag.search(
        SearchRequest(
            query="summary",
            top_k=5,
            file_ids=[upload.file_id],
        )
    )
    assert search_resp.results, "search returned no results"
    print(
        f"[PASS] rag.search → {len(search_resp.results)} results, "
        f"top score={search_resp.results[0].score:.4f}"
    )
