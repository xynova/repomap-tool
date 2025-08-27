#!/bin/bash

# Script to clean up old Docker images from GitHub Container Registry
# Usage: ./cleanup_docker_images.sh [days_to_keep] [repository]

set -e

DAYS_TO_KEEP=${1:-7}  # Default to 7 days
REPOSITORY=${2:-"$GITHUB_REPOSITORY"}  # Default to current repository
REGISTRY="ghcr.io"

echo "Cleaning up Docker images older than $DAYS_TO_KEEP days from $REGISTRY/$REPOSITORY"

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is required but not installed."
    echo "Install it from: https://cli.github.com/"
    exit 1
fi

# Check if user is authenticated
if ! gh auth status &> /dev/null; then
    echo "Error: Not authenticated with GitHub CLI."
    echo "Run: gh auth login"
    exit 1
fi

# Get list of packages (Docker images)
echo "Fetching list of packages..."
PACKAGES=$(gh api repos/$REPOSITORY/packages --jq '.[].name' 2>/dev/null || echo "")

if [ -z "$PACKAGES" ]; then
    echo "No packages found for repository $REPOSITORY"
    exit 0
fi

echo "Found packages: $PACKAGES"

# For each package, get versions and delete old ones
for PACKAGE in $PACKAGES; do
    echo "Processing package: $PACKAGE"
    
    # Get package versions older than specified days
    OLD_VERSIONS=$(gh api repos/$REPOSITORY/packages/container/$PACKAGE/versions \
        --jq ".[] | select(.created_at < \"$(date -d \"$DAYS_TO_KEEP days ago\" -Iseconds)\") | .id" 2>/dev/null || echo "")
    
    if [ -n "$OLD_VERSIONS" ]; then
        echo "Found old versions to delete: $OLD_VERSIONS"
        
        for VERSION_ID in $OLD_VERSIONS; do
            echo "Deleting version $VERSION_ID of package $PACKAGE"
            gh api repos/$REPOSITORY/packages/container/$PACKAGE/versions/$VERSION_ID \
                --method DELETE 2>/dev/null || echo "Failed to delete version $VERSION_ID"
        done
    else
        echo "No old versions found for package $PACKAGE"
    fi
done

echo "Cleanup completed!"
