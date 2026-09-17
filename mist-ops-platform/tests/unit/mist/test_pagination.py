"""Tests for list_all_entities pagination (T005)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.shared.mist.endpoints import ApiResult, MistEndpointService
from src.shared.mist.types import MistEndpoint, MistEntityRegistry

STATUS_OK = 200  # Name the healthy response code used by pagination helpers.
STATUS_FORBIDDEN = 403  # Name the HTTP 4xx response used to prove client-error handling.
STATUS_BAD_GATEWAY = 502  # Name the HTTP 5xx response used to prove server-error handling.
EXPECTED_THREE_PAGES = 3  # Name the multi-page count so assertions avoid magic values.


def _make_response(
    data: object,
    next_url: str | None = None,
    status: int = STATUS_OK,
) -> SimpleNamespace:
    """Create a mock SDK response object."""
    resp = SimpleNamespace(status_code=status, data=data)  # Keep status visible to the service.
    if next_url:
        resp.next = next_url
    else:
        resp.next = None
    return resp


def _endpoint() -> MistEndpoint:
    """Return the list endpoint used by these pagination tests."""
    return MistEndpoint(  # Keep one registry value so each test uses the same contract.
        entity_type="org_site_list",  # Name the entity that list_all_entities receives.
        api_module="orgs.sites",  # Keep the SDK module valid for this endpoint.
        read_method=None,  # A list-only endpoint needs no read method.
        write_method=None,  # A list-only endpoint needs no write method.
        id_params=("org_id",),  # Require the org identifier supplied by each test.
        list_method="listOrgSites",  # Name the SDK method patched by each test.
    )


def _list_sites(service: MistEndpointService, mock_func: MagicMock) -> ApiResult:
    """Call list_all_entities with the registry patched."""
    resolver_patch = patch.object(service, "_resolve_func", return_value=mock_func)  # Patch SDK.
    registry_patch = patch.object(  # Patch endpoint lookup.
        MistEntityRegistry,  # Patch the shared registry used by list_all_entities.
        "get",  # Replace only the lookup method for this test.
        return_value=_endpoint(),  # Return the same endpoint contract for every test.
    )
    with resolver_patch, registry_patch:  # Replace both lookups during the call.
        return service.list_all_entities("org_site_list", {"org_id": "test-org"})  # Run list.


class TestListAllEntitiesPagination:
    """Verify list_all_entities follows response.next across pages."""

    def test_single_page(self) -> None:
        session = MagicMock()
        service = MistEndpointService(session)
        mock_func = MagicMock(return_value=_make_response([{"id": "a"}]))

        result = _list_sites(service, mock_func)

        assert result.status_code == STATUS_OK
        assert result.data == [{"id": "a"}]
        assert mock_func.call_count == 1

    def test_three_pages(self) -> None:
        session = MagicMock()
        service = MistEndpointService(session)

        page1 = _make_response([{"id": "a"}], next_url="/page2")
        page2 = _make_response([{"id": "b"}], next_url="/page3")
        page3 = _make_response([{"id": "c"}])

        mock_func = MagicMock(side_effect=[page1, page2, page3])

        result = _list_sites(service, mock_func)

        assert result.status_code == STATUS_OK
        assert len(result.data) == EXPECTED_THREE_PAGES
        assert result.data == [{"id": "a"}, {"id": "b"}, {"id": "c"}]
        assert mock_func.call_count == EXPECTED_THREE_PAGES

    def test_empty_response(self) -> None:
        session = MagicMock()
        service = MistEndpointService(session)
        mock_func = MagicMock(return_value=_make_response([]))

        result = _list_sites(service, mock_func)

        assert result.data == []

    def test_http_4xx_response_returns_error_body(self) -> None:
        session = MagicMock()  # Avoid a live Mist session.
        service = MistEndpointService(session)  # Exercise real failure handling.
        body = {"detail": "Forbidden"}  # Keep the client-error signal visible.
        response = _make_response(body, status=STATUS_FORBIDDEN)  # Build the 403 response.
        mock_func = MagicMock(return_value=response)  # Return the client-error page.

        result = _list_sites(service, mock_func)  # Exercise the real list failure path.

        assert result.status_code == STATUS_FORBIDDEN  # The caller must see 403.
        assert result.success is False  # A client error must not look like a successful page.
        assert result.error == "Forbidden"  # The Mist error detail must remain observable.
        assert result.data == body  # The error body must not become a data record.

    def test_http_5xx_response_returns_error_body(self) -> None:
        session = MagicMock()  # Avoid a live Mist session.
        service = MistEndpointService(session)  # Exercise real failure handling.
        body = {"detail": "Bad gateway"}  # Keep the server-error signal visible.
        response = _make_response(body, status=STATUS_BAD_GATEWAY)  # Build the 502 response.
        mock_func = MagicMock(return_value=response)  # Return the server-error page.

        result = _list_sites(service, mock_func)  # Exercise the real list failure path.

        assert result.status_code == STATUS_BAD_GATEWAY  # The caller must see the HTTP 5xx status.
        assert result.success is False  # A server error must not look like a successful page.
        assert result.error == "Bad gateway"  # The Mist error detail must remain observable.
        assert result.data == body  # The error body must not become a data record.

    def test_no_list_method_raises(self) -> None:
        session = MagicMock()
        service = MistEndpointService(session)

        with (
            patch.object(
                MistEntityRegistry,
                "get",
                return_value=MistEndpoint(
                    entity_type="device",
                    api_module="sites.devices",
                    read_method="getSiteDevice",
                    write_method="updateSiteDevice",
                    id_params=("site_id", "device_id"),
                ),
            ),
            pytest.raises(AttributeError, match="No list_method"),
        ):
            service.list_all_entities("device", {"site_id": "s1", "device_id": "d1"})
