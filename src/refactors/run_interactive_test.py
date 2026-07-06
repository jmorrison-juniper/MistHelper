"""RunInteractiveTestManager extracted from MistHelper.

Runs the interactive-safe menu-option test flow used by ``--testinteractive``
mode. Delegates runner construction to the ``_build_interactive_test_runner``
helper that remains in MistHelper and preserves module-level ``org_id``
mutation semantics through late-bound getattr/setattr closures on the
MistHelper module.

Runtime dependencies (``org_id`` module attribute, ``menu_actions`` global,
``InteractiveTestRunner`` class, and the ``_build_interactive_test_runner``
helper) are still owned by MistHelper.py. They are resolved lazily via
``importlib.import_module`` so the extracted module import-graph stays flat
and monkeypatched attributes are honoured in tests.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing on 3.10+

import importlib  # Late-import MistHelper module to avoid circular src<->MistHelper dependency
import logging  # Structured action logging required by coding standards
from types import SimpleNamespace  # Bundle runtime dependencies without coupling to a dataclass
from typing import Any  # Loose typing for late-bound module attributes


def _resolve_runtime_dependencies() -> SimpleNamespace:  # Module-level dependency resolver used at manager init
    """Resolve MistHelper-owned runtime dependencies without static cross-module imports."""
    logging.info(  # Log before importing MistHelper module for dependency resolution
        "Resolving RunInteractiveTestManager runtime dependencies from MistHelper"
    )
    misthelper_module = importlib.import_module("MistHelper")  # Late import avoids circular dependency
    logging.debug(  # Log after successful module import for observability
        "RunInteractiveTestManager runtime dependencies resolved successfully"
    )
    return SimpleNamespace(
        misthelper_module=misthelper_module,  # Retained so global lookups honour monkeypatch in tests
    )


class RunInteractiveTestManager:  # Manager class owning the run_interactive_test() flow (PR-12 extraction)
    """Run interactive-safe menu tests via the extracted InteractiveTestRunner.

    Owns the top-level orchestration originally defined as
    ``run_interactive_test()`` in MistHelper.py. Delegates runner
    construction to ``_build_interactive_test_runner`` in MistHelper and
    preserves the module-level ``org_id`` mutation contract using
    getattr/setattr closures on the MistHelper module handle.

    SECURITY: Executes only options classified as interactive-safe by
    OperationRegistry.

    Usage:
        RunInteractiveTestManager().run()
    """

    def __init__(self) -> None:  # Manager constructor -- late-binds MistHelper module handle
        """Initialize manager with late-bound MistHelper handles."""
        logging.info(  # Log construction start for observability
            "RunInteractiveTestManager init: starting new manager instance"
        )
        self._deps: SimpleNamespace = _resolve_runtime_dependencies()  # Late-bound MistHelper handles
        logging.debug("RunInteractiveTestManager init complete")  # Log after construction

    def _misthelper(self) -> Any:  # Accessor for the late-bound MistHelper module handle
        """Return the current MistHelper module so monkeypatched attributes are honoured."""
        return self._deps.misthelper_module  # Resolve at call-time so tests can substitute values

    def _get_org_id(self) -> Any:  # Getter closure passed to the InteractiveTestRunner builder
        """Return the current module-level org_id from MistHelper (honours monkeypatch)."""
        return getattr(self._misthelper(), "org_id", None)  # Read shared runtime org context

    def _set_org_id(self, new_org_id: Any) -> None:  # Setter closure passed to the InteractiveTestRunner builder
        """Persist the runner-resolved org_id back into the MistHelper module-level attribute."""
        self._misthelper().org_id = new_org_id  # Persist runner outcome to shared module state

    def run(self) -> bool:  # Top-level entry-point invoked by --testinteractive CLI mode
        """Run interactive-safe menu tests via the extracted InteractiveTestRunner.

        Returns:
            bool: Runner outcome — True if all tested options passed, False otherwise.
        """
        logging.info("Routing run_interactive_test to InteractiveTestRunner")  # Preserved original entry log
        runner = self._misthelper()._build_interactive_test_runner(  # Build runner with context closures
            self._get_org_id, self._set_org_id
        )
        logging.info("Executing interactive test runner")  # Preserved log before invocation
        result = bool(runner.execute())  # Cast Any (runner return) to bool for strict typing conformance
        logging.debug("Completed run_interactive_test with result=%s", result)  # Preserved outcome log
        return result  # Signal pass/fail to callers for exit-code logic
