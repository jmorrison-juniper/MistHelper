"""Negative guards for the capture click journey."""

from __future__ import annotations

import logging  # Record each guard test without exposing run data.

import pytest  # Check each input to the journey.

from tests.e2e.upgrade_portal.test_capture import (  # Exercise the guard used by the real browser journey.
    OPTIONS_SAVE_ID,  # The plan-save control must stay unused after a failure.
    CaptureClickJourney,  # Own the actual run and version admission checks.
)
from tests.e2e.upgrade_portal.test_upgrade import (  # Use the source of the current option-control identifiers.
    START_BUTTON_ID,  # The firmware start control stays unused.
    TYPE_VERSION_SELECT_IDS,  # Cover each current type control.
)
from tests.support.upgrade_portal_e2e.site_lock import RunLedger  # Keep the unit run key in a test-owned ledger.

logger = logging.getLogger(__name__)  # Tie test records to this guard module.


class FakeCount:
    """Return a fixed count from a browser locator."""

    def __init__(self, count: int) -> None:
        """Store a count for the local locator."""
        self.value = count  # Keep the local count explicit.

    def count(self) -> int:
        """Return the fixed locator count."""
        return self.value  # Report only the local count.


class FakeControl:
    """Return a fixed option list and record a selected test value."""

    def __init__(
        self,
        page: FakePage,
        option_count: int,
        control_count: int = 1,
        empty_selection: bool = False,
    ) -> None:
        """Bind one fake select to the local page counters."""
        self.page = page  # Count selections from local controls.
        self.option_count = option_count  # One means only the empty prompt exists.
        self.control_count = control_count  # Zero means the real page omitted this control.
        self.empty_selection = empty_selection  # Model a control that accepts no selected option.
        self.value = ""  # No type has a selection before the helper runs.

    def count(self) -> int:
        """Return the number of matching type controls."""
        return self.control_count  # Let a negative case prove a missing control fails.

    def locator(self, selector: str) -> FakeCount:
        """Return the fixed option count for the requested list."""
        del selector  # This unit proof uses only the option count.
        return FakeCount(self.option_count)  # Keep the guard input local.

    def select_option(self, index: int) -> list[str]:
        """Record a selection if the positive helper reaches this control."""
        logger.info("Record one local version selection")  # Record before the control changes state.
        self.page.selection_calls += 1  # Count only local selection actions.
        if self.empty_selection:  # Preserve a failed selection for the guard's negative case.
            logger.debug("The local control selected no version")  # Report the local response.
            return []  # Match Playwright when the control selects no option.
        self.value = f"version-{index}"  # Return one selected version to the check.
        logger.debug("The local control selected one offered version")  # Report the safe result state.
        return [self.value]  # Match the Playwright select result shape.

    def input_value(self) -> str:
        """Return the value selected by the shared helper."""
        return self.value  # Expose only the local fake value.


class FakePage:
    """Record browser actions but send no request."""

    def __init__(
        self,
        missing_type: str | None = None,
        missing_row_type: str | None = None,
        missing_control_type: str | None = None,
        empty_selection_type: str | None = None,
    ) -> None:
        """Prepare a page with one fault."""
        self.url = "http://127.0.0.1:8056/runs/e2e-run-3380-unit/options"  # Use a local synthetic address.
        self.missing_type = missing_type  # Keep the negative condition explicit.
        self.missing_row_type = missing_row_type  # Name a device family with no target row.
        self.missing_control_type = missing_control_type  # Name a device family with no control.
        self.empty_selection_type = empty_selection_type  # Name a control that selects no offered version.
        self.requested_testids: list[str] = []  # Record controls that the helper reads.
        self.options_save_calls = 0  # Count any plan-save control access.
        self.firmware_calls = 0  # Count any firmware-start control access.
        self.selection_calls = 0  # Count any version selection.
        self.controls = {  # Give each control one prompt or one prompt plus a version.
            test_id: FakeControl(
                self,
                1 if test_id == missing_type else 2,
                0 if test_id == missing_control_type else 1,
                empty_selection=test_id == empty_selection_type,
            )
            for test_id in TYPE_VERSION_SELECT_IDS
        }

    def wait_for_url(self, pattern: str, timeout: int) -> None:
        """Record the existing options-page wait without launching a browser."""
        self.wait = (pattern, timeout)  # Preserve the URL and bound for assertions.

    def locator(self, selector: str) -> FakeCount:
        """Report whether the matching device type has a target row."""
        device_type = selector.split('data-device-type="', 1)[1].split('"', 1)[0]  # Read the requested row type.
        return FakeCount(0 if device_type == self.missing_row_type else 1)  # Use a local target-row count.

    def get_by_test_id(self, test_id: str) -> FakeControl:
        """Record the requested control and return its local stand-in."""
        self.requested_testids.append(test_id)  # Show which browser control the guard reached.
        if test_id == OPTIONS_SAVE_ID:  # A negative guard must stop before this button.
            self.options_save_calls += 1  # Make any accidental save visible.
        if test_id == START_BUTTON_ID:  # This test does not start firmware.
            self.firmware_calls += 1  # Make any accidental firmware start visible.
        return self.controls.get(test_id, FakeControl(self, 1))  # Unknown controls hold no offered option.


