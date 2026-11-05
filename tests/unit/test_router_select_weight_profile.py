"""Unit tests for ``RouterSelectRequest.weight_profile``.

``POST /v1/router/select`` now accepts an Auto Router weight profile such as
``cost_first`` or ``latency_first``. The field is optional: omitting it lets
the gateway resolve the profile from the key, template or org default.
"""

import pytest

import meshapi._types as types

RouterSelectRequest = getattr(types, "RouterSelectRequest", None)

pytestmark = pytest.mark.skipif(
    RouterSelectRequest is None,
    reason="RouterSelectRequest is not exposed by this SDK build",
)


@pytest.mark.parametrize("profile", ["cost_first", "latency_first"])
def test_weight_profile_is_serialised_when_set(profile: str) -> None:
    request = RouterSelectRequest.model_validate(
        {"model": "auto", "weight_profile": profile}
    )

    body = request.model_dump(exclude_none=True)

    assert body["weight_profile"] == profile


def test_weight_profile_is_omitted_when_unset() -> None:
    request = RouterSelectRequest.model_validate({"model": "auto"})

    assert request.weight_profile is None
    assert "weight_profile" not in request.model_dump(exclude_none=True)
