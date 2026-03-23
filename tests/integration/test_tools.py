"""Integration tests for tool functions - file ops, dir ops, search."""
import os
import tempfile

import pytest

from nixclaw.tools.file_operations import read_file, write_file, delete_file
from nixclaw.tools.directory_ops import list_dir, create_dir
from nixclaw.tools.search_tools import search_files, search_content


@pytest.fixture
def tmp_workspace():
    """Create a temporary workspace with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        with open(os.path.join(tmpdir, "hello.py"), "w") as f:
            f.write("print('hello world')\n")
        with open(os.path.join(tmpdir, "data.txt"), "w") as f:
            f.write("line 1\nline 2\nfoo bar baz\nline 4\n")

        sub = os.path.join(tmpdir, "subdir")
        os.makedirs(sub)
        with open(os.path.join(sub, "nested.py"), "w") as f:
            f.write("# nested file\nimport os\n")

        yield tmpdir


# ── File Operations ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_read_file(tmp_workspace):
    result = await read_file(os.path.join(tmp_workspace, "hello.py"))
    assert "hello world" in result


@pytest.mark.asyncio
async def test_read_file_line_range(tmp_workspace):
    result = await read_file(os.path.join(tmp_workspace, "data.txt"), start_line=2, end_line=3)
    assert "line 2" in result
    assert "line 1" not in result


@pytest.mark.asyncio
async def test_read_nonexistent():
    result = await read_file("/nonexistent/file.txt")
    assert "Error" in result


@pytest.mark.asyncio
async def test_write_and_read(tmp_workspace):
    path = os.path.join(tmp_workspace, "new_file.txt")
    await write_file(path, "test content")
    result = await read_file(path)
    assert "test content" in result


@pytest.mark.asyncio
async def test_write_append(tmp_workspace):
    path = os.path.join(tmp_workspace, "append.txt")
    await write_file(path, "first\n")
    await write_file(path, "second\n", append=True)
    result = await read_file(path)
    assert "first" in result
    assert "second" in result


@pytest.mark.asyncio
async def test_write_creates_dirs(tmp_workspace):
    path = os.path.join(tmp_workspace, "new", "deep", "dir", "file.txt")
    result = await write_file(path, "deep content")
    assert "Successfully" in result
    assert os.path.exists(path)


@pytest.mark.asyncio
async def test_delete_file(tmp_workspace):
    path = os.path.join(tmp_workspace, "hello.py")
    result = await delete_file(path)
    assert "Successfully" in result
    assert not os.path.exists(path)


@pytest.mark.asyncio
async def test_delete_nonexistent():
    result = await delete_file("/nonexistent/file.txt")
    assert "Error" in result


# ── Directory Operations ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_dir(tmp_workspace):
    result = await list_dir(tmp_workspace)
    assert "hello.py" in result
    assert "data.txt" in result
    assert "subdir/" in result


@pytest.mark.asyncio
async def test_list_dir_recursive(tmp_workspace):
    result = await list_dir(tmp_workspace, recursive=True)
    assert "nested.py" in result


@pytest.mark.asyncio
async def test_list_dir_filter(tmp_workspace):
    result = await list_dir(tmp_workspace, recursive=True, file_type=".py")
    assert "hello.py" in result
    assert "data.txt" not in result


@pytest.mark.asyncio
async def test_create_dir(tmp_workspace):
    path = os.path.join(tmp_workspace, "new_dir", "sub")
    result = await create_dir(path)
    assert "Successfully" in result
    assert os.path.isdir(path)


# ── Search Operations ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_files_by_pattern(tmp_workspace):
    result = await search_files(tmp_workspace, pattern="*.py")
    assert "hello.py" in result
    assert "nested.py" in result
    assert "data.txt" not in result


@pytest.mark.asyncio
async def test_search_content(tmp_workspace):
    result = await search_content(tmp_workspace, query="foo bar")
    assert "data.txt" in result
    assert "foo bar baz" in result


@pytest.mark.asyncio
async def test_search_content_regex(tmp_workspace):
    result = await search_content(tmp_workspace, query=r"line \d+")
    assert "data.txt" in result


@pytest.mark.asyncio
async def test_search_content_case_insensitive(tmp_workspace):
    result = await search_content(
        tmp_workspace, query="HELLO", case_sensitive=False, file_pattern="*.py"
    )
    assert "hello.py" in result


@pytest.mark.asyncio
async def test_search_no_matches(tmp_workspace):
    result = await search_content(tmp_workspace, query="xyz_not_found_abc")
    assert "No matches" in result
