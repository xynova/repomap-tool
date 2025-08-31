#!/usr/bin/env python3
"""
simple_hybrid_demo.py - Simple demonstration of hybrid matching approach

This script shows why hybrid matching is better than rigid dictionaries
without requiring external dependencies.
"""

import re
import math
from collections import Counter
from typing import Dict, List, Set, Tuple


def split_identifier(identifier: str) -> List[str]:
    """Split an identifier into words."""
    if not identifier:
        return []

    # Split by underscores and hyphens first
    parts = re.split(r"[_-]", identifier)

    # Then split camelCase and PascalCase
    words = []
    for part in parts:
        if part:
            camel_parts = re.findall(
                r"[A-Z]?[a-z]+|[A-Z]{2,}(?=[A-Z][a-z]|\b|\d)|\d+", part
            )
            words.extend(camel_parts)

    return [word.lower() for word in words if word]


def calculate_simple_similarity(query: str, identifier: str) -> float:
    """Calculate simple similarity between query and identifier."""
    query_words = set(split_identifier(query))
    identifier_words = set(split_identifier(identifier))

    if not query_words or not identifier_words:
        return 0.0

    # Jaccard similarity
    intersection = len(query_words.intersection(identifier_words))
    union = len(query_words.union(identifier_words))

    if union == 0:
        return 0.0

    return intersection / union


def calculate_tfidf_similarity(
    query: str,
    identifier: str,
    word_frequencies: Dict[str, int],
    total_identifiers: int,
) -> float:
    """Calculate TF-IDF similarity."""
    query_words = set(split_identifier(query))
    identifier_words = set(split_identifier(identifier))

    if not query_words or not identifier_words:
        return 0.0

    # Calculate IDF for each word
    query_vector = {}
    identifier_vector = {}

    for word in query_words:
        if word in word_frequencies:
            idf = math.log(total_identifiers / word_frequencies[word])
            query_vector[word] = idf

    for word in identifier_words:
        if word in word_frequencies:
            idf = math.log(total_identifiers / word_frequencies[word])
            identifier_vector[word] = idf

    # Calculate cosine similarity
    common_words = set(query_vector.keys()) & set(identifier_vector.keys())

    if not common_words:
        return 0.0

    numerator = sum(
        query_vector[word] * identifier_vector[word] for word in common_words
    )
    query_magnitude = math.sqrt(sum(score**2 for score in query_vector.values()))
    identifier_magnitude = math.sqrt(
        sum(score**2 for score in identifier_vector.values())
    )

    if query_magnitude == 0 or identifier_magnitude == 0:
        return 0.0

    return numerator / (query_magnitude * identifier_magnitude)


def hybrid_similarity(
    query: str,
    identifier: str,
    word_frequencies: Dict[str, int],
    total_identifiers: int,
) -> float:
    """Calculate hybrid similarity combining multiple approaches."""
    # Simple similarity (like fuzzy matching)
    simple_score = calculate_simple_similarity(query, identifier)

    # TF-IDF similarity
    tfidf_score = calculate_tfidf_similarity(
        query, identifier, word_frequencies, total_identifiers
    )

    # Weighted combination
    overall_score = simple_score * 0.6 + tfidf_score * 0.4

    return overall_score


