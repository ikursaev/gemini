#!/usr/bin/env python3
"""
Simple test script to identify hanging issues.
"""

from pathlib import Path

import requests

BASE_URL = "http://localhost:8000"


def test_basic_health():
    print("Testing basic health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Health check: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False


def test_frontend():
    print("Testing frontend...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"Frontend: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Frontend test failed: {e}")
        return False


def test_tasks_api():
    print("Testing tasks API...")
    try:
        response = requests.get(f"{BASE_URL}/api/tasks", timeout=5)
        print(f"Tasks API: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Tasks API test failed: {e}")
        return False


def test_file_validation():
    print("Testing file validation...")
    try:
        # Create test file
        test_file = Path("/tmp/simple_test.txt")
        test_file.write_text("test content")

        with open(test_file, "rb") as f:
            files = {"file": ("simple_test.txt", f, "text/plain")}
            print("Sending POST request...")
            response = requests.post(f"{BASE_URL}/uploadfile/", files=files, timeout=10)
            print(f"File validation: {response.status_code}")

        # Cleanup
        test_file.unlink(missing_ok=True)
        return response.status_code == 400
    except Exception as e:
        print(f"File validation test failed: {e}")
        return False


if __name__ == "__main__":
    print("Running simple tests...")

    print("1. Health check")
    if not test_basic_health():
        print("Health check failed, stopping")
        exit(1)

    print("2. Frontend test")
    if not test_frontend():
        print("Frontend test failed, stopping")
        exit(1)

    print("3. Tasks API test")
    if not test_tasks_api():
        print("Tasks API test failed, stopping")
        exit(1)

    print("4. File validation test")
    if not test_file_validation():
        print("File validation test failed, stopping")
        exit(1)

    print("All tests passed!")
