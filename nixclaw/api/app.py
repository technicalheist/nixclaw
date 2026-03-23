"""FastAPI application for REST API task submission and status polling.

Start with: uvicorn nixclaw.api.app:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from nixclaw.api.routes import router
from nixclaw.logger import get_logger, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("NixClaw API starting up")
    yield
    logger.info("NixClaw API shutting down")


app = FastAPI(
    title="NixClaw API",
    description="REST API for the NixClaw multi-agent AI system",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(router, prefix="/api/v1")
