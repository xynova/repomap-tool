#!/bin/bash

# Script to ensure a nightly image exists before attempting a release
# This can be run manually or as part of the release process

set -e

REGISTRY="ghcr.io"
IMAGE_NAME="xynova/repomap-tool"
NIGHTLY_TAG="$REGISTRY/$IMAGE_NAME:nightly"

echo "Checking if nightly image exists: $NIGHTLY_TAG"

# Try to pull the nightly image
if docker manifest inspect $NIGHTLY_TAG >/dev/null 2>&1; then
    echo "✅ Nightly image exists and is accessible"
else
    echo "❌ Nightly image not found or not accessible"
    echo ""
    echo "To fix this:"
    echo "1. Go to GitHub Actions and manually trigger the 'Nightly Build' workflow"
    echo "2. Wait for the workflow to complete successfully"
    echo "3. Then try the release again"
    echo ""
    echo "Or run this command to trigger the nightly build:"
    echo "gh workflow run nightly.yml"
    exit 1
fi
