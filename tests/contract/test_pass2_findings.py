"""Contract tests for second-pass audit findings.

Covers:
  - A: POST /v1/audio/translations — new AudioTranslationsParams + audio_translate() method
  - B: ResponsesParams missing ~9 spec fields (+ plugins)
  - C: ChatCompletionParams missing cache, transforms, reasoning_effort
  - D: CreateTemplateParams missing team_id
"""

from unittest.mock import MagicMock

import pytest

from meshapi._types import (
    AudioTranslationsParams,
    ChatCompletionParams,
    ChatMessage,
    CreateTemplateParams,
    ResponsesParams,
    TranscriptionResponse,
)


# ---------------------------------------------------------------------------
# A. POST /v1/audio/translations — AudioTranslationsParams + audio_translate()
# ---------------------------------------------------------------------------


def test_audio_translations_params_required_model():
    params = AudioTranslationsParams(model="openai/whisper-1")
    assert params.model == "openai/whisper-1"
    assert params.prompt is None
    assert params.response_format is None
    assert params.temperature is None


def test_audio_translations_params_all_fields():
    params = AudioTranslationsParams(
        model="openai/whisper-1",
        prompt="Translate this audio",
        response_format="json",
        temperature=0.5,
    )
    dumped = params.model_dump(exclude_none=True)
    assert dumped["model"] == "openai/whisper-1"
    assert dumped["prompt"] == "Translate this audio"
    assert dumped["response_format"] == "json"
    assert dumped["temperature"] == 0.5


def test_audio_translations_params_temperature_bounds():
    """Temperature must be in [0, 2]."""
    with pytest.raises(Exception):
        AudioTranslationsParams(model="openai/whisper-1", temperature=3.0)


def test_audio_resource_has_audio_translate():
    from meshapi.resources.audio import AudioResource
    assert hasattr(AudioResource, "audio_translate")


def test_async_audio_resource_has_audio_translate():
    from meshapi.resources.audio import AsyncAudioResource
    assert hasattr(AsyncAudioResource, "audio_translate")


def test_audio_translate_calls_correct_endpoint():
    from meshapi.resources.audio import AudioResource

    mock_http = MagicMock()
    mock_http.post_multipart.return_value = {"text": "Hello world"}
    resource = AudioResource(mock_http)

    params = AudioTranslationsParams(model="openai/whisper-1")
    file_bytes = b"fake_audio_bytes"
    result = resource.audio_translate(file_bytes, params)

    mock_http.post_multipart.assert_called_once()
    call_args = mock_http.post_multipart.call_args
    # First positional arg is the path
    assert call_args[0][0] == "/v1/audio/translations"
    assert isinstance(result, TranscriptionResponse)
    assert result.text == "Hello world"


def test_audio_translate_uses_model_field():
    from meshapi.resources.audio import AudioResource

    mock_http = MagicMock()
    mock_http.post_multipart.return_value = {"text": "Translated text"}
    resource = AudioResource(mock_http)

    params = AudioTranslationsParams(model="openai/whisper-1", prompt="Context hint")
    resource.audio_translate(b"bytes", params)

    call_kwargs = mock_http.post_multipart.call_args
    fields = call_kwargs[0][1]
    assert fields.get("model") == "openai/whisper-1"
    assert fields.get("prompt") == "Context hint"


def test_audio_translate_distinct_from_translate():
    """audio_translate() must post to /v1/audio/translations,
    not /v1/audio/transcriptions/translate."""
    from meshapi.resources.audio import AudioResource

    mock_http = MagicMock()
    mock_http.post_multipart.return_value = {"text": "out"}
    resource = AudioResource(mock_http)

    resource.audio_translate(b"data", AudioTranslationsParams(model="openai/whisper-1"))
    path = mock_http.post_multipart.call_args[0][0]
    assert path == "/v1/audio/translations"
    assert "transcriptions" not in path


def test_audio_translations_params_exported():
    import meshapi
    assert "AudioTranslationsParams" in meshapi.__all__
    assert hasattr(meshapi, "AudioTranslationsParams")


# ---------------------------------------------------------------------------
# B. ResponsesParams missing fields
# ---------------------------------------------------------------------------


