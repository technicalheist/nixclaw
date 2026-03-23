from __future__ import annotations

import os
from pathlib import Path


async def list_dir(
    directory: str, recursive: bool = False, file_type: str = ""
) -> str:
    """List contents of a directory. Optionally recursive and filtered by extension (e.g. '.py')."""
    path = Path(directory)
    if not path.exists():
        return f"Error: Directory not found: {directory}"
    if not path.is_dir():
        return f"Error: Not a directory: {directory}"

    try:
        entries: list[str] = []
        if recursive:
            for root, dirs, files in os.walk(path):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                rel = os.path.relpath(root, path)
                for name in sorted(files):
                    if file_type and not name.endswith(file_type):
                        continue
                    full = os.path.join(rel, name) if rel != "." else name
                    entries.append(full)
        else:
            for entry in sorted(path.iterdir()):
                if entry.name.startswith("."):
                    continue
                if file_type and entry.is_file() and not entry.name.endswith(file_type):
                    continue
                suffix = "/" if entry.is_dir() else ""
                entries.append(f"{entry.name}{suffix}")

        if not entries:
            return f"Directory {directory} is empty (or no matches for filter '{file_type}')"

        # Limit output
        if len(entries) > 500:
            shown = entries[:500]
            return "\n".join(shown) + f"\n\n... and {len(entries) - 500} more entries"
        return "\n".join(entries)

    except PermissionError:
        return f"Error: Permission denied: {directory}"


async def create_dir(directory: str) -> str:
    """Create a directory and all parent directories."""
    path = Path(directory)
    if path.exists():
        return f"Directory already exists: {directory}"
    try:
        path.mkdir(parents=True, exist_ok=True)
        return f"Successfully created directory: {directory}"
    except PermissionError:
        return f"Error: Permission denied: {directory}"
    except OSError as e:
        return f"Error creating directory: {e}"
