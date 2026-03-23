from __future__ import annotations

import logging
import sys
from pathlib import Path

from nixclaw.config import get_settings

_CONFIGURED = False


def setup_logging() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    _CONFIGURED = True

    settings = get_settings()
    level = getattr(logging, settings.system.log_level.upper(), logging.INFO)

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    console.setLevel(level)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(console)

    # File handler if logs dir is writable
    logs_dir = Path(settings.storage.logs_dir)
    try:
        logs_dir.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(logs_dir / "autogen-agent.log")
        fh.setFormatter(fmt)
        fh.setLevel(level)
        root.addHandler(fh)
    except OSError:
        root.warning("Cannot write to %s, file logging disabled", logs_dir)

    # Telegram log bot handler (sends WARNING+ to the log bot)
    try:
        from nixclaw.integrations.telegram_log import TelegramLogHandler

        tg_handler = TelegramLogHandler(level=logging.WARNING)
        tg_handler.setFormatter(fmt)
        root.addHandler(tg_handler)
    except Exception:
        pass  # Log bot is optional, never break startup

    # Suppress noisy third-party loggers
    for name in ("httpx", "httpcore", "openai", "urllib3"):
        logging.getLogger(name).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)
