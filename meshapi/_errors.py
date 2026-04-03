"""MeshAPI API error type."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    import httpx


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
            error = body.get("error", {})
            request_id = body.get("request_id", request_id)
            return cls(
                error.get("message", f"HTTP {status}"),
                status=status,
                error_code=error.get("code", "unknown_error"),
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
