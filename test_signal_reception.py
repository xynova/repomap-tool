#!/usr/bin/env python3
"""
Test script to check if Cursor's test runner sends SIGINT properly.
This script will log all signals it receives and run a simple test.
"""

import signal
import sys
import time
import os
import threading

# Track all signals received
signals_received = []
signal_lock = threading.Lock()

def signal_handler(signum, frame):
    """Handle all signals and log them."""
    with signal_lock:
        signals_received.append((signum, time.time()))
        print(f"\n🛑 SIGNAL RECEIVED: {signum} at {time.time()}")
        print(f"   Signal name: {signal.Signals(signum).name if hasattr(signal.Signals, signum) else 'UNKNOWN'}")
        print(f"   Frame: {frame}")
        print(f"   Total signals received: {len(signals_received)}")
        
        # Don't exit immediately, let's see what happens
        if signum == signal.SIGINT:
            print("   → SIGINT received, but continuing to run...")
        elif signum == signal.SIGTERM:
            print("   → SIGTERM received, but continuing to run...")
        else:
            print(f"   → Signal {signum} received, but continuing to run...")

def register_signal_handlers():
    """Register handlers for common signals."""
    print("🔧 Registering signal handlers...")
    
    # Register for common signals
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGQUIT, signal_handler)
    signal.signal(signal.SIGHUP, signal_handler)
    signal.signal(signal.SIGUSR1, signal_handler)
    signal.signal(signal.SIGUSR2, signal_handler)
    
    print("✅ Signal handlers registered for: SIGINT, SIGTERM, SIGQUIT, SIGHUP, SIGUSR1, SIGUSR2")

def run_simple_test():
    """Run a simple test that takes some time."""
    print("🧪 Running simple test...")
    print("   ⏰ You have 10 seconds to press the CANCEL button in Cursor!")
    print("   ⏰ Press CANCEL now to test signal reception!")
    
    for i in range(10):
        print(f"   Test step {i+1}/10... (Press CANCEL now if you haven't already!)")
        time.sleep(1)
        
        # Check if we've received any signals
        with signal_lock:
            if signals_received:
                print(f"   → {len(signals_received)} signals received so far")
    
    print("✅ Test completed successfully!")

def main():
    """Main function."""
    print("🚀 Starting signal reception test...")
    print(f"   PID: {os.getpid()}")
    print(f"   Python: {sys.version}")
    print(f"   Working directory: {os.getcwd()}")
    
    # Register signal handlers
    register_signal_handlers()
    
    # Run the test
    try:
        run_simple_test()
    except KeyboardInterrupt:
        print("\n⚠️  KeyboardInterrupt caught (this is expected)")
    except Exception as e:
        print(f"\n❌ Exception caught: {e}")
    finally:
        # Report final results
        print("\n📊 FINAL RESULTS:")
        print(f"   Total signals received: {len(signals_received)}")
        for i, (signum, timestamp) in enumerate(signals_received):
            signal_name = signal.Signals(signum).name if hasattr(signal.Signals, signum) else f"UNKNOWN({signum})"
            print(f"   {i+1}. {signal_name} at {timestamp}")
        
        if not signals_received:
            print("   → NO SIGNALS RECEIVED - Cursor may not be sending signals properly!")
        else:
            print("   → Signals were received successfully!")

if __name__ == "__main__":
    main()
