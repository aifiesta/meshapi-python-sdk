"""The SDK declares which dated API version it was built against (MESH-508).

MeshAPI versions its contract by date, in a request header. An SDK that sends
nothing is served the gateway's BASELINE — which is safe today, but it also means
the SDK never states what response shape it can actually parse. Sending the version
explicitly is the difference between "whatever the server defaults to" and "the
shape this release was written for".

Concretely: when the gateway publishes a version that removes a field this SDK
declares, an unpinned caller keeps working only because BASELINE happens not to
move. A pinned caller keeps working *by contract*, and the gateway can see — in
`usage_events.api_version` — who is still on the old shape before retiring it.
"""

from __future__ import annotations

import httpx

from meshapi import MESH_API_VERSION, AsyncMeshAPI, MeshAPI

_HEADER = "X-Mesh-Version"


def _capturing_transport(seen: dict) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        seen["headers"] = dict(request.headers)
        # Echo it back the way the gateway does, so the assertions below can compare
        # what was sent against what was served.
        return httpx.Response(
            200,
            json=[],
            headers={_HEADER: request.headers.get(_HEADER, "")},
        )

    return httpx.MockTransport(handler)


class TestTheConstant:
    def test_a_dated_version_is_exported(self):
        """Public, because a caller pinning per-request needs something to pass, and
        a caller debugging a shape mismatch needs to know what was sent."""
        assert MESH_API_VERSION == "2026-08"

    def test_it_is_a_yyyy_mm_label(self):
        """The gateway 400s a malformed label rather than falling back, so a typo here
        would break every request this SDK makes, not degrade quietly."""
        year, _, month = MESH_API_VERSION.partition("-")
        assert len(year) == 4 and year.isdigit()
        assert len(month) == 2 and month.isdigit()
        assert 1 <= int(month) <= 12


class TestDefaultHeader:
    def test_the_sync_client_sends_it(self):
        seen: dict = {}
        client = MeshAPI(
            base_url="https://api.test",
            token="rsk_test",
            httpx_client=httpx.Client(
                base_url="https://api.test", transport=_capturing_transport(seen)
            ),
        )

        client.models.list()

        assert seen["headers"][_HEADER.lower()] == MESH_API_VERSION

    async def test_the_async_client_sends_it(self):
        seen: dict = {}
        client = AsyncMeshAPI(
            base_url="https://api.test",
            token="rsk_test",
            async_httpx_client=httpx.AsyncClient(
                base_url="https://api.test", transport=_capturing_transport(seen)
            ),
        )

        await client.models.list()

        assert seen["headers"][_HEADER.lower()] == MESH_API_VERSION

    def test_what_it_sends_satisfies_a_strict_gateway(self):
        """Simulates the real gateway rather than asserting against a permissive mock.

        MeshAPI 400s `invalid_api_version` on a label it does not serve, and treats an
        EMPTY header value as a typo'd pin rather than "no pin". A transport that
        accepts anything would let both mistakes pass, so this one enforces the same
        rules and the call has to survive them.
        """
        served = {MESH_API_VERSION, "2026-09"}

        def strict_gateway(request: httpx.Request) -> httpx.Response:
            pinned = request.headers.get(_HEADER)
            if pinned is not None and pinned.strip() not in served:
                return httpx.Response(
                    400, json={"error": {"code": "invalid_api_version"}}
                )
            return httpx.Response(200, json=[])

        client = MeshAPI(
            base_url="https://api.test",
            token="rsk_test",
            httpx_client=httpx.Client(
                base_url="https://api.test", transport=httpx.MockTransport(strict_gateway)
            ),
        )

        assert client.models.list() == []

    def test_it_does_not_displace_the_sdk_identity_header(self):
        """Two different headers with two different jobs: one says which SDK build,
        the other which contract. Neither substitutes for the other."""
        seen: dict = {}
        client = MeshAPI(
            base_url="https://api.test",
            token="rsk_test",
            httpx_client=httpx.Client(
                base_url="https://api.test", transport=_capturing_transport(seen)
            ),
        )

        client.models.list()

        assert seen["headers"]["x-meshapi-sdk"].startswith("python/")
        assert seen["headers"][_HEADER.lower()] == MESH_API_VERSION


class TestPerClientOverride:
    def test_a_caller_may_pin_a_different_version(self):
        """A customer who has migrated ahead of this SDK release must not be forced
        back onto the version the SDK was built against."""
        seen: dict = {}
        client = MeshAPI(
            base_url="https://api.test",
            token="rsk_test",
            api_version="2026-09",
            httpx_client=httpx.Client(
                base_url="https://api.test", transport=_capturing_transport(seen)
            ),
        )

        client.models.list()

        assert seen["headers"][_HEADER.lower()] == "2026-09"

    def test_none_means_send_nothing(self):
        """Explicit opt-out, distinct from "unset". Omitting the header entirely is
        how a caller asks for the gateway's baseline whatever it may become — the
        pre-MESH-508 behaviour, still reachable on purpose.
        """
        seen: dict = {}
        client = MeshAPI(
            base_url="https://api.test",
            token="rsk_test",
            api_version=None,
            httpx_client=httpx.Client(
                base_url="https://api.test", transport=_capturing_transport(seen)
            ),
        )

        client.models.list()

        assert _HEADER.lower() not in seen["headers"]

    async def test_the_async_client_honours_the_override_too(self):
        """Both clients build their headers independently, so the override has to be
        asserted on each — a fix applied to one is exactly the kind of thing that gets
        missed on the other."""
        seen: dict = {}
        client = AsyncMeshAPI(
            base_url="https://api.test",
            token="rsk_test",
            api_version="2026-09",
            async_httpx_client=httpx.AsyncClient(
                base_url="https://api.test", transport=_capturing_transport(seen)
            ),
        )

        await client.models.list()

        assert seen["headers"][_HEADER.lower()] == "2026-09"
