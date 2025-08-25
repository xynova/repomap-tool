#!/bin/bash
# refactoring_commands.sh - Commands optimized for refactoring work

# Set your project path here (use absolute path)
PROJECT_PATH="${1:-$(pwd)}"

# Convert to absolute path
PROJECT_PATH=$(realpath "$PROJECT_PATH")

echo "Refactoring-Optimized RepoMap Commands"
echo "====================================="
echo "Project: $PROJECT_PATH"
echo ""

# Function to generate repo map with context
generate_refactoring_map() {
    local description="$1"
    local cmd="$2"
    
    echo "=== $description ==="
    echo "Command: $cmd"
    echo "Output:"
    echo "----------------------------------------"
    eval "$cmd"
    echo "----------------------------------------"
    echo ""
}

# 1. Comprehensive Analysis (Best for refactoring)
echo "1. COMPREHENSIVE ANALYSIS (Recommended for refactoring)"
generate_refactoring_map "Full codebase analysis with maximum detail" \
    "docker run --rm -v $PROJECT_PATH:/project repomap-tool /project --map-tokens 8192"

# 2. Architecture-focused analysis
echo "2. ARCHITECTURE FOCUS"
generate_refactoring_map "Focus on main files and core architecture" \
    "docker run --rm -v $PROJECT_PATH:/project repomap-tool /project --map-tokens 4096 --mentioned-files 'main.py,app.py,index.js,main.go,__init__.py' --mentioned-idents 'main,init,setup,config,app'"

# 3. Class and function analysis
echo "3. CLASS AND FUNCTION ANALYSIS"
generate_refactoring_map "Focus on classes, methods, and functions" \
    "docker run --rm -v $PROJECT_PATH:/project repomap-tool /project --map-tokens 4096 --mentioned-idents 'class,def,function,method,constructor'"

# 4. Database and data models
echo "4. DATA MODELS AND DATABASE"
generate_refactoring_map "Focus on data models and database code" \
    "docker run --rm -v $PROJECT_PATH:/project repomap-tool /project --map-tokens 4096 --mentioned-idents 'model,schema,database,db,table,entity'"

# 5. API and endpoints
echo "5. API AND ENDPOINTS"
generate_refactoring_map "Focus on API endpoints and routes" \
    "docker run --rm -v $PROJECT_PATH:/project repomap-tool /project --map-tokens 4096 --mentioned-idents 'api,route,endpoint,controller,handler'"

# 6. Configuration and settings
echo "6. CONFIGURATION AND SETTINGS"
generate_refactoring_map "Focus on configuration and settings files" \
    "docker run --rm -v $PROJECT_PATH:/project repomap-tool /project --map-tokens 2048 --mentioned-files 'config,settings,env,.env,*.conf,*.yml,*.yaml' --mentioned-idents 'config,settings,env,setup'"

# 7. Testing and validation
echo "7. TESTING AND VALIDATION"
generate_refactoring_map "Focus on test files and validation" \
    "docker run --rm -v $PROJECT_PATH:/project repomap-tool /project --map-tokens 2048 --mentioned-files 'test,spec,specs,*_test.py,*_test.js' --mentioned-idents 'test,assert,expect,validate'"

# 8. Utility and helper functions
echo "8. UTILITY AND HELPER FUNCTIONS"
generate_refactoring_map "Focus on utility and helper functions" \
    "docker run --rm -v $PROJECT_PATH:/project repomap-tool /project --map-tokens 2048 --mentioned-files 'utils,helpers,common,shared' --mentioned-idents 'util,helper,common,shared'"

# 9. Error handling and logging
echo "9. ERROR HANDLING AND LOGGING"
generate_refactoring_map "Focus on error handling and logging" \
    "docker run --rm -v $PROJECT_PATH:/project repomap-tool /project --map-tokens 2048 --mentioned-idents 'error,exception,log,logger,handle,try,catch'"

# 10. Performance and optimization
echo "10. PERFORMANCE AND OPTIMIZATION"
generate_refactoring_map "Focus on performance-related code" \
    "docker run --rm -v $PROJECT_PATH:/project repomap-tool /project --map-tokens 2048 --mentioned-idents 'performance,optimize,cache,async,thread,pool'"

echo "=== REFACTORING WORKFLOW ==="
echo ""
echo "For refactoring work, use this workflow:"
echo ""
echo "1. Start with COMPREHENSIVE ANALYSIS (8192 tokens) to understand the full codebase"
echo "2. Use specific focus commands based on what you're refactoring:"
echo "   - Architecture changes → Use ARCHITECTURE FOCUS"
echo "   - Data model changes → Use DATA MODELS AND DATABASE"
echo "   - API changes → Use API AND ENDPOINTS"
echo "   - Configuration changes → Use CONFIGURATION AND SETTINGS"
echo ""
echo "3. For ongoing refactoring, use dynamic context:"
echo "   docker run --rm -v $PROJECT_PATH:/project repomap-tool /project \\"
echo "     --map-tokens 4096 \\"
echo "     --chat-files 'src/main.py,src/models.py' \\"
echo "     --mentioned-files 'src/config/settings.py' \\"
echo "     --mentioned-idents 'refactor,optimize,improve'"
echo ""
echo "4. Always check cache stats to ensure you're getting fresh data:"
echo "   docker run --rm -v $PROJECT_PATH:/project repomap-tool /project --cache-stats"
echo ""
echo "5. Force refresh when making significant changes:"
echo "   docker run --rm -v $PROJECT_PATH:/project repomap-tool /project --force-refresh --map-tokens 8192"
