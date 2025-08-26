#!/bin/bash

set -e

# Function to show help
show_help() {
    echo "Docker RepoMap Tool"
    echo ""
    echo "Usage:"
    echo "  docker run repomap-tool <command> [options]"
    echo ""
    echo "Commands:"
    echo "  analyze <project_path>    Analyze a project and generate a code map"
    echo "  search <project_path> <query>  Search for identifiers in a project"
    echo "  config <project_path>     Generate a configuration file for the project"
    echo "  version                   Show version information"
    echo ""
    echo "Examples:"
    echo "  docker run -v /path/to/project:/project repomap-tool analyze /project"
    echo "  docker run -v /path/to/project:/project repomap-tool search /project 'auth'"
    echo "  docker run -v /path/to/project:/project repomap-tool config /project"
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

# Check if command is provided
if [[ -z "$1" ]]; then
    echo "Error: Command is required"
    echo ""
    show_help
    exit 1
fi

# Run the CLI
exec repomap-tool "$@"
