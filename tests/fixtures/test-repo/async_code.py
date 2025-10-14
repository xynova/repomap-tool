"""
Async/await patterns for testing.
"""

import asyncio
from typing import List, Dict, Any


async def async_simple():
    """Simple async function."""
    await asyncio.sleep(0.001)
    return "async result"


async def async_with_args(x: int, y: int) -> int:
    """Async function with arguments."""
    await asyncio.sleep(0.001)
    return x + y


async def async_generator(n: int):
    """Async generator."""
    for i in range(n):
        await asyncio.sleep(0.001)
        yield i


async def async_with_exception():
    """Async function that raises exception."""
    await asyncio.sleep(0.001)
    raise ValueError("Async exception")


async def async_with_try_except():
    """Async function with try-except."""
    try:
        await async_with_exception()
    except ValueError as e:
        return f"Caught: {e}"


class AsyncClass:
    """Class with async methods."""

    async def async_method(self):
        """Async method."""
        await asyncio.sleep(0.001)
        return "async method"

    async def async_method_with_args(self, x: int):
        """Async method with arguments."""
        await asyncio.sleep(0.001)
        return x * 2


async def async_main():
    """Main async function."""
    result1 = await async_simple()
    result2 = await async_with_args(5, 3)

    async_gen = async_generator(3)
    results = []
    async for value in async_gen:
        results.append(value)

    return {"simple": result1, "with_args": result2, "generator": results}
