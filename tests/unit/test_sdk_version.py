"""The advertised SDK version must match the packaged version.

Three places used to carry the version independently — ``pyproject.toml``,
``meshapi.__version__`` and the ``X-MeshAPI-SDK`` header constant — and they
drifted: 0.1.12 shipped reporting ``python/0.1.11`` in the header and
``0.1.11`` from ``__version__``, so clients and server telemetry disagreed about
which release was talking.

Two of the three are now *derived* from ``meshapi._version``, which is drift
these tests cannot even express. What remains is the one pair a test has to
cover: that literal against ``pyproject.toml``.

The sibling SDKs have hit the same bug — meshapi-node-sdk 1.0.4 reported
node/0.1.3 — so each now carries a guard of this shape.
"""

import pathlib
import re

import meshapi
from meshapi._http import _SDK_VERSION_VALUE
from meshapi._version import __version__


def _pyproject_version() -> str:
    text = (pathlib.Path(__file__).resolve().parents[2] / "pyproject.toml").read_text()
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    assert match, "could not find version in pyproject.toml"
    return match.group(1)


def test_version_matches_pyproject():
    assert __version__ == _pyproject_version(), (
        "meshapi/_version.py is out of sync with pyproject.toml — bump both together"
    )


def test_header_derives_from_the_single_source():
    assert _SDK_VERSION_VALUE == f"python/{__version__}"


def test_public_version_derives_from_the_single_source():
    """`meshapi.__version__` is what users and bug reports quote."""
    assert meshapi.__version__ == __version__
