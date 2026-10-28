from meshapi._usage_types import UsageFilter


def test_empty_filter_sends_nothing():
    assert UsageFilter().to_payload() == {}


def test_new_fields_serialise():
    f = UsageFilter(
        provider="openai",
        fault_owner="provider",
        is_byok=False,
        stream=True,
        traffic_type="external",
        is_retry_attempt=[True, False],
    )
    assert f.to_payload() == {
        "provider": "openai",
        "fault_owner": "provider",
        "is_byok": False,
        "stream": True,
        "traffic_type": "external",
        "is_retry_attempt": [True, False],
    }
