#!/bin/bash

echo "🧪 Testing RepoMap-Tool Tool Against Real Codebase"
echo "===================================================="

# Check if we're in CI (DOCKER_IMAGE_NAME is set) or local development
if [ -n "$DOCKER_IMAGE_NAME" ]; then
    echo "📦 CI mode: Using pre-built Docker image"
    echo "Image: ${DOCKER_IMAGE_NAME}:${DOCKER_TAG}"
else
    echo "📦 Local mode: Building Docker image..."
    make docker-build
    if [ $? -ne 0 ]; then
        echo "❌ Build failed"
        exit 1
    fi
    echo "✅ Build successful"
fi

# Function to run a test in a separate container
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo ""
    echo "🔍 $test_name"
    echo "$(echo "$test_name" | sed 's/./-/g')"
    
    # Use environment variables for Docker image, fallback to repomap-tool for local development
    local docker_image="${DOCKER_IMAGE_NAME:-repomap-tool}:${DOCKER_TAG:-latest}"
    
    # Run test in separate container instance against the real codebase
    # Run command directly so the entrypoint script can handle it
    if docker run --rm -v "$(pwd):/project" "$docker_image" $test_command; then
        echo "✅ $test_name passed"
        return 0
    else
        echo "❌ $test_name failed"
        return 1
    fi
}

# Test 1: Analyze the real repomap-tool codebase
run_test "Test 1: Analyze Real Codebase" \
    "analyze /project --semantic --threshold 0.05 --verbose --output json" || exit 1

# Test 2: Search for specific identifiers in the real codebase
run_test "Test 2: Search for DockerRepoMap Class" \
    "search /project 'DockerRepoMap' --match-type hybrid --threshold 0.5 --verbose --output json" || exit 1

# Test 3: Search for function names
run_test "Test 3: Search for analyze_project Function" \
    "search /project 'analyze_project' --match-type fuzzy --threshold 0.6 --verbose --output json" || exit 1

# Test 4: Search for matcher classes (fixed query)
run_test "Test 4: Search for FuzzyMatcher Class" \
    "search /project 'FuzzyMatcher' --match-type fuzzy --threshold 0.5 --verbose --output json" || exit 1

# Test 5: Search for SemanticMatcher
run_test "Test 5: Search for SemanticMatcher Class" \
    "search /project 'SemanticMatcher' --match-type fuzzy --threshold 0.5 --verbose --output json" || exit 1

# Test 6: Search for CLI commands
run_test "Test 6: Search for CLI Commands" \
    "search /project 'analyze' --match-type semantic --threshold 0.4 --verbose --output json" || exit 1

# Test 7: Analyze with fuzzy matching
run_test "Test 7: Fuzzy Analysis of Real Codebase" \
    "analyze /project --fuzzy --threshold 0.6 --verbose --output json" || exit 1

# Test 8: Analyze with hybrid matching
run_test "Test 8: Hybrid Analysis of Real Codebase" \
    "analyze /project --fuzzy --semantic --threshold 0.1 --verbose --output json" || exit 1

# Test 9: Search for configuration related code
run_test "Test 9: Search for Configuration Code" \
    "search /project 'config' --match-type semantic --threshold 0.3 --verbose --output json" || exit 1

# Test 10: Search for test related code
run_test "Test 10: Search for Test Code" \
    "search /project 'test' --match-type hybrid --threshold 0.4 --verbose --output json" || exit 1

# Test 11: Search for specific function types
run_test "Test 11: Search for Function Definitions" \
    "search /project 'def' --match-type fuzzy --threshold 0.5 --verbose --output json" || exit 1

# Test 12: Search for class definitions
run_test "Test 12: Search for Class Definitions" \
    "search /project 'class' --match-type fuzzy --threshold 0.5 --verbose --output json" || exit 1

echo ""
echo "✅ All Docker tests against real codebase completed successfully!"
echo ""
echo "🎯 Key Benefits of RepoMap Tool:"
echo "   - Real codebase analysis and matching"
echo "   - Semantic code understanding"
echo "   - Fuzzy string matching capabilities"
echo "   - Configurable thresholds for precision/recall"
echo "   - Multiple output formats (JSON, text, markdown)"
echo "   - Docker-based deployment for consistency"
echo "   - Isolated container testing for reliability"
echo "   - Works against actual production codebases"