def demonstrate_hybrid_vs_rigid():
    """Demonstrate why hybrid approach is better than rigid dictionaries."""

    print("🧪 Hybrid Matching vs Rigid Dictionary Approach")
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
        # Custom domain-specific terms (rigid dict would miss these)
        "widget_factory",
        "gadget_builder",
        "doohickey_processor",
        "thingamajig_handler",
        "whatchamacallit_validator",
        "gizmo_creator",
        "contraption_manager",
        "flibbertigibbet_analyzer",
        "kerfuffle_resolver",
        "brouhaha_handler",
    }

    # Build word frequency model
    print("📊 Building word frequency model...")
    word_frequencies = Counter()
    for identifier in sample_identifiers:
        words = split_identifier(identifier)
        for word in set(words):
            word_frequencies[word] += 1

    total_identifiers = len(sample_identifiers)

    print(
        f"   Found {len(word_frequencies)} unique words across {total_identifiers} identifiers"
    )

    # Test scenarios
    test_cases = [
        # Standard cases (both approaches should work)
        ("auth", "authentication-related terms"),
        ("login", "login-related terms"),
        ("data", "data-related terms"),
        # Domain-specific cases (rigid dict would fail)
        ("widget", "widget-related terms"),
        ("gadget", "gadget-related terms"),
        ("doohickey", "doohickey-related terms"),
        ("flibbertigibbet", "flibbertigibbet-related terms"),
        # Partial matches
        ("process", "processing-related terms"),
        ("valid", "validation-related terms"),
        ("create", "creation-related terms"),
        # Abbreviations
        ("db", "database-related terms"),
        ("api", "API-related terms"),
        ("http", "HTTP-related terms"),
    ]

    print("\n🔍 Testing Query Scenarios:")
    print("-" * 40)

    for query, description in test_cases:
        print(f"\n📝 Query: '{query}' ({description})")

        # Find matches using hybrid approach
        matches = []
        for identifier in sample_identifiers:
            score = hybrid_similarity(
                query, identifier, word_frequencies, total_identifiers
            )
            if score > 0.1:  # Low threshold to show all matches
                matches.append((identifier, score))

        # Sort by score
        matches.sort(key=lambda x: x[1], reverse=True)

        print(f"   Found {len(matches)} matches:")
        for i, (identifier, score) in enumerate(matches[:5]):
            print(f"   {i+1}. {identifier} (score: {score:.3f})")

    # Show why rigid dictionaries fail
    print("\n❌ Why Rigid Dictionaries Fail:")
    print("-" * 40)

    # Simulate rigid dictionary approach
    rigid_categories = {
        "authentication": ["auth", "login", "password", "token", "session", "user"],
        "data_processing": ["data", "process", "transform", "convert", "parse"],
        "configuration": ["config", "setting", "option", "parameter", "env"],
        "api_development": ["api", "endpoint", "route", "handler", "service"],
        "database": ["db", "database", "query", "table", "record"],
        "testing": ["test", "mock", "fixture", "assert", "coverage"],
        "file_operations": ["file", "read", "write", "path", "directory"],
        "network": ["http", "url", "connection", "client", "server"],
        "logging": ["log", "debug", "error", "trace", "console"],
        "caching": ["cache", "store", "retrieve", "expire", "invalidate"],
    }

    # Create reverse mapping
    rigid_mappings = {}
    for category, terms in rigid_categories.items():
        for term in terms:
            rigid_mappings[term] = category

    rigid_failures = [
        ("widget", "No 'widget' category in rigid dict"),
        ("gadget", "No 'gadget' category in rigid dict"),
        ("doohickey", "No 'doohickey' category in rigid dict"),
        ("flibbertigibbet", "No 'flibbertigibbet' category in rigid dict"),
        ("kerfuffle", "No 'kerfuffle' category in rigid dict"),
        ("brouhaha", "No 'brouhaha' category in rigid dict"),
    ]

    for query, reason in rigid_failures:
        print(f"\n🔍 Query: '{query}'")
        print(f"   ❌ {reason}")

        # Show that hybrid approach still finds matches
        matches = []
        for identifier in sample_identifiers:
            score = hybrid_similarity(
                query, identifier, word_frequencies, total_identifiers
            )
            if score > 0.1:
                matches.append((identifier, score))

        matches.sort(key=lambda x: x[1], reverse=True)

        if matches:
            print(f"   ✅ Hybrid approach found {len(matches)} matches:")
            for identifier, score in matches[:3]:
                print(f"      - {identifier} (score: {score:.3f})")
        else:
            print(f"   ❌ No matches found")

    # Show TF-IDF benefits
    print("\n📈 TF-IDF Benefits:")
    print("-" * 40)

    print("Most common words (low IDF = less distinctive):")
    for word, freq in sorted(
        word_frequencies.items(), key=lambda x: x[1], reverse=True
    )[:10]:
        idf = math.log(total_identifiers / freq)
        print(f"   '{word}': {freq} occurrences (IDF: {idf:.2f})")

    print("\nMost distinctive words (high IDF):")
    for word, freq in sorted(
        word_frequencies.items(),
        key=lambda x: math.log(total_identifiers / x[1]),
        reverse=True,
    )[:10]:
        idf = math.log(total_identifiers / freq)
        print(f"   '{word}': {freq} occurrences (IDF: {idf:.2f})")

    # Demonstrate adaptive learning
    print("\n🔄 Adaptive Learning Benefits:")
    print("-" * 40)

    print("Hybrid approach learns from the actual codebase:")
    print("   - Common words (like 'data', 'user') get lower weight")
    print("   - Distinctive words (like 'widget', 'gadget') get higher weight")
    print("   - No predefined categories needed")
    print("   - Adapts to any domain or terminology")

    print("\nRigid dictionary limitations:")
    print("   - Fixed categories that may not match the codebase")
    print("   - Misses domain-specific terminology")
    print("   - Requires manual maintenance and updates")
    print("   - Doesn't adapt to different codebases")


if __name__ == "__main__":
    demonstrate_hybrid_vs_rigid()
