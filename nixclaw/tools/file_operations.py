from __future__ import annotations

import os
from pathlib import Path

import aiofiles


async def read_file(file_path: str, start_line: int = 0, end_line: int = 0) -> str:
    """Read file contents. Optionally specify start_line and end_line (1-based) to read a range."""
    path = Path(file_path)
    if not path.exists():
        return f"Error: File not found: {file_path}"
    if not path.is_file():
        return f"Error: Not a file: {file_path}"

    try:
        async with aiofiles.open(path, "r", encoding="utf-8", errors="replace") as f:
            content = await f.read()
    except PermissionError:
        return f"Error: Permission denied: {file_path}"

    if start_line > 0 or end_line > 0:
        lines = content.splitlines(keepends=True)
        start = max(0, start_line - 1)
        end = end_line if end_line > 0 else len(lines)
        content = "".join(lines[start:end])

    # Truncate very large outputs
    max_chars = 100_000
    if len(content) > max_chars:
        content = content[:max_chars] + f"\n\n... [truncated, total {len(content)} chars]"

    return content


async def write_file(file_path: str, content: str, append: bool = False) -> str:
    """Write or append content to a file. Creates parent directories if needed."""
    path = Path(file_path)

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        async with aiofiles.open(path, mode, encoding="utf-8") as f:
            await f.write(content)
        return f"Successfully {'appended to' if append else 'wrote'} {file_path} ({len(content)} chars)"
    except PermissionError:
        return f"Error: Permission denied: {file_path}"
    except OSError as e:
        return f"Error writing {file_path}: {e}"


async def delete_file(file_path: str) -> str:
    """Delete a file. Does not delete directories."""
    path = Path(file_path)
    if not path.exists():
        return f"Error: File not found: {file_path}"
    if not path.is_file():
        return f"Error: Not a file (use rmdir for directories): {file_path}"

    try:
        os.remove(path)
        return f"Successfully deleted {file_path}"
    except PermissionError:
        return f"Error: Permission denied: {file_path}"
    except OSError as e:
        return f"Error deleting {file_path}: {e}"
