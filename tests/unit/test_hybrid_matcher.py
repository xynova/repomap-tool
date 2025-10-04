#!/usr/bin/env python3
"""
test_hybrid_matcher.py - Test script for the hybrid matcher

This script demonstrates how the hybrid matcher works and why it's better
than rigid dictionary approaches.
"""

import os
import sys

sys.path.append(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "src",
    )
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


def test_hybrid_matcher():
    """Test the hybrid matcher with various scenarios."""

    print("🧪 Testing Hybrid Matcher vs Rigid Dictionary Approach")
    print("=" * 60)

    # Sample identifiers from a typical codebase
    sample_identifiers = {
        # Authentication related
        "user_authentication",
        "auth_token",
        "login_handler",
        "password_validation",
        "oauth_provider",
        "jwt_decoder",
        "session_manager",
        "credential_store",
        # Data processing
        "data_processor",
        "file_parser",
        "json_serializer",
        "csv_loader",
        "data_transformer",
        "format_converter",
        "batch_processor",
        "stream_handler",
        # Configuration
        "config_manager",
        "settings_loader",
        "env_parser",
        "option_validator",
        "preference_store",
        "parameter_builder",
        "flag_handler",
        "default_setter",
        # API related
        "api_client",
        "endpoint_handler",
        "route_mapper",
        "request_validator",
        "response_formatter",
        "service_dispatcher",
        "method_invoker",
        "proxy_handler",
        # Database
        "db_connection",
        "query_executor",
        "table_mapper",
        "record_finder",
        "data_migrator",
        "schema_validator",
        "index_builder",
        "transaction_manager",
        # Testing
        "test_runner",
        "mock_builder",
        "fixture_loader",
        "assert_validator",
        "coverage_reporter",
        "spec_executor",
        "unit_tester",
        "integration_checker",
        # File operations
        "file_reader",
        "path_resolver",
        "directory_scanner",
        "upload_handler",
        "download_manager",
        "stream_processor",
        "buffer_handler",
        "file_validator",
        # Network
        "http_client",
        "url_parser",
        "connection_pool",
        "request_sender",
        "response_handler",
        "socket_manager",
        "proxy_connector",
        "dns_resolver",
        # Logging
        "log_writer",
        "debug_handler",
        "error_reporter",
        "trace_collector",
        "console_output",
        "file_logger",
        "syslog_sender",
        "metadata_attacher",
        # Caching
        "cache_manager",
        "memoizer",
        "store_handler",
        "retrieval_service",
        "expiration_checker",
        "invalidation_handler",
        "hit_counter",
        "miss_tracker",
        # Custom domain-specific terms
        "widget_factory",
        "gadget_builder",
        "doohickey_processor",
        "thingamajig_handler",
        "whatchamacallit_validator",
        "gizmo_creator",
        "contraption_manager",
    }

    # Clear service cache to avoid conflicts with other tests
    from repomap_tool.cli.services import clear_service_cache

    clear_service_cache()

    # Create config and use service factory
    config = RepoMapConfig(
        project_root=".",
        fuzzy_match=FuzzyMatchConfig(
            threshold=60, strategies=["prefix", "substring", "levenshtein"]
        ),
        semantic_match=SemanticMatchConfig(enabled=True, threshold=0.2),
        performance=PerformanceConfig(),
        dependencies=DependencyConfig(),
    )
    service_factory = get_service_factory()
    repomap_service = service_factory.create_repomap_service(config)
    matcher = repomap_service.hybrid_matcher

    # Build TF-IDF model
    print("📊 Building TF-IDF model from codebase...")
    matcher.build_tfidf_model(sample_identifiers)

    # Test scenarios
    test_cases = [
        # Scenario 1: Exact matches (should work well)
        ("auth", "authentication-related terms"),
        # Scenario 2: Partial matches (fuzzy should help)
        ("login", "login-related terms"),
        # Scenario 3: Conceptual matches (semantic should help)
        ("security", "security-related terms"),
        # Scenario 4: Domain-specific terms (rigid dict would fail)
        ("widget", "widget-related terms"),
        # Scenario 5: Abbreviations (fuzzy should help)
        ("db", "database-related terms"),
        # Scenario 6: Conceptual similarity (semantic should help)
        ("process", "processing-related terms"),
        # Scenario 7: Custom terms (rigid dict would completely miss)
        ("gadget", "gadget-related terms"),
        # Scenario 8: Mixed concepts
        ("data", "data-related terms"),
        # Scenario 9: Action-oriented queries
        ("create", "creation-related terms"),
        # Scenario 10: State-oriented queries
        ("valid", "validation-related terms"),
    ]

    print("\n🔍 Testing Various Query Scenarios:")
    print("-" * 40)

    for query, description in test_cases:
        print(f"\n📝 Query: '{query}' ({description})")

        # Get hybrid matches
        matches = matcher.find_hybrid_matches(query, sample_identifiers, threshold=0.2)

        print(f"   Found {len(matches)} matches:")
        for i, (identifier, score, components) in enumerate(matches[:5]):
            print(f"   {i+1}. {identifier}")
            print(
                f"      Overall: {score:.2f} | Fuzzy: {components['fuzzy']:.2f} | TF-IDF: {components['tfidf']:.2f} | Vector: {components['vector']:.2f} | Context: {components['context']:.2f}"
            )

    # Demonstrate why rigid dictionaries fail
    print("\n❌ Why Rigid Dictionaries Fail:")
    print("-" * 40)

    rigid_dict_examples = [
        ("widget", "Rigid dict has no 'widget' category"),
        ("gadget", "Rigid dict has no 'gadget' category"),
        ("doohickey", "Rigid dict has no 'doohickey' category"),
        ("whatchamacallit", "Rigid dict has no 'whatchamacallit' category"),
    ]

    for query, reason in rigid_dict_examples:
        print(f"\n🔍 Query: '{query}'")
        print(f"   ❌ {reason}")

        # Show that hybrid matcher still finds matches
        matches = matcher.find_hybrid_matches(query, sample_identifiers, threshold=0.2)
        if matches:
            print(f"   ✅ Hybrid matcher found {len(matches)} matches:")
            for identifier, score, _ in matches[:3]:
                print(f"      - {identifier} (score: {score:.2f})")
        else:
            print("   ❌ No matches found")

    # Show TF-IDF benefits
    print("\n📈 TF-IDF Benefits:")
    print("-" * 40)

    # Show word frequencies
    print("Most common words in codebase:")
    for word, freq in sorted(
        matcher.word_frequencies.items(), key=lambda x: x[1], reverse=True
    )[:10]:
        print(f"   '{word}': {freq} occurrences")

    # Show IDF values
    print("\nIDF values (higher = more distinctive):")
    for word, idf in sorted(
        matcher.idf_cache.items(), key=lambda x: x[1], reverse=True
    )[:10]:
        print(f"   '{word}': {idf:.2f}")

    # Demonstrate context similarity
    print("\n🔄 Context Similarity Examples:")
    print("-" * 40)

    context_examples = [
        ("user_auth", "user_authentication"),
        ("data_process", "data_processor"),
        ("file_read", "file_reader"),
        ("cache_store", "cache_manager"),
    ]

    for query, identifier in context_examples:
        context_score = matcher.calculate_context_similarity(query, identifier)
        print(f"   '{query}' vs '{identifier}': {context_score:.2f}")


if __name__ == "__main__":
    test_hybrid_matcher()
