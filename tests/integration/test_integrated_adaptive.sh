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
    
    # Run test in separate container instance
    if docker run --rm -v "$TEST_PROJECT_DIR:/project" repomap-tool $test_command; then
        echo "✅ $test_name passed"
        return 0
    else
        echo "❌ $test_name failed"
        return 1
    fi
}

# Test 1: Basic semantic matching
run_test "Test 1: Basic Semantic Matching" \
    "repomap-tool analyze /project --semantic --threshold 0.05 --verbose --output json" || exit 1

# Test 2: Fuzzy matching
run_test "Test 2: Fuzzy Matching" \
    "repomap-tool analyze /project --fuzzy --threshold 0.6 --verbose --output json" || exit 1

# Test 3: Combined fuzzy + semantic
run_test "Test 3: Combined Fuzzy + Semantic" \
    "repomap-tool analyze /project --fuzzy --semantic --threshold 0.1 --verbose --output json" || exit 1

# Test 4: Search functionality
run_test "Test 4: Search Functionality" \
    "repomap-tool search /project 'authenticate' --match-type hybrid --threshold 0.5 --verbose --output json" || exit 1

# Test 5: High threshold for precision
run_test "Test 5: High Threshold (Precision)" \
    "repomap-tool analyze /project --semantic --threshold 0.8 --verbose --output json" || exit 1

# Test 6: Help command
run_test "Test 6: Help Command" \
    "repomap-tool --help" || exit 1

# Test 7: Version command
run_test "Test 7: Version Command" \
    "repomap-tool --version" || exit 1

# Cleanup
echo ""
echo "🧹 Cleaning up test project..."
rm -rf "$TEST_PROJECT_DIR"

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
