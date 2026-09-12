"""Console echo helper for MistHelper interactive output (feature 1031).

Why:
    Legacy sites in MistHelper used ``logging.warning(...)  # Legacy console
    echo routed via logger.`` to double as a user-visible print and a log
    record. The WARNING level was chosen only because the root console
    handler was configured at WARNING. That practice flooded
    ``data/script.log`` with menu text and made real warnings invisible.

    ``echo()`` restores signal to the WARNING channel by writing the
    message directly to stdout and emitting a single INFO-level log
    record on the module logger. Callers migrate mechanically: replace
    ``logging.warning(msg, *args)`` with ``echo(msg, *args)`` and drop
    the marker comment. No handler configuration is touched. No level
    argument is offered. The helper is a primitive with two effects.

See ``specs/1031-warning-echo-refactor/contracts/echo_helper.md`` for
the full contract (clauses C-1 through C-6).
"""

from __future__ import annotations  # WHY: consistent PEP 604 style across src/utils.

import logging  # WHY: emit the INFO-level record that keeps script.log capture intact.

_LOGGER = logging.getLogger(__name__)  # Module-level logger; propagates to root handlers.


def echo(msg: str, *args: object) -> None:
    """Print a message to stdout and emit one INFO-level log record.

    Why:
        This helper replaces the legacy ``logging.warning(...)  # Legacy
        console echo routed via logger.`` pattern that polluted the
        WARNING channel with menu, prompt, and progress text. Callers
        get one call that both shows the user the message and records
        it in ``data/script.log`` at the correct severity (INFO).

    Args:
        msg (str): The message template. Supports ``%``-style placeholders
            such as ``"%s"`` and ``"%d"``. When ``args`` is empty the
            template is printed verbatim, so a literal ``%`` character
            is safe.
        *args (object): Positional arguments consumed by ``%``-style
            formatting. When empty the template is used as-is on stdout,
            and the log record carries no args.

    Returns:
        None: The function exists for its two side effects.
    """
    print(msg % args if args else msg)  # WHY: apply %-formatting only when args exist; preserve literal '%'.
    _LOGGER.info(msg, *args)  # WHY: defer formatting to logging layer per constitution principle VII.
