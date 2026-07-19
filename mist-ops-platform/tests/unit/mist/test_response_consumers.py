"""Tests verifying consumer code branches on ApiResult .success/.error (T020).

Confirms executor and rollback correctly use .success and .error
properties from ApiResult after T018 added them.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

from src.shared.mist.endpoints import ApiResult
from src.worker.deploy.executor import ConfigPushExecutor


def _api_result(
    status_code: int = 200,
    data: dict[str, Any] | None = None,
) -> ApiResult:
    return ApiResult(status_code=status_code, data=data or {})


class TestExecutorBranchesOnSuccess:
    """executor.py branches on result.success and logs result.error."""

    def test_success_branch_returns_success_true(self) -> None:
        mock_mist = MagicMock()
        mock_mist.write_entity.return_value = _api_result(200)

        executor = ConfigPushExecutor.__new__(ConfigPushExecutor)
        executor._db = MagicMock()
        executor._mist = mock_mist

        result = executor.push_revision(
            "device",
            {"site_id": "s1", "device_id": "d1"},
            {"config": "value"},
        )
        assert result.success is True
        assert result.error == ""

    def test_failure_branch_returns_error_message(self) -> None:
        mock_mist = MagicMock()
        mock_mist.write_entity.return_value = _api_result(
            404,
            {"detail": "Device not found"},
        )

        executor = ConfigPushExecutor.__new__(ConfigPushExecutor)
        executor._db = MagicMock()
        executor._mist = mock_mist

        result = executor.push_revision(
            "device",
            {"site_id": "s1", "device_id": "d1"},
            {"config": "value"},
        )
        assert result.success is False
        assert "Device not found" in result.error


class TestRollbackBranchesOnSuccess:
    """rollback.py branches on result.success for snapshot reads."""

    def test_read_config_success_returns_data(self) -> None:
        from src.worker.deploy.rollback import RollbackService

        mock_mist = MagicMock()
        mock_mist.read_entity.return_value = _api_result(
            200,
            {"name": "test-ap"},
        )

        service = RollbackService.__new__(RollbackService)
        service._mist = mock_mist

        data = service._read_current_config(
            "device",
            {"site_id": "s1", "device_id": "d1"},
        )
        assert data is not None
        assert data["name"] == "test-ap"

    def test_read_config_failure_returns_none(self) -> None:
        from src.worker.deploy.rollback import RollbackService

        mock_mist = MagicMock()
        mock_mist.read_entity.return_value = _api_result(
            404,
            {"detail": "Not found"},
        )

        service = RollbackService.__new__(RollbackService)
        service._mist = mock_mist

        data = service._read_current_config(
            "device",
            {"site_id": "s1", "device_id": "d1"},
        )
        assert data is None
