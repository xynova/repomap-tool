#!/bin/bash

# Default values
PROJECT_PATH=${1:-/path/to/your/project}
MAP_TOKENS=${2:-1024}
VERBOSE=${3:-false}

echo "Running RepoMap Tool..."
echo "======================"
echo "Project: $PROJECT_PATH"
echo "Map tokens: $MAP_TOKENS"
echo "Verbose: $VERBOSE"
echo ""

# Check if project path exists
if [ ! -d "$PROJECT_PATH" ]; then
    echo "Error: Project directory does not exist: $PROJECT_PATH"
    echo "Usage: ./run.sh <project_path> [map_tokens] [verbose]"
    exit 1
fi

# Build verbose flag
VERBOSE_FLAG=""
if [ "$VERBOSE" = "true" ]; then
    VERBOSE_FLAG="--verbose"
fi

# Run the Docker container
docker run -it --rm \
  -v "$PROJECT_PATH:/project" \
  -v "$(pwd)/cache:/app/cache" \
  repomap-tool \
  /project \
  --map-tokens "$MAP_TOKENS" \
  $VERBOSE_FLAG \
  --output /project/repo_map.txt
