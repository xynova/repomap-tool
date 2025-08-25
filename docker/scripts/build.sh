#!/bin/bash

echo "Building Docker RepoMap Tool..."
echo "================================"

# Change to parent directory to access aider codebase
cd ..

# Build the Docker image from parent directory
docker build -f docker-repomap/Dockerfile -t repomap-tool .

# Change back to docker-repomap directory
cd docker-repomap

echo ""
echo "Build complete!"
echo ""
echo "Usage examples:"
echo "  docker run -v /path/to/project:/project repomap-tool /project"
echo "  docker run -v /path/to/project:/project repomap-tool /project --map-tokens 2048 --verbose"
echo "  docker run -v /path/to/project:/project repomap-tool /project --cache-stats"
echo "  docker run -v /path/to/project:/project repomap-tool /project --clear-cache --force-refresh"
echo ""
echo "For help:"
echo "  docker run repomap-tool --help"
