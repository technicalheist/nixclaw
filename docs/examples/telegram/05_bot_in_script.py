"""
Integrate Telegram notifications into your own Python scripts.

This shows a real-world pattern: run a long task with progress
updates sent to Telegram.
"""
import asyncio
import time

from nixclaw.integrations.telegram_bot import get_notifier
from nixclaw.integrations.telegram_log import get_log_bot


async def long_running_pipeline():
    """Simulate a data processing pipeline with Telegram updates."""
    notifier = get_notifier()
    log_bot = get_log_bot()

    task_id = "pipeline_001"
    steps = [
        ("Downloading data", 2),
        ("Validating schema", 1),
        ("Transforming records", 3),
        ("Loading to database", 2),
        ("Generating report", 1),
    ]

    # Notify start
    await notifier.notify_task_started(task_id, "Data Pipeline")
    log_bot.task_started(task_id, "Data Pipeline")

    for i, (step_name, duration) in enumerate(steps, 1):
        progress = f"[{i}/{len(steps)}] {step_name}..."
        print(progress)

        # Send progress to log bot (detailed)
        log_bot.task_output(task_id, progress)

        # Simulate work
        await asyncio.sleep(duration)

        # Send milestone update to primary bot (summary only)
        if i == len(steps):
            await notifier.notify_task_completed(
                task_id,
                "Data Pipeline",
                f"All {len(steps)} steps completed successfully.\n"
                f"Records processed: 10,542\n"
                f"Duration: {sum(d for _, d in steps)}s",
            )
            log_bot.task_completed(
                task_id,
                "Data Pipeline",
                f"Completed all {len(steps)} steps. 10,542 records processed.",
            )

    # Wait for log bot to flush
    time.sleep(2)
    print("Pipeline complete!")


if __name__ == "__main__":
    asyncio.run(long_running_pipeline())