def test_responses_params_new_fields_present():
    params = ResponsesParams(
        input="Hello",
        previous_response_id="resp_abc",
        instructions="Be concise",
        thinking={"enabled": True},
        caching={"ttl": 300},
        store=True,
        include=["citations"],
        expire_at=1700000000,
        max_tool_calls=5,
        context_management={"strategy": "truncate"},
        plugins=[{"type": "web_search"}],
    )
    dumped = params.model_dump(exclude_none=True)
    assert dumped["previous_response_id"] == "resp_abc"
    assert dumped["instructions"] == "Be concise"
    assert dumped["thinking"] == {"enabled": True}
    assert dumped["caching"] == {"ttl": 300}
    assert dumped["store"] is True
    assert dumped["include"] == ["citations"]
    assert dumped["expire_at"] == 1700000000
    assert dumped["max_tool_calls"] == 5
    assert dumped["context_management"] == {"strategy": "truncate"}
    assert dumped["plugins"] == [{"type": "web_search"}]


def test_responses_params_new_fields_default_to_none():
    params = ResponsesParams(input="test")
    assert params.previous_response_id is None
    assert params.instructions is None
    assert params.thinking is None
    assert params.caching is None
    assert params.store is None
    assert params.include is None
    assert params.expire_at is None
    assert params.max_tool_calls is None
    assert params.context_management is None
    assert params.plugins is None


def test_responses_params_max_tool_calls_bounds():
    """max_tool_calls must be 1..10."""
    with pytest.raises(Exception):
        ResponsesParams(input="x", max_tool_calls=0)
    with pytest.raises(Exception):
        ResponsesParams(input="x", max_tool_calls=11)


def test_responses_params_max_tool_calls_valid():
    p1 = ResponsesParams(input="x", max_tool_calls=1)
    assert p1.max_tool_calls == 1
    p2 = ResponsesParams(input="x", max_tool_calls=10)
    assert p2.max_tool_calls == 10


# ---------------------------------------------------------------------------
# C. ChatCompletionParams — cache, transforms, reasoning_effort
# ---------------------------------------------------------------------------


def test_chat_completion_params_cache_field():
    params = ChatCompletionParams(
        messages=[ChatMessage(role="user", content="Hi")],
        cache=True,
    )
    dumped = params.model_dump(exclude_none=True)
    assert dumped["cache"] is True


def test_chat_completion_params_cache_false():
    params = ChatCompletionParams(
        messages=[ChatMessage(role="user", content="Hi")],
        cache=False,
    )
    dumped = params.model_dump(exclude_none=True)
    assert dumped["cache"] is False


def test_chat_completion_params_transforms_field():
    params = ChatCompletionParams(
        messages=[ChatMessage(role="user", content="Hi")],
        transforms=["middle-out"],
    )
    dumped = params.model_dump(exclude_none=True)
    assert dumped["transforms"] == ["middle-out"]


def test_chat_completion_params_reasoning_effort():
    for effort in ("high", "medium", "low", "none"):
        params = ChatCompletionParams(
            messages=[ChatMessage(role="user", content="Hi")],
            reasoning_effort=effort,  # type: ignore[arg-type]
        )
        assert params.reasoning_effort == effort


def test_chat_completion_params_new_fields_default_to_none():
    params = ChatCompletionParams(messages=[ChatMessage(role="user", content="Hi")])
    assert params.cache is None
    assert params.transforms is None
    assert params.reasoning_effort is None


# ---------------------------------------------------------------------------
# D. CreateTemplateParams — team_id
# ---------------------------------------------------------------------------


def test_create_template_params_team_id():
    params = CreateTemplateParams(name="My Template", team_id="team_abc123")
    assert params.team_id == "team_abc123"
    dumped = params.model_dump(exclude_none=True)
    assert dumped["team_id"] == "team_abc123"


def test_create_template_params_team_id_optional():
    params = CreateTemplateParams(name="My Template")
    assert params.team_id is None
    dumped = params.model_dump(exclude_none=True)
    assert "team_id" not in dumped


def test_create_template_params_team_id_in_dump():
    params = CreateTemplateParams(name="t", team_id="team_xyz")
    d = params.model_dump(exclude_none=True)
    assert d["team_id"] == "team_xyz"
    assert d["name"] == "t"
