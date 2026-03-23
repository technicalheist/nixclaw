"""Retry logic with exponential backoff for transient failures."""
from __future__ import annotations

import asyncio
import functools
from typing import Any, Callable, TypeVar

from nixclaw.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


async def retry_async(
    func: Callable[..., Any],
    *args: Any,
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
    **kwargs: Any,
) -> Any:
    """Call an async function with exponential backoff on failure.

    Args:
        func: Async function to call.
        max_retries: Maximum number of retry attempts.
        backoff_factor: Multiplier for delay between retries.
        initial_delay: Initial delay in seconds before first retry.
        retryable_exceptions: Tuple of exception types that trigger a retry.

    Returns:
        The return value of the function.

    Raises:
        The last exception if all retries are exhausted.
    """
    last_exception: Exception | None = None
    delay = initial_delay

    for attempt in range(1, max_retries + 2):  # +1 for initial attempt
        try:
            return await func(*args, **kwargs)
        except retryable_exceptions as e:
            last_exception = e
            if attempt > max_retries:
                break
            logger.warning(
                "Attempt %d/%d failed for %s: %s. Retrying in %.1fs...",
                attempt, max_retries + 1, func.__name__, e, delay,
            )
            await asyncio.sleep(delay)
            delay *= backoff_factor

    logger.error("All %d attempts failed for %s", max_retries + 1, func.__name__)
    raise last_exception  # type: ignore[misc]


def with_retry(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable:
    """Decorator that adds retry with exponential backoff to an async function."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await retry_async(
                func, *args,
                max_retries=max_retries,
                backoff_factor=backoff_factor,
                initial_delay=initial_delay,
                retryable_exceptions=retryable_exceptions,
                **kwargs,
            )
        return wrapper

    return decorator
