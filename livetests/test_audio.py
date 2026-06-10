"""Live tests for /v1/audio/* endpoints."""

from __future__ import annotations

import os

from meshapi import MeshAPI, SpeechParams, ListVoicesParams, TranscriptionParams

TTS_MODEL = os.environ.get("MESHAPI_TTS_MODEL", "sarvam/bulbul:v2")
STT_MODEL = os.environ.get("MESHAPI_STT_MODEL", "sarvam/saaras:v3")


def test_audio_synthesize(client: MeshAPI) -> None:
    params = SpeechParams(input="Hello from MeshAPI audio test.", model=TTS_MODEL)
    audio_bytes = client.audio.synthesize(params)
    assert isinstance(audio_bytes, bytes)
    assert len(audio_bytes) > 0
    print(f"[PASS] audio.synthesize -> {len(audio_bytes)} bytes")


def test_audio_stt_from_tts(client: MeshAPI) -> None:
    audio_bytes = client.audio.synthesize(
        SpeechParams(input="Hello from MeshAPI audio test.", model=TTS_MODEL)
    )
    assert isinstance(audio_bytes, bytes) and len(audio_bytes) > 0, "TTS step failed; skipping STT"

    result = client.audio.transcribe(
        audio_bytes,
        TranscriptionParams(model=STT_MODEL),
        filename="tts_output.wav",
    )
    assert result is not None
    assert isinstance(result.text, str) and len(result.text) > 0
    print(f"[PASS] audio.transcribe (via TTS audio) -> {result.text!r}")


def test_audio_list_voices(client: MeshAPI) -> None:
    voices = client.audio.list_voices(ListVoicesParams(page_size=5))
    assert voices is not None
    print(f"[PASS] audio.list_voices -> {type(voices)}")
