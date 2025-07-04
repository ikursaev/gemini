#!/usr/bin/env python3
"""
Simple test runner that validates the test suite structure.
"""

import subprocess
import sys
from pathlib import Path


def check_test_file_syntax():
    """Check that all test files have valid Python syntax."""
    test_files = [
        "tests/test_app.py",
        "tests/test_advanced.py",
        "tests/test_performance.py",
        "tests/test_edge_cases.py",
        "tests/test_integration.py",
        "tests/conftest.py",
    ]

    print("🔍 Checking test file syntax...")

    for test_file in test_files:
        if Path(test_file).exists():
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", test_file],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                print(f"✅ {test_file} - syntax OK")
            else:
                print(f"❌ {test_file} - syntax error:")
                print(result.stderr)
                return False
        else:
            print(f"⚠️  {test_file} - file not found")

    return True


def validate_test_structure():
    """Validate the test suite structure."""
    print("\n📁 Validating test structure...")

    expected_files = [
        "tests/__init__.py",
        "tests/test_app.py",
        "tests/conftest.py",
        "tests/README.md",
        "run_tests.py",
    ]

    for file_path in expected_files:
        if Path(file_path).exists():
            print(f"✅ {file_path} - exists")
        else:
            print(f"❌ {file_path} - missing")
            if file_path == "tests/__init__.py":
                # Create missing __init__.py
                Path("tests/__init__.py").touch()
                print(f"   Created {file_path}")


def check_dependencies():
    """Check that required test dependencies are available."""
    print("\n📦 Checking test dependencies...")

    dependencies = ["pytest", "pytest_asyncio", "pytest_cov"]

    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep} - available")
        except ImportError:
            print(f"❌ {dep} - missing")
            print(f"   Install with: uv add --dev {dep.replace('_', '-')}")


def run_basic_validation():
    """Run basic validation without requiring imports."""
    print("🧪 Document Extractor Test Suite Validation")
    print("=" * 50)

    # Check syntax
    syntax_ok = check_test_file_syntax()

    # Validate structure
    validate_test_structure()

    # Check dependencies
    check_dependencies()

    print("\n" + "=" * 50)
    if syntax_ok:
        print("✅ Test suite validation completed successfully!")
        print("\n📋 Test Suite Overview:")
        print("   • test_app.py        - Core functionality tests")
        print("   • test_advanced.py   - Advanced scenarios & edge cases")
        print("   • test_performance.py - Performance & load testing")
        print("   • test_edge_cases.py - Error handling & edge cases")
        print("   • test_integration.py - End-to-end workflow tests")
        print("   • conftest.py        - Test fixtures & configuration")
        print("\n🚀 To run tests:")
        print("   python run_tests.py")
        print("   pytest tests/ -v")
        print("   pytest tests/test_app.py -v")
        return 0
    else:
        print("❌ Test suite validation failed!")
        return 1


if __name__ == "__main__":
    sys.exit(run_basic_validation())
