import asyncio

import pytest

from meshapi._types_keys import ApiKeyDetails
from meshapi.resources.keys import AsyncKeysResource, KeysResource

PAYLOAD = {
    "id": "key_123",
    "org_id": "org_1",
    "label": "ci",
    "masked_key": "rsk_...abcd",
    "scopes": ["chat"],
    "allowed_models": ["openai/gpt-4o-mini"],
    "blocked_models": [],
    "model_limits": None,
    "effective_limits": {"rpm": 60},
}


class FakeSync:
    def __init__(self):
        self.paths = []

    def get(self, path):
        self.paths.append(path)
        return PAYLOAD


class FakeAsync:
    def __init__(self):
        self.paths = []

    async def get(self, path):
        self.paths.append(path)
        return PAYLOAD


def test_retrieve_calls_path_and_parses():
    http = FakeSync()
    key = KeysResource(http).retrieve("key_123")
    assert http.paths == ["/v1/keys/key_123"]
    assert isinstance(key, ApiKeyDetails)
    assert key.org_id == "org_1"
    assert key.scopes == ["chat"]
    assert key.effective_limits == {"rpm": 60}


def test_retrieve_escapes_key_id():
    http = FakeSync()
    KeysResource(http).retrieve("a/b")
    assert http.paths == ["/v1/keys/a%2Fb"]


@pytest.mark.parametrize("bad", ["", "   "])
def test_retrieve_rejects_empty_id(bad):
    with pytest.raises(ValueError):
        KeysResource(FakeSync()).retrieve(bad)


def test_async_retrieve():
    http = FakeAsync()
    key = asyncio.run(AsyncKeysResource(http).retrieve("key_123"))
    assert http.paths == ["/v1/keys/key_123"]
    assert key.id == "key_123"
