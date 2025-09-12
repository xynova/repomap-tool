"""
File system validation utilities for secure and reliable file operations.

This module provides comprehensive validation for all file system operations
to prevent security vulnerabilities and improve reliability.
"""

import os
import stat
from pathlib import Path
from typing import Optional, Union, List, Tuple
import logging

from ..exceptions import FileAccessError, ValidationError

logger = logging.getLogger(__name__)

# Security constants
MAX_PATH_LENGTH = 4096
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB default limit
FORBIDDEN_CHARS = ['\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07', 
                   '\x08', '\x0b', '\x0c', '\x0e', '\x0f', '\x10', '\x11', '\x12', 
                   '\x13', '\x14', '\x15', '\x16', '\x17', '\x18', '\x19', '\x1a', 
                   '\x1b', '\x1c', '\x1d', '\x1e', '\x1f']

# Forbidden path patterns that could indicate path traversal attacks
FORBIDDEN_PATTERNS = [
    '../', '..\\', 
    '/./', '\\.\\',
    '//', '\\\\',
    '/dev/', '/proc/', '/sys/',  # Unix system directories
    'CON', 'PRN', 'AUX', 'NUL',  # Windows reserved names
    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
]


class FileValidator:
    """Validates file system operations for security and reliability."""
    
    def __init__(self, project_root: Optional[Union[str, Path]] = None):
        """Initialize validator with optional project root for sandboxing.
        
        Args:
            project_root: Optional project root to restrict operations to
        """
        self.project_root = Path(project_root).resolve() if project_root else None
        
    def validate_path(
        self, 
        path: Union[str, Path], 
        must_exist: bool = False,
        must_be_file: bool = False,
        must_be_dir: bool = False,
        allow_create: bool = True
    ) -> Path:
        """Comprehensive path validation.
        
        Args:
            path: Path to validate
            must_exist: Whether path must already exist
            must_be_file: Whether path must be a file (if exists)
            must_be_dir: Whether path must be a directory (if exists)
            allow_create: Whether to allow creation of non-existent paths
            
        Returns:
            Validated Path object
            
        Raises:
            ValidationError: If path validation fails
            FileAccessError: If file access is denied
        """
        try:
            # Convert to string for initial validation
            path_str = str(path)
            
            # Basic security checks
            self._check_path_security(path_str)
            
            # Convert to Path and resolve
            path_obj = Path(path).resolve()
            
            # Check path length after resolution
            if len(str(path_obj)) > MAX_PATH_LENGTH:
                raise ValidationError(f"Resolved path too long: {len(str(path_obj))} > {MAX_PATH_LENGTH}")
            
            # Sandbox check if project root is set
            if self.project_root and not self._is_within_sandbox(path_obj):
                raise ValidationError(f"Path outside project root: {path_obj}")
            
            # Existence checks
            if must_exist and not path_obj.exists():
                raise FileAccessError(f"Path does not exist: {path_obj}")
            
            if path_obj.exists():
                # Type checks
                if must_be_file and not path_obj.is_file():
                    raise ValidationError(f"Path is not a file: {path_obj}")
                if must_be_dir and not path_obj.is_dir():
                    raise ValidationError(f"Path is not a directory: {path_obj}")
                    
                # Permission checks
                self._check_permissions(path_obj)
            elif not allow_create:
                raise ValidationError(f"Path does not exist and creation not allowed: {path_obj}")
                
            return path_obj
            
        except (OSError, ValueError) as e:
            if "File name too long" in str(e):
                raise ValidationError("Path too long") from e
            raise ValidationError(f"Invalid path: {e}") from e
    
    def validate_file_operation(
        self, 
        path: Union[str, Path], 
        operation: str,
        max_size: Optional[int] = None
    ) -> Path:
        """Validate file for specific operation.
        
        Args:
            path: File path to validate
            operation: Operation type ('read', 'write', 'append')
            max_size: Maximum allowed file size in bytes
            
        Returns:
            Validated Path object
            
        Raises:
            ValidationError: If validation fails
            FileAccessError: If access is denied
        """
        if operation not in ('read', 'write', 'append'):
            raise ValidationError(f"Invalid operation: {operation}")
        
        # Basic path validation
        path_obj = self.validate_path(
            path, 
            must_exist=(operation == 'read'),
            must_be_file=True,
            allow_create=(operation in ('write', 'append'))
        )
        
        # Size check for existing files
        if path_obj.exists():
            file_size = path_obj.stat().st_size
            max_allowed = max_size or MAX_FILE_SIZE
            if file_size > max_allowed:
                raise ValidationError(f"File too large: {file_size} > {max_allowed} bytes")
        
        # Operation-specific checks
        if operation == 'read':
            if not os.access(path_obj, os.R_OK):
                raise FileAccessError(f"No read permission: {path_obj}")
        elif operation in ('write', 'append'):
            # Check parent directory permissions
            parent = path_obj.parent
            if not parent.exists():
                # Check if we can create parent directories
                try:
                    parent.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    raise FileAccessError(f"Cannot create parent directory: {e}") from e
            
            if not os.access(parent, os.W_OK):
                raise FileAccessError(f"No write permission in directory: {parent}")
        
        return path_obj
    
    def safe_read_text(self, path: Union[str, Path], encoding: str = 'utf-8') -> str:
        """Safely read text from file with validation.
        
        Args:
            path: File path to read
            encoding: Text encoding to use
            
        Returns:
            File contents as string
            
        Raises:
            ValidationError: If validation fails
            FileAccessError: If read fails
        """
        validated_path = self.validate_file_operation(path, 'read')
        
        try:
            return validated_path.read_text(encoding=encoding)
        except UnicodeDecodeError as e:
            raise FileAccessError(f"Text decoding failed: {e}") from e
        except OSError as e:
            raise FileAccessError(f"Read failed: {e}") from e
    
    def safe_write_text(
        self, 
        path: Union[str, Path], 
        content: str, 
        encoding: str = 'utf-8',
        max_size: Optional[int] = None
    ) -> None:
        """Safely write text to file with validation.
        
        Args:
            path: File path to write
            content: Text content to write
            encoding: Text encoding to use
            max_size: Maximum allowed file size
            
        Raises:
            ValidationError: If validation fails
            FileAccessError: If write fails
        """
        # Check content size
        content_bytes = content.encode(encoding)
        max_allowed = max_size or MAX_FILE_SIZE
        if len(content_bytes) > max_allowed:
            raise ValidationError(f"Content too large: {len(content_bytes)} > {max_allowed} bytes")
        
        validated_path = self.validate_file_operation(path, 'write', max_size)
        
        try:
            validated_path.write_text(content, encoding=encoding)
            logger.debug(f"Successfully wrote {len(content_bytes)} bytes to {validated_path}")
        except OSError as e:
            raise FileAccessError(f"Write failed: {e}") from e
    
    def safe_create_directory(self, path: Union[str, Path], parents: bool = True) -> Path:
        """Safely create directory with validation.
        
        Args:
            path: Directory path to create
            parents: Whether to create parent directories
            
        Returns:
            Created directory path
            
        Raises:
            ValidationError: If validation fails
            FileAccessError: If creation fails
        """
        validated_path = self.validate_path(
            path, 
            must_exist=False,
            must_be_dir=False,
            allow_create=True
        )
        
        try:
            validated_path.mkdir(parents=parents, exist_ok=True)
            logger.debug(f"Created directory: {validated_path}")
            return validated_path
        except OSError as e:
            raise FileAccessError(f"Directory creation failed: {e}") from e
    
    def _check_path_security(self, path_str: str) -> None:
        """Check path for security issues.
        
        Args:
            path_str: Path string to check
            
        Raises:
            ValidationError: If security issues found
        """
        # Check for null bytes and control characters
        for char in FORBIDDEN_CHARS:
            if char in path_str:
                raise ValidationError(f"Path contains forbidden character: {repr(char)}")
        
        # Check path length
        if len(path_str) > MAX_PATH_LENGTH:
            raise ValidationError(f"Path too long: {len(path_str)} > {MAX_PATH_LENGTH}")
        
        # Check for suspicious patterns
        path_lower = path_str.lower()
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.lower() in path_lower:
                raise ValidationError(f"Path contains forbidden pattern: {pattern}")
        
        # Check for relative path traversal
        if '..' in Path(path_str).parts:
            raise ValidationError("Path contains parent directory references")
    
    def _is_within_sandbox(self, path: Path) -> bool:
        """Check if path is within project root sandbox.
        
        Args:
            path: Path to check
            
        Returns:
            True if path is within sandbox
        """
        if not self.project_root:
            return True
        
        try:
            path.relative_to(self.project_root)
            return True
        except ValueError:
            return False
    
    def _check_permissions(self, path: Path) -> None:
        """Check file permissions and access.
        
        Args:
            path: Path to check
            
        Raises:
            FileAccessError: If permission check fails
        """
        try:
            stat_info = path.stat()
            
            # Check for suspicious permissions
            mode = stat_info.st_mode
            if mode & stat.S_ISUID:
                logger.warning(f"File has setuid bit: {path}")
            if mode & stat.S_ISGID:
                logger.warning(f"File has setgid bit: {path}")
            
            # Basic access check
            if not os.access(path, os.R_OK):
                raise FileAccessError(f"No read access: {path}")
                
        except OSError as e:
            raise FileAccessError(f"Permission check failed: {e}") from e


# Global validator instance for convenience
_default_validator = FileValidator()

# Convenience functions
def validate_path(path: Union[str, Path], **kwargs) -> Path:
    """Validate path using default validator."""
    return _default_validator.validate_path(path, **kwargs)

def safe_read_text(path: Union[str, Path], encoding: str = 'utf-8') -> str:
    """Safely read text using default validator."""
    return _default_validator.safe_read_text(path, encoding)

def safe_write_text(path: Union[str, Path], content: str, encoding: str = 'utf-8') -> None:
    """Safely write text using default validator."""
    return _default_validator.safe_write_text(path, content, encoding)

def safe_create_directory(path: Union[str, Path], parents: bool = True) -> Path:
    """Safely create directory using default validator."""
    return _default_validator.safe_create_directory(path, parents)
