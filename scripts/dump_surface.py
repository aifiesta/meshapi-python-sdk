"""Print the SDK's typed surface as JSON for the contract drift gate."""

from __future__ import annotations

import ast
import inspect
import json
import re
import sys
from pathlib import Path

from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
RESOURCES = ROOT / "meshapi" / "resources"
HTTP_VERBS = {"get", "post", "put", "patch", "delete", "get_bytes", "post_bytes", "post_multipart",
              "stream", "stream_json"}
VERB_TO_METHOD = {"get_bytes": "GET", "post_bytes": "POST", "post_multipart": "POST",
                  "stream": "POST", "stream_json": "POST"}

# SDK type name -> spec component name, where the two differ.
SPEC_NAMES = {
    "ModelInfo": "ModelOut",
    "ChatCompletionParams": "ChatCompletionRequest",
    "ChatMessage": "Message",
    "ChatCompletionChoice": "Choice",
    "CompareParams": "CompareRequest",
    "CreateBatchParams": "CreateBatchRequest",
    "CreateTemplateParams": "CreateTemplateRequest",
    "UpdateTemplateParams": "UpdateTemplateRequest",
    "EmbeddingsParams": "EmbeddingsRequest",
    "ImageGenerationParams": "ImageGenerationRequest",
    "ModerationParams": "ModerationRequest",
    "ResponsesParams": "ResponsesRequest",
    "RouterSelectParams": "RouterSelectRequest",
    "SpeechParams": "SpeechRequest",
    "VideoGenerationParams": "VideoGenerationRequest",
    "WebSearchParams": "WebSearchRequest",
    "TranscriptionParams": "Body_create_transcription",
    "AudioTranslationsParams": "Body_create_translation",
    "TranscriptionTranslateParams": "Body_create_transcription_translate",
    "RagFileStatus": "FileStatusResponse",
    "RagFileListResponse": "FileListResponse",
}


def _models() -> dict[str, type[BaseModel]]:
    import meshapi._types as types_mod

    return {
        name: obj
        for name, obj in vars(types_mod).items()
        if inspect.isclass(obj) and issubclass(obj, BaseModel) and obj is not BaseModel
        and obj.__module__ == types_mod.__name__
    }


def model_fields() -> list[list[str]]:
    rows: set[tuple[str, str]] = set()
    for name, cls in _models().items():
        names = [SPEC_NAMES.get(name, name)] if name in SPEC_NAMES else []
        for owner in [name, *names]:
            for field, info in cls.model_fields.items():
                rows.add((owner, field))
                if info.alias:
                    rows.add((owner, info.alias))
    return sorted([list(r) for r in rows])


def _fstring_path(node: ast.expr) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts = []
        for piece in node.values:
            if isinstance(piece, ast.Constant):
                parts.append(str(piece.value))
            else:
                ident = next((n.id for n in ast.walk(piece) if isinstance(n, ast.Name)
                              and n.id != "quote"), "param")
                parts.append("{" + ident + "}")
        return "".join(parts)
    return None


def _function_param_names(fn: ast.AST, models: dict[str, type[BaseModel]]) -> set[str]:
    names: set[str] = set()
    args = fn.args  # type: ignore[attr-defined]
    for arg in [*args.args, *args.kwonlyargs]:
        if arg.arg in ("self", "params", "body"):
            continue
        names.add(arg.arg)
    # Query/body models passed as `params` expose their fields as request params.
    for arg in args.args:
        text = ast.unparse(arg.annotation) if arg.annotation else ""
        for model_name, cls in models.items():
            if re.search(rf"\b{model_name}\b", text):
                names.update(cls.model_fields)
    for node in ast.walk(fn):
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) \
                and isinstance(node.slice.value, str):
            names.add(node.slice.value)
        if isinstance(node, ast.Dict):
            names.update(k.value for k in node.keys
                         if isinstance(k, ast.Constant) and isinstance(k.value, str))
    return names


def params() -> list[str]:
    from meshapi._http import _API_VERSION_HEADER

    models = _models()
    found: set[str] = set()
    for source in sorted(RESOURCES.glob("*.py")):
        tree = ast.parse(source.read_text())
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for call in ast.walk(fn):
                if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                        and call.func.attr in HTTP_VERBS and call.args):
                    continue
                path = _fstring_path(call.args[0])
                if path is None or not path.startswith("/"):
                    continue
                method = VERB_TO_METHOD.get(call.func.attr, call.func.attr.upper())
                scope = f"{method} {path}"
                names = _function_param_names(fn, models) | {_API_VERSION_HEADER}
                names.update(re.findall(r"\{(\w+)\}", path))
                found.update(f"{scope}:{n}" for n in names)
    return sorted(found)


def build_surface() -> dict:
    version = (ROOT / ".meshapi-spec-version").read_text().strip()
    return {
        "schema_version": "1",
        "spec_version": version,
        "model_fields": model_fields(),
        "params": params(),
    }


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    json.dump(build_surface(), sys.stdout, indent=1)
    sys.stdout.write("\n")
