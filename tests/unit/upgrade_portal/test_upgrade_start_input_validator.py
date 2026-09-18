"""Tests for required destructive upgrade inputs."""

from __future__ import annotations  # Keep annotations inert during test collection.

import logging  # Capture visible validation failures without reading secrets.

from pytest import LogCaptureFixture  # Type the log fixture for focused mypy checks.

from src.upgrade_portal.app.routes.upgrade import (  # Import the route helper under test.
    UpgradeStartInput,
    UpgradeStartInputFailure,
    UpgradeStartInputValidator,
)


class TestUpgradeStartInputValidator:
    """Verify that missing destructive inputs fail where they are absent."""

    def test_missing_json_body_fails_visibly(self, caplog: LogCaptureFixture) -> None:
        """A missing body reports the missing request body."""
        with caplog.at_level(logging.ERROR):  # Capture the visible operator-facing failure.
            result = UpgradeStartInputValidator.validate("run-2753", None)  # Validate without a default body.
        assert isinstance(result, UpgradeStartInputFailure)  # The caller receives a structured refusal.
        assert result.field_name == "json_body"  # The refusal names the absent request body.
        assert "json_body is missing or invalid" in caplog.text  # The log records the exact missing input.

    def test_missing_device_ids_fail_visibly(self, caplog: LogCaptureFixture) -> None:
        """A missing device list reports the missing target set."""
        body = {"firmware_version": "1.2.3", "strategy": "serial"}  # Omit the destructive target set.
        with caplog.at_level(logging.ERROR):  # Capture the visible operator-facing failure.
            result = UpgradeStartInputValidator.validate("run-2753", body)  # Validate without device defaults.
        assert isinstance(result, UpgradeStartInputFailure)  # The caller receives a structured refusal.
        assert result.field_name == "device_ids"  # The refusal names the absent target list.
        assert "device_ids is missing or invalid" in caplog.text  # The log records the exact missing input.

    def test_missing_firmware_version_fails_visibly(self, caplog: LogCaptureFixture) -> None:
        """A missing firmware version reports the missing image choice."""
        body = {"device_ids": ["ap-1"], "strategy": "serial"}  # Omit the image that the operator must choose.
        with caplog.at_level(logging.ERROR):  # Capture the visible operator-facing failure.
            result = UpgradeStartInputValidator.validate("run-2753", body)  # Validate without version defaults.
        assert isinstance(result, UpgradeStartInputFailure)  # The caller receives a structured refusal.
        assert result.field_name == "firmware_version"  # The refusal names the absent target image.
        assert "firmware_version is missing or invalid" in caplog.text  # The log records the exact missing input.

    def test_missing_strategy_fails_visibly(self, caplog: LogCaptureFixture) -> None:
        """A missing strategy reports the missing execution mode."""
        body = {"device_ids": ["ap-1"], "firmware_version": "1.2.3"}  # Omit the required execution mode.
        with caplog.at_level(logging.ERROR):  # Capture the visible operator-facing failure.
            result = UpgradeStartInputValidator.validate("run-2753", body)  # Validate without strategy defaults.
        assert isinstance(result, UpgradeStartInputFailure)  # The caller receives a structured refusal.
        assert result.field_name == "strategy"  # The refusal names the absent execution mode.
        assert "strategy is missing or invalid" in caplog.text  # The log records the exact missing input.

    def test_complete_input_preserves_explicit_values(self) -> None:
        """Complete input reaches the service without secret or identifier defaults."""
        body = {  # Use all destructive inputs, so the guard must accept them.
            "device_ids": [" ap-1 "],  # Include space to prove stable normalization.
            "firmware_version": " 1.2.3 ",  # Include space to prove stable normalization.
            "strategy": "parallel",  # Use a documented execution mode.
            "rollback_enabled": True,  # Keep the explicit rollback choice.
        }
        result = UpgradeStartInputValidator.validate("run-2753", body)  # Validate the complete input.
        assert isinstance(result, UpgradeStartInput)  # The caller receives service-ready input.
        assert result.device_ids == ["ap-1"]  # The target list holds no blank identifier.
        assert result.firmware_version == "1.2.3"  # The target version holds the operator choice.
        assert result.strategy == "parallel"  # The execution mode holds the operator choice.
        assert result.rollback_enabled is True  # The rollback flag holds the operator choice.
