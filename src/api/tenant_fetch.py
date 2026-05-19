"""Tenant fetch utilities for Mist API operations.

src/api/tenant_fetch.py -- extracted from MistHelper.py to keep the monolith
under the 5-Item Rule limit (Wave 2 decomposition, issue #331).

Target audience: Junior NOC engineers -- every line has an inline comment.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

import mistapi.api.v1.orgs.gatewaytemplates
import mistapi.api.v1.orgs.networks
import mistapi.api.v1.orgs.servicepolicies
import mistapi.api.v1.sites.gatewaytemplates
import mistapi.api.v1.sites.networks
import mistapi.api.v1.sites.servicepolicies


class APITenantFetchUtils:
    """Tenant fetch utilities for org, site, service policy, and gateway template scopes.

    Uses constructor injection for the Mist API session and org ID resolver callable
    to keep this module free of circular imports with MistHelper.py.

    Extracted from MistHelper.py for Wave 2 systematic decomposition (issue #331).
    """

    def __init__(self, apisession: object, get_org_id_fn: Callable[[], str]) -> None:
        """Store injected dependencies for use by all tenant-fetching methods.

        Args:
            apisession: Active Mist API session for making API calls.
            get_org_id_fn: Callable that returns the current org ID string.
        """
        self._session = apisession  # Mist API session for all API calls
        self._get_org_id = get_org_id_fn  # Org ID resolver called lazily per method

    def organization_tenants(self) -> list[str]:
        """Fetch all tenants defined in organization networks.

        Returns:
            List of tenant names found in organization networks, or empty list if error.
        """
        try:
            org_id = self._get_org_id()  # Resolve org ID via injected callable
            logging.info("Fetching org networks for tenant info from org_id: %s", org_id)
            response = mistapi.api.v1.orgs.networks.listOrgNetworks(
                self._session, org_id, limit=1000
            )  # Fetch all org networks from Mist API
            if not (hasattr(response, "data") and response.data):
                logging.warning("No org networks found or response data is empty")
                return []
            logging.debug("Received %d org networks from API", len(response.data))
            tenant_list = sorted(self._extract_tenants_from_networks(response.data))
            logging.info("Found %d unique org-network tenants: %s", len(tenant_list), tenant_list)
            return tenant_list
        except Exception as error:
            logging.error("Error fetching org tenants from networks: %s", error)
            return []

    def site_tenants(self, site_id: str) -> list[str]:
        """Fetch all tenants defined in site-level derived networks.

        Args:
            site_id: The site ID to fetch tenants for.

        Returns:
            List of tenant names found in site derived networks, or empty list if error.
        """
        try:
            logging.info("Fetching site derived networks for tenant info from site_id: %s", site_id)
            response = mistapi.api.v1.sites.networks.listSiteNetworksDerived(
                self._session, site_id
            )  # Fetch site-derived network list from Mist API
            if not (hasattr(response, "data") and response.data):
                logging.warning("No site derived networks found or response data is empty")
                return []
            logging.debug("Received %d site derived networks from API", len(response.data))
            tenant_list = sorted(self._extract_tenants_from_networks(response.data))
            logging.info("Found %d unique site-network tenants: %s", len(tenant_list), tenant_list)
            return tenant_list
        except Exception as error:
            logging.error("Error fetching site tenants from derived networks: %s", error)
            return []

    def service_policy_tenants(self, site_id: str | None = None) -> list[str]:
        """Fetch all tenants defined in organization and site service policies.

        Args:
            site_id: Optional site ID. If None, only org policies are fetched.

        Returns:
            List of tenant names found in service policies, or empty list if error.
        """
        try:
            tenant_names: set[str] = set()  # Deduplicate across org and site policies
            org_id = self._get_org_id()  # Resolve org ID via injected callable
            tenant_names.update(self._fetch_org_policy_tenants(org_id))
            if site_id:  # Only fetch site policies when a site_id is provided
                tenant_names.update(self._fetch_site_policy_tenants(site_id))
            tenant_list = sorted(tenant_names)
            logging.info("Found %d unique tenants across service policies: %s", len(tenant_list), tenant_list)
            return tenant_list
        except Exception as error:
            logging.error("Error fetching tenants from service policies: %s", error)
            return []

    def gateway_template_tenants(self, site_id: str | None = None) -> list[str]:
        """Fetch all tenants defined in organization and site gateway templates.

        Args:
            site_id: Optional site ID. If None, only org templates are fetched.

        Returns:
            List of tenant names found in gateway templates, or empty list if error.
        """
        try:
            tenant_names: set[str] = set()  # Deduplicate across org and site templates
            org_id = self._get_org_id()  # Resolve org ID via injected callable
            tenant_names.update(self._fetch_org_template_tenants(org_id))
            if site_id:  # Only fetch site templates when a site_id is provided
                tenant_names.update(self._fetch_site_template_tenants(site_id))
            tenant_list = sorted(tenant_names)
            logging.info("Found %d unique tenants across gateway templates: %s", len(tenant_list), tenant_list)
            return tenant_list
        except Exception as error:
            logging.error("Error fetching tenants from gateway templates: %s", error)
            return []

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_tenants_from_networks(networks_data: list) -> set[str]:
        """Extract tenant names from a list of Mist network objects.

        Each network contributes its name as a tenant identifier and may also
        contain an explicit ``tenants`` dict whose keys are tenant names.
        """
        tenant_names: set[str] = set()
        for network in networks_data:  # Iterate each network object in the response
            if not isinstance(network, dict):  # Skip any non-dict entries
                continue
            network_name = network.get("name")  # Network name is itself a tenant identifier
            if network_name and isinstance(network_name, str):
                tenant_names.add(network_name)
                logging.debug("Found network tenant '%s'", network_name)
            tenants_dict = network.get("tenants", {})  # Explicit tenants sub-dict (may be absent)
            if isinstance(tenants_dict, dict):
                for name in tenants_dict:  # Each key in the dict is a tenant name
                    if name and isinstance(name, str):
                        tenant_names.add(name)
                        logging.debug("Found explicit tenant '%s' in network '%s'", name, network_name)
        return tenant_names

    @staticmethod
    def _extract_tenants_from_policy_item(policy: dict) -> set[str]:
        """Extract tenant names from a single Mist service policy dict.

        Handles three patterns: ``tenants`` list, ``tenant`` scalar, and
        ``services[].tenant`` nested strings.
        """
        tenant_names: set[str] = set()  # Collected from all patterns in this policy
        policy_name = policy.get("name", "unnamed")  # For log context only
        for name in policy.get("tenants", []):  # Preferred list format
            if name and isinstance(name, str):
                tenant_names.add(name)
                logging.debug("Found tenant '%s' in policy '%s'", name, policy_name)
        single = policy.get("tenant", "")  # Legacy scalar field
        if single and isinstance(single, str):
            tenant_names.add(single)
            logging.debug("Found single tenant '%s' in policy '%s'", single, policy_name)
        for svc in policy.get("services", []):  # Per-service tenant references
            if isinstance(svc, dict):
                svc_tenant = svc.get("tenant", "")
                if svc_tenant and isinstance(svc_tenant, str):
                    tenant_names.add(svc_tenant)
                    logging.debug("Found tenant '%s' in service within policy '%s'", svc_tenant, policy_name)
        return tenant_names

    @staticmethod
    def _extract_tenants_from_policies(policies_data: list) -> set[str]:
        """Extract tenant names from a list of Mist service policy objects."""
        tenant_names: set[str] = set()  # Deduplicate across all policies
        for policy in policies_data:  # Iterate each service policy object
            if not isinstance(policy, dict):  # Skip any non-dict entries
                continue
            tenant_names.update(APITenantFetchUtils._extract_tenants_from_policy_item(policy))
        return tenant_names

    @staticmethod
    def _extract_router_tenants(router: dict, tmpl_name: str) -> set[str]:
        """Extract tenant names from a gateway template router configuration dict."""
        tenant_names: set[str] = set()  # Collected from router.tenants and router.tenant_profiles
        for item in router.get("tenants", []):  # Named tenant objects in router config
            if isinstance(item, dict):
                name = item.get("name", "")
                if name and isinstance(name, str):
                    tenant_names.add(name)
                    logging.debug("Found tenant '%s' in template '%s' router", name, tmpl_name)
        for name in router.get("tenant_profiles", {}):  # Profile names are tenant identifiers
            if name and isinstance(name, str):
                tenant_names.add(name)
                logging.debug("Found tenant profile '%s' in template '%s'", name, tmpl_name)
        return tenant_names

    @staticmethod
    def _extract_network_tenants(networks: list, tmpl_name: str) -> set[str]:
        """Extract tenant names from gateway template network blocks."""
        tenant_names: set[str] = set()  # Collected from networks[].tenants dict keys
        for network in networks:  # Iterate each network block in the template
            if not isinstance(network, dict):  # Skip any non-dict entries
                continue
            for name in network.get("tenants", {}):  # Each key in the dict is a tenant name
                if name and isinstance(name, str):
                    tenant_names.add(name)
                    logging.debug("Found tenant '%s' in template '%s' network", name, tmpl_name)
        return tenant_names

    @staticmethod
    def _extract_tenants_from_templates(templates_data: list) -> set[str]:
        """Extract tenant names from a list of Mist gateway template objects.

        Handles: ``router.tenants[].name``, ``router.tenant_profiles`` keys,
        and ``networks[].tenants`` dict keys.
        """
        tenant_names: set[str] = set()  # Deduplicate across all templates
        for tmpl in templates_data:  # Iterate each gateway template object
            if not isinstance(tmpl, dict):  # Skip any non-dict entries
                continue
            tmpl_name = tmpl.get("name", "unnamed")  # For log context only
            router = tmpl.get("router", {})  # Router config sub-dict (may be absent)
            if isinstance(router, dict):  # Only process dict-type router configs
                tenant_names.update(APITenantFetchUtils._extract_router_tenants(router, tmpl_name))
            tenant_names.update(APITenantFetchUtils._extract_network_tenants(tmpl.get("networks", []), tmpl_name))
        return tenant_names

    def _fetch_org_policy_tenants(self, org_id: str) -> set[str]:
        """Fetch and extract tenant names from org-level service policies."""
        try:
            logging.info("Fetching org service policies for tenant info from org_id: %s", org_id)
            response = mistapi.api.v1.orgs.servicepolicies.listOrgServicePolicies(
                self._session, org_id, limit=1000
            )  # Org service policies endpoint
            if not (hasattr(response, "data") and response.data):
                logging.warning("No org service policies found or response data is empty")
                return set()
            logging.debug("Received %d org service policies", len(response.data))
            return self._extract_tenants_from_policies(response.data)
        except Exception as error:
            logging.warning("Could not fetch org service policies: %s", error)
            return set()

    def _fetch_site_policy_tenants(self, site_id: str) -> set[str]:
        """Fetch and extract tenant names from site-level derived service policies."""
        try:
            logging.info("Fetching site service policies for tenant info from site_id: %s", site_id)
            response = mistapi.api.v1.sites.servicepolicies.listSiteServicePoliciesDerived(
                self._session, site_id
            )  # Site service policies endpoint
            if not (hasattr(response, "data") and response.data):
                logging.warning("No site service policies found or response data is empty")
                return set()
            logging.debug("Received %d site service policies", len(response.data))
            return self._extract_tenants_from_policies(response.data)
        except Exception as error:
            logging.warning("Could not fetch site service policies: %s", error)
            return set()

    def _fetch_org_template_tenants(self, org_id: str) -> set[str]:
        """Fetch and extract tenant names from org-level gateway templates."""
        try:
            logging.info("Fetching org gateway templates for tenant info from org_id: %s", org_id)
            response = mistapi.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates(
                self._session, org_id, limit=1000
            )  # Org templates endpoint
            if not (hasattr(response, "data") and response.data):
                logging.warning("No org gateway templates found or response data is empty")
                return set()
            logging.debug("Received %d org gateway templates", len(response.data))
            return self._extract_tenants_from_templates(response.data)
        except Exception as error:
            logging.warning("Could not fetch org gateway templates: %s", error)
            return set()

    def _fetch_site_template_tenants(self, site_id: str) -> set[str]:
        """Fetch and extract tenant names from site-level derived gateway templates."""
        try:
            logging.info("Fetching site gateway templates for tenant info from site_id: %s", site_id)
            response = mistapi.api.v1.sites.gatewaytemplates.listSiteGatewayTemplatesDerived(
                self._session, site_id
            )  # Site templates endpoint
            if not (hasattr(response, "data") and response.data):
                logging.warning("No site gateway templates found or response data is empty")
                return set()
            logging.debug("Received %d site gateway templates", len(response.data))
            return self._extract_tenants_from_templates(response.data)
        except Exception as error:
            logging.warning("Could not fetch site gateway templates: %s", error)
            return set()
