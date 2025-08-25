#!/bin/bash
# fuzzy_matching_examples.sh - Comprehensive examples of fuzzy matching usage

PROJECT_PATH="${1:-$(pwd)/..}"
PROJECT_PATH=$(realpath "$PROJECT_PATH")

echo "🚀 Docker RepoMap - Fuzzy Matching Examples"
echo "=========================================="
echo "Project: $PROJECT_PATH"
echo ""

# Example 1: Basic fuzzy matching
echo "1️⃣ Basic Fuzzy Matching"
echo "----------------------"
echo "Query: 'auth' (finds authentication-related functions)"
docker run --rm -v $PROJECT_PATH:/project repomap-tool /project \
  --mentioned-idents 'auth' \
  --fuzzy-match \
  --map-tokens 2048
echo ""

# Example 2: High threshold matching
echo "2️⃣ High Threshold Matching (80%)"
echo "--------------------------------"
echo "Query: 'validate' (only very close matches)"
docker run --rm -v $PROJECT_PATH:/project repomap-tool /project \
  --mentioned-idents 'validate' \
  --fuzzy-match \
  --fuzzy-threshold 80 \
  --map-tokens 1024
echo ""

# Example 3: Custom strategies
echo "3️⃣ Custom Strategies (prefix + substring only)"
echo "----------------------------------------------"
echo "Query: 'process' (using prefix and substring matching)"
docker run --rm -v $PROJECT_PATH:/project repomap-tool /project \
  --mentioned-idents 'process' \
  --fuzzy-match \
  --fuzzy-strategies 'prefix,substring' \
  --map-tokens 1024
echo ""

# Example 4: Multiple identifiers
echo "4️⃣ Multiple Identifiers"
echo "----------------------"
echo "Query: 'auth,process,validate' (multiple fuzzy searches)"
docker run --rm -v $PROJECT_PATH:/project repomap-tool /project \
  --mentioned-idents 'auth,process,validate' \
  --fuzzy-match \
  --map-tokens 2048
echo ""

# Example 5: Low threshold for discovery
echo "5️⃣ Discovery Mode (low threshold)"
echo "--------------------------------"
echo "Query: 'test' (finds many test-related functions)"
docker run --rm -v $PROJECT_PATH:/project repomap-tool /project \
  --mentioned-idents 'test' \
  --fuzzy-match \
  --fuzzy-threshold 50 \
  --map-tokens 1024
echo ""

# Example 6: Word-based matching
echo "6️⃣ Word-Based Matching"
echo "---------------------"
echo "Query: 'user auth' (finds functions with both words)"
docker run --rm -v $PROJECT_PATH:/project repomap-tool /project \
  --mentioned-idents 'user auth' \
  --fuzzy-match \
  --fuzzy-strategies 'word' \
  --map-tokens 1024
echo ""

# Example 7: Combined with mentioned files
echo "7️⃣ Combined with Mentioned Files"
echo "-------------------------------"
echo "Query: 'auth' + mentioned files"
docker run --rm -v $PROJECT_PATH:/project repomap-tool /project \
  --mentioned-idents 'auth' \
  --mentioned-files 'aider/repomap.py,aider/coders/base_coder.py' \
  --fuzzy-match \
  --map-tokens 2048
echo ""

# Example 8: Performance comparison
echo "8️⃣ Performance Comparison"
echo "------------------------"
echo "Without fuzzy matching:"
docker run --rm -v $PROJECT_PATH:/project repomap-tool /project \
  --mentioned-idents 'authenticate_user' \
  --map-tokens 1024

echo ""
echo "With fuzzy matching:"
docker run --rm -v $PROJECT_PATH:/project repomap-tool /project \
  --mentioned-idents 'auth' \
  --fuzzy-match \
  --map-tokens 1024
echo ""

echo "✅ Fuzzy Matching Examples Complete!"
echo ""
echo "Key Features Demonstrated:"
echo "• Multiple matching strategies (prefix, substring, levenshtein, word)"
echo "• Configurable similarity thresholds"
echo "• Intelligent identifier discovery"
echo "• Integration with existing RepoMap functionality"
echo "• Performance optimization with caching"
