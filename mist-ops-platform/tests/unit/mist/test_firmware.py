"""Tests for FirmwareOrchestrator.execute_upgrade safety gate (T025).

Confirms:
1. execute_upgrade calls validate_upgrade before SDK call
2. Fails with RuntimeError if validation fails
3. Calls write_entity with firmware_site entity type
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.shared.mist.endpoints import ApiResult


class TestFirmwareExecuteUpgrade:
    """FirmwareOrchestrator.execute_upgrade safety gate tests."""

    def test_calls_write_entity_with_firmware_site(self) -> None:
        from src.worker.deploy.firmware import FirmwareOrchestrator

        mock_mist = MagicMock()
        mock_mist.write_entity.return_value = ApiResult(
            status_code=200,
            data={"upgrade_id": "u-123"},
        )

        orch = FirmwareOrchestrator.__new__(FirmwareOrchestrator)
        orch._db = MagicMock()
        orch._mist = mock_mist

        orch.validate_upgrade = MagicMock(
            return_value={
                "valid": True,
                "image_version": "1.0",
                "device_count": 1,
                "device_model": "AP45",
            }
        )
        orch.build_upgrade_payload = MagicMock(
            return_value={
                "firmware_version": "1.0",
                "image_type": "ap",
                "device_model": "AP45",
                "target_device_ids": ["d1"],
                "content_hash": "abc123",
            }
        )

        result = orch.execute_upgrade(
            site_id="site-1",
            image_id=uuid4(),
            target_device_ids=[uuid4()],
        )

        mock_mist.write_entity.assert_called_once()
        call_kwargs = mock_mist.write_entity.call_args
        assert call_kwargs.kwargs["entity_type"] == "firmware_site"
        assert call_kwargs.kwargs["ids"] == {"site_id": "site-1"}
        assert result.success is True

    def test_raises_if_validation_fails(self) -> None:
        from src.worker.deploy.firmware import FirmwareOrchestrator

        orch = FirmwareOrchestrator.__new__(FirmwareOrchestrator)
        orch._db = MagicMock()
        orch._mist = MagicMock()

        orch.validate_upgrade = MagicMock(
            return_value={
                "valid": False,
                "errors": ["Image not approved"],
            }
        )

        with pytest.raises(RuntimeError, match="Pre-upgrade validation"):
            orch.execute_upgrade(
                site_id="site-1",
                image_id=uuid4(),
                target_device_ids=[uuid4()],
            )

        orch._mist.write_entity.assert_not_called()

    def test_returns_error_on_api_failure(self) -> None:
        from src.worker.deploy.firmware import FirmwareOrchestrator

        mock_mist = MagicMock()
        mock_mist.write_entity.return_value = ApiResult(
            status_code=500,
            data={"detail": "Internal Server Error"},
        )

        orch = FirmwareOrchestrator.__new__(FirmwareOrchestrator)
        orch._db = MagicMock()
        orch._mist = mock_mist

        orch.validate_upgrade = MagicMock(
            return_value={
                "valid": True,
                "image_version": "1.0",
                "device_count": 1,
                "device_model": "AP45",
            }
        )
        orch.build_upgrade_payload = MagicMock(
            return_value={
                "firmware_version": "1.0",
            }
        )

        result = orch.execute_upgrade(
            site_id="site-1",
            image_id=uuid4(),
            target_device_ids=[uuid4()],
        )

        assert result.success is False
        assert result.error is not None
        assert "Internal Server Error" in result.error
