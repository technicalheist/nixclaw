"""API request/response schemas.

Phase 4 implementation. These Pydantic models define the API contract
for task submission and status polling.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TaskSubmitRequest(BaseModel):
    task: str = Field(..., description="Task description")
    priority: str = Field(default="normal", description="Priority: high, normal, low")
    callback_url: str | None = Field(default=None, description="Webhook URL for completion callback")
    agent_profiles: list[str] = Field(default_factory=list, description="Specific agent profiles to use")


class TaskSubmitResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    id: str
    status: str
    progress: int = 0
    current_subtask: str | None = None
    started_at: datetime | None = None
    estimated_completion: datetime | None = None
    logs: list[str] = Field(default_factory=list)
    intermediate_results: dict[str, Any] = Field(default_factory=dict)
    result: Any = None
    error: str | None = None
