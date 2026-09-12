"""is_debug_mode extracted from MistHelper (SC-002).

Owns the module-level ``is_debug_mode()`` predicate originally defined at
MistHelper.py:318-320, and re-lands it as a ``@staticmethod`` on
``IsDebugMode`` per FR-005 carry-forward. All 12 MistHelper.py callsites
are rewritten in the same PR to reference the extracted class method;
no wrapper shim remains in MistHelper.py after this extraction. The
legacy ``EnvironmentUtils.is_debug_mode`` wrapper at MistHelper.py:5891-5900
is deleted outright in the same PR (0 callers per spec clarification Q1).
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing

import logging  # Structured action logging per Constitution VII
import sys  # Read CLI argv to detect --debug / -d flag presence


class IsDebugMode:  # Class-body seam for the debug-mode predicate (FR-005 carry-forward)
    """Class-body seam owning the debug-mode predicate."""

    @staticmethod
    def check() -> bool:  # Return True when the operator passed --debug or -d on the CLI
        """Return True if the ``--debug`` or ``-d`` flag is present in ``sys.argv``.

        Preserves the exact semantics of the origin ``is_debug_mode()`` function
        that previously lived at MistHelper.py:318-320. No behavioral change:
        the predicate is a pure argv scan with no side effects.
        """
        logging.debug("[DEBUG-MODE] Checking CLI flags for debug-mode indicators")  # BEFORE: predicate entry
        result = "--debug" in sys.argv or "-d" in sys.argv  # Return True if debug flag present in command line
        logging.debug("[DEBUG-MODE] Debug-mode predicate result: %s", result)  # AFTER: predicate outcome
        return result  # Emit the boolean verdict to the caller
