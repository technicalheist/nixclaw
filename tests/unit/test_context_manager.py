"""Unit tests for ContextManager."""
import pytest

from nixclaw.core.context_manager import ContextManager


def test_add_and_get():
    cm = ContextManager(max_tokens=10000)
    cm.add("agent1", "Hello world")
    assert "Hello world" in cm.get_context()
    assert cm.entry_count == 1


def test_token_pruning():
    cm = ContextManager(max_tokens=50)
    cm.add("a", "x" * 200)  # ~50 tokens
    cm.add("b", "y" * 200)  # another ~50 tokens, should prune first

    ctx = cm.get_context()
    assert "y" in ctx
    # First entry should have been pruned
    assert cm.entry_count <= 2


def test_get_context_for_agent():
    cm = ContextManager(max_tokens=10000)
    cm.add("agent1", "msg from 1")
    cm.add("agent2", "msg from 2")

    ctx = cm.get_context_for_agent("agent1")
    assert "msg from 2" in ctx
    assert "msg from 1" not in ctx


def test_clear():
    cm = ContextManager(max_tokens=10000)
    cm.add("a", "test")
    cm.clear()
    assert cm.entry_count == 0
    assert cm.token_usage == 0
