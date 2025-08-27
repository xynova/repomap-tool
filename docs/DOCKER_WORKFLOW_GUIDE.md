# Docker Workflow Guide

## Overview

The Docker workflow has been updated to use GitHub Container Registry (ghcr.io) for building, testing, and storing Docker images. This approach provides better integration with GitHub Actions and allows for proper image sharing between jobs.

## Key Changes

### 1. Image Tagging Strategy
- Images are now tagged with date and commit SHA: `YYYYMMDD-HHMMSS-COMMIT_SHA`
- Example: `ghcr.io/username/repomap-tool:20241201-143022-a1b2c3d4`
- This allows for easy identification and expiration of old images

### 2. GitHub Container Registry Integration
- Uses `ghcr.io` instead of Docker Hub
- No need for external Docker Hub credentials
- Integrated with GitHub's built-in container registry
- Free for public repositories

### 3. Multi-Job Workflow
- **docker-build**: Builds and pushes the image, runs basic tests
- **docker-integration-test**: Pulls the image and runs integration tests
- **cleanup-old-images**: Removes images older than 7 days (only on main/develop)

## Workflow Structure

```yaml
jobs:
  docker-build:
    # Builds and pushes image with date/commit tag
    # Tests basic functionality
    
  docker-integration-test:
    # Pulls image from registry
    # Runs comprehensive integration tests
    
  cleanup-old-images:
    # Removes old images (7+ days old)
    # Only runs on main/develop branches
```

## Authentication

The workflow uses GitHub's built-in `GITHUB_TOKEN` secret, which is automatically available in GitHub Actions. No additional setup is required.

## Image Lifecycle

1. **Build**: Image is built with date/commit tag
2. **Push**: Image is pushed to GitHub Container Registry
3. **Test**: Image is pulled and tested in integration job
4. **Cleanup**: Old images are automatically removed after 7 days

## Manual Cleanup

You can manually clean up old images using the provided script:

```bash
# Clean up images older than 7 days
./scripts/dev/cleanup_docker_images.sh 7

# Clean up images older than 30 days
./scripts/dev/cleanup_docker_images.sh 30

# Clean up images for a specific repository
./scripts/dev/cleanup_docker_images.sh 7 username/repository
```

## Prerequisites

- GitHub CLI (`gh`) must be installed for cleanup operations
- Repository must have appropriate permissions for package management

## Troubleshooting

### Image Not Found
If you see "Unable to find image" errors:
1. Check that the image was successfully pushed in the build job
2. Verify the image tag is correctly passed between jobs
3. Ensure the integration test job is waiting for the build job

### Permission Denied
If you see permission errors:
1. Check that the workflow has `packages: write` permission for build job
2. Check that the workflow has `packages: read` permission for test job
3. Verify the `GITHUB_TOKEN` is available

### Cleanup Failures
If cleanup fails:
1. Ensure GitHub CLI is properly installed
2. Check that the token has sufficient permissions
3. Verify the repository name is correct

## Benefits

1. **No External Dependencies**: Uses GitHub's built-in container registry
2. **Automatic Cleanup**: Old images are automatically removed
3. **Better Integration**: Seamless integration with GitHub Actions
4. **Cost Effective**: Free for public repositories
5. **Traceable**: Images are tagged with commit information for debugging

## Migration from Docker Hub

If you were previously using Docker Hub:
1. Remove Docker Hub login steps
2. Update image references to use `ghcr.io` format
3. Update any external systems that pull these images
4. Consider setting up image mirroring if needed for external systems
