#!/bin/bash

# Script to build and push base image with dependencies only
# This enables optimal Docker layer caching

set -e

# Configuration
REGISTRY=${REGISTRY:-"ghcr.io"}
IMAGE_NAME=${IMAGE_NAME:-"xynova/repomap-tool"}
PYTHON_VERSION=${PYTHON_VERSION:-"3.11"}

echo "🔧 Building base image with dependencies only..."

# Generate requirements hash
echo "📋 Generating requirements hash..."
REQUIREMENTS_HASH=$(python3 -c "
import hashlib
import toml

# Read pyproject.toml
data = toml.load('pyproject.toml')

# Get dependencies
deps = data['project']['dependencies']
deps_str = '\n'.join(sorted(deps))

# Create hash
hash_obj = hashlib.sha256(deps_str.encode())
print('deps-' + hash_obj.hexdigest()[:12])
")

echo "📦 Dependencies hash: $REQUIREMENTS_HASH"

# Check if the base image already exists
echo "🔍 Checking if base image already exists..."
if docker pull "${REGISTRY}/${IMAGE_NAME}:${REQUIREMENTS_HASH}" 2>/dev/null; then
    echo "✅ Base image already exists: ${REGISTRY}/${IMAGE_NAME}:${REQUIREMENTS_HASH}"
    echo "   Skipping build - using existing image"
else
    echo "📦 Base image not found - building new one..."
    
    # Build base image with dependencies only
    echo "🐳 Building base image..."
    docker build \
        --target base \
        --tag "${REGISTRY}/${IMAGE_NAME}:${REQUIREMENTS_HASH}" \
        --tag "${REGISTRY}/${IMAGE_NAME}:deps-latest" \
        --file docker/Dockerfile \
        .

    # Push base image to registry
    echo "📤 Pushing base image to registry..."
    docker push "${REGISTRY}/${IMAGE_NAME}:${REQUIREMENTS_HASH}"
    docker push "${REGISTRY}/${IMAGE_NAME}:deps-latest"

    echo "✅ Base image built and pushed successfully!"
fi

echo "   Image: ${REGISTRY}/${IMAGE_NAME}:${REQUIREMENTS_HASH}"
echo "   Latest: ${REGISTRY}/${IMAGE_NAME}:deps-latest"

# Output the hash for GitHub Actions (if running in CI)
if [ -n "$GITHUB_OUTPUT" ]; then
    echo "deps_hash=$REQUIREMENTS_HASH" >> $GITHUB_OUTPUT
fi

# Also write to file for local development
echo "$REQUIREMENTS_HASH" > .deps-image-tag
