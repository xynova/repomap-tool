#!/usr/bin/env python3
"""
pydantic_example.py - Example demonstrating Pydantic integration

This example shows how to use the new Pydantic models for configuration
management, validation, and structured data handling.
"""

import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from models import (
    RepoMapConfig, FuzzyMatchConfig, SemanticMatchConfig,
    SearchRequest, MatchResult, create_error_response
)


def example_configuration_validation():
    """Example: Configuration validation with Pydantic."""
    print("🔧 Configuration Validation Example")
    print("=" * 50)
    
    # Valid configuration
    try:
        config = RepoMapConfig(
            project_root=".",
            fuzzy_match=FuzzyMatchConfig(
                enabled=True,
                threshold=75,
                strategies=['prefix', 'levenshtein']
            ),
            semantic_match=SemanticMatchConfig(
                enabled=True,
                threshold=0.3
            ),
            verbose=True
        )
        print("✅ Valid configuration created successfully")
        print(f"   Project root: {config.project_root}")
        print(f"   Fuzzy enabled: {config.fuzzy_match.enabled}")
        print(f"   Semantic threshold: {config.semantic_match.threshold}")
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
    
    # Invalid configuration (will raise validation error)
    print("\n🔍 Testing invalid configuration...")
    try:
        invalid_config = RepoMapConfig(
            project_root="/nonexistent/path",  # Invalid path
            fuzzy_match=FuzzyMatchConfig(
                enabled=True,
                threshold=150,  # Invalid threshold (>100)
                strategies=['invalid_strategy']  # Invalid strategy
            )
        )
    except Exception as e:
        print(f"✅ Validation correctly caught error: {e}")


def example_search_request():
    """Example: Search request validation."""
    print("\n🔍 Search Request Example")
    print("=" * 50)
    
    # Valid search request
    try:
        request = SearchRequest(
            query="user_authentication",
            match_type="hybrid",
            threshold=0.8,
            max_results=20,
            include_context=True
        )
        print("✅ Valid search request created")
        print(f"   Query: {request.query}")
        print(f"   Match type: {request.match_type}")
        print(f"   Threshold: {request.threshold}")
        
    except Exception as e:
        print(f"❌ Search request validation failed: {e}")
    
    # Invalid search request
    print("\n🔍 Testing invalid search request...")
    try:
        invalid_request = SearchRequest(
            query="",  # Empty query
            threshold=1.5,  # Invalid threshold (>1.0)
            max_results=0  # Invalid max_results
        )
    except Exception as e:
        print(f"✅ Validation correctly caught error: {e}")


def example_match_results():
    """Example: Match result creation and validation."""
    print("\n🎯 Match Results Example")
    print("=" * 50)
    
    # Create match results
    results = [
        MatchResult(
            identifier="user_authentication",
            score=0.95,
            strategy="fuzzy",
            match_type="fuzzy",
            file_path="auth/user.py",
            line_number=42,
            metadata={"confidence": "high"}
        ),
        MatchResult(
            identifier="authenticate_user",
            score=0.87,
            strategy="semantic",
            match_type="semantic",
            file_path="auth/authentication.py",
            line_number=15,
            metadata={"tfidf_score": 0.87}
        )
    ]
    
    print("✅ Match results created successfully")
    for i, result in enumerate(results, 1):
        print(f"   Result {i}: {result.identifier} (score: {result.score:.2f})")
    
    # Test score normalization
    print("\n🔍 Testing score normalization...")
    try:
        normalized_result = MatchResult(
            identifier="test",
            score=1.5,  # Will be normalized to 1.0
            strategy="test",
            match_type="fuzzy"
        )
        print(f"✅ Score normalized: {normalized_result.score}")
    except Exception as e:
        print(f"❌ Score normalization failed: {e}")


def example_config_serialization():
    """Example: Configuration serialization and deserialization."""
    print("\n💾 Configuration Serialization Example")
    print("=" * 50)
    
    # Create configuration
    config = RepoMapConfig(
        project_root=".",
        fuzzy_match=FuzzyMatchConfig(enabled=True, threshold=80),
        semantic_match=SemanticMatchConfig(enabled=True, threshold=0.4),
        output_format="json",
        verbose=True
    )
    
    # Serialize to dictionary
    config_dict = config.model_dump()
    print("✅ Configuration serialized to dictionary")
    
    # Serialize to JSON
    config_json = config.model_dump_json(indent=2)
    print("✅ Configuration serialized to JSON")
    print(f"   JSON length: {len(config_json)} characters")
    
    # Deserialize from dictionary
    try:
        new_config = RepoMapConfig(**config_dict)
        print("✅ Configuration deserialized from dictionary")
        print(f"   Project root: {new_config.project_root}")
        print(f"   Fuzzy threshold: {new_config.fuzzy_match.threshold}")
        
    except Exception as e:
        print(f"❌ Deserialization failed: {e}")


def example_error_handling():
    """Example: Error response creation."""
    print("\n🚨 Error Handling Example")
    print("=" * 50)
    
    # Create error responses
    errors = [
        create_error_response(
            "Project root does not exist",
            "ValidationError",
            {"path": "/nonexistent/path"},
            "req_123"
        ),
        create_error_response(
            "Invalid threshold value",
            "ConfigurationError",
            {"threshold": 150, "valid_range": "0-100"}
        )
    ]
    
    print("✅ Error responses created")
    for i, error in enumerate(errors, 1):
        print(f"   Error {i}: {error.error_type} - {error.error}")
        if error.details:
            print(f"      Details: {error.details}")


def main():
    """Run all examples."""
    print("🚀 Docker RepoMap Pydantic Integration Examples")
    print("=" * 60)
    
    example_configuration_validation()
    example_search_request()
    example_match_results()
    example_config_serialization()
    example_error_handling()
    
    print("\n" + "=" * 60)
    print("✅ All examples completed successfully!")
    print("\nKey benefits of Pydantic integration:")
    print("  • Automatic validation of configuration and data")
    print("  • Type safety with runtime checking")
    print("  • Structured error messages")
    print("  • Easy serialization/deserialization")
    print("  • IDE support with autocomplete")
    print("  • Self-documenting code with field descriptions")


if __name__ == "__main__":
    main()
