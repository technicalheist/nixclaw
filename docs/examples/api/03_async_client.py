"""
Async Python client using httpx for the NixClaw REST API.

Start the server first: nixclaw --serve
"""
import asyncio
import httpx

BASE_URL = "http://localhost:8000/api/v1"


async def main():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as client:

        # Health check
        resp = await client.get("/health")
        print(f"Health: {resp.json()['status']}")

        # Submit multiple tasks concurrently
        tasks_to_submit = [
            "List files in /tmp",
            "Show current date and time",
            "Check Python version",
        ]

        print(f"\nSubmitting {len(tasks_to_submit)} tasks concurrently...")

        async def submit(description: str) -> str:
            resp = await client.post("/tasks", json={"task": description})
            return resp.json()["task_id"]

        task_ids = await asyncio.gather(*[submit(t) for t in tasks_to_submit])

        for desc, tid in zip(tasks_to_submit, task_ids):
            print(f"  {tid}: {desc}")

        # Poll all tasks
        print("\nWaiting for completion...")
        for _ in range(20):
            await asyncio.sleep(3)

            all_done = True
            for tid in task_ids:
                resp = await client.get(f"/tasks/{tid}")
                info = resp.json()
                status = info["status"]
                print(f"  {tid}: {status}")
                if status not in ("completed", "failed"):
                    all_done = False

            if all_done:
                break

        # Print results
        print("\n=== Results ===")
        for tid in task_ids:
            resp = await client.get(f"/tasks/{tid}")
            info = resp.json()
            print(f"\n[{tid}] {info['status']}")
            if info.get("result"):
                print(info["result"][:200])
            if info.get("error"):
                print(f"Error: {info['error']}")


if __name__ == "__main__":
    asyncio.run(main())
