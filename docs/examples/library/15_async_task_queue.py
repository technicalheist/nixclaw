"""
Example 15: Async Task Queue — Fire-and-forget background task execution.

Submit tasks that run in the background. Poll for status or
register webhook callbacks for completion.
"""
import asyncio

from nixclaw.core.async_task_queue import AsyncTaskQueue


async def main():
    # Reset singleton for clean example
    AsyncTaskQueue.reset()
    queue = AsyncTaskQueue.get_instance()

    # Submit a task — returns immediately with task_id
    print("=== Submitting Tasks ===")
    task_id = await queue.submit(
        task_description="List all Python files in /tmp",
        priority="high",
    )
    print(f"Task submitted: {task_id}")

    # Check status immediately (should be pending/in_progress)
    info = queue.get_task_info(task_id)
    print(f"Status: {info['status']}")

    # Submit another task with a webhook callback
    task_id_2 = await queue.submit(
        task_description="Check disk usage",
        priority="normal",
        callback_url="https://your-server.com/webhook",  # Will POST result here
    )
    print(f"Task 2 submitted: {task_id_2}")

    # List all tasks
    print(f"\nAll tasks: {queue.get_all_tasks()}")
    print(f"Summary: {queue.get_summary()}")

    # Cancel a task
    cancelled = await queue.cancel(task_id_2)
    print(f"\nCancelled task 2: {cancelled}")

    # Wait a bit for task 1 to complete
    print("\nWaiting for task 1...")
    await asyncio.sleep(5)

    # Check final status
    info = queue.get_task_info(task_id)
    if info:
        print(f"Final status: {info['status']}")
        if info.get("result"):
            print(f"Result: {info['result'][:200]}")
        if info.get("error"):
            print(f"Error: {info['error']}")

    AsyncTaskQueue.reset()


if __name__ == "__main__":
    asyncio.run(main())
