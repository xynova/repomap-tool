#!/bin/bash

# Entrypoint script for repomap-tool Docker container
# Uses the installed repomap-tool command-line entry point

set -e

# If the first argument is "bash", execute bash commands directly
if [ "$1" = "bash" ]; then
    exec "$@"
else
    # Otherwise, run the repomap-tool CLI using the installed entry point
    # This allows users to run: docker run ... repomap-tool:latest search /workspace "query"
    exec repomap-tool "$@"
fi
