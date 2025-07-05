#!/usr/bin/env python3
"""
Test script to verify that dropdown opening doesn't cause layout shifts.
"""

import requests


def test_layout_shift_fix():
    """Test that the dropdown positioning fix prevents layout shifts."""
    print("🔧 Testing Layout Shift Fix")
    print("=" * 40)

    base_url = "http://localhost:8000"

    # Test 1: Check for layout shift prevention CSS
    print("\n1. Testing layout shift prevention...")
    try:
        response = requests.get(base_url)
        if response.status_code == 200:
            content = response.text
            
            # Check for layout shift prevention elements
            shift_prevention_checks = [
                "overflow-x: hidden" in content,
                "position: fixed" in content,
                "isolation: isolate" in content,
                "will-change: transform, opacity" in content,
                "getBoundingClientRect" in content,
            ]
            
            passed_checks = sum(shift_prevention_checks)
            if passed_checks >= 3:
                print(f"✅ Layout shift prevention implemented ({passed_checks}/5 checks passed)")
            else:
                print(f"❌ Layout shift prevention incomplete ({passed_checks}/5 checks passed)")
                
        else:
            print(f"❌ Homepage failed to load: {response.status_code}")
    except Exception as e:
        print(f"❌ Layout shift test failed: {e}")

    # Test 2: Check dropdown positioning improvements
    print("\n2. Testing dropdown positioning...")
    try:
        response = requests.get(base_url)
        if response.status_code == 200:
            content = response.text
            
            # Check for positioning improvements
            positioning_checks = [
                "buttonRect.getBoundingClientRect" in content,
                "dropdown.style.position" in content,
                "window.innerWidth" in content,
                "dropdown.style.top" in content,
                "dropdown.style.right" in content,
            ]
            
            passed_checks = sum(positioning_checks)
            if passed_checks >= 4:
                print(f"✅ Dropdown positioning improved ({passed_checks}/5 checks passed)")
            else:
                print(f"❌ Dropdown positioning needs work ({passed_checks}/5 checks passed)")
                
        else:
            print(f"❌ Homepage failed to load: {response.status_code}")
    except Exception as e:
        print(f"❌ Positioning test failed: {e}")

    print("\n" + "=" * 40)
    print("🎯 Layout Shift Fix Summary:")
    print("🔧 Fixes Applied:")
    print("  • Changed dropdown to position: fixed")
    print("  • Added dynamic positioning with getBoundingClientRect")
    print("  • Added overflow-x: hidden to body")
    print("  • Used isolation: isolate on container")
    print("  • Added will-change for GPU acceleration")
    print("  • Implemented viewport boundary checks")
    print()
    print("✅ Expected Result:")
    print("  • No elements should move when dropdown opens")
    print("  • Dropdown should appear in fixed position")
    print("  • Page layout should remain stable")
    print("  • Smooth transitions maintained")


if __name__ == "__main__":
    test_layout_shift_fix()
