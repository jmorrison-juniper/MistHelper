"""Tests verifying executor and rollback use correct method signatures (T017).

Confirms write_entity receives entity_type/ids/body kwargs, and
read_entity receives entity_type/ids kwargs — no api_module/write_method.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

from src.worker.deploy.executor import ConfigPushExecutor, PushResult


def _make_api_result(
    status_code: int = 200,
    data: dict[str, Any] | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        status_code=status_code,
        data=data or {},
        success=status_code < 300,
        error=None if status_code < 300 else "API error",
    )


class TestExecutorWriteEntitySignature:
    """executor.py must call write_entity(entity_type=, ids=, body=)."""

    def test_push_revision_calls_write_entity(self) -> None:
        mock_mist = MagicMock()
        mock_mist.write_entity.return_value = _make_api_result()

        executor = ConfigPushExecutor.__new__(ConfigPushExecutor)
        executor._db = MagicMock()
        executor._mist = mock_mist

        result = executor.push_revision(
            entity_type="device",
            entity_ids={"site_id": "s1", "device_id": "d1"},
            config_payload={"radio_config": {"band_24": {}}},
        )

        mock_mist.write_entity.assert_called_once_with(
            entity_type="device",
            ids={"site_id": "s1", "device_id": "d1"},
            body={"radio_config": {"band_24": {}}},
        )
        assert result.success is True

    def test_push_unknown_entity_type_returns_failure(self) -> None:
        executor = ConfigPushExecutor.__new__(ConfigPushExecutor)
        executor._db = MagicMock()
        executor._mist = MagicMock()

        result = executor.push_revision(
            entity_type="nonexistent_entity",
            entity_ids={"org_id": "o1"},
            config_payload={},
        )

        assert result.success is False
        assert "No write endpoint" in result.error


class TestRollbackReadEntitySignature:
    """rollback.py must call read_entity(entity_type=, ids=)."""

    def test_read_current_config_calls_read_entity(self) -> None:
        from src.worker.deploy.rollback import RollbackService

        mock_mist = MagicMock()
        mock_mist.read_entity.return_value = _make_api_result(
            data={"name": "office-ap", "radio_config": {}},
        )

        service = RollbackService.__new__(RollbackService)
        service._mist = mock_mist

        config = service._read_current_config(
            "device",
            {"site_id": "s1", "device_id": "d1"},
        )

        mock_mist.read_entity.assert_called_once_with(
            entity_type="device",
            ids={"site_id": "s1", "device_id": "d1"},
        )
        assert config is not None
        assert config["name"] == "office-ap"

    def test_read_unknown_entity_returns_none(self) -> None:
        from src.worker.deploy.rollback import RollbackService

        service = RollbackService.__new__(RollbackService)
        service._mist = MagicMock()

        config = service._read_current_config(
            "nonexistent_entity",
            {"org_id": "o1"},
        )

        assert config is None
