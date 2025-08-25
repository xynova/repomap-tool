#!/usr/bin/env python3
"""
adaptive_vs_rigid_comparison.py - Simple comparison of adaptive vs rigid approaches
"""

from adaptive_semantic_matcher import AdaptiveSemanticMatcher

def compare_approaches():
    """Compare adaptive vs rigid approaches."""
    
    print("🔄 Adaptive vs Rigid Approach Comparison")
    print("=" * 50)
    
    # Sample identifiers
    identifiers = {
        'user_authentication', 'data_processor', 'file_parser', 'widget_factory',
        'gadget_builder', 'doohickey_processor', 'api_client', 'db_connection',
        'cache_manager', 'log_writer', 'upload_handler', 'download_manager',
        'connection_pool', 'performance_monitor', 'security_audit_trail'
    }
    
    # Initialize adaptive matcher
    matcher = AdaptiveSemanticMatcher(verbose=False)
    matcher.learn_from_identifiers(identifiers)
    
    # Test queries that were problematic with rigid approaches
    problematic_queries = [
        "process", "valid", "create", "manage", "handle"
    ]
    
    print("\n🔍 Queries that failed with rigid approaches:")
    print("-" * 40)
    
    for query in problematic_queries:
        matches = matcher.find_semantic_matches(query, identifiers, threshold=0.01)  # Very low threshold
        
        if matches:
            print(f"\n✅ '{query}' found {len(matches)} matches:")
            for identifier, score in matches[:3]:
                print(f"   - {identifier} (score: {score:.3f})")
        else:
            print(f"\n❌ '{query}' found 0 matches")
    
    # Show semantic clusters
    print("\n🔄 Semantic Clusters (Adaptive Discovery):")
    print("-" * 40)
    
    clusters = matcher.get_semantic_clusters(identifiers, similarity_threshold=0.2)
    
    for i, cluster in enumerate(clusters):
        print(f"\nCluster {i+1}:")
        for identifier in sorted(cluster):
            print(f"   - {identifier}")
    
    # Show word importance
    print("\n📊 Word Importance Analysis:")
    print("-" * 40)
    
    print("Most distinctive words (high IDF):")
    for word, idf in matcher.get_most_important_words(8):
        print(f"   '{word}': {idf:.2f}")
    
    print("\nMost common words (low IDF):")
    for word, freq in matcher.get_common_words(8):
        idf = matcher.get_word_importance(word)
        print(f"   '{word}': {freq} occurrences (IDF: {idf:.2f})")
    
    # Demonstrate the key difference
    print("\n🎯 Key Difference:")
    print("-" * 40)
    print("Rigid Approach:")
    print("   ❌ Predefined categories")
    print("   ❌ Misses domain-specific terms")
    print("   ❌ Doesn't adapt to codebase")
    print("   ❌ Fixed rules")
    
    print("\nAdaptive Approach:")
    print("   ✅ Learns from actual codebase")
    print("   ✅ Handles any terminology")
    print("   ✅ Adapts to naming patterns")
    print("   ✅ Discovers relationships automatically")

if __name__ == "__main__":
    compare_approaches()
