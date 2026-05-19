"""Unit tests for src/api/tenant_fetch.py -- APITenantFetchUtils (issue #331)."""

from __future__ import annotations  # Enable postponed evaluation of annotations for Python 3.10 compat

from unittest.mock import MagicMock  # Use MagicMock to simulate the Mist API session without real calls

import pytest  # Test framework providing fixtures and parametrize

from src.api.tenant_fetch import APITenantFetchUtils  # Class under test


# ── helpers ──────────────────────────────────────────────────────────────────


def _make_response(data: list) -> MagicMock:
    """Return a mock Mist API response object with a .data attribute."""
    response = MagicMock()  # Simulate the response object returned by mistapi
    response.data = data  # Set the data list that the methods inspect
    return response


def _make_utils(responses: dict | None = None) -> APITenantFetchUtils:
    """Build an APITenantFetchUtils with a mock session that returns canned responses.

    Args:
        responses: Optional dict mapping API function name to list of response dicts.
                   If None, the session returns an empty data list for every call.
    """
    session = MagicMock()  # Stand-in for the live Mist apisession object
    if responses:  # Configure per-function return values when provided
        for attr_path, data in responses.items():  # Each key is a dotted module path
            parts = attr_path.split(".")  # Walk the mock attribute chain
            target = session  # Start from the top-level mock session object
            for part in parts:  # Descend through each attribute level
                target = getattr(target, part)  # Create or retrieve the nested mock
            target.return_value = _make_response(data)  # Return our canned response
    else:  # Default: every call returns an empty data list
        session.return_value = _make_response([])
    return APITenantFetchUtils(session, lambda: "test-org-id")  # Inject a fixed org ID callable


# ── _extract_tenants_from_networks ────────────────────────────────────────────


class TestExtractTenantsFromNetworks:
    """Tests for the static helper that extracts tenants from network objects."""

    def test_returns_empty_on_empty_input(self) -> None:
        """Should return an empty set when given no network objects."""
        result = APITenantFetchUtils._extract_tenants_from_networks([])  # Call static helper directly
        assert result == set()  # Expect nothing from empty input

    def test_extracts_network_name(self) -> None:
        """Should include the network name itself as a tenant identifier."""
        networks = [{"name": "net-a", "tenants": {}}]  # One network with no explicit tenants
        result = APITenantFetchUtils._extract_tenants_from_networks(networks)
        assert "net-a" in result  # Network name must be in the result set

    def test_extracts_explicit_tenants(self) -> None:
        """Should extract keys from the explicit tenants dict."""
        networks = [{"name": "net-a", "tenants": {"tenant-1": {}, "tenant-2": {}}}]
        result = APITenantFetchUtils._extract_tenants_from_networks(networks)
        assert "tenant-1" in result  # Explicit tenant key must be in result
        assert "tenant-2" in result  # Both explicit tenant keys must be in result

    def test_skips_non_dict_entries(self) -> None:
        """Should silently skip non-dict items in the networks list."""
        networks = [None, "invalid", 42, {"name": "valid-net"}]  # Mix of valid and invalid
        result = APITenantFetchUtils._extract_tenants_from_networks(networks)
        assert "valid-net" in result  # Only the valid dict entry should contribute
        assert len(result) == 1  # Invalid entries produce nothing

    def test_ignores_non_dict_tenants_value(self) -> None:
        """Should tolerate a non-dict tenants value without raising an exception."""
        networks = [{"name": "net-b", "tenants": "not-a-dict"}]  # Malformed tenants field
        result = APITenantFetchUtils._extract_tenants_from_networks(networks)
        assert "net-b" in result  # Network name still extracted
        assert "not-a-dict" not in result  # Invalid tenants value should not be added


# ── _extract_tenants_from_policy_item ────────────────────────────────────────


