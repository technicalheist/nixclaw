from __future__ import annotations

import logging
import sys
from pathlib import Path

from nixclaw.config import get_settings

_CONFIGURED = False
_VERBOSE = False


def setup_logging(verbose: bool = False) -> None:
    global _CONFIGURED, _VERBOSE
    if _CONFIGURED:
        return
    _CONFIGURED = True
    _VERBOSE = verbose

    settings = get_settings()

    # In normal mode: only show WARNING+
    # In verbose mode: show the configured level (default INFO)
    if verbose:
        level = getattr(logging, settings.system.log_level.upper(), logging.INFO)
    else:
        level = logging.WARNING

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    console.setLevel(level)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)  # Root captures everything; handlers filter
    root.addHandler(console)

    # File handler always logs at INFO+ (full detail regardless of verbose)
    logs_dir = Path(settings.storage.logs_dir)
    try:
        logs_dir.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(logs_dir / "nixagent.log")
        fh.setFormatter(fmt)
        fh.setLevel(logging.INFO)
        root.addHandler(fh)
    except OSError:
        pass  # Silently skip if not writable

    # Telegram log bot handler (sends WARNING+ to the log bot)
    try:
        from nixclaw.integrations.telegram_log import TelegramLogHandler

        tg_handler = TelegramLogHandler(level=logging.WARNING)
        tg_handler.setFormatter(fmt)
        root.addHandler(tg_handler)
    except Exception:
        pass

    # Suppress noisy third-party loggers
    noisy_loggers = ["httpx", "httpcore", "openai", "urllib3", "telegram"]
    for name in noisy_loggers:
        logging.getLogger(name).setLevel(logging.ERROR if not verbose else logging.WARNING)


def is_verbose() -> bool:
    return _VERBOSE


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)
