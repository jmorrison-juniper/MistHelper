"""Tenant fetch utilities for Mist API operations.

src/api/tenant_fetch.py -- extracted from MistHelper.py to keep the monolith
under the 5-Item Rule limit (Wave 2 decomposition, issue #331).

Dependencies are injected via the constructor so this module has no
circular imports with MistHelper.py.

Target audience: Junior NOC engineers -- every line has an inline comment.
"""

from __future__ import annotations  # Enable postponed evaluation of annotations

import logging  # Standard library logging for all diagnostic output
from collections.abc import Callable  # Callable type hint for the org ID resolver

import mistapi.api.v1.orgs.gatewaytemplates  # Mist API: org-level gateway template operations
import mistapi.api.v1.orgs.networks  # Mist API: org-level network operations
import mistapi.api.v1.orgs.servicepolicies  # Mist API: org-level service policy operations
import mistapi.api.v1.sites.gatewaytemplates  # Mist API: site-level gateway template operations
import mistapi.api.v1.sites.networks  # Mist API: site-level derived network operations
import mistapi.api.v1.sites.servicepolicies  # Mist API: site-level service policy operations


class APITenantFetchUtils:
    """Tenant fetch utilities for org, site, service policy, and gateway template scopes.

    Uses constructor injection for the Mist API session and org ID resolver callable
    to keep this module free of circular imports with MistHelper.py.

    Usage::

        _utils = APITenantFetchUtils(
            apisession=apisession,
            get_org_id_fn=ConfigUtils.get_cached_or_prompted_org_id,
        )
        tenants = _utils.organization_tenants()

    Extracted from MistHelper.py for Wave 2 systematic decomposition (issue #331).
    """

    def __init__(self, apisession: object, get_org_id_fn: Callable[[], str]) -> None:
        """Store injected dependencies for use by all tenant-fetching methods.

        Args:
            apisession: Active Mist API session for making API calls.
            get_org_id_fn: Callable that returns the current org ID string.
        """
        self._session = apisession  # Store Mist API session for all API calls in this instance
        self._get_org_id = get_org_id_fn  # Store org ID resolver -- called lazily per method

    def organization_tenants(self) -> list[str]:
        """Fetch all tenants defined in organization networks using the Mist API.

        Returns:
            list: List of tenant names found in organization networks, or empty list if error.

        SECURITY: Read-only operation fetching configuration data only.
        """
        try:
            org_id = self._get_org_id()  # Resolve org ID at call time via injected callable
            # Log before API call
            logging.info("Fetching organization networks for tenant information from org_id: %s", org_id)

            # Fetch all org networks from Mist API
            response = mistapi.api.v1.orgs.networks.listOrgNetworks(self._session, org_id, limit=1000)

            if hasattr(response, "data") and response.data:  # Validate response has data before processing
                networks_data = response.data  # Extract data payload from API response
                logging.debug("Received %d organization networks from API", len(networks_data))  # Log result count

                tenant_names: set[str] = set()  # Use set to deduplicate tenant names across networks
                for network in networks_data:  # Iterate each network object in the response
                    if isinstance(network, dict):  # Only process dict-type network entries
                        network_name = network.get("name")  # The network name itself is a valid tenant for service ping
                        if network_name and isinstance(network_name, str):  # Only add non-empty string names
                            tenant_names.add(network_name)  # Add network name as tenant
                            logging.debug("Found network tenant '%s'", network_name)  # Log each tenant discovered

                        if "tenants" in network:  # Check for explicit tenant sub-keys inside the network object
                            tenants_dict = network.get("tenants", {})  # Extract tenants sub-dictionary
                            if isinstance(tenants_dict, dict):  # Only process dict-type tenant containers
                                for tenant_name in tenants_dict.keys():  # Each key in tenants dict is a tenant name
                                    if tenant_name and isinstance(tenant_name, str):  # Filter out empty/non-string keys
                                        tenant_names.add(tenant_name)  # Add explicit tenant name to the set
                                        logging.debug(
                                            "Found explicit tenant '%s' in network '%s'",
                                            tenant_name,
                                            network.get("name", "unnamed"),  # Include network context in log
                                        )

                tenant_list = sorted(tenant_names)  # Sort for deterministic output and display
                # Log final count
                logging.info("Found %d unique tenants across organization networks: %s", len(tenant_list), tenant_list)
                return tenant_list  # Return sorted list of unique tenant names

            else:
                # Warn operator of empty response
                logging.warning("No organization networks found or response data is empty")
                return []  # Return empty list on missing data

        except Exception as error:  # Catch all errors to prevent cascading failures in ServicePingManager
            logging.error("Error fetching organization tenants from networks: %s", error)  # Log full error context
            return []  # Return empty list on error so caller can continue

    def site_tenants(self, site_id: str) -> list[str]:
        """Fetch all tenants defined in site-level derived networks using the Mist API.

        Args:
            site_id: The site ID to fetch tenants for.

        Returns:
            list: List of tenant names found in site derived networks, or empty list if error.

        SECURITY: Read-only operation fetching configuration data only.
        """
        try:
            # Log before API call
            logging.info("Fetching site derived networks for tenant information from site_id: %s", site_id)

            # Fetch site-derived network list from Mist API
            response = mistapi.api.v1.sites.networks.listSiteNetworksDerived(self._session, site_id)

            if hasattr(response, "data") and response.data:  # Validate response has data
                networks_data = response.data  # Extract data payload
                logging.debug("Received %d site derived networks from API", len(networks_data))  # Log result count

                tenant_names: set[str] = set()  # Use set to deduplicate tenant names
                for network in networks_data:  # Iterate each site-derived network
                    if isinstance(network, dict):  # Only process dict-type network entries
                        network_name = network.get("name")  # Network name serves as a tenant identifier
                        if network_name and isinstance(network_name, str):  # Only add non-empty string names
                            tenant_names.add(network_name)  # Add network name as tenant
                            logging.debug("Found site network tenant '%s'", network_name)  # Log each discovered tenant

                        if "tenants" in network:  # Check for explicit tenant sub-keys
                            tenants_dict = network.get("tenants", {})  # Extract tenants sub-dict
                            if isinstance(tenants_dict, dict):  # Only process dict-type tenant containers
                                for tenant_name in tenants_dict.keys():  # Each key is a tenant name
                                    if tenant_name and isinstance(tenant_name, str):  # Filter empty/non-string keys
                                        tenant_names.add(tenant_name)  # Add tenant to the set
                                        logging.debug(
                                            "Found explicit tenant '%s' in site network '%s'",
                                            tenant_name,
                                            network.get("name", "unnamed"),  # Include network context in log
                                        )

                tenant_list = sorted(tenant_names)  # Sort for deterministic output
                # Log final count
                logging.info("Found %d unique tenants across site derived networks: %s", len(tenant_list), tenant_list)
                return tenant_list  # Return sorted list of unique tenant names

            else:
                logging.warning("No site derived networks found or response data is empty")  # Warn on empty response
                return []  # Return empty list on missing data

        except Exception as error:  # Catch all errors to prevent cascading failures in caller
            logging.error("Error fetching site tenants from derived networks: %s", error)  # Log full error context
            return []  # Return empty list on error

    def service_policy_tenants(self, site_id: str | None = None) -> list[str]:  # noqa: C901, PLR0912, PLR0915
        """Fetch all tenants defined in organization and site service policies.

        Args:
            site_id: Optional site ID for site-specific policies. If None, only org policies fetched.

        Returns:
            list: List of tenant names found in service policies, or empty list if error.

        SECURITY: Read-only operation fetching configuration data only.
        """
        try:
            tenant_names: set[str] = set()  # Use set to deduplicate across org and site policies

            org_id = self._get_org_id()  # Resolve org ID at call time via injected callable
            # Log before API call
            logging.info("Fetching organization service policies for tenant information from org_id: %s", org_id)

            try:
                # Fetch all org service policies
                response = mistapi.api.v1.orgs.servicepolicies.listOrgServicePolicies(self._session, org_id, limit=1000)

                if hasattr(response, "data") and response.data:  # Validate response has data
                    policies_data = response.data  # Extract data payload
                    # Log result count
                    logging.debug("Received %d organization service policies from API", len(policies_data))

                    for policy in policies_data:  # Iterate each org service policy
                        if isinstance(policy, dict):  # Only process dict-type policy entries
                            tenants_list = policy.get("tenants", [])  # Extract tenants array from policy
                            if isinstance(tenants_list, list):  # Only process list-type tenant containers
                                for tenant_name in tenants_list:  # Each entry in tenants list is a tenant name
                                    if tenant_name and isinstance(tenant_name, str):  # Filter empty/non-string values
                                        tenant_names.add(tenant_name)  # Add tenant to the set
                                        logging.debug(
                                            "Found tenant '%s' in org service policy '%s'",
                                            tenant_name,
                                            policy.get("name", "unnamed"),  # Include policy context in log
                                        )

                            # Check legacy single-tenant field for compatibility
                            tenant_name_single = policy.get("tenant", "")
                            if tenant_name_single and isinstance(tenant_name_single, str):  # Only add non-empty string
                                tenant_names.add(tenant_name_single)  # Add legacy single tenant
                                logging.debug(
                                    "Found single tenant '%s' in org service policy '%s'",
                                    tenant_name_single,
                                    policy.get("name", "unnamed"),  # Include policy context in log
                                )

                            services = policy.get("services", [])  # Check nested services array for tenant refs
                            if isinstance(services, list):  # Only process list-type services containers
                                for service in services:  # Iterate each service in the policy
                                    if isinstance(service, dict):  # Only process dict-type service entries
                                        service_tenant = service.get("tenant", "")  # Extract tenant from service entry
                                        # Only add non-empty string
                                        if service_tenant and isinstance(service_tenant, str):
                                            tenant_names.add(service_tenant)  # Add service-level tenant
                                            logging.debug(
                                                "Found tenant '%s' in org service policy service", service_tenant
                                            )  # Log nested discovery

            except Exception as org_error:  # Catch org policy errors without blocking site policy fetch
                logging.warning("Could not fetch organization service policies: %s", org_error)  # Warn but continue

            if site_id:  # Only fetch site policies when a site_id is provided
                # Log before API call
                logging.info("Fetching site service policies for tenant information from site_id: %s", site_id)

                try:
                    response = mistapi.api.v1.sites.servicepolicies.listSiteServicePoliciesDerived(
                        self._session, site_id
                    )  # Fetch site-derived service policies

                    if hasattr(response, "data") and response.data:  # Validate response has data
                        policies_data = response.data  # Extract data payload
                        # Log result count
                        logging.debug("Received %d site service policies from API", len(policies_data))

                        for policy in policies_data:  # Iterate each site service policy
                            if isinstance(policy, dict):  # Only process dict-type policy entries
                                tenants_list = policy.get("tenants", [])  # Extract tenants array from policy
                                if isinstance(tenants_list, list):  # Only process list-type tenant containers
                                    for tenant_name in tenants_list:  # Each entry is a tenant name
                                        # Filter empty/non-string values
                                        if tenant_name and isinstance(tenant_name, str):
                                            tenant_names.add(tenant_name)  # Add tenant to the set
                                            logging.debug(
                                                "Found tenant '%s' in site service policy '%s'",
                                                tenant_name,
                                                policy.get("name", "unnamed"),  # Include policy context in log
                                            )

                                tenant_name_single = policy.get("tenant", "")  # Check legacy single-tenant field
                                # Only add non-empty string
                                if tenant_name_single and isinstance(tenant_name_single, str):
                                    tenant_names.add(tenant_name_single)  # Add legacy single tenant
                                    logging.debug(
                                        "Found single tenant '%s' in site service policy '%s'",
                                        tenant_name_single,
                                        policy.get("name", "unnamed"),  # Include policy context in log
                                    )

                                services = policy.get("services", [])  # Check nested services array
                                if isinstance(services, list):  # Only process list-type services
                                    for service in services:  # Iterate each service entry
                                        if isinstance(service, dict):  # Only process dict-type services
                                            service_tenant = service.get("tenant", "")  # Extract tenant from service
                                            # Only add non-empty string
                                            if service_tenant and isinstance(service_tenant, str):
                                                tenant_names.add(service_tenant)  # Add service-level tenant
                                                logging.debug(
                                                    "Found tenant '%s' in site service policy service", service_tenant
                                                )  # Log nested discovery

                except Exception as site_error:  # Catch site policy errors without blocking the full result
                    logging.warning("Could not fetch site service policies: %s", site_error)  # Warn but continue

            tenant_list = sorted(tenant_names)  # Sort for deterministic output
            # Log final count
            logging.info("Found %d unique tenants across service policies: %s", len(tenant_list), tenant_list)
            return tenant_list  # Return sorted list of all discovered tenant names

        except Exception as error:  # Catch outer errors to prevent cascading failures
            logging.error("Error fetching tenants from service policies: %s", error)  # Log full error context
            return []  # Return empty list on error

    def gateway_template_tenants(self, site_id: str | None = None) -> list[str]:  # noqa: C901, PLR0912, PLR0915
        """Fetch all tenants defined in organization and site gateway templates.

        Args:
            site_id: Optional site ID for site-specific templates. If None, only org templates fetched.

        Returns:
            list: List of tenant names found in gateway templates, or empty list if error.

        SECURITY: Read-only operation fetching configuration data only.
        """
        try:
            tenant_names: set[str] = set()  # Use set to deduplicate across org and site templates

            org_id = self._get_org_id()  # Resolve org ID at call time via injected callable
            # Log before API call
            logging.info("Fetching organization gateway templates for tenant information from org_id: %s", org_id)

            try:
                response = mistapi.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates(
                    self._session, org_id, limit=1000
                )  # Fetch all org gateway templates

                if hasattr(response, "data") and response.data:  # Validate response has data
                    templates_data = response.data  # Extract data payload
                    # Log result count
                    logging.debug("Received %d organization gateway templates from API", len(templates_data))

                    for template in templates_data:  # Iterate each org gateway template
                        if isinstance(template, dict):  # Only process dict-type template entries
                            router_config = template.get("router", {})  # Extract router configuration block
                            if isinstance(router_config, dict):  # Only process dict-type router configs
                                # Extract tenant list from router config
                                tenants_config = router_config.get("tenants", [])
                                if isinstance(tenants_config, list):  # Only process list-type tenant containers
                                    for tenant_item in tenants_config:  # Iterate each tenant config item
                                        if isinstance(tenant_item, dict):  # Only process dict-type tenant items
                                            tenant_name = tenant_item.get("name", "")  # Extract tenant name field
                                            # Filter empty/non-string names
                                            if tenant_name and isinstance(tenant_name, str):
                                                tenant_names.add(tenant_name)  # Add tenant to the set
                                                logging.debug(
                                                    "Found tenant '%s' in org gateway template '%s'",
                                                    tenant_name,
                                                    template.get("name", "unnamed"),  # Include template context in log
                                                )

                                # Extract tenant profiles dict
                                tenant_profiles = router_config.get("tenant_profiles", {})
                                if isinstance(tenant_profiles, dict):  # Only process dict-type tenant profiles
                                    for tenant_name in tenant_profiles.keys():  # Each key is a tenant profile name
                                        # Filter empty/non-string names
                                        if tenant_name and isinstance(tenant_name, str):
                                            tenant_names.add(tenant_name)  # Add tenant profile name
                                            logging.debug(
                                                "Found tenant profile '%s' in org gateway template", tenant_name
                                            )  # Log discovery

                            networks_config = template.get("networks", [])  # Extract networks configuration list
                            if isinstance(networks_config, list):  # Only process list-type network configs
                                for network in networks_config:  # Iterate each network in the template
                                    # Only process network dicts with tenants
                                    if isinstance(network, dict) and "tenants" in network:
                                        tenants_dict = network.get("tenants", {})  # Extract tenants sub-dict
                                        if isinstance(tenants_dict, dict):  # Only process dict-type tenant containers
                                            for tenant_name in tenants_dict.keys():  # Each key is a tenant name
                                                # Filter empty/non-string keys
                                                if tenant_name and isinstance(tenant_name, str):
                                                    tenant_names.add(tenant_name)  # Add tenant to the set
                                                    logging.debug(
                                                        "Found tenant '%s' in org gateway template network", tenant_name
                                                    )  # Log discovery

            except Exception as org_error:  # Catch org template errors without blocking site template fetch
                logging.warning("Could not fetch organization gateway templates: %s", org_error)  # Warn but continue

            if site_id:  # Only fetch site templates when a site_id is provided
                # Log before API call
                logging.info("Fetching site gateway templates for tenant information from site_id: %s", site_id)

                try:
                    response = mistapi.api.v1.sites.gatewaytemplates.listSiteGatewayTemplatesDerived(
                        self._session, site_id
                    )  # Fetch site-derived gateway templates

                    if hasattr(response, "data") and response.data:  # Validate response has data
                        templates_data = response.data  # Extract data payload
                        # Log result count
                        logging.debug("Received %d site gateway templates from API", len(templates_data))

                        for template in templates_data:  # Iterate each site gateway template
                            if isinstance(template, dict):  # Only process dict-type template entries
                                router_config = template.get("router", {})  # Extract router configuration block
                                if isinstance(router_config, dict):  # Only process dict-type router configs
                                    # Extract tenant list from router config
                                    tenants_config = router_config.get("tenants", [])
                                    if isinstance(tenants_config, list):  # Only process list-type tenant containers
                                        for tenant_item in tenants_config:  # Iterate each tenant config item
                                            if isinstance(tenant_item, dict):  # Only process dict-type tenant items
                                                tenant_name = tenant_item.get("name", "")  # Extract tenant name field
                                                # Filter empty/non-string names
                                                if tenant_name and isinstance(tenant_name, str):
                                                    tenant_names.add(tenant_name)  # Add tenant to the set
                                                    logging.debug(
                                                        "Found tenant '%s' in site gateway template '%s'",
                                                        tenant_name,
                                                        # Include template context in log
                                                        template.get("name", "unnamed"),
                                                    )

                                    # Extract tenant profiles dict
                                    tenant_profiles = router_config.get("tenant_profiles", {})
                                    if isinstance(tenant_profiles, dict):  # Only process dict-type tenant profiles
                                        for tenant_name in tenant_profiles.keys():  # Each key is a tenant profile name
                                            # Filter empty/non-string names
                                            if tenant_name and isinstance(tenant_name, str):
                                                tenant_names.add(tenant_name)  # Add tenant profile name
                                                logging.debug(
                                                    "Found tenant profile '%s' in site gateway template", tenant_name
                                                )  # Log discovery

                                networks_config = template.get("networks", [])  # Extract networks configuration list
                                if isinstance(networks_config, list):  # Only process list-type network configs
                                    for network in networks_config:  # Iterate each network in the template
                                        # Only process network dicts with tenants
                                        if isinstance(network, dict) and "tenants" in network:
                                            tenants_dict = network.get("tenants", {})  # Extract tenants sub-dict
                                            # Only process dict-type tenant containers
                                            if isinstance(tenants_dict, dict):
                                                for tenant_name in tenants_dict.keys():  # Each key is a tenant name
                                                    # Filter empty/non-string keys
                                                    if tenant_name and isinstance(tenant_name, str):
                                                        tenant_names.add(tenant_name)  # Add tenant to the set
                                                        logging.debug(
                                                            "Found tenant '%s' in site gateway template network",
                                                            tenant_name,
                                                        )  # Log discovery

                except Exception as site_error:  # Catch site template errors without blocking the full result
                    logging.warning("Could not fetch site gateway templates: %s", site_error)  # Warn but continue

            tenant_list = sorted(tenant_names)  # Sort for deterministic output
            # Log final count
            logging.info("Found %d unique tenants across gateway templates: %s", len(tenant_list), tenant_list)
            return tenant_list  # Return sorted list of all discovered tenant names

        except Exception as error:  # Catch outer errors to prevent cascading failures
            logging.error("Error fetching tenants from gateway templates: %s", error)  # Log full error context
            return []  # Return empty list on error
