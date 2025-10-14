"""
Utility functions with various patterns for testing.
"""

import asyncio
import functools
import time
from typing import List, Dict, Any, Optional, Callable, Generator, AsyncGenerator
from pathlib import Path


def sync_function(x: int, y: int) -> int:
    """Simple synchronous function."""
    return x + y


def function_with_defaults(a: int, b: int = 10, c: str = "default") -> str:
    """Function with default parameters."""
    return f"{a} + {b} = {a + b}, c={c}"


def function_with_varargs(*args: int) -> int:
    """Function with variable arguments."""
    return sum(args)


def function_with_kwargs(**kwargs: Any) -> Dict[str, Any]:
    """Function with keyword arguments."""
    return kwargs


def function_with_complex_signature(
    required: str, optional: Optional[int] = None, *args: str, **kwargs: Any
) -> Dict[str, Any]:
    """Function with complex signature."""
    return {
        "required": required,
        "optional": optional,
        "args": list(args),
        "kwargs": kwargs,
    }


def decorator_function(func: Callable) -> Callable:
    """Simple decorator function."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)

    return wrapper


@decorator_function
def decorated_function(x: int) -> int:
    """Function with decorator."""
    return x * 2


def generator_function(n: int) -> Generator[int, None, None]:
    """Generator function."""
    for i in range(n):
        yield i * i


async def async_function(x: int, y: int) -> int:
    """Simple async function."""
    await asyncio.sleep(0.001)  # Simulate async work
    return x + y


async def async_generator_function(n: int) -> AsyncGenerator[int, None]:
    """Async generator function."""
    for i in range(n):
        await asyncio.sleep(0.001)  # Simulate async work
        yield i * i


def function_with_exception(x: int) -> int:
    """Function that may raise exception."""
    if x < 0:
        raise ValueError("x must be non-negative")
    return x * 2


def function_with_try_except(x: int) -> Optional[int]:
    """Function with try-except block."""
    try:
        return function_with_exception(x)
    except ValueError as e:
        print(f"Error: {e}")
        return None


def function_with_context_manager(file_path: str) -> str:
    """Function using context manager."""
    with open(file_path, "r") as f:
        return f.read()


def function_with_list_comprehension(numbers: List[int]) -> List[int]:
    """Function with list comprehension."""
    return [x * 2 for x in numbers if x > 0]


def function_with_dict_comprehension(items: List[str]) -> Dict[str, int]:
    """Function with dict comprehension."""
    return {item: len(item) for item in items}


def function_with_nested_functions(x: int) -> int:
    """Function with nested functions."""

    def inner_function(y: int) -> int:
        return y * 2

    def another_inner(z: int) -> int:
        return z + 1

    return inner_function(another_inner(x))


def function_with_lambda(numbers: List[int]) -> List[int]:
    """Function using lambda."""
    return list(map(lambda x: x * 2, numbers))


def function_with_closure(x: int) -> Callable[[int], int]:
    """Function returning closure."""

    def closure(y: int) -> int:
        return x + y

    return closure


def function_with_recursion(n: int) -> int:
    """Recursive function."""
    if n <= 1:
        return 1
    return n * function_with_recursion(n - 1)


def function_with_class_method():
    """Function that uses class methods."""

    class Helper:
        @staticmethod
        def static_method(x: int) -> int:
            return x * 2

        @classmethod
        def class_method(cls, x: int) -> int:
            return x * 3

    return Helper.static_method(5) + Helper.class_method(3)


def function_with_property():
    """Function that uses properties."""

    class DataHolder:
        def __init__(self, value: int):
            self._value = value

        @property
        def value(self) -> int:
            return self._value

        @value.setter
        def value(self, new_value: int) -> None:
            if new_value < 0:
                raise ValueError("Value must be non-negative")
            self._value = new_value

    holder = DataHolder(10)
    return holder.value
