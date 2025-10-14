"""
Dependency chain C
This is the end of the dependency chain.
"""

from .models import User
from .utils import generator_function, function_with_recursion


def calculate_result(data: str) -> str:
    """Calculate the final result."""
    return f"Calculated: {data}"


def store_data(data: str) -> None:
    """Store data to storage."""
    print(f"Storing: {data}")


def retrieve_data(key: str) -> str:
    """Retrieve data from storage."""
    return f"Retrieved data for key: {key}"


def finalize_result() -> str:
    """Finalize the result."""
    return "Result finalized"


def cleanup_resources() -> None:
    """Cleanup resources."""
    print("Resources cleaned up")


def process_with_generator(n: int) -> list:
    """Process using generator."""
    return list(generator_function(n))


def process_with_recursion(n: int) -> int:
    """Process using recursion."""
    return function_with_recursion(n)


def create_user_instance(username: str, email: str) -> User:
    """Create a user instance."""
    return User(id=1, username=username, email=email)


def get_user_info(user: User) -> dict:
    """Get user information."""
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role.value,
        "is_admin": user.is_admin,
        "display_name": user.display_name,
    }
