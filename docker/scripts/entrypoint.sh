#!/bin/bash

set -e

# Function to show help
show_help() {
    echo "Docker RepoMap Tool"
    echo ""
    echo "Usage:"
    echo "  docker run repomap-tool <project_path> [options]"
    echo ""
    echo "Examples:"
    echo "  docker run -v /path/to/project:/project repomap-tool /project"
    echo "  docker run -v /path/to/project:/project repomap-tool /project --map-tokens 2048"
    echo "  docker run -v /path/to/project:/project repomap-tool /project --cache-stats"
    echo ""
    echo "Options:"
    echo "  --map-tokens N     Token budget for repo map (default: 1024)"
    echo "  --output FILE      Output file path"
    echo "  --clear-cache      Clear cache before generating"
    echo "  --force-refresh    Force refresh of repo map"
    echo "  --cache-stats      Show cache statistics"
    echo "  --verbose          Verbose output"
    echo "  --extensions       File extensions to include"
    echo ""
    echo "Volume mounts:"
    echo "  -v /host/project:/project    Mount your project directory"
    echo "  -v /host/cache:/app/cache    Mount cache directory (optional)"
}

# Check if help is requested
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    show_help
    exit 0
fi

# Check if project path is provided
if [[ -z "$1" ]]; then
    echo "Error: Project path is required"
    echo ""
    show_help
    exit 1
fi

# Run the repomap script
exec python external_repomap.py "$@"
