"""Live tests: stable request options and optional multimodal features."""

from __future__ import annotations

import pytest
from meshapi import (
    MeshAPI,
    BuiltinTool,
    ChatCompletionParams,
    ChatMessage,
    CompareParams,
    ContentPartAudio,
    ContentPartImage,
    ContentPartText,
    EmbeddingsParams,
    ImageDetail,
    ImageOptions,
    InputAudio,
    ResponsesParams,
)


def test_chat_stable_options(client: MeshAPI, model: str) -> None:
    resp = client.chat.completions.create(
        ChatCompletionParams(
            model=model,
            messages=[ChatMessage(role="user", content="Reply with exactly the word: seeded")],
            seed=42,
            temperature=0,
            top_p=1,
            user="python-feature-matrix",
            max_tokens=10,
        )
    )
    assert resp.id, "expected response id"
    assert resp.model, "expected model in response"


@pytest.mark.skip(reason="reasoning.effort not supported by default model; needs a reasoning-capable model")
def test_responses_stable_options(client: MeshAPI, model: str) -> None:
    resp = client.responses.create(
        ResponsesParams(
            model=model,
            input="Say ok",
            reasoning={"effort": "low"},
            response_format={"type": "text"},
            tool_choice="auto",
            max_output_tokens=16,
            user="python-feature-matrix",
        )
    )
    assert resp.id, "expected response id"
    assert resp.status, "expected status field"


def test_embeddings_stable_options(client: MeshAPI, embeddings_model: str) -> None:
    result = client.embeddings.create(
        EmbeddingsParams(
            model=embeddings_model,
            input=["alpha", "beta"],
            user="python-feature-matrix",
        )
    )
    assert len(result.data) == 2, "expected 2 embedding items for 2 inputs"


def test_compare_stable_options(client: MeshAPI, model: str, second_model: str) -> None:
    result = client.compare.create(
        CompareParams(
            models=[model, second_model],
            messages=[ChatMessage(role="user", content="Reply with compare")],
            comparison_instructions="Do not add extra prose.",
            max_tokens=10,
            skip_comparison=True,
        )
    )
    assert len(result.results) == 2


def test_multimodal_image_input(client: MeshAPI, image_url: str | None) -> None:
    if not image_url:
        pytest.skip("set MESHAPI_IMAGE_URL to enable multimodal image test")
    from config import get_env

    resp = client.chat.completions.create(
        ChatCompletionParams(
            model=get_env("MESHAPI_IMAGE_MODEL") or "openai/gpt-4o-mini",
            messages=[
                ChatMessage(
                    role="user",
                    content=[
                        ContentPartText(type="text", text="Describe this image in three words."),
                        ContentPartImage(type="image_url", image_url=ImageDetail(url=image_url)),
                    ],
                )
            ],
            max_tokens=30,
        )
    )
    assert resp.id


def test_multimodal_audio_input(client: MeshAPI, audio_b64: str | None, audio_format: str) -> None:
    if not audio_b64:
        pytest.skip("set MESHAPI_INPUT_AUDIO_B64 to enable audio input test")
    from config import get_env

    resp = client.chat.completions.create(
        ChatCompletionParams(
            model=get_env("MESHAPI_AUDIO_MODEL") or "openai/gpt-4o-mini",
            messages=[
                ChatMessage(
                    role="user",
                    content=[
                        ContentPartText(type="text", text="Transcribe this audio briefly."),
                        ContentPartAudio(
                            type="input_audio",
                            input_audio=InputAudio(data=audio_b64, format=audio_format),
                        ),
                    ],
                )
            ],
            max_tokens=40,
        )
    )
    assert resp.id


def test_multimodal_audio_output(client: MeshAPI, audio_out_model: str | None) -> None:
    if not audio_out_model:
        pytest.skip("set MESHAPI_AUDIO_OUT_MODEL to enable audio output test")

    resp = client.chat.completions.create(
        ChatCompletionParams(
            model=audio_out_model,
            messages=[ChatMessage(role="user", content="Say hello in one sentence.")],
            modalities=["text", "audio"],
            audio={"voice": "alloy", "format": "wav"},  # type: ignore[arg-type]
            max_tokens=40,
        )
    )
    assert resp.id


@pytest.mark.skip(reason="gpt-5.4-image-mini should only be used for image generation endpoint, not chat modality")
def test_multimodal_image_generation(client: MeshAPI, image_gen_model: str | None) -> None:
    resp = client.chat.completions.create(

        ChatCompletionParams(
            model=image_gen_model,
            messages=[ChatMessage(role="user", content="Generate a simple red square icon.")],
            modality="image",
            image=ImageOptions(n=1, size="1024x1024", quality="high"),
            async_mode=False,
            max_tokens=100,
        )
    )
    assert resp.id
