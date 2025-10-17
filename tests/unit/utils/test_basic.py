#!/usr/bin/env python3
"""
Basic test to verify core functionality
"""

import sys
import os

sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src")
)

# flake8: noqa: E402


def test_imports():
    """Test that all core modules can be imported."""
    try:
        from repomap_tool.code_search.fuzzy_matcher import FuzzyMatcher
        print("✅ FuzzyMatcher imported successfully")
    except ImportError as e:
        print(f"❌ FuzzyMatcher import failed: {e}")
        assert False, f"FuzzyMatcher import failed: {e}"

    try:
        from repomap_tool.code_search.adaptive_semantic_matcher import AdaptiveSemanticMatcher
        print("✅ AdaptiveSemanticMatcher imported successfully")
    except ImportError as e:
        print(f"❌ AdaptiveSemanticMatcher import failed: {e}")
        assert False, f"AdaptiveSemanticMatcher import failed: {e}"

    try:
        from repomap_tool.code_search.hybrid_matcher import HybridMatcher
        print("✅ HybridMatcher imported successfully")
    except ImportError as e:
        print(f"❌ HybridMatcher import failed: {e}")
        assert False, f"HybridMatcher import failed: {e}"

    # If we get here, all imports succeeded
    assert True




if __name__ == "__main__":
    print("🧪 Running basic import tests...")
    print("=" * 50)

    success = True

    if not test_imports():
        success = False

    print("=" * 50)
    if success:
        print("✅ All basic import tests passed!")
    else:
        print("❌ Some tests failed!")
        sys.exit(1)
