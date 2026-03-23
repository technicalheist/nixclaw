"""
Example 12: Security Utilities — Secret masking, path sanitization, input validation.

These utilities help prevent accidental secret leaks in logs
and protect against common injection attacks.
"""
from nixclaw.core.security import mask_secrets, sanitize_path, validate_task_input


def example_mask_secrets():
    """Mask sensitive values in log output."""
    print("=== Secret Masking ===")

    logs = [
        "Connecting with api_key=sk-abc123def456ghi789jkl012mno345pqr",
        "Bot token: 123456789:ABCdefGHI-jklMNOpqrSTUvwxyz1234567",
        "password=my_super_secret_password123",
        "Using PyPI token pypi-AgEIcHlwaS5vcmcCJGI0YjY0YWE2LTM3YT",
        "GitHub PAT: ghp_1234567890abcdefghijklmnopqrstuvwxyz",
        "Normal log: Processing 42 items in batch 7",  # Should not be masked
    ]

    for log in logs:
        masked = mask_secrets(log)
        print(f"  Original: {log}")
        print(f"  Masked:   {masked}")
        print()


def example_sanitize_path():
    """Sanitize file paths to prevent traversal attacks."""
    print("=== Path Sanitization ===")

    paths = [
        "/home/user/documents/file.txt",       # Normal — unchanged
        "../../etc/passwd",                      # Traversal — blocked
        "/tmp/file\x00.txt",                    # Null byte — removed
        "/home/user/../root/.ssh/id_rsa",       # Traversal — blocked
        "logs/../../etc/shadow",                # Traversal — blocked
    ]

    for path in paths:
        clean = sanitize_path(path)
        changed = " (SANITIZED)" if clean != path else ""
        print(f"  Input:  {repr(path)}")
        print(f"  Output: {clean}{changed}")
        print()


def example_validate_input():
    """Validate task input before processing."""
    print("=== Input Validation ===")

    inputs = [
        "Analyze the project structure",         # Valid
        "",                                       # Empty
        "   ",                                    # Whitespace only
        "x" * 60_000,                            # Too long
        "Fix the bug in auth.py",                # Valid
    ]

    for task_input in inputs:
        display = task_input[:50] + "..." if len(task_input) > 50 else task_input
        valid, reason = validate_task_input(task_input)
        status = "VALID" if valid else f"INVALID ({reason})"
        print(f"  {repr(display):55s} -> {status}")


if __name__ == "__main__":
    example_mask_secrets()
    example_sanitize_path()
    example_validate_input()
