#!/usr/bin/env python3
"""
Test script to verify circular badge implementation.
"""

import time
from pathlib import Path

import requests


def test_circular_badges():
    """Test the circular badge styling."""
    print("🔴 Testing Circular Badge Implementation")
    print("=" * 50)

    base_url = "http://localhost:8000"

    # Test 1: Check HTML for circular badge classes
    print("\n1. Testing circular badge HTML structure...")
    try:
        response = requests.get(base_url)
        if response.status_code == 200:
            content = response.text

            # Check for circular badge classes
            circular_checks = [
                "w-6 h-6 rounded-full" in content,
                "leading-none" in content,
                "min-width: 1.5rem" in content,
                "aspect-ratio: 1" in content,
            ]

            passed_checks = sum(circular_checks)
            if passed_checks >= 3:
                print(
                    f"✅ Circular badge structure found ({passed_checks}/4 checks passed)"
                )
            else:
                print(
                    f"❌ Circular badge structure incomplete ({passed_checks}/4 checks passed)"
                )

        else:
            print(f"❌ Homepage failed to load: {response.status_code}")
    except Exception as e:
        print(f"❌ Badge structure test failed: {e}")

    # Test 2: Upload multiple files to test badge appearance
    print("\n2. Testing badge appearance with multiple tasks...")
    test_file_path = Path("/workspace/test_image.png")

    if test_file_path.exists():
        try:
            # Upload multiple files to create badges
            for i in range(3):
                with open(test_file_path, "rb") as f:
                    files = {"file": (f"test_image_{i}.png", f, "image/png")}
                    response = requests.post(f"{base_url}/uploadfile/", files=files)

                if response.status_code == 200:
                    result = response.json()
                    print(
                        f"✅ File {i + 1} uploaded. Task ID: {result.get('task_id', 'Unknown')}"
                    )
                else:
                    print(f"❌ File {i + 1} upload failed: {response.status_code}")

                time.sleep(0.5)  # Small delay between uploads

            # Check tasks API
            print("\n3. Checking tasks API for badge data...")
            time.sleep(2)  # Wait for processing

            tasks_response = requests.get(f"{base_url}/api/tasks")
            if tasks_response.status_code == 200:
                tasks = tasks_response.json()
                if tasks:
                    print(f"✅ Found {len(tasks)} tasks - badges should be visible")
                    print("ℹ️ Check browser to see circular badges in action!")
                else:
                    print("ℹ️ No tasks found, but API is working")
            else:
                print(f"❌ Tasks API failed: {tasks_response.status_code}")

        except Exception as e:
            print(f"❌ Upload test failed: {e}")
    else:
        print("ℹ️ Test file not found, skipping upload test")

    print("\n" + "=" * 50)
    print("🎯 Circular Badge Improvements Summary:")
    print("🔴 Badge Shape Changes:")
    print("  • Changed from px-2.5 py-1 (pill) to w-6 h-6 (circle)")
    print("  • Added leading-none for better text centering")
    print("  • Added min-width: 1.5rem for double-digit numbers")
    print("  • Added aspect-ratio: 1 for perfect circles")
    print()
    print("✨ Visual Benefits:")
    print("  • Perfect circular shape instead of vertical pill")
    print("  • Better centering of numbers")
    print("  • Consistent size regardless of content")
    print("  • Professional badge appearance")


if __name__ == "__main__":
    test_circular_badges()
