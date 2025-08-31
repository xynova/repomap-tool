#!/bin/bash

# Script to build final image using cached base image with dependencies
# This leverages the cached dependencies for faster builds

set -e

# Configuration
REGISTRY=${REGISTRY:-"ghcr.io"}
IMAGE_NAME=${IMAGE_NAME:-"xynova/repomap-tool"}
PYTHON_VERSION=${PYTHON_VERSION:-"3.11"}

echo "🔧 Building final image using cached dependencies..."

# Get the dependencies hash (from env var in CI, or file in local dev)
if [ -n "$DEPS_HASH" ]; then
    REQUIREMENTS_HASH="$DEPS_HASH"
    echo "📦 Using dependencies hash from environment: $REQUIREMENTS_HASH"
elif [ -f .deps-image-tag ]; then
    REQUIREMENTS_HASH=$(cat .deps-image-tag)
    echo "📦 Using dependencies hash from file: $REQUIREMENTS_HASH"
else
    echo "❌ No dependencies hash found. Set DEPS_HASH environment variable or run build-deps-image.sh first."
    exit 1
fi

echo "📦 Using dependencies image: ${REGISTRY}/${IMAGE_NAME}:${REQUIREMENTS_HASH}"

# Pull the base image to ensure we have it locally
echo "📥 Pulling base image..."
docker pull "${REGISTRY}/${IMAGE_NAME}:${REQUIREMENTS_HASH}" || {
    echo "❌ Base image not found. Run build-deps-image.sh first."
    exit 1
}

# Determine the first tag to build to (for tagging other images)
FIRST_TAG=""
if [ -n "$FULL_TAG" ]; then
    FIRST_TAG="$FULL_TAG"
elif [ -n "$NIGHTLY_TAG" ]; then
    FIRST_TAG="$NIGHTLY_TAG"
elif [ -n "$NIGHTLY_LATEST_TAG" ]; then
    FIRST_TAG="$NIGHTLY_LATEST_TAG"
else
    # If no tags provided, build to a temporary tag
    FIRST_TAG="${REGISTRY}/${IMAGE_NAME}:temp-$(date +%s)"
fi

# Build final image using the base image
echo "🐳 Building final image to: $FIRST_TAG"
docker build \
    --target final \
    --build-arg BASE_IMAGE="${REGISTRY}/${IMAGE_NAME}:${REQUIREMENTS_HASH}" \
    --tag "$FIRST_TAG" \
    --file docker/Dockerfile \
    .

# Push the first tag
echo "📤 Pushing: $FIRST_TAG"
docker push "$FIRST_TAG"

# Handle additional tags if provided
if [ -n "$FULL_TAG" ] && [ "$FULL_TAG" != "$FIRST_TAG" ]; then
    echo "📤 Tagging and pushing: $FULL_TAG"
    docker tag "$FIRST_TAG" "$FULL_TAG"
    docker push "$FULL_TAG"
fi

if [ -n "$NIGHTLY_TAG" ] && [ "$NIGHTLY_TAG" != "$FIRST_TAG" ]; then
    echo "📤 Tagging and pushing: $NIGHTLY_TAG"
    docker tag "$FIRST_TAG" "$NIGHTLY_TAG"
    docker push "$NIGHTLY_TAG"
fi

if [ -n "$NIGHTLY_LATEST_TAG" ] && [ "$NIGHTLY_LATEST_TAG" != "$FIRST_TAG" ]; then
    echo "📤 Tagging and pushing: $NIGHTLY_LATEST_TAG"
    docker tag "$FIRST_TAG" "$NIGHTLY_LATEST_TAG"
    docker push "$NIGHTLY_LATEST_TAG"
fi

echo "✅ Final image built and pushed successfully!"
echo "   Base: ${REGISTRY}/${IMAGE_NAME}:${REQUIREMENTS_HASH}"
