from __future__ import annotations

from autogen_core.models import ModelInfo
from autogen_ext.models.openai import OpenAIChatCompletionClient

from nixclaw.config import get_settings
from nixclaw.logger import get_logger

logger = get_logger(__name__)


def create_client(
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> OpenAIChatCompletionClient:
    """Create an OpenAI-compatible chat completion client.

    Uses config defaults for any parameter not explicitly provided.
    """
    settings = get_settings()
    llm = settings.llm

    client = OpenAIChatCompletionClient(
        model=model or llm.model,
        api_key=api_key or llm.api_key,
        base_url=base_url or llm.base_url,
        model_info=ModelInfo(
            vision=False,
            function_calling=True,
            json_output=True,
            family="unknown",
            structured_output=True,
        ),
    )
    logger.info("Created LLM client: model=%s base_url=%s", model or llm.model, base_url or llm.base_url)
    return client
