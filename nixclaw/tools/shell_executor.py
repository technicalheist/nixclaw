from __future__ import annotations

import asyncio
import os
import re
import resource
import signal
import time
from pathlib import Path

from nixclaw.config import get_settings
from nixclaw.logger import get_logger

logger = get_logger(__name__)

# Dangerous patterns that are always blocked
_DANGEROUS_PATTERNS = [
    r"rm\s+-[^\s]*r[^\s]*f.*\s+/\s*$",  # rm -rf /
    r"rm\s+-[^\s]*f[^\s]*r.*\s+/\s*$",  # rm -fr /
    r":\s*\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:",  # fork bomb
    r"mkfs\.",  # format filesystem
    r"dd\s+.*of=/dev/[sh]d",  # overwrite disk
    r">\s*/dev/[sh]d",  # redirect to disk device
    r"chmod\s+-R\s+777\s+/\s*$",  # chmod 777 /
    r"wget\s+.*\|\s*(ba)?sh",  # pipe wget to shell
    r"curl\s+.*\|\s*(ba)?sh",  # pipe curl to shell
    r"python.*-c\s+.*import\s+os.*system",  # python os.system injection
    r"eval\s*\(",  # eval injection
    r">\s*/etc/passwd",  # overwrite passwd
    r">\s*/etc/shadow",  # overwrite shadow
]
_DANGEROUS_RE = [re.compile(p) for p in _DANGEROUS_PATTERNS]


def _is_command_safe(command: str) -> tuple[bool, str]:
    """Validate command against safety rules. Returns (is_safe, reason)."""
    for pattern in _DANGEROUS_RE:
        if pattern.search(command):
            return False, "Blocked by safety rule: matches dangerous pattern"

    settings = get_settings()
    for blacklisted in settings.command_executor.dangerous_commands_blacklist:
        if blacklisted.strip() and blacklisted.strip() in command:
            return False, f"Blocked: matches blacklisted command '{blacklisted.strip()}'"

    return True, ""


def _make_preexec_fn(memory_limit_mb: int) -> object:
    """Create a preexec function that sets resource limits on the child process."""

    def _preexec() -> None:
        # New process group for clean signal delivery
        os.setsid()

        # Set memory limit (soft and hard) in bytes
        if memory_limit_mb > 0:
            limit_bytes = memory_limit_mb * 1024 * 1024
            try:
                resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
            except (ValueError, OSError):
                pass  # Platform may not support RLIMIT_AS

        # Set CPU time limit (generous: 2x the timeout as a backstop)
        try:
            resource.setrlimit(resource.RLIMIT_CPU, (3600, 3600))
        except (ValueError, OSError):
            pass

        # Limit number of child processes to prevent fork bombs
        # Use a generous limit to avoid breaking normal commands
        try:
            resource.setrlimit(resource.RLIMIT_NPROC, (4096, 4096))
        except (ValueError, OSError):
            pass

    return _preexec


async def execute_shell_command(
    command: str,
    working_dir: str = "",
    timeout: int = 0,
    env_vars: str = "",
) -> str:
    """Execute a shell command with safety checks, timeout, resource limits, and output limits.

    Args:
        command: The shell command to execute.
        working_dir: Working directory (defaults to configured working dir).
        timeout: Timeout in seconds (0 = use default from config).
        env_vars: Comma-separated KEY=VALUE pairs for environment variables.

    Returns:
        Command output with metadata (exit code, duration, stdout, stderr).
    """
    settings = get_settings()

    # Safety check
    is_safe, reason = _is_command_safe(command)
    if not is_safe:
        logger.warning("Command blocked: %s | Reason: %s", command, reason)
        return f"BLOCKED: {reason}\nCommand: {command}"

    # Resolve working directory
    work_dir = working_dir or settings.command_executor.working_dir
    Path(work_dir).mkdir(parents=True, exist_ok=True)

    # Resolve timeout
    cmd_timeout = timeout if timeout > 0 else settings.command_executor.timeout_default

    # Build environment
    env = os.environ.copy()
    if env_vars:
        for pair in env_vars.split(","):
            pair = pair.strip()
            if "=" in pair:
                key, value = pair.split("=", 1)
                env[key.strip()] = value.strip()

    max_output = settings.command_executor.max_output_size
    memory_limit = settings.command_executor.memory_limit_mb
    start_time = time.monotonic()

    logger.info(
        "Executing command: %s (timeout=%ds, mem_limit=%dMB, cwd=%s)",
        command, cmd_timeout, memory_limit, work_dir,
    )

    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=work_dir,
            env=env,
            preexec_fn=_make_preexec_fn(memory_limit),
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(), timeout=cmd_timeout
            )
        except asyncio.TimeoutError:
            # Graceful shutdown: SIGTERM first, then SIGKILL
            logger.warning("Command timed out after %ds, sending SIGTERM: %s", cmd_timeout, command)
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            except ProcessLookupError:
                pass

            try:
                await asyncio.wait_for(process.wait(), timeout=15)
            except asyncio.TimeoutError:
                logger.warning("SIGTERM failed, sending SIGKILL: %s", command)
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass
                await process.wait()

            duration = time.monotonic() - start_time
            return (
                f"TIMEOUT after {duration:.1f}s (limit: {cmd_timeout}s)\n"
                f"Command: {command}\n"
                f"The command was terminated. Partial output may be unavailable."
            )

        duration = time.monotonic() - start_time
        exit_code = process.returncode

        # Decode output with truncation
        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")

        truncated = False
        if len(stdout) > max_output:
            stdout = stdout[:max_output] + "\n... [stdout truncated]"
            truncated = True
        if len(stderr) > max_output:
            stderr = stderr[:max_output] + "\n... [stderr truncated]"
            truncated = True

        # Build result
        parts = [
            f"Exit Code: {exit_code}",
            f"Duration: {duration:.2f}s",
        ]
        if truncated:
            parts.append("Output: TRUNCATED")

        if stdout.strip():
            parts.append(f"\n--- STDOUT ---\n{stdout.strip()}")
        if stderr.strip():
            parts.append(f"\n--- STDERR ---\n{stderr.strip()}")
        if not stdout.strip() and not stderr.strip():
            parts.append("\n(no output)")

        result = "\n".join(parts)
        logger.info("Command completed: exit=%d duration=%.2fs", exit_code, duration)
        return result

    except FileNotFoundError:
        return f"Error: Working directory not found: {work_dir}"
    except PermissionError:
        return f"Error: Permission denied executing command"
    except Exception as e:
        logger.exception("Unexpected error executing command: %s", command)
        return f"Error: {type(e).__name__}: {e}"
