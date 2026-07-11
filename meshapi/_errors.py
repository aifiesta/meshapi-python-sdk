"""MeshAPI API error type."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    import httpx


# Fallback machine-readable codes by HTTP status, used when the response body
# is not the standard {"error": {"code": ...}} envelope.
_STATUS_ERROR_CODES: Dict[int, str] = {
    400: "invalid_request",
    401: "unauthorized",
    402: "spend_limit_exceeded",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    422: "validation_error",
    429: "rate_limit_exceeded",
    500: "upstream_error",
    502: "upstream_error",
    503: "upstream_error",
    504: "upstream_error",
}


class MeshAPIError(Exception):
    """Raised when MeshAPI returns a non-2xx response or a mid-stream error."""

    status: int
    error_code: str
    request_id: str
    details: List[Any]
    provider_error: Optional[Dict[str, Any]]
    retry_after_seconds: Optional[int]

    def __init__(
        self,
        message: str,
        *,
        status: int,
        error_code: str,
        request_id: str,
        details: Optional[List[Any]] = None,
        provider_error: Optional[Dict[str, Any]] = None,
        retry_after_seconds: Optional[int] = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.error_code = error_code
        self.request_id = request_id
        self.details = details or []
        self.provider_error = provider_error
        self.retry_after_seconds = retry_after_seconds

    def __repr__(self) -> str:
        return (
            f"MeshAPIError(status={self.status!r}, "
            f"error_code={self.error_code!r}, "
            f"request_id={self.request_id!r}, "
            f"message={str(self)!r})"
        )

    @classmethod
    def from_response(cls, response: "httpx.Response") -> "MeshAPIError":
        """Parse a MeshAPIError from an httpx Response."""
        status = response.status_code
        content_type = response.headers.get("content-type", "")
        request_id = response.headers.get("x-request-id", "")

        if "application/json" not in content_type:
            raw = response.text[:500]
            return cls(
                raw or f"HTTP {status}",
                status=status,
                error_code="parse_error",
                request_id=request_id,
            )

        try:
            body = response.json()
            error = body.get("error") if isinstance(body, dict) else None
            if not isinstance(error, dict):
                error = {}
            if isinstance(body, dict):
                request_id = body.get("request_id", request_id)
            # Fall back to a status-derived code and a FastAPI-style "detail"
            # message when the body isn't the standard {"error": {...}} envelope
            # (e.g. GET /v1/models/{id} 404s return {"detail": "..."}).
            code = error.get("code") or _STATUS_ERROR_CODES.get(status, "http_error")
            detail = body.get("detail") if isinstance(body, dict) else None
            message = error.get("message") or (detail if isinstance(detail, str) else None) or f"HTTP {status}"
            return cls(
                message,
                status=status,
                error_code=code,
                request_id=request_id,
                details=error.get("details") or [],
                provider_error=error.get("provider_error"),
                retry_after_seconds=error.get("retry_after_seconds"),
            )
        except Exception:
            raw = response.text[:500]
            return cls(
                raw or f"HTTP {status}",
                status=status,
                error_code="parse_error",
                request_id=request_id,
            )

    @classmethod
    def stream_interrupted(cls, cause: str) -> "MeshAPIError":
        """Create an error representing a mid-stream connection failure."""
        return cls(
            f"Stream interrupted: {cause}",
            status=0,
            error_code="stream_interrupted",
            request_id="",
        )


class StructuredOutputError(MeshAPIError):
    """Raised by ``chat.completions.parse()`` when the model's response cannot be
    parsed into the requested schema.

    The most common cause is that the model does not support structured outputs
    (``response_format``): the gateway forwards the field, the provider ignores
    it, and the model returns plain text instead of JSON. The underlying
    ``pydantic.ValidationError`` / ``json.JSONDecodeError`` is preserved on
    ``__cause__``. A client-side error, so ``status`` is ``0``.
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            status=0,
            error_code="structured_output_parse_error",
            request_id="",
        )
