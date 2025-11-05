#!/bin/bash

# Script to clean up stuck test processes
# Use this when the cancel button doesn't properly terminate test processes

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

# Find and kill any remaining pytest processes
PYTEST_PIDS=$(pgrep -f "python.*pytest" 2>/dev/null || true)
if [ -n "$PYTEST_PIDS" ]; then
    echo "🔍 Found pytest processes: $PYTEST_PIDS"
    for pid in $PYTEST_PIDS; do
        if [ "$pid" != "$$" ]; then  # Don't kill ourselves
            echo "💀 Terminating pytest process $pid..."
            kill -TERM "$pid" 2>/dev/null || true
        fi
    done
    sleep 1
    
    # Force kill if still running
    for pid in $PYTEST_PIDS; do
        if [ "$pid" != "$$" ] && kill -0 "$pid" 2>/dev/null; then
            echo "💀 Force killing pytest process $pid..."
            kill -KILL "$pid" 2>/dev/null || true
        fi
    done
fi

# Also check for any Python processes that might be test-related
PYTHON_PIDS=$(pgrep -f "python.*test" 2>/dev/null || true)
if [ -n "$PYTHON_PIDS" ]; then
    echo "🔍 Found test-related Python processes: $PYTHON_PIDS"
    for pid in $PYTHON_PIDS; do
        if [ "$pid" != "$$" ]; then  # Don't kill ourselves
            echo "💀 Terminating test process $pid..."
            kill -TERM "$pid" 2>/dev/null || true
        fi
    done
    sleep 1
    
    # Force kill if still running
    for pid in $PYTHON_PIDS; do
        if [ "$pid" != "$$" ] && kill -0 "$pid" 2>/dev/null; then
            echo "💀 Force killing test process $pid..."
            kill -KILL "$pid" 2>/dev/null || true
        fi
    done
fi

echo "✅ Cleanup completed"
echo "📊 Remaining processes:"
ps aux | grep -E "(pytest|python.*test)" | grep -v grep || echo "No test processes found"
