"""Audio resource — /v1/audio/* endpoints."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .._http import AsyncHttpClient, SyncHttpClient
from .._types import (
    ListVoicesParams,
    SpeechParams,
    TranscriptionParams,
    TranscriptionResponse,
    TranscriptionTranslateParams,
)


class AudioResource:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def synthesize(self, params: SpeechParams) -> bytes:
        """POST /v1/audio/speech — returns raw audio bytes."""
        return self._http.post_bytes("/v1/audio/speech", params.model_dump(exclude_none=True))

    def transcribe(
        self,
        file: bytes,
        params: TranscriptionParams,
        *,
        filename: str = "audio.mp3",
    ) -> TranscriptionResponse:
        """POST /v1/audio/transcriptions — multipart upload."""
        fields = params.model_dump(exclude_none=True)
        data = self._http.post_multipart(
            "/v1/audio/transcriptions",
            fields,
            file_data=(filename, file, "application/octet-stream"),
            file_field="file",
        )
        return TranscriptionResponse.model_validate(data)

    def get_transcription(self, transcription_id: str) -> Any:
        """GET /v1/audio/transcriptions/{transcription_id}."""
        return self._http.get(f"/v1/audio/transcriptions/{transcription_id}")

    def translate(
        self,
        file: bytes,
        params: Optional[TranscriptionTranslateParams] = None,
        *,
        filename: str = "audio.mp3",
    ) -> TranscriptionResponse:
        """POST /v1/audio/transcriptions/translate — multipart upload, translates to English."""
        fields: Dict[str, Any] = {}
        if params is not None:
            fields = params.model_dump(exclude_none=True)
        data = self._http.post_multipart(
            "/v1/audio/transcriptions/translate",
            fields,
            file_data=(filename, file, "application/octet-stream"),
            file_field="file",
        )
        return TranscriptionResponse.model_validate(data)

    def list_voices(self, params: Optional[ListVoicesParams] = None) -> Any:
        """GET /v1/audio/voices — list/search voices."""
        query: Dict[str, Any] = {}
        if params is not None:
            query = {k: v for k, v in params.model_dump(exclude_none=True).items()}
        return self._http.get("/v1/audio/voices", params=query or None)

    def get_voice(self, voice_id: str) -> Any:
        """GET /v1/audio/voices/{voice_id}."""
        return self._http.get(f"/v1/audio/voices/{voice_id}")


class AsyncAudioResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def synthesize(self, params: SpeechParams) -> bytes:
        """POST /v1/audio/speech — returns raw audio bytes."""
        return await self._http.post_bytes("/v1/audio/speech", params.model_dump(exclude_none=True))

    async def transcribe(
        self,
        file: bytes,
        params: TranscriptionParams,
        *,
        filename: str = "audio.mp3",
    ) -> TranscriptionResponse:
        """POST /v1/audio/transcriptions — multipart upload."""
        fields = params.model_dump(exclude_none=True)
        data = await self._http.post_multipart(
            "/v1/audio/transcriptions",
            fields,
            file_data=(filename, file, "application/octet-stream"),
            file_field="file",
        )
        return TranscriptionResponse.model_validate(data)

    async def get_transcription(self, transcription_id: str) -> Any:
        """GET /v1/audio/transcriptions/{transcription_id}."""
        return await self._http.get(f"/v1/audio/transcriptions/{transcription_id}")

    async def translate(
        self,
        file: bytes,
        params: Optional[TranscriptionTranslateParams] = None,
        *,
        filename: str = "audio.mp3",
    ) -> TranscriptionResponse:
        """POST /v1/audio/transcriptions/translate — multipart upload, translates to English."""
        fields: Dict[str, Any] = {}
        if params is not None:
            fields = params.model_dump(exclude_none=True)
        data = await self._http.post_multipart(
            "/v1/audio/transcriptions/translate",
            fields,
            file_data=(filename, file, "application/octet-stream"),
            file_field="file",
        )
        return TranscriptionResponse.model_validate(data)

    async def list_voices(self, params: Optional[ListVoicesParams] = None) -> Any:
        """GET /v1/audio/voices — list/search voices."""
        query: Dict[str, Any] = {}
        if params is not None:
            query = {k: v for k, v in params.model_dump(exclude_none=True).items()}
        return await self._http.get("/v1/audio/voices", params=query or None)

    async def get_voice(self, voice_id: str) -> Any:
        """GET /v1/audio/voices/{voice_id}."""
        return await self._http.get(f"/v1/audio/voices/{voice_id}")
