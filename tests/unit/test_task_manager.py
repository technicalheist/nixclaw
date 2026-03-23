"""Unit tests for TaskManager."""
import pytest

from nixclaw.core.task_manager import TaskManager
from nixclaw.storage.models import TaskStatus, TaskType


@pytest.fixture
def manager():
    return TaskManager()


def test_create_task(manager):
    task = manager.create_task(title="Test task", description="A test")
    assert task.title == "Test task"
    assert task.status == TaskStatus.PENDING
    assert task.id in [t.id for t in manager.get_all_tasks()]


def test_update_status(manager):
    task = manager.create_task(title="Test")
    manager.update_status(task.id, TaskStatus.IN_PROGRESS)
    assert manager.get_task(task.id).status == TaskStatus.IN_PROGRESS


def test_completed_sets_timestamp(manager):
    task = manager.create_task(title="Test")
    manager.update_status(task.id, TaskStatus.COMPLETED)
    assert manager.get_task(task.id).completed_at is not None


def test_parent_child_linking(manager):
    parent = manager.create_task(title="Parent")
    child = manager.create_task(title="Child", parent_task_id=parent.id)
    assert len(manager.get_subtasks(parent.id)) == 1
    assert manager.get_subtasks(parent.id)[0].id == child.id


def test_get_runnable_tasks(manager):
    t1 = manager.create_task(title="Task 1")
    t2 = manager.create_task(title="Task 2", dependencies=[t1.id])

    # t2 should not be runnable because t1 is not completed
    runnable = manager.get_runnable_tasks()
    assert t1.id in [t.id for t in runnable]
    assert t2.id not in [t.id for t in runnable]

    # Complete t1, now t2 should be runnable
    manager.update_status(t1.id, TaskStatus.COMPLETED)
    runnable = manager.get_runnable_tasks()
    assert t2.id in [t.id for t in runnable]


def test_summary(manager):
    manager.create_task(title="T1")
    manager.create_task(title="T2")
    t3 = manager.create_task(title="T3")
    manager.update_status(t3.id, TaskStatus.COMPLETED)

    summary = manager.get_summary()
    assert summary["pending"] == 2
    assert summary["completed"] == 1
