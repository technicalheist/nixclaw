"""
Python client for the NixClaw REST API.

Start the server first: nixclaw --serve
"""
import time
import requests

BASE_URL = "http://localhost:8000/api/v1"


class NixClawClient:
    """Simple HTTP client for the NixClaw API."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()

    def health(self) -> dict:
        """Check system health."""
        return self.session.get(f"{self.base_url}/health").json()

    def submit(
        self,
        task: str,
        priority: str = "normal",
        agent_profiles: list[str] | None = None,
        callback_url: str | None = None,
    ) -> str:
        """Submit a task. Returns task_id."""
        payload = {"task": task, "priority": priority}
        if agent_profiles:
            payload["agent_profiles"] = agent_profiles
        if callback_url:
            payload["callback_url"] = callback_url

        resp = self.session.post(f"{self.base_url}/tasks", json=payload)
        resp.raise_for_status()
        return resp.json()["task_id"]

    def status(self, task_id: str) -> dict:
        """Get task status."""
        resp = self.session.get(f"{self.base_url}/tasks/{task_id}")
        resp.raise_for_status()
        return resp.json()

    def list_tasks(self) -> list[dict]:
        """List all tasks."""
        return self.session.get(f"{self.base_url}/tasks").json()

    def cancel(self, task_id: str) -> dict:
        """Cancel a running task."""
        resp = self.session.post(f"{self.base_url}/tasks/{task_id}/cancel")
        return resp.json()

    def agents(self) -> dict:
        """Get agent pool status."""
        return self.session.get(f"{self.base_url}/agents/status").json()

    def wait(self, task_id: str, poll_interval: int = 3, timeout: int = 300) -> dict:
        """Poll until task completes or times out."""
        start = time.time()
        while time.time() - start < timeout:
            info = self.status(task_id)
            if info["status"] in ("completed", "failed"):
                return info
            time.sleep(poll_interval)
        return {"status": "timeout"}


def main():
    client = NixClawClient()

    # Health check
    print("Health:", client.health()["status"])

    # Submit a task
    task_id = client.submit("List Python files in the current directory")
    print(f"Submitted: {task_id}")

    # Wait for result
    result = client.wait(task_id)
    print(f"Status: {result['status']}")
    if result.get("result"):
        print(f"Result: {result['result'][:300]}")

    # List all
    print(f"\nAll tasks: {len(client.list_tasks())} total")
    print(f"Agents: {client.agents()}")


if __name__ == "__main__":
    main()
