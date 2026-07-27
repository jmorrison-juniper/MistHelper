"""EOF-safe input helpers used across MistHelper and its src/ packages.

This module is the canonical home of the ``InputUtils`` class after
initiative 1015 T-09. ``MistHelper.py`` re-exports the class so historical
``MistHelper.InputUtils`` / ``mh.InputUtils`` callers keep working
transparently -- the re-exported symbol is the same class, not a
delegator.

The ``ensure_tqdm_available()`` probe was retained for the single call
site in ``src/refactors/main_entrypoint.py``. Since initiative 1015 T-14
made ``tqdm`` resolve through ``src.utils.tqdm_wrapper`` at import time
(with a no-op fallback when the real package is missing), no runtime
rebinding of a module global is required -- the probe simply reports
whether the real ``tqdm`` package is active.

Issue: https://github.com/jmorrison-juniper/MistHelper/issues/433 (Phase C).
"""

from __future__ import annotations  # Enable PEP 604 union syntax on Python 3.13.

import logging  # Used by every action-log line below per the project's NON-NEGOTIABLE rule.

from src.utils.tqdm_wrapper import tqdm as _tqdm  # Canonical tqdm handle (T-14) for the availability probe.


class InputUtils:
    """Centralized input handling utilities (canonical home in ``src/utils/``).

    ``MistHelper.py`` re-exports this class so ``MistHelper.InputUtils``
    callers keep working without a delegator.
    """

    @staticmethod
    def ensure_tqdm_available() -> bool:
        """Return True when the real ``tqdm`` package is active; False when the wrapper's fallback is in use.

        The rebind dance that lived in ``MistHelper.InputUtils`` before
        initiative 1015 T-09 is no longer needed: T-14 made
        ``src.utils.tqdm_wrapper`` resolve the real ``tqdm`` at import
        time and expose a no-op iterable-passthrough when the package is
        missing. Callers still invoke this probe for its logging side
        effect; the return value is informational.
        """
        if hasattr(_tqdm, "__module__") and _tqdm.__module__.startswith("tqdm"):  # Real tqdm package is active.
            logging.debug("ensure_tqdm_available: real tqdm package is active")  # Action-log the healthy path.
            return True  # Progress bars are functional.
        logging.warning(  # Warn once that progress bars are degraded to the no-op fallback.
            "ensure_tqdm_available: tqdm fallback in use - progress bars will be disabled"
        )
        return False  # Caller may proceed without progress bars.

    @staticmethod
    def safe_input(
        prompt: str,
        default_value: str = "",
        allow_empty: bool = True,
        context: str = "unknown",
    ) -> str:
        """Return trimmed user input, degrading to ``default_value`` on EOF/empty."""
        logging.debug("safe_input entered (context=%s)", context)  # Action-log entry per project rule.
        try:
            user_input = input(
                prompt
            ).strip()  # noqa: STRUCT-PARAMS  # bare input() OK here -- this IS the safe wrapper.
        except EOFError:  # Stream closed (Ctrl+D, broken pipe, SSH disconnect).
            return InputUtils._handle_eof(context, default_value)  # Degrade gracefully to the default.
        except KeyboardInterrupt:  # Operator pressed Ctrl+C to abort the prompt.
            return InputUtils._handle_interrupt(context)  # Acknowledge cancellation to caller.
        if not user_input:  # Blank entry -- dispatch to the empty-value resolver.
            return InputUtils._handle_empty(default_value, allow_empty, context)  # Return default/empty per policy.
        logging.debug("safe_input returned non-empty value (context=%s)", context)  # Action-log normal path.
        return user_input  # Normal path: return the trimmed user response.

    @staticmethod
    def _handle_empty(default_value: str, allow_empty: bool, context: str) -> str:
        """Resolve the empty-input case per default/allow_empty policy."""
        # WHY: extracted to keep safe_input CC<=5 and length<=25 lines.
        if default_value:  # Blank entry but a default is configured.
            logging.debug(  # Action-log the default substitution for traceability.
                "Empty input for %s, using default: '%s'", context, default_value
            )
            return default_value  # Return the caller-supplied default verbatim.
        if allow_empty:  # Blank entry is acceptable here.
            logging.debug("Empty input for %s allowed by caller", context)  # Action-log no-op return.
            return ""  # Return the empty string as-is.
        logging.warning(  # Warn so operator sees that an empty answer is not OK here.
            "Empty input not allowed for %s, returning empty string", context
        )
        return ""  # Signal invalid/empty response to the caller.

    @staticmethod
    def _handle_eof(context: str, default_value: str) -> str:
        """Handle a closed input stream by degrading to ``default_value``.

        Why:
            Extracted from ``safe_input`` to keep it CC<=5 and length<=25.
            Emits at WARNING (not INFO) so the operator sees the disconnect
            notice on the default root-logger config -- previously we relied
            on a raw ``print()``, which #886 Phase 2 (T20) is retiring in
            favour of logger calls across ``src/``.
        """
        logging.warning(  # Uses warning level so it surfaces on the operator terminal.
            "[EOF] Input stream closed during %s. Using default value: '%s'",
            context,
            default_value,
        )
        return default_value  # Degrade gracefully to the default instead of crashing.

    @staticmethod
    def _handle_interrupt(context: str) -> str:
        """Handle a Ctrl+C interrupt by returning an empty sentinel.

        Why:
            Extracted from ``safe_input`` to keep it CC<=5 and length<=25.
            Uses WARNING so the operator sees the acknowledgement without
            needing INFO enabled -- part of the #886 Phase 2 print-to-logger
            migration for ``src/utils/``.
        """
        logging.warning(
            "[INTERRUPT] User interrupted %s. Canceling...", context
        )  # Surface at WARNING so operator sees it.
        return ""  # Return empty so the caller can detect the abort.
