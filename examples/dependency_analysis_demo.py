#!/usr/bin/env python3
"""
Dependency Analysis Demo

This script demonstrates the end-to-end dependency analysis functionality
that was implemented in Phase 2 of the repomap-tool project.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the path so we can import repomap_tool
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from repomap_tool.models import RepoMapConfig, DependencyConfig
from repomap_tool.core.repo_map import DockerRepoMap


def main():
    """Demonstrate dependency analysis functionality."""
    print("🚀 Phase 2: Dependency Analysis Implementation Demo")
    print("=" * 60)
    
    # Get the current directory as the project root
    project_root = Path.cwd()
    print(f"📁 Project Root: {project_root}")
    
    # Create dependency configuration
    dependency_config = DependencyConfig(
        enabled=True,
        max_graph_size=1000,
        enable_call_graph=True,
        enable_impact_analysis=True,
        centrality_algorithms=["degree", "betweenness", "pagerank"],
        performance_threshold_seconds=30.0
    )
    
    # Create main configuration
    config = RepoMapConfig(
        project_root=str(project_root),
        dependencies=dependency_config,
        verbose=True,
        log_level="INFO"
    )
    
    print(f"⚙️  Configuration: {dependency_config}")
    print()
    
    try:
        # Initialize DockerRepoMap with dependency analysis
        print("🔧 Initializing DockerRepoMap with dependency analysis...")
        repomap = DockerRepoMap(config)
        print("✅ DockerRepoMap initialized successfully!")
        print()
        
        # Build dependency graph
        print("📊 Building dependency graph...")
        dependency_graph = repomap.build_dependency_graph()
        print("✅ Dependency graph built successfully!")
        print()
        
        # Get graph statistics
        stats = dependency_graph.get_graph_statistics()
        print("📈 Graph Statistics:")
        print(f"   • Total Files: {stats['total_nodes']}")
        print(f"   • Total Dependencies: {stats['total_edges']}")
        print(f"   • Circular Dependencies: {stats['cycles']}")
        print(f"   • Leaf Nodes: {stats['leaf_nodes']}")
        print(f"   • Root Nodes: {stats['root_nodes']}")
        print(f"   • Construction Time: {dependency_graph.construction_time:.2f}s")
        print()
        
        # Get centrality scores
        print("🎯 Calculating centrality scores...")
        centrality_scores = repomap.get_centrality_scores()
        
        # Show top centrality files
        sorted_scores = sorted(centrality_scores.items(), key=lambda x: x[1], reverse=True)
        top_files = sorted_scores[:5]
        
        print("🏆 Top Centrality Files:")
        for i, (file_path, score) in enumerate(top_files, 1):
            print(f"   {i}. {file_path}: {score:.4f}")
        print()
        
        # Find circular dependencies
        print("🔄 Checking for circular dependencies...")
        cycles = repomap.find_circular_dependencies()
        
        if cycles:
            print(f"⚠️  Found {len(cycles)} circular dependencies:")
            for i, cycle in enumerate(cycles, 1):
                print(f"   Cycle {i}: {' → '.join(cycle)}")
        else:
            print("✅ No circular dependencies found!")
        print()
        
        # Analyze impact for a specific file
        print("💥 Analyzing change impact...")
        test_file = "src/repomap_tool/core/repo_map.py"
        
        if os.path.exists(test_file):
            impact_report = repomap.analyze_change_impact(test_file)
            print(f"📋 Impact Analysis for {test_file}:")
            print(f"   • Risk Score: {impact_report.risk_score:.2f}")
            print(f"   • Affected Files: {len(impact_report.affected_files)}")
            print(f"   • Breaking Change Potential: {impact_report.breaking_change_potential}")
            print(f"   • Suggested Tests: {len(impact_report.suggested_tests)}")
        else:
            print(f"⚠️  Test file {test_file} not found, skipping impact analysis")
        print()
        
        # Show language distribution
        if 'language_distribution' in stats:
            print("🌐 Language Distribution:")
            for lang, count in stats['language_distribution'].items():
                print(f"   • {lang}: {count} files")
            print()
        
        print("🎉 Demo completed successfully!")
        print("\n💡 This demonstrates the complete Phase 2 implementation:")
        print("   • Multi-language import analysis")
        print("   • Dependency graph construction")
        print("   • Centrality calculations")
        print("   • Circular dependency detection")
        print("   • Change impact analysis")
        print("   • CLI integration")
        print("   • Configuration management")
        
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
