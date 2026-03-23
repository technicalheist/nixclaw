from __future__ import annotations

import os
from pathlib import Path
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load .env from project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default)


def _env_int(key: str, default: int = 0) -> int:
    return int(os.getenv(key, str(default)))


def _env_float(key: str, default: float = 0.0) -> float:
    return float(os.getenv(key, str(default)))


def _env_bool(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).lower() in ("true", "1", "yes")


def _env_list(key: str, default: str = "") -> list[str]:
    raw = os.getenv(key, default)
    return [x.strip() for x in raw.split(",") if x.strip()] if raw else []


class LLMConfig(BaseModel):
    model: str = Field(default_factory=lambda: _env("LLM_MODEL", "qwen3.5-plus"))
    api_key: str = Field(default_factory=lambda: _env("LLM_API_KEY"))
    base_url: str = Field(default_factory=lambda: _env("LLM_BASE_URL", "https://llm.shivrajan.com/v1"))
    temperature: float = Field(default_factory=lambda: _env_float("LLM_TEMPERATURE", 0.7))
    max_tokens: int = Field(default_factory=lambda: _env_int("LLM_MAX_TOKENS", 4096))
    request_timeout: int = Field(default_factory=lambda: _env_int("LLM_REQUEST_TIMEOUT", 60))


class TelegramConfig(BaseModel):
    bot_token: str = Field(default_factory=lambda: _env("TELEGRAM_BOT_TOKEN"))
    bot_token_log: str = Field(default_factory=lambda: _env("TELEGRAM_BOT_TOKEN_LOG"))
    user_ids: list[str] = Field(default_factory=lambda: _env_list("TELEGRAM_USER_IDS"))
    log_level: str = Field(default_factory=lambda: _env("TELEGRAM_LOG_LEVEL", "info"))
    message_rate_limit: int = Field(default_factory=lambda: _env_int("TELEGRAM_MESSAGE_RATE_LIMIT", 10))
    enable_notifications: bool = Field(default_factory=lambda: _env_bool("TELEGRAM_ENABLE_NOTIFICATIONS", True))


class AgentConfig(BaseModel):
    max_concurrent_agents: int = Field(default_factory=lambda: _env_int("AGENT_MAX_CONCURRENT_AGENTS", 10))
    task_timeout_default: int = Field(default_factory=lambda: _env_int("AGENT_TASK_TIMEOUT_DEFAULT", 3600))
    memory_context_limit: int = Field(default_factory=lambda: _env_int("AGENT_MEMORY_CONTEXT_LIMIT", 8000))
    max_retries: int = Field(default_factory=lambda: _env_int("AGENT_MAX_RETRIES", 3))
    retry_backoff_factor: int = Field(default_factory=lambda: _env_int("AGENT_RETRY_BACKOFF_FACTOR", 2))
    enable_reflection: bool = Field(default_factory=lambda: _env_bool("AGENT_ENABLE_REFLECTION", True))
    streaming_enabled: bool = Field(default_factory=lambda: _env_bool("AGENT_STREAMING_ENABLED", False))


class CommandExecutorConfig(BaseModel):
    timeout_default: int = Field(default_factory=lambda: _env_int("COMMAND_EXECUTOR_TIMEOUT_DEFAULT", 300))
    max_output_size: int = Field(default_factory=lambda: _env_int("COMMAND_EXECUTOR_MAX_OUTPUT_SIZE", 10485760))
    memory_limit_mb: int = Field(default_factory=lambda: _env_int("COMMAND_EXECUTOR_MEMORY_LIMIT", 512))
    cpu_shares: int = Field(default_factory=lambda: _env_int("COMMAND_EXECUTOR_CPU_SHARES", 1024))
    max_concurrent: int = Field(default_factory=lambda: _env_int("COMMAND_EXECUTOR_MAX_CONCURRENT", 5))
    enable_sandbox: bool = Field(default_factory=lambda: _env_bool("COMMAND_EXECUTOR_ENABLE_SANDBOX", True))
    dangerous_commands_blacklist: list[str] = Field(
        default_factory=lambda: _env_list("COMMAND_EXECUTOR_DANGEROUS_COMMANDS_BLACKLIST", "rm -rf /,: () { : | : & };:")
    )
    working_dir: str = Field(
        default_factory=lambda: _env("COMMAND_EXECUTOR_WORKING_DIR", "/tmp/agent_workdir")
    )


class StorageConfig(BaseModel):
    database_url: str = Field(default_factory=lambda: _env("DATABASE_URL", "sqlite:///./agent_tasks.db"))
    redis_url: str = Field(default_factory=lambda: _env("REDIS_URL", "redis://localhost:6379/0"))
    logs_dir: str = Field(default_factory=lambda: _env("STORAGE_LOGS_DIR", "/var/log/autogen-agent"))
    temp_dir: str = Field(default_factory=lambda: _env("STORAGE_TEMP_DIR", "/tmp/autogen-agent"))


class SystemConfig(BaseModel):
    log_level: str = Field(default_factory=lambda: _env("LOG_LEVEL", "info"))
    debug_mode: bool = Field(default_factory=lambda: _env_bool("DEBUG_MODE", False))
    max_run_iterations: int = Field(default_factory=lambda: _env_int("MAX_RUN_ITERATIONS", 50))
    heartbeat_interval: int = Field(default_factory=lambda: _env_int("HEARTBEAT_INTERVAL", 30))
    task_persistence_enabled: bool = Field(default_factory=lambda: _env_bool("TASK_PERSISTENCE_ENABLED", True))
    enable_human_in_loop: bool = Field(default_factory=lambda: _env_bool("ENABLE_HUMAN_IN_LOOP", True))
    api_port: int = Field(default_factory=lambda: _env_int("API_PORT", 8000))
    api_host: str = Field(default_factory=lambda: _env("API_HOST", "0.0.0.0"))


class Settings(BaseModel):
    llm: LLMConfig = Field(default_factory=LLMConfig)
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    command_executor: CommandExecutorConfig = Field(default_factory=CommandExecutorConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    system: SystemConfig = Field(default_factory=SystemConfig)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