class TestExtractTenantsFromPolicyItem:
    """Tests for the static helper that extracts tenants from one policy object."""

    def test_extracts_tenants_list(self) -> None:
        """Should extract all entries from the tenants list field."""
        policy = {"name": "p1", "tenants": ["t1", "t2"]}  # Modern list format
        result = APITenantFetchUtils._extract_tenants_from_policy_item(policy)
        assert result == {"t1", "t2"}  # Both list entries must be in the result

    def test_extracts_tenant_scalar(self) -> None:
        """Should extract the legacy scalar tenant field."""
        policy = {"name": "p2", "tenant": "legacy-tenant"}  # Legacy scalar field
        result = APITenantFetchUtils._extract_tenants_from_policy_item(policy)
        assert "legacy-tenant" in result  # Scalar tenant must be included

    def test_extracts_service_tenants(self) -> None:
        """Should extract tenant names nested inside services list items."""
        policy = {
            "name": "p3",
            "services": [{"tenant": "svc-tenant-1"}, {"tenant": "svc-tenant-2"}],
        }  # Services with per-item tenant references
        result = APITenantFetchUtils._extract_tenants_from_policy_item(policy)
        assert "svc-tenant-1" in result  # Service tenant 1 must be in result
        assert "svc-tenant-2" in result  # Service tenant 2 must be in result

    def test_empty_policy_returns_empty_set(self) -> None:
        """Should return an empty set for a policy with no tenant fields."""
        policy = {"name": "p-empty"}  # Policy with no tenant information
        result = APITenantFetchUtils._extract_tenants_from_policy_item(policy)
        assert result == set()  # No tenants means empty result


# ── _extract_tenants_from_policies ───────────────────────────────────────────


class TestExtractTenantsFromPolicies:
    """Tests for the aggregate policies extractor."""

    def test_aggregates_across_policies(self) -> None:
        """Should merge tenants from multiple policy objects."""
        policies = [
            {"name": "p1", "tenants": ["ta"]},  # First policy contributes 'ta'
            {"name": "p2", "tenants": ["tb"]},  # Second policy contributes 'tb'
        ]
        result = APITenantFetchUtils._extract_tenants_from_policies(policies)
        assert result == {"ta", "tb"}  # Both contributions must be present

    def test_deduplicates(self) -> None:
        """Should deduplicate tenant names appearing in multiple policies."""
        policies = [{"name": "p1", "tenants": ["shared"]}, {"name": "p2", "tenants": ["shared"]}]
        result = APITenantFetchUtils._extract_tenants_from_policies(policies)
        assert result == {"shared"}  # Duplicate should appear only once

    def test_returns_empty_on_empty_list(self) -> None:
        """Should return empty set when policy list is empty."""
        assert APITenantFetchUtils._extract_tenants_from_policies([]) == set()


# ── _extract_router_tenants ──────────────────────────────────────────────────


class TestExtractRouterTenants:
    """Tests for the static helper that extracts tenants from router config."""

    def test_extracts_named_tenants(self) -> None:
        """Should extract tenant names from router.tenants list."""
        router = {"tenants": [{"name": "rt1"}, {"name": "rt2"}]}  # Named tenant objects
        result = APITenantFetchUtils._extract_router_tenants(router, "tmpl-a")
        assert result == {"rt1", "rt2"}  # Both named tenants must be in result

    def test_extracts_tenant_profiles(self) -> None:
        """Should extract profile names from router.tenant_profiles dict keys."""
        router = {"tenant_profiles": {"profile-x": {}, "profile-y": {}}}  # Profile dict
        result = APITenantFetchUtils._extract_router_tenants(router, "tmpl-b")
        assert result == {"profile-x", "profile-y"}  # Both profile names must be in result

    def test_empty_router_returns_empty(self) -> None:
        """Should return empty set for a router with no tenant fields."""
        assert APITenantFetchUtils._extract_router_tenants({}, "tmpl-c") == set()


# ── _extract_network_tenants ─────────────────────────────────────────────────


class TestExtractNetworkTenants:
    """Tests for the static helper that extracts tenants from template network blocks."""

    def test_extracts_dict_keys_as_tenants(self) -> None:
        """Should extract tenant names from networks[].tenants dict keys."""
        networks = [{"tenants": {"nt1": {}, "nt2": {}}}]  # Dict keys are tenant names
        result = APITenantFetchUtils._extract_network_tenants(networks, "tmpl-d")
        assert result == {"nt1", "nt2"}  # Both dict keys must be in result

    def test_returns_empty_for_empty_list(self) -> None:
        """Should return empty set for an empty networks list."""
        assert APITenantFetchUtils._extract_network_tenants([], "tmpl-e") == set()


