"""Select and verify model-compatible device versions in organization browser journeys."""

from __future__ import annotations  # Keep browser types optional during test-server imports.

import logging  # Record selection actions and counts without session values.
from collections.abc import Mapping  # Require saved versions to stay bound to device addresses.
from typing import TYPE_CHECKING  # Avoid a browser import before the strict capability guard runs.

if TYPE_CHECKING:  # The server imports test support without using browser controls.
    from playwright.sync_api import Locator, Page  # Check real browser types without loading them at runtime.


class ModelVersionPicker:  # Own actual selections and assertions rather than an obsolete control alias.
    """Select offered versions and verify exact device counts, values, and family states."""

    def __init__(self, page: Page) -> None:  # Keep actions on one test-owned browser page.
        """Bind the picker to the organization options page."""
        logging.info("Bind the model version picker")  # Record the start of picker actions.
        self.page = page  # Use the same page for selection and resulting-value checks.
        logging.debug("Bound the model version picker")  # Confirm the binding without session data.

    def controls(
        self, expected_count: int, device_type: str | None = None, mac: str | None = None
    ) -> Locator:  # Require explicit inventory expectations before a locator loop.
        """Return actual selects after an exact count check, including an expected empty family."""
        from playwright.sync_api import expect  # Load browser assertions only for a browser action.

        assert expected_count >= 0, "The expected device count must not be negative."  # Reject an invalid count.
        logging.info("Read model version controls, expecting %s", expected_count)  # Record the count boundary.
        selector = "select[data-org-version-for]"  # Reuse the per-device metadata from the prior-art test.
        if device_type is not None:  # Restrict a family assertion without using a legacy identifier.
            selector += f'[data-device-type="{device_type}"]'  # Keep the production family scope.
        if mac is not None:  # Saved versions belong to device addresses rather than row positions.
            selector += f'[data-org-version-for="{mac}"]'  # Bind the locator to the expected device.
        controls = self.page.locator(selector)  # Read only the test-owned page.
        expect(controls).to_have_count(expected_count)  # A missing row must fail instead of skipping a loop.
        logging.debug("Read %s model version controls", controls.count())  # Report the verified count.
        return controls  # Let journeys make explicit empty-row and saved-value assertions.

    def select(
        self, version: str, expected_count: int, device_type: str | None = None, mac: str | None = None
    ) -> None:  # Exercise real select controls instead of typing a family-wide version.
        """Select and verify an offered version for every expected device."""
        from playwright.sync_api import expect  # Use browser assertions for the real control state.

        assert expected_count > 0, "Use controls(0) to assert an empty inventory."  # Reject an empty selection loop.
        controls = self.controls(expected_count, device_type, mac)  # Check the inventory before selection.
        for index in range(expected_count):  # Select every expected device, not just the first row.
            control = controls.nth(index)  # Keep the action tied to its checked row.
            expect(control).to_be_visible()  # An excluded family must not receive a selection.
            expect(control).to_be_enabled()  # A disabled control must not send a target.
            expect(control.locator(f'option[value="{version}"]')).to_have_count(1)  # Require a model-offered option.
            logging.info("Select a model version for device %s of %s", index + 1, expected_count)  # Record the action.
            selected = control.select_option(version)  # Trigger the real option-selection and change events.
            logging.debug("Selected %s model version value(s)", len(selected))  # Report the browser result.
            assert selected == [version], "The device did not select the requested version."  # No partial selection.
            expect(control).to_have_value(version)  # Verify the value that the form will send.

    def expect_values(self, values: Mapping[str, str]) -> None:  # Verify restoration by device address.
        """Require every saved device value and reject absent or extra rows."""
        from playwright.sync_api import expect  # Read actual values rather than a copied stand-in result.

        assert len(values) > 0, "Saved-value assertions need an explicit device map."  # Reject an empty assertion.
        self.controls(len(values))  # Reject a missing or extra device before comparing values.
        logging.info("Check saved model versions for %s devices", len(values))  # Record the restoration boundary.
        for mac, version in values.items():  # Preserve each version's association with its own device.
            control = self.controls(1, mac=mac)  # Reject a duplicate or absent device address.
            expect(control).to_have_value(version)  # Require the real saved select value.
        logging.debug("Verified saved model versions for %s devices", len(values))  # Report complete restoration.

    def expect_state(
        self, expected_count: int, device_type: str, selected: bool
    ) -> None:  # Verify that excluded family rows cannot send targets.
        """Require the exact family count and each select's visibility and enabled state."""
        from playwright.sync_api import expect  # Check visual and submission states together.

        controls = self.controls(expected_count, device_type)  # Keep an expected empty family explicit.
        logging.info("Check %s model controls with selected state %s", expected_count, selected)  # Record the intent.
        for index in range(expected_count):  # Check every expected row of the family.
            control = controls.nth(index)  # Do not hide a later row defect behind the first row.
            if selected:  # A selected family must permit an offered version choice.
                expect(control).to_be_visible()  # Require access to the device control.
                expect(control).to_be_enabled()  # Require a value that the form can send.
            else:  # An excluded family must neither show nor send a target.
                expect(control).to_be_hidden()  # Preserve the row-hiding rule.
                expect(control).to_be_disabled()  # Preserve the submission rule.
        logging.debug("Verified %s model controls with selected state %s", expected_count, selected)  # Report all rows.
