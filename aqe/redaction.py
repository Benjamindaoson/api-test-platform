from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any


REDACTED = "[REDACTED]"
LOCAL_PATH = "[LOCAL_PATH]"

_SENSITIVE_KEY_PARTS = ("authorization", "api_key", "apikey", "token", "secret", "password", "cookie")
_BEARER_TOKEN = re.compile(r"(?i)\bbearer\s+[a-z0-9._~+/=-]+")
_OPENAI_STYLE_KEY = re.compile(r"\b(?:sk|rk|pk)-[a-zA-Z0-9_-]{8,}\b")
_WINDOWS_PATH = re.compile(r"(?i)\b[a-z]:[\\/][^\s\"']+")


def redact_for_evidence(value: Any, *, secrets: Sequence[str] = ()) -> Any:
    """Return a JSON-compatible tree with credential and machine-path values removed."""
    normalized_secrets = tuple(secret for secret in secrets if secret)
    return _redact_value(value, normalized_secrets)


def _redact_value(value: Any, secrets: tuple[str, ...]) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): REDACTED if _is_sensitive_key(str(key)) else _redact_value(item, secrets)
            for key, item in value.items()
        }
    if isinstance(value, tuple | list):
        return [_redact_value(item, secrets) for item in value]
    if isinstance(value, str):
        return _redact_text(value, secrets)
    if value is None or isinstance(value, bool | int | float):
        return value
    return str(value)


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)


def _redact_text(value: str, secrets: tuple[str, ...]) -> str:
    redacted = value
    for secret in secrets:
        redacted = redacted.replace(secret, REDACTED)
    redacted = _BEARER_TOKEN.sub(f"Bearer {REDACTED}", redacted)
    redacted = _OPENAI_STYLE_KEY.sub(f"sk-{REDACTED}", redacted)
    return _WINDOWS_PATH.sub(_replace_windows_path, redacted)


def _replace_windows_path(match: re.Match[str]) -> str:
    normalized = match.group(0).replace("\\", "/")
    filename = normalized.rsplit("/", 1)[-1]
    return f"{LOCAL_PATH}/{filename}"
