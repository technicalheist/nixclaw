from __future__ import annotations

import os
from pathlib import Path
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load .env from the current working directory (where the user runs nixclaw)
# This works correctly whether nixclaw is run from source or installed via pip
load_dotenv(Path.cwd() / ".env")


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
    # Active provider: openai | anthropic | gemini | vertex | qwen
    provider: str = Field(default_factory=lambda: _env("PROVIDER", "openai"))

    # Generic / legacy vars (used as fallback when provider-specific vars are absent)
    model: str = Field(default_factory=lambda: _env("LLM_MODEL", ""))
    api_key: str = Field(default_factory=lambda: _env("LLM_API_KEY", ""))
    base_url: str = Field(default_factory=lambda: _env("LLM_BASE_URL", ""))
    temperature: float = Field(default_factory=lambda: _env_float("LLM_TEMPERATURE", 0.7))
    max_tokens: int = Field(default_factory=lambda: _env_int("LLM_MAX_TOKENS", 4096))
    request_timeout: int = Field(default_factory=lambda: _env_int("LLM_REQUEST_TIMEOUT", 60))

    # OpenAI-compatible (also covers Ollama, vLLM, custom deployments)
    openai_api_key: str = Field(default_factory=lambda: _env("OPENAI_API_KEY", ""))
    openai_base_url: str = Field(default_factory=lambda: _env("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    openai_model: str = Field(default_factory=lambda: _env("OPENAI_MODEL", "gpt-4o"))

    # Anthropic
    anthropic_api_key: str = Field(default_factory=lambda: _env("ANTHROPIC_API_KEY", ""))
    anthropic_base_url: str = Field(default_factory=lambda: _env("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1"))
    anthropic_model: str = Field(default_factory=lambda: _env("ANTHROPIC_MODEL", "claude-3-opus-20240229"))

    # Gemini
    gemini_api_key: str = Field(default_factory=lambda: _env("GEMINI_API_KEY", ""))
    gemini_base_url: str = Field(default_factory=lambda: _env("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai"))
    gemini_model: str = Field(default_factory=lambda: _env("GEMINI_MODEL", "gemini-2.5-flash"))

    # Vertex AI
    vertex_api_key: str = Field(default_factory=lambda: _env("VERTEX_API_KEY", ""))
    vertex_base_url: str = Field(default_factory=lambda: _env("VERTEX_BASE_URL", "https://aiplatform.googleapis.com/v1"))
    vertex_model: str = Field(default_factory=lambda: _env("VERTEX_MODEL", "gemini-2.5-flash-lite"))

    # Qwen (uses email/password auth instead of API key)
    qwen_email: str = Field(default_factory=lambda: _env("QWEN_EMAIL", ""))
    qwen_password: str = Field(default_factory=lambda: _env("QWEN_PASSWORD", ""))
    qwen_model: str = Field(default_factory=lambda: _env("QWEN_MODEL", "qwen3.5-plus"))


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
    logs_dir: str = Field(default_factory=lambda: _env("STORAGE_LOGS_DIR", "/var/log/nixagent"))
    temp_dir: str = Field(default_factory=lambda: _env("STORAGE_TEMP_DIR", "/tmp/nixagent"))


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
