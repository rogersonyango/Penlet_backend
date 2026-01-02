#!/usr/bin/env python3
"""
Test runner script for Penlet API.
This script runs all tests and provides a summary.
"""
import subprocess
import sys

def run_tests():
    """Run pytest with coverage report."""
    print("=" * 60)
    print("Running Penlet API Tests")
    print("=" * 60)
    
    # Run pytest with options
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",  # Verbose output
        "--tb=short",  # Short traceback
        "--color=yes",  # Colored output
        "-q",  # Quieter output
    ]
    
    try:
        result = subprocess.run(cmd, cwd="/home/nakato/Penlet_backend")
        return result.returncode
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

def run_specific_tests(test_file):
    """Run specific test file."""
    print(f"Running tests from: {test_file}")
    
    cmd = [
        sys.executable, "-m", "pytest",
        f"tests/{test_file}",
        "-v",
        "--tb=short",
        "--color=yes"
    ]
    
    try:
        result = subprocess.run(cmd, cwd="/home/nakato/Penlet_backend")
        return result.returncode
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

def run_tests_with_coverage():
    """Run tests with coverage report."""
    print("=" * 60)
    print("Running Tests with Coverage")
    print("=" * 60)
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "--cov=app",
        "--cov-report=term-missing",
        "--cov-report=html",
        "-v",
        "--tb=short"
    ]
    
    try:
        result = subprocess.run(cmd, cwd="/home/nakato/Penlet_backend")
        return result.returncode
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--coverage":
            sys.exit(run_tests_with_coverage())
        else:
            sys.exit(run_specific_tests(sys.argv[1]))
    else:
        sys.exit(run_tests())

