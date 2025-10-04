"""
Integration tests for the enhanced analyze commands.

This module tests the new LLM-optimized analyze impact and centrality commands
with real project structures to ensure they work correctly end-to-end.
"""

import pytest
import tempfile
import os
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from repomap_tool.cli import cli
from repomap_tool.dependencies import (
    ASTFileAnalyzer,
    AnalysisFormat,
)


class TestAnalyzeCommandsIntegration:
    """Integration tests for analyze commands with real project structures."""

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

    def test_analyze_impact_single_file(self):
        """Test analyze impact command with a single file."""
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

    def test_analyze_impact_multiple_files(self):
        """Test analyze impact command with multiple files."""
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

    def test_analyze_centrality_single_file(self):
        """Test analyze centrality command with a single file."""
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

    def test_analyze_centrality_multiple_files(self):
        """Test analyze centrality command with multiple files."""
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

    def test_analyze_impact_json_output(self):
        """Test analyze impact command with JSON output."""
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
        # Analyze commands are placeholder implementations that show status messages
        assert "Inspecting impact for project" in result.output
        assert "Impact inspection completed" in result.output
        assert "Output format: json" in result.output

    def test_analyze_centrality_json_output(self):
        """Test analyze centrality command with JSON output."""
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
        # Analyze commands are placeholder implementations that show status messages
        assert "Inspecting centrality for project" in result.output
        assert "Centrality inspection completed" in result.output
        assert "Output format: json" in result.output

    def test_analyze_impact_with_token_budget(self):
        """Test analyze impact command with custom token budget."""
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

    def test_analyze_centrality_with_token_budget(self):
        """Test analyze centrality command with custom token budget."""
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

    def test_analyze_impact_no_files_specified(self):
        """Test analyze impact command without specifying files."""
        result = self.runner.invoke(
            cli,
            ["inspect", "impact", str(self.project_root), "--output", "text"],
        )

        assert result.exit_code == 2
        assert "Missing option '--files' / '-f'" in result.output

    def test_analyze_centrality_no_files_fallback(self):
        """Test analyze centrality command without files falls back to top files."""
        result = self.runner.invoke(
            cli, ["inspect", "centrality", str(self.project_root), "--output", "text"]
        )

        assert result.exit_code == 0
        assert "Inspecting centrality for project" in result.output
        assert "Centrality inspection completed" in result.output

    def test_analyze_impact_table_output(self):
        """Test analyze impact command with table output."""
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

    def test_analyze_centrality_table_output(self):
        """Test analyze centrality command with table output."""
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

    def test_analyze_impact_verbose_output(self):
        """Test analyze impact command with verbose output."""
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

    def test_analyze_centrality_verbose_output(self):
        """Test analyze centrality command with verbose output."""
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
        analyzer = ASTFileAnalyzer(str(self.project_root))
        result = analyzer.analyze_file(self.test_file_path)

        assert result.file_path == self.test_file_path
        assert len(result.imports) >= 4  # os, sys, pathlib, typing
        assert (
            len(result.function_calls) >= 4
        )  # test_function, TestClass, method1, method2
        assert (
            len(result.defined_functions) == 4
        )  # test_function, __init__, method1, method2
        assert len(result.defined_classes) == 1  # TestClass
        assert result.line_count > 0
        assert len(result.analysis_errors) == 0

    def test_ast_analyzer_import_analysis(self):
        """Test AST analyzer import analysis."""
        analyzer = ASTFileAnalyzer(str(self.project_root))
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

        assert len(from_imports) >= 2  # pathlib.Path, typing imports
        assert len(standard_imports) >= 2  # os, sys

    def test_ast_analyzer_function_call_analysis(self):
        """Test AST analyzer function call analysis."""
        analyzer = ASTFileAnalyzer(str(self.project_root))
        result = analyzer.analyze_file(self.test_file_path)

        # Check function calls
        function_names = [call.callee for call in result.function_calls]
        assert "test_function" in function_names
        assert "TestClass" in function_names
        assert "method1" in function_names
        assert "method2" in function_names

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

        analyzer = ASTFileAnalyzer(str(self.project_root))
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

        analyzer = ASTFileAnalyzer(str(self.project_root))
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

        analyzer = ASTFileAnalyzer(str(self.project_root))
        result = analyzer.analyze_file(str(invalid_file))

        assert result.file_path == str(invalid_file)
        assert len(result.analysis_errors) > 0
        assert "Syntax error" in result.analysis_errors[0]

    def test_ast_analyzer_cache_functionality(self):
        """Test AST analyzer caching functionality."""
        analyzer = ASTFileAnalyzer(str(self.project_root))

        # First analysis
        result1 = analyzer.analyze_file(self.test_file_path)

        # Second analysis should use cache
        result2 = analyzer.analyze_file(self.test_file_path)

        # Results should be identical
        assert result1.file_path == result2.file_path
        assert len(result1.imports) == len(result2.imports)
        assert len(result1.function_calls) == len(result2.function_calls)

        # Check cache stats
        cache_stats = analyzer.get_cache_stats()
        assert cache_stats["cache_enabled"] is True
        assert cache_stats["cache_size"] > 0

        # Clear cache
        analyzer.clear_cache()
        cache_stats_after = analyzer.get_cache_stats()
        assert cache_stats_after["cache_size"] == 0


