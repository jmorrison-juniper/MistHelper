"""Tenant fetch utilities for Mist API operations.

src/api/tenant_fetch.py -- extracted from MistHelper.py to keep the monolith
under the 5-Item Rule limit (Wave 2 decomposition, issue #331).

Target audience: Junior NOC engineers -- every line has an inline comment.
"""

from __future__ import annotations  # Postpone annotation evaluation for forward-compat typing

import logging  # Standard-library logger used by every fetch method for observability
from collections.abc import Callable, Iterable  # Callable for injected resolver, Iterable for helpers
from typing import Any  # Generic type used for untyped mistapi response payloads

import mistapi.api.v1.orgs.gatewaytemplates  # Org gateway-template endpoint namespace
import mistapi.api.v1.orgs.networks  # Org networks endpoint namespace
import mistapi.api.v1.orgs.servicepolicies  # Org service-policies endpoint namespace
import mistapi.api.v1.sites.gatewaytemplates  # Site gateway-template endpoint namespace
import mistapi.api.v1.sites.networks  # Site networks endpoint namespace
import mistapi.api.v1.sites.servicepolicies  # Site service-policies endpoint namespace

_API_PAGE_LIMIT = 1000  # Standard pagination cap for org-level Mist list endpoints


def _add_valid_name(target: set[str], value: Any) -> None:  # Reusable single-value guard-and-insert
    """Add ``value`` to ``target`` only when it is a non-empty string identifier."""
    if isinstance(value, str) and value:  # Guard: reject None, empty strings, and non-string junk
        target.add(value)  # Safe to insert -- mistapi payloads occasionally carry ints or None


def _add_valid_names(target: set[str], values: Iterable[Any]) -> None:  # Bulk variant over any iterable
    """Add every non-empty string from ``values`` into ``target`` (dict keys, lists, sets)."""
    for value in values:  # Iterate any iterable; caller passes dict keys, lists, or generators
        _add_valid_name(target, value)  # Delegate per-item validity to keep logic single-sourced


