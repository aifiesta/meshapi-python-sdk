"""Live checks that the version this SDK pins is one the gateway actually serves.

The contract tests prove the header is *sent*. Only a real gateway can prove it is
**accepted** — and that is the failure that matters: MeshAPI answers a version it does
not serve with `400 invalid_api_version` rather than falling back, so a stale
`MESH_API_VERSION` in a published release breaks every request that release makes.

Run against a real deployment:

    cd livetests && pytest test_api_version.py -v
"""

from __future__ import annotations

from typing import Optional

import httpx
import pytest

from meshapi import MESH_API_VERSION, MeshAPI

from config import BASE_URL, TOKEN  # type: ignore[import-not-found]

_HEADER = "X-Mesh-Version"


def _auth() -> dict:
    return {"Authorization": f"Bearer {TOKEN}"}


def _served_versions() -> list:
    """The gateway's own list of pinnable versions, or skip.

    `GET /v1/api-versions` landed in routersvc #1119 and reaches prod only on a
    `v*.*.*` tag, so a 404 means "this deployment is older than the endpoint" — not a
    failure of this SDK. Skipping is the honest outcome; the checks that do not need
    the endpoint still run and still catch a stale pin.
    """
    response = httpx.get(f"{BASE_URL}/v1/api-versions", headers=_auth(), timeout=30.0)
    if response.status_code == 404:
        pytest.skip(f"{BASE_URL} predates GET /v1/api-versions (routersvc #1119)")
    response.raise_for_status()
    return response.json()


def test_the_pinned_version_is_served(client: MeshAPI) -> None:
    """The whole point: a real request carrying this SDK's pin must succeed.

    If this fails with `invalid_api_version`, the constant is stale and this release
    cannot talk to the gateway at all.
    """
    assert client.models.list()


def test_the_gateway_lists_our_pinned_version() -> None:
    """Catches a stale SDK the moment a version is retired, rather than when a
    customer reports a 400."""
    labels = [entry["label"] for entry in _served_versions()]

    assert MESH_API_VERSION in labels, (
        f"this SDK pins {MESH_API_VERSION}, which {BASE_URL} does not serve; "
        f"served versions are {labels}"
    )


def test_our_pinned_version_is_not_already_sunset() -> None:
    """A version can still be listed while on its way out. `sunset_on` is the date it
    stops being served — a release pinning a sunset version is already broken, it just
    has not failed yet."""
    entry = next(
        (e for e in _served_versions() if e["label"] == MESH_API_VERSION), None
    )
    if entry is None:
        pytest.skip("covered by test_the_gateway_lists_our_pinned_version")

    assert entry["status"] != "sunset", (
        f"this SDK pins {MESH_API_VERSION}, which is sunset "
        f"(sunset_on={entry.get('sunset_on')}); see {entry.get('notes_url')}"
    )


def _echoed(response: httpx.Response) -> Optional[str]:
    """The version the gateway says it served.

    Read under either name on purpose. routersvc renamed the header to
    `X-Mesh-Version` (#1110), but that reaches a deployment only on a `v*.*.*` tag —
    as of 2026-08-12 api-dev echoes `x-mesh-version` and **prod still echoes
    `mesh-version`**. Both accept either name on the *request*, so the SDK's pin is
    honoured on both; only the echo lags. Being strict about the echo name here would
    report a green SDK as broken against an untagged prod, which is a fact about the
    deployment, not about this client.
    """
    return response.headers.get(_HEADER) or response.headers.get("Mesh-Version")


def test_the_response_echoes_the_version_served() -> None:
    """The gateway echoes the version it served. An echo that differs from what was
    sent means the SDK is parsing a shape it did not ask for."""
    response = httpx.get(
        f"{BASE_URL}/v1/models",
        headers={**_auth(), _HEADER: MESH_API_VERSION},
        timeout=60.0,
    )
    response.raise_for_status()

    assert _echoed(response) == MESH_API_VERSION


def test_an_unserved_version_is_rejected_loudly() -> None:
    """Confirms the gateway does NOT silently fall back — the property the whole
    pinning scheme rests on. If this ever returned 200, a typo'd pin would leave a
    caller believing they were pinned when they were not.
    """
    response = httpx.get(
        f"{BASE_URL}/v1/models",
        headers={**_auth(), _HEADER: "1999-01"},
        timeout=30.0,
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_api_version"


def test_an_unpinned_request_is_served_the_baseline() -> None:
    """No header means the gateway's baseline, and it says which one it used. This is
    what `api_version=None` opts into."""
    baseline: Optional[str] = next(
        (e["label"] for e in _served_versions() if e["baseline"]), None
    )
    assert baseline, "the gateway must mark exactly one version as the baseline"

    response = httpx.get(f"{BASE_URL}/v1/models", headers=_auth(), timeout=60.0)
    response.raise_for_status()

    assert _echoed(response) == baseline
