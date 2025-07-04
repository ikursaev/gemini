import base64
from pathlib import Path

import requests

# Create a test PNG
png_data = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
)
test_file = Path("/tmp/quick_test.png")
test_file.write_bytes(png_data)

# Upload the file
with open(test_file, "rb") as f:
    files = {"file": ("quick_test.png", f, "image/png")}
    response = requests.post("http://localhost:8000/uploadfile/", files=files)

print("Upload response:", response.status_code)
if response.status_code == 200:
    data = response.json()
    print("Task ID:", data.get("task_id"))
    print("Status:", data.get("status"))
else:
    print("Error:", response.text)
