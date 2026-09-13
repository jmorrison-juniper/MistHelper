#!/usr/bin/env python3
"""Verify Wave 1 bounded-decomposition scope boundary constraints.

Checks that Wave 1 changes respected all explicit exclusion boundaries:
1. No new packet-capture decomposition files added to src/capture/.
2. Menu action key set has not been reduced from Wave 1 baseline.
3. Wave-1-touched classes remain accessible in MistHelper module.
4. The bounded-decomposition-checklist.md evidence document is present.

Exit code 0 means all checks pass. Exit code 1 means one or more violations found.

Usage:
    python scripts/wave1/verify_wave1_scope_boundaries.py
"""

from __future__ import annotations  # Enable postponed evaluation of annotations for Python 3.9 compat

import logging  # Structured output for CI and operator use
import sys  # For sys.exit and sys.path manipulation
from pathlib import Path  # For cross-platform file path handling

# Configure structured output so CI logs show PASS/FAIL clearly
logging.basicConfig(
    level=logging.INFO,  # Show info and above; debug messages appear only in verbose mode
    format="%(levelname)s %(message)s",  # Simple level+message format for readability
)

# Repository root resolved from this script's location: scripts/wave1/ -> scripts/ -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[2]  # Two levels up from scripts/wave1/

# Baseline menu_actions key count at Wave 1 completion (2026-05-15)
# Any count below this value means menu keys were silently removed
_MENU_ACTIONS_BASELINE = 178  # Documented baseline for scope boundary enforcement

# Expected src/capture/ filenames at Wave 1 baseline — no new additions allowed
# Wave 1 exclusion: no packet-capture architecture decomposition
_CAPTURE_BASELINE_FILES = {
    "packet_capture.py",  # Pre-existing packet capture module
    "__init__.py",  # Package init file
}

# Wave-1-touched classes that must remain accessible in MistHelper
# These were the in-scope classes modified during Wave 1 safe_input and logging work
_WAVE1_CLASSES = [
    "TroubleshootUtils",  # Touched in safe_input hardening and logging envelopes
    "SSHRunnerManager",  # Touched in safe_input hardening and logging envelopes
    "InputUtils",  # Core safe_input infrastructure
    "OperationRegistry",  # Routing/safety classification baseline
    "PacketCaptureManager",  # Wave 1 exclusion: must NOT have been extracted
]


def _check_packet_capture_not_decomposed() -> tuple[bool, str]:
    """Check that no new packet-capture files were added to src/capture/."""
    logging.info("Checking src/capture/ for new packet-capture decomposition files")  # Log before scan
    capture_path = _REPO_ROOT / "src" / "capture"  # Path to the capture module directory
    if not capture_path.exists():  # Missing directory means no decomposition possible
        logging.debug("src/capture/ not found -- skipping packet capture decomposition check")  # Debug note
        return True, "src/capture/ not found -- no decomposition possible"  # Not a failure
    actual_files = {  # Collect all filenames, excluding compiled bytecode subdirectories
        f.name for f in capture_path.iterdir() if not f.name.startswith("__pycache__")
    }
    new_files = actual_files - _CAPTURE_BASELINE_FILES  # Anything beyond baseline is a violation
    logging.debug("src/capture/ files: %s", actual_files)  # Log all found files for traceability
    if new_files:  # Any new files indicate unauthorized packet-capture decomposition in Wave 1
        return False, f"New packet-capture files in src/capture/: {new_files}"
    return True, "No new packet-capture decomposition files -- OK"  # Clean result


def _check_menu_actions_not_reduced() -> tuple[bool, str]:
    """Check that menu_actions key count has not dropped below Wave 1 baseline."""
    logging.info(  # Log before import attempt so failures are traceable
        "Checking menu_actions key count against baseline of %d", _MENU_ACTIONS_BASELINE
    )
    sys.path.insert(0, str(_REPO_ROOT))  # Ensure repo root on path so MistHelper is importable
    try:
        import MistHelper  # pylint: disable=import-outside-toplevel  # noqa: PLC0415
    except ImportError as exc:  # Import failure is a hard error -- report and fail
        return False, f"Could not import MistHelper: {exc}"
    actual_count = len(MistHelper.menu_actions)  # Count all currently registered menu keys
    logging.debug(  # Log count and baseline for comparison in operator output
        "menu_actions count: %d (baseline: %d)", actual_count, _MENU_ACTIONS_BASELINE
    )
    if actual_count < _MENU_ACTIONS_BASELINE:  # Below baseline means keys were removed
        return False, f"menu_actions shrank: got {actual_count}, expected >= {_MENU_ACTIONS_BASELINE}"
    return True, f"menu_actions key count {actual_count} >= baseline {_MENU_ACTIONS_BASELINE} -- OK"


