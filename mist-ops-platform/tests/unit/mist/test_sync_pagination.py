"""Tests verifying sync services retrieve all pages (T021 / US4).

Mock multi-page responses for org_site_list, org_inventory, and audit_log
to confirm list_all_entities pagination is used end-to-end.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4


def _api_result(data: list) -> SimpleNamespace:
    # The sync services read .success before they read .data (issue #1884).
    return SimpleNamespace(status_code=200, data=data, success=True)


class TestInventorySyncPagination:
    """inventory.py sync methods must get all pages via list_all_entities."""

    def test_sync_sites_gets_all_pages(self) -> None:
        from src.worker.sync.inventory import InventorySyncService

        service = InventorySyncService.__new__(InventorySyncService)
        service._mist = MagicMock()
        service._org_id = "org-1"
        service._db = MagicMock()
        service._upsert_site = MagicMock()

        all_sites = [{"id": f"s{i}", "name": f"Site {i}"} for i in range(250)]
        service._mist.list_all_entities.return_value = _api_result(all_sites)

        count = service._sync_sites(uuid4())

        assert count == 250
        assert service._upsert_site.call_count == 250
        service._mist.list_all_entities.assert_called_once_with(
            "org_site_list",
            ids={"org_id": "org-1"},
        )

    def test_sync_devices_gets_all_pages(self) -> None:
        from src.worker.sync.inventory import InventorySyncService

        service = InventorySyncService.__new__(InventorySyncService)
        service._mist = MagicMock()
        service._org_id = "org-1"
        service._db = MagicMock()
        service._upsert_device = MagicMock()

        all_devices = [{"id": f"d{i}", "mac": f"aa:bb:{i:04d}"} for i in range(300)]
        service._mist.list_all_entities.return_value = _api_result(
            all_devices,
        )

        count = service._sync_devices(uuid4())

        assert count == 300
        assert service._upsert_device.call_count == 300


class TestEventSyncPagination:
    """events.py sync must get all audit log pages via list_all_entities."""

    def test_fetch_events_gets_all_pages(self) -> None:
        from src.worker.sync.events import EventSyncService

        service = EventSyncService.__new__(EventSyncService)
        service._mist = MagicMock()
        service._org_id = str(uuid4())

        all_events = [{"id": f"e{i}", "message": f"event {i}"} for i in range(150)]
        service._mist.list_all_entities.return_value = _api_result(all_events)

        result = service._fetch_events()

        assert len(result) == 150
        service._mist.list_all_entities.assert_called_once_with(
            "audit_log",
            ids={"org_id": service._org_id},
        )
