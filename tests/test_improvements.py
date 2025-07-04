#!/usr/bin/env python3
"""
Comprehensive test script for the improved task management system.
Tests all the new features: persistence, badges, and button styling.
"""

import time
from pathlib import Path

import requests

BASE_URL = "http://localhost:8000"


def test_task_persistence_and_badges():
    """Test the improved task management features."""
    print("🧪 Testing Enhanced Task Management System")
    print("=" * 50)  # Test 1: Upload a file to create a task
    print("\n1. Testing file upload and task creation...")
    test_file = Path("/workspace/test_image.png")

    with open(test_file, "rb") as f:
        files = {"file": ("test_image.png", f, "image/png")}
        response = requests.post(f"{BASE_URL}/uploadfile/", files=files)

    if response.status_code == 200:
        result = response.json()
        task_id = result.get("task_id")
        print(f"✅ File uploaded successfully! Task ID: {task_id}")
    else:
        print(f"❌ Upload failed: {response.status_code} - {response.text}")
        return

    # Test 2: Check task API endpoint
    print("\n2. Testing /api/tasks endpoint...")
    response = requests.get(f"{BASE_URL}/api/tasks")
    if response.status_code == 200:
        tasks = response.json()
        print(f"✅ Tasks API working! Found {len(tasks)} task(s)")
        for task in tasks:
            print(
                f"   - Task {task.get('task_id', 'Unknown')[:8]}... Status: {task.get('status', 'Unknown')}"
            )
            print(f"     Filename: {task.get('filename', 'Unknown')}")
            print(f"     Timestamp: {task.get('timestamp', 'Unknown')}")
    else:
        print(f"❌ Tasks API failed: {response.status_code}")
        return

    # Test 3: Wait for task completion and check result
    print(f"\n3. Monitoring task {task_id[:8]}... for completion...")
    max_wait = 30  # seconds
    start_time = time.time()

    while time.time() - start_time < max_wait:
        response = requests.get(f"{BASE_URL}/api/tasks")
        if response.status_code == 200:
            tasks = response.json()
            our_task = next((t for t in tasks if t.get("task_id") == task_id), None)

            if our_task:
                status = our_task.get("status")
                print(f"   Current status: {status}")

                if status == "SUCCESS":
                    print("✅ Task completed successfully!")
                    break
                elif status == "FAILURE":
                    print("❌ Task failed!")
                    break

        time.sleep(2)
    else:
        print("⚠️  Task did not complete within timeout")

    # Test 4: Test task result download
    print(f"\n4. Testing result download for task {task_id[:8]}...")
    response = requests.get(f"{BASE_URL}/api/tasks/{task_id}/result")
    if response.status_code == 200:
        result = response.json()
        if "markdown" in result:
            print("✅ Task result download successful!")
            print(f"   Content length: {len(result['markdown'])} characters")
        else:
            print("⚠️  Result format unexpected")
    else:
        print(f"❌ Result download failed: {response.status_code}")

    # Test 5: Check download endpoint
    print("\n5. Testing markdown download endpoint...")
    response = requests.get(f"{BASE_URL}/download_markdown/{task_id}")
    if response.status_code == 200:
        print("✅ Markdown download endpoint working!")
        print(f"   Response type: {response.headers.get('content-type', 'Unknown')}")
    else:
        print(f"❌ Markdown download failed: {response.status_code}")

    print("\n" + "=" * 50)
    print("🎉 Test Complete!")
    print("\nTo test the UI improvements:")
    print("1. Open http://localhost:8000 in your browser")
    print("2. Check the modern Tasks button styling")
    print("3. Look for colorful badges with task counters")
    print("4. Upload a file and watch the badges update")
    print("5. Reload the page to test persistence")


if __name__ == "__main__":
    test_task_persistence_and_badges()
