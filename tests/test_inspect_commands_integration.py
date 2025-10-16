"""
Integration tests for the inspect commands.

This module tests the LLM-optimized inspect impact and centrality commands
with real project structures to ensure they work correctly end-to-end.
"""

import pytest
import tempfile
import os
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from repomap_tool.cli import cli
from repomap_tool.code_analysis import (
    ASTFileAnalyzer,
    AnalysisFormat,
)
from repomap_tool.code_analysis.tree_sitter_parser import TreeSitterParser
from repomap_tool.core.cache_manager import CacheManager
from repomap_tool.core.tag_cache import TreeSitterTagCache


class TestInspectCommandsIntegration:
    """Integration tests for inspect commands with real project structures."""

    def setup_method(self):
        """Set up test environment with a real project structure."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

        # Create a realistic Python project structure
        self._create_test_project()

        # Initialize CLI runner
        self.runner = CliRunner()

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_project(self):
        """Create a realistic test project structure."""
        # Create main package structure
        src_dir = self.project_root / "src" / "test_project"
        src_dir.mkdir(parents=True)

        # Create __init__.py
        (src_dir / "__init__.py").write_text(
            """# Test project package
"""
        )

        # Create user_service.py (main service file)
        (src_dir / "user_service.py").write_text(
            """# User service implementation
import database
from auth import validate_credentials
from email import send_notification
from models.user import User

class UserService:
    def __init__(self):
        self.db = database.get_connection()

    def create_user(self, user_data):
        # Validate credentials
        if not validate_credentials(user_data.get('email')):
            raise ValueError("Invalid email")

        # Create user in database
        user = User(**user_data)
        user_id = self.db.save_user(user)

        # Send notification
        send_notification(user.email, "Welcome!")

        return user_id

    def delete_user(self, user_id):
        user = self.db.get_user_by_id(user_id)
        if user:
            self.db.delete_user(user_id)
            return True
        return False

    def update_profile(self, user_id, profile_data):
        user = self.db.get_user_by_id(user_id)
        if user:
            user.update_profile(profile_data)
            self.db.save_user(user)
            return True
        return False
"""
        )

        # Create auth.py
        (src_dir / "auth.py").write_text(
            """# Authentication utilities
import re
from typing import Optional

def validate_credentials(email: str) -> bool:
    '''Validate email credentials'''
    if not email:
        return False
    pattern = '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def hash_password(password: str) -> str:
    '''Hash password for storage'''
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    '''Verify password against hash'''
    return hash_password(password) == hashed
"""
        )

        # Create database.py
        (src_dir / "database.py").write_text(
            """# Database utilities
import sqlite3
from typing import Optional, Dict, Any

class DatabaseConnection:
    def __init__(self, db_path: str = "test.db"):
        self.connection = sqlite3.connect(db_path)

    def save_user(self, user) -> int:
        cursor = self.connection.cursor()
        cursor.execute("INSERT INTO users (name, email) VALUES (?, ?)",
                      (user.name, user.email))
        self.connection.commit()
        return cursor.lastrowid

    def get_user_by_id(self, user_id: int):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            return {"id": row[0], "name": row[1], "email": row[2]}
        return None

    def delete_user(self, user_id: int):
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        self.connection.commit()

def get_connection() -> DatabaseConnection:
    return DatabaseConnection()
"""
        )

        # Create email.py
        (src_dir / "email.py").write_text(
            """# Email utilities
import smtplib
from typing import Optional

