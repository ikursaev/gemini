import time

import requests

task_id = "dc76ab42-df46-4cb4-a35b-97ae6247bdd7"
for i in range(10):
    response = requests.get("http://localhost:8000/api/tasks")
    if response.status_code == 200:
        tasks = response.json()
        our_task = next(
            (task for task in tasks if task.get("task_id") == task_id), None
        )
        if our_task:
            print(f"Attempt {i + 1}: Status = {our_task.get('status')}")
            if our_task.get("status") in ["SUCCESS", "FAILURE"]:
                break
    time.sleep(2)
