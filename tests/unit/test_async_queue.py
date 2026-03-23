"""Unit tests for AsyncTaskQueue."""
import pytest

from nixclaw.core.async_task_queue import AsyncTaskQueue


@pytest.fixture
def queue():
    AsyncTaskQueue.reset()
    q = AsyncTaskQueue.get_instance()
    yield q
    AsyncTaskQueue.reset()


def test_singleton():
    AsyncTaskQueue.reset()
    q1 = AsyncTaskQueue.get_instance()
    q2 = AsyncTaskQueue.get_instance()
    assert q1 is q2
    AsyncTaskQueue.reset()


def test_get_task_info_not_found(queue):
    info = queue.get_task_info("nonexistent")
    assert info is None


def test_get_summary_empty(queue):
    summary = queue.get_summary()
    assert isinstance(summary, dict)


def test_get_all_tasks_empty(queue):
    tasks = queue.get_all_tasks()
    assert isinstance(tasks, list)
    assert len(tasks) == 0


@pytest.mark.asyncio
async def test_cancel_not_running(queue):
    cancelled = await queue.cancel("nonexistent")
    assert cancelled is False
