#!/bin/bash

# Wrapper script to run tests with proper cleanup on termination
# This script ensures all pytest worker processes are terminated when cancelled

set -e

# Function to cleanup processes
cleanup_processes() {
    echo "🧹 Cleaning up test processes..."
    
    # Find and kill pytest worker processes
    WORKER_PIDS=$(pgrep -f "pytest.*worker" 2>/dev/null || true)
    if [ -n "$WORKER_PIDS" ]; then
        echo "🔍 Found worker processes: $WORKER_PIDS"
        for pid in $WORKER_PIDS; do
            echo "💀 Terminating worker process $pid..."
            kill -TERM "$pid" 2>/dev/null || true
        done
        sleep 1
        
        # Force kill if still running
        for pid in $WORKER_PIDS; do
            if kill -0 "$pid" 2>/dev/null; then
                echo "💀 Force killing worker process $pid..."
                kill -KILL "$pid" 2>/dev/null || true
            fi
        done
    fi
    
    # Find and kill any remaining pytest processes (excluding our own)
    PYTEST_PIDS=$(pgrep -f "python.*pytest" 2>/dev/null || true)
    if [ -n "$PYTEST_PIDS" ]; then
        echo "🔍 Found pytest processes: $PYTEST_PIDS"
        for pid in $PYTEST_PIDS; do
            # Don't kill ourselves or the main test process
            if [ "$pid" != "$$" ] && [ "$pid" != "$TEST_PID" ]; then
                echo "💀 Terminating pytest process $pid..."
                kill -TERM "$pid" 2>/dev/null || true
            fi
        done
        sleep 1
        
        # Force kill if still running
        for pid in $PYTEST_PIDS; do
            if [ "$pid" != "$$" ] && [ "$pid" != "$TEST_PID" ] && kill -0 "$pid" 2>/dev/null; then
                echo "💀 Force killing pytest process $pid..."
                kill -KILL "$pid" 2>/dev/null || true
            fi
        done
    fi
    
    echo "✅ Cleanup completed"
}

# Set up signal handlers
trap cleanup_processes SIGINT SIGTERM

# Run the actual test command
echo "🚀 Running tests with automatic cleanup..."
"$@"
