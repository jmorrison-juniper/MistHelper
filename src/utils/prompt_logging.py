"""Structured prompt logging helpers."""
import logging
from typing import Optional, Dict


def get_prompt_logger(name: str = "prompt") -> logging.Logger:
    return logging.getLogger(name)


def log_prompt_event(logger: Optional[logging.Logger], event: str, details: Optional[Dict] = None) -> None:
    if logger is None:
        logger = get_prompt_logger()
    try:
        logger.info({"event": event, **(details or {})})
    except Exception:
        # Fallback to plain text logging
        logger.info(f"{event} {details}")
