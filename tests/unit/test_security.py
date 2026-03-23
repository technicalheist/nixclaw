"""Unit tests for security utilities."""
from nixclaw.core.security import mask_secrets, sanitize_path, validate_task_input


def test_mask_openai_key():
    text = "Using key sk-abcdefghij1234567890abcdefghij"
    masked = mask_secrets(text)
    assert "sk-abcde" in masked
    assert "abcdefghij1234567890abcdefghij" not in masked
    assert "***" in masked


def test_mask_telegram_token():
    text = "Bot token is 123456789:ABCdefGHI-jklMNOpqrSTUvwxyz1234567"
    masked = mask_secrets(text)
    assert "***" in masked


def test_mask_password():
    text = "password=my_secret_pass123"
    masked = mask_secrets(text)
    assert "my_secret_pass123" not in masked


def test_mask_api_key():
    text = "api_key=super_secret_key_value"
    masked = mask_secrets(text)
    assert "super_secret_key_value" not in masked


def test_no_false_positive():
    text = "This is a normal log message with no secrets"
    assert mask_secrets(text) == text


def test_sanitize_path_traversal():
    assert ".." not in sanitize_path("../../etc/passwd")
    assert sanitize_path("/home/user/../root") == "/home/user/root"


def test_sanitize_null_bytes():
    assert "\x00" not in sanitize_path("/tmp/file\x00.txt")


def test_validate_task_empty():
    valid, reason = validate_task_input("")
    assert valid is False

    valid, reason = validate_task_input("   ")
    assert valid is False


def test_validate_task_too_long():
    valid, reason = validate_task_input("x" * 60_000)
    assert valid is False


def test_validate_task_normal():
    valid, reason = validate_task_input("Analyze the project structure")
    assert valid is True