@pytest.mark.parametrize(
    ("status", "reason"),
    [(409, "409"), (503, "503")],
    ids=("live-run-refusal", "lock-store-unavailable"),
)
def test_create_refusal_fails_before_save_or_firmware(status: int, reason: str) -> None:
    """A refused create response stops the journey before any browser action."""
    page = FakePage()  # Build no browser and send no HTTP request.
    ledger = RunLedger()  # Keep the unit run ledger empty on refused creation.
    journey = CaptureClickJourney(page, ledger)  # Use the same guard as the native journey.
    logger.info("Check the failure path for run-create status %s", status)  # Record the case before it runs.
    with pytest.raises(AssertionError, match=reason):  # Require the status-specific failure.
        journey.require_created_run(status)  # Exercise the actual guard used by the browser test.
    logger.debug("The refused create path stopped before browser actions")  # Confirm the guard result.
    assert page.options_save_calls == 0, "A refused create response must not access the options save control."
    assert page.firmware_calls == 0, "A refused create response must not access the firmware start control."
    assert page.requested_testids == [], "A refused create response must stop before reading page controls."
    assert ledger.runs == (), "A refused create response must not enter a run in the cleanup ledger."


def test_available_type_versions_are_selected_before_the_journey_continues() -> None:
    """Available real type controls pass the same guard used by the browser journey."""
    page = FakePage()  # Give each type control one offered version.
    ledger = RunLedger()  # Record the run key that the options URL supplies.
    journey = CaptureClickJourney(page, ledger)  # Run the decision method from the journey.
    logger.info("Check the positive control for all current type versions")  # Record the control case.
    run_id = journey.prepare_options()  # Require the three versions and select them through shared prior art.
    logger.debug("The positive control prepared one run and selected %d values", page.selection_calls)  # Count work.
    assert run_id == "e2e-run-3380-unit", "The guard must return the run key from the options URL."
    assert ledger.runs == (run_id,), "The guard must record the run before it selects options."
    assert page.selection_calls == len(TYPE_VERSION_SELECT_IDS), "The shared helper must select all three types."
    for test_id in TYPE_VERSION_SELECT_IDS:  # Require a selected value in each current family control.
        assert page.controls[test_id].input_value() == "version-1", f"{test_id} did not retain its offered value."
    assert page.options_save_calls == 0, "Preparing options must not save the plan without the click."
    assert page.firmware_calls == 0, "The click journey must not start firmware."


