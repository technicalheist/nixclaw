from __future__ import annotations

import fnmatch
import os
import re
from pathlib import Path


async def search_files(
    directory: str,
    pattern: str = "*",
    recursive: bool = True,
    max_results: int = 100,
) -> str:
    """Search for files by glob pattern (e.g. '*.py', 'test_*'). Returns matching file paths."""
    path = Path(directory)
    if not path.exists():
        return f"Error: Directory not found: {directory}"

    matches: list[str] = []
    try:
        if recursive:
            for root, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for name in files:
                    if fnmatch.fnmatch(name, pattern):
                        matches.append(os.path.join(root, name))
                        if len(matches) >= max_results:
                            break
                if len(matches) >= max_results:
                    break
        else:
            for entry in path.iterdir():
                if entry.is_file() and fnmatch.fnmatch(entry.name, pattern):
                    matches.append(str(entry))
                    if len(matches) >= max_results:
                        break
    except PermissionError:
        return f"Error: Permission denied: {directory}"

    if not matches:
        return f"No files matching '{pattern}' found in {directory}"

    result = "\n".join(matches)
    if len(matches) >= max_results:
        result += f"\n\n... (limited to {max_results} results)"
    return result


async def search_content(
    directory: str,
    query: str,
    file_pattern: str = "*",
    case_sensitive: bool = True,
    max_matches: int = 50,
    context_lines: int = 2,
) -> str:
    """Search file contents for a regex pattern. Returns matches with surrounding context lines."""
    path = Path(directory)
    if not path.exists():
        return f"Error: Directory not found: {directory}"

    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        regex = re.compile(query, flags)
    except re.error as e:
        return f"Error: Invalid regex '{query}': {e}"

    results: list[str] = []
    total_matches = 0

    try:
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for name in files:
                if not fnmatch.fnmatch(name, file_pattern):
                    continue
                filepath = os.path.join(root, name)
                try:
                    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                        lines = f.readlines()
                except (PermissionError, OSError):
                    continue

                for i, line in enumerate(lines):
                    if regex.search(line):
                        total_matches += 1
                        start = max(0, i - context_lines)
                        end = min(len(lines), i + context_lines + 1)
                        context = []
                        for j in range(start, end):
                            marker = ">>>" if j == i else "   "
                            context.append(f"  {marker} {j + 1}: {lines[j].rstrip()}")
                        results.append(f"{filepath}:\n" + "\n".join(context))

                        if total_matches >= max_matches:
                            break
                if total_matches >= max_matches:
                    break
            if total_matches >= max_matches:
                break
    except PermissionError:
        return f"Error: Permission denied: {directory}"

    if not results:
        return f"No matches for '{query}' in {directory}"

    output = f"Found {total_matches} match(es):\n\n" + "\n\n".join(results)
    if total_matches >= max_matches:
        output += f"\n\n... (limited to {max_matches} matches)"
    return output
