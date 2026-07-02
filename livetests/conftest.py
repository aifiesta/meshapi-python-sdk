"""
pytest conftest for the MeshAPI Python live-test suite.

Registers shared fixtures so every test_*.py file can import
`client`, `model`, and helpers directly without touching config.py.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Make sure the local SDK is importable even when running via pytest from CI
# (the requirements.txt already does `pip install -e ../meshapi-python-sdk`,
#  but this is a safety net for non-venv runs).
# ---------------------------------------------------------------------------
SDK_ROOT = Path(__file__).resolve().parents[1]
if str(SDK_ROOT) not in sys.path:
    sys.path.insert(0, str(SDK_ROOT))

# ---------------------------------------------------------------------------
# Import after sys.path is set up
# ---------------------------------------------------------------------------
from config import BASE_URL, TOKEN, MODEL, get_env  # noqa: E402
from meshapi import MeshAPI  # noqa: E402


# ---------------------------------------------------------------------------
# Strict-mode preflight (pre-hackathon gate)
# ---------------------------------------------------------------------------
#
# Several feature tests skip-by-default when an env var is unset (image gen,
# vision, audio in/out, video). A skipped test reads as "passed" — so a green
# run can mean almost nothing ran. Set MESHAPI_STRICT_LIVETESTS=1 in the
# pre-hackathon gate: the run fails fast unless every optional-feature env var
# is present, forcing those tests to actually execute. See .env.livetest.example.

# Env vars whose absence turns a real feature test into a silent skip.
STRICT_REQUIRED_ENV = [
    "MESHAPI_IMAGE_GEN_MODEL",
    "MESHAPI_IMAGE_URL",
    "MESHAPI_INPUT_AUDIO_B64",
    "MESHAPI_AUDIO_OUT_MODEL",
    "MESHAPI_VIDEO_GEN_MODEL",
]


def _strict_mode() -> bool:
    return (os.getenv("MESHAPI_STRICT_LIVETESTS") or "").lower() in ("1", "true", "yes")


def pytest_configure(config: "pytest.Config") -> None:
    if not _strict_mode():
        return
    missing = [name for name in STRICT_REQUIRED_ENV if not get_env(name)]
    if missing:
        pytest.exit(
            "MESHAPI_STRICT_LIVETESTS is set but these env vars are unset, so their "
            "feature tests would silently skip:\n  - " + "\n  - ".join(missing) + "\n"
            "Set them (see .env.livetest.example) or unset MESHAPI_STRICT_LIVETESTS.",
            returncode=1,
        )


# ---------------------------------------------------------------------------
# Session-scoped shared client fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def client() -> MeshAPI:
    """Return a single MeshAPI client reused for all tests in the session."""
    return MeshAPI(base_url=BASE_URL, token=TOKEN)


@pytest.fixture(scope="session")
def model() -> str:
    return MODEL


@pytest.fixture(scope="session")
def embeddings_model() -> str:
    return get_env("MESHAPI_EMBEDDINGS_MODEL", "openai/text-embedding-3-small")



@pytest.fixture(scope="session")
def second_model() -> str:
    """A second distinct model for compare tests. Defaults to a different model from MODEL."""
    default = "anthropic/claude-haiku-4.5" if MODEL == "openai/gpt-4o-mini" else "openai/gpt-4o-mini"
    return get_env("MESHAPI_SECOND_MODEL", default)


@pytest.fixture(scope="session")
def image_url() -> str | None:
    return get_env("MESHAPI_IMAGE_URL")


@pytest.fixture(scope="session")
def audio_b64() -> str | None:
    return get_env("MESHAPI_INPUT_AUDIO_B64")


@pytest.fixture(scope="session")
def audio_format() -> str:
    return get_env("MESHAPI_INPUT_AUDIO_FORMAT", "wav")


@pytest.fixture(scope="session")
def audio_out_model() -> str | None:
    return get_env("MESHAPI_AUDIO_OUT_MODEL")


@pytest.fixture(scope="session")
def image_gen_model() -> str | None:
    return get_env("MESHAPI_IMAGE_GEN_MODEL")


@pytest.fixture(scope="session")
def realtime_model() -> str | None:
    return get_env("MESHAPI_REALTIME_MODEL")


# ---------------------------------------------------------------------------
# Helpers available as fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def unique_tag() -> str:
    """A stable unique tag for the entire test session (e.g. for file uploads)."""
    return f"ci-{int(time.time())}"
