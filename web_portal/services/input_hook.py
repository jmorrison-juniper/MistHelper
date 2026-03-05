"""Input interception service for web portal operations.

Replaces builtins.input with a thread-aware version that can read
answers from a per-thread deque when running inside a web context.
Falls back to original input() for CLI/SSH sessions.
"""

import builtins
import logging
import threading
from collections import deque
from contextlib import contextmanager
from typing import Generator


class InputInterceptor:
    """Intercept builtins.input() to feed web-submitted answers.

    Uses threading.local() so each web request thread gets its own
    answer deque without affecting CLI or SSH sessions.
    """

    _original_input = None
    _local = threading.local()
    _installed = False

    @classmethod
    def install(cls) -> None:
        """Replace builtins.input with the patched version."""
        if cls._installed:
            return
        cls._original_input = builtins.input
        builtins.input = cls._patched_input
        cls._installed = True
        logging.info("InputInterceptor installed")

    @classmethod
    def _patched_input(cls, prompt: str = "") -> str:
        """Read from thread-local deque if available, else original."""
        queue = getattr(cls._local, "input_queue", None)
        if queue is not None and len(queue) > 0:
            answer = queue.popleft()
            logging.debug("InputInterceptor: answered '%s'", answer)
            return str(answer)
        if queue is not None and len(queue) == 0:
            raise EOFError("Web input queue exhausted")
        return cls._original_input(prompt)

    @classmethod
    def set_queue(cls, answers: list) -> None:
        """Load answers into the current thread's input queue."""
        cls._local.input_queue = deque(answers)

    @classmethod
    def clear_queue(cls) -> None:
        """Remove the input queue from the current thread."""
        cls._local.input_queue = None


@contextmanager
def web_input_context(answers: list) -> Generator[None, None, None]:
    """Context manager that sets and clears the input queue.

    Usage:
        with web_input_context(["site-id-123", "device-mac"]):
            run_operation()  # input() calls read from the queue
    """
    InputInterceptor.set_queue(answers)
    try:
        yield
    finally:
        InputInterceptor.clear_queue()
