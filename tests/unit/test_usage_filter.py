from meshapi._cost_types import UsageFilter


def test_empty_filter_serialises_to_empty_body():
    assert UsageFilter().to_body() == {}


def test_new_filter_fields_serialise():
    body = UsageFilter(
        provider=["openai"],
        fault_owner="provider",
        is_byok=False,
        stream=True,
        traffic_type="external",
        is_retry_attempt=[True, False],
    ).to_body()
    assert body == {
        "provider": ["openai"],
        "fault_owner": "provider",
        "is_byok": False,
        "stream": True,
        "traffic_type": "external",
        "is_retry_attempt": [True, False],
    }


def test_unset_fields_are_dropped():
    assert UsageFilter(stream=False).to_body() == {"stream": False}
