"""
Example 06: Task Manager — Track tasks with dependencies and status.

The TaskManager handles task DAGs: create tasks, set dependencies,
track status, and find which tasks are ready to run.
"""
from nixclaw import TaskManager
from nixclaw.storage.models import TaskStatus, TaskType


def main():
    tm = TaskManager(persist=False)  # In-memory only for this example

    # Create a parent task
    parent = tm.create_task(
        title="Build user authentication",
        description="Implement full auth system",
        type=TaskType.CODE,
        priority=1,
    )

    # Create subtasks with dependencies
    design = tm.create_task(
        title="Design auth schema",
        type=TaskType.ANALYSIS,
        parent_task_id=parent.id,
    )

    implement = tm.create_task(
        title="Implement login/register endpoints",
        type=TaskType.CODE,
        parent_task_id=parent.id,
        dependencies=[design.id],  # Can't start until design is done
    )

    test = tm.create_task(
        title="Write auth tests",
        type=TaskType.CODE,
        parent_task_id=parent.id,
        dependencies=[implement.id],  # Can't start until implementation is done
    )

    # Check what's runnable
    print("Initial runnable tasks:")
    for t in tm.get_runnable_tasks():
        print(f"  - {t.title} (id={t.id})")

    # Complete the design task
    tm.update_status(design.id, TaskStatus.COMPLETED)
    print("\nAfter completing design:")
    for t in tm.get_runnable_tasks():
        print(f"  - {t.title} (id={t.id})")

    # Complete the implementation
    tm.update_status(implement.id, TaskStatus.COMPLETED)
    print("\nAfter completing implementation:")
    for t in tm.get_runnable_tasks():
        print(f"  - {t.title} (id={t.id})")

    # Summary
    print(f"\nTask summary: {tm.get_summary()}")
    print(f"Subtasks of parent: {[t.title for t in tm.get_subtasks(parent.id)]}")


if __name__ == "__main__":
    main()
