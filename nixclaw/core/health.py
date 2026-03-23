"""Health check and monitoring utilities."""
from __future__ import annotations

import time
from typing import Any

from nixclaw.config import get_settings
from nixclaw.logger import get_logger

logger = get_logger(__name__)

_start_time = time.monotonic()


async def check_health() -> dict[str, Any]:
    """Run health checks on all system components."""
    results: dict[str, Any] = {
        "status": "ok",
        "uptime_seconds": round(time.monotonic() - _start_time, 1),
        "checks": {},
    }

    # LLM connectivity
    results["checks"]["llm"] = await _check_llm()

    # Database
    results["checks"]["database"] = await _check_database()

    # Telegram
    results["checks"]["telegram"] = _check_telegram()
    results["checks"]["telegram_log"] = _check_telegram_log()

    # Agent factory
    results["checks"]["agents"] = _check_agents()

    # Overall status
    failed = [k for k, v in results["checks"].items() if v.get("status") == "error"]
    if failed:
        results["status"] = "degraded"

    return results


async def _check_llm() -> dict:
    settings = get_settings()
    return {
        "status": "configured" if settings.llm.api_key else "not_configured",
        "model": settings.llm.model,
        "base_url": settings.llm.base_url,
    }


async def _check_database() -> dict:
    try:
        from nixclaw.storage.database import Database
        db = Database.get_instance()
        async with db.session() as session:
            await session.execute(
                __import__("sqlalchemy").text("SELECT 1")
            )
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def _check_telegram() -> dict:
    settings = get_settings()
    token = settings.telegram.bot_token
    enabled = bool(token and token != "your_bot_token_here")
    return {
        "status": "configured" if enabled else "not_configured",
        "user_count": len(settings.telegram.user_ids),
    }


def _check_telegram_log() -> dict:
    settings = get_settings()
    token = settings.telegram.bot_token_log
    enabled = bool(token and token not in ("", "your_log_bot_token_here"))
    return {"status": "configured" if enabled else "not_configured"}


def _check_agents() -> dict:
    try:
        from nixclaw.agents.agent_factory import AgentFactory
        factory = AgentFactory.get_instance()
        return factory.get_status()
    except Exception as e:
        return {"status": "error", "error": str(e)}
