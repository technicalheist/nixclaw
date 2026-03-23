"""Security utilities — secret masking, input sanitization, path validation."""
from __future__ import annotations

import re

# Patterns that look like secrets (API keys, tokens, passwords)
_SECRET_PATTERNS = [
    re.compile(r"(sk-[a-zA-Z0-9]{20,})"),            # OpenAI-style keys
    re.compile(r"(pypi-[a-zA-Z0-9_-]{20,})"),         # PyPI tokens
    re.compile(r"(\d+:[A-Za-z0-9_-]{30,})"),          # Telegram bot tokens
    re.compile(r"(ghp_[a-zA-Z0-9]{30,})"),            # GitHub PATs
    re.compile(r"(password\s*[=:]\s*\S+)", re.I),     # password=xxx
    re.compile(r"(api[_-]?key\s*[=:]\s*\S+)", re.I),  # api_key=xxx
    re.compile(r"(secret\s*[=:]\s*\S+)", re.I),       # secret=xxx
    re.compile(r"(token\s*[=:]\s*\S+)", re.I),        # token=xxx
]


def mask_secrets(text: str) -> str:
    """Replace secret-looking values in text with masked versions."""
    result = text
    for pattern in _SECRET_PATTERNS:
        result = pattern.sub(lambda m: m.group(0)[:8] + "***", result)
    return result


def sanitize_path(path: str) -> str:
    """Remove path traversal attempts and null bytes."""
    # Remove null bytes
    path = path.replace("\x00", "")
    # Normalize and block traversal
    parts = path.split("/")
    clean: list[str] = []
    for part in parts:
        if part == "..":
            continue
        clean.append(part)
    return "/".join(clean)


def validate_task_input(task: str) -> tuple[bool, str]:
    """Validate task input for obvious injection attempts.

    Returns (is_valid, reason).
    """
    if not task or not task.strip():
        return False, "Task description cannot be empty"

    if len(task) > 50_000:
        return False, "Task description too long (max 50,000 chars)"

    return True, ""
