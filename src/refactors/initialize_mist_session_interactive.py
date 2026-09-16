"""Interactive Mist session initializer extracted from MistHelper (SC-023).

Owns the interactive email/password login flow originally defined as the
top-level `initialize_mist_session_interactive` function in MistHelper.py,
and re-lands it as a class-body method per FR-005. The three MistHelper
callsites (login retry after args, session-switch flow, entrypoint
`_establish_mist_session`) are rewritten in the same PR to invoke the
class method. No wrapper shim remains in MistHelper.py after this
extraction.

MistHelper module-globals (`apisession`, `mistapi`, `msp_privileges`,
`selected_msp`, `org_id`) are read and written via the shared
`_snapshot_session_globals_to_state` / `_restore_session_globals_from_state`
helpers, which stay in MistHelper.py. All dependencies are resolved
lazily through the `_MH` proxy so live re-bindings after interactive
login and test monkeypatching are honoured.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing

from typing import Any  # Loose typing for late-bound MistHelper attributes

from src.config.source_dependency_resolver import (
    SourceDependencyResolver,  # WHY: resolve source dependencies without importing the root module.
)
from src.refactors.msp_privilege_detection import (
    detect_msp_privileges,  # Direct import: MSP detector was extracted per 1015 T-05
)

_MH = SourceDependencyResolver  # Use the source resolver for lazy dependency access.


class MistSessionInteractiveInitializer:  # Interactive login orchestration seam
    """Class-body seam for the interactive Mist API login workflow."""

    @classmethod
    def initialize(cls) -> bool:  # Interactive login entrypoint
        """Run the interactive login flow and store state on the application context."""
        context = _MH.MainEntrypoint.context  # Use the explicit context instead of module session globals.
        state = context.as_selector_state()  # Build the short-lived state bag for the current orchestrator seam.

        def _detect_msp_for_login() -> Any:  # DI adapter binding MSP detection to freshly-authenticated session
            """Delegate MSP detection to the freshly-authenticated session in state."""
            return detect_msp_privileges(  # Call the extracted MSP detector directly without a module state read.
                state.get("apisession")  # Orchestrator stores the new session in state before this runs.
            )

        session_manager = _MH.LoginOrchestrator(  # Build the interactive login orchestrator with injected deps.
            state=state,  # Pass the mutable state bag the orchestrator will update.
            safe_input=_MH.InputUtils.safe_input,  # Inject the EOF-safe input function.
            detect_msp_privileges=_detect_msp_for_login,  # Bind MSP detection to the new login session.
        )
        login_success = session_manager.execute()  # Run the interactive login workflow.
        context.apply_msp_selection(state)  # Store the result on the explicit context.
        return bool(login_success)  # Report whether the interactive login succeeded.