class APITenantFetchUtils:  # Public class re-exported to MistHelper.py via the api package
    """Tenant fetch utilities for org, site, service policy, and gateway template scopes.

    Uses constructor injection for the Mist API session and org ID resolver callable
    to keep this module free of circular imports with MistHelper.py.

    Extracted from MistHelper.py for Wave 2 systematic decomposition (issue #331).
    """

    def __init__(self, apisession: object, get_org_id_fn: Callable[[], str]) -> None:  # DI constructor
        """Store injected dependencies for use by all tenant-fetching methods.

        Args:
            apisession: Active Mist API session for making API calls.
            get_org_id_fn: Callable that returns the current org ID string.
        """
        self._session = apisession  # Mist API session for all API calls
        self._get_org_id = get_org_id_fn  # Org ID resolver called lazily per method

    def organization_tenants(self) -> list[str]:  # Public method: org-scope network tenants
        """Fetch all tenants defined in organization networks.

        Returns:
            List of tenant names found in organization networks, or empty list if error.
        """
        try:
            org_id = self._get_org_id()  # Resolve org ID via injected callable
            logging.info("Fetching org networks for tenant info from org_id: %s", org_id)  # Trace request
            response = mistapi.api.v1.orgs.networks.listOrgNetworks(
                self._session, org_id, limit=_API_PAGE_LIMIT
            )  # Fetch all org networks from Mist API
            if not (hasattr(response, "data") and response.data):  # Defensive: response may lack data
                logging.warning("No org networks found or response data is empty")  # Surface empty result
                return []  # Callers treat empty list as "no tenants found"
            logging.debug("Received %d org networks from API", len(response.data))  # Payload size trace
            tenant_list = sorted(self._extract_tenants_from_networks(response.data))  # Dedupe + sort
            logging.info("Found %d unique org-network tenants: %s", len(tenant_list), tenant_list)  # Report
            return tenant_list  # Sorted list handed back to caller
        except Exception as error:  # Broad guard: never propagate API failures to the UI
            logging.error("Error fetching org tenants from networks: %s", error)  # Log root cause
            return []  # Fail-safe empty list keeps callers simple

    def site_tenants(self, site_id: str) -> list[str]:  # Public method: site-scope derived-network tenants
        """Fetch all tenants defined in site-level derived networks.

        Args:
            site_id: The site ID to fetch tenants for.

        Returns:
            List of tenant names found in site derived networks, or empty list if error.
        """
        try:
            logging.info("Fetching site derived networks for tenant info from site_id: %s", site_id)  # Trace
            response = mistapi.api.v1.sites.networks.listSiteNetworksDerived(
                self._session, site_id
            )  # Fetch site-derived network list from Mist API
            if not (hasattr(response, "data") and response.data):  # Guard against missing/empty payload
                logging.warning("No site derived networks found or response data is empty")  # Empty trace
                return []  # Fail-safe empty result
            logging.debug("Received %d site derived networks from API", len(response.data))  # Size trace
            tenant_list = sorted(self._extract_tenants_from_networks(response.data))  # Dedupe + sort
            logging.info("Found %d unique site-network tenants: %s", len(tenant_list), tenant_list)  # Report
            return tenant_list  # Sorted list handed back to caller
        except Exception as error:  # Broad guard mirrors organization_tenants for symmetry
            logging.error("Error fetching site tenants from derived networks: %s", error)  # Log root cause
            return []  # Fail-safe empty list keeps callers simple

    def service_policy_tenants(self, site_id: str | None = None) -> list[str]:  # Union of org + site policies
        """Fetch all tenants defined in organization and site service policies.

        Args:
            site_id: Optional site ID. If None, only org policies are fetched.

        Returns:
            List of tenant names found in service policies, or empty list if error.
        """
        try:
            tenant_names: set[str] = set()  # Deduplicate across org and site policies
            org_id = self._get_org_id()  # Resolve org ID via injected callable
            tenant_names.update(self._fetch_org_policy_tenants(org_id))  # Org-scope contributions
            if site_id:  # Only fetch site policies when a site_id is provided
                tenant_names.update(self._fetch_site_policy_tenants(site_id))  # Site-scope contributions
            tenant_list = sorted(tenant_names)  # Deterministic order for UI + tests
            logging.info(
                "Found %d unique tenants across service policies: %s", len(tenant_list), tenant_list
            )  # Emit final union count for operator visibility
            return tenant_list  # Sorted list handed back to caller
        except Exception as error:  # Broad guard: never propagate API failures to the UI
            logging.error("Error fetching tenants from service policies: %s", error)  # Log root cause
            return []  # Fail-safe empty list keeps callers simple

    def gateway_template_tenants(self, site_id: str | None = None) -> list[str]:  # Union of gw templates
        """Fetch all tenants defined in organization and site gateway templates.

        Args:
            site_id: Optional site ID. If None, only org templates are fetched.

        Returns:
            List of tenant names found in gateway templates, or empty list if error.
        """
        try:
            tenant_names: set[str] = set()  # Deduplicate across org and site templates
            org_id = self._get_org_id()  # Resolve org ID via injected callable
            tenant_names.update(self._fetch_org_template_tenants(org_id))  # Org-scope contributions
            if site_id:  # Only fetch site templates when a site_id is provided
                tenant_names.update(self._fetch_site_template_tenants(site_id))  # Site-scope contributions
            tenant_list = sorted(tenant_names)  # Deterministic order for UI + tests
            logging.info(
                "Found %d unique tenants across gateway templates: %s", len(tenant_list), tenant_list
            )  # Emit final union count for operator visibility
            return tenant_list  # Sorted list handed back to caller
        except Exception as error:  # Broad guard: never propagate API failures to the UI
            logging.error("Error fetching tenants from gateway templates: %s", error)  # Log root cause
            return []  # Fail-safe empty list keeps callers simple

    # ------------------------------------------------------------------
    # Private helpers -- kept @staticmethod because none touch instance
    # state; several are called from other @staticmethods via the class.
    # ------------------------------------------------------------------

    @staticmethod
    def _collect_network_tenants(network: dict[str, Any], target: set[str]) -> None:  # Per-network merger
        """Collect tenant names from one network dict into ``target`` (name + tenants keys)."""
        _add_valid_name(target, network.get("name"))  # Network name itself is a tenant identifier
        tenants_dict = network.get("tenants")  # Optional dict whose keys are extra tenants
        if isinstance(tenants_dict, dict):  # Guard: skip non-dict payloads defensively
            _add_valid_names(target, tenants_dict.keys())  # Each key is a tenant identifier

    @staticmethod
    def _extract_tenants_from_networks(networks_data: list[Any]) -> set[str]:  # Aggregate over network list
        """Extract tenant names from a list of Mist network objects.

        Each network contributes its name as a tenant identifier and may also
        contain an explicit ``tenants`` dict whose keys are tenant names.
        """
        tenant_names: set[str] = set()  # Accumulator returned to the caller
        for network in networks_data:  # Iterate each network object in the response
            if isinstance(network, dict):  # Guard: skip any non-dict entries silently
                APITenantFetchUtils._collect_network_tenants(network, tenant_names)  # Merge into accumulator
        return tenant_names  # Fully populated set returned to caller

    @staticmethod
    def _extract_service_tenants(services: Iterable[Any], target: set[str]) -> None:  # svc.tenant collector
        """Collect ``svc.tenant`` values from each service dict into ``target``."""
        for svc in services:  # Iterate the per-service list on the parent policy
            if isinstance(svc, dict):  # Guard: skip malformed non-dict service entries
                _add_valid_name(target, svc.get("tenant"))  # Per-service tenant reference

    @staticmethod
    def _extract_tenants_from_policy_item(policy: dict[str, Any]) -> set[str]:  # One-policy tenant merge
        """Extract tenant names from a single Mist service policy dict.

        Handles three patterns: ``tenants`` list, ``tenant`` scalar, and
        ``services[].tenant`` nested strings.
        """
        tenant_names: set[str] = set()  # Aggregates all three tenant patterns
        _add_valid_names(tenant_names, policy.get("tenants", []))  # Preferred list format
        _add_valid_name(tenant_names, policy.get("tenant"))  # Legacy scalar field
        APITenantFetchUtils._extract_service_tenants(
            policy.get("services", []), tenant_names
        )  # Nested per-service references
        return tenant_names  # Fully populated set returned to caller

    @staticmethod
    def _extract_tenants_from_policies(policies_data: list[Any]) -> set[str]:  # Aggregate over policy list
        """Extract tenant names from a list of Mist service policy objects."""
        tenant_names: set[str] = set()  # Deduplicate across all policies
        for policy in policies_data:  # Iterate each service policy object
            if not isinstance(policy, dict):  # Skip any non-dict entries
                continue  # Move to the next policy without contributing tenants
            tenant_names.update(
                APITenantFetchUtils._extract_tenants_from_policy_item(policy)
            )  # Merge the per-policy set into the aggregate
        return tenant_names  # Fully populated set returned to caller

    @staticmethod
    def _collect_router_tenant_items(items: Iterable[Any], target: set[str]) -> None:  # tenants[] merger
        """Collect tenant names from router ``tenants[].name`` dict entries into ``target``."""
        for item in items:  # Iterate the router.tenants list (list of dicts)
            if isinstance(item, dict):  # Guard: skip non-dict entries defensively
                _add_valid_name(target, item.get("name"))  # Named tenant object contributes its .name

    @staticmethod
    def _extract_router_tenants(router: dict[str, Any], tmpl_name: str) -> set[str]:  # Router-block merge
        """Extract tenant names from a gateway template router configuration dict."""
        tenant_names: set[str] = set()  # Collected from router.tenants and router.tenant_profiles
        APITenantFetchUtils._collect_router_tenant_items(
            router.get("tenants", []), tenant_names
        )  # Named tenant references
        _add_valid_names(tenant_names, router.get("tenant_profiles", {}))  # Profile keys are tenant IDs
        logging.debug(
            "Extracted %d router tenants for template '%s'", len(tenant_names), tmpl_name
        )  # Diagnostic trace with template context
        return tenant_names  # Fully populated set returned to caller

    @staticmethod
    def _extract_network_tenants(networks: list[Any], tmpl_name: str) -> set[str]:  # Networks-block merge
        """Extract tenant names from gateway template network blocks."""
        tenant_names: set[str] = set()  # Collected from networks[].tenants dict keys
        for network in networks:  # Iterate each network block in the template
            if isinstance(network, dict):  # Guard: skip any non-dict entries
                _add_valid_names(tenant_names, network.get("tenants", {}))  # Each dict key is a tenant name
        logging.debug(
            "Extracted %d network tenants for template '%s'", len(tenant_names), tmpl_name
        )  # Diagnostic trace with template context
        return tenant_names  # Fully populated set returned to caller

    @staticmethod
    def _extract_tenants_from_templates(templates_data: list[Any]) -> set[str]:  # Aggregate over templates
        """Extract tenant names from a list of Mist gateway template objects.

        Handles: ``router.tenants[].name``, ``router.tenant_profiles`` keys,
        and ``networks[].tenants`` dict keys.
        """
        tenant_names: set[str] = set()  # Deduplicate across all templates
        for tmpl in templates_data:  # Iterate each gateway template object
            if not isinstance(tmpl, dict):  # Skip any non-dict entries
                continue  # Move to the next template without contributing tenants
            tmpl_name = tmpl.get("name", "unnamed")  # For log context only
            router = tmpl.get("router", {})  # Router config sub-dict (may be absent)
            if isinstance(router, dict):  # Only process dict-type router configs
                tenant_names.update(
                    APITenantFetchUtils._extract_router_tenants(router, tmpl_name)
                )  # Merge router-derived tenants
            tenant_names.update(
                APITenantFetchUtils._extract_network_tenants(tmpl.get("networks", []), tmpl_name)
            )  # Merge networks-derived tenants
        return tenant_names  # Fully populated set returned to caller

    def _fetch_org_policy_tenants(self, org_id: str) -> set[str]:  # Org service-policies API wrapper
        """Fetch and extract tenant names from org-level service policies."""
        try:
            logging.info("Fetching org service policies for tenant info from org_id: %s", org_id)  # Request trace
            response = mistapi.api.v1.orgs.servicepolicies.listOrgServicePolicies(
                self._session, org_id, limit=_API_PAGE_LIMIT
            )  # Org service policies endpoint
            if not (hasattr(response, "data") and response.data):  # Guard against missing/empty payload
                logging.warning("No org service policies found or response data is empty")  # Empty trace
                return set()  # Fail-safe empty set
            logging.debug("Received %d org service policies", len(response.data))  # Payload size trace
            return self._extract_tenants_from_policies(response.data)  # Parse into deduped set
        except Exception as error:  # Broad guard: policy endpoint may 404 on legacy orgs
            logging.warning("Could not fetch org service policies: %s", error)  # Warn rather than error
            return set()  # Fail-safe empty set keeps union caller simple

    def _fetch_site_policy_tenants(self, site_id: str) -> set[str]:  # Site service-policies API wrapper
        """Fetch and extract tenant names from site-level derived service policies."""
        try:
            logging.info("Fetching site service policies for tenant info from site_id: %s", site_id)  # Request trace
            response = mistapi.api.v1.sites.servicepolicies.listSiteServicePoliciesDerived(
                self._session, site_id
            )  # Site service policies endpoint
            if not (hasattr(response, "data") and response.data):  # Guard against missing/empty payload
                logging.warning("No site service policies found or response data is empty")  # Empty trace
                return set()  # Fail-safe empty set
            logging.debug("Received %d site service policies", len(response.data))  # Payload size trace
            return self._extract_tenants_from_policies(response.data)  # Parse into deduped set
        except Exception as error:  # Broad guard mirrors _fetch_org_policy_tenants for symmetry
            logging.warning("Could not fetch site service policies: %s", error)  # Warn rather than error
            return set()  # Fail-safe empty set keeps union caller simple

    def _fetch_org_template_tenants(self, org_id: str) -> set[str]:  # Org gateway-templates API wrapper
        """Fetch and extract tenant names from org-level gateway templates."""
        try:
            logging.info("Fetching org gateway templates for tenant info from org_id: %s", org_id)  # Request trace
            response = mistapi.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates(
                self._session, org_id, limit=_API_PAGE_LIMIT
            )  # Org templates endpoint
            if not (hasattr(response, "data") and response.data):  # Guard against missing/empty payload
                logging.warning("No org gateway templates found or response data is empty")  # Empty trace
                return set()  # Fail-safe empty set
            logging.debug("Received %d org gateway templates", len(response.data))  # Payload size trace
            return self._extract_tenants_from_templates(response.data)  # Parse into deduped set
        except Exception as error:  # Broad guard: template endpoint may 404 on legacy orgs
            logging.warning("Could not fetch org gateway templates: %s", error)  # Warn rather than error
            return set()  # Fail-safe empty set keeps union caller simple

    def _fetch_site_template_tenants(self, site_id: str) -> set[str]:  # Site gateway-templates API wrapper
        """Fetch and extract tenant names from site-level derived gateway templates."""
        try:
            logging.info("Fetching site gateway templates for tenant info from site_id: %s", site_id)  # Request trace
            response = mistapi.api.v1.sites.gatewaytemplates.listSiteGatewayTemplatesDerived(
                self._session, site_id
            )  # Site templates endpoint
            if not (hasattr(response, "data") and response.data):  # Guard against missing/empty payload
                logging.warning("No site gateway templates found or response data is empty")  # Empty trace
                return set()  # Fail-safe empty set
            logging.debug("Received %d site gateway templates", len(response.data))  # Payload size trace
            return self._extract_tenants_from_templates(response.data)  # Parse into deduped set
        except Exception as error:  # Broad guard mirrors _fetch_org_template_tenants for symmetry
            logging.warning("Could not fetch site gateway templates: %s", error)  # Warn rather than error
            return set()  # Fail-safe empty set keeps union caller simple
