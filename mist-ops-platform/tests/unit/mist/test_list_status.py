"""Tests for the status and the page cap of list_all_entities (issue #1884).

The tests cover three defects. The first defect reported a hardcoded status
of 200 for every list call. The second defect turned a Mist error body into
one data record. The third defect let a repeated page token loop without an
end.
"""

from __future__ import annotations

import importlib
import logging
import sys
from enum import Enum
from types import ModuleType, SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest

from src.shared.mist.endpoints import (
    MAX_429_RETRIES,
    MAX_PAGINATION_PAGES,
    ApiResult,
    MistEndpointService,
)
from src.shared.mist.types import MistEndpoint, MistEntityRegistry

ORG_UUID = UUID("11111111-1111-1111-1111-111111111111")

STATUS_OK = 200
STATUS_UNAUTHORIZED = 401
STATUS_RATE_LIMIT = 429
EXPECTED_CALLS = 2
EXPECTED_SITES = 2

SITE_LIST_ENDPOINT = MistEndpoint(
    entity_type="org_site_list",
    api_module="orgs.sites",
    read_method=None,
    write_method=None,
    id_params=("org_id",),
    list_method="listOrgSites",
)


def _response(
    data: Any,
    status: int = STATUS_OK,
    next_token: str | None = None,
) -> SimpleNamespace:
    """Build a mock SDK response with a status, a body, and a page token."""
    return SimpleNamespace(status_code=status, data=data, next=next_token)


def _list_sites(service: MistEndpointService, func: MagicMock) -> Any:
    """Run list_all_entities against a mock SDK function."""
    with (
        patch.object(service, "_resolve_func", return_value=func),
        patch.object(MistEntityRegistry, "get", return_value=SITE_LIST_ENDPOINT),
    ):
        return service.list_all_entities("org_site_list", {"org_id": "org-1"})


class TestListAllEntitiesStatus:
    """list_all_entities must report the real status of the Mist call."""

    def test_error_status_is_reported(self) -> None:
        """A 429 page reports a failure and holds the Mist error body."""
        service = MistEndpointService(MagicMock())
        body = {"detail": "Too many requests"}
        func = MagicMock(return_value=_response(body, status=STATUS_RATE_LIMIT))

        result = _list_sites(service, func)

        assert result.status_code == STATUS_RATE_LIMIT
        assert result.success is False
        assert result.error == "Too many requests"
        assert result.data == body

    def test_error_body_is_not_a_data_record(self) -> None:
        """An error body must never appear as one data record."""
        service = MistEndpointService(MagicMock())
        body = {"detail": "Unauthorized"}
        func = MagicMock(return_value=_response(body, status=STATUS_UNAUTHORIZED))

        result = _list_sites(service, func)

        assert result.data != [body]

    def test_extract_list_drops_a_dict_body(self) -> None:
        """_extract_list returns no record for a dictionary body."""
        rows = MistEndpointService._extract_list(_response({"detail": "bad token"}))

        assert rows == []

    def test_success_keeps_the_real_status(self) -> None:
        """A 200 page reports 200 and holds every data record."""
        service = MistEndpointService(MagicMock())
        func = MagicMock(return_value=_response([{"id": "s1"}]))

        result = _list_sites(service, func)

        assert result.status_code == STATUS_OK
        assert result.data == [{"id": "s1"}]

    def test_late_page_failure_is_reported(self) -> None:
        """A failure on page two reports the failure of that page."""
        service = MistEndpointService(MagicMock())
        page1 = _response([{"id": "s1"}], next_token="/page2")
        # A 401 never retries. `_invoke_with_protection` retries a 429 up to
        # MAX_429_RETRIES times (issue #1886), so a 429 here would call the
        # mock four times and prove nothing about the reported status.
        page2 = _response({"detail": "Unauthorized"}, status=STATUS_UNAUTHORIZED)
        func = MagicMock(side_effect=[page1, page2])

        result = _list_sites(service, func)

        assert result.status_code == STATUS_UNAUTHORIZED
        assert result.success is False

    def test_exhausted_429_retries_report_the_failure(self) -> None:
        """A page that stays at 429 reports the failure once the retries run out."""
        service = MistEndpointService(MagicMock())
        page1 = _response([{"id": "s1"}], next_token="/page2")
        throttled = _response({"detail": "Too many requests"}, status=STATUS_RATE_LIMIT)
        # One call for page one, then MAX_429_RETRIES + 1 calls for page two.
        pages = [page1, *[throttled] * (MAX_429_RETRIES + 1)]
        func = MagicMock(side_effect=pages)

        with patch("src.shared.mist.endpoints.time.sleep"):  # skip the real backoff wait
            result = _list_sites(service, func)

        assert result.status_code == STATUS_RATE_LIMIT
        assert result.success is False


