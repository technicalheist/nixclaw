from __future__ import annotations

import os

from nixclaw.config import Settings, get_settings
from nixclaw.logger import get_logger

logger = get_logger(__name__)

# Providers that use API-key + base-URL + model (OpenAI-style)
_API_KEY_PROVIDERS = ("openai", "anthropic", "gemini", "vertex")


def configure_llm(settings: Settings | None = None) -> None:
    """Configure environment variables so nixagent can reach the LLM.

    nixagent reads PROVIDER and the matching provider-specific vars
    (e.g. OPENAI_API_KEY, ANTHROPIC_MODEL, QWEN_EMAIL …).  This function
    propagates nixclaw's LLMConfig to those env vars so both layers stay
    in sync.  Generic LLM_* vars act as fallbacks for each provider.
    """
    settings = settings or get_settings()
    llm = settings.llm
    provider = llm.provider.lower()

    # Always publish the active provider
    os.environ["PROVIDER"] = provider

    if provider == "openai":
        os.environ["OPENAI_API_KEY"] = llm.openai_api_key or llm.api_key
        os.environ["OPENAI_BASE_URL"] = llm.openai_base_url or llm.base_url or "https://api.openai.com/v1"
        os.environ["OPENAI_MODEL"] = llm.openai_model or llm.model or "gpt-4o"

    elif provider == "anthropic":
        os.environ["ANTHROPIC_API_KEY"] = llm.anthropic_api_key or llm.api_key
        os.environ["ANTHROPIC_BASE_URL"] = llm.anthropic_base_url or llm.base_url or "https://api.anthropic.com/v1"
        os.environ["ANTHROPIC_MODEL"] = llm.anthropic_model or llm.model or "claude-3-opus-20240229"

    elif provider == "gemini":
        os.environ["GEMINI_API_KEY"] = llm.gemini_api_key or llm.api_key
        os.environ["GEMINI_BASE_URL"] = llm.gemini_base_url or llm.base_url or "https://generativelanguage.googleapis.com/v1beta/openai"
        os.environ["GEMINI_MODEL"] = llm.gemini_model or llm.model or "gemini-2.5-flash"

    elif provider == "vertex":
        os.environ["VERTEX_API_KEY"] = llm.vertex_api_key or llm.api_key
        os.environ["VERTEX_BASE_URL"] = llm.vertex_base_url or llm.base_url or "https://aiplatform.googleapis.com/v1"
        os.environ["VERTEX_MODEL"] = llm.vertex_model or llm.model or "gemini-2.5-flash-lite"

    elif provider == "qwen":
        if llm.qwen_email:
            os.environ["QWEN_EMAIL"] = llm.qwen_email
        if llm.qwen_password:
            os.environ["QWEN_PASSWORD"] = llm.qwen_password
        os.environ["QWEN_MODEL"] = llm.qwen_model or llm.model or "qwen3.5-plus"

    else:
        # Unknown provider — fall back to OpenAI-style env vars
        os.environ["OPENAI_API_KEY"] = llm.api_key
        os.environ["OPENAI_BASE_URL"] = llm.base_url
        os.environ["OPENAI_MODEL"] = llm.model

    logger.info("Configured LLM env: provider=%s", provider)


def create_client(
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> None:
    """Configure LLM environment variables for nixagent (backwards-compat shim).

    No longer returns a client object — nixagent manages HTTP connections
    internally.  If specific overrides are supplied they are injected into
    the active provider's env vars before nixagent reads them.
    """
    settings = get_settings()
    provider = settings.llm.provider.lower()

    if model:
        os.environ[f"{provider.upper()}_MODEL"] = model
    if api_key:
        if provider == "qwen":
            # Qwen uses email/password; ignore api_key override
            pass
        else:
            os.environ[f"{provider.upper()}_API_KEY"] = api_key
    if base_url:
        os.environ[f"{provider.upper()}_BASE_URL"] = base_url

    configure_llm(settings)
    logger.info("Configured LLM env: provider=%s model_override=%s", provider, model)
