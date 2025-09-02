#!/bin/bash
# Basic Tree Exploration Workflow Example
# This script demonstrates the core tree exploration functionality

set -e

echo "🌳 Tree Exploration Basic Workflow Example"
echo "=========================================="
echo ""

# Set a session ID for this example
export REPOMAP_SESSION="example_session_$(date +%s)"
echo "💡 Using session: $REPOMAP_SESSION"
echo ""

# Step 1: Explore a project with an intent
echo "🔍 Step 1: Exploring project for 'authentication bugs'"
echo "Command: repomap-tool explore . 'authentication bugs'"
echo ""

# This would normally run the explore command
# repomap-tool explore . "authentication bugs"

echo "Expected output:"
echo "  🔍 Found 2-3 exploration contexts:"
echo "    • Auth Error Handling [id: auth_errors_abc123] (confidence: 0.92)"
echo "    • Frontend Auth Flow [id: frontend_auth_def456] (confidence: 0.87)"
echo "    • Auth Validation [id: auth_validation_ghi789] (confidence: 0.81)"
echo ""

# Step 2: Focus on a specific tree
echo "🎯 Step 2: Focusing on the Auth Error Handling tree"
echo "Command: repomap-tool focus auth_errors_abc123"
echo ""

# This would normally run the focus command
# repomap-tool focus auth_errors_abc123

echo "Expected output:"
echo "  ✅ Focused on tree: auth_errors_abc123"
echo ""

# Step 3: View the current tree
echo "📋 Step 3: Viewing the current tree structure"
echo "Command: repomap-tool map"
echo ""

# This would normally run the map command
# repomap-tool map

echo "Expected output:"
echo "  🌳 Exploration Tree: Auth Error Handling"
echo "  📍 Root: AuthErrorHandler"
echo "  🎯 Confidence: 0.92"
echo "  📊 Nodes: 5"
echo "  "
echo "  ├── AuthErrorHandler (src/auth/error_handler.py:15)"
echo "  │   ├── handle_login_error (src/auth/error_handler.py:42)"
echo "  │   ├── validate_credentials (src/auth/error_handler.py:68)"
echo "  │   └── log_auth_failure (src/auth/error_handler.py:85)"
echo "  ├── LoginValidator (src/auth/validators.py:12)"
echo "  └── AuthExceptions (src/auth/exceptions.py:8)"
echo ""

# Step 4: Expand the tree in a specific area
echo "🔍 Step 4: Expanding the tree in the validation area"
echo "Command: repomap-tool expand 'validation'"
echo ""

# This would normally run the expand command
# repomap-tool expand "validation"

echo "Expected output:"
echo "  ✅ Expanded tree in area: validation"
echo ""

# Step 5: View the expanded tree
echo "📋 Step 5: Viewing the expanded tree"
echo "Command: repomap-tool map --include-code"
echo ""

# This would normally run the map command with code
# repomap-tool map --include-code

echo "Expected output:"
echo "  🌳 Exploration Tree: Auth Error Handling"
echo "  📍 Root: AuthErrorHandler"
echo "  🎯 Confidence: 0.92"
echo "  📊 Nodes: 8"
echo "  "
echo "  ├── AuthErrorHandler (src/auth/error_handler.py:15)"
echo "  │   ├── handle_login_error (src/auth/error_handler.py:42)"
echo "  │   ├── validate_credentials (src/auth/error_handler.py:68)"
echo "  │   └── log_auth_failure (src/auth/error_handler.py:85)"
echo "  ├── LoginValidator (src/auth/validators.py:12)"
echo "  │   ├── check_password_strength (src/auth/validators.py:23)"
echo "  │   ├── validate_password_format (src/auth/validators.py:45)  # 🆕 EXPANDED"
echo "  │   └── check_common_passwords (src/auth/validators.py:67)   # 🆕 EXPANDED"
echo "  └── AuthExceptions (src/auth/exceptions.py:8)"
echo "  "
echo "  ✅ Expanded areas: validation"
echo ""

# Step 6: Check session status
echo "📊 Step 6: Checking session status"
echo "Command: repomap-tool status"
echo ""

# This would normally run the status command
# repomap-tool status

echo "Expected output:"
echo "  📊 Session Status: $REPOMAP_SESSION"
echo "  ═══════════════════════════════════════"
echo "  "
echo "  🎯 Current Focus: auth_errors_abc123"
echo "  📅 Session Started: [timestamp]"
echo "  🕐 Last Activity: [timestamp]"
echo "  "
echo "  🌳 Exploration Trees (1 total):"
echo "    1. 🎯 auth_errors_abc123 [FOCUSED] - Auth Error Handling"
echo "  "
echo "  💡 Quick Actions:"
echo "    repomap-tool map                          # View current focused tree"
echo "    repomap-tool expand <area>               # Expand current tree"
echo "    repomap-tool prune <area>                # Prune current tree"
echo ""

echo "🎉 Basic workflow demonstration complete!"
echo ""
echo "💡 To run this workflow with a real project:"
echo "   1. Navigate to your project directory"
echo "   2. Run each command in sequence"
echo "   3. Explore different areas and intents"
echo ""
echo "🔧 Available commands:"
echo "   repomap-tool explore <project> <intent>   # Discover trees"
echo "   repomap-tool focus <tree_id>              # Focus on tree"
echo "   repomap-tool expand <area>                # Expand tree"
echo "   repomap-tool prune <area>                 # Prune tree"
echo "   repomap-tool map                          # View tree"
echo "   repomap-tool status                       # Session status"
echo "   repomap-tool list-trees                   # List all trees"
