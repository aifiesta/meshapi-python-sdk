import importlib.util
import json
import subprocess
import sys
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
SPEC_PATH = ROOT / "contract" / "openapi.public.json"
BASELINE = ROOT / "contract-baseline.json"
SPEC_VERSION = (ROOT / ".meshapi-spec-version").read_text().strip()


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
    return json.loads(SPEC_PATH.read_text())


def _gate(tmp_path, spec, actual):
    spec_file, actual_file = tmp_path / "spec.json", tmp_path / "actual.json"
    spec_file.write_text(json.dumps(spec))
    actual_file.write_text(json.dumps(actual))
    return subprocess.run(
        [sys.executable, "-m", "meshapi_contract.gate", "--spec", str(spec_file),
         "--actual", str(actual_file), "--spec-version", SPEC_VERSION,
         "--baseline", str(BASELINE)],
        capture_output=True, text=True,
    )


def test_envelope_matches_gate_contract(actual_json):
    assert actual_json["schema_version"] == "1"
    assert actual_json["spec_version"] == SPEC_VERSION
    assert actual_json["model_fields"] and actual_json["params"]


def test_no_new_drift_beyond_baseline(tmp_path, spec, actual_json):
    result = _gate(tmp_path, spec, actual_json)
    assert result.returncode == 0, result.stdout


def test_new_spec_field_fails_gate(tmp_path, spec, actual_json):
    mutated = json.loads(json.dumps(spec))
    mutated["components"]["schemas"]["ChatCompletionRequest"]["properties"]["zz_drift_probe"] = {
        "type": "string"
    }
    result = _gate(tmp_path, mutated, actual_json)
    assert result.returncode == 1
    assert "missing field: ChatCompletionRequest.zz_drift_probe" in result.stdout


def test_baseline_has_no_stale_entries(spec, actual_json):
    rows = set(diff_surface(expected_surface(public_subset(spec)), actual_surface_from_json(actual_json)))
    stale = set(json.loads(BASELINE.read_text())["allow"]) - rows
    assert not stale, sorted(stale)


def test_new_spec_param_fails_gate(tmp_path, spec, actual_json):
    mutated = json.loads(json.dumps(spec))
    mutated["paths"]["/v1/chat/completions"]["post"].setdefault("parameters", []).append(
        {"name": "newparam", "in": "query", "schema": {"type": "string"}}
    )
    result = _gate(tmp_path, mutated, actual_json)
    assert result.returncode == 1
    assert "missing param: POST /v1/chat/completions:newparam" in result.stdout
