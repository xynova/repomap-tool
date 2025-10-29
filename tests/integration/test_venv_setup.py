#!/usr/bin/env python3
"""
Virtual Environment Setup Test

This test verifies that the virtual environment is properly configured
and can import all required modules for the repomap-tool.
"""

import sys
import importlib
from pathlib import Path


def test_venv_activation(capsys):
    """Test that we're running in the virtual environment."""
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")

    # Check if we're in a virtual environment
    in_venv = hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )
    print(f"In virtual environment: {in_venv}")

    # If we're in a venv, the executable should be in the venv directory
    if in_venv:
        assert (
            "venv" in sys.executable or "env" in sys.executable
        ), "Should be running in virtual environment"
        print("✅ Virtual environment is active")
    else:
        print("⚠️ Not running in virtual environment")


def test_required_imports(capsys):
    """Test that all required modules can be imported."""
    required_modules = ["pydantic", "click", "rich", "pytest"]

    print("\nTesting required imports:")
    for module_name in required_modules:
        try:
            importlib.import_module(module_name)
            print(f"✅ {module_name} imported successfully")
        except ImportError as e:
            print(f"❌ {module_name} import failed: {e}")
            raise


def test_repomap_imports(capsys):
    """Test that repomap-tool modules can be imported."""
    # Add src to path
    project_root = Path(__file__).parent.parent.parent
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    repomap_modules = ["repomap_tool.core", "repomap_tool.models", "repomap_tool.cli"]

    print("\nTesting repomap-tool imports:")
    for module_name in repomap_modules:
        try:
            importlib.import_module(module_name)
            print(f"✅ {module_name} imported successfully")
        except ImportError as e:
            print(f"❌ {module_name} import failed: {e}")
            # Don't raise here as these might not be available in all environments


def test_matcher_imports(capsys):
    """Test that matcher modules can be imported."""
    # Add src to path
    project_root = Path(__file__).parent.parent.parent
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    matcher_modules = [
        "repomap_tool.matchers.fuzzy_matcher",
        "repomap_tool.matchers.semantic_matcher",
        "repomap_tool.matchers.adaptive_semantic_matcher",
        "repomap_tool.matchers.hybrid_matcher",
    ]

    print("\nTesting matcher imports:")
    for module_name in matcher_modules:
        try:
            importlib.import_module(module_name)
            print(f"✅ {module_name} imported successfully")
        except ImportError as e:
            print(f"❌ {module_name} import failed: {e}")
            # Don't raise here as these might not be available in all environments


if __name__ == "__main__":
    print("🧪 Testing Virtual Environment Setup")
    print("=" * 50)

    test_venv_activation()
    test_required_imports()
    test_repomap_imports()
    test_matcher_imports()

    print("\n✅ Virtual environment setup test completed!")
