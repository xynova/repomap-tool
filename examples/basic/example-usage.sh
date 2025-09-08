#!/bin/bash

echo "RepoMap-Tool Tool - Example Usage"
echo "==================================="
echo ""

# Example 1: Basic usage
echo "Example 1: Basic repo map generation"
echo "------------------------------------"
echo "docker run -v /path/to/project:/project repomap-tool /project"
echo ""

# Example 2: With custom token budget
echo "Example 2: Custom token budget"
echo "------------------------------"
echo "docker run -v /path/to/project:/project repomap-tool /project --map-tokens 2048"
echo ""

# Example 3: Verbose output
echo "Example 3: Verbose output"
echo "-------------------------"
echo "docker run -v /path/to/project:/project repomap-tool /project --verbose"
echo ""

# Example 4: Show cache statistics
echo "Example 4: Cache statistics"
echo "---------------------------"
echo "docker run -v /path/to/project:/project repomap-tool /project --cache-stats"
echo ""

# Example 5: Clear cache and regenerate
echo "Example 5: Clear cache and regenerate"
echo "-------------------------------------"
echo "docker run -v /path/to/project:/project repomap-tool /project --clear-cache --force-refresh"
echo ""

# Example 6: Custom output file
echo "Example 6: Custom output file"
echo "-----------------------------"
echo "docker run -v /path/to/project:/project repomap-tool /project --output /project/custom_map.txt"
echo ""

# Example 7: Using the run script
echo "Example 7: Using the run script"
echo "-------------------------------"
echo "./run.sh /path/to/project"
echo "./run.sh /path/to/project 2048"
echo "./run.sh /path/to/project 2048 true"
echo ""

# Example 8: Docker Compose
echo "Example 8: Docker Compose"
echo "-------------------------"
echo "docker-compose up --build"
echo ""

echo "For more information, see README.md"
