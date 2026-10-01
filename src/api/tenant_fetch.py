"""Tenant fetch utilities for Mist API operations.

src/api/tenant_fetch.py -- extracted from MistHelper.py to keep the monolith
under the 5-Item Rule limit (Wave 2 decomposition, issue #331).

Target audience: Junior NOC engineers -- every line has an inline comment.
"""

from __future__ import annotations  # Postpone annotation evaluation for forward-compat typing

import logging  # Standard-library logger used by every fetch method for observability
from collections.abc import Callable, Iterable  # Callable for injected resolver, Iterable for helpers
from typing import Any, Literal  # Generic payload types and the two required request fields.

import mistapi.api.v1.orgs.gatewaytemplates  # Org gateway-template endpoint namespace
import mistapi.api.v1.orgs.networks  # Org networks endpoint namespace
import mistapi.api.v1.orgs.servicepolicies  # Org service-policies endpoint namespace
import mistapi.api.v1.sites.gatewaytemplates  # Site gateway-template endpoint namespace
import mistapi.api.v1.sites.networks  # Site networks endpoint namespace
import mistapi.api.v1.sites.servicepolicies  # Site service-policies endpoint namespace
import requests  # WHY: Mist SDK transport failures surface through requests exceptions.

from src.api.response_integrity import (
    ResponseIntegrityChecker,
)  # WHY: a silent parse failure must not read as an empty result (issue #2934).

logger = logging.getLogger(__name__)  # Name the logger for this module so a reader can filter by source.

_API_PAGE_LIMIT = 1000  # Standard pagination cap for org-level Mist list endpoints
_HTTP_OK = 200  # WHY: a response double without a status should keep legacy success behavior.
_HTTP_ERROR_MIN = 400  # WHY: HTTP 4xx and 5xx statuses mean the payload cannot prove emptiness.


def _response_status_code(response: Any) -> int:
    """Return the HTTP status when the SDK response exposes one."""
    status_code = getattr(response, "status_code", _HTTP_OK)  # WHY: old tests use simple response doubles.
    return status_code if isinstance(status_code, int) else _HTTP_OK  # WHY: non-int mock attributes are not statuses.


class TenantIdentifierValidator:
    """Validate required request identifiers without disclosing invalid values."""

    @staticmethod
    def resolve(org_id_fn: Callable[[], object], site_id: object = None) -> tuple[str, str | None]:
        """Resolve the organization and validate an optional supplied site."""
        org_id = TenantIdentifierValidator.require(org_id_fn(), "org_id")
        validated_site: str | None = None
        if site_id is not None:
            validated_site = TenantIdentifierValidator.require(site_id, "site_id")
        return org_id, validated_site

    @staticmethod
    def require(value: object, field: Literal["org_id", "site_id"]) -> str:
        """Return a nonblank identifier unchanged, or raise a field-named error."""
        logger.info("Checking the %s tenant identifier. checked_identifiers=0", field)
        if not isinstance(value, str) or not value.strip():
            logger.error(
                "Cannot fetch tenants: %s must be a non-empty string. checked_identifiers=1 refused_identifiers=1",
                field,
            )
            raise ValueError(f"{field} must be a non-empty string.")
        logger.debug("Checked the %s tenant identifier. checked_identifiers=1 refused_identifiers=0", field)
        return value  # Check whitespace without changing an opaque identifier.


class TenantNameCollector:
    """Collect optional payload names without treating them as request inputs."""

    @staticmethod
    def add(target: set[str], value: object) -> None:
        """Ignore missing or unknown optional names and retain nonempty strings."""
        if isinstance(value, str) and value:
            target.add(value)

    @staticmethod
    def collect(target: set[str], values: Iterable[object]) -> None:
        """Collect optional names from lists, mapping keys, or other iterables."""
        for value in values:
            TenantNameCollector.add(target, value)


