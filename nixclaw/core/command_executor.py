from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from nixclaw.config import get_settings
from nixclaw.logger import get_logger
from nixclaw.storage.models import CommandExecution, CommandStatus
from nixclaw.tools.shell_executor import execute_shell_command

logger = get_logger(__name__)


class CommandExecutorService:
    """Background command execution service with queuing and concurrency limits.

    Commands are submitted and tracked by ID. Supports concurrent execution
    up to a configurable limit, with result retrieval by command ID.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._max_concurrent = settings.command_executor.max_concurrent
        self._semaphore = asyncio.Semaphore(self._max_concurrent)
        self._executions: dict[str, CommandExecution] = {}
        self._tasks: dict[str, asyncio.Task] = {}

    async def submit(
        self,
        command: str,
        working_dir: str = "",
        timeout: int = 0,
        agent_id: str | None = None,
        env_vars: dict[str, str] | None = None,
    ) -> str:
        """Submit a command for background execution. Returns the execution ID."""
        execution = CommandExecution(
            command=command,
            working_dir=working_dir or get_settings().command_executor.working_dir,
            timeout=timeout or get_settings().command_executor.timeout_default,
            environment=env_vars or {},
            agent_id=agent_id,
        )
        self._executions[execution.id] = execution

        task = asyncio.create_task(self._run(execution))
        self._tasks[execution.id] = task

        logger.info("Submitted command %s: %s", execution.id, command)
        return execution.id

    async def _run(self, execution: CommandExecution) -> None:
        """Execute a command with concurrency limiting."""
        async with self._semaphore:
            execution.status = CommandStatus.RUNNING
            execution.start_time = datetime.now(timezone.utc)

            env_str = ",".join(f"{k}={v}" for k, v in execution.environment.items())

            try:
                result = await execute_shell_command(
                    command=execution.command,
                    working_dir=execution.working_dir,
                    timeout=execution.timeout,
                    env_vars=env_str,
                )

                execution.end_time = datetime.now(timezone.utc)
                execution.duration = (
                    execution.end_time - execution.start_time
                ).total_seconds()

                # Parse result for exit code
                if result.startswith("BLOCKED"):
                    execution.status = CommandStatus.FAILED
                    execution.stderr = result
                elif result.startswith("TIMEOUT"):
                    execution.status = CommandStatus.TIMEOUT
                    execution.stderr = result
                elif result.startswith("Error:"):
                    execution.status = CommandStatus.FAILED
                    execution.stderr = result
                else:
                    execution.status = CommandStatus.COMPLETED
                    # Extract exit code from result
                    for line in result.splitlines():
                        if line.startswith("Exit Code:"):
                            try:
                                execution.exit_code = int(line.split(":")[1].strip())
                            except ValueError:
                                pass
                            break
                    execution.stdout = result

            except Exception as e:
                execution.status = CommandStatus.FAILED
                execution.stderr = str(e)
                execution.end_time = datetime.now(timezone.utc)
                logger.exception("Command %s failed: %s", execution.id, e)

    async def get_result(self, execution_id: str) -> CommandExecution | None:
        """Get execution result. Waits for completion if still running."""
        execution = self._executions.get(execution_id)
        if not execution:
            return None

        task = self._tasks.get(execution_id)
        if task and not task.done():
            await task

        return execution

    def get_status(self, execution_id: str) -> CommandStatus | None:
        execution = self._executions.get(execution_id)
        return execution.status if execution else None

    async def cancel(self, execution_id: str) -> bool:
        """Cancel a running command."""
        task = self._tasks.get(execution_id)
        if task and not task.done():
            task.cancel()
            execution = self._executions.get(execution_id)
            if execution:
                execution.status = CommandStatus.CANCELLED
            return True
        return False

    def get_all_executions(self) -> list[CommandExecution]:
        return list(self._executions.values())
