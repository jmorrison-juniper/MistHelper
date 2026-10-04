"""Unit contracts for refusal state handling in the upgrade portal."""

from __future__ import annotations

from pathlib import Path

from src.interfaces.portals.upgrade_portal.app.routes import capture

REPO_ROOT = Path(__file__).resolve().parents[3]  # The repository root for the browser asset.
PORTAL_ROOT = REPO_ROOT / "src" / "interfaces" / "portals" / "upgrade_portal"
SCRIPT_PATH = PORTAL_ROOT / "app" / "assets" / "static" / "js" / "portal.js"
TEMPLATE_PATH = PORTAL_ROOT / "app" / "assets" / "templates" / "capture" / "capture.html"


def script_function(name: str) -> str:
    """Return one portal.js function for a focused source contract."""
    source = SCRIPT_PATH.read_text(encoding="utf-8")  # The browser asset is UTF-8 text.
    start = source.index(f"function {name}(")  # A missing function must fail the contract.
    end = source.find("\n    function ", start + 1)  # The next top-level function ends the body.
    return source[start:] if end < 0 else source[start:end]  # Keep only the requested function.


def test_blank_capture_status_has_no_queued_message() -> None:
    """A page without a capture must not claim that a capture was queued."""
    status = capture.blank_status("", capture.TIER_STANDARD)  # Build the first page state.
    assert status["state"] == capture.STATE_PENDING  # The empty panel remains pending.
    assert status["message"] == ""  # No capture exists before the first press.


def test_opening_capture_status_keeps_the_queued_message() -> None:
    """A real capture must still tell the operator that the worker is queued."""
    record = capture.opening_record(  # Build the complete job shape that the route passes to the worker.
        {
            "capture_id": "cap-1",
            "tier": capture.TIER_STANDARD,
            "run_id": "",
            "role": "pre",
            "site_id": "site-1",
        }
    )
    assert record["message"] == capture.START_MESSAGE  # The worker has accepted the capture.


def test_capture_start_refusal_resets_state_and_scrolls_the_error() -> None:
    """A refused capture start restores the panel and exposes its refusal."""
    function = script_function("startCapture")  # Read the start path only.
    assert 'setText(region.querySelector(\'[data-capture-field="state"]\'), "pending")' in function
    assert 'setText(region.querySelector(\'[data-capture-field="message"]\'), "")' in function
    assert "showCaptureError" in function  # The refusal remains next to the capture.
    assert 'box.scrollIntoView({ block: "center" })' in script_function("showCaptureError")


def test_capture_refusal_region_is_next_to_the_start_control() -> None:
    """The capture refusal region must render before the progress tables."""
    template = TEMPLATE_PATH.read_text(encoding="utf-8")  # The capture page is UTF-8 text.
    assert template.index('data-testid="capture-start-button"') < template.index('data-testid="capture-error"')
    assert template.index('data-testid="capture-error"') < template.index('data-testid="capture-progress"')


def test_precheck_refusal_restores_each_original_state() -> None:
    """A refused multi-site pre-check restores every selected row."""
    function = script_function("runOrgPrechecks")  # Read the sequence catch path.
    assert "var originalStates = {}" in function  # The server-painted values are saved.
    assert "restoreOrgPrecheckStates(card, originalStates)" in function  # The catch path restores them.
