"""
Dependency chain A -> B -> C
This file imports from dependency_chain_b.
"""

from .dependency_chain_b import process_data, validate_input, format_output
from .dependency_chain_c import finalize_result, cleanup_resources
from .models import User, UserRepository
from .utils import sync_function, async_function


def initialize_system():
    """Initialize the system."""
    print("Initializing system...")
    return True


def start_processing():
    """Start the processing pipeline."""
    data = validate_input("test data")
    result = process_data(data)
    formatted = format_output(result)
    return formatted


def shutdown_system():
    """Shutdown the system."""
    result = finalize_result()
    cleanup_resources()
    return result


def create_user(username: str, email: str):
    """Create a new user."""
    user_repo = UserRepository()
    user = User(id=1, username=username, email=email)
    return user_repo.save(user)


def process_user_data(user: User):
    """Process user data."""
    # Use sync function
    processed_id = sync_function(user.id, 100)

    # Use async function (would need to be awaited in real usage)
    # processed_email = await async_function(len(user.email), 10)

    return {"id": processed_id, "username": user.username, "email": user.email}
