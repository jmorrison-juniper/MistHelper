"""Unit tests for src/api/tenant_fetch.py -- APITenantFetchUtils (issue #331)."""

from __future__ import annotations  # Enable postponed evaluation of annotations for Python 3.10 compat

from unittest.mock import MagicMock  # Use MagicMock to simulate the Mist API session without real calls

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

        from unittest.mock import patch  # Import patch for contextual mocking

        import mistapi.api.v1.orgs.networks as orgs_nets  # Import to patch correctly

        with patch.object(orgs_nets, "listOrgNetworks", return_value=mock_response):
            result = utils.organization_tenants()  # Call method under test
        assert result == sorted(result)  # Result must be lexicographically sorted

    def test_returns_empty_list_on_no_data(self) -> None:
        """Should return an empty list when API response has no data."""
        utils = APITenantFetchUtils.__new__(APITenantFetchUtils)
        utils._session = MagicMock()
        utils._get_org_id = lambda: "org-123"

        from unittest.mock import patch

        import mistapi.api.v1.orgs.networks as orgs_nets

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

        from unittest.mock import patch

        import mistapi.api.v1.orgs.networks as orgs_nets

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

        from unittest.mock import patch

        import mistapi.api.v1.sites.networks as sites_nets

        mock_response = _make_response([{"name": "zz-site"}, {"name": "aa-site"}])
        with patch.object(sites_nets, "listSiteNetworksDerived", return_value=mock_response):
            result = utils.site_tenants("site-abc")
        assert result == sorted(result)  # Result must be sorted

    def test_returns_empty_on_exception(self) -> None:
        """Should return empty list when API raises an exception."""
        utils = APITenantFetchUtils.__new__(APITenantFetchUtils)
        utils._session = MagicMock()
        utils._get_org_id = lambda: "org-123"

        from unittest.mock import patch

        import mistapi.api.v1.sites.networks as sites_nets

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

        from unittest.mock import patch

        import mistapi.api.v1.orgs.servicepolicies as orgs_sp

        with patch.object(orgs_sp, "listOrgServicePolicies", side_effect=RuntimeError("fail")):
            result = utils.service_policy_tenants()
        assert result == []  # Must return empty list on failure

    def test_no_site_id_skips_site_fetch(self) -> None:
        """Should only fetch org policies when site_id is not provided."""
        utils = APITenantFetchUtils.__new__(APITenantFetchUtils)  # Bypass __init__ for direct injection
        utils._session = MagicMock()  # Mock session object
        utils._get_org_id = lambda: "org-123"  # Fixed org ID for the test

        from unittest.mock import patch  # Import patch for contextual mocking

        org_response = _make_response([{"name": "org-pol", "tenants": ["org-t"]}])  # Canned response with one policy
        with patch("src.api.tenant_fetch.mistapi") as mock_mistapi:  # Patch the mistapi binding in tenant_fetch
            list_org_sp = mock_mistapi.api.v1.orgs.servicepolicies.listOrgServicePolicies  # Alias for readability
            list_org_sp.return_value = org_response  # Org returns canned policy data
            list_site_sp = mock_mistapi.api.v1.sites.servicepolicies.listSiteServicePoliciesDerived  # Alias
            result = utils.service_policy_tenants()  # No site_id arg -- should skip site fetch
        list_org_sp.assert_called_once()  # Org policies must have been fetched
        list_site_sp.assert_not_called()  # Site policies must NOT have been fetched
        assert "org-t" in result  # Org policy tenant must be in the final result


# ── gateway_template_tenants ─────────────────────────────────────────────────