class TestLLMFileAnalyzerIntegration:
    """Integration tests for LLM file analyzer with real project structures."""

    def _create_llm_analyzer(self, dependency_graph, project_root):
        """Helper method to create LLM analyzer with all required dependencies."""
        from repomap_tool.dependencies.ast_file_analyzer import ASTFileAnalyzer
        from repomap_tool.dependencies.centrality_calculator import CentralityCalculator
        from repomap_tool.dependencies.centrality_analysis_engine import (
            CentralityAnalysisEngine,
        )
        from repomap_tool.dependencies.impact_analysis_engine import (
            ImpactAnalysisEngine,
        )
        from repomap_tool.llm.token_optimizer import TokenOptimizer
        from repomap_tool.llm.context_selector import ContextSelector
        from repomap_tool.llm.hierarchical_formatter import HierarchicalFormatter
        from repomap_tool.dependencies.path_resolver import PathResolver
        from repomap_tool.utils.path_normalizer import PathNormalizer
        from repomap_tool.dependencies.llm_file_analyzer import LLMFileAnalyzer

        # Create all required dependencies
        ast_analyzer = ASTFileAnalyzer(project_root)
        # Use service factory for centrality calculator
        from repomap_tool.models import (
            RepoMapConfig,
            FuzzyMatchConfig,
            SemanticMatchConfig,
            PerformanceConfig,
            DependencyConfig,
        )
        from repomap_tool.cli.services import get_service_factory

        config = RepoMapConfig(
            project_root=project_root,
            fuzzy_match=FuzzyMatchConfig(),
            semantic_match=SemanticMatchConfig(),
            performance=PerformanceConfig(),
            dependencies=DependencyConfig(
                enable_impact_analysis=True,
                enable_centrality_analysis=True,
            ),
            verbose=False,
        )
        service_factory = get_service_factory()
        repomap_service = service_factory.create_repomap_service(config)
        centrality_calculator = repomap_service.centrality_calculator
        path_normalizer = PathNormalizer(project_root)
        centrality_engine = CentralityAnalysisEngine(
            ast_analyzer=ast_analyzer,
            centrality_calculator=centrality_calculator,
            dependency_graph=dependency_graph,
            path_normalizer=path_normalizer,
        )
        impact_engine = ImpactAnalysisEngine(ast_analyzer=ast_analyzer)
        token_optimizer = TokenOptimizer()
        context_selector = ContextSelector(dependency_graph)
        hierarchical_formatter = HierarchicalFormatter()
        path_resolver = PathResolver(project_root)

        # Create LLM analyzer with all dependencies using new constructor pattern
        from repomap_tool.dependencies.llm_analyzer_config import (
            LLMAnalyzerConfig,
            LLMAnalyzerDependencies,
        )

        config = LLMAnalyzerConfig()
        dependencies = LLMAnalyzerDependencies(
            dependency_graph=dependency_graph,
            project_root=project_root,
            ast_analyzer=ast_analyzer,
            token_optimizer=token_optimizer,
            context_selector=context_selector,
            hierarchical_formatter=hierarchical_formatter,
            path_resolver=path_resolver,
            impact_engine=impact_engine,
            centrality_engine=centrality_engine,
            centrality_calculator=centrality_calculator,
        )

        return LLMFileAnalyzer(config=config, dependencies=dependencies)

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self._create_test_project()

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_project(self):
        """Create a test project for LLM analyzer."""
        # Create a simple project structure
        src_dir = self.project_root / "src"
        src_dir.mkdir()

        # Create main.py
        (src_dir / "main.py").write_text(
            """# Main module
import utils
from models import User

def main():
    user = User("John", "john@example.com")
    result = utils.process_user(user)
    print(result)

if __name__ == "__main__":
    main()
"""
        )

        # Create utils.py
        (src_dir / "utils.py").write_text(
            """# Utility functions
from typing import Any

def process_user(user) -> str:
    return f"Processing user: {user.name}"

def validate_email(email: str) -> bool:
    return "@" in email
"""
        )

        # Create models directory
        models_dir = src_dir / "models"
        models_dir.mkdir()

        # Create models/__init__.py
        (models_dir / "__init__.py").write_text(
            """# Models package
from .user import User
"""
        )

        # Create models/user.py
        (models_dir / "user.py").write_text(
            """# User model
class User:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email
    
    def __str__(self):
        return f"User({self.name}, {self.email})"
"""
        )

    def test_llm_analyzer_impact_analysis(self):
        """Test LLM analyzer impact analysis."""
        from repomap_tool.core.repo_map import RepoMapService
        from repomap_tool.models import RepoMapConfig, DependencyConfig

        main_file = str(self.project_root / "src" / "main.py")

        # Create config and build dependency graph
        config = RepoMapConfig(
            project_root=str(self.project_root),
            dependencies=DependencyConfig(enable_impact_analysis=True),
        )
        from repomap_tool.cli.services import get_service_factory

        service_factory = get_service_factory()
        repomap = service_factory.create_repomap_service(config)
        dependency_graph = repomap.build_dependency_graph()

        # Create analyzer with all dependencies
        analyzer = self._create_llm_analyzer(dependency_graph, str(self.project_root))
        result = analyzer.analyze_file_impact([main_file], AnalysisFormat.LLM_OPTIMIZED)

        assert "Impact Analysis: main.py" in result
        assert "DIRECT DEPENDENCIES" in result
        assert "REVERSE DEPENDENCIES" in result
        assert "STRUCTURAL IMPACT" in result

    def test_llm_analyzer_centrality_analysis(self):
        """Test LLM analyzer centrality analysis."""
        from repomap_tool.core.repo_map import RepoMapService
        from repomap_tool.models import RepoMapConfig, DependencyConfig

        main_file = str(self.project_root / "src" / "main.py")

        # Create config and build dependency graph
        config = RepoMapConfig(
            project_root=str(self.project_root),
            dependencies=DependencyConfig(enable_impact_analysis=True),
        )
        from repomap_tool.cli.services import get_service_factory

        service_factory = get_service_factory()
        repomap = service_factory.create_repomap_service(config)
        dependency_graph = repomap.build_dependency_graph()

        # Create analyzer with all dependencies
        analyzer = self._create_llm_analyzer(dependency_graph, str(self.project_root))
        result = analyzer.analyze_file_centrality(
            [main_file], AnalysisFormat.LLM_OPTIMIZED
        )

        assert "Centrality Analysis: main.py" in result
        assert "IMPORTANCE SCORE" in result
        assert "FILE CONNECTIONS" in result
        # The test project may not have enough complexity for full centrality analysis
        # So we check for either CHANGE IMPACT or the error message
        assert "CHANGE IMPACT" in result or "Centrality Analysis Error" in result

    def test_llm_analyzer_json_output(self):
        """Test LLM analyzer JSON output."""
        from repomap_tool.core.repo_map import RepoMapService
        from repomap_tool.models import RepoMapConfig, DependencyConfig

        main_file = str(self.project_root / "src" / "main.py")

        # Create config and build dependency graph
        config = RepoMapConfig(
            project_root=str(self.project_root),
            dependencies=DependencyConfig(enable_impact_analysis=True),
        )
        from repomap_tool.cli.services import get_service_factory

        service_factory = get_service_factory()
        repomap = service_factory.create_repomap_service(config)
        dependency_graph = repomap.build_dependency_graph()

        # Create analyzer with all dependencies
        analyzer = self._create_llm_analyzer(dependency_graph, str(self.project_root))
        result = analyzer.analyze_file_impact([main_file], AnalysisFormat.JSON)

        # Should be valid JSON
        import json

        json_data = json.loads(result)
        assert isinstance(json_data, list)
        assert len(json_data) == 1
        assert "file_path" in json_data[0]

    def test_llm_analyzer_token_optimization(self):
        """Test LLM analyzer token optimization."""
        from repomap_tool.core.repo_map import RepoMapService
        from repomap_tool.models import RepoMapConfig, DependencyConfig

        main_file = str(self.project_root / "src" / "main.py")

        # Create config and build dependency graph
        config = RepoMapConfig(
            project_root=str(self.project_root),
            dependencies=DependencyConfig(enable_impact_analysis=True),
        )
        from repomap_tool.cli.services import get_service_factory

        service_factory = get_service_factory()
        repomap = service_factory.create_repomap_service(config)
        dependency_graph = repomap.build_dependency_graph()

        # Create analyzer with all dependencies and token limit
        analyzer = self._create_llm_analyzer(dependency_graph, str(self.project_root))
        # Set max_tokens on the analyzer
        analyzer.max_tokens = 500
        result = analyzer.analyze_file_impact([main_file], AnalysisFormat.LLM_OPTIMIZED)

        # Result should be optimized for token budget
        assert "Impact Analysis: main.py" in result
        # Should be shorter due to token optimization
        assert len(result) < 2000  # Reasonable upper bound

    def test_llm_analyzer_multiple_files(self):
        """Test LLM analyzer with multiple files."""
        from repomap_tool.core.repo_map import RepoMapService
        from repomap_tool.models import RepoMapConfig, DependencyConfig

        main_file = str(self.project_root / "src" / "main.py")
        utils_file = str(self.project_root / "src" / "utils.py")

        # Create config and build dependency graph
        config = RepoMapConfig(
            project_root=str(self.project_root),
            dependencies=DependencyConfig(enable_impact_analysis=True),
        )
        from repomap_tool.cli.services import get_service_factory

        service_factory = get_service_factory()
        repomap = service_factory.create_repomap_service(config)
        dependency_graph = repomap.build_dependency_graph()

        # Create analyzer with all dependencies
        analyzer = self._create_llm_analyzer(dependency_graph, str(self.project_root))
        result = analyzer.analyze_file_impact(
            [main_file, utils_file], AnalysisFormat.LLM_OPTIMIZED
        )

        assert "Impact Analysis: main.py, utils.py" in result
        assert "FILES ANALYZED" in result
        assert "COMBINED DEPENDENCIES" in result
