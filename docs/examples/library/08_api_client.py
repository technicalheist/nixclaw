"""
Example 08: REST API Client — Submit tasks and poll status via HTTP.

First start the API server:
    nixclaw --serve --port 8000

Then run this script to interact with it.
"""
import time
import requests

BASE_URL = "http://localhost:8000/api/v1"


def submit_task(description: str, priority: str = "normal") -> str:
    """Submit a task and return the task_id."""
    response = requests.post(
        f"{BASE_URL}/tasks",
        json={
            "task": description,
            "priority": priority,
        },
    )
    response.raise_for_status()
    data = response.json()
    print(f"Task submitted: {data['task_id']} (status: {data['status']})")
    return data["task_id"]


def get_status(task_id: str) -> dict:
    """Poll task status."""
    response = requests.get(f"{BASE_URL}/tasks/{task_id}")
    response.raise_for_status()
    return response.json()


def wait_for_completion(task_id: str, poll_interval: int = 5, timeout: int = 300) -> dict:
    """Poll until the task completes or times out."""
    start = time.time()
    while time.time() - start < timeout:
        status = get_status(task_id)
        print(f"  Status: {status['status']}")

        if status["status"] in ("completed", "failed"):
            return status

        time.sleep(poll_interval)

    return {"status": "timeout"}


def list_all_tasks() -> list:
    """List all tasks in the queue."""
    response = requests.get(f"{BASE_URL}/tasks")
    response.raise_for_status()
    return response.json()


def cancel_task(task_id: str) -> dict:
    """Cancel a running task."""
    response = requests.post(f"{BASE_URL}/tasks/{task_id}/cancel")
    return response.json()


def health_check() -> dict:
    """Check system health."""
    response = requests.get(f"{BASE_URL}/health")
    response.raise_for_status()
    return response.json()


def main():
    # Check health first
    print("=== Health Check ===")
    health = health_check()
    print(f"Status: {health['status']}")
    print(f"Uptime: {health['uptime_seconds']}s")
    print()

    # Submit a task
    print("=== Submit Task ===")
    task_id = submit_task("List all files in the current directory")
    print()

    # Poll for completion
    print("=== Waiting for completion ===")
    result = wait_for_completion(task_id, poll_interval=3)
    print()

    if result["status"] == "completed":
        print("=== Result ===")
        print(result.get("result", "(no result)"))
    elif result["status"] == "failed":
        print(f"=== Failed ===\n{result.get('error')}")

    # List all tasks
    print("\n=== All Tasks ===")
    for task in list_all_tasks():
        print(f"  {task['id']}: {task['title']} [{task['status']}]")


if __name__ == "__main__":
    main()