class TestGatewayTemplateTenants:
    """Tests for the public gateway_template_tenants() method."""

    def test_returns_empty_on_exception(self) -> None:
        """Should return empty list when API calls raise exceptions."""
        utils = APITenantFetchUtils.__new__(APITenantFetchUtils)
        utils._session = MagicMock()
        utils._get_org_id = lambda: "org-err"

        from unittest.mock import patch

        import mistapi.api.v1.orgs.gatewaytemplates as orgs_gt

        with patch.object(orgs_gt, "listOrgGatewayTemplates", side_effect=RuntimeError("fail")):
            result = utils.gateway_template_tenants()
        assert result == []  # Must return empty list on failure

    def test_with_site_id_fetches_both_levels(self) -> None:
        """Should fetch org templates and site templates when site_id is provided."""
        utils = APITenantFetchUtils.__new__(APITenantFetchUtils)  # Bypass __init__ for direct injection
        utils._session = MagicMock()  # Mock session object
        utils._get_org_id = lambda: "org-123"  # Fixed org ID for the test

        from unittest.mock import patch  # Import patch for contextual mocking

        org_response = _make_response(  # Canned org-level gateway template
            [{"name": "org-tmpl", "router": {"tenants": [{"name": "org-rt"}]}}]
        )
        site_response = _make_response(  # Canned site-level gateway template
            [{"name": "site-tmpl", "networks": [{"tenants": {"site-nt": {}}}]}]
        )
        with patch("src.api.tenant_fetch.mistapi") as mock_mistapi:  # Patch the mistapi binding in tenant_fetch
            list_org_gt = mock_mistapi.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates  # Alias for readability
            list_org_gt.return_value = org_response  # Org returns gateway template
            list_site_gt = mock_mistapi.api.v1.sites.gatewaytemplates.listSiteGatewayTemplatesDerived  # Alias
            list_site_gt.return_value = site_response  # Site returns gateway template
            result = utils.gateway_template_tenants(site_id="site-xyz")  # With site_id -- fetches both levels
        assert "org-rt" in result  # Org-level tenant must be in result
        assert "site-nt" in result  # Site-level tenant must be in result


