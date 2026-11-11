"""Unit tests for APICoreFetchUtils (issue #878 tranche 2 -- un-omit).

Covers all three static methods of the extracted core fetch helper:
``all_sites_with_limit``, ``all_inventory_with_limit`` and
``get_api_response_data``.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.foundation.runtime.config import runtime_settings
from src.mist.access.api.api_core_fetch_utils import APICoreFetchUtils, APIFetchError

# ---------- all_sites_with_limit ----------


def test_all_sites_with_limit_calls_list_org_sites_and_paginates() -> None:
    """all_sites_with_limit must call listOrgSites then delegate to get_all."""
    fake_mh = SimpleNamespace(apisession="session-obj")
    initial_response = MagicMock(name="listOrgSitesResponse")
    initial_response.status = 200  # Success status.
    paginated_sites = [{"id": "s1"}, {"id": "s2"}]
    fake_mistapi = MagicMock(name="mistapi")
    fake_mistapi.api.v1.orgs.sites.listOrgSites.return_value = initial_response
    fake_mistapi.get_all.return_value = paginated_sites

    with (
        patch("src.mist.access.api.api_core_fetch_utils.mistapi", fake_mistapi),
        patch("src.mist.access.api.api_core_fetch_utils.SourceDependencyResolver", fake_mh),
        patch.object(runtime_settings, "DEFAULT_API_PAGE_LIMIT", 500),
    ):
        result = APICoreFetchUtils.all_sites_with_limit("org-uuid")

    fake_mistapi.api.v1.orgs.sites.listOrgSites.assert_called_once_with("session-obj", "org-uuid", limit=500)
    fake_mistapi.get_all.assert_called_once_with(response=initial_response, mist_session="session-obj")
    assert result == paginated_sites


def test_all_sites_with_limit_raises_on_http_403() -> None:
    """all_sites_with_limit must raise APIFetchError on HTTP 403."""
    fake_mh = SimpleNamespace(apisession="session-obj")
    error_response = MagicMock(name="listOrgSitesError")
    error_response.status = 403  # Forbidden.
    fake_mistapi = MagicMock(name="mistapi")
    fake_mistapi.api.v1.orgs.sites.listOrgSites.return_value = error_response

    with (
        patch("src.mist.access.api.api_core_fetch_utils.mistapi", fake_mistapi),
        patch("src.mist.access.api.api_core_fetch_utils.SourceDependencyResolver", fake_mh),
        patch.object(runtime_settings, "DEFAULT_API_PAGE_LIMIT", 500),
    ):
        with pytest.raises(APIFetchError, match="HTTP 403"):
            APICoreFetchUtils.all_sites_with_limit("org-uuid")

    fake_mistapi.api.v1.orgs.sites.listOrgSites.assert_called_once()
    fake_mistapi.get_all.assert_not_called()  # Should not reach pagination on error.


def test_all_sites_with_limit_raises_on_http_503() -> None:
    """all_sites_with_limit must raise APIFetchError on HTTP 503."""
    fake_mh = SimpleNamespace(apisession="session-obj")
    error_response = MagicMock(name="listOrgSitesError")
    error_response.status = 503  # Service unavailable.
    fake_mistapi = MagicMock(name="mistapi")
    fake_mistapi.api.v1.orgs.sites.listOrgSites.return_value = error_response

    with (
        patch("src.mist.access.api.api_core_fetch_utils.mistapi", fake_mistapi),
        patch("src.mist.access.api.api_core_fetch_utils.SourceDependencyResolver", fake_mh),
        patch.object(runtime_settings, "DEFAULT_API_PAGE_LIMIT", 500),
    ):
        with pytest.raises(APIFetchError, match="HTTP 503"):
            APICoreFetchUtils.all_sites_with_limit("org-uuid")


# ---------- all_inventory_with_limit ----------


def test_all_inventory_with_limit_requests_vc_members_and_paginates() -> None:
    """all_inventory_with_limit must pass vc=True and paginate through get_all."""
    fake_mh = SimpleNamespace(apisession="session-obj")
    initial_response = MagicMock(name="getOrgInventoryResponse")
    initial_response.status = 200  # Success status.
    paginated_inventory = [{"mac": "aa"}, {"mac": "bb"}]
    fake_mistapi = MagicMock(name="mistapi")
    fake_mistapi.api.v1.orgs.inventory.getOrgInventory.return_value = initial_response
    fake_mistapi.get_all.return_value = paginated_inventory

    with (
        patch("src.mist.access.api.api_core_fetch_utils.mistapi", fake_mistapi),
        patch("src.mist.access.api.api_core_fetch_utils.SourceDependencyResolver", fake_mh),
        patch.object(runtime_settings, "DEFAULT_API_PAGE_LIMIT", 250),
    ):
        result = APICoreFetchUtils.all_inventory_with_limit("org-uuid")

    fake_mistapi.api.v1.orgs.inventory.getOrgInventory.assert_called_once_with(
        "session-obj", "org-uuid", vc=True, limit=250
    )
    fake_mistapi.get_all.assert_called_once_with(response=initial_response, mist_session="session-obj")
    assert result == paginated_inventory


def test_all_inventory_with_limit_raises_on_http_403() -> None:
    """all_inventory_with_limit must raise APIFetchError on HTTP 403."""
    fake_mh = SimpleNamespace(apisession="session-obj")
    error_response = MagicMock(name="getOrgInventoryError")
    error_response.status = 403  # Forbidden.
    fake_mistapi = MagicMock(name="mistapi")
    fake_mistapi.api.v1.orgs.inventory.getOrgInventory.return_value = error_response

    with (
        patch("src.mist.access.api.api_core_fetch_utils.mistapi", fake_mistapi),
        patch("src.mist.access.api.api_core_fetch_utils.SourceDependencyResolver", fake_mh),
        patch.object(runtime_settings, "DEFAULT_API_PAGE_LIMIT", 250),
    ):
        with pytest.raises(APIFetchError, match="HTTP 403"):
            APICoreFetchUtils.all_inventory_with_limit("org-uuid")

    fake_mistapi.get_all.assert_not_called()  # Should not reach pagination on error.


def test_all_inventory_with_limit_raises_on_http_503() -> None:
    """all_inventory_with_limit must raise APIFetchError on HTTP 503."""
    fake_mh = SimpleNamespace(apisession="session-obj")
    error_response = MagicMock(name="getOrgInventoryError")
    error_response.status = 503  # Service unavailable.
    fake_mistapi = MagicMock(name="mistapi")
    fake_mistapi.api.v1.orgs.inventory.getOrgInventory.return_value = error_response

    with (
        patch("src.mist.access.api.api_core_fetch_utils.mistapi", fake_mistapi),
        patch("src.mist.access.api.api_core_fetch_utils.SourceDependencyResolver", fake_mh),
        patch.object(runtime_settings, "DEFAULT_API_PAGE_LIMIT", 250),
    ):
        with pytest.raises(APIFetchError, match="HTTP 503"):
            APICoreFetchUtils.all_inventory_with_limit("org-uuid")


# ---------- get_api_response_data ----------


def test_get_api_response_data_returns_data_attribute_when_present() -> None:
    """When response has a .data attribute the helper returns it."""
    response = SimpleNamespace(data={"payload": True})
    assert APICoreFetchUtils.get_api_response_data(response) == {"payload": True}


def test_get_api_response_data_falls_back_to_response_when_data_missing() -> None:
    """When response has no .data attribute the raw object flows through."""
    raw = {"just": "a dict"}
    assert APICoreFetchUtils.get_api_response_data(raw) is raw


def test_get_api_response_data_returns_none_when_data_is_none() -> None:
    """A .data attribute set to None is returned verbatim (no fallback swap)."""
    response = SimpleNamespace(data=None)
    assert APICoreFetchUtils.get_api_response_data(response) is None

