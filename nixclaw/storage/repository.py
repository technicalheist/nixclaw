"""Repository layer for CRUD operations on tasks, agents, and commands.

Converts between Pydantic models (used in app code) and SQLAlchemy rows
(used for persistence).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from nixclaw.logger import get_logger
from nixclaw.storage.database import TaskRow, AgentRow, CommandRow
from nixclaw.storage.models import (
    AgentMetadata,
    AgentStatus,
    CommandExecution,
    CommandStatus,
    ResourceUsage,
    Task,
    TaskStatus,
    TaskType,
    TokenUsage,
)

logger = get_logger(__name__)


# ── Task Repository ─────────────────────────────────────────────────────────


def _task_to_row(task: Task) -> TaskRow:
    return TaskRow(
        id=task.id,
        parent_task_id=task.parent_task_id,
        title=task.title,
        description=task.description,
        type=task.type.value,
        status=task.status.value,
        priority=task.priority,
        estimated_time=task.estimated_time,
        required_tools=json.dumps(task.required_tools),
        assigned_agent_id=task.assigned_agent_id,
        result=str(task.result) if task.result is not None else None,
        error=task.error,
        created_at=task.created_at,
        completed_at=task.completed_at,
        dependencies=json.dumps(task.dependencies),
        estimated_tokens=task.estimated_tokens,
    )


def _row_to_task(row: TaskRow) -> Task:
    return Task(
        id=row.id,
        parent_task_id=row.parent_task_id,
        title=row.title,
        description=row.description or "",
        type=TaskType(row.type),
        status=TaskStatus(row.status),
        priority=row.priority,
        estimated_time=row.estimated_time or 0.0,
        required_tools=json.loads(row.required_tools or "[]"),
        assigned_agent_id=row.assigned_agent_id,
        result=row.result,
        error=row.error,
        created_at=row.created_at,
        completed_at=row.completed_at,
        dependencies=json.loads(row.dependencies or "[]"),
        estimated_tokens=row.estimated_tokens or 0,
    )


class TaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, task: Task) -> None:
        row = _task_to_row(task)
        await self._session.merge(row)
        await self._session.commit()

    async def get(self, task_id: str) -> Task | None:
        result = await self._session.execute(
            select(TaskRow).where(TaskRow.id == task_id)
        )
        row = result.scalar_one_or_none()
        return _row_to_task(row) if row else None

    async def get_by_status(self, status: TaskStatus) -> list[Task]:
        result = await self._session.execute(
            select(TaskRow).where(TaskRow.status == status.value).order_by(TaskRow.priority)
        )
        return [_row_to_task(row) for row in result.scalars().all()]

    async def get_subtasks(self, parent_id: str) -> list[Task]:
        result = await self._session.execute(
            select(TaskRow).where(TaskRow.parent_task_id == parent_id)
        )
        return [_row_to_task(row) for row in result.scalars().all()]

    async def update_status(self, task_id: str, status: TaskStatus) -> None:
        values: dict = {"status": status.value}
        if status == TaskStatus.COMPLETED:
            values["completed_at"] = datetime.now(timezone.utc)
        await self._session.execute(
            update(TaskRow).where(TaskRow.id == task_id).values(**values)
        )
        await self._session.commit()

    async def set_result(self, task_id: str, result: str) -> None:
        await self._session.execute(
            update(TaskRow).where(TaskRow.id == task_id).values(result=result)
        )
        await self._session.commit()

    async def set_error(self, task_id: str, error: str) -> None:
        await self._session.execute(
            update(TaskRow)
            .where(TaskRow.id == task_id)
            .values(error=error, status=TaskStatus.FAILED.value)
        )
        await self._session.commit()

    async def get_all(self) -> list[Task]:
        result = await self._session.execute(
            select(TaskRow).order_by(TaskRow.created_at.desc())
        )
        return [_row_to_task(row) for row in result.scalars().all()]

    async def get_summary(self) -> dict[str, int]:
        tasks = await self.get_all()
        summary: dict[str, int] = {}
        for t in tasks:
            summary[t.status.value] = summary.get(t.status.value, 0) + 1
        return summary


# ── Command Repository ──────────────────────────────────────────────────────


class CommandRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, cmd: CommandExecution) -> None:
        row = CommandRow(
            id=cmd.id,
            command=cmd.command,
            working_dir=cmd.working_dir,
            timeout=cmd.timeout,
            status=cmd.status.value,
            exit_code=cmd.exit_code,
            stdout=cmd.stdout,
            stderr=cmd.stderr,
            start_time=cmd.start_time,
            end_time=cmd.end_time,
            duration=cmd.duration,
            peak_memory_mb=cmd.resource_usage.peak_memory_mb,
            peak_cpu_percent=cmd.resource_usage.peak_cpu_percent,
            output_truncated=int(cmd.output_truncated),
            agent_id=cmd.agent_id,
            request_id=cmd.request_id,
        )
        await self._session.merge(row)
        await self._session.commit()

    async def get(self, cmd_id: str) -> CommandExecution | None:
        result = await self._session.execute(
            select(CommandRow).where(CommandRow.id == cmd_id)
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        return CommandExecution(
            id=row.id,
            command=row.command,
            working_dir=row.working_dir,
            timeout=row.timeout,
            status=CommandStatus(row.status),
            exit_code=row.exit_code,
            stdout=row.stdout or "",
            stderr=row.stderr or "",
            start_time=row.start_time,
            end_time=row.end_time,
            duration=row.duration or 0.0,
            resource_usage=ResourceUsage(
                peak_memory_mb=row.peak_memory_mb or 0.0,
                peak_cpu_percent=row.peak_cpu_percent or 0.0,
            ),
            output_truncated=bool(row.output_truncated),
            agent_id=row.agent_id,
            request_id=row.request_id or "",
        )

    async def get_by_status(self, status: CommandStatus) -> list[CommandExecution]:
        result = await self._session.execute(
            select(CommandRow).where(CommandRow.status == status.value)
        )
        rows = result.scalars().all()
        return [
            (await self.get(row.id))  # type: ignore
            for row in rows
            if row.id
        ]
