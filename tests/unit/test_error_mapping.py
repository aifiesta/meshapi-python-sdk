"""Unit tests for error parsing and mapping."""

import json
from unittest.mock import MagicMock

import pytest

from routersvc._errors import RouterSvcApiError


def make_mock_response(status: int, body: dict, content_type: str = "application/json") -> MagicMock:
    mock = MagicMock()
    mock.status_code = status
    mock.headers = {"content-type": content_type, "x-request-id": "req_test01"}
    mock.json.return_value = body
    mock.text = json.dumps(body)
    return mock


# ---------------------------------------------------------------------------
# from_response
# ---------------------------------------------------------------------------


def test_401_unauthorized():
    body = {"error": {"code": "unauthorized", "message": "Invalid or missing API key."}, "request_id": "req_001"}
    resp = make_mock_response(401, body)
    err = RouterSvcApiError.from_response(resp)
    assert err.status == 401
    assert err.error_code == "unauthorized"
    assert err.request_id == "req_001"
    assert "Invalid or missing API key" in str(err)


def test_422_validation_error_with_details():
    body = {
        "error": {
            "code": "validation_error",
            "message": "Request validation failed.",
            "details": [{"type": "missing", "loc": ["body", "messages"], "msg": "Field required"}],
        },
        "request_id": "req_422",
    }
    resp = make_mock_response(422, body)
    err = RouterSvcApiError.from_response(resp)
    assert err.status == 422
    assert err.error_code == "validation_error"
    assert len(err.details) == 1
    assert err.details[0]["type"] == "missing"


def test_429_rate_limit_with_retry_after():
    body = {
        "error": {
            "code": "rate_limit_exceeded",
            "message": "Rate limit exceeded.",
            "retry_after_seconds": 5,
        },
        "request_id": "req_429",
    }
    resp = make_mock_response(429, body)
    err = RouterSvcApiError.from_response(resp)
    assert err.status == 429
    assert err.error_code == "rate_limit_exceeded"
    assert err.retry_after_seconds == 5


def test_500_upstream_error():
    body = {"error": {"code": "upstream_error", "message": "Upstream provider returned an error."}, "request_id": "req_500"}
    resp = make_mock_response(500, body)
    err = RouterSvcApiError.from_response(resp)
    assert err.status == 500
    assert err.error_code == "upstream_error"


def test_html_body_parse_error():
    mock = MagicMock()
    mock.status_code = 502
    mock.headers = {"content-type": "text/html", "x-request-id": ""}
    mock.text = "<html><body>Bad Gateway</body></html>"
    err = RouterSvcApiError.from_response(mock)
    assert err.error_code == "parse_error"
    assert "Bad Gateway" in str(err)


def test_plain_text_body_parse_error():
    mock = MagicMock()
    mock.status_code = 503
    mock.headers = {"content-type": "text/plain", "x-request-id": ""}
    mock.text = "Service Unavailable"
    err = RouterSvcApiError.from_response(mock)
    assert err.error_code == "parse_error"


def test_malformed_json_body_parse_error():
    mock = MagicMock()
    mock.status_code = 500
    mock.headers = {"content-type": "application/json", "x-request-id": ""}
    mock.json.side_effect = ValueError("Invalid JSON")
    mock.text = "not json"
    err = RouterSvcApiError.from_response(mock)
    assert err.error_code == "parse_error"


def test_stream_interrupted_factory():
    err = RouterSvcApiError.stream_interrupted("connection reset")
    assert err.error_code == "stream_interrupted"
    assert err.status == 0
    assert "connection reset" in str(err)


def test_repr():
    err = RouterSvcApiError("oops", status=404, error_code="not_found", request_id="req_x")
    r = repr(err)
    assert "RouterSvcApiError" in r
    assert "404" in r
    assert "not_found" in r


def test_isinstance_exception():
    err = RouterSvcApiError("msg", status=400, error_code="bad_request", request_id="req_y")
    assert isinstance(err, Exception)
    assert isinstance(err, RouterSvcApiError)
