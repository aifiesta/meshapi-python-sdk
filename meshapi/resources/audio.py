"""Audio resource — /v1/audio/* endpoints."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .._http import AsyncHttpClient, SyncHttpClient
from .._types import (
    AudioTranslationsParams,
    ListVoicesParams,
    SpeechParams,
    TranscriptionParams,
    TranscriptionResponse,
    TranscriptionTranslateParams,
    Voice,
    VoicesResponse,
)


class AudioResource:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def synthesize(self, params: SpeechParams, *, request_id: Optional[str] = None) -> bytes:
        """POST /v1/audio/speech — returns raw audio bytes."""
        return self._http.post_bytes(
            "/v1/audio/speech", params.model_dump(exclude_none=True), request_id=request_id
        )

    def transcribe(
        self,
        file: bytes,
        params: TranscriptionParams,
        *,
        filename: str = "audio.mp3",
        request_id: Optional[str] = None,
    ) -> TranscriptionResponse:
        """POST /v1/audio/transcriptions — multipart upload."""
        fields = params.model_dump(exclude_none=True)
        data = self._http.post_multipart(
            "/v1/audio/transcriptions",
            fields,
            file_data=(filename, file, "application/octet-stream"),
            file_field="file",
            request_id=request_id,
        )
        return TranscriptionResponse.model_validate(data)

    def get_transcription(
        self, transcription_id: str, *, request_id: Optional[str] = None
    ) -> Any:
        """GET /v1/audio/transcriptions/{transcription_id}."""
        return self._http.get(
            f"/v1/audio/transcriptions/{transcription_id}", request_id=request_id
        )

    def translate(
        self,
        file: bytes,
        params: Optional[TranscriptionTranslateParams] = None,
        *,
        filename: str = "audio.mp3",
        request_id: Optional[str] = None,
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
            request_id=request_id,
        )
        return TranscriptionResponse.model_validate(data)

    def audio_translate(
        self,
        file: bytes,
        params: AudioTranslationsParams,
        *,
        filename: str = "audio.mp3",
        request_id: Optional[str] = None,
    ) -> TranscriptionResponse:
        """POST /v1/audio/translations — standalone translation endpoint.

        Translates the uploaded audio to English.  This is a distinct endpoint
        from ``translate()`` which posts to ``/v1/audio/transcriptions/translate``.
        """
        fields = params.model_dump(exclude_none=True)
        data = self._http.post_multipart(
            "/v1/audio/translations",
            fields,
            file_data=(filename, file, "application/octet-stream"),
            file_field="file",
            request_id=request_id,
        )
        return TranscriptionResponse.model_validate(data)

    def list_voices(
        self,
        params: Optional[ListVoicesParams] = None,
        *,
        request_id: Optional[str] = None,
    ) -> VoicesResponse:
        """GET /v1/audio/voices — list/search voices."""
        query: Dict[str, Any] = {}
        if params is not None:
            query = {k: v for k, v in params.model_dump(exclude_none=True).items()}
        data = self._http.get("/v1/audio/voices", params=query or None, request_id=request_id)
        return VoicesResponse.model_validate(data)

    def get_voice(self, voice_id: str, *, request_id: Optional[str] = None) -> Voice:
        """GET /v1/audio/voices/{voice_id}."""
        data = self._http.get(f"/v1/audio/voices/{voice_id}", request_id=request_id)
        return Voice.model_validate(data)


class AsyncAudioResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def synthesize(self, params: SpeechParams, *, request_id: Optional[str] = None) -> bytes:
        """POST /v1/audio/speech — returns raw audio bytes."""
        return await self._http.post_bytes(
            "/v1/audio/speech", params.model_dump(exclude_none=True), request_id=request_id
        )

    async def transcribe(
        self,
        file: bytes,
        params: TranscriptionParams,
        *,
        filename: str = "audio.mp3",
        request_id: Optional[str] = None,
    ) -> TranscriptionResponse:
        """POST /v1/audio/transcriptions — multipart upload."""
        fields = params.model_dump(exclude_none=True)
        data = await self._http.post_multipart(
            "/v1/audio/transcriptions",
            fields,
            file_data=(filename, file, "application/octet-stream"),
            file_field="file",
            request_id=request_id,
        )
        return TranscriptionResponse.model_validate(data)

    async def get_transcription(
        self, transcription_id: str, *, request_id: Optional[str] = None
    ) -> Any:
        """GET /v1/audio/transcriptions/{transcription_id}."""
        return await self._http.get(
            f"/v1/audio/transcriptions/{transcription_id}", request_id=request_id
        )

    async def translate(
        self,
        file: bytes,
        params: Optional[TranscriptionTranslateParams] = None,
        *,
        filename: str = "audio.mp3",
        request_id: Optional[str] = None,
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
            request_id=request_id,
        )
        return TranscriptionResponse.model_validate(data)

    async def audio_translate(
        self,
        file: bytes,
        params: AudioTranslationsParams,
        *,
        filename: str = "audio.mp3",
        request_id: Optional[str] = None,
    ) -> TranscriptionResponse:
        """POST /v1/audio/translations — standalone translation endpoint.

        Translates the uploaded audio to English.  This is a distinct endpoint
        from ``translate()`` which posts to ``/v1/audio/transcriptions/translate``.
        """
        fields = params.model_dump(exclude_none=True)
        data = await self._http.post_multipart(
            "/v1/audio/translations",
            fields,
            file_data=(filename, file, "application/octet-stream"),
            file_field="file",
            request_id=request_id,
        )
        return TranscriptionResponse.model_validate(data)

    async def list_voices(
        self,
        params: Optional[ListVoicesParams] = None,
        *,
        request_id: Optional[str] = None,
    ) -> VoicesResponse:
        """GET /v1/audio/voices — list/search voices."""
        query: Dict[str, Any] = {}
        if params is not None:
            query = {k: v for k, v in params.model_dump(exclude_none=True).items()}
        data = await self._http.get("/v1/audio/voices", params=query or None, request_id=request_id)
        return VoicesResponse.model_validate(data)

    async def get_voice(self, voice_id: str, *, request_id: Optional[str] = None) -> Voice:
        """GET /v1/audio/voices/{voice_id}."""
        data = await self._http.get(f"/v1/audio/voices/{voice_id}", request_id=request_id)
        return Voice.model_validate(data)
