# Testing the RouterSVC Python SDK

This document describes the different types of tests available in the Python SDK and how to run them.

## 1. Environment Setup

Ensure you have a virtual environment set up and all development dependencies installed:

```bash
# Create and activate venv
python -m venv .venv
source .venv/bin/activate

# Install the SDK in editable mode with dev dependencies
pip install -e ".[dev]"
```

## 2. Test Types

### 2.1 Unit Tests
Located in `tests/unit/`. These tests verify individual components (like URL building, error mapping, and SSE parsing) in isolation. They are fast and do not require any external services.

**To run unit tests:**
```bash
pytest tests/unit/ -v
```

### 2.2 Contract Tests
Located in `tests/contract/`. These tests ensure that our internal Pydantic models correctly parse and validate JSON responses that follow the RouterSVC API schema. They use local JSON fixtures and do not require a network.

**To run contract tests:**
```bash
pytest tests/contract/ -v
```

### 2.3 Integration Tests
Located in `tests/integration/`. These tests perform real HTTP requests against a running RouterSVC instance. They verify that the SDK correctly interacts with all endpoints (Chat, Models, Templates).

**Prerequisites:**
- A running RouterSVC instance (default: `http://localhost:8000`).
- A valid Data-plane API key (`rsk_...`).

**Environment Variables:**
| Variable | Description | Default |
| :--- | :--- | :--- |
| `ROUTERSVC_BASE_URL` | The URL of the API gateway | `http://localhost:8000` |
| `ROUTERSVC_TOKEN` | A valid API key | (preset in code for dev) |

**To run integration tests:**
```bash
ROUTERSVC_BASE_URL=http://localhost:8000 ROUTERSVC_TOKEN=your_rsk_key pytest tests/integration/ -v
```

---

## 3. Live Tests (Standalone)

Located in the separate `routersvc-python-livetest/` directory. These are standalone scripts designed for quick, manual verification of the SDK against a live server.

**To run live tests:**
1. Navigate to the directory: `cd ../routersvc-python-livetest`
2. Configure the server and token in `config.py`.
3. Run individual scripts:
```bash
python test_models.py
python test_templates.py
python test_chat.py
python test_stream.py
```

## 4. Running All Local Tests

To run all tests that do NOT require a network:
```bash
pytest tests/unit/ tests/contract/ -v
```
