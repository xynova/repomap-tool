"""
Dependency chain B
This file imports from dependency_chain_c.
"""

from .dependency_chain_c import calculate_result, store_data, retrieve_data
from .models import BaseModel, UserRole
from .utils import function_with_defaults, function_with_exception


def process_data(data: str) -> str:
    """Process the input data."""
    print(f"Processing data: {data}")
    result = calculate_result(data)
    return f"Processed: {result}"


def validate_input(data: str) -> str:
    """Validate input data."""
    if not data or len(data) < 3:
        raise ValueError("Data must be at least 3 characters long")
    return data


def format_output(result: str) -> str:
    """Format the output."""
    return f"Formatted: {result.upper()}"


def store_processed_data(data: str) -> bool:
    """Store processed data."""
    try:
        store_data(data)
        return True
    except Exception as e:
        print(f"Error storing data: {e}")
        return False


def retrieve_processed_data(key: str) -> str:
    """Retrieve processed data."""
    return retrieve_data(key)


def handle_user_role(role: UserRole) -> str:
    """Handle user role."""
    if role == UserRole.ADMIN:
        return "Admin access granted"
    elif role == UserRole.USER:
        return "User access granted"
    else:
        return "Guest access granted"


def process_with_defaults(value: int) -> str:
    """Process with default parameters."""
    return function_with_defaults(value)


def process_with_exception(value: int) -> int:
    """Process with potential exception."""
    try:
        return function_with_exception(value)
    except ValueError as e:
        print(f"Exception caught: {e}")
        return -1
