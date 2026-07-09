"""Chat completions resource — POST /v1/chat/completions."""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, FrozenSet, Iterator, List, Optional

import httpx

from .._errors import MeshAPIError
from .._http import AsyncHttpClient, SyncHttpClient
from .._resilience import DEFAULT_FALLBACK_STATUS_CODES, FallbackEvent
from .._types import ChatCompletionChunk, ChatCompletionParams, ChatCompletionResponse

_CHAT_COMPLETIONS_PATH = "/v1/chat/completions"


def _resolve_chain(
    http_fallback: Any, fallback_models: Optional[List[str]], primary: Optional[str]
) -> "tuple[List[str], FrozenSet[int]]":
    """Resolve the effective fallback chain (per-call override wins over the
    client config) with the primary model filtered out, plus the status set
    eligible for advancing the chain.
    """
    if fallback_models is not None:
        models = fallback_models
    elif http_fallback is not None:
        models = http_fallback.models
    else:
        models = []
    chain = [m for m in models if m != primary]
    on_status = frozenset(
        http_fallback.on_status if http_fallback is not None else DEFAULT_FALLBACK_STATUS_CODES
    )
    return chain, on_status


def _is_fallback_eligible(err: Exception, on_status: FrozenSet[int]) -> bool:
    """A failure is worth trying on another model when it is transient
    (default 502/503/504 — a provider/gateway path problem, not this request)
    or a pre-response network error. Timeouts and cancellation always
    propagate; terminal API errors (4xx auth/validation/billing) never
    advance the chain — they would fail identically on every model.
    """
    if isinstance(err, MeshAPIError):
        return err.status in on_status
    if isinstance(err, httpx.TimeoutException):
        return False
    return isinstance(err, httpx.RequestError)


def _fallback_event(
    last_error: Optional[Exception],
    from_model: str,
    to_model: str,
    chain_index: int,
    chain_length: int,
) -> FallbackEvent:
    err = last_error if isinstance(last_error, MeshAPIError) else None
    return FallbackEvent(
        from_model=from_model,
        to_model=to_model,
        chain_index=chain_index,
        chain_length=chain_length,
        status=err.status if err is not None else None,
        error_code=err.error_code if err is not None else None,
        request_id=(err.request_id or None) if err is not None else None,
    )


def _body_for_model(body: Dict[str, Any], model: Optional[str]) -> Dict[str, Any]:
    attempt_body = dict(body)
    if model is not None:
        attempt_body["model"] = model
    return attempt_body


class CompletionsResource:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def create(
        self,
        params: ChatCompletionParams,
        *,
        fallback_models: Optional[List[str]] = None,
    ) -> ChatCompletionResponse:
        """Non-streaming completion. Returns the full response.

        ``fallback_models`` is a client-side directive — never sent to the
        server. It overrides the client-wide ``fallback.models`` chain: when
        the primary model's request fails with a transient error (default
        502/503/504, after transport retries), the SDK re-issues the request
        against each chain model in order. Terminal errors (auth, validation,
        billing) never advance the chain. Each hop fires a ``fallback`` event.
        """
        body = params.model_dump(exclude_none=True)
        body.pop("fallback_models", None)  # client directive — never on the wire
        body["stream"] = False

        primary = body.get("model")
        chain, on_status = _resolve_chain(self._http.fallback, fallback_models, primary)

        last_error: Optional[Exception] = None
        # `model` may be unset (the key's default_model applies server-side) —
        # label it for fallback events; the chain always names explicit models.
        from_model = primary or "(key default)"
        for index in range(len(chain) + 1):
            model = primary if index == 0 else chain[index - 1]
            if index > 0:
                self._http.emit(
                    _fallback_event(last_error, from_model, model, index - 1, len(chain))  # type: ignore[arg-type]
                )
            try:
                data = self._http.post(_CHAT_COMPLETIONS_PATH, _body_for_model(body, model))
                return ChatCompletionResponse.model_validate(data)
            except Exception as err:
                last_error = err
                from_model = model or from_model
                if not chain or not _is_fallback_eligible(err, on_status):
                    raise
        assert last_error is not None  # chain exhausted — re-raise the last error
        raise last_error

    def stream(self, params: ChatCompletionParams) -> Iterator[ChatCompletionChunk]:
        """Streaming completion. Returns an iterator of SSE chunks.

        Streams do NOT retry or fallback-chain on failure (a partially
        consumed stream cannot be transparently restarted). Catch
        MeshAPIError and restart a new request if reconnection is needed.
        """
        body = params.model_dump(exclude_none=True)
        body["stream"] = True
        yield from self._http.stream(_CHAT_COMPLETIONS_PATH, body)


class ChatResource:
    def __init__(self, http: SyncHttpClient) -> None:
        self.completions = CompletionsResource(http)


class AsyncCompletionsResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def create(
        self,
        params: ChatCompletionParams,
        *,
        fallback_models: Optional[List[str]] = None,
    ) -> ChatCompletionResponse:
        """Non-streaming completion.

        ``fallback_models`` is a client-side directive — never sent to the
        server. See ``CompletionsResource.create`` for the chain semantics.
        """
        body = params.model_dump(exclude_none=True)
        body.pop("fallback_models", None)  # client directive — never on the wire
        body["stream"] = False

        primary = body.get("model")
        chain, on_status = _resolve_chain(self._http.fallback, fallback_models, primary)

        last_error: Optional[Exception] = None
        from_model = primary or "(key default)"
        for index in range(len(chain) + 1):
            model = primary if index == 0 else chain[index - 1]
            if index > 0:
                self._http.emit(
                    _fallback_event(last_error, from_model, model, index - 1, len(chain))  # type: ignore[arg-type]
                )
            try:
                data = await self._http.post(
                    _CHAT_COMPLETIONS_PATH, _body_for_model(body, model)
                )
                return ChatCompletionResponse.model_validate(data)
            except Exception as err:
                last_error = err
                from_model = model or from_model
                if not chain or not _is_fallback_eligible(err, on_status):
                    raise
        assert last_error is not None  # chain exhausted — re-raise the last error
        raise last_error

    async def stream(self, params: ChatCompletionParams) -> AsyncIterator[ChatCompletionChunk]:
        """Streaming completion. Returns an async iterator of SSE chunks.

        Streams do NOT retry or fallback-chain on failure (a partially
        consumed stream cannot be transparently restarted). Catch
        MeshAPIError and restart a new request if reconnection is needed.
        """
        body = params.model_dump(exclude_none=True)
        body["stream"] = True
        async for chunk in self._http.stream(_CHAT_COMPLETIONS_PATH, body):
            yield chunk


class AsyncChatResource:
    def __init__(self, http: AsyncHttpClient) -> None:
        self.completions = AsyncCompletionsResource(http)
