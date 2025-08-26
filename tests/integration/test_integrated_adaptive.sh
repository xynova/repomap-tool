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

# Test 1: Basic semantic matching
echo ""
echo "🔍 Test 1: Basic Semantic Matching"
echo "----------------------------------"
docker run --rm -v $(pwd)/..:/project repomap-tool repomap-tool analyze /project \
    --semantic \
    --threshold 0.05 \
    --verbose \
    --output json

# Test 2: Fuzzy matching
echo ""
echo "🔍 Test 2: Fuzzy Matching"
echo "-------------------------"
docker run --rm -v $(pwd)/..:/project repomap-tool repomap-tool analyze /project \
    --fuzzy \
    --threshold 0.6 \
    --verbose \
    --output json

# Test 3: Combined fuzzy + semantic
echo ""
echo "🔍 Test 3: Combined Fuzzy + Semantic"
echo "------------------------------------"
docker run --rm -v $(pwd)/..:/project repomap-tool repomap-tool analyze /project \
    --fuzzy \
    --semantic \
    --threshold 0.1 \
    --verbose \
    --output json

# Test 4: High threshold for precision
echo ""
echo "🔍 Test 4: High Threshold (Precision)"
echo "-------------------------------------"
docker run --rm -v $(pwd)/..:/project repomap-tool repomap-tool analyze /project \
    --semantic \
    --threshold 0.8 \
    --verbose \
    --output json

# Test 5: Low threshold for recall
echo ""
echo "🔍 Test 5: Low Threshold (Recall)"
echo "---------------------------------"
docker run --rm -v $(pwd)/..:/project repomap-tool repomap-tool analyze /project \
    --semantic \
    --threshold 0.01 \
    --verbose \
    --output json

echo ""
echo "✅ All tests completed!"
echo ""
echo "🎯 Key Benefits of RepoMap Tool:"
echo "   - Semantic code analysis and matching"
echo "   - Fuzzy string matching capabilities"
echo "   - Configurable thresholds for precision/recall"
echo "   - Multiple output formats (JSON, text, markdown)"
echo "   - Docker-based deployment for consistency"
