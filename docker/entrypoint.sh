#!/bin/bash

# Entrypoint script for repomap-tool Docker container
# This script handles both tool commands and bash commands

set -e

# If the first argument is "bash", check if it's bash -c
if [ "$1" = "bash" ] && [ "$2" = "-c" ]; then
    # For bash -c "command", execute the command through our CLI
    exec python3 -m repomap_tool.cli $3
elif [ "$1" = "bash" ]; then
    # For other bash commands, execute directly
    exec "$@"
else
    # Otherwise, run the repomap-tool CLI
    # This allows users to run: docker run ... repomap-tool:latest search /workspace "query"
    # And it gets converted to: python3 -m repomap_tool.cli search /workspace "query"
    exec python3 -m repomap_tool.cli "$@"
fi
