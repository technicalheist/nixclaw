"""
Example 11: Retry Logic — Handle transient failures with exponential backoff.

The retry module provides both a function and a decorator for retrying
failed async operations.
"""
import asyncio
import random

from nixclaw.core.retry import retry_async, with_retry


# Simulate a flaky API call
call_count = 0


async def flaky_api_call(endpoint: str) -> dict:
    """Simulates an API that fails 60% of the time."""
    global call_count
    call_count += 1

    if random.random() < 0.6:
        raise ConnectionError(f"Attempt {call_count}: Connection refused to {endpoint}")

    return {"status": "ok", "data": f"Response from {endpoint}", "attempt": call_count}


async def example_retry_function():
    """Use retry_async() to wrap any async function."""
    global call_count
    call_count = 0

    print("=== retry_async() ===")
    try:
        result = await retry_async(
            flaky_api_call,
            "https://api.example.com/data",
            max_retries=5,
            initial_delay=0.5,
            backoff_factor=2.0,
            retryable_exceptions=(ConnectionError,),
        )
        print(f"Success on attempt {result['attempt']}: {result}")
    except ConnectionError as e:
        print(f"All retries exhausted: {e}")


# Use the decorator for cleaner syntax
@with_retry(max_retries=3, initial_delay=0.1, retryable_exceptions=(ValueError,))
async def process_data(data: str) -> str:
    """A function that sometimes fails during processing."""
    if random.random() < 0.5:
        raise ValueError("Temporary processing error")
    return f"Processed: {data}"


async def example_decorator():
    """Use @with_retry decorator."""
    print("\n=== @with_retry decorator ===")
    try:
        result = await process_data("Hello, World!")
        print(f"Result: {result}")
    except ValueError as e:
        print(f"Failed after retries: {e}")


if __name__ == "__main__":
    asyncio.run(example_retry_function())
    asyncio.run(example_decorator())