def _check_wave1_classes_still_accessible() -> tuple[bool, str]:
    """Check that all Wave-1-touched classes remain accessible in MistHelper."""
    logging.info("Checking Wave-1-touched classes still accessible in MistHelper")  # Log before scan
    sys.path.insert(0, str(_REPO_ROOT))  # Ensure repo root on path for import
    try:
        import MistHelper  # pylint: disable=import-outside-toplevel  # noqa: PLC0415
    except ImportError as exc:  # Import failure prevents the check from running
        return False, f"Could not import MistHelper: {exc}"
    missing = [  # Collect classes that are no longer accessible in the module
        cls for cls in _WAVE1_CLASSES if not hasattr(MistHelper, cls)
    ]
    logging.debug("Classes checked: %s  Missing: %s", _WAVE1_CLASSES, missing)  # Log result for tracing
    if missing:  # Missing classes mean extraction or rename happened outside Wave 1 scope
        return False, f"Wave-1 classes missing from MistHelper: {missing}"
    return True, f"All {len(_WAVE1_CLASSES)} Wave-1-touched classes accessible -- OK"  # All present


def _check_checklist_exists() -> tuple[bool, str]:
    """Check that the bounded-decomposition-checklist.md evidence document is present."""
    logging.info("Checking bounded-decomposition-checklist.md exists")  # Log before file check
    checklist_path = (  # Absolute path to the scope-boundary constraints evidence document
        _REPO_ROOT / "specs" / "192-compliance-decomposition-wave1" / "bounded-decomposition-checklist.md"
    )
    if not checklist_path.exists():  # Missing document means audit trail is incomplete
        return False, f"bounded-decomposition-checklist.md not found: {checklist_path}"
    logging.debug("Checklist found at: %s", checklist_path)  # Confirm the path exists
    return True, "bounded-decomposition-checklist.md present -- OK"  # Document found


def main() -> int:
    """Run all scope boundary checks and report pass/fail per condition."""
    logging.info("=== Wave 1 Scope Boundary Verification ===")  # Header for log readability
    checks = [  # Ordered list of (label, check function) pairs — all must pass
        ("Packet capture not decomposed", _check_packet_capture_not_decomposed),
        ("Menu actions not reduced", _check_menu_actions_not_reduced),
        ("Wave-1 classes still accessible", _check_wave1_classes_still_accessible),
        ("Bounded-decomposition checklist exists", _check_checklist_exists),
    ]
    failures: list[str] = []  # Accumulate all failed condition messages for summary
    for label, check_fn in checks:  # Run each check and report individually
        logging.info("Checking: %s", label)  # Log the check name before running it
        passed, message = check_fn()  # Execute the check function and get result
        if passed:  # Check passed -- log at info level
            logging.info("  PASS: %s", message)
        else:  # Check failed -- log at error level so CI highlights it
            logging.error("  FAIL: %s", message)
            failures.append(f"{label}: {message}")  # Accumulate failure details for summary
    if failures:  # One or more violations found -- scope boundaries were broken
        logging.error(  # Error header with violation count
            "=== Scope Boundary Audit FAILED (%d violation(s)) ===", len(failures)
        )
        for failure in failures:  # Print each violation so the operator knows what to fix
            logging.error("  - %s", failure)
        return 1  # Non-zero exit signals CI gate failure
    logging.info(  # All checks passed -- clean scope compliance
        "=== Scope Boundary Audit PASSED -- all %d checks OK ===", len(checks)
    )
    return 0  # Zero exit signals clean scope boundary compliance


if __name__ == "__main__":
    sys.exit(main())  # Run as standalone script and exit with pass/fail code
