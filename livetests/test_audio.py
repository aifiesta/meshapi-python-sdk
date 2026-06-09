"""Live tests for /v1/audio/* endpoints."""

from __future__ import annotations

import os

from meshapi import MeshAPI, SpeechParams, ListVoicesParams

TTS_MODEL = os.environ.get("MESHAPI_TTS_MODEL", "sarvam/bulbul:v2")
STT_MODEL = os.environ.get("MESHAPI_STT_MODEL", "sarvam/saaras:v3")


def test_audio_synthesize(client: MeshAPI) -> None:
    params = SpeechParams(input="Hello from MeshAPI audio test.", model=TTS_MODEL)
    audio_bytes = client.audio.synthesize(params)
    assert isinstance(audio_bytes, bytes)
    assert len(audio_bytes) > 0
    print(f"[PASS] audio.synthesize -> {len(audio_bytes)} bytes")


def test_audio_list_voices(client: MeshAPI) -> None:
    voices = client.audio.list_voices(ListVoicesParams(page_size=5))
    assert voices is not None
    print(f"[PASS] audio.list_voices -> {type(voices)}")
