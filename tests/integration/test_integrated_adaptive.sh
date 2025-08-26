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

# Test 1: Basic adaptive semantic matching
echo ""
echo "🔍 Test 1: Basic Adaptive Semantic Matching"
echo "-------------------------------------------"
docker run --rm -v $(pwd)/..:/project repomap-tool /project \
    --mentioned-idents "process,valid,create" \
    --adaptive-semantic \
    --semantic-threshold 0.05 \
    --verbose

# Test 2: Domain-specific terms
echo ""
echo "🔍 Test 2: Domain-Specific Terms"
echo "--------------------------------"
docker run --rm -v $(pwd)/..:/project repomap-tool /project \
    --mentioned-idents "widget,gadget,doohickey" \
    --adaptive-semantic \
    --semantic-threshold 0.1 \
    --verbose

# Test 3: Combined fuzzy + adaptive semantic
echo ""
echo "🔍 Test 3: Combined Fuzzy + Adaptive Semantic"
echo "---------------------------------------------"
docker run --rm -v $(pwd)/..:/project repomap-tool /project \
    --mentioned-idents "auth,data,file" \
    --fuzzy-match \
    --fuzzy-threshold 60 \
    --adaptive-semantic \
    --semantic-threshold 0.1 \
    --verbose

# Test 4: Complex queries
echo ""
echo "🔍 Test 4: Complex Queries"
echo "--------------------------"
docker run --rm -v $(pwd)/..:/project repomap-tool /project \
    --mentioned-idents "connection pool,rate limit,audit trail" \
    --adaptive-semantic \
    --semantic-threshold 0.2 \
    --verbose

# Test 5: Low threshold to see more matches
echo ""
echo "🔍 Test 5: Low Threshold (More Matches)"
echo "---------------------------------------"
docker run --rm -v $(pwd)/..:/project repomap-tool /project \
    --mentioned-idents "user,api,db" \
    --adaptive-semantic \
    --semantic-threshold 0.01 \
    --verbose

echo ""
echo "✅ All tests completed!"
echo ""
echo "🎯 Key Benefits of Adaptive Semantic Matching:"
echo "   - Learns from actual codebase patterns"
echo "   - No predefined categories needed"
echo "   - Handles domain-specific terminology"
echo "   - Adapts to different naming conventions"
echo "   - Discovers semantic relationships automatically"
