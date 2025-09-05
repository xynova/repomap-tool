"""
Session management for tree exploration.

This module provides external session control via CLI parameters and environment variables,
allowing multiple independent exploration sessions to run simultaneously.
"""

import os
import json
import pickle
import tempfile
import logging
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

from repomap_tool.models import ExplorationSession
from repomap_tool.exceptions import RepoMapError

logger = logging.getLogger(__name__)


class SessionStoreError(RepoMapError):
    """Error related to session storage operations."""

    pass


class CorruptedSessionError(SessionStoreError):
    """Error when session data is corrupted."""

    pass


class SessionStore:
    """Handles persistence of exploration sessions."""

    def __init__(self, storage_dir: Optional[str] = None):
        """Initialize session store.

        Args:
            storage_dir: Directory to store sessions. Defaults to temp directory.
        """
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            self.storage_dir = Path(tempfile.gettempdir()) / "repomap_sessions"

        # Ensure storage directory exists
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Session storage directory: {self.storage_dir}")

    def save_session(self, session: ExplorationSession) -> None:
        """Save session to storage.

        Args:
            session: Session to save

        Raises:
            SessionStoreError: If saving fails
        """
        try:
            session_file = self.storage_dir / f"{session.session_id}.json"

            # Convert to dict for JSON serialization
            session_dict = session.model_dump()
            session_dict["last_activity"] = session.last_activity.isoformat()
            session_dict["created_at"] = session.created_at.isoformat()

            # Handle TreeNode objects that can't be directly serialized
            for tree in session_dict["exploration_trees"].values():
                if tree.get("tree_structure"):
                    tree["tree_structure"] = self._serialize_tree_node(
                        tree["tree_structure"]
                    )

                # Convert sets to lists for JSON serialization
                if "expanded_areas" in tree and isinstance(tree["expanded_areas"], set):
                    tree["expanded_areas"] = list(tree["expanded_areas"])
                if "pruned_areas" in tree and isinstance(tree["pruned_areas"], set):
                    tree["pruned_areas"] = list(tree["pruned_areas"])

                # Convert datetime fields to ISO format strings
                if "created_at" in tree and hasattr(tree["created_at"], "isoformat"):
                    tree["created_at"] = tree["created_at"].isoformat()
                if "last_modified" in tree and hasattr(
                    tree["last_modified"], "isoformat"
                ):
                    tree["last_modified"] = tree["last_modified"].isoformat()

            with open(session_file, "w") as f:
                json.dump(session_dict, f, indent=2)

            logger.debug(f"Saved session {session.session_id} to {session_file}")

        except Exception as e:
            raise SessionStoreError(
                f"Failed to save session {session.session_id}: {e}"
            ) from e

    def load_session(self, session_id: str) -> Optional[ExplorationSession]:
        """Load session from storage.

        Args:
            session_id: ID of session to load

        Returns:
            Loaded session or None if not found

        Raises:
            CorruptedSessionError: If session data is corrupted
        """
        try:
            session_file = self.storage_dir / f"{session_id}.json"

            if not session_file.exists():
                logger.debug(f"Session file not found: {session_file}")
                return None

            with open(session_file, "r") as f:
                session_dict = json.load(f)

            # Convert datetime strings back to datetime objects
            session_dict["last_activity"] = datetime.fromisoformat(
                session_dict["last_activity"]
            )
            session_dict["created_at"] = datetime.fromisoformat(
                session_dict["created_at"]
            )

            # Handle TreeNode deserialization
            for tree in session_dict["exploration_trees"].values():
                if tree.get("tree_structure"):
                    tree["tree_structure"] = self._deserialize_tree_node(
                        tree["tree_structure"]
                    )

                # Convert lists back to sets for ExplorationTree model
                if "expanded_areas" in tree and isinstance(
                    tree["expanded_areas"], list
                ):
                    tree["expanded_areas"] = set(tree["expanded_areas"])
                if "pruned_areas" in tree and isinstance(tree["pruned_areas"], list):
                    tree["pruned_areas"] = set(tree["pruned_areas"])

                # Convert datetime strings back to datetime objects
                if "created_at" in tree and isinstance(tree["created_at"], str):
                    tree["created_at"] = datetime.fromisoformat(tree["created_at"])
                if "last_modified" in tree and isinstance(tree["last_modified"], str):
                    tree["last_modified"] = datetime.fromisoformat(
                        tree["last_modified"]
                    )

            # Create session from dict
            session = ExplorationSession(**session_dict)
            logger.debug(f"Loaded session {session_id} from {session_file}")
            return session

        except json.JSONDecodeError as e:
            raise CorruptedSessionError(
                f"Session {session_id} has corrupted JSON data: {e}"
            ) from e
        except Exception as e:
            raise SessionStoreError(f"Failed to load session {session_id}: {e}") from e

    def delete_session(self, session_id: str) -> bool:
        """Delete session from storage.

        Args:
            session_id: ID of session to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            session_file = self.storage_dir / f"{session_id}.json"

            if session_file.exists():
                session_file.unlink()
                logger.debug(f"Deleted session {session_id}")
                return True
            else:
                logger.debug(f"Session file not found for deletion: {session_file}")
                return False

        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False

    def list_sessions(self) -> List[str]:
        """List all available session IDs.

        Returns:
            List of session IDs
        """
        try:
            session_files = list(self.storage_dir.glob("*.json"))
            session_ids = [f.stem for f in session_files]
            logger.debug(f"Found {len(session_ids)} sessions: {session_ids}")
            return session_ids
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return []

    def _serialize_tree_node(self, node: Dict) -> Dict:
        """Serialize TreeNode for JSON storage.

        Args:
            node: TreeNode dict to serialize

        Returns:
            Serialized node dict
        """
        # Remove parent reference to avoid circular references
        serialized = node.copy()
        if "parent" in serialized:
            del serialized["parent"]

        # Recursively serialize children
        if "children" in serialized:
            serialized["children"] = [
                self._serialize_tree_node(child) for child in serialized["children"]
            ]

        return serialized

    def _deserialize_tree_node(self, node_dict: Dict) -> Dict:
        """Deserialize TreeNode from JSON storage.

        Args:
            node_dict: Serialized node dict

        Returns:
            Deserialized node dict
        """
        # TreeNode will be properly reconstructed when creating ExplorationTree
        # This is just a placeholder for now
        return node_dict


class SessionManager:
    """Manages exploration sessions with external control."""

    def __init__(self, storage_dir: Optional[str] = None):
        """Initialize session manager.

        Args:
            storage_dir: Directory to store sessions
        """
        self.session_store = SessionStore(storage_dir)

    def get_session_id(self, cli_session: Optional[str] = None) -> str:
        """Get session ID from CLI parameter or environment.

        Args:
            cli_session: Session ID from CLI parameter

        Returns:
            Session ID to use
        """
        # CLI parameter takes precedence
        if cli_session:
            return cli_session

        # Check environment variable
        env_session = os.environ.get("REPOMAP_SESSION")
        if env_session:
            return env_session

        # Generate new session ID
        timestamp = int(datetime.now().timestamp())
        return f"session_{timestamp}"

    def get_or_create_session(
        self, session_id: str, project_path: str
    ) -> ExplorationSession:
        """Get existing session or create new one.

        Args:
            session_id: Session ID to get or create
            project_path: Project path for the session

        Returns:
            Session object
        """
        try:
            # Try to load existing session
            session = self.session_store.load_session(session_id)

            if session:
                # Validate project path matches
                if session.project_path == project_path:
                    logger.debug(
                        f"Using existing session {session_id} for {project_path}"
                    )
                    return session
                else:
                    logger.warning(
                        f"Session {session_id} exists but project path mismatch: "
                        f"expected {project_path}, got {session.project_path}"
                    )
                    # Create new session with same ID but different project
                    session = ExplorationSession(
                        session_id=session_id, project_path=project_path
                    )
            else:
                # Create new session
                session = ExplorationSession(
                    session_id=session_id, project_path=project_path
                )
                logger.debug(f"Created new session {session_id} for {project_path}")

        except (FileNotFoundError, CorruptedSessionError) as e:
            logger.warning(
                f"Session {session_id} not found or corrupted, creating new: {e}"
            )
            session = ExplorationSession(
                session_id=session_id, project_path=project_path
            )

        # Save the new session
        self.session_store.save_session(session)
        return session

    def get_session(self, session_id: str) -> Optional[ExplorationSession]:
        """Get existing session by ID.

        Args:
            session_id: Session ID to retrieve

        Returns:
            Session object or None if not found
        """
        try:
            return self.session_store.load_session(session_id)
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None

    def persist_session(self, session: ExplorationSession) -> None:
        """Persist session to storage.

        Args:
            session: Session to persist
        """
        try:
            session.last_activity = datetime.now()
            self.session_store.save_session(session)
            logger.debug(f"Persisted session {session.session_id}")
        except Exception as e:
            logger.error(f"Failed to persist session {session.session_id}: {e}")

    def delete_session(self, session_id: str) -> bool:
        """Delete session.

        Args:
            session_id: Session ID to delete

        Returns:
            True if deleted, False if not found
        """
        return self.session_store.delete_session(session_id)

    def list_sessions(self) -> List[str]:
        """List all available sessions.

        Returns:
            List of session IDs
        """
        return self.session_store.list_sessions()

    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up old sessions.

        Args:
            max_age_hours: Maximum age in hours before cleanup

        Returns:
            Number of sessions cleaned up
        """
        try:
            cleaned_count = 0
            current_time = datetime.now()

            for session_id in self.list_sessions():
                session = self.get_session(session_id)
                if session:
                    age_hours = (
                        current_time - session.last_activity
                    ).total_seconds() / 3600
                    if age_hours > max_age_hours:
                        if self.delete_session(session_id):
                            cleaned_count += 1
                            logger.info(
                                f"Cleaned up old session {session_id} (age: {age_hours:.1f}h)"
                            )

            return cleaned_count

        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {e}")
            return 0
