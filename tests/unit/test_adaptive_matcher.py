#!/usr/bin/env python3
"""
test_adaptive_matcher.py - Test script for the adaptive semantic matcher

This script demonstrates how the adaptive semantic matcher learns from
the actual codebase and provides much more flexible matching.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src'))

from matchers.adaptive_semantic_matcher import AdaptiveSemanticMatcher

def test_adaptive_matcher():
    """Test the adaptive semantic matcher with various scenarios."""
    
    print("🧪 Testing Adaptive Semantic Matcher")
    print("=" * 50)
    
    # Sample identifiers from a typical codebase
    sample_identifiers = {
        # Authentication related
        'user_authentication', 'auth_token', 'login_handler', 'password_validation',
        'oauth_provider', 'jwt_decoder', 'session_manager', 'credential_store',
        
        # Data processing
        'data_processor', 'file_parser', 'json_serializer', 'csv_loader',
        'data_transformer', 'format_converter', 'batch_processor', 'stream_handler',
        
        # Configuration
        'config_manager', 'settings_loader', 'env_parser', 'option_validator',
        'preference_store', 'parameter_builder', 'flag_handler', 'default_setter',
        
        # API related
        'api_client', 'endpoint_handler', 'route_mapper', 'request_validator',
        'response_formatter', 'service_dispatcher', 'method_invoker', 'proxy_handler',
        
        # Database
        'db_connection', 'query_executor', 'table_mapper', 'record_finder',
        'data_migrator', 'schema_validator', 'index_builder', 'transaction_manager',
        
        # Testing
        'test_runner', 'mock_builder', 'fixture_loader', 'assert_validator',
        'coverage_reporter', 'spec_executor', 'unit_tester', 'integration_checker',
        
        # File operations
        'file_reader', 'path_resolver', 'directory_scanner', 'upload_handler',
        'download_manager', 'stream_processor', 'buffer_handler', 'file_validator',
        
        # Network
        'http_client', 'url_parser', 'connection_pool', 'request_sender',
        'response_handler', 'socket_manager', 'proxy_connector', 'dns_resolver',
        
        # Logging
        'log_writer', 'debug_handler', 'error_reporter', 'trace_collector',
        'console_output', 'file_logger', 'syslog_sender', 'metadata_attacher',
        
        # Caching
        'cache_manager', 'memoizer', 'store_handler', 'retrieval_service',
        'expiration_checker', 'invalidation_handler', 'hit_counter', 'miss_tracker',
        
        # Custom domain-specific terms (any approach should handle these)
        'widget_factory', 'gadget_builder', 'doohickey_processor', 'thingamajig_handler',
        'whatchamacallit_validator', 'gizmo_creator', 'contraption_manager',
        'flibbertigibbet_analyzer', 'kerfuffle_resolver', 'brouhaha_handler',
        
        # More complex patterns
        'user_profile_manager', 'data_export_service', 'api_rate_limiter',
        'file_upload_validator', 'database_connection_pool', 'cache_invalidation_handler',
        'error_logging_service', 'performance_monitor', 'security_audit_trail'
    }
    
    # Initialize adaptive matcher
    matcher = AdaptiveSemanticMatcher(verbose=False)
    
    # Learn from the codebase
    print("📊 Learning from codebase...")
    matcher.learn_from_identifiers(sample_identifiers)
    
    # Test scenarios that were problematic with rigid approaches
    test_cases = [
        # These should work much better now
        ("process", "processing-related terms"),
        ("valid", "validation-related terms"),
        ("create", "creation-related terms"),
        ("manage", "management-related terms"),
        ("handle", "handler-related terms"),
        
        # Domain-specific terms
        ("widget", "widget-related terms"),
        ("gadget", "gadget-related terms"),
        ("doohickey", "doohickey-related terms"),
        
        # Conceptual queries
        ("user", "user-related terms"),
        ("data", "data-related terms"),
        ("file", "file-related terms"),
        ("api", "API-related terms"),
        ("db", "database-related terms"),
        
        # Action-oriented queries
        ("export", "export-related terms"),
        ("upload", "upload-related terms"),
        ("download", "download-related terms"),
        ("cache", "cache-related terms"),
        ("log", "logging-related terms"),
        
        # Complex queries
        ("rate limit", "rate limiting terms"),
        ("connection pool", "connection pooling terms"),
        ("audit trail", "audit-related terms"),
        ("performance monitor", "performance monitoring terms")
    ]
    
    print("\n🔍 Testing Adaptive Semantic Matching:")
    print("-" * 40)
    
    for query, description in test_cases:
        print(f"\n📝 Query: '{query}' ({description})")
        
        # Find semantic matches
        matches = matcher.find_semantic_matches(query, sample_identifiers, threshold=0.05)
        
        print(f"   Found {len(matches)} matches:")
        for i, (identifier, score) in enumerate(matches[:5]):
            print(f"   {i+1}. {identifier} (score: {score:.3f})")
    
    # Show what the matcher learned
    print("\n📈 What the Adaptive Matcher Learned:")
    print("-" * 40)
    
    print("Most important words (high IDF = distinctive):")
    for word, idf in matcher.get_most_important_words(10):
        print(f"   '{word}': {idf:.2f}")
    
    print("\nMost common words (low IDF = common):")
    for word, freq in matcher.get_common_words(10):
        idf = matcher.get_word_importance(word)
        print(f"   '{word}': {freq} occurrences (IDF: {idf:.2f})")
    
    # Show semantic clusters
    print("\n🔄 Semantic Clusters Discovered:")
    print("-" * 40)
    
    clusters = matcher.get_semantic_clusters(sample_identifiers, similarity_threshold=0.2)
    
    for i, cluster in enumerate(clusters[:5]):  # Show first 5 clusters
        print(f"\nCluster {i+1} ({len(cluster)} items):")
        for identifier in sorted(cluster):
            print(f"   - {identifier}")
    
    # Show related identifiers
    print("\n🔗 Related Identifiers Example:")
    print("-" * 40)
    
    example_identifier = 'user_authentication'
    related = matcher.get_related_identifiers(example_identifier, max_results=8)
    
    print(f"Identifiers related to '{example_identifier}':")
    for identifier, similarity in related:
        print(f"   - {identifier} (similarity: {similarity:.3f})")
    
    # Show query suggestions
    print("\n💡 Query Suggestions:")
    print("-" * 40)
    
    example_identifier = 'data_processor'
    suggestions = matcher.suggest_queries(example_identifier)
    
    print(f"Suggested queries for '{example_identifier}':")
    for suggestion in suggestions[:10]:
        print(f"   - {suggestion}")
    
    # Demonstrate why this is better than rigid approaches
    print("\n✅ Why Adaptive Approach is Better:")
    print("-" * 40)
    
    print("1. Learns from actual codebase patterns")
    print("2. No predefined categories needed")
    print("3. Handles domain-specific terminology automatically")
    print("4. Adapts to different naming conventions")
    print("5. Discovers semantic relationships automatically")
    print("6. Provides meaningful similarity scores")
    print("7. Can suggest related queries and identifiers")
    print("8. Groups similar functionality into clusters")

if __name__ == "__main__":
    test_adaptive_matcher()
