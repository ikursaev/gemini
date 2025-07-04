#!/usr/bin/env python3
"""Simple API test to debug the upload issue."""

import json
from pathlib import Path

import requests


def test_upload():
    # Create a simple text file
    test_file = Path("/tmp/test.txt")
    test_file.write_text("This is a test document for upload testing.")

    url = "http://localhost:8000/uploadfile/"

    try:
        with open(test_file, "rb") as f:
            files = {"file": ("test.txt", f, "text/plain")}
            response = requests.post(url, files=files)

        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")

        if response.status_code == 200:
            data = response.json()
            print(f"Success! Task ID: {data.get('task_id')}")
        else:
            print("Failed!")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print("Could not parse error response as JSON")

    except Exception as e:
        print(f"Exception occurred: {e}")

    finally:
        test_file.unlink(missing_ok=True)


def test_tasks_api():
    url = "http://localhost:8000/api/tasks"
    response = requests.get(url)
    print(f"\nTasks API Status: {response.status_code}")
    print(f"Tasks Response: {response.text}")


if __name__ == "__main__":
    test_upload()
    test_tasks_api()
