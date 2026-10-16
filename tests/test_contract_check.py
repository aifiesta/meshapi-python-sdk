import importlib.util
import json
import os
from pathlib import Path

import pytest

pytest.importorskip("meshapi_contract")
from meshapi_contract.diff import public_subset  # noqa: E402
from meshapi_contract.surface import (  # noqa: E402
    actual_surface_from_json,
    diff_surface,
    expected_surface,
)

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = Path(
    os.environ.get("MESHAPI_SPEC_PATH", ROOT.parent / "meshapi-docs" / "api" / "openapi.json")
)


def _load_dumper():
    spec = importlib.util.spec_from_file_location("dump_surface", ROOT / "scripts" / "dump_surface.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def actual_json():
    return _load_dumper().build_surface()


@pytest.fixture(scope="module")
def spec():
    return json.loads((ROOT / "tests" / "fixtures" / "contract_spec.json").read_text())


@pytest.fixture(scope="module")
def published_spec():
    if not SPEC_PATH.exists():
        pytest.skip(f"published spec not found at {SPEC_PATH}")
    return json.loads(SPEC_PATH.read_text())


def test_envelope_matches_gate_contract(actual_json):
    assert actual_json["schema_version"] == "1"
    assert actual_json["spec_version"] == (ROOT / ".meshapi-spec-version").read_text().strip()
    assert actual_json["model_fields"] and actual_json["params"]


def test_sdk_covers_fixture_spec(spec, actual_json):
    rows = diff_surface(expected_surface(public_subset(spec)), actual_surface_from_json(actual_json))
    assert rows == []


@pytest.mark.xfail(reason="SDK does not yet cover the full published spec", strict=False)
def test_sdk_covers_published_spec(published_spec, actual_json):
    rows = diff_surface(
        expected_surface(public_subset(published_spec)), actual_surface_from_json(actual_json)
    )
    assert rows == []


def test_gate_detects_field_stripped_from_actual(spec, actual_json):
    expected = expected_surface(public_subset(spec))
    actual = actual_surface_from_json(actual_json)
    present = sorted(expected.model_fields & actual.model_fields)
    victim = present[0]
    stripped = type(actual)(actual.model_fields - {victim}, actual.params)
    assert diff_surface(expected, stripped) == [f"missing field: {victim[0]}.{victim[1]}"]


def test_gate_detects_field_added_to_spec(spec, actual_json):
    mutated = json.loads(json.dumps(public_subset(spec)))
    mutated["components"]["schemas"]["ChatCompletionRequest"]["properties"]["zz_drift_probe"] = {
        "type": "string"
    }
    rows = diff_surface(expected_surface(mutated), actual_surface_from_json(actual_json))
    assert "missing field: ChatCompletionRequest.zz_drift_probe" in rows
