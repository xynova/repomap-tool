#!/bin/bash
# conversation_simulator.sh - Simulate a conversation with dynamic repo map generation

# Set your project path here (use absolute path)
PROJECT_PATH="${1:-$(pwd)/..}"

# Convert to absolute path
PROJECT_PATH=$(realpath "$PROJECT_PATH")

echo "Conversation Simulator with Dynamic RepoMap"
echo "==========================================="
echo "Project: $PROJECT_PATH"
echo ""

# Function to generate repo map with context
generate_repo_map() {
    local message="$1"
    local chat_files="$2"
    local mentioned_files="$3"
    local mentioned_idents="$4"
    local map_tokens="${5:-1024}"
    
    echo "Message: $message"
    echo "Context:"
    echo "  Chat files: $chat_files"
    echo "  Mentioned files: $mentioned_files"
    echo "  Mentioned identifiers: $mentioned_idents"
    echo "  Token budget: $map_tokens"
    echo ""
    
    # Build command
    local cmd="docker run --rm -v $PROJECT_PATH:/project repomap-tool /project --map-tokens $map_tokens"
    
    if [ ! -z "$chat_files" ]; then
        cmd="$cmd --chat-files '$chat_files'"
    fi
    
    if [ ! -z "$mentioned_files" ]; then
        cmd="$cmd --mentioned-files '$mentioned_files'"
    fi
    
    if [ ! -z "$mentioned_idents" ]; then
        cmd="$cmd --mentioned-idents '$mentioned_idents'"
    fi
    
    echo "Running: $cmd"
    echo "Output:"
    echo "----------------------------------------"
    eval "$cmd"
    echo "----------------------------------------"
    echo ""
}

# Conversation flow
echo "=== Starting Conversation ==="

# 1. Initial question
echo "User: What is this codebase about?"
generate_repo_map "What is this codebase about?" "" "" "" 1024

# 2. Specific file mention
echo "User: Can you explain what happens in src/main.py?"
generate_repo_map "Can you explain what happens in src/main.py?" "" "src/main.py" "" 1024

# 3. Function mention
echo "User: How does the process_data function work?"
generate_repo_map "How does the process_data function work?" "" "" "process_data" 1024

# 4. Add file to chat context
echo "User: I want to work on the authentication system"
generate_repo_map "I want to work on the authentication system" "src/auth.py" "" "authenticate,auth,login" 2048

# 5. Complex request with multiple context
echo "User: I need to refactor the authentication system to use JWT tokens"
generate_repo_map "I need to refactor the authentication system to use JWT tokens" "src/auth.py,src/models.py" "src/config/settings.py" "authenticate,jwt,token,user" 4096

# 6. Focus on specific functionality
echo "User: How does the error handling work in the data processing?"
generate_repo_map "How does the error handling work in the data processing?" "" "src/utils/helpers.py" "error,exception,handle" 2048

# 7. Architecture question
echo "User: What is the overall architecture of this application?"
generate_repo_map "What is the overall architecture of this application?" "" "src/main.py,src/config,src/models" "main,init,setup,config" 4096

echo "=== Conversation Complete ==="
echo ""
echo "This demonstrates how the repo map adapts to each message:"
echo "- Initial questions get general overview"
echo "- File mentions focus on specific files"
echo "- Function mentions focus on related code"
echo "- Chat files influence the ranking"
echo "- Complex requests get more tokens and broader context"
