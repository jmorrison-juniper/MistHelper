"""Tests for list_all_entities pagination (T005)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.shared.mist.endpoints import ApiResult, MistEndpointService
from src.shared.mist.types import MistEndpoint, MistEntityRegistry


def _make_response(data: list, next_url: str | None = None) -> SimpleNamespace:
    """Create a mock SDK response object."""
    resp = SimpleNamespace(status_code=200, data=data)
    if next_url:
        resp.next = next_url
    else:
        resp.next = None
    return resp


class TestListAllEntitiesPagination:
    """Verify list_all_entities follows response.next across pages."""

    def test_single_page(self) -> None:
        session = MagicMock()
        service = MistEndpointService(session)
        mock_func = MagicMock(return_value=_make_response([{"id": "a"}]))

        with patch.object(service, "_resolve_func", return_value=mock_func):
            with patch.object(
                MistEntityRegistry,
                "get",
                return_value=MistEndpoint(
                    entity_type="org_site_list",
                    api_module="orgs.sites",
                    read_method=None,
                    write_method=None,
                    id_params=("org_id",),
                    list_method="listOrgSites",
                ),
            ):
                result = service.list_all_entities("org_site_list", {"org_id": "test-org"})

        assert result.status_code == 200
        assert result.data == [{"id": "a"}]
        assert mock_func.call_count == 1

    def test_three_pages(self) -> None:
        session = MagicMock()
        service = MistEndpointService(session)

        page1 = _make_response([{"id": "a"}], next_url="/page2")
        page2 = _make_response([{"id": "b"}], next_url="/page3")
        page3 = _make_response([{"id": "c"}])

        mock_func = MagicMock(side_effect=[page1, page2, page3])

        with patch.object(service, "_resolve_func", return_value=mock_func):
            with patch.object(
                MistEntityRegistry,
                "get",
                return_value=MistEndpoint(
                    entity_type="org_site_list",
                    api_module="orgs.sites",
                    read_method=None,
                    write_method=None,
                    id_params=("org_id",),
                    list_method="listOrgSites",
                ),
            ):
                result = service.list_all_entities("org_site_list", {"org_id": "test-org"})

        assert result.status_code == 200
        assert len(result.data) == 3
        assert result.data == [{"id": "a"}, {"id": "b"}, {"id": "c"}]
        assert mock_func.call_count == 3

    def test_empty_response(self) -> None:
        session = MagicMock()
        service = MistEndpointService(session)
        mock_func = MagicMock(return_value=_make_response([]))

        with patch.object(service, "_resolve_func", return_value=mock_func):
            with patch.object(
                MistEntityRegistry,
                "get",
                return_value=MistEndpoint(
                    entity_type="org_site_list",
                    api_module="orgs.sites",
                    read_method=None,
                    write_method=None,
                    id_params=("org_id",),
                    list_method="listOrgSites",
                ),
            ):
                result = service.list_all_entities("org_site_list", {"org_id": "test-org"})

        assert result.data == []

    def test_no_list_method_raises(self) -> None:
        session = MagicMock()
        service = MistEndpointService(session)

        with patch.object(
            MistEntityRegistry,
            "get",
            return_value=MistEndpoint(
                entity_type="device",
                api_module="sites.devices",
                read_method="getSiteDevice",
                write_method="updateSiteDevice",
                id_params=("site_id", "device_id"),
            ),
        ):
            with pytest.raises(AttributeError, match="No list_method"):
                service.list_all_entities("device", {"site_id": "s1", "device_id": "d1"})