class TestPaginationLoopGuards:
    """The page loop must stop on a repeated cursor and at the page cap.

    `main` already owns both guards through `_accept_cursor` and
    `MAX_PAGINATION_PAGES` (issue #1903), so these cases pin the guards that
    the module already holds instead of adding a second cap.
    """

    def test_repeated_token_stops_the_loop(self, caplog: pytest.LogCaptureFixture) -> None:
        """An equal next cursor stops the loop and logs the reason."""
        service = MistEndpointService(MagicMock())
        page = _response([{"id": "s1"}], next_token="/same")
        func = MagicMock(return_value=page)

        with caplog.at_level(logging.WARNING, logger="src.shared.mist.endpoints"):
            result = _list_sites(service, func)

        assert func.call_count == EXPECTED_CALLS
        assert result.data == [{"id": "s1"}, {"id": "s1"}]
        assert "repeated a cursor" in caplog.text

    def test_page_cap_stops_the_loop(self, caplog: pytest.LogCaptureFixture) -> None:
        """A new cursor on every page stops the loop at the page cap."""
        service = MistEndpointService(MagicMock())
        pages = [_response([{"id": str(i)}], next_token=f"/page{i}") for i in range(1000)]
        func = MagicMock(side_effect=pages)

        with caplog.at_level(logging.WARNING, logger="src.shared.mist.endpoints"):
            result = _list_sites(service, func)

        assert func.call_count == MAX_PAGINATION_PAGES
        assert len(result.data) == MAX_PAGINATION_PAGES
        assert "page limit" in caplog.text


def _install_constants_stub() -> None:
    """Register a stub for src.shared.config.constants when it is absent.

    The config package is not present on this branch. The stub lets the
    inventory sync test import the module under test. If the real package
    exists, the stub is not used.
    """
    try:
        importlib.import_module("src.shared.config.constants")
    except ModuleNotFoundError:
        stub = ModuleType("src.shared.config.constants")
        stub.EntityType = Enum("EntityType", {"DEVICE": "device"})  # type: ignore[attr-defined]
        sys.modules.setdefault("src.shared.config", ModuleType("src.shared.config"))
        sys.modules["src.shared.config.constants"] = stub


def _inventory_module() -> Any:
    """Import the inventory sync module with the constants stub in place."""
    _install_constants_stub()
    return importlib.import_module("src.worker.sync.inventory")


def _inventory_service() -> Any:
    """Build an InventorySyncService with mock collaborators."""
    module = _inventory_module()
    service = module.InventorySyncService.__new__(module.InventorySyncService)
    service._mist = MagicMock()
    service._db = MagicMock()
    service._org_id = "org-1"
    service._upsert_site = MagicMock()
    service._upsert_device = MagicMock()
    return service


class TestInventorySyncRejectsFailures:
    """The inventory sync must write no row when the Mist call fails."""

    def test_sync_sites_writes_no_row_on_failure(self) -> None:
        """A 429 site list raises and writes no site row."""
        service = _inventory_service()
        module = _inventory_module()
        service._mist.list_all_entities.return_value = ApiResult(
            status_code=STATUS_RATE_LIMIT,
            data={"detail": "Too many requests"},
        )

        with pytest.raises(module.MistSyncError, match="429"):
            service._sync_sites(ORG_UUID)

        assert service._upsert_site.call_count == 0
        assert service._db.flush.call_count == 0

    def test_sync_devices_writes_no_row_on_failure(self) -> None:
        """A 401 device list raises and writes no device row."""
        service = _inventory_service()
        module = _inventory_module()
        service._mist.list_all_entities.return_value = ApiResult(
            status_code=STATUS_UNAUTHORIZED,
            data={"detail": "Unauthorized"},
        )

        with pytest.raises(module.MistSyncError, match="401"):
            service._sync_devices(ORG_UUID)

        assert service._upsert_device.call_count == 0
        assert service._db.flush.call_count == 0

    def test_sync_sites_writes_rows_on_success(self) -> None:
        """A successful site list writes one row for each site."""
        service = _inventory_service()
        service._mist.list_all_entities.return_value = ApiResult(
            status_code=STATUS_OK,
            data=[{"id": "s1"}, {"id": "s2"}],
        )

        count = service._sync_sites(ORG_UUID)

        assert count == EXPECTED_SITES
        assert service._upsert_site.call_count == EXPECTED_SITES