def send_notification(email: str, message: str) -> bool:
    '''Send email notification'''
    try:
        # Simulate email sending
        print(f"Sending email to {email}: {message}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def send_bulk_notifications(emails: list, message: str) -> int:
    '''Send bulk email notifications'''
    sent_count = 0
    for email in emails:
        if send_notification(email, message):
            sent_count += 1
    return sent_count
"""
        )

        # Create models directory
        models_dir = src_dir / "models"
        models_dir.mkdir()

        # Create models/__init__.py
        (models_dir / "__init__.py").write_text(
            """# Models package
"""
        )

        # Create models/user.py
        (models_dir / "user.py").write_text(
            """# User model
from typing import Optional, Dict, Any

class User:
    def __init__(self, name: str, email: str, **kwargs):
        self.name = name
        self.email = email
        self.profile = kwargs.get('profile', {})
        self.created_at = kwargs.get('created_at')

    def update_profile(self, profile_data: Dict[str, Any]):
        '''Update user profile'''
        self.profile.update(profile_data)

    def to_dict(self) -> Dict[str, Any]:
        '''Convert user to dictionary'''
        return {
            'name': self.name,
            'email': self.email,
            'profile': self.profile,
            'created_at': self.created_at
        }

    def __str__(self):
        return f"User(name={self.name}, email={self.email})"
"""
        )

        # Create API directory
        api_dir = src_dir / "api"
        api_dir.mkdir()

        # Create api/user_routes.py
        (api_dir / "user_routes.py").write_text(
            """# User API routes
from flask import Flask, request, jsonify
from ..user_service import UserService

app = Flask(__name__)
user_service = UserService()

@app.route('/users', methods=['POST'])
def create_user():
    user_data = request.get_json()
    try:
        user_id = user_service.create_user(user_data)
        return jsonify({'user_id': user_id}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    success = user_service.delete_user(user_id)
    if success:
        return jsonify({'message': 'User deleted'}), 200
    else:
        return jsonify({'error': 'User not found'}), 404

@app.route('/users/<int:user_id>/profile', methods=['PUT'])
def update_profile(user_id):
    profile_data = request.get_json()
    success = user_service.update_profile(user_id, profile_data)
    if success:
        return jsonify({'message': 'Profile updated'}), 200
    else:
        return jsonify({'error': 'User not found'}), 404
"""
        )

        # Create tests directory
        tests_dir = self.project_root / "tests"
        tests_dir.mkdir()

        # Create tests/test_user_service.py
        (tests_dir / "test_user_service.py").write_text(
            """# Tests for user service
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from test_project.user_service import UserService

class TestUserService:
    def test_create_user(self):
        service = UserService()
        user_data = {'name': 'Test User', 'email': 'test@example.com'}
        user_id = service.create_user(user_data)
        assert user_id is not None

    def test_delete_user(self):
        service = UserService()
        # Test with non-existent user
        result = service.delete_user(999)
        assert result is False

    def test_update_profile(self):
        service = UserService()
        profile_data = {'bio': 'Test bio'}
        # Test with non-existent user
        result = service.update_profile(999, profile_data)
        assert result is False
"""
        )

    def test_inspect_impact_single_file(self):
        """Test inspect impact command with a single file."""
        user_service_path = str(
            self.project_root / "src" / "test_project" / "user_service.py"
        )

        result = self.runner.invoke(
            cli,
            [
                "inspect",
                "impact",
                str(self.project_root),
                "--files",
                user_service_path,
                "--output",
                "text",
            ],
        )

        assert result.exit_code == 0
        assert "Inspecting impact for project" in result.output
        assert "Target files" in result.output
        assert "Impact inspection completed" in result.output

    def test_inspect_impact_multiple_files(self):
        """Test inspect impact command with multiple files."""
        user_service_path = str(
            self.project_root / "src" / "test_project" / "user_service.py"
        )
        auth_path = str(self.project_root / "src" / "test_project" / "auth.py")

        result = self.runner.invoke(
            cli,
            [
                "inspect",
                "impact",
                str(self.project_root),
                "--files",
                user_service_path,
                "--files",
                auth_path,
                "--output",
                "text",
            ],
        )

        assert result.exit_code == 0
        assert "Inspecting impact for project" in result.output
        assert "Target files" in result.output
        assert "Impact inspection completed" in result.output

    def test_inspect_centrality_single_file(self):
        """Test inspect centrality command with a single file."""
        user_service_path = str(
            self.project_root / "src" / "test_project" / "user_service.py"
        )

        result = self.runner.invoke(
            cli,
            [
                "inspect",
                "centrality",
                str(self.project_root),
                "--files",
                user_service_path,
                "--output",
                "text",
            ],
        )

        assert result.exit_code == 0
        assert "Inspecting centrality for project" in result.output
        assert "Files" in result.output
        assert "Centrality inspection completed" in result.output

    def test_inspect_centrality_multiple_files(self):
        """Test inspect centrality command with multiple files."""
        user_service_path = str(
            self.project_root / "src" / "test_project" / "user_service.py"
        )
        auth_path = str(self.project_root / "src" / "test_project" / "auth.py")

        result = self.runner.invoke(
            cli,
            [
                "inspect",
                "centrality",
                str(self.project_root),
                "--files",
                user_service_path,
                "--files",
                auth_path,
                "--output",
                "text",
            ],
        )

        assert result.exit_code == 0
        assert "Inspecting centrality for project" in result.output
        assert "Files" in result.output
        assert "Centrality inspection completed" in result.output

    def test_inspect_impact_json_output(self):
        """Test inspect impact command with JSON output."""
        user_service_path = str(
            self.project_root / "src" / "test_project" / "user_service.py"
        )

        result = self.runner.invoke(
            cli,
            [
                "inspect",
                "impact",
                str(self.project_root),
                "--files",
                user_service_path,
                "--output",
                "json",
            ],
        )

        assert result.exit_code == 0
        # Inspect commands show status messages and perform analysis
        assert "Inspecting impact for project" in result.output
        assert "Impact inspection completed" in result.output
        assert "Output format: json" in result.output

    def test_inspect_centrality_json_output(self):
        """Test inspect centrality command with JSON output."""
        user_service_path = str(
            self.project_root / "src" / "test_project" / "user_service.py"
        )

        result = self.runner.invoke(
            cli,
            [
                "inspect",
                "centrality",
                str(self.project_root),
                "--files",
                user_service_path,
                "--output",
                "json",
            ],
        )

        assert result.exit_code == 0
        # Inspect commands show status messages and perform analysis
        assert "Inspecting centrality for project" in result.output
        assert "Centrality inspection completed" in result.output
        assert "Output format: json" in result.output

    def test_inspect_impact_with_token_budget(self):
        """Test inspect impact command with custom token budget."""
        user_service_path = str(
            self.project_root / "src" / "test_project" / "user_service.py"
        )

        result = self.runner.invoke(
            cli,
            [
                "inspect",
                "impact",
                str(self.project_root),
                "--files",
                user_service_path,
                "--output",
                "text",
                "--max-tokens",
                "2000",
            ],
        )

        assert result.exit_code == 0
        assert "Inspecting impact for project" in result.output
        assert "Impact inspection completed" in result.output

    def test_inspect_centrality_with_token_budget(self):
        """Test inspect centrality command with custom token budget."""
        user_service_path = str(
            self.project_root / "src" / "test_project" / "user_service.py"
        )

        result = self.runner.invoke(
            cli,
            [
                "inspect",
                "centrality",
                str(self.project_root),
                "--files",
                user_service_path,
                "--output",
                "text",
                "--max-tokens",
                "2000",
            ],
        )

        assert result.exit_code == 0
        assert "Inspecting centrality for project" in result.output
        assert "Centrality inspection completed" in result.output

    def test_inspect_impact_no_files_specified(self):
        """Test inspect impact command without specifying files."""
        result = self.runner.invoke(
            cli,
            ["inspect", "impact", str(self.project_root), "--output", "text"],
        )

        assert result.exit_code == 2
        assert "Missing option '--files' / '-f'" in result.output

    def test_inspect_centrality_no_files_fallback(self):
        """Test inspect centrality command without files falls back to top files."""
        result = self.runner.invoke(
            cli, ["inspect", "centrality", str(self.project_root), "--output", "text"]
        )

        assert result.exit_code == 0
        assert "Inspecting centrality for project" in result.output
        assert "Centrality inspection completed" in result.output

    def test_inspect_impact_table_output(self):
        """Test inspect impact command with table output."""
        user_service_path = str(
            self.project_root / "src" / "test_project" / "user_service.py"
        )

        result = self.runner.invoke(
            cli,
            [
                "inspect",
                "impact",
                str(self.project_root),
                "--files",
                user_service_path,
                "--output",
                "text",
            ],
        )

        assert result.exit_code == 0
        assert "Inspecting impact for project" in result.output
        assert "Impact inspection completed" in result.output

    def test_inspect_centrality_table_output(self):
        """Test inspect centrality command with table output."""
        user_service_path = str(
            self.project_root / "src" / "test_project" / "user_service.py"
        )

        result = self.runner.invoke(
            cli,
            [
                "inspect",
                "centrality",
                str(self.project_root),
                "--files",
                user_service_path,
                "--output",
                "text",
            ],
        )

        assert result.exit_code == 0
        assert "Inspecting centrality for project" in result.output
        assert "Centrality inspection completed" in result.output

    def test_inspect_impact_verbose_output(self):
        """Test inspect impact command with verbose output."""
        user_service_path = str(
            self.project_root / "src" / "test_project" / "user_service.py"
        )

        result = self.runner.invoke(
            cli,
            [
                "inspect",
                "impact",
                str(self.project_root),
                "--files",
                user_service_path,
                "--output",
                "text",
                "--verbose",
            ],
        )

        assert result.exit_code == 0
        assert "Inspecting impact for project" in result.output
        assert "Impact inspection completed" in result.output

    def test_inspect_centrality_verbose_output(self):
        """Test inspect centrality command with verbose output."""
        user_service_path = str(
            self.project_root / "src" / "test_project" / "user_service.py"
        )

        result = self.runner.invoke(
            cli,
            [
                "inspect",
                "centrality",
                str(self.project_root),
                "--files",
                user_service_path,
                "--output",
                "text",
                "--verbose",
            ],
        )

        assert result.exit_code == 0
        assert "Inspecting centrality for project" in result.output
        assert "Centrality inspection completed" in result.output


class TestASTFileAnalyzerIntegration:
    """Integration tests for AST file analyzer with real files."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self._create_simple_test_file()

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_simple_test_file(self):
        """Create a simple test file for AST analysis."""
        test_file = self.project_root / "test_file.py"
        test_file.write_text(
            """# Test file for AST analysis
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional

def test_function(param1: str, param2: int = 10) -> bool:
    '''Test function with type hints'''
    result = param1 + str(param2)
    return len(result) > 0

class TestClass:
    def __init__(self, name: str):
        self.name = name
        self.value = 42

    def method1(self) -> str:
        return f"Hello {self.name}"

    def method2(self, items: List[str]) -> Dict[str, int]:
        return {item: len(item) for item in items}

# Function calls
result = test_function("test", 20)
obj = TestClass("example")
message = obj.method1()
counts = obj.method2(["a", "bb", "ccc"])
"""
        )
        self.test_file_path = str(test_file)

    def test_ast_analyzer_basic_functionality(self):
        """Test basic AST analyzer functionality."""
        # Create a mock cache manager
        mock_cache_manager = MagicMock(spec=CacheManager)
        # Create a TreeSitterParser with the project root and mock cache
        tree_sitter_parser_instance = MagicMock(spec=TreeSitterParser)
        # Inlined mock tags for this test
        mock_tags = [
            MagicMock(kind="import", name="os", line=2, alias=None, is_relative=False, resolved_path=None, symbols=[], module="os"),
            MagicMock(kind="import", name="sys", line=3, alias=None, is_relative=False, resolved_path=None, symbols=[], module="sys"),
            MagicMock(kind="import_from", name="Path", module="pathlib", line=4, alias=None, is_relative=False, resolved_path=None, symbols=["Path"]),
            MagicMock(kind="import_from", name="List", module="typing", line=5, alias=None, is_relative=False, resolved_path=None, symbols=["List", "Dict", "Optional"]),
            MagicMock(kind="function", name="test_function", line=7, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="class", name="TestClass", line=12, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="method", name="__init__", line=13, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="method", name="method1", line=16, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="method", name="method2", line=19, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="call", name="test_function", callee="test_function", line=23, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="call", name="TestClass", callee="TestClass", line=24, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="call", name="method1", callee="obj.method1", line=25, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="call", name="method2", callee="obj.method2", line=26, alias=None, is_relative=False, resolved_path=None, symbols=[]),
        ]
        tree_sitter_parser_instance.get_tags.return_value = mock_tags # Configure mock get_tags

        analyzer = ASTFileAnalyzer(str(self.project_root), tree_sitter_parser=tree_sitter_parser_instance)
        result = analyzer.analyze_file(self.test_file_path)

        assert result.file_path == self.test_file_path
        assert len(result.imports) >= 4  # os, sys, pathlib, typing
        assert (
            len(result.function_calls) >= 4
        )  # test_function, TestClass, method1, method2
        assert (
            len(result.defined_functions) == 1
        )  # test_function (only function from mock tags)
        assert len(result.defined_classes) == 1  # TestClass
        assert len(result.defined_methods) == 3 # __init__, method1, method2
        assert result.line_count > 0
        assert len(result.analysis_errors) == 0

    def test_ast_analyzer_import_analysis(self):
        """Test AST analyzer import analysis."""
        mock_cache_manager = MagicMock(spec=CacheManager)
        tree_sitter_parser_instance = MagicMock(spec=TreeSitterParser)
        # Inlined mock tags for this test
        mock_tags = [
            MagicMock(kind="import", name="os", line=2, alias=None, is_relative=False, resolved_path=None, symbols=[], module="os"),
            MagicMock(kind="import", name="sys", line=3, alias=None, is_relative=False, resolved_path=None, symbols=[], module="sys"),
            MagicMock(kind="import_from", name="Path", module="pathlib", line=4, alias=None, is_relative=False, resolved_path=None, symbols=["Path"]),
            MagicMock(kind="import_from", name="List", module="typing", line=5, alias=None, is_relative=False, resolved_path=None, symbols=["List", "Dict", "Optional"]),
            MagicMock(kind="function", name="test_function", line=7, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="class", name="TestClass", line=12, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="method", name="__init__", line=13, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="method", name="method1", line=16, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="method", name="method2", line=19, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="call", name="test_function", callee="test_function", line=23, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="call", name="TestClass", callee="TestClass", line=24, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="call", name="method1", callee="obj.method1", line=25, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="call", name="method2", callee="obj.method2", line=26, alias=None, is_relative=False, resolved_path=None, symbols=[]),
        ]
        tree_sitter_parser_instance.get_tags.return_value = mock_tags # Configure mock get_tags

        analyzer = ASTFileAnalyzer(str(self.project_root), tree_sitter_parser=tree_sitter_parser_instance)
        result = analyzer.analyze_file(self.test_file_path)

        # Check specific imports
        import_modules = [imp.module for imp in result.imports]
        assert "os" in import_modules
        assert "sys" in import_modules
        assert "pathlib" in import_modules
        assert "typing" in import_modules

        # Check import types
        from_imports = [
            imp for imp in result.imports if imp.symbols
        ]  # from imports have symbols
        standard_imports = [
            imp for imp in result.imports if not imp.symbols
        ]  # standard imports have no symbols

        assert len(from_imports) == 2  # pathlib.Path, typing.List
        assert len(standard_imports) == 2  # os, sys

    def test_ast_analyzer_function_call_analysis(self):
        """Test AST analyzer function call analysis."""
        mock_cache_manager = MagicMock(spec=CacheManager)
        tree_sitter_parser_instance = MagicMock(spec=TreeSitterParser)
        # Inlined mock tags for this test
        mock_tags = [
            MagicMock(kind="import", name="os", line=2, alias=None, is_relative=False, resolved_path=None, symbols=[], module="os"),
            MagicMock(kind="import", name="sys", line=3, alias=None, is_relative=False, resolved_path=None, symbols=[], module="sys"),
            MagicMock(kind="import_from", name="Path", module="pathlib", line=4, alias=None, is_relative=False, resolved_path=None, symbols=["Path"]),
            MagicMock(kind="import_from", name="List", module="typing", line=5, alias=None, is_relative=False, resolved_path=None, symbols=["List", "Dict", "Optional"]),
            MagicMock(kind="function", name="test_function", line=7, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="class", name="TestClass", line=12, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="method", name="__init__", line=13, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="method", name="method1", line=16, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="method", name="method2", line=19, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="call", name="test_function", callee="test_function", line=23, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="call", name="TestClass", callee="TestClass", line=24, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="call", name="method1", callee="obj.method1", line=25, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="call", name="method2", callee="obj.method2", line=26, alias=None, is_relative=False, resolved_path=None, symbols=[]),
        ]
        tree_sitter_parser_instance.get_tags.return_value = mock_tags # Configure mock get_tags

        analyzer = ASTFileAnalyzer(str(self.project_root), tree_sitter_parser=tree_sitter_parser_instance)
        result = analyzer.analyze_file(self.test_file_path)

        # Check function calls
        function_names = [call.callee for call in result.function_calls]
        assert "test_function" in function_names
        assert "TestClass" in function_names
        assert "obj.method1" in function_names # Updated assertion
        assert "obj.method2" in function_names # Updated assertion
        assert len(function_names) == 4 # Ensure all 4 calls are captured

    def test_ast_analyzer_multiple_files(self):
        """Test AST analyzer with multiple files."""
        # Create another test file
        test_file2 = self.project_root / "test_file2.py"
        test_file2.write_text(
            """# Second test file
import test_file
from test_file import TestClass

def another_function():
    obj = TestClass("test")
    return obj.method1()
"""
        )

        # For multiple files, we'll need to mock get_tags for each file path
        mock_cache_manager = MagicMock(spec=CacheManager)
        tree_sitter_parser_instance = MagicMock(spec=TreeSitterParser)

        # Inlined mock tags for the first file
        mock_tags_file1 = [
            MagicMock(kind="import", name="os", line=2, alias=None, is_relative=False, resolved_path=None, symbols=[], module="os"),
            MagicMock(kind="import", name="sys", line=3, alias=None, is_relative=False, resolved_path=None, symbols=[], module="sys"),
            MagicMock(kind="import_from", name="Path", module="pathlib", line=4, alias=None, is_relative=False, resolved_path=None, symbols=["Path"]),
            MagicMock(kind="import_from", name="List", module="typing", line=5, alias=None, is_relative=False, resolved_path=None, symbols=["List", "Dict", "Optional"]),
            MagicMock(kind="function", name="test_function", line=7, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="class", name="TestClass", line=12, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="method", name="__init__", line=13, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="method", name="method1", line=16, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="method", name="method2", line=19, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="call", name="test_function", callee="test_function", line=23, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="call", name="TestClass", callee="TestClass", line=24, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="call", name="method1", callee="obj.method1", line=25, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="call", name="method2", callee="obj.method2", line=26, alias=None, is_relative=False, resolved_path=None, symbols=[]),
        ]
        # Inlined mock tags for the second file
        mock_tags_file2 = [
            MagicMock(kind="import", name="test_file", line=2, alias=None, is_relative=False, resolved_path=None, symbols=[], module="test_file"),
            MagicMock(kind="import_from", name="TestClass", module="test_file", line=3, alias=None, is_relative=False, resolved_path=None, symbols=["TestClass"]),
            MagicMock(kind="function", name="another_function", line=5, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="call", name="TestClass", callee="TestClass", line=6, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="call", name="method1", callee="obj.method1", line=7, alias=None, is_relative=False, resolved_path=None, symbols=[]),
        ]

        # Mock get_tags for each file path correctly
        def get_tags_side_effect(file_path, use_cache=True):
            if file_path == self.test_file_path:
                return mock_tags_file1
            elif file_path == str(test_file2):
                return mock_tags_file2
            return [] # Default empty list if file not mocked

        tree_sitter_parser_instance.get_tags.side_effect = get_tags_side_effect

        analyzer = ASTFileAnalyzer(str(self.project_root), tree_sitter_parser=tree_sitter_parser_instance)
        results = analyzer.analyze_multiple_files(
            [self.test_file_path, str(test_file2)]
        )

        assert len(results) == 2
        assert self.test_file_path in results
        assert str(test_file2) in results

        # Check that the second file imports from the first
        second_result = results[str(test_file2)]
        import_modules = [imp.module for imp in second_result.imports]
        assert "test_file" in import_modules
        assert len(import_modules) == 2 # test_file (import), test_file (from import)
        assert len(second_result.defined_functions) == 1 # another_function
        assert len(second_result.defined_methods) == 0 # No methods in second file
        assert len(second_result.defined_classes) == 0 # No classes in second file

    def test_ast_analyzer_reverse_dependencies(self):
        """Test AST analyzer reverse dependency detection."""
        # Create a file that imports from the test file
        dependent_file = self.project_root / "dependent.py"
        dependent_file.write_text(
            """# File that depends on test_file
import test_file
from test_file import TestClass, test_function

def use_test_file():
    result = test_function("hello", 5)
    obj = TestClass("world")
    return obj.method1()
"""
        )

        mock_cache_manager = MagicMock(spec=CacheManager)
        tree_sitter_parser_instance = MagicMock(spec=TreeSitterParser)

        # Inlined mock tags for this test
        mock_tags_file1 = [
            MagicMock(kind="import", name="os", line=2, alias=None, is_relative=False, resolved_path=None, symbols=[], module="os"),
            MagicMock(kind="import", name="sys", line=3, alias=None, is_relative=False, resolved_path=None, symbols=[], module="sys"),
            MagicMock(kind="import_from", name="Path", module="pathlib", line=4, alias=None, is_relative=False, resolved_path=None, symbols=["Path"]),
            MagicMock(kind="import_from", name="List", module="typing", line=5, alias=None, is_relative=False, resolved_path=None, symbols=["List", "Dict", "Optional"]),
            MagicMock(kind="function", name="test_function", line=7, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="class", name="TestClass", line=12, alias=None, is_relative=False, resolved_path=None, symbols=[]),
        ]
        mock_tags_dependent_file = [
            MagicMock(kind="import", name="test_file", line=2, alias=None, is_relative=False, resolved_path=None, symbols=[], module="test_file"),
            MagicMock(kind="import_from", name="TestClass", module="test_file", line=3, alias=None, is_relative=False, resolved_path=None, symbols=["TestClass", "test_function"]),
            MagicMock(kind="function", name="use_test_file", line=5, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="call", name="test_function", callee="test_function", line=6, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="call", name="TestClass", callee="TestClass", line=7, alias=None, is_relative=False, resolved_path=None, symbols=[]),
            MagicMock(kind="call", name="method1", callee="obj.method1", line=8, alias=None, is_relative=False, resolved_path=None, symbols=[]),
        ]

        # Mock get_tags for both files correctly
        def get_tags_side_effect_deps(file_path, use_cache=True):
            if file_path == self.test_file_path:
                return mock_tags_file1
            elif file_path == str(dependent_file):
                return mock_tags_dependent_file
            return []

        tree_sitter_parser_instance.get_tags.side_effect = get_tags_side_effect_deps

        analyzer = ASTFileAnalyzer(str(self.project_root), tree_sitter_parser=tree_sitter_parser_instance)
        all_files = [self.test_file_path, str(dependent_file)]

        reverse_deps = analyzer.find_reverse_dependencies(
            self.test_file_path, all_files
        )

        assert len(reverse_deps) >= 1
        assert any(dep.source_file == str(dependent_file) for dep in reverse_deps)

    def test_ast_analyzer_error_handling(self):
        """Test AST analyzer error handling with invalid files."""
        # Create a file with syntax errors
        invalid_file = self.project_root / "invalid.py"
        invalid_file.write_text(
            """# Invalid Python syntax
def broken_function(
    # Missing closing parenthesis
    return "broken"
"""
        )

        mock_cache_manager = MagicMock(spec=CacheManager)
        tree_sitter_parser_instance = MagicMock(spec=TreeSitterParser)
        # Mock get_tags to simulate a parsing error by returning an empty list and setting analysis_errors
        tree_sitter_parser_instance.get_tags.return_value = [] # Return empty list on error
        # ASTFileAnalyzer expects errors to be populated during analysis if parsing fails
        # Mock the analyzer itself to control analysis_errors directly if needed, or check the parsing path

        # For simplicity, we'll assume a parsing error from TreeSitterParser results in an empty tags list and the analyzer adding an error.
        # The analyzer's internal error handling is what we're truly testing.

        analyzer = ASTFileAnalyzer(str(self.project_root), tree_sitter_parser=tree_sitter_parser_instance)
        result = analyzer.analyze_file(str(invalid_file))

        assert result.file_path == str(invalid_file)
        assert len(result.analysis_errors) > 0
        # The error message is now from ASTFileAnalyzer's error handling, not a direct mock. We can simplify to 'Error analyzing file'
        assert "Syntax error at line 2: '(' was never closed" in result.analysis_errors[0] # Updated assertion to expect specific error

    def test_ast_analyzer_cache_functionality(self):
        """Test AST analyzer caching functionality."""
        # The analyzer's internal cache will be used directly
        tree_sitter_parser_instance = MagicMock(spec=TreeSitterParser)
        # Mock get_tags to return tags
        mock_tags = [
            MagicMock(kind="import", name="os", line=2, alias=None, is_relative=False, resolved_path=None, symbols=[], module="os"),
            MagicMock(kind="function", name="test_function", line=7, alias=None, is_relative=False, resolved_path=None, symbols=[]),
        ]
        tree_sitter_parser_instance.get_tags.return_value = mock_tags

        # Instantiate ASTFileAnalyzer - its internal cache is an empty dict by default
        analyzer = ASTFileAnalyzer(str(self.project_root), tree_sitter_parser=tree_sitter_parser_instance)
        analyzer.cache_enabled = True # Ensure caching is enabled

        # First analysis - should populate analyzer's internal cache
        result1 = analyzer.analyze_file(self.test_file_path)

        # Second analysis - should use analyzer's internal cache, so get_tags should not be called again
        result2 = analyzer.analyze_file(self.test_file_path)

        # Assert that get_tags was called only once due to internal caching by ASTFileAnalyzer
        tree_sitter_parser_instance.get_tags.assert_called_once_with(self.test_file_path, use_cache=True) # Ensure tree-sitter's cache is used

        # Results should be identical
        assert result1.file_path == result2.file_path
        assert len(result1.imports) == len(result2.imports)
        assert len(result1.function_calls) == len(result2.function_calls)

        # Check cache stats - these are ASTFileAnalyzer's internal stats
        cache_stats = analyzer.get_cache_stats()
        assert cache_stats["cache_enabled"] is True
        assert cache_stats["cache_size"] == 1 # One item cached

        # Clear cache - should clear ASTFileAnalyzer's internal cache
        analyzer.clear_cache()
        cache_stats_after = analyzer.get_cache_stats()
        assert cache_stats_after["cache_size"] == 0 # Verify cache size is 0 after clear
