"""Unit tests for database persistence layer."""
import asyncio
import os
import tempfile

import pytest

from nixclaw.storage.database import Database, Base
from nixclaw.storage.repository import TaskRepository, CommandRepository
from nixclaw.storage.models import (
    Task, TaskStatus, TaskType,
    CommandExecution, CommandStatus,
)


@pytest.fixture
async def db():
    """Create a temporary SQLite database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    Database.reset()
    database = Database(url=f"sqlite:///{db_path}")
    await database.init_tables()
    yield database
    await database.close()
    Database.reset()
    os.unlink(db_path)


@pytest.mark.asyncio
async def test_save_and_get_task(db):
    async with db.session() as session:
        repo = TaskRepository(session)

        task = Task(title="Test task", description="A test", type=TaskType.CODE)
        await repo.save(task)

        loaded = await repo.get(task.id)
        assert loaded is not None
        assert loaded.title == "Test task"
        assert loaded.type == TaskType.CODE
        assert loaded.status == TaskStatus.PENDING


@pytest.mark.asyncio
async def test_update_task_status(db):
    async with db.session() as session:
        repo = TaskRepository(session)

        task = Task(title="Status test")
        await repo.save(task)
        await repo.update_status(task.id, TaskStatus.COMPLETED)

        loaded = await repo.get(task.id)
        assert loaded.status == TaskStatus.COMPLETED
        assert loaded.completed_at is not None


@pytest.mark.asyncio
async def test_set_task_error(db):
    async with db.session() as session:
        repo = TaskRepository(session)

        task = Task(title="Error test")
        await repo.save(task)
        await repo.set_error(task.id, "Something went wrong")

        loaded = await repo.get(task.id)
        assert loaded.status == TaskStatus.FAILED
        assert loaded.error == "Something went wrong"


@pytest.mark.asyncio
async def test_get_tasks_by_status(db):
    async with db.session() as session:
        repo = TaskRepository(session)

        t1 = Task(title="Pending 1")
        t2 = Task(title="Pending 2")
        t3 = Task(title="Done", status=TaskStatus.COMPLETED)
        await repo.save(t1)
        await repo.save(t2)
        await repo.save(t3)

        pending = await repo.get_by_status(TaskStatus.PENDING)
        assert len(pending) == 2

        completed = await repo.get_by_status(TaskStatus.COMPLETED)
        assert len(completed) == 1


@pytest.mark.asyncio
async def test_get_subtasks(db):
    async with db.session() as session:
        repo = TaskRepository(session)

        parent = Task(title="Parent")
        child1 = Task(title="Child 1", parent_task_id=parent.id)
        child2 = Task(title="Child 2", parent_task_id=parent.id)
        await repo.save(parent)
        await repo.save(child1)
        await repo.save(child2)

        subtasks = await repo.get_subtasks(parent.id)
        assert len(subtasks) == 2


@pytest.mark.asyncio
async def test_task_with_dependencies(db):
    async with db.session() as session:
        repo = TaskRepository(session)

        t1 = Task(title="Step 1")
        t2 = Task(title="Step 2", dependencies=[t1.id])
        await repo.save(t1)
        await repo.save(t2)

        loaded = await repo.get(t2.id)
        assert t1.id in loaded.dependencies


@pytest.mark.asyncio
async def test_save_and_get_command(db):
    async with db.session() as session:
        repo = CommandRepository(session)

        cmd = CommandExecution(
            command="echo hello",
            working_dir="/tmp",
            status=CommandStatus.COMPLETED,
            exit_code=0,
            stdout="hello\n",
            duration=0.5,
        )
        await repo.save(cmd)

        loaded = await repo.get(cmd.id)
        assert loaded is not None
        assert loaded.command == "echo hello"
        assert loaded.exit_code == 0
        assert loaded.status == CommandStatus.COMPLETED


@pytest.mark.asyncio
async def test_task_summary(db):
    async with db.session() as session:
        repo = TaskRepository(session)

        await repo.save(Task(title="T1", status=TaskStatus.PENDING))
        await repo.save(Task(title="T2", status=TaskStatus.PENDING))
        await repo.save(Task(title="T3", status=TaskStatus.COMPLETED))
        await repo.save(Task(title="T4", status=TaskStatus.FAILED))

        summary = await repo.get_summary()
        assert summary["pending"] == 2
        assert summary["completed"] == 1
        assert summary["failed"] == 1
