#!/bin/bash
# quick_commands.sh - Quick, ready-to-use docker-repomap commands

# Set your project path here
PROJECT_PATH="${1:-$PWD}"

echo "Quick Docker RepoMap Commands"
echo "============================="
echo "Project: $PROJECT_PATH"
echo ""

# Function to run command and show output
run_command() {
    echo "Running: $1"
    echo "Output:"
    echo "----------------------------------------"
    eval "$1"
    echo "----------------------------------------"
    echo ""
}

# 1. Basic repo map
echo "1. Basic Repo Map (1024 tokens)"
run_command "docker run --rm -v $PROJECT_PATH:/project repomap-tool /project"

# 2. Detailed repo map
echo "2. Detailed Repo Map (2048 tokens)"
run_command "docker run --rm -v $PROJECT_PATH:/project repomap-tool /project --map-tokens 2048"

# 3. Cache stats
echo "3. Cache Statistics"
run_command "docker run --rm -v $PROJECT_PATH:/project repomap-tool /project --cache-stats"

# 4. Focus on main files
echo "4. Focus on Main Files"
run_command "docker run --rm -v $PROJECT_PATH:/project repomap-tool /project --mentioned-files 'main.py,app.py,index.js,main.go'"

# 5. Focus on common functions
echo "5. Focus on Common Functions"
run_command "docker run --rm -v $PROJECT_PATH:/project repomap-tool /project --mentioned-idents 'main,init,setup,config'"

# 6. Authentication focus
echo "6. Authentication Focus"
run_command "docker run --rm -v $PROJECT_PATH:/project repomap-tool /project --mentioned-idents 'auth,login,authenticate,user'"

# 7. Verbose output
echo "7. Verbose Output"
run_command "docker run --rm -v $PROJECT_PATH:/project repomap-tool /project --verbose"

# 8. Save to file
echo "8. Save to File"
run_command "docker run --rm -v $PROJECT_PATH:/project repomap-tool /project --output /tmp/repo_map_$(date +%Y%m%d_%H%M%S).txt"

echo "Done! Check the output above for each command."
