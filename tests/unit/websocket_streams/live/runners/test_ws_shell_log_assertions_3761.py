"""Prove shell log assertions accept and reject real captured records."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import ast  # Read the controlled logger records without creating a JSON risk case.
import logging  # Emit real Python log records into pytest capture.
from typing import Any  # Preserve captured fields for the semantic assertion methods.

import pytest  # Check each assertion's refusal result.

from src.websocket_streams.live.transport.runtime.logging.bounds import (
    MAX_EVENT_LENGTH,  # Preserve the runtime event length.
    MAX_FIELD_LENGTH,  # Preserve the runtime field length.
)  # Use the unchanged runtime bounds.
from src.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,  # Produce records through the runtime logger.
)  # Produce controlled records through the runtime logger.
from tests.unit.websocket_streams.live.runners.test_ws_shell_runner import (
    ShellLogAssertions,  # Exercise the exact assertions used by the native shell test.
)  # Exercise the exact assertions used by the native shell test.
from tests.unit.websocket_streams.live.transport.fake_mist_cloud.server import (
    FakeMistCloud,  # Supply the same local fake URL shape as the native shell test.
)  # Supply the same local fake URL shape as the native shell test.

CONTROL_LOGGER_NAME = "tests.unit.websocket_streams.live.runners.shell.issue3761"  # Match the native record selector.


class TestShellLogAssertionControls:
    """Exercise the extracted checks through actual logging records."""

    @staticmethod
    def captured_payloads(records: list[logging.LogRecord]) -> list[dict[str, Any]]:
        """Read actual captured messages into payloads for controlled checks."""
        shell_records = [record for record in records if ".runners.shell." in record.name]  # Match native selection.
        return [ast.literal_eval(record.message) for record in shell_records]  # Read real logger messages.

    def test_assertions_accept_controlled_runtime_records(self, caplog: pytest.LogCaptureFixture) -> None:
        """All grouped assertions accept 21 safe runtime records."""
        caplog.set_level(logging.DEBUG)  # Capture the controlled runtime events.
        with FakeMistCloud() as cloud:  # Keep the address value local and deterministic.
            target = logging.getLogger(CONTROL_LOGGER_NAME)  # Use the package-shaped logger name.
            emitter = StructuredTransportLogger(target)  # Apply the real transport log boundary.
            for event_index in range(21):  # Match the original distinct event count.
                emitter.emit(logging.DEBUG, f"shell_event_{event_index}", {"status": "ok"})  # Emit one safe record.
            ShellLogAssertions.assert_secret_exclusion(caplog, cloud)  # Accept logs with no secret values.
            payloads = self.captured_payloads(caplog.records)  # Read the actual captured runtime records.
            assert len(payloads) == 21  # Prove the control captured all expected runtime records.
            ShellLogAssertions.assert_event_coverage(payloads)  # Accept all 21 distinct events.
            ShellLogAssertions.assert_safe_fields(payloads)  # Accept only allowlisted fields.
            ShellLogAssertions.assert_event_lengths(payloads)  # Accept bounded event names.
            ShellLogAssertions.assert_field_lengths(payloads)  # Accept bounded safe strings.

    @pytest.mark.parametrize("secret_kind", ["address", "path", "typed", "output"])
    def test_secret_assertion_rejects_each_secret_value(
        self,
        secret_kind: str,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Each original secret value causes the exclusion assertion to fail."""
        caplog.set_level(logging.DEBUG)  # Capture the deliberately exposed value.
        with FakeMistCloud() as cloud:  # Use a local address for the address refusal case.
            secret_values = {  # Keep the four original secret inputs explicit.
                "address": cloud.base_ws_url,  # Exercise the address exclusion.
                "path": "/shell/default",  # Exercise the path exclusion.
                "typed": "SECRET-TYPED",  # Exercise the typed-text exclusion.
                "output": "SECRET-OUTPUT",  # Exercise the output-text exclusion.
            }
            target = logging.getLogger(CONTROL_LOGGER_NAME)  # Use a name accepted by the native record selector.
            target.info("%s", secret_values[secret_kind])  # Emit a real secret-bearing record.
            with pytest.raises(AssertionError, match="not in"):  # Require the same exclusion condition to refuse it.
                ShellLogAssertions.assert_secret_exclusion(caplog, cloud)  # Check the captured real log text.

    def test_event_count_assertion_rejects_missing_event(self, caplog: pytest.LogCaptureFixture) -> None:
        """A captured event set below 21 fails the unchanged event-count check."""
        caplog.set_level(logging.DEBUG)  # Capture every controlled structured event.
        emitter = StructuredTransportLogger(logging.getLogger(CONTROL_LOGGER_NAME))  # Use the runtime logger boundary.
        for event_index in range(20):  # Emit one fewer event than the required count.
            emitter.emit(logging.DEBUG, f"shell_event_{event_index}", {"status": "ok"})  # Emit a real safe record.
        payloads = self.captured_payloads(caplog.records)  # Read the actual captured records.
        with pytest.raises(AssertionError, match="20 == 21"):  # Require the original exact count to reject the set.
            ShellLogAssertions.assert_event_coverage(payloads)  # Apply the native event-count assertion.

    def test_safe_field_assertion_rejects_unapproved_field(self, caplog: pytest.LogCaptureFixture) -> None:
        """A captured JSON record with an unapproved field fails the allowlist check."""
        caplog.set_level(logging.DEBUG)  # Capture the deliberately unsafe record.
        target = logging.getLogger(CONTROL_LOGGER_NAME)  # Use a name accepted by the native record selector.
        target.info("%s", '{"event":"shell_event","unexpected":"value"}')  # Emit a real JSON log record.
        payloads = self.captured_payloads(caplog.records)  # Read the actual captured record.
        with pytest.raises(AssertionError, match="False"):  # Require the unchanged allowlist check to reject it.
            ShellLogAssertions.assert_safe_fields(payloads)  # Apply the native safe-field assertion.

    def test_event_length_assertion_rejects_long_event(self, caplog: pytest.LogCaptureFixture) -> None:
        """A captured event beyond the bound fails the unchanged length check."""
        caplog.set_level(logging.DEBUG)  # Capture the deliberately long event.
        target = logging.getLogger(CONTROL_LOGGER_NAME)  # Use a name accepted by the native record selector.
        event = "e" * (MAX_EVENT_LENGTH + 1)  # Exceed the existing event limit by one character.
        target.info("%s", '{"event":"' + event + '"}')  # Emit a real JSON log record.
        payloads = self.captured_payloads(caplog.records)  # Read the actual captured record.
        with pytest.raises(AssertionError, match="False"):  # Require the unchanged event bound to reject it.
            ShellLogAssertions.assert_event_lengths(payloads)  # Apply the native event-length assertion.

    def test_field_length_assertion_rejects_long_safe_value(self, caplog: pytest.LogCaptureFixture) -> None:
        """A captured safe field beyond the bound fails the unchanged length check."""
        caplog.set_level(logging.DEBUG)  # Capture the deliberately long safe value.
        target = logging.getLogger(CONTROL_LOGGER_NAME)  # Use a name accepted by the native record selector.
        value = "x" * (MAX_FIELD_LENGTH + 1)  # Exceed the existing safe-string limit by one character.
        target.info("%s", '{"event":"shell_event","status":"' + value + '"}')  # Emit a real JSON log record.
        payloads = self.captured_payloads(caplog.records)  # Read the actual captured record.
        with pytest.raises(AssertionError, match="False"):  # Require the unchanged field bound to reject it.
            ShellLogAssertions.assert_field_lengths(payloads)  # Apply the native field-length assertion.