# ── _extract_tenants_from_templates ──────────────────────────────────────────


class TestExtractTenantsFromTemplates:
    """Tests for the aggregate templates extractor."""

    def test_extracts_router_and_network_tenants(self) -> None:
        """Should aggregate tenants from both router and network sub-structures."""
        templates = [
            {
                "name": "tmpl-full",
                "router": {
                    "tenants": [{"name": "router-t"}],
                    "tenant_profiles": {"profile-t": {}},
                },
                "networks": [{"tenants": {"net-t": {}}}],
            }
        ]  # Template with all three tenant location patterns
        result = APITenantFetchUtils._extract_tenants_from_templates(templates)
        assert {"router-t", "profile-t", "net-t"}.issubset(result)  # All three patterns extracted

    def test_returns_empty_for_empty_list(self) -> None:
        """Should return empty set for an empty templates list."""
        assert APITenantFetchUtils._extract_tenants_from_templates([]) == set()


# ── organization_tenants ─────────────────────────────────────────────────────


class TestOrganizationTenants:
    """Tests for the public organization_tenants() method."""

    def test_returns_sorted_list(self) -> None:
        """Should return tenant names as a sorted list."""
        utils = APITenantFetchUtils.__new__(APITenantFetchUtils)  # Bypass __init__ for direct injection
        utils._session = MagicMock()  # Mock session object
        utils._get_org_id = lambda: "org-123"  # Fixed org ID for the test
        # Configure the mock to return two networks with tenant names
        mock_response = _make_response([{"name": "zzz-net"}, {"name": "aaa-net"}])
        utils._session.return_value = mock_response  # Session call returns this response

        import mistapi.api.v1.orgs.networks as orgs_nets  # Import to patch correctly
        from unittest.mock import patch  # Import patch for contextual mocking

        with patch.object(orgs_nets, "listOrgNetworks", return_value=mock_response):
            result = utils.organization_tenants()  # Call method under test
        assert result == sorted(result)  # Result must be lexicographically sorted

    def test_returns_empty_list_on_no_data(self) -> None:
        """Should return an empty list when API response has no data."""
        utils = APITenantFetchUtils.__new__(APITenantFetchUtils)
        utils._session = MagicMock()
        utils._get_org_id = lambda: "org-123"

        import mistapi.api.v1.orgs.networks as orgs_nets
        from unittest.mock import patch

        empty_response = MagicMock()  # Create a response with empty data
        empty_response.data = None  # No data triggers the early-return guard
        with patch.object(orgs_nets, "listOrgNetworks", return_value=empty_response):
            result = utils.organization_tenants()
        assert result == []  # Empty data must return empty list

    def test_returns_empty_list_on_exception(self) -> None:
        """Should return an empty list when the API call raises an exception."""
        utils = APITenantFetchUtils.__new__(APITenantFetchUtils)
        utils._session = MagicMock()
        utils._get_org_id = lambda: "org-error"

        import mistapi.api.v1.orgs.networks as orgs_nets
        from unittest.mock import patch

        with patch.object(orgs_nets, "listOrgNetworks", side_effect=RuntimeError("API error")):
            result = utils.organization_tenants()  # Must not raise, must return empty
        assert result == []  # Exception must produce empty list, not a traceback


# ── site_tenants ─────────────────────────────────────────────────────────────


class TestSiteTenants:
    """Tests for the public site_tenants() method."""

    def test_returns_sorted_list(self) -> None:
        """Should return tenant names as a sorted list from site derived networks."""
        utils = APITenantFetchUtils.__new__(APITenantFetchUtils)
        utils._session = MagicMock()
        utils._get_org_id = lambda: "org-123"

        import mistapi.api.v1.sites.networks as sites_nets
        from unittest.mock import patch

        mock_response = _make_response([{"name": "zz-site"}, {"name": "aa-site"}])
        with patch.object(sites_nets, "listSiteNetworksDerived", return_value=mock_response):
            result = utils.site_tenants("site-abc")
        assert result == sorted(result)  # Result must be sorted

    def test_returns_empty_on_exception(self) -> None:
        """Should return empty list when API raises an exception."""
        utils = APITenantFetchUtils.__new__(APITenantFetchUtils)
        utils._session = MagicMock()
        utils._get_org_id = lambda: "org-123"

        import mistapi.api.v1.sites.networks as sites_nets
        from unittest.mock import patch

        with patch.object(sites_nets, "listSiteNetworksDerived", side_effect=OSError("timeout")):
            result = utils.site_tenants("site-bad")
        assert result == []  # Exception must not propagate


