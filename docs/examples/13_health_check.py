"""
Example 13: Health Check — Monitor all system components.

The health check inspects LLM config, database, Telegram bots,
and agent status. Useful for monitoring and debugging.
"""
import asyncio
import json

from nixclaw.core.health import check_health


async def main():
    print("=== NixClaw Health Check ===\n")

    health = await check_health()

    print(f"Overall Status: {health['status']}")
    print(f"Uptime: {health['uptime_seconds']}s\n")

    print("Component Checks:")
    for component, status in health["checks"].items():
        if isinstance(status, dict):
            state = status.get("status", "unknown")
            icon = "OK" if state in ("ok", "configured") else "!!"
            print(f"  [{icon}] {component}: {state}")

            # Print extra details
            for key, value in status.items():
                if key != "status":
                    print(f"       {key}: {value}")
        else:
            print(f"  [??] {component}: {status}")

    # Full JSON output
    print(f"\nFull JSON:\n{json.dumps(health, indent=2, default=str)}")


if __name__ == "__main__":
    asyncio.run(main())
