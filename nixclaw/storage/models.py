from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


# ── Task Models ──────────────────────────────────────────────────────────────


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class TaskType(str, Enum):
    CODE = "code"
    ANALYSIS = "analysis"
    RESEARCH = "research"
    SYSTEM = "system"
    DEBUG = "debug"
    GENERAL = "general"


class Task(BaseModel):
    id: str = Field(default_factory=_new_id)
    parent_task_id: str | None = None
    title: str
    description: str = ""
    type: TaskType = TaskType.GENERAL
    subtasks: list[Task] = Field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 5
    estimated_time: float = 0.0
    required_tools: list[str] = Field(default_factory=list)
    assigned_agent_id: str | None = None
    result: Any = None
    error: str | None = None
    created_at: datetime = Field(default_factory=_utc_now)
    completed_at: datetime | None = None
    dependencies: list[str] = Field(default_factory=list)
    estimated_tokens: int = 0


# ── Agent Models ─────────────────────────────────────────────────────────────


class AgentStatus(str, Enum):
    IDLE = "idle"
    BUSY = "busy"
    FAILED = "failed"
    TERMINATED = "terminated"


class TokenUsage(BaseModel):
    total: int = 0
    used: int = 0
    remaining: int = 0


class AgentMetadata(BaseModel):
    id: str = Field(default_factory=_new_id)
    profile: str = "general"
    status: AgentStatus = AgentStatus.IDLE
    assigned_tasks: list[str] = Field(default_factory=list)
    current_task_id: str | None = None
    tools_available: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utc_now)
    last_activity: datetime = Field(default_factory=_utc_now)
    error_count: int = 0
    token_usage: TokenUsage = Field(default_factory=TokenUsage)


# ── Command Execution Models ────────────────────────────────────────────────


class CommandStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResourceUsage(BaseModel):
    peak_memory_mb: float = 0.0
    peak_cpu_percent: float = 0.0
    process_count: int = 0


class CommandExecution(BaseModel):
    id: str = Field(default_factory=_new_id)
    command: str
    working_dir: str = "/tmp/agent_workdir"
    timeout: int = 300
    environment: dict[str, str] = Field(default_factory=dict)
    status: CommandStatus = CommandStatus.PENDING
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    start_time: datetime | None = None
    end_time: datetime | None = None
    duration: float = 0.0
    resource_usage: ResourceUsage = Field(default_factory=ResourceUsage)
    output_truncated: bool = False
    max_output_size_bytes: int = 10485760
    agent_id: str | None = None
    request_id: str = Field(default_factory=_new_id)


# ── Task Breakdown Request/Response ─────────────────────────────────────────


class TaskBreakdownResult(BaseModel):
    parent_task: Task
    subtasks: list[Task]
    execution_order: list[list[str]] = Field(default_factory=list)
