#!/bin/bash

echo "🧪 Testing Integrated Adaptive Semantic Matching"
echo "================================================"

# Build the Docker image with adaptive semantic matching
echo "📦 Building Docker image..."
make docker-build

if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi

echo "✅ Build successful"

# Create a test project directory
echo "📁 Creating test project..."
TEST_PROJECT_DIR=$(mktemp -d)
# Ensure cleanup on exit (including error exits)
trap 'rm -rf "$TEST_PROJECT_DIR"' EXIT
echo "Test project created at: $TEST_PROJECT_DIR"

# Create sample Python files for testing
cat > "$TEST_PROJECT_DIR/auth.py" << 'EOF'
def authenticate_user(username, password):
    """Authenticate a user with username and password."""
    if username and password:
        return True
    return False

def user_login(credentials):
    """Process user login with credentials."""
    return authenticate_user(credentials.get('username'), credentials.get('password'))

class UserAuth:
    def __init__(self):
        self.logged_in = False
    
    def login(self, username, password):
        self.logged_in = authenticate_user(username, password)
        return self.logged_in
EOF

cat > "$TEST_PROJECT_DIR/data_processor.py" << 'EOF'
def process_data(data_input):
    """Process input data and return results."""
    if not data_input:
        return None
    return [item.upper() for item in data_input]

def data_handler(raw_data):
    """Handle raw data processing."""
    processed = process_data(raw_data)
    return processed

class DataProcessor:
    def __init__(self):
        self.cache = {}
    
    def process(self, data):
        return process_data(data)
EOF

cat > "$TEST_PROJECT_DIR/README.md" << 'EOF'
# Test Project for RepoMap Tool

This is a simple test project to verify the RepoMap Tool functionality.
EOF

echo "✅ Test project created with sample files"

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

# Test 13: Search for authentication related code
run_test "Test 13: Search for Authentication Code" \
    "search /project 'authenticate' --match-type hybrid --threshold 0.5 --verbose --output json" || exit 1

# Test 14: Analyze with high threshold
run_test "Test 14: High Threshold Analysis" \
    "analyze /project --semantic --threshold 0.8 --verbose --output json" || exit 1

echo ""
echo "✅ All tests completed successfully!"
echo ""
echo "🎯 Key Benefits of RepoMap Tool:"
echo "   - Semantic code analysis and matching"
echo "   - Fuzzy string matching capabilities"
echo "   - Configurable thresholds for precision/recall"
echo "   - Multiple output formats (JSON, text, markdown)"
echo "   - Docker-based deployment for consistency"
echo "   - Isolated container testing for reliability"
