"""Single source of truth for the package version.

Three places used to carry it independently — ``pyproject.toml``,
``meshapi.__version__`` and the ``X-MeshAPI-SDK`` header constant — and they
drifted: 0.1.12 shipped reporting ``python/0.1.11`` in the header and
``0.1.11`` from ``__version__``. Both the header and ``__version__`` now derive
from here, so only this literal and ``pyproject.toml`` can disagree, and
``tests/unit/test_sdk_version.py`` asserts they do not.

Kept in its own module rather than in ``__init__`` so ``_http`` can import it
without a circular import.
"""

__version__ = "0.1.12"
