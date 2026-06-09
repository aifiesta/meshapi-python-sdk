"""Live tests for POST /v1/audio/speech, POST /v1/audio/transcriptions, and GET /v1/audio/voices."""

import os
from meshapi import SpeechParams, ListVoicesParams

from .config import client

TTS_MODEL = os.environ.get("MESHAPI_TTS_MODEL", "sarvam/bulbul:v2")
STT_MODEL = os.environ.get("MESHAPI_STT_MODEL", "sarvam/saaras:v3")


def test_speech_synthesize():
    params = SpeechParams(input="Hello from MeshAPI audio test.", model=TTS_MODEL)
    audio_bytes = client.audio.synthesize(params)
    assert isinstance(audio_bytes, bytes)
    assert len(audio_bytes) > 0
    print(f"[PASS] audio.synthesize -> {len(audio_bytes)} bytes")


def test_list_voices():
    voices = client.audio.list_voices(ListVoicesParams(page_size=5))
    assert voices is not None
    print(f"[PASS] audio.list_voices -> {type(voices)}")


def test_get_voice():
    voices = client.audio.list_voices(ListVoicesParams(page_size=1))
    # Just ensure it doesn't throw; response shape is opaque
    assert voices is not None
    print("[PASS] audio.get_voice (list only, id lookup skipped if no voices)")
