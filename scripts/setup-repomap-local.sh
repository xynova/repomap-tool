#!/bin/bash

# Setup script for repomap-tool:local tagging
# This script demonstrates how to tag any repomap-tool image as 'repomap-tool:local'

set -e

echo "🚀 Setting up repomap-tool:local..."

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  build     Build from source and tag as repomap-tool:local"
    echo "  pull      Pull from registry and tag as repomap-tool:local"
    echo "  registry  Pull from specific registry and tag as repomap-tool:local"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 build                                    # Build from source"
    echo "  $0 pull                                     # Pull from ghcr.io/xynova/repomap-tool:latest"
    echo "  $0 registry ghcr.io/xynova/repomap-tool:v1.0.0  # Pull specific version"
    echo "  $0 registry docker.io/yourorg/repomap-tool:dev   # Pull from custom registry"
}

# Function to build from source
build_from_source() {
    echo "📦 Building from source..."
    if [ ! -f "docker/Dockerfile" ]; then
        echo "❌ Error: docker/Dockerfile not found. Run this script from the project root."
        exit 1
    fi
    
    docker build -t repomap-tool:local -f docker/Dockerfile .
    echo "✅ Built and tagged as repomap-tool:local"
}

# Function to pull from default registry
pull_from_registry() {
    echo "📥 Pulling from default registry..."
    docker pull ghcr.io/xynova/repomap-tool:latest
    docker tag ghcr.io/xynova/repomap-tool:latest repomap-tool:local
    echo "✅ Pulled and tagged as repomap-tool:local"
}

# Function to pull from specific registry
pull_from_specific_registry() {
    local registry_image="$1"
    if [ -z "$registry_image" ]; then
        echo "❌ Error: Registry image not specified"
        echo "Usage: $0 registry <registry-image>"
        exit 1
    fi
    
    echo "📥 Pulling from $registry_image..."
    docker pull "$registry_image"
    docker tag "$registry_image" repomap-tool:local
    echo "✅ Pulled and tagged as repomap-tool:local"
}

# Function to test the setup
test_setup() {
    echo "🧪 Testing setup..."
    docker run --rm repomap-tool:local version
    echo "✅ Setup successful! You can now use 'repomap-tool:local' in your commands."
}

# Main script logic
case "${1:-help}" in
    "build")
        build_from_source
        test_setup
        ;;
    "pull")
        pull_from_registry
        test_setup
        ;;
    "registry")
        pull_from_specific_registry "$2"
        test_setup
        ;;
    "help"|*)
        show_usage
        ;;
esac

echo ""
echo "🎯 Next steps:"
echo "  docker run --rm -e TERM=dumb -v \$(pwd)/.repomap:/app/cache -v /path/to/project:/workspace repomap-tool:local analyze /workspace --fuzzy --semantic"
