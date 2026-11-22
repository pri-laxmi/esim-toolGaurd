"""Persistent action and error logging for eSim ToolGuard."""

import logging
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "actions.log"
LOGGER_NAME = "esim_toolguard"


def setup_logger():
    """Configure and return the application logger."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Avoid duplicate file writes when setup_logger is called repeatedly.
    if not any(getattr(handler, "baseFilename", None) == str(LOG_FILE.resolve())
               for handler in logger.handlers):
        handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        logger.addHandler(handler)
    return logger


def log_action(message):
    """Record an application action at INFO level."""
    setup_logger().info(message)


def log_error(message):
    """Record an application error at ERROR level."""
    setup_logger().error(message)


def get_logs():
    """Return the complete persistent log contents, or an empty string."""
    if not LOG_FILE.is_file():
        return ""
    return LOG_FILE.read_text(encoding="utf-8")
