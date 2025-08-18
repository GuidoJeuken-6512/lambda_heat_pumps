#!/usr/bin/env python3
"""Test runner for Modbus API compatibility tests."""

import sys
import subprocess
import os


def run_tests():
    """Run the Modbus compatibility tests."""
    print("🧪 Running Modbus API Compatibility Tests")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("tests/test_modbus_compatibility.py"):
        print("❌ Error: test file not found. Please run from the project root.")
        return False
    
    # Run pytest with verbose output
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_modbus_compatibility.py",
        "-v",
        "--tb=short"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print("📋 Test Results:")
        print(result.stdout)
        
        if result.stderr:
            print("⚠️  Warnings/Errors:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ All tests passed!")
            return True
        else:
            print("❌ Some tests failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def run_specific_test(test_name):
    """Run a specific test by name."""
    print(f"🧪 Running specific test: {test_name}")
    print("=" * 50)
    
    cmd = [
        sys.executable, "-m", "pytest",
        f"tests/test_modbus_compatibility.py::{test_name}",
        "-v",
        "--tb=short"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print("📋 Test Results:")
        print(result.stdout)
        
        if result.stderr:
            print("⚠️  Warnings/Errors:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ Test passed!")
            return True
        else:
            print("❌ Test failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False


def list_tests():
    """List all available tests."""
    print("📋 Available Tests:")
    print("=" * 50)
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_modbus_compatibility.py",
        "--collect-only",
        "-q"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"❌ Error listing tests: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "list":
            list_tests()
        elif command == "test":
            if len(sys.argv) > 2:
                test_name = sys.argv[2]
                run_specific_test(test_name)
            else:
                print(
                    "❌ Please specify a test name: "
                    "python run_modbus_tests.py test <test_name>"
                )
        else:
            print("❌ Unknown command. Use: list, test, or no arguments for all tests")
    else:
        run_tests() 