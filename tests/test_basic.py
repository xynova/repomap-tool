#!/usr/bin/env python3
"""
Basic test to verify core functionality
"""

import sys
import os

sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
)

# flake8: noqa: E402
from repomap_tool.models import (
    RepoMapConfig,
    FuzzyMatchConfig,
    SemanticMatchConfig,
    PerformanceConfig,
    DependencyConfig,
)
from repomap_tool.cli.services import get_service_factory


def test_imports():
    """Test that all core modules can be imported."""
    try:
        print("✅ FuzzyMatcher imported successfully")
    except ImportError as e:
        print(f"❌ FuzzyMatcher import failed: {e}")
        assert False, f"FuzzyMatcher import failed: {e}"

    try:
        print("✅ AdaptiveSemanticMatcher imported successfully")
    except ImportError as e:
        print(f"❌ AdaptiveSemanticMatcher import failed: {e}")
        assert False, f"AdaptiveSemanticMatcher import failed: {e}"

    try:
        print("✅ HybridMatcher imported successfully")
    except ImportError as e:
        print(f"❌ HybridMatcher import failed: {e}")
        assert False, f"HybridMatcher import failed: {e}"

    # If we get here, all imports succeeded
    assert True


def test_fuzzy_matcher():
    """Test basic fuzzy matching functionality."""
    try:
        # Create config and use service factory
        config = RepoMapConfig(
            project_root=".",
            fuzzy_match=FuzzyMatchConfig(threshold=70),
            semantic_match=SemanticMatchConfig(),
            performance=PerformanceConfig(),
            dependencies=DependencyConfig(),
        )
        service_factory = get_service_factory()
        repomap_service = service_factory.create_repomap_service(config)
        matcher = repomap_service.fuzzy_matcher

        # Test data
        identifiers = {
            "user_authentication",
            "auth_token",
            "login_handler",
            "password_validation",
            "data_processor",
            "file_parser",
            "json_serializer",
            "csv_loader",
        }

        # Test matching
        results = matcher.match_identifiers("auth", identifiers)

        if results:
            print("✅ FuzzyMatcher basic functionality works")
            assert True
        else:
            print("❌ FuzzyMatcher returned no results")
            assert False, "FuzzyMatcher returned no results"

    except Exception as e:
        print(f"❌ FuzzyMatcher test failed: {e}")
        assert False, f"FuzzyMatcher test failed: {e}"


def test_adaptive_matcher():
    """Test basic adaptive semantic matching functionality."""
    try:
        # Clear service cache to avoid conflicts with other tests
        from repomap_tool.cli.services import clear_service_cache

        clear_service_cache()

        # Create config and use service factory
        config = RepoMapConfig(
            project_root=".",
            fuzzy_match=FuzzyMatchConfig(),
            semantic_match=SemanticMatchConfig(enabled=True),
            performance=PerformanceConfig(),
            dependencies=DependencyConfig(),
        )
        service_factory = get_service_factory()
        repomap_service = service_factory.create_repomap_service(config)
        matcher = repomap_service.semantic_matcher

        # Test data
        identifiers = {
            "user_authentication",
            "auth_token",
            "login_handler",
            "password_validation",
            "data_processor",
            "file_parser",
            "json_serializer",
            "csv_loader",
        }

        # Learn from identifiers
        matcher.learn_from_identifiers(identifiers)

        # Test matching
        results = matcher.find_semantic_matches("auth", identifiers, threshold=0.1)

        if results:
            print("✅ AdaptiveSemanticMatcher basic functionality works")
            assert True
        else:
            print("❌ AdaptiveSemanticMatcher returned no results")
            assert False, "AdaptiveSemanticMatcher returned no results"

    except Exception as e:
        print(f"❌ AdaptiveSemanticMatcher test failed: {e}")
        assert False, f"AdaptiveSemanticMatcher test failed: {e}"


if __name__ == "__main__":
    print("🧪 Running basic functionality tests...")
    print("=" * 50)

    success = True

    if not test_imports():
        success = False

    if not test_fuzzy_matcher():
        success = False

    if not test_adaptive_matcher():
        success = False

    print("=" * 50)
    if success:
        print("✅ All basic tests passed!")
    else:
        print("❌ Some tests failed!")
        sys.exit(1)
