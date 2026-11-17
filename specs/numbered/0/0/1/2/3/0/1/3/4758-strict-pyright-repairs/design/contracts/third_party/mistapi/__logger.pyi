"""Declare the installed SDK sanitizer without importing its logging side effects."""

import logging

class LogSanitizer(logging.Filter):
    """Preserve the SDK filter constructor and record mutation contract."""

    def __init__(self) -> None: ...
    def filter(self, record: logging.LogRecord) -> bool: ...
