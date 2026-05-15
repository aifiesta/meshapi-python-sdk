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
    return get_env("MESHAPI_EMBEDDINGS_MODEL", MODEL)


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


# ---------------------------------------------------------------------------
# Helpers available as fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def unique_tag() -> str:
    """A stable unique tag for the entire test session (e.g. for file uploads)."""
    return f"ci-{int(time.time())}"
