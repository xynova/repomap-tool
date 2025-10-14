"""
Test models with various class patterns for testing.
"""

from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class UserRole(Enum):
    """User role enumeration."""

    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


@dataclass
class BaseModel:
    """Base model with common attributes."""

    id: int
    created_at: str
    updated_at: str


class User(BaseModel):
    """User model with inheritance."""

    def __init__(
        self, id: int, username: str, email: str, role: UserRole = UserRole.USER
    ):
        super().__init__(id, "2024-01-01", "2024-01-01")
        self.username = username
        self.email = email
        self.role = role
        self._password_hash: Optional[str] = None

    @property
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == UserRole.ADMIN

    @property
    def display_name(self) -> str:
        """Get user display name."""
        return f"{self.username} ({self.email})"

    def set_password(self, password: str) -> None:
        """Set user password."""
        self._password_hash = f"hashed_{password}"

    def verify_password(self, password: str) -> bool:
        """Verify user password."""
        return self._password_hash == f"hashed_{password}"


class AbstractRepository(ABC):
    """Abstract repository interface."""

    @abstractmethod
    def save(self, entity: BaseModel) -> BaseModel:
        """Save entity to repository."""
        pass

    @abstractmethod
    def find_by_id(self, entity_id: int) -> Optional[BaseModel]:
        """Find entity by ID."""
        pass

    @abstractmethod
    def delete(self, entity_id: int) -> bool:
        """Delete entity by ID."""
        pass


class UserRepository(AbstractRepository):
    """User repository implementation."""

    def __init__(self):
        self._users: Dict[int, User] = {}
        self._next_id = 1

    def save(self, entity: User) -> User:
        """Save user to repository."""
        if entity.id is None:
            entity.id = self._next_id
            self._next_id += 1
        self._users[entity.id] = entity
        return entity

    def find_by_id(self, entity_id: int) -> Optional[User]:
        """Find user by ID."""
        return self._users.get(entity_id)

    def delete(self, entity_id: int) -> bool:
        """Delete user by ID."""
        if entity_id in self._users:
            del self._users[entity_id]
            return True
        return False

    def find_by_username(self, username: str) -> Optional[User]:
        """Find user by username."""
        for user in self._users.values():
            if user.username == username:
                return user
        return None


class Service:
    """Service class with dependency injection."""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def create_user(self, username: str, email: str) -> User:
        """Create new user."""
        user = User(id=None, username=username, email=email)
        return self.user_repo.save(user)

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user."""
        user = self.user_repo.find_by_username(username)
        if user and user.verify_password(password):
            return user
        return None
