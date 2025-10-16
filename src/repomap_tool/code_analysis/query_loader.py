import logging
from pathlib import Path
from typing import Dict, Optional

from repomap_tool.core.logging_service import get_logger
from repomap_tool.protocols import QueryLoaderProtocol

logger = get_logger(__name__)


class FileQueryLoader(QueryLoaderProtocol):
    """Loads tree-sitter query strings from .scm files.

    This loader is responsible for locating and reading query files
    from a designated, fixed directory.
    """

    def __init__(self):
        """Initialize the FileQueryLoader.

        The custom_queries_dir is always derived from the current file's location.
        """
        self.custom_queries_dir = (Path(__file__).parent / "queries").resolve()
        self.query_cache: Dict[str, str] = {}

        logger.debug(f"FileQueryLoader initialized with queries directory: {self.custom_queries_dir}")
        if not self.custom_queries_dir.exists():
            logger.warning(f"FileQueryLoader: Queries directory does not exist: {self.custom_queries_dir}")

    def load_query(self, language: str) -> Optional[str]:
        """Load the .scm query file for the specified language.

        Args:
            language: Language identifier (e.g., "python", "javascript").

        Returns:
            The query string if found, otherwise None.
        """
        if language in self.query_cache:
            return self.query_cache[language]

        logger.debug(f"FileQueryLoader: Loading query for language: {language} from {self.custom_queries_dir}")

        query_path = self.custom_queries_dir / f"{language}-tags.scm"
        if query_path.exists():
            try:
                query_content = query_path.read_text()
                self.query_cache[language] = query_content
                logger.debug(f"FileQueryLoader: Loaded query from: {query_path}")
                return query_content
            except Exception as e:
                logger.error(f"FileQueryLoader: Could not read query file {query_path}: {e}")
                return None
        else:
            logger.warning(f"FileQueryLoader: Query file not found for language {language} at {query_path}")
            return None
