#!/bin/bash

# Script to build final image using cached base image with dependencies
# This leverages the cached dependencies for faster builds

set -e

# Configuration
REGISTRY=${REGISTRY:-"ghcr.io"}
IMAGE_NAME=${IMAGE_NAME:-"xynova/repomap-tool"}
PYTHON_VERSION=${PYTHON_VERSION:-"3.11"}

echo "🔧 Building final image using cached dependencies..."

# Get the dependencies hash
if [ -f .deps-image-tag ]; then
    REQUIREMENTS_HASH=$(cat .deps-image-tag)
else
    echo "❌ No dependencies image tag found. Run build-deps-image.sh first."
    exit 1
fi

echo "📦 Using dependencies image: ${REGISTRY}/${IMAGE_NAME}:${REQUIREMENTS_HASH}"

# Pull the base image to ensure we have it locally
echo "📥 Pulling base image..."
docker pull "${REGISTRY}/${IMAGE_NAME}:${REQUIREMENTS_HASH}" || {
    echo "❌ Base image not found. Run build-deps-image.sh first."
    exit 1
}

# Build final image using the base image
echo "🐳 Building final image..."
docker build \
    --target final \
    --build-arg BASE_IMAGE="${REGISTRY}/${IMAGE_NAME}:${REQUIREMENTS_HASH}" \
    --tag "${REGISTRY}/${IMAGE_NAME}:latest" \
    --file docker/Dockerfile \
    .

echo "✅ Final image built successfully!"
echo "   Image: ${REGISTRY}/${IMAGE_NAME}:latest"
echo "   Base: ${REGISTRY}/${IMAGE_NAME}:${REQUIREMENTS_HASH}"
