from meshapi._types_keys import ApiKeyDetails


def test_minimal_payload_parses():
    key = ApiKeyDetails.model_validate({"id": "key_1"})
    assert key.scopes == []
    assert key.allowed_models is None
    assert key.effective_limits is None


def test_unknown_fields_are_kept():
    key = ApiKeyDetails.model_validate({"id": "key_1", "new_field": 1})
    assert key.model_extra == {"new_field": 1}


def test_no_secret_fields_declared():
    fields = set(ApiKeyDetails.model_fields)
    assert "key" not in fields
    assert "key_hash" not in fields
