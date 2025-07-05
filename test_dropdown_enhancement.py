#!/usr/bin/env python3
"""
Quick test script to verify the enhanced tasks dropdown functionality.
"""

import time
from pathlib import Path

import requests


def test_enhanced_dropdown():
    """Test the enhanced tasks dropdown functionality."""
    print("🚀 Testing Enhanced Tasks Dropdown")
    print("=" * 50)

    base_url = "http://localhost:8000"

    # Test 1: Check if homepage loads with new dropdown structure
    print("\n1. Testing homepage loading...")
    try:
        response = requests.get(base_url)
        if response.status_code == 200:
            content = response.text
            # Check for new dropdown elements
            checks = [
                "dropdown-header" in content,
                "task-item" in content,
                "download-button" in content,
                "status-indicator" in content,
                "Recent Tasks" in content,
            ]

            if all(checks):
                print("✅ Enhanced dropdown structure found")
            else:
                print("❌ Some enhanced elements missing")

        else:
            print(f"❌ Homepage failed to load: {response.status_code}")
    except Exception as e:
        print(f"❌ Homepage test failed: {e}")

    # Test 2: Test file upload and task creation
    print("\n2. Testing file upload and task creation...")
    test_file_path = Path("/workspace/test_image.png")

    if test_file_path.exists():
        try:
            with open(test_file_path, "rb") as f:
                files = {"file": ("test_image.png", f, "image/png")}
                response = requests.post(f"{base_url}/uploadfile/", files=files)

            if response.status_code == 200:
                result = response.json()
                task_id = result.get("task_id")
                print(f"✅ File uploaded successfully. Task ID: {task_id}")

                # Test 3: Check tasks API
                print("\n3. Testing tasks API...")
                time.sleep(1)  # Wait a moment

                tasks_response = requests.get(f"{base_url}/api/tasks")
                if tasks_response.status_code == 200:
                    tasks = tasks_response.json()
                    print(f"✅ Tasks API working. Found {len(tasks)} tasks")

                    if tasks:
                        task = tasks[0]
                        required_fields = ["task_id", "status", "filename"]
                        if all(field in task for field in required_fields):
                            print("✅ Task structure correct")
                        else:
                            print("❌ Task structure incomplete")
                else:
                    print(f"❌ Tasks API failed: {tasks_response.status_code}")

            else:
                print(f"❌ File upload failed: {response.status_code}")

        except Exception as e:
            print(f"❌ Upload test failed: {e}")
    else:
        print("❌ Test file not found")

    print("\n" + "=" * 50)
    print("🎨 Enhanced Tasks Dropdown Features:")
    print("• Beautiful gradient header with icon")
    print("• Hover effects on task items")
    print("• Pill-shaped download buttons")
    print("• Animated status indicators")
    print("• Enhanced empty state")
    print("• Better typography and spacing")
    print("• Custom scrollbar styling")
    print("• Improved dark mode support")


if __name__ == "__main__":
    test_enhanced_dropdown()
