"""Unit tests for retry logic."""
import pytest

from nixclaw.core.retry import retry_async, with_retry


@pytest.mark.asyncio
async def test_retry_succeeds_first_try():
    call_count = 0

    async def succeeds():
        nonlocal call_count
        call_count += 1
        return "ok"

    result = await retry_async(succeeds, max_retries=3, initial_delay=0.01)
    assert result == "ok"
    assert call_count == 1


@pytest.mark.asyncio
async def test_retry_succeeds_after_failures():
    call_count = 0

    async def fails_twice():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("not yet")
        return "ok"

    result = await retry_async(fails_twice, max_retries=3, initial_delay=0.01)
    assert result == "ok"
    assert call_count == 3


@pytest.mark.asyncio
async def test_retry_exhausted():
    async def always_fails():
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        await retry_async(always_fails, max_retries=2, initial_delay=0.01)


@pytest.mark.asyncio
async def test_retry_only_catches_specified():
    async def raises_type_error():
        raise TypeError("wrong type")

    # Should not retry TypeError when only ValueError is retryable
    with pytest.raises(TypeError):
        await retry_async(
            raises_type_error,
            max_retries=3,
            initial_delay=0.01,
            retryable_exceptions=(ValueError,),
        )


@pytest.mark.asyncio
async def test_with_retry_decorator():
    call_count = 0

    @with_retry(max_retries=2, initial_delay=0.01)
    async def flaky():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("flaky")
        return "done"

    result = await flaky()
    assert result == "done"
    assert call_count == 2
