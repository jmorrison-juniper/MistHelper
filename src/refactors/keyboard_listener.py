"""KeyboardListener extracted from MistHelper.

Houses the legacy ``listen_keyboard`` no-op stub as a first-class
instance method. The original function was a harmless fallback left
behind after the real keyboard-listener feature was removed. It stays
as a class-level shim so any remaining call sites (currently one:
the interactive SSR/SRX websocket shell in ``CLIShellManager``)
receive a stable, discoverable target after the module-level function
is deleted (FR-005 / FR-006 -- no wrappers or aliases left in
MistHelper).

No runtime dependencies on MistHelper -- the method only logs and
returns ``None``, so no late-import machinery is needed.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing on 3.10+

import logging  # Structured action logging required by coding standards
from typing import Any  # Loose typing for the pass-through *args/**kwargs


class KeyboardListener:  # Manager class owning the listen_keyboard() no-op stub (PR-13 extraction)
    """Keyboard listener stub for legacy call sites of the removed feature.

    The original keyboard-listener functionality was removed for
    simplicity. This class preserves a stable, discoverable target for
    the remaining call site (the SSR/SRX interactive websocket shell)
    without leaving a module-level function in MistHelper.

    SECURITY: This is a no-op -- it does not open any input device,
    subscribe to keystrokes, or return a listener object. Callers
    that expect a real listener should treat the ``None`` return as
    "no listener available" and fall back to their own input loop.

    Usage:
        KeyboardListener().listen(on_release=..., delay_second_char=0)
    """

    def listen(self, *args: Any, **kwargs: Any) -> None:  # Instance method preserving the original signature
        """No-op keyboard listener: log the call and return None.

        Preserves the ``*args``/``**kwargs`` pass-through signature of
        the removed ``listen_keyboard`` module-level function so no
        existing keyword arguments (``on_release``, ``delay_second_char``,
        ``delay_other_chars``, ``lower``) need to change at the call site.

        Args:
            *args: Positional arguments accepted but ignored.
            **kwargs: Keyword arguments accepted but ignored.

        Returns:
            None: There is no listener object to return.
        """
        logging.info(  # Log entry so any lingering caller is visible in ops logs
            "KeyboardListener.listen invoked (no-op stub; feature removed)"
        )
        logging.debug(  # Log exit with arg-count summary for postmortem tracing without leaking values
            "KeyboardListener.listen returning None args_len=%d kwargs_keys=%s",
            len(args),  # Positional-arg count without dumping the arg values themselves
            sorted(kwargs.keys()),  # Sorted key list keeps log ordering deterministic
        )
        return None  # Preserve the None return contract of the removed listen_keyboard stub