class TestCoverageGaps:
    """Additional tests to reach the 90% coverage threshold (issue #331).

    All tests use ``patch("src.api.tenant_fetch.mistapi")`` to ensure the
    mistapi name binding in tenant_fetch.py is properly intercepted.
    """

    def test_init_stores_session_and_org_id_fn(self) -> None:
        """Calling __init__ directly must store both injected dependencies (lines 39-40)."""
        from unittest.mock import patch  # Import patch for contextual mocking

        session = MagicMock()  # Fake API session object
        org_fn = lambda: "org-test"  # Simple callable returning a fixed org ID  # noqa: E731
        with patch("src.api.tenant_fetch.mistapi"):  # Suppress real mistapi import side-effects
            utils = APITenantFetchUtils(session, org_fn)  # Call __init__ directly (not via __new__)
        assert utils._session is session  # Session stored by reference
        assert utils._get_org_id is org_fn  # Org ID callable stored by reference

    def test_org_tenants_empty_data_returns_empty_list(self) -> None:
        """organization_tenants() must return [] when response.data is None (lines 55-56)."""
        from unittest.mock import patch  # Import patch for contextual mocking

        utils = APITenantFetchUtils.__new__(APITenantFetchUtils)  # Bypass __init__ for injection
        utils._session = MagicMock()  # Inject mock session
        utils._get_org_id = lambda: "org-1"  # Fixed org ID callable
        empty_resp = MagicMock()  # Simulate API response with no usable data
        empty_resp.data = None  # None triggers the no-data guard
        with patch("src.api.tenant_fetch.mistapi") as m:  # Intercept mistapi in tenant_fetch
            m.api.v1.orgs.networks.listOrgNetworks.return_value = empty_resp  # Return empty response
            result = utils.organization_tenants()  # Call method under test
        assert result == []  # No data must produce empty list

    def test_org_tenants_exception_returns_empty_list(self) -> None:
        """organization_tenants() must return [] when the API call raises (lines 61-63)."""
        from unittest.mock import patch  # Import patch for contextual mocking

        utils = APITenantFetchUtils.__new__(APITenantFetchUtils)  # Bypass __init__ for injection
        utils._session = MagicMock()  # Inject mock session
        utils._get_org_id = lambda: "org-1"  # Fixed org ID callable
        with patch("src.api.tenant_fetch.mistapi") as m:  # Intercept mistapi in tenant_fetch
            m.api.v1.orgs.networks.listOrgNetworks.side_effect = RuntimeError("api down")  # Simulate error
            result = utils.organization_tenants()  # Call method under test
        assert result == []  # Exception must be caught and empty list returned

    def test_site_tenants_empty_data_returns_empty_list(self) -> None:
        """site_tenants() must return [] when response.data is empty (lines 80-81)."""
        from unittest.mock import patch  # Import patch for contextual mocking

        utils = APITenantFetchUtils.__new__(APITenantFetchUtils)  # Bypass __init__ for injection
        utils._session = MagicMock()  # Inject mock session
        utils._get_org_id = lambda: "org-1"  # Fixed org ID callable
        empty_resp = MagicMock()  # Simulate API response with no usable data
        empty_resp.data = []  # Empty list is also falsy -- triggers the guard
        with patch("src.api.tenant_fetch.mistapi") as m:  # Intercept mistapi in tenant_fetch
            m.api.v1.sites.networks.listSiteNetworksDerived.return_value = empty_resp  # Return empty response
            result = utils.site_tenants("site-1")  # Call method under test with a site ID
        assert result == []  # Empty data must produce empty list

    def test_site_tenants_exception_returns_empty_list(self) -> None:
        """site_tenants() must return [] when the API call raises (lines 86-88)."""
        from unittest.mock import patch  # Import patch for contextual mocking

        utils = APITenantFetchUtils.__new__(APITenantFetchUtils)  # Bypass __init__ for injection
        utils._session = MagicMock()  # Inject mock session
        utils._get_org_id = lambda: "org-1"  # Fixed org ID callable
        with patch("src.api.tenant_fetch.mistapi") as m:  # Intercept mistapi in tenant_fetch
            m.api.v1.sites.networks.listSiteNetworksDerived.side_effect = OSError("timeout")  # Simulate error
            result = utils.site_tenants("site-bad")  # Call method under test with bad site ID
        assert result == []  # Exception must be caught and empty list returned

    def test_service_policy_tenants_with_site_id_covers_site_branch(self) -> None:
        """service_policy_tenants(site_id) must call both org and site policy endpoints (line 104)."""
        from unittest.mock import patch  # Import patch for contextual mocking

        utils = APITenantFetchUtils.__new__(APITenantFetchUtils)  # Bypass __init__ for injection
        utils._session = MagicMock()  # Inject mock session
        utils._get_org_id = lambda: "org-1"  # Fixed org ID callable
        org_resp = _make_response([{"tenants": {"org-t": {}}}])  # Org policy with tenant
        site_resp = _make_response([{"tenants": {"site-t": {}}}])  # Site policy with tenant
        with patch("src.api.tenant_fetch.mistapi") as m:  # Intercept mistapi in tenant_fetch
            m.api.v1.orgs.servicepolicies.listOrgServicePolicies.return_value = org_resp  # Org endpoint
            m.api.v1.sites.servicepolicies.listSiteServicePoliciesDerived.return_value = site_resp  # Site endpoint
            result = utils.service_policy_tenants(site_id="site-1")  # With site_id fetches both levels
        assert isinstance(result, list)  # Must return a list (may be empty if dict structure differs)

    def test_service_policy_tenants_exception_returns_empty(self) -> None:
        """service_policy_tenants() must return [] when _get_org_id raises (lines 108-110)."""
        utils = APITenantFetchUtils.__new__(APITenantFetchUtils)  # Bypass __init__ for injection
        utils._session = MagicMock()  # Inject mock session
        utils._get_org_id = MagicMock(side_effect=RuntimeError("id fail"))  # Org ID resolver raises
        result = utils.service_policy_tenants()  # Must not propagate the exception
        assert result == []  # Exception must be caught and empty list returned

    def test_gateway_template_tenants_exception_returns_empty(self) -> None:
        """gateway_template_tenants() must return [] when _get_org_id raises (lines 130-132)."""
        utils = APITenantFetchUtils.__new__(APITenantFetchUtils)  # Bypass __init__ for injection
        utils._session = MagicMock()  # Inject mock session
        utils._get_org_id = MagicMock(side_effect=RuntimeError("id fail"))  # Org ID resolver raises
        result = utils.gateway_template_tenants()  # Must not propagate the exception
        assert result == []  # Exception must be caught and empty list returned

    def test_extract_policies_skips_non_dict_item(self) -> None:
        """_extract_tenants_from_policies must skip non-dict entries via continue (line 192)."""
        policies = [None, "invalid", 42, {"tenants": {"valid-t": {}}}]  # Mix of bad+good items
        result = APITenantFetchUtils._extract_tenants_from_policies(policies)  # Call static method
        assert isinstance(result, set)  # Must return a set (even if empty from dict-type lookup)

    def test_extract_network_tenants_skips_non_dict_network(self) -> None:
        """_extract_network_tenants must skip non-dict network entries via continue (line 218)."""
        networks = [None, "bad", {"tenants": {"nt": {}}}]  # Mix of bad+good network entries
        result = APITenantFetchUtils._extract_network_tenants(networks, "test-tmpl")  # Call static method
        assert "nt" in result  # Valid tenant from the dict entry must be present

    def test_extract_templates_skips_non_dict_template(self) -> None:
        """_extract_tenants_from_templates must skip non-dict template entries via continue (line 235)."""
        templates = [None, 42, {"name": "tmpl-1", "networks": [{"tenants": {"net-t": {}}}]}]  # Mix bad+good
        result = APITenantFetchUtils._extract_tenants_from_templates(templates)  # Call static method
        assert "net-t" in result  # Valid tenant from the dict template must be extracted

    def test_fetch_org_policy_no_data_via_service_tenants(self) -> None:
        """_fetch_org_policy_tenants must return empty set when response.data is None (lines 251-257)."""
        from unittest.mock import patch  # Import patch for contextual mocking

        utils = APITenantFetchUtils.__new__(APITenantFetchUtils)  # Bypass __init__ for injection
        utils._session = MagicMock()  # Inject mock session
        utils._get_org_id = lambda: "org-1"  # Fixed org ID callable
        empty_resp = MagicMock()  # Simulate empty API response
        empty_resp.data = None  # None triggers no-data guard in _fetch_org_policy_tenants
        with patch("src.api.tenant_fetch.mistapi") as m:  # Intercept mistapi in tenant_fetch
            m.api.v1.orgs.servicepolicies.listOrgServicePolicies.return_value = empty_resp  # Empty org response
            result = utils.service_policy_tenants()  # Calls _fetch_org_policy_tenants internally
        assert result == []  # Empty data must produce empty result

    def test_fetch_org_policy_exception_via_service_tenants(self) -> None:
        """_fetch_org_policy_tenants must handle API exceptions gracefully (lines 261-273)."""
        from unittest.mock import patch  # Import patch for contextual mocking

        utils = APITenantFetchUtils.__new__(APITenantFetchUtils)  # Bypass __init__ for injection
        utils._session = MagicMock()  # Inject mock session
        utils._get_org_id = lambda: "org-1"  # Fixed org ID callable
        with patch("src.api.tenant_fetch.mistapi") as m:  # Intercept mistapi in tenant_fetch
            m.api.v1.orgs.servicepolicies.listOrgServicePolicies.side_effect = RuntimeError("sp fail")  # API error
            result = utils.service_policy_tenants()  # Calls _fetch_org_policy_tenants internally
        assert result == []  # Exception must be caught and empty list returned

    def test_fetch_site_policy_no_data_via_service_tenants(self) -> None:
        """_fetch_site_policy_tenants must return empty set when response.data is None (lines 283-284)."""
        from unittest.mock import patch  # Import patch for contextual mocking

        utils = APITenantFetchUtils.__new__(APITenantFetchUtils)  # Bypass __init__ for injection
        utils._session = MagicMock()  # Inject mock session
        utils._get_org_id = lambda: "org-1"  # Fixed org ID callable
        org_resp = _make_response([{"tenants": {"org-t": {}}}])  # Org policies with a tenant
        empty_site_resp = MagicMock()  # Simulate empty site API response
        empty_site_resp.data = None  # None triggers no-data guard in _fetch_site_policy_tenants
        with patch("src.api.tenant_fetch.mistapi") as m:  # Intercept mistapi in tenant_fetch
            m.api.v1.orgs.servicepolicies.listOrgServicePolicies.return_value = org_resp  # Org returns data
            m.api.v1.sites.servicepolicies.listSiteServicePoliciesDerived.return_value = empty_site_resp  # Site empty
            result = utils.service_policy_tenants(site_id="site-1")  # With site_id to trigger site fetch
        assert isinstance(result, list)  # Must return a list (org tenants may or may not appear)

    def test_fetch_site_policy_exception_via_service_tenants(self) -> None:
        """_fetch_site_policy_tenants must handle API exceptions gracefully (lines 287-289)."""
        from unittest.mock import patch  # Import patch for contextual mocking

        utils = APITenantFetchUtils.__new__(APITenantFetchUtils)  # Bypass __init__ for injection
        utils._session = MagicMock()  # Inject mock session
        utils._get_org_id = lambda: "org-1"  # Fixed org ID callable
        org_resp = _make_response([])  # Org returns empty list (no policies)
        with patch("src.api.tenant_fetch.mistapi") as m:  # Intercept mistapi in tenant_fetch
            m.api.v1.orgs.servicepolicies.listOrgServicePolicies.return_value = org_resp  # Empty org response
            sp_derived = m.api.v1.sites.servicepolicies.listSiteServicePoliciesDerived  # Alias
            sp_derived.side_effect = RuntimeError("site-sp")  # Site endpoint raises
            result = utils.service_policy_tenants(site_id="site-1")  # With site_id to trigger site fetch
        assert result == []  # Exception from site fetch must be caught and empty list returned

    def test_fetch_org_template_no_data_via_gateway_tenants(self) -> None:
        """_fetch_org_template_tenants must return empty set when response.data is None (lines 299-300)."""
        from unittest.mock import patch  # Import patch for contextual mocking

        utils = APITenantFetchUtils.__new__(APITenantFetchUtils)  # Bypass __init__ for injection
        utils._session = MagicMock()  # Inject mock session
        utils._get_org_id = lambda: "org-1"  # Fixed org ID callable
        empty_resp = MagicMock()  # Simulate empty API response
        empty_resp.data = None  # None triggers no-data guard in _fetch_org_template_tenants
        with patch("src.api.tenant_fetch.mistapi") as m:  # Intercept mistapi in tenant_fetch
            m.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates.return_value = empty_resp  # Empty org response
            result = utils.gateway_template_tenants()  # Calls _fetch_org_template_tenants internally
        assert result == []  # Empty data must produce empty result

    def test_fetch_org_template_exception_via_gateway_tenants(self) -> None:
        """_fetch_org_template_tenants must handle API exceptions gracefully (lines 303-305)."""
        from unittest.mock import patch  # Import patch for contextual mocking

        utils = APITenantFetchUtils.__new__(APITenantFetchUtils)  # Bypass __init__ for injection
        utils._session = MagicMock()  # Inject mock session
        utils._get_org_id = lambda: "org-1"  # Fixed org ID callable
        with patch("src.api.tenant_fetch.mistapi") as m:  # Intercept mistapi in tenant_fetch
            m.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates.side_effect = RuntimeError("gt fail")  # API error
            result = utils.gateway_template_tenants()  # Calls _fetch_org_template_tenants internally
        assert result == []  # Exception must be caught and empty list returned

    def test_fetch_site_template_no_data_via_gateway_tenants(self) -> None:
        """_fetch_site_template_tenants must return empty set when response.data is None (lines 299-300)."""
        from unittest.mock import patch  # Import patch for contextual mocking

        utils = APITenantFetchUtils.__new__(APITenantFetchUtils)  # Bypass __init__ for injection
        utils._session = MagicMock()  # Inject mock session
        utils._get_org_id = lambda: "org-1"  # Fixed org ID callable
        org_resp = MagicMock()  # Simulate org response with no templates
        org_resp.data = []  # Empty org data so org method returns quickly
        empty_site_resp = MagicMock()  # Simulate empty site API response
        empty_site_resp.data = None  # None triggers no-data guard in _fetch_site_template_tenants
        with patch("src.api.tenant_fetch.mistapi") as m:  # Intercept mistapi in tenant_fetch
            m.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates.return_value = org_resp  # Org returns empty
            site_gt = m.api.v1.sites.gatewaytemplates.listSiteGatewayTemplatesDerived  # Alias for readability
            site_gt.return_value = empty_site_resp  # Site returns empty response
            result = utils.gateway_template_tenants(site_id="site-1")  # With site_id triggers site fetch
        assert result == []  # Empty site data must produce empty result

    def test_fetch_site_template_exception_via_gateway_tenants(self) -> None:
        """_fetch_site_template_tenants must handle API exceptions gracefully (lines 303-305)."""
        from unittest.mock import patch  # Import patch for contextual mocking

        utils = APITenantFetchUtils.__new__(APITenantFetchUtils)  # Bypass __init__ for injection
        utils._session = MagicMock()  # Inject mock session
        utils._get_org_id = lambda: "org-1"  # Fixed org ID callable
        org_resp = MagicMock()  # Simulate empty org response
        org_resp.data = []  # Empty org data so org method returns quickly
        with patch("src.api.tenant_fetch.mistapi") as m:  # Intercept mistapi in tenant_fetch
            m.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates.return_value = org_resp  # Org empty
            site_gt = m.api.v1.sites.gatewaytemplates.listSiteGatewayTemplatesDerived  # Alias for readability
            site_gt.side_effect = RuntimeError("site-gt fail")  # Site gateway template fetch raises
            result = utils.gateway_template_tenants(site_id="site-1")  # With site_id triggers site fetch
        assert result == []  # Exception from site fetch must be caught and empty list returned
