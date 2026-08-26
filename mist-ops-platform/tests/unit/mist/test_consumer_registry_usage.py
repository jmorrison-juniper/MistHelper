"""Tests verifying consumer modules call registry correctly (T014b).

Each refactored consumer should use list_all_entities or read_entity
with the correct entity type string — no raw api_module/list_method args.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.shared.mist.endpoints import ApiResult


def _mock_api_result(
    data: dict[str, Any] | list[dict[str, Any]],
    status_code: int = 200,
) -> ApiResult:
    """Return a real ApiResult, because the callers now read result.success.

    A SimpleNamespace carried only status_code and data. `_read_records` reads
    `result.success` before it reads `result.data` (issue #1884), so a stub
    without that property raised AttributeError instead of proving the call.
    """
    return ApiResult(status_code=status_code, data=data)


class TestAuthUsesRegistry:
    """auth.py must call list_all_entities('self_identity', {})."""

    def test_fetch_self_calls_self_identity(self) -> None:
        import sys

        # Mock modules that auth.py's import chain requires
        stubs = {
            "pydantic_settings": MagicMock(),
            "hvac": MagicMock(),
        }
        saved = {k: sys.modules.get(k) for k in stubs}
        sys.modules.update(stubs)
        try:
            # Force reimport with stubs in place
            for mod_key in list(sys.modules):
                if mod_key.startswith("src.shared.config.settings"):
                    del sys.modules[mod_key]
                if mod_key.startswith("src.shared.mist.session"):
                    del sys.modules[mod_key]
                if mod_key.startswith("src.shared.services.auth"):
                    del sys.modules[mod_key]

            from src.shared.services.auth import AuthService

            mock_mist = MagicMock()
            mock_mist.list_all_entities.return_value = _mock_api_result(
                [{"privileges": [{"scope": "org", "org_id": "o1"}]}],
            )

            with (
                patch(
                    "src.shared.services.auth.MistEndpointService",
                    return_value=mock_mist,
                ),
                patch("src.shared.services.auth.mistapi"),
            ):
                service = AuthService.__new__(AuthService)
                service._factory = MagicMock()
                service._redis = None
                service._fetch_self("fake-token")

            mock_mist.list_all_entities.assert_called_once_with(
                "self_identity",
                {},
            )
        finally:
            for key, original in saved.items():
                if original is None:
                    sys.modules.pop(key, None)
                else:
                    sys.modules[key] = original


class TestPreChecksUsesRegistry:
    """pre_checks.py must call list_all_entities('org_device_list') once.

    Issue #1886: the fetch moved from once-per-device to once-per-run,
    so this test now drives the shared fetch, not the per-device path.
    """

    def test_fetch_device_index_calls_org_device_list(self) -> None:
        from src.worker.checks.pre_checks import PreCheckService

        runner = PreCheckService.__new__(PreCheckService)
        runner._mist = MagicMock()  # WHY: stand in for the real Mist client.
        runner._mist.list_all_entities.return_value = _mock_api_result(
            [{"id": "dev-1", "status": "connected"}],
        )

        # WHY: one org-wide fetch must build the index for every target.
        index, fetch_error = runner._fetch_device_index("org-1", ["dev-1"])

        runner._mist.list_all_entities.assert_called_once_with(
            "org_device_list",
            ids={"org_id": "org-1"},
        )
        assert fetch_error is None  # WHY: a 200 response must not report an error.
        # WHY: the static lookup must read the index, not call the API again.
        result = PreCheckService._ping_device("dev-1", index, fetch_error)
        assert result.passed is True


class TestPostChecksUsesRegistry:
    """post_checks.py must call list_all_entities('org_device_list') once.

    Issue #1886: the fetch moved from once-per-device to once-per-run,
    so this test now drives the shared fetch, not the per-device path.
    """

    def test_fetch_device_index_calls_org_device_list(self) -> None:
        from src.worker.checks.post_checks import PostCheckService

        runner = PostCheckService.__new__(PostCheckService)
        runner._mist = MagicMock()  # WHY: stand in for the real Mist client.
        runner._mist.list_all_entities.return_value = _mock_api_result(
            [{"id": "dev-1", "status": "connected"}],
        )

        # WHY: one org-wide fetch must build the index for every target.
        index, fetch_error = runner._fetch_device_index("org-1", ["dev-1"])

        runner._mist.list_all_entities.assert_called_once_with(
            "org_device_list",
            ids={"org_id": "org-1"},
        )
        assert fetch_error is None  # WHY: a 200 response must not report an error.
        # WHY: the static lookup must read the index, not call the API again.
        result = PostCheckService._get_device_health("dev-1", index, fetch_error)
        assert result.passed is True


class TestStatusUsesRegistry:
    """status.py must call read_entity('device_stats')."""

    def test_capture_status_calls_device_stats(self) -> None:
        from src.worker.sync.status import StatusSyncService

        service = StatusSyncService.__new__(StatusSyncService)
        service._mist = MagicMock()
        service._mist.read_entity.return_value = _mock_api_result(
            {"status": "connected", "uptime": 3600},
        )
        service._db = MagicMock()
        service._org_id = uuid4()

        mock_device = MagicMock()
        mock_device.site_id = uuid4()
        mock_device.device_id = uuid4()

        service._capture_status(mock_device)

        service._mist.read_entity.assert_called_once_with(
            "device_stats",
            ids={
                "site_id": str(mock_device.site_id),
                "device_id": str(mock_device.device_id),
            },
        )


class TestEventsUsesRegistry:
    """events.py must call list_all_entities('audit_log')."""

    def test_fetch_events_calls_audit_log(self) -> None:
        from src.worker.sync.events import EventSyncService

        service = EventSyncService.__new__(EventSyncService)
        service._mist = MagicMock()
        service._org_id = str(uuid4())
        service._mist.list_all_entities.return_value = _mock_api_result(
            [{"id": "evt-1", "message": "config changed"}],
        )

        result = service._fetch_events()

        service._mist.list_all_entities.assert_called_once_with(
            "audit_log",
            ids={"org_id": str(service._org_id)},
        )
        assert len(result) == 1


class TestInventoryUsesRegistry:
    """inventory.py must call list_all_entities for sites and devices."""

    def test_sync_sites_calls_org_site_list(self) -> None:
        from src.worker.sync.inventory import InventorySyncService

        service = InventorySyncService.__new__(InventorySyncService)
        service._mist = MagicMock()
        service._org_id = "org-123"
        service._db = MagicMock()
        service._mist.list_all_entities.return_value = _mock_api_result(
            [{"id": "site-1", "name": "HQ"}],
        )
        service._upsert_site = MagicMock()

        count = service._sync_sites(uuid4())

        service._mist.list_all_entities.assert_called_once_with(
            "org_site_list",
            ids={"org_id": "org-123"},
        )
        assert count == 1

    def test_sync_devices_calls_org_inventory(self) -> None:
        from src.worker.sync.inventory import InventorySyncService

        service = InventorySyncService.__new__(InventorySyncService)
        service._mist = MagicMock()
        service._org_id = "org-123"
        service._db = MagicMock()
        service._mist.list_all_entities.return_value = _mock_api_result(
            [{"id": "dev-1", "mac": "aabbcc"}],
        )
        service._upsert_device = MagicMock()

        count = service._sync_devices(uuid4())

        service._mist.list_all_entities.assert_called_once_with(
            "org_inventory",
            ids={"org_id": "org-123"},
        )
        assert count == 1
