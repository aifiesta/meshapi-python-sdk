"""The X-MeshAPI-SDK version header must match the packaged version.

`_SDK_VERSION_VALUE` in meshapi/_http.py and `version` in pyproject.toml are two
places that have to agree, and they drifted: 0.1.12 shipped reporting
python/0.1.11. The Node SDK had the identical bug (1.0.4 reporting node/0.1.3),
which its guard test caught — this is that guard.
"""

import pathlib
import re

from meshapi._http import _SDK_VERSION_VALUE


def _pyproject_version() -> str:
    text = (pathlib.Path(__file__).resolve().parents[2] / "pyproject.toml").read_text()
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    assert match, "could not find version in pyproject.toml"
    return match.group(1)


def test_sdk_version_matches_pyproject():
    assert _SDK_VERSION_VALUE == f"python/{_pyproject_version()}", (
        "_SDK_VERSION_VALUE in meshapi/_http.py is out of sync with pyproject.toml"
    )
