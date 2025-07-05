#!/usr/bin/env python3
"""
Test script to validate the improved layout and colorful tasks dropdown.
"""

import time
from pathlib import Path

import requests


def test_layout_improvements():
    """Test the layout and dropdown improvements."""
    print("🎨 Testing Layout & Colorful Dropdown Improvements")
    print("=" * 60)

    base_url = "http://localhost:8000"

    # Test 1: Check responsive layout improvements
    print("\n1. Testing responsive layout...")
    try:
        response = requests.get(base_url)
        if response.status_code == 200:
            content = response.text

            # Check for new layout improvements
            layout_checks = [
                "max-w-lg md:max-w-xl lg:max-w-2xl xl:max-w-3xl 2xl:max-w-4xl"
                in content,
                "padding-left: 10vw" in content,
                "padding-right: 10vw" in content,
            ]

            if any(layout_checks):
                print("✅ Responsive layout improvements found")
            else:
                print("❌ Layout improvements not detected")

        else:
            print(f"❌ Homepage failed to load: {response.status_code}")
    except Exception as e:
        print(f"❌ Layout test failed: {e}")

    # Test 2: Check colorful dropdown styling
    print("\n2. Testing colorful dropdown styling...")
    try:
        response = requests.get(base_url)
        if response.status_code == 200:
            content = response.text

            # Check for colorful dropdown elements
            dropdown_checks = [
                "rainbow-glow" in content,
                "background-size: 300%" in content,
                "linear-gradient(45deg, #3b82f6, #8b5cf6, #ec4899, #10b981, #f59e0b"
                in content,
                "animation: rainbow-glow 4s ease-in-out infinite" in content,
                "filter: blur(12px)" in content,
            ]

            passed_checks = sum(dropdown_checks)
            if passed_checks >= 3:
                print(
                    f"✅ Colorful dropdown styling found ({passed_checks}/5 checks passed)"
                )
            else:
                print(
                    f"❌ Colorful dropdown styling incomplete ({passed_checks}/5 checks passed)"
                )

        else:
            print(f"❌ Homepage failed to load: {response.status_code}")
    except Exception as e:
        print(f"❌ Dropdown styling test failed: {e}")

    # Test 3: Test file upload to see dropdown in action
    print("\n3. Testing dropdown functionality...")
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

                # Wait a moment for task processing
                time.sleep(2)

                # Check tasks API
                tasks_response = requests.get(f"{base_url}/api/tasks")
                if tasks_response.status_code == 200:
                    tasks = tasks_response.json()
                    if tasks:
                        print(
                            "✅ Tasks API working, colorful dropdown should be visible"
                        )
                    else:
                        print("ℹ️ No tasks returned, but API is working")
                else:
                    print(f"❌ Tasks API failed: {tasks_response.status_code}")

            else:
                print(f"❌ File upload failed: {response.status_code}")

        except Exception as e:
            print(f"❌ Upload test failed: {e}")
    else:
        print("ℹ️ Test file not found, skipping upload test")

    print("\n" + "=" * 60)
    print("🎯 Layout & Dropdown Improvements Summary:")
    print("📐 Layout Changes:")
    print("  • Reduced main content width to ~60% of screen")
    print("  • Added responsive padding (10vw, 15vw, 20vw)")
    print("  • Better proportional sizing across devices")
    print("  • Enhanced container max-widths")
    print()
    print("🌈 Colorful Dropdown Features:")
    print("  • Removed black borders")
    print("  • Added animated rainbow glow effect")
    print("  • Enhanced backdrop blur and shadows")
    print("  • Hover effects with increased glow")
    print("  • Better visual prominence on page")
    print("  • Smooth color transitions")


if __name__ == "__main__":
    test_layout_improvements()
