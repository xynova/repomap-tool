#!/bin/bash
set -e

# Build script for repomap-tool Docker images
# Usage: ./scripts/build-docker.sh [gpu|cpu|both]

BUILD_TYPE=${1:-both}

echo "🐳 Building repomap-tool Docker images..."

if [ "$BUILD_TYPE" = "gpu" ] || [ "$BUILD_TYPE" = "both" ]; then
    echo "📦 Building GPU-enabled image (default)..."
    docker build -f docker/Dockerfile -t repomap-tool:latest .
    docker build -f docker/Dockerfile -t repomap-tool:gpu .
    echo "✅ GPU image built: repomap-tool:latest, repomap-tool:gpu"
fi

if [ "$BUILD_TYPE" = "cpu" ] || [ "$BUILD_TYPE" = "both" ]; then
    echo "📦 Building CPU-only image..."
    docker build -f docker/Dockerfile.cpu -t repomap-tool:cpu .
    echo "✅ CPU image built: repomap-tool:cpu"
fi

echo ""
echo "🎉 Build complete!"
echo ""
echo "Available images:"
echo "  repomap-tool:latest  (GPU-enabled, default)"
echo "  repomap-tool:gpu     (GPU-enabled, explicit)"
echo "  repomap-tool:cpu     (CPU-only, for constrained environments)"
echo ""
echo "Usage:"
echo "  # GPU environments (default)"
echo "  docker run --rm -t --gpus all -v \$(pwd):/workspace repomap-tool:latest explore find \"query\""
echo ""
echo "  # CPU-only environments"
echo "  docker run --rm -t -v \$(pwd):/workspace repomap-tool:cpu explore find \"query\""
