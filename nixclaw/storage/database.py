"""Async SQLite database layer using SQLAlchemy + aiosqlite.

Provides task, agent, and command execution persistence across restarts.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from nixclaw.config import get_settings
from nixclaw.logger import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    pass


# ── SQLAlchemy ORM Models ───────────────────────────────────────────────────


class TaskRow(Base):
    __tablename__ = "tasks"

    id = Column(String(12), primary_key=True)
    parent_task_id = Column(String(12), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    type = Column(String(20), default="general")
    status = Column(String(20), default="pending", index=True)
    priority = Column(Integer, default=5)
    estimated_time = Column(Float, default=0.0)
    required_tools = Column(Text, default="[]")  # JSON list
    assigned_agent_id = Column(String(12), nullable=True)
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    dependencies = Column(Text, default="[]")  # JSON list
    estimated_tokens = Column(Integer, default=0)


class AgentRow(Base):
    __tablename__ = "agents"

    id = Column(String(12), primary_key=True)
    profile = Column(String(50), default="general")
    status = Column(String(20), default="idle", index=True)
    assigned_tasks = Column(Text, default="[]")  # JSON list
    current_task_id = Column(String(12), nullable=True)
    tools_available = Column(Text, default="[]")  # JSON list
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_activity = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    error_count = Column(Integer, default=0)
    token_total = Column(Integer, default=0)
    token_used = Column(Integer, default=0)


class CommandRow(Base):
    __tablename__ = "commands"

    id = Column(String(12), primary_key=True)
    command = Column(Text, nullable=False)
    working_dir = Column(String(512), default="/tmp/agent_workdir")
    timeout = Column(Integer, default=300)
    status = Column(String(20), default="pending", index=True)
    exit_code = Column(Integer, nullable=True)
    stdout = Column(Text, default="")
    stderr = Column(Text, default="")
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    duration = Column(Float, default=0.0)
    peak_memory_mb = Column(Float, default=0.0)
    peak_cpu_percent = Column(Float, default=0.0)
    output_truncated = Column(Integer, default=0)  # bool as int
    agent_id = Column(String(12), nullable=True)
    request_id = Column(String(12), nullable=True)


# ── Database Connection ─────────────────────────────────────────────────────


class Database:
    """Async database connection manager."""

    _instance: Database | None = None

    def __init__(self, url: str | None = None) -> None:
        settings = get_settings()
        raw_url = url or settings.storage.database_url

        # Convert sqlite:/// to sqlite+aiosqlite:///
        if raw_url.startswith("sqlite:///"):
            db_path = raw_url.replace("sqlite:///", "")
            if db_path.startswith("./"):
                db_path = str(Path(db_path).resolve())
            async_url = f"sqlite+aiosqlite:///{db_path}"
        else:
            async_url = raw_url

        self._engine = create_async_engine(async_url, echo=False)
        self._session_factory = async_sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False
        )
        logger.info("Database initialized: %s", async_url)

    @classmethod
    def get_instance(cls, url: str | None = None) -> Database:
        if cls._instance is None:
            cls._instance = cls(url)
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        cls._instance = None

    async def init_tables(self) -> None:
        """Create all tables if they don't exist."""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized")

    def session(self) -> AsyncSession:
        """Get a new async session."""
        return self._session_factory()

    async def close(self) -> None:
        await self._engine.dispose()
        logger.info("Database connection closed")
