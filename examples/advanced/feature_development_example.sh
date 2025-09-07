#!/bin/bash
# feature_development_example.sh - Example of using docker-repomap for feature development

# Set your project path here (use absolute path)
PROJECT_PATH="${1:-$(pwd)/..}"

# Convert to absolute path
PROJECT_PATH=$(realpath "$PROJECT_PATH")

echo "Feature Development with RepoMap-Tool"
echo "======================================"
echo "Project: $PROJECT_PATH"
echo "Example: Adding 'aider export' command"
echo ""

# Function to generate repo map with context
generate_feature_map() {
    local step="$1"
    local description="$2"
    local cmd="$3"
    
    echo "=== STEP $step: $description ==="
    echo "Command: $cmd"
    echo "Output:"
    echo "----------------------------------------"
    eval "$cmd"
    echo "----------------------------------------"
    echo ""
}

# Step 1: Initial understanding of the codebase structure
echo "STEP 1: Understanding the codebase structure"
generate_feature_map "1" "Get overview of main entry points and command structure" \
    "docker run --rm -v $PROJECT_PATH:/project repomap-tool /project --map-tokens 4096 --mentioned-files 'aider/main.py,aider/commands.py' --mentioned-idents 'main,command,cli'"

# Step 2: Focus on command system
echo "STEP 2: Understanding the command system"
generate_feature_map "2" "Focus on command handling and argument parsing" \
    "docker run --rm -v $PROJECT_PATH:/project repomap-tool /project --map-tokens 4096 --mentioned-files 'aider/commands.py,aider/args.py' --mentioned-idents 'command,argparse,parser,add_argument'"

# Step 3: Look at existing commands for patterns
echo "STEP 3: Understanding existing command patterns"
generate_feature_map "3" "Analyze existing commands to understand patterns" \
    "docker run --rm -v $PROJECT_PATH:/project repomap-tool /project --map-tokens 4096 --mentioned-idents 'cmd_,def cmd_'"

# Step 4: Focus on conversation/history system
echo "STEP 4: Understanding conversation and history system"
generate_feature_map "4" "Focus on conversation and history management" \
    "docker run --rm -v $PROJECT_PATH:/project repomap-tool /project --map-tokens 4096 --mentioned-files 'aider/history.py,aider/io.py' --mentioned-idents 'history,conversation,chat,save,load'"

# Step 5: Look at file I/O and export patterns
echo "STEP 5: Understanding file I/O and export patterns"
generate_feature_map "5" "Focus on file I/O and export functionality" \
    "docker run --rm -v $PROJECT_PATH:/project repomap-tool /project --map-tokens 4096 --mentioned-idents 'write,read,export,save,file,io'"

# Step 6: Focus on specific files you'll be working on
echo "STEP 6: Detailed analysis of files you'll modify"
generate_feature_map "6" "Detailed analysis of commands.py and related files" \
    "docker run --rm -v $PROJECT_PATH:/project repomap-tool /project --map-tokens 8192 --mentioned-files 'aider/commands.py,aider/history.py,aider/io.py' --mentioned-idents 'export,conversation,history,file'"

echo "=== FEATURE DEVELOPMENT WORKFLOW ==="
echo ""
echo "Now you have comprehensive context for developing the 'aider export' feature!"
echo ""
echo "Based on the repo maps above, you would:"
echo ""
echo "1. Add the new command to aider/commands.py:"
echo "   def cmd_export(self, args):"
echo "       # Export conversation to file"
echo ""
echo "2. Add argument parsing to aider/args.py:"
echo "   parser.add_argument('--export', help='Export conversation to file')"
echo ""
echo "3. Use the conversation/history system from aider/history.py"
echo ""
echo "4. Use file I/O patterns from aider/io.py"
echo ""
echo "=== ONGOING DEVELOPMENT ==="
echo ""
echo "As you work on the feature, use dynamic context:"
echo ""
echo "# When working on commands.py"
echo "docker run --rm -v $PROJECT_PATH:/project repomap-tool /project \\"
echo "  --map-tokens 4096 \\"
echo "  --chat-files 'aider/commands.py' \\"
echo "  --mentioned-idents 'export,conversation,history'"
echo ""
echo "# When working on history.py"
echo "docker run --rm -v $PROJECT_PATH:/project repomap-tool /project \\"
echo "  --map-tokens 4096 \\"
echo "  --chat-files 'aider/history.py,aider/commands.py' \\"
echo "  --mentioned-idents 'save,export,file'"
echo ""
echo "# When testing the feature"
echo "docker run --rm -v $PROJECT_PATH:/project repomap-tool /project \\"
echo "  --map-tokens 4096 \\"
echo "  --mentioned-files 'aider/commands.py,aider/history.py,aider/io.py' \\"
echo "  --mentioned-idents 'test,export,conversation'"
echo ""
echo "=== BENEFITS OF THIS APPROACH ==="
echo ""
echo "1. **Comprehensive Context**: You understand the entire codebase structure"
echo "2. **Pattern Recognition**: You see how existing commands are implemented"
echo "3. **Dependency Awareness**: You know which files and functions you'll need"
echo "4. **Consistent Style**: You follow the same patterns as existing code"
echo "5. **Efficient Development**: You don't waste time exploring irrelevant code"
echo ""
echo "This approach gives you the same level of codebase understanding that"
echo "aider's internal RepoMap provides, but as an external tool!"
