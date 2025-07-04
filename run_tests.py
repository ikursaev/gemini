#!/usr/bin/env python3
"""
Comprehensive test runner for the Document Extractor application.

This script runs all test suites and generates reports.
Usage:
    python run_tests.py [options]

Options:
    --fast      Run only fast tests (skip performance tests)
    --performance  Run only performance tests
    --coverage  Generate coverage report
    --html      Generate HTML test report
    --verbose   Verbose output
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description=""):
    """Run a shell command and return the result."""
    print(f"\n{'=' * 60}")
    print(f"Running: {description or cmd}")
    print(f"{'=' * 60}")

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)

    return result.returncode == 0


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run Document Extractor tests")
    parser.add_argument("--fast", action="store_true", help="Run only fast tests")
    parser.add_argument(
        "--performance", action="store_true", help="Run only performance tests"
    )
    parser.add_argument(
        "--coverage", action="store_true", help="Generate coverage report"
    )
    parser.add_argument("--html", action="store_true", help="Generate HTML report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Ensure we're in the project root
    project_root = Path(__file__).parent

    # Base pytest command
    pytest_cmd = ["python", "-m", "pytest"]

    if args.verbose:
        pytest_cmd.append("-v")

    # Test selection
    if args.fast:
        pytest_cmd.extend(["-m", "not performance and not slow"])
        test_description = "Fast Tests Only"
    elif args.performance:
        pytest_cmd.extend(["-m", "performance"])
        test_description = "Performance Tests Only"
    else:
        test_description = "All Tests"

    # Coverage options
    if args.coverage:
        pytest_cmd.extend(
            [
                "--cov=app",
                "--cov-report=term-missing",
                "--cov-report=xml",
            ]
        )
        if args.html:
            pytest_cmd.append("--cov-report=html")

    # HTML report
    if args.html:
        pytest_cmd.extend(["--html=tests/reports/report.html", "--self-contained-html"])

    # Add test directories
    pytest_cmd.append("tests/")

    # Run the tests
    cmd_str = " ".join(pytest_cmd)
    success = run_command(cmd_str, f"{test_description} - pytest")

    if not success:
        print("\n❌ Tests failed!")
        return 1

    # Run additional checks
    print("\n" + "=" * 60)
    print("Running additional code quality checks...")
    print("=" * 60)

    # Run ruff for linting
    ruff_success = run_command("ruff check app/ tests/", "Ruff Linting")

    # Run type checking if mypy is available
    mypy_success = True
    try:
        result = subprocess.run(["mypy", "--version"], capture_output=True)
        if result.returncode == 0:
            mypy_success = run_command("mypy app/", "Type Checking (mypy)")
    except FileNotFoundError:
        print("⚠️  mypy not found, skipping type checking")

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    if success and ruff_success and mypy_success:
        print("✅ All tests and checks passed!")
        return 0
    else:
        print("❌ Some tests or checks failed:")
        if not success:
            print("  - pytest tests failed")
        if not ruff_success:
            print("  - ruff linting failed")
        if not mypy_success:
            print("  - mypy type checking failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
