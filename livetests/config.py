from __future__ import annotations

import os
import sys
from pathlib import Path


SDK_ROOT = Path(__file__).resolve().parents[1]
if str(SDK_ROOT) not in sys.path:
    sys.path.insert(0, str(SDK_ROOT))


def _load_shared_env() -> dict[str, str]:
    env_path = Path(__file__).resolve().parents[1] / ".env.livetest"
    values: dict[str, str] = {}
    if not env_path.exists():
        return values

    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


_SHARED_ENV = _load_shared_env()

BASE_URL = os.getenv("MESHAPI_BASE_URL") or _SHARED_ENV.get("MESHAPI_BASE_URL", "http://localhost:8000")
TOKEN = os.getenv("MESHAPI_TOKEN") or _SHARED_ENV.get("MESHAPI_TOKEN", "rsk_01KN96KQWDPF2X1E9CP8567JY4")
MODEL = os.getenv("MESHAPI_MODEL") or _SHARED_ENV.get("MESHAPI_MODEL", "openai/gpt-4o-mini")


def get_env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name) or _SHARED_ENV.get(name, default)