class APITenantFetchUtils:  # Public class re-exported to MistHelper.py via the api package
    """Tenant fetch utilities for org, site, service policy, and gateway template scopes.

    Uses constructor injection for the Mist API session and org ID resolver callable
    to keep this module free of circular imports with MistHelper.py.

    Extracted from MistHelper.py for Wave 2 systematic decomposition (issue #331).
    """

    def __init__(self, apisession: object, get_org_id_fn: Callable[[], object]) -> None:  # DI constructor
        """Store injected dependencies for use by all tenant-fetching methods.

        Args:
            apisession: Active Mist API session for making API calls.
            get_org_id_fn: Callable whose result must pass required identifier validation.
        """
        self._session = apisession  # Mist API session for all API calls
        self._get_org_id = get_org_id_fn  # Org ID resolver called lazily per method

    def organization_tenants(self) -> list[str]:  # Public method: org-scope network tenants
        """Fetch all tenants defined in organization networks.

        Returns:
            List of tenant names found in organization networks, or empty list if error.

        Raises:
            ValueError: The resolved organization identifier is invalid.
        """
        try:
            org_id = TenantIdentifierValidator.require(self._get_org_id(), "org_id")
            logger.info("Fetching org networks for tenant info from org_id: %s", org_id)  # Trace request
            response = mistapi.api.v1.orgs.networks.listOrgNetworks(
                self._session, org_id, limit=_API_PAGE_LIMIT
            )  # Fetch all org networks from Mist API
            status_code = _response_status_code(response)  # WHY: a 5xx can carry an empty payload without raising.
            if status_code >= _HTTP_ERROR_MIN:  # WHY: a failing HTTP status makes the count untrustworthy.
                logger.error(  # WHY: the operator must see the cloud status instead of a false empty result.
                    "The cloud returned HTTP %s for the organization network tenant list at org %s",
                    status_code,
                    org_id,
                )
                return []  # WHY: preserve the existing failure contract for this helper.
            if ResponseIntegrityChecker.body_failed_to_parse(response):  # WHY: a broken reply is not an empty list.
                ResponseIntegrityChecker.report_parse_failure(
                    response, "the organization network tenant list", str(org_id)
                )
                return []  # WHY: preserve the existing failure contract for this helper.
            if not (hasattr(response, "data") and response.data):  # Defensive: response may lack data
                logger.warning("No org networks found or response data is empty")  # Surface empty result
                return []  # Callers treat empty list as "no tenants found"
            logger.debug("Received %d org networks from API", len(response.data))  # Payload size trace
            tenant_list = sorted(self._extract_tenants_from_networks(response.data))  # Dedupe + sort
            logger.info("Found %d unique org-network tenants: %s", len(tenant_list), tenant_list)  # Report
            return tenant_list  # Sorted list handed back to caller
        except (AttributeError, requests.RequestException) as error:  # Expected API or SDK lookup failure.
            logging.error("Error fetching org tenants from networks: %s", error)  # Log root cause
            return []  # Fail-safe empty list keeps callers simple

    def site_tenants(self, site_id: str) -> list[str]:  # Public method: site-scope derived-network tenants
        """Fetch all tenants defined in site-level derived networks.

        Args:
            site_id: The site ID to fetch tenants for.

        Returns:
            List of tenant names found in site derived networks, or empty list if error.

        Raises:
            ValueError: The required site identifier is invalid.
        """
        try:
            site_id = TenantIdentifierValidator.require(site_id, "site_id")
            logger.info("Fetching site derived networks for tenant info from site_id: %s", site_id)  # Trace
            response = mistapi.api.v1.sites.networks.listSiteNetworksDerived(
                self._session, site_id
            )  # Fetch site-derived network list from Mist API
            status_code = _response_status_code(response)  # WHY: a 5xx can carry an empty payload without raising.
            if status_code >= _HTTP_ERROR_MIN:  # WHY: a failing HTTP status makes the count untrustworthy.
                logger.error(  # WHY: the operator must see the cloud status instead of a false empty result.
                    "The cloud returned HTTP %s for the site network tenant list at site %s",
                    status_code,
                    site_id,
                )
                return []  # WHY: preserve the existing failure contract for this helper.
            if ResponseIntegrityChecker.body_failed_to_parse(response):  # WHY: a broken reply is not an empty list.
                ResponseIntegrityChecker.report_parse_failure(response, "the site network tenant list", str(site_id))
                return []  # WHY: preserve the existing failure contract for this helper.
            if not (hasattr(response, "data") and response.data):  # Guard against missing/empty payload
                logger.warning("No site derived networks found or response data is empty")  # Empty trace
                return []  # Fail-safe empty result
            logger.debug("Received %d site derived networks from API", len(response.data))  # Size trace
            tenant_list = sorted(self._extract_tenants_from_networks(response.data))  # Dedupe + sort
            logger.info("Found %d unique site-network tenants: %s", len(tenant_list), tenant_list)  # Report
            return tenant_list  # Sorted list handed back to caller
        except (AttributeError, requests.RequestException) as error:  # Expected API or SDK lookup failure.
            logging.error("Error fetching site tenants from derived networks: %s", error)  # Log root cause
            return []  # Fail-safe empty list keeps callers simple

    def service_policy_tenants(self, site_id: str | None = None) -> list[str]:  # Union of org + site policies
        """Fetch all tenants defined in organization and site service policies.

        Args:
            site_id: Optional site ID. If None, only org policies are fetched.

        Returns:
            List of tenant names found in service policies, or empty list if error.

        Raises:
            ValueError: The organization or supplied site identifier is invalid.
        """
        try:
            org_id, site_id = TenantIdentifierValidator.resolve(self._get_org_id, site_id)
            tenant_names: set[str] = set()  # Deduplicate across org and site policies
            tenant_names.update(self._fetch_org_policy_tenants(org_id))  # Org-scope contributions
            if site_id is not None:  # Only None selects organization-only discovery.
                tenant_names.update(self._fetch_site_policy_tenants(site_id))  # Site-scope contributions
            tenant_list = sorted(tenant_names)  # Deterministic order for UI + tests
            logger.info("Found %d unique tenants across service policies: %s", len(tenant_list), tenant_list)
            return tenant_list  # Sorted list handed back to caller
        except (AttributeError, requests.RequestException) as error:  # Expected API or SDK lookup failure.
            logging.error("Error fetching tenants from service policies: %s", error)  # Log root cause
            return []  # Fail-safe empty list keeps callers simple

    def gateway_template_tenants(self, site_id: str | None = None) -> list[str]:  # Union of gw templates
        """Fetch all tenants defined in organization and site gateway templates.

        Args:
            site_id: Optional site ID. If None, only org templates are fetched.

        Returns:
            List of tenant names found in gateway templates, or empty list if error.

        Raises:
            ValueError: The organization or supplied site identifier is invalid.
        """
        try:
            org_id, site_id = TenantIdentifierValidator.resolve(self._get_org_id, site_id)
            tenant_names: set[str] = set()  # Deduplicate across org and site templates
            tenant_names.update(self._fetch_org_template_tenants(org_id))  # Org-scope contributions
            if site_id is not None:  # Only None selects organization-only discovery.
                tenant_names.update(self._fetch_site_template_tenants(site_id))  # Site-scope contributions
            tenant_list = sorted(tenant_names)  # Deterministic order for UI + tests
            logger.info("Found %d unique tenants across gateway templates: %s", len(tenant_list), tenant_list)
            return tenant_list  # Sorted list handed back to caller
        except (AttributeError, requests.RequestException) as error:  # Expected API or SDK lookup failure.
            logging.error("Error fetching tenants from gateway templates: %s", error)  # Log root cause
            return []  # Fail-safe empty list keeps callers simple

    # ------------------------------------------------------------------
    # Private helpers -- kept @staticmethod because none touch instance
    # state. Several are called from other @staticmethods via the class.
    # ------------------------------------------------------------------

    @staticmethod
    def _collect_network_tenants(network: dict[str, Any], target: set[str]) -> None:  # Per-network merger
        """Collect tenant names from one network dict into ``target`` (name + tenants keys)."""
        TenantNameCollector.add(target, network.get("name"))  # Network name itself is a tenant identifier
        tenants_dict = network.get("tenants")  # Optional dict whose keys are extra tenants
        if isinstance(tenants_dict, dict):  # Guard: skip non-dict payloads defensively
            TenantNameCollector.collect(target, tenants_dict.keys())  # Each key is a tenant identifier

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
                TenantNameCollector.add(target, svc.get("tenant"))  # Per-service tenant reference

    @staticmethod
    def _extract_tenants_from_policy_item(policy: dict[str, Any]) -> set[str]:  # One-policy tenant merge
        """Extract tenant names from a single Mist service policy dict.

        Handles three patterns: ``tenants`` list, ``tenant`` scalar, and
        ``services[].tenant`` nested strings.
        """
        tenant_names: set[str] = set()  # Aggregates all three tenant patterns
        TenantNameCollector.collect(tenant_names, policy.get("tenants", []))  # Preferred list format
        TenantNameCollector.add(tenant_names, policy.get("tenant"))  # Legacy scalar field
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
                TenantNameCollector.add(target, item.get("name"))  # Named tenant object contributes its .name

    @staticmethod
    def _extract_router_tenants(router: dict[str, Any], tmpl_name: str) -> set[str]:  # Router-block merge
        """Extract tenant names from a gateway template router configuration dict."""
        tenant_names: set[str] = set()  # Collected from router.tenants and router.tenant_profiles
        APITenantFetchUtils._collect_router_tenant_items(
            router.get("tenants", []), tenant_names
        )  # Named tenant references
        TenantNameCollector.collect(tenant_names, router.get("tenant_profiles", {}))  # Profile keys are tenant IDs
        logger.debug(
            "Extracted %d router tenants for template '%s'", len(tenant_names), tmpl_name
        )  # Diagnostic trace with template context
        return tenant_names  # Fully populated set returned to caller

    @staticmethod
    def _extract_network_tenants(networks: list[Any], tmpl_name: str) -> set[str]:  # Networks-block merge
        """Extract tenant names from gateway template network blocks."""
        tenant_names: set[str] = set()  # Collected from networks[].tenants dict keys
        for network in networks:  # Iterate each network block in the template
            if isinstance(network, dict):  # Guard: skip any non-dict entries
                TenantNameCollector.collect(tenant_names, network.get("tenants", {}))  # Each dict key is a tenant name
        logger.debug(
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
            org_id = TenantIdentifierValidator.require(org_id, "org_id")
            logger.info("Fetching org service policies for tenant info from org_id: %s", org_id)  # Request trace
            response = mistapi.api.v1.orgs.servicepolicies.listOrgServicePolicies(
                self._session, org_id, limit=_API_PAGE_LIMIT
            )  # Org service policies endpoint
            if not (hasattr(response, "data") and response.data):  # Guard against missing/empty payload
                logger.warning("No org service policies found or response data is empty")  # Empty trace
                return set()  # Fail-safe empty set
            logger.debug("Received %d org service policies", len(response.data))  # Payload size trace
            return self._extract_tenants_from_policies(response.data)  # Parse into deduped set
        except (AttributeError, requests.RequestException) as error:  # Policy endpoint may be unavailable on old orgs.
            logging.warning("Could not fetch org service policies: %s", error)  # Warn rather than error
            return set()  # Fail-safe empty set keeps union caller simple

    def _fetch_site_policy_tenants(self, site_id: str) -> set[str]:  # Site service-policies API wrapper
        """Fetch and extract tenant names from site-level derived service policies."""
        try:
            site_id = TenantIdentifierValidator.require(site_id, "site_id")
            logger.info("Fetching site service policies for tenant info from site_id: %s", site_id)  # Request trace
            response = mistapi.api.v1.sites.servicepolicies.listSiteServicePoliciesDerived(
                self._session, site_id
            )  # Site service policies endpoint
            if not (hasattr(response, "data") and response.data):  # Guard against missing/empty payload
                logger.warning("No site service policies found or response data is empty")  # Empty trace
                return set()  # Fail-safe empty set
            logger.debug("Received %d site service policies", len(response.data))  # Payload size trace
            return self._extract_tenants_from_policies(response.data)  # Parse into deduped set
        except (AttributeError, requests.RequestException) as error:  # Site policy endpoint may be unavailable.
            logging.warning("Could not fetch site service policies: %s", error)  # Warn rather than error
            return set()  # Fail-safe empty set keeps union caller simple

    def _fetch_org_template_tenants(self, org_id: str) -> set[str]:  # Org gateway-templates API wrapper
        """Fetch and extract tenant names from org-level gateway templates."""
        try:
            org_id = TenantIdentifierValidator.require(org_id, "org_id")
            logger.info("Fetching org gateway templates for tenant info from org_id: %s", org_id)  # Request trace
            response = mistapi.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates(
                self._session, org_id, limit=_API_PAGE_LIMIT
            )  # Org templates endpoint
            if not (hasattr(response, "data") and response.data):  # Guard against missing/empty payload
                logger.warning("No org gateway templates found or response data is empty")  # Empty trace
                return set()  # Fail-safe empty set
            logger.debug("Received %d org gateway templates", len(response.data))  # Payload size trace
            return self._extract_tenants_from_templates(response.data)  # Parse into deduped set
        except (
            AttributeError,
            requests.RequestException,
        ) as error:  # Template endpoint may be unavailable on old orgs.
            logging.warning("Could not fetch org gateway templates: %s", error)  # Warn rather than error
            return set()  # Fail-safe empty set keeps union caller simple

    def _fetch_site_template_tenants(self, site_id: str) -> set[str]:  # Site gateway-templates API wrapper
        """Fetch and extract tenant names from site-level derived gateway templates."""
        try:
            site_id = TenantIdentifierValidator.require(site_id, "site_id")
            logger.info("Fetching site gateway templates for tenant info from site_id: %s", site_id)  # Request trace
            response = mistapi.api.v1.sites.gatewaytemplates.listSiteGatewayTemplatesDerived(
                self._session, site_id
            )  # Site templates endpoint
            if not (hasattr(response, "data") and response.data):  # Guard against missing/empty payload
                logger.warning("No site gateway templates found or response data is empty")  # Empty trace
                return set()  # Fail-safe empty set
            logger.debug("Received %d site gateway templates", len(response.data))  # Payload size trace
            return self._extract_tenants_from_templates(response.data)  # Parse into deduped set
        except (AttributeError, requests.RequestException) as error:  # Site template endpoint may be unavailable.
            logging.warning("Could not fetch site gateway templates: %s", error)  # Warn rather than error
            return set()  # Fail-safe empty set keeps union caller simple
