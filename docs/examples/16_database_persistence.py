"""
Example 16: Database Persistence — Store and retrieve tasks from SQLite.

Tasks are automatically persisted to SQLite when task_persistence_enabled=true
in .env. You can also use the repository layer directly.
"""
import asyncio
import os
import tempfile

from nixclaw.storage.database import Database
from nixclaw.storage.repository import TaskRepository, CommandRepository
from nixclaw.storage.models import (
    Task, TaskStatus, TaskType,
    CommandExecution, CommandStatus,
)


async def main():
    # Create a temporary database for this example
    db_path = os.path.join(tempfile.gettempdir(), "nixclaw_example.db")
    Database.reset()
    db = Database(url=f"sqlite:///{db_path}")
    await db.init_tables()

    print("=== Task Persistence ===\n")

    async with db.session() as session:
        repo = TaskRepository(session)

        # Create and save tasks
        parent = Task(
            title="Build todo app",
            description="Full-stack todo application",
            type=TaskType.CODE,
            priority=1,
        )
        await repo.save(parent)
        print(f"Saved parent task: {parent.id}")

        child1 = Task(title="Create database schema", parent_task_id=parent.id, type=TaskType.CODE)
        child2 = Task(title="Build API endpoints", parent_task_id=parent.id, dependencies=[child1.id])
        child3 = Task(title="Write tests", parent_task_id=parent.id, dependencies=[child2.id])
        await repo.save(child1)
        await repo.save(child2)
        await repo.save(child3)

        # Update status
        await repo.update_status(child1.id, TaskStatus.COMPLETED)
        await repo.set_result(child1.id, "Created users, todos, tags tables")

        # Query tasks
        pending = await repo.get_by_status(TaskStatus.PENDING)
        print(f"Pending tasks: {[t.title for t in pending]}")

        completed = await repo.get_by_status(TaskStatus.COMPLETED)
        print(f"Completed tasks: {[t.title for t in completed]}")

        subtasks = await repo.get_subtasks(parent.id)
        print(f"Subtasks: {[t.title for t in subtasks]}")

        summary = await repo.get_summary()
        print(f"Summary: {summary}")

        # Load a task back
        loaded = await repo.get(parent.id)
        print(f"\nLoaded task: {loaded.title} (status: {loaded.status})")

    print("\n=== Command Persistence ===\n")

    async with db.session() as session:
        cmd_repo = CommandRepository(session)

        # Save a command execution
        cmd = CommandExecution(
            command="echo hello",
            working_dir="/tmp",
            status=CommandStatus.COMPLETED,
            exit_code=0,
            stdout="hello\n",
            duration=0.05,
        )
        await cmd_repo.save(cmd)
        print(f"Saved command: {cmd.id}")

        # Load it back
        loaded_cmd = await cmd_repo.get(cmd.id)
        print(f"Loaded command: {loaded_cmd.command} (exit={loaded_cmd.exit_code})")

    await db.close()
    Database.reset()

    # Cleanup
    os.unlink(db_path)
    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
