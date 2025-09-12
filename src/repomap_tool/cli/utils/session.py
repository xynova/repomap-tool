"""
Session management utilities for RepoMap-Tool CLI.

This module contains functions for managing exploration sessions.
"""

import os
from typing import Optional

from rich.console import Console

console = Console()


def get_project_path_from_session(session_id: str) -> Optional[str]:
    """Get project path from session data.

    Args:
        session_id: Session ID to retrieve project path for

    Returns:
        Project path from session or None if session not found
    """
    try:
        from ...trees import SessionManager

        # Initialize session manager with storage directory from environment
        session_storage_dir = os.environ.get("REPOMAP_SESSION_DIR")
        session_manager = SessionManager(storage_dir=session_storage_dir)
        session = session_manager.get_session(session_id)

        if session:
            return session.project_path
        else:
            console.print(f"[yellow]Session '{session_id}' not found[/yellow]")
            return None

    except ImportError:
        console.print("[red]Session management not available[/red]")
        return None
    except Exception as e:
        console.print(f"[red]Error retrieving session: {e}[/red]")
        return None


def create_session_id() -> str:
    """Create a new session ID based on current timestamp."""
    import time
    return f"explore_{int(time.time())}"


def get_or_create_session(session: Optional[str]) -> str:
    """Get existing session or create a new one.
    
    Args:
        session: Optional session ID
        
    Returns:
        Session ID to use
    """
    session_id = session or os.environ.get("REPOMAP_SESSION")
    if not session_id:
        session_id = create_session_id()
        console.print(f"💡 Using session: {session_id}")
        console.print(f"Set: export REPOMAP_SESSION={session_id}")
    return session_id
