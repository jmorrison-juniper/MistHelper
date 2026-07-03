"""EOF-safe input helpers used across MistHelper and its src/ packages.

The legacy ``InputUtils.safe_input`` lives on a class inside ``MistHelper.py``
which makes it awkward to import from sibling ``src/`` modules without
introducing circular imports. This module exposes the same behavior as a
standalone class-method so any src/ module can ``from src.utils.input_utils
import InputUtils`` and call ``InputUtils.safe_input(prompt, context=...)``.

The implementation matches the original line-for-line so log output and
return semantics stay identical for both call paths.

Issue: https://github.com/jmorrison-juniper/MistHelper/issues/433 (Phase C)
"""

from __future__ import annotations  # Enable PEP 604 union syntax on Python 3.13.

import logging  # Used by every action-log line below per the project's NON-NEGOTIABLE rule.


class InputUtils:
    """Centralized input handling utilities (extracted to ``src/utils/`` for reuse).

    Same name and same public API as the MistHelper.py class. Any future
    consolidation should re-export this implementation from MistHelper.py
    rather than maintain two copies.
    """

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
        """Handle a closed input stream by degrading to ``default_value``."""
        # WHY: extracted to keep safe_input CC<=5 and length<=25 lines.
        print(  # Notify operator at the terminal before degrading gracefully.
            f"\n[EOF] Input stream closed during {context}. " f"Using default value: '{default_value}'"
        )
        logging.info(  # Action-log the disconnect with the substituted default.
            "EOF encountered on input during %s - returning default: '%s'",
            context,
            default_value,
        )
        return default_value  # Degrade gracefully to the default instead of crashing.

    @staticmethod
    def _handle_interrupt(context: str) -> str:
        """Handle a Ctrl+C interrupt by returning an empty sentinel."""
        # WHY: extracted to keep safe_input CC<=5 and length<=25 lines.
        print(f"\n[INTERRUPT] User interrupted {context}. Canceling...")  # Acknowledge cancellation.
        logging.info("KeyboardInterrupt encountered during %s", context)  # Action-log the interrupt.
        return ""  # Return empty so the caller can detect the abort.
