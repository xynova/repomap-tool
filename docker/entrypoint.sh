#!/bin/bash

# Entrypoint script for repomap-tool Docker container
# This script handles both tool commands and bash commands

set -e

# If the first argument is "bash", execute the command directly
if [ "$1" = "bash" ]; then
    exec "$@"
else
    # Otherwise, run the repomap-tool CLI
    # This allows users to run: docker run ... repomap-tool:latest search /workspace "query"
    # And it gets converted to: python3 -m repomap_tool.cli search /workspace "query"
    exec python3 -m repomap_tool.cli "$@"
fi