# ── service_policy_tenants ───────────────────────────────────────────────────


class TestServicePolicyTenants:
    """Tests for the public service_policy_tenants() method."""

    def test_returns_empty_on_exception(self) -> None:
        """Should return empty list when API calls raise exceptions."""
        utils = APITenantFetchUtils.__new__(APITenantFetchUtils)
        utils._session = MagicMock()
        utils._get_org_id = lambda: "org-err"

        import mistapi.api.v1.orgs.servicepolicies as orgs_sp
        from unittest.mock import patch

        with patch.object(orgs_sp, "listOrgServicePolicies", side_effect=RuntimeError("fail")):
            result = utils.service_policy_tenants()
        assert result == []  # Must return empty list on failure

    def test_no_site_id_skips_site_fetch(self) -> None:
        """Should only fetch org policies when site_id is not provided."""
        utils = APITenantFetchUtils.__new__(APITenantFetchUtils)
        utils._session = MagicMock()
        utils._get_org_id = lambda: "org-123"

        import mistapi.api.v1.orgs.servicepolicies as orgs_sp
        import mistapi.api.v1.sites.servicepolicies as sites_sp
        from unittest.mock import patch

        org_response = _make_response([{"name": "org-pol", "tenants": ["org-t"]}])
        with (
            patch.object(orgs_sp, "listOrgServicePolicies", return_value=org_response) as mock_org,
            patch.object(sites_sp, "listSiteServicePoliciesDerived") as mock_site,
        ):
            result = utils.service_policy_tenants()  # No site_id arg
        mock_org.assert_called_once()  # Org policies must have been fetched
        mock_site.assert_not_called()  # Site policies must NOT have been fetched
        assert "org-t" in result  # Org policy tenant must be in result


# ── gateway_template_tenants ─────────────────────────────────────────────────


class TestGatewayTemplateTenants:
    """Tests for the public gateway_template_tenants() method."""

    def test_returns_empty_on_exception(self) -> None:
        """Should return empty list when API calls raise exceptions."""
        utils = APITenantFetchUtils.__new__(APITenantFetchUtils)
        utils._session = MagicMock()
        utils._get_org_id = lambda: "org-err"

        import mistapi.api.v1.orgs.gatewaytemplates as orgs_gt
        from unittest.mock import patch

        with patch.object(orgs_gt, "listOrgGatewayTemplates", side_effect=RuntimeError("fail")):
            result = utils.gateway_template_tenants()
        assert result == []  # Must return empty list on failure

    def test_with_site_id_fetches_both_levels(self) -> None:
        """Should fetch org templates and site templates when site_id is provided."""
        utils = APITenantFetchUtils.__new__(APITenantFetchUtils)
        utils._session = MagicMock()
        utils._get_org_id = lambda: "org-123"

        import mistapi.api.v1.orgs.gatewaytemplates as orgs_gt
        import mistapi.api.v1.sites.gatewaytemplates as sites_gt
        from unittest.mock import patch

        org_response = _make_response([{"name": "org-tmpl", "router": {"tenants": [{"name": "org-rt"}]}}])
        site_response = _make_response([{"name": "site-tmpl", "networks": [{"tenants": {"site-nt": {}}}]}])
        with (
            patch.object(orgs_gt, "listOrgGatewayTemplates", return_value=org_response),
            patch.object(sites_gt, "listSiteGatewayTemplatesDerived", return_value=site_response),
        ):
            result = utils.gateway_template_tenants(site_id="site-xyz")
        assert "org-rt" in result  # Org-level tenant must be in result
        assert "site-nt" in result  # Site-level tenant must be in result