@pytest.mark.parametrize(
    ("fault", "expected"),
    [
        ("missing-row", "has no target row"),
        ("missing-control", "rendered 0 controls"),
    ],
    ids=("missing-device-row", "missing-type-control"),
)
@pytest.mark.parametrize(
    "test_id",
    TYPE_VERSION_SELECT_IDS,
    ids=("ap", "switch", "gateway"),
)
def test_missing_target_or_control_fails_before_save_or_firmware(fault: str, expected: str, test_id: str) -> None:
    """A missing target row or type control stops before plan save and firmware start."""
    device_type = test_id.rsplit("-", 1)[1]  # Match the type value used by the target-row data attribute.
    options = {"missing_row_type": device_type} if fault == "missing-row" else {"missing_control_type": test_id}
    page = FakePage(**options)  # Remove only the selected type's required row or control.
    ledger = RunLedger()  # Keep the run in the guard's cleanup ledger.
    journey = CaptureClickJourney(page, ledger)  # Exercise the actual guard used by the browser test.
    logger.info("Check the %s guard for %s", fault, test_id)  # Record the measured negative case.
    with pytest.raises(AssertionError, match=expected):  # Require a specific failure for this missing input.
        journey.prepare_options()  # Reject the fixture fault before the plan save.
    logger.debug("The %s guard stopped before save or firmware", fault)  # Confirm the failure boundary.
    assert page.selection_calls == 0, "A missing row or control must stop before version selection."
    assert page.options_save_calls == 0, "A missing row or control must not access the plan-save control."
    assert page.firmware_calls == 0, "A missing row or control must not access the firmware-start control."
    assert ledger.runs == ("e2e-run-3380-unit",), "The run must enter the teardown ledger before validation."


@pytest.mark.parametrize(
    "missing_type",
    TYPE_VERSION_SELECT_IDS,
    ids=("ap-version-unavailable", "switch-version-unavailable", "gateway-version-unavailable"),
)
def test_missing_type_version_fails_before_save_or_firmware(missing_type: str) -> None:
    """An empty type control stops the journey before plan save or firmware start."""
    page = FakePage(missing_type)  # Remove one offered version from a synthetic control.
    ledger = RunLedger()  # Record only the test-owned synthetic run key.
    journey = CaptureClickJourney(page, ledger)  # Use the same guard as the native journey.
    logger.info("Check the missing-version path for %s", missing_type)  # Record the type before the guard runs.
    with pytest.raises(AssertionError, match=missing_type):  # Require a specific failure for each device type.
        journey.prepare_options()  # The guard must reject the empty control before the plan save.
    logger.debug("The empty version path stopped before save or firmware")  # Confirm the failure boundary.
    assert page.options_save_calls == 0, "An empty type control must not access the options save control."
    assert page.firmware_calls == 0, "An empty type control must not access the firmware start control."
    assert page.selection_calls == 0, "The helper must select no version when one required type is empty."
    assert OPTIONS_SAVE_ID not in page.requested_testids, "The guard must stop before it reads the save control."
    assert START_BUTTON_ID not in page.requested_testids, "The guard must stop before it reads the firmware control."
    assert ledger.runs == ("e2e-run-3380-unit",), "The guard must ledger its synthetic run before checking controls."


def test_empty_selection_fails_before_save_or_firmware() -> None:
    """A helper that selects no value stops before plan save or firmware start."""
    test_id = TYPE_VERSION_SELECT_IDS[0]  # Use the first type control for this failure.
    page = FakePage(empty_selection_type=test_id)  # Keep all rows and offered options available.
    ledger = RunLedger()  # Track only the local synthetic run key.
    journey = CaptureClickJourney(page, ledger)  # Exercise the actual browser-test guard.
    logger.info("Check the helper result when one selected value remains empty")  # Record the negative scenario.
    with pytest.raises(AssertionError, match=f"{test_id} kept an empty version"):  # Require the precise failure.
        journey.prepare_options()  # Stop before saving a plan that lacks one device type.
    logger.debug("The empty selection failed before save or firmware")  # Confirm the failure boundary.
    assert page.selection_calls == len(TYPE_VERSION_SELECT_IDS), "The helper must attempt all current type controls."
    assert page.options_save_calls == 0, "An empty selected value must not access the options save control."
    assert page.firmware_calls == 0, "An empty selected value must not start firmware."
    assert OPTIONS_SAVE_ID not in page.requested_testids, "The guard must stop before it reads the save control."
    assert START_BUTTON_ID not in page.requested_testids, "The guard must stop before it reads the firmware control."
    assert ledger.runs == ("e2e-run-3380-unit",), "The guard must ledger the synthetic run before checking values."
