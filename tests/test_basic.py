#!/usr/bin/env python3
"""
Basic test to verify core functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

def test_imports():
    """Test that all core modules can be imported."""
    try:
        from repomap_tool.matchers.fuzzy_matcher import FuzzyMatcher
        print("✅ FuzzyMatcher imported successfully")
    except ImportError as e:
        print(f"❌ FuzzyMatcher import failed: {e}")
        return False
    
    try:
        from repomap_tool.matchers.adaptive_semantic_matcher import AdaptiveSemanticMatcher
        print("✅ AdaptiveSemanticMatcher imported successfully")
    except ImportError as e:
        print(f"❌ AdaptiveSemanticMatcher import failed: {e}")
        return False
    
    try:
        from repomap_tool.matchers.hybrid_matcher import HybridMatcher
        print("✅ HybridMatcher imported successfully")
    except ImportError as e:
        print(f"❌ HybridMatcher import failed: {e}")
        return False
    
    return True

def test_fuzzy_matcher():
    """Test basic fuzzy matching functionality."""
    try:
        from repomap_tool.matchers.fuzzy_matcher import FuzzyMatcher
        
        matcher = FuzzyMatcher(threshold=70, verbose=False)
        
        # Test data
        identifiers = {
            'user_authentication', 'auth_token', 'login_handler', 'password_validation',
            'data_processor', 'file_parser', 'json_serializer', 'csv_loader'
        }
        
        # Test matching
        results = matcher.match_identifiers('auth', identifiers)
        
        if results:
            print("✅ FuzzyMatcher basic functionality works")
            return True
        else:
            print("❌ FuzzyMatcher returned no results")
            return False
            
    except Exception as e:
        print(f"❌ FuzzyMatcher test failed: {e}")
        return False

def test_adaptive_matcher():
    """Test basic adaptive semantic matching functionality."""
    try:
        from repomap_tool.matchers.adaptive_semantic_matcher import AdaptiveSemanticMatcher
        
        matcher = AdaptiveSemanticMatcher(verbose=False)
        
        # Test data
        identifiers = {
            'user_authentication', 'auth_token', 'login_handler', 'password_validation',
            'data_processor', 'file_parser', 'json_serializer', 'csv_loader'
        }
        
        # Learn from identifiers
        matcher.learn_from_identifiers(identifiers)
        
        # Test matching
        results = matcher.find_semantic_matches('auth', identifiers, threshold=0.1)
        
        if results:
            print("✅ AdaptiveSemanticMatcher basic functionality works")
            return True
        else:
            print("❌ AdaptiveSemanticMatcher returned no results")
            return False
            
    except Exception as e:
        print(f"❌ AdaptiveSemanticMatcher test failed: {e}")
        return False

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
