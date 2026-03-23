"""API route definitions - task submission, status polling, agent management."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from nixclaw.api.schemas import TaskSubmitRequest, TaskSubmitResponse, TaskStatusResponse
from nixclaw.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["tasks"])


@router.post("/tasks", response_model=TaskSubmitResponse)
async def submit_task(request: TaskSubmitRequest) -> TaskSubmitResponse:
    """Submit a new task for autonomous background execution.

    Returns immediately with a task_id. Use GET /tasks/{task_id} to poll status.
    """
    from nixclaw.core.async_task_queue import get_task_queue

    queue = get_task_queue()
    task_id = await queue.submit(
        task_description=request.task,
        priority=request.priority,
        agent_profiles=request.agent_profiles or None,
        callback_url=request.callback_url,
    )

    logger.info("API task submitted: %s (id=%s)", request.task[:80], task_id)

    return TaskSubmitResponse(
        task_id=task_id,
        status="pending",
        message="Task submitted for background execution.",
    )


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    """Get the current status and result of a submitted task."""
    from nixclaw.core.async_task_queue import get_task_queue

    queue = get_task_queue()
    info = queue.get_task_info(task_id)

    if not info:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    return TaskStatusResponse(
        id=info["id"],
        status=info["status"],
        started_at=info.get("created_at"),
        result=info.get("result"),
        error=info.get("error"),
    )


@router.get("/tasks", response_model=list[dict])
async def list_tasks():
    """List all tasks in the queue."""
    from nixclaw.core.async_task_queue import get_task_queue

    queue = get_task_queue()
    return queue.get_all_tasks()


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str) -> dict:
    """Cancel a running task."""
    from nixclaw.core.async_task_queue import get_task_queue

    queue = get_task_queue()
    cancelled = await queue.cancel(task_id)

    if cancelled:
        return {"status": "cancelled", "task_id": task_id}
    raise HTTPException(status_code=400, detail="Task not running or already completed")


@router.get("/agents/status")
async def get_agents_status() -> dict:
    """Get status of all agents."""
    from nixclaw.agents.agent_factory import AgentFactory

    factory = AgentFactory.get_instance()
    return factory.get_status()


@router.get("/health")
async def health_check() -> dict:
    """Detailed health check of all system components."""
    from nixclaw.core.health import check_health

    return await check_health()
