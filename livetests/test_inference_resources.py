"""Live tests: embeddings, responses, compare, files, and batches."""

from __future__ import annotations

import time

import pytest

from meshapi import (
    MeshAPI,
    BatchRequestItem,
    ChatMessage,
    CompareParams,
    CreateBatchParams,
    EmbeddingsParams,
    ResponsesParams,
    UploadBatchFileParams,
)


def _batch_requests(tag: str, model: str) -> list[BatchRequestItem]:
    return [
        BatchRequestItem(
            custom_id=f"{tag}-1",
            body={
                "model": model,
                "messages": [{"role": "user", "content": "Reply with the single word: hello"}],
                "max_tokens": 16,
            },
        ),
        BatchRequestItem(
            custom_id=f"{tag}-2",
            body={
                "model": model,
                "messages": [{"role": "user", "content": "Reply with the single word: world"}],
                "max_tokens": 16,
            },
        ),
    ]


def test_embeddings_create(client: MeshAPI, embeddings_model: str) -> None:
    result = client.embeddings.create(
        EmbeddingsParams(
            model=embeddings_model,
            input="MeshAPI embeddings smoke test",
        )
    )
    assert result.data, "expected at least one embedding item"
    assert result.model, "expected model field in response"
    assert len(result.data[0].embedding) > 0, "expected non-empty embedding vector"


def test_responses_create(client: MeshAPI, model: str) -> None:
    resp = client.responses.create(
        ResponsesParams(
            model=model,
            input="Reply with exactly the word: ok",
            max_output_tokens=16,
        )
    )
    assert resp.id, "expected response id"
    assert resp.model is not None, "expected model field"


def test_responses_stream(client: MeshAPI, model: str) -> None:
    from meshapi._errors import MeshAPIError
    try:
        events = list(
            client.responses.stream(
                ResponsesParams(
                    model=model,
                    input="Count from 1 to 3.",
                    max_output_tokens=32,
                )
            )
        )
        assert events, "expected at least one streaming event"
    except MeshAPIError as e:
        if e.status == 501:
            pytest.skip(f"Skipping responses stream test: {e}")
        raise



def test_compare_create(client: MeshAPI, model: str, second_model: str) -> None:
    result = client.compare.create(
        CompareParams(
            models=[model, second_model],
            messages=[ChatMessage(role="user", content="Reply with the word: compare")],
            skip_comparison=True,
            max_tokens=16,
        )
    )
    assert len(result.results) == 2, f"expected 2 results, got {len(result.results)}"


@pytest.mark.xfail(reason="server-side SQLAlchemy session concurrency issue when compare tests run back-to-back")
def test_compare_stream(client: MeshAPI, model: str, second_model: str) -> None:
    events = list(
        client.compare.stream(
            CompareParams(
                models=[model, second_model],
                messages=[ChatMessage(role="user", content="Reply with the word: stream")],
                skip_comparison=True,
                max_tokens=16,
            )
        )
    )
    assert events, "expected at least one compare stream event"


@pytest.mark.skip(reason="files/batches endpoint validation mismatch — needs API spec investigation")
def test_files_and_batches_lifecycle(client: MeshAPI, model: str, unique_tag: str) -> None:
    file_tag = f"{unique_tag}-batch"

    uploaded = client.files.upload(
        UploadBatchFileParams(requests=_batch_requests(file_tag, model))
    )
    assert uploaded.id, "expected file id after upload"

    try:
        fetched = client.files.get(uploaded.id)
        assert fetched.id == uploaded.id

        content = client.files.content(uploaded.id)
        assert content, "expected non-empty file content"
        assert f"{file_tag}-1".encode() in content

        batch = client.batches.create(
            CreateBatchParams(
                input_file_id=uploaded.id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
                metadata={"suite": "python-livetest"},
            )
        )
        assert batch.id, "expected batch id"

        batch_list = client.batches.list(limit=10)
        assert any(item.id == batch.id for item in batch_list.data), "created batch not found in list"

        got_batch = client.batches.get(batch.id)
        assert got_batch.id == batch.id

        cancelled = client.batches.cancel(batch.id)
        assert cancelled.id == batch.id

    finally:
        try:
            client.files.delete(uploaded.id)
        except Exception:
            pass


def test_images_generate(client: MeshAPI, image_gen_model: str | None) -> None:
    if not image_gen_model:
        pytest.skip("MESHAPI_IMAGE_GEN_MODEL not set")
        
    from meshapi import ImageGenerationParams
    
    resp = client.images.generate(
        ImageGenerationParams(
            model=image_gen_model,
            prompt="A small blue square on a white background.",
            n=1,
            size="1024x1024",
        )
    )
    assert resp.created, "expected created timestamp"
    assert resp.data, "expected data field"
    assert len(resp.data) == 1, "expected 1 image"
    assert resp.data[0].b64_json or resp.data[0].url, "expected image data"

