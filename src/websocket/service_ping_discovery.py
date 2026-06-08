"""Service ping discovery and payload composition helpers extracted from MistHelper.py."""

from __future__ import annotations

import logging
from typing import Any

apisession: Any = None
mistapi: Any = None
APITenantFetchUtils: Any = None
ConfigUtils: Any = None
APIFetchUtils: Any = None
InputUtils: Any = None


def configure_service_ping_discovery_dependencies(
    *,
    apisession_dependency: Any,
    mistapi_dependency: Any,
    api_tenant_fetch_utils: Any,
    config_utils: Any,
    api_fetch_utils: Any,
    input_utils: Any,
) -> None:
    """Configure discovery module dependencies from the MistHelper orchestration layer."""
    global apisession
    global mistapi
    global APITenantFetchUtils
    global ConfigUtils
    global APIFetchUtils
    global InputUtils

    apisession = apisession_dependency
    mistapi = mistapi_dependency
    APITenantFetchUtils = api_tenant_fetch_utils
    ConfigUtils = config_utils
    APIFetchUtils = api_fetch_utils
    InputUtils = input_utils


class ServicePingDiscoveryMixin:
    """Discovery and payload-composition mixin for ServicePingManager."""

    def _fetch_all_tenants(self) -> None:
        """Fetch tenants from all available tenant sources."""
        print("\n-> Fetching organization tenants...")
        self._fetch_org_tenants()

        print("-> Fetching site tenants...")
        self._fetch_site_tenants()

        print("-> Fetching service policy tenants...")
        self._fetch_policy_tenants()

        print("-> Fetching gateway template tenants...")
        self._fetch_template_tenants()

    def _fetch_org_tenants(self) -> None:
        """Fetch organization-level tenants."""
        tenant_utils = APITenantFetchUtils(apisession, ConfigUtils.get_cached_or_prompted_org_id)
        tenants = tenant_utils.organization_tenants()
        if tenants:
            self.org_tenants = tenants
            print(f"   -> Found {len(self.org_tenants)} organization-level tenants")
            self._debug_print(f"Organization tenants: {self.org_tenants}")
        else:
            print("   -> No organization-level tenants found")

    def _fetch_site_tenants(self) -> None:
        """Fetch site-level tenants."""
        if self.site_id is None:
            return
        tenant_utils = APITenantFetchUtils(apisession, ConfigUtils.get_cached_or_prompted_org_id)
        tenants = tenant_utils.site_tenants(self.site_id)
        if tenants:
            self.site_tenants = tenants
            print(f"   -> Found {len(self.site_tenants)} site-level tenants")
            self._debug_print(f"Site tenants: {self.site_tenants}")
        else:
            print("   -> No site-level tenants found")

    def _fetch_policy_tenants(self) -> None:
        """Fetch service-policy tenants."""
        tenant_utils = APITenantFetchUtils(apisession, ConfigUtils.get_cached_or_prompted_org_id)
        tenants = tenant_utils.service_policy_tenants(self.site_id)
        if tenants:
            self.policy_tenants = tenants
            print(f"   -> Found {len(self.policy_tenants)} service policy tenants")
            self._debug_print(f"Service policy tenants: {self.policy_tenants}")
        else:
            print("   -> No service policy tenants found")

    def _fetch_template_tenants(self) -> None:
        """Fetch gateway-template tenants."""
        tenant_utils = APITenantFetchUtils(apisession, ConfigUtils.get_cached_or_prompted_org_id)
        tenants = tenant_utils.gateway_template_tenants(self.site_id)
        if tenants:
            self.template_tenants = tenants
            print(f"   -> Found {len(self.template_tenants)} gateway template tenants")
            self._debug_print(f"Gateway template tenants: {self.template_tenants}")
        else:
            print("   -> No gateway template tenants found")

    def _fetch_all_services(self) -> None:
        """Fetch services from org and device configuration."""
        print("\n-> Fetching organization services...")
        self._fetch_org_services()

        print("-> Fetching device configuration for additional options...")
        self._fetch_device_config()

    def _fetch_org_services(self) -> None:
        """Fetch organization-level services."""
        services = APIFetchUtils.organization_services()
        if services:
            self.org_services = services
            self.org_service_names = [service["name"] for service in services if service.get("name")]
            print(f"   -> Found {len(self.org_service_names)} organization-level services")
            self._debug_print(f"Organization services: {self.org_service_names}")
        else:
            print("   -> No organization-level services found")

    def _fetch_device_config(self) -> None:
        """Fetch device configuration and extract tenant/service discovery values."""
        try:
            logging.info("Fetching device configuration for site %s device %s", self.site_id, self.device_id)
            config_response = mistapi.api.v1.sites.devices.getSiteDevice(apisession, self.site_id, self.device_id)
            device_config = getattr(config_response, "data", {})
            logging.debug("Device configuration retrieved with %d top-level keys", len(device_config.keys()))
            self._debug_print(f"Device config keys: {list(device_config.keys())}")

            self._extract_from_device_config(device_config)
            self._extract_from_device_stats()
        except Exception as error:
            logging.warning("Could not fetch device configuration: %s", error)
            self._debug_print(f"Config error: {error}")
            print("!? Cannot retrieve device configuration")

    def _extract_from_device_config(self, config: dict[str, Any]) -> None:
        """Extract tenant and service names from device configuration payload."""
        tenants_set: set[str] = set()  # Accumulate discovered tenant names (deduplicated) from all config sections.
        services_set: set[str] = set()  # Accumulate discovered service names (deduplicated) from all sections.

        logging.info("Extracting tenants/services from service_policies + routing_instances")  # Before action.
        self._collect_from_service_policies(config, tenants_set, services_set)  # Walk service_policies block.
        self._collect_from_routing_instances(config, tenants_set)  # Walk routing_instances block.
        self._extract_from_router_config(
            config.get("router", {}), tenants_set, services_set
        )  # Walk router subsection for additional tenants and services.
        logging.debug(
            "Raw discovery counts: tenants=%d services=%d", len(tenants_set), len(services_set)
        )  # After-action raw count summary before filtering underscore-prefixed system names.

        self.device_tenants = sorted(
            [tenant for tenant in tenants_set if tenant and not tenant.startswith("_")]
        )  # Keep only operator-defined tenants (drop empty + system underscore names) and sort for determinism.
        self.device_services = sorted(
            [service for service in services_set if service and not service.startswith("_")]
        )  # Keep only operator-defined services (drop empty + system underscore names) sorted for determinism.

        self._report_device_config_results()  # Print operator-facing summary of discovered tenants and services.

    @staticmethod
    def _collect_from_service_policies(config: dict[str, Any], tenants_set: set[str], services_set: set[str]) -> None:
        """Walk the service_policies list extracting tenant names and inner service names."""
        for policy in config.get("service_policies", []):
            if not isinstance(policy, dict):
                continue  # Skip malformed list entries that are not dicts.
            tenant_name = policy.get("tenant")  # Optional tenant key on each policy entry.
            if tenant_name:
                tenants_set.add(tenant_name)  # Add discovered tenant to dedup set.
            ServicePingDiscoveryMixin._extract_services_from_policy(
                policy, services_set
            )  # Pull inner service names via shared helper.

    @staticmethod
    def _collect_from_routing_instances(config: dict[str, Any], tenants_set: set[str]) -> None:
        """Walk the routing_instances list extracting tenant names (skipping underscore-prefixed system names)."""
        for instance in config.get("routing_instances", []):
            if not isinstance(instance, dict):
                continue  # Skip malformed entries.
            name = instance.get("name")  # Routing instance name doubles as a tenant identifier.
            if name and not str(name).startswith("_"):
                tenants_set.add(str(name))  # Add only operator-defined routing instances to tenant set.

    def _extract_services_from_policy(self, policy: dict[str, Any], services_set: set[str]) -> None:
        """Extract service names from a policy object."""
        services = policy.get("services", [])
        if not isinstance(services, list):
            return

        for service_item in services:
            if isinstance(service_item, dict):
                service_name = service_item.get("name")
                if service_name:
                    services_set.add(str(service_name))
            elif isinstance(service_item, str):
                services_set.add(service_item)

    def _extract_from_router_config(self, router: dict[str, Any], tenants: set[str], services: set[str]) -> None:
        """Extract tenant/service names from router configuration section."""
        if not isinstance(router, dict):
            return

        for tenant_item in router.get("tenants", []):
            if isinstance(tenant_item, dict):
                tenant_name = tenant_item.get("name")
                if tenant_name:
                    tenants.add(str(tenant_name))

        for service_item in router.get("services", []):
            if isinstance(service_item, dict):
                service_name = service_item.get("name")
                if service_name:
                    services.add(str(service_name))

    def _extract_from_device_stats(self) -> None:
        """Extract service names from device stats payload."""
        try:
            logging.info(
                "Fetching device stats for service discovery on site %s device %s",
                self.site_id,
                self.device_id,
            )
            stats_response = mistapi.api.v1.sites.stats.getSiteDeviceStats(apisession, self.site_id, self.device_id)
            stats_data = getattr(stats_response, "data", {})
            logging.debug("Device stats retrieved with %d top-level keys", len(stats_data.keys()))
            self._debug_print(f"Stats keys: {list(stats_data.keys())}")

            for service_stat in stats_data.get("service_stat", []):
                if isinstance(service_stat, dict):
                    service_name = service_stat.get("name")
                    if (
                        service_name
                        and not str(service_name).startswith("_")
                        and service_name not in self.device_services
                    ):
                        self.device_services.append(str(service_name))
                        self.device_services.sort()
        except Exception as error:
            logging.debug(
                "Device stats retrieval failed for site %s device %s: %s",
                self.site_id,
                self.device_id,
                error,
            )
            self._debug_print(f"Could not fetch stats: {error}")

    def _report_device_config_results(self) -> None:
        """Print summary of discovered tenant/service values from device config."""
        self._debug_print(f"Found tenants from device: {self.device_tenants}")
        self._debug_print(f"Found services from device: {self.device_services}")

        if self.device_tenants:
            print(f"   -> Found {len(self.device_tenants)} tenants from device configuration")
        else:
            print("   -> No tenants found in device configuration")

        if self.device_services:
            print(f"   -> Found {len(self.device_services)} additional services from device configuration")
        else:
            print("   -> No additional services found in device configuration")

    def _build_combined_tenants(self) -> list[str]:
        """Build merged tenant list with deterministic precedence and defaults."""
        combined = list(self.org_tenants)
        for source in [self.site_tenants, self.policy_tenants, self.template_tenants, self.device_tenants]:
            for tenant in source:
                if tenant not in combined:
                    combined.append(tenant)

        if self.DEFAULT_TENANT not in combined:
            combined.append(self.DEFAULT_TENANT)
            self._debug_print(f"Added default tenant: {self.DEFAULT_TENANT}")

        self._debug_print(f"Combined tenant list: {combined}")
        return combined

    def _build_combined_services(self) -> list[str]:
        """Build merged service list with deterministic precedence and defaults."""
        combined = list(self.org_service_names)
        for service in self.device_services:
            if service not in combined:
                combined.append(service)

        if self.DEFAULT_SERVICE not in combined:
            combined.append(self.DEFAULT_SERVICE)
            self._debug_print(f"Added default service: {self.DEFAULT_SERVICE}")

        self._debug_print(f"Combined service list: {combined}")
        return combined

    def _prompt_for_tenant(self, available_tenants: list[str]) -> str | None:
        """Prompt for tenant selection from discovered list."""
        if not available_tenants:
            return self._prompt_manual_tenant()

        print("\nAvailable Tenants:")
        self._display_tenant_categories(available_tenants)

        default_index = None
        if self.DEFAULT_TENANT in available_tenants:
            default_index = available_tenants.index(self.DEFAULT_TENANT)

        print(f"  [{len(available_tenants)}] Skip tenant selection")
        return self._get_tenant_selection(available_tenants, default_index)

    def _display_tenant_categories(self, all_tenants: list[str]) -> None:
        """Display tenants grouped by discovery source, each within its own category section."""
        categories = self._build_tenant_categories(all_tenants)  # Compute ordered (label, items, suffix) tuples.
        index = 0  # Running global tenant index shown to operator across all category sections.
        for label, items, suffix in categories:
            index = self._print_indexed_category(label, items, suffix, index)  # Print section, advance index.

    def _build_tenant_categories(self, all_tenants: list[str]) -> list[tuple[str, list[str], str]]:
        """Build the ordered list of (header_label, filtered_items, suffix_text) sections for tenant display."""
        org = self.org_tenants  # Alias for readability — already-deduplicated source list.
        site_only = self._filter_unique(self.site_tenants, org)  # Site-only after excluding org tenants.
        policy_only = self._filter_unique(self.policy_tenants, org, site_only)  # Policy-only after prior sources.
        template_only = self._filter_unique(
            self.template_tenants, org, site_only, policy_only
        )  # Template-only after prior sources.
        device_only = self._filter_unique(
            self.device_tenants, org, site_only, policy_only, template_only
        )  # Device-only after prior sources.
        remaining = self._filter_unique(
            all_tenants, org, site_only, policy_only, template_only, device_only
        )  # Anything left over (default/custom).
        return [
            (f"  Organization Tenants ({len(org)}):", list(org), "(org networks)"),
            (f"  Site Tenants ({len(site_only)}):", site_only, "(site networks)"),
            (f"  Service Policy Tenants ({len(policy_only)}):", policy_only, "(service policies)"),
            (
                f"  Gateway Template Tenants ({len(template_only)}):",
                template_only,
                "(gateway templates)",
            ),
            (
                f"  Device Configuration Tenants ({len(device_only)}):",
                device_only,
                "(device config)",
            ),
            (f"  Additional Tenants ({len(remaining)}):", remaining, "(default/custom)"),
        ]

    @staticmethod
    def _filter_unique(source: list[str], *exclude_lists: list[str]) -> list[str]:
        """Return items from source that do not appear in any of the exclude_lists, preserving order."""
        excluded: set[str] = set()  # Union of all exclude lists for O(1) membership tests.
        for exclude in exclude_lists:
            excluded.update(exclude)  # Merge each exclude list into combined excluded set.
        return [item for item in source if item not in excluded]  # Preserve source order while filtering.

    @staticmethod
    def _print_indexed_category(label: str, items: list[str], suffix: str, index: int) -> int:
        """Print a labeled category section with indexed entries, returning the next available index."""
        if not items:
            return index  # Empty section — skip header entirely (legacy behavior).
        print(label)  # Print section header line.
        for name in items:
            print(f"    [{index}] {name} {suffix}")  # Print indexed entry with provenance suffix.
            index += 1  # Advance global index for next entry across all sections.
        return index

    def _get_tenant_selection(self, tenants: list[str], default_index: int | None) -> str | None:
        """Read tenant selection from user input."""
        while True:
            try:
                prompt = f"\nSelect tenant index (0-{len(tenants)})"
                if default_index is not None:
                    prompt += f" [default: {default_index} ({self.DEFAULT_TENANT})]: "
                else:
                    prompt += " [default: skip]: "

                selection = InputUtils.safe_input(prompt, context="service_ping_tenant_selection").strip()

                if not selection:
                    if default_index is not None:
                        tenant = tenants[default_index]
                        print(f"!? Using default tenant: {tenant}")
                        return tenant
                    return None

                selected_index = int(selection)
                if selected_index == len(tenants):
                    print("!? Skipping tenant selection")
                    return None

                if 0 <= selected_index < len(tenants):
                    tenant = tenants[selected_index]
                    self._print_tenant_source(tenant)
                    return tenant

                print(f"Please enter a number between 0 and {len(tenants)}")
            except ValueError:
                print("Please enter a valid number")
            except KeyboardInterrupt:
                print("\nOperation cancelled")
                raise

    def _print_tenant_source(self, tenant: str) -> None:
        """Print tenant source label for selected tenant."""
        if tenant in self.org_tenants:
            print(f"!? Selected organization tenant: {tenant}")
        elif tenant in self.site_tenants:
            print(f"!? Selected site tenant: {tenant}")
        elif tenant in self.policy_tenants:
            print(f"!? Selected service policy tenant: {tenant}")
        elif tenant in self.template_tenants:
            print(f"!? Selected gateway template tenant: {tenant}")
        elif tenant in self.device_tenants:
            print(f"!? Selected device configuration tenant: {tenant}")
        else:
            print(f"!? Selected default/custom tenant: {tenant}")

    def _prompt_manual_tenant(self) -> str | None:
        """Prompt manual tenant entry when discovery returns no tenants."""
        print("\n-> No tenants found in any configuration source")
        manual = InputUtils.safe_input(
            "-> Enter tenant name manually (or press Enter to skip): ",
            context="service_ping_tenant_manual",
        ).strip()
        if manual:
            print(f"!? Manual tenant: {manual}")
            return manual
        print("-> Proceeding without tenant (may cause service ping to fail)")
        return None

    def _prompt_for_service(self, available_services: list[str]) -> str:
        """Prompt for service selection from discovered list."""
        if not available_services:
            return self._prompt_required_service()

        print("\nAvailable Services:")
        self._display_service_categories(available_services)

        default_index = None
        if self.DEFAULT_SERVICE in available_services:
            default_index = available_services.index(self.DEFAULT_SERVICE)

        print(f"  [{len(available_services)}] Enter custom service name")
        return self._get_service_selection(available_services, default_index)

    def _display_service_categories(self, all_services: list[str]) -> None:
        """Display services grouped by discovery source (org section uses rich label, others use suffix tag)."""
        index = self._print_org_services_section(0)  # Org section uses per-service detail formatting.
        device_only = self._filter_unique(
            self.device_services, self.org_service_names
        )  # Device-only after excluding org services.
        index = self._print_indexed_category(
            f"  Device Configuration Services ({len(device_only)}):",
            device_only,
            "(device config)",
            index,
        )  # Print device-only section using shared helper.
        remaining = self._filter_unique(
            all_services, self.org_service_names, self.device_services
        )  # Anything not previously listed.
        self._print_indexed_category(
            f"  Additional Services ({len(remaining)}):",
            remaining,
            "(default/custom)",
            index,
        )  # Print remaining section using shared helper (index no longer needed afterward).

    def _print_org_services_section(self, start_index: int) -> int:
        """Print the Organization Services section with rich `(type) - description` labels."""
        if not self.org_service_names:
            return start_index  # Empty section — skip header (legacy behavior).
        index = start_index  # Local running index initialized from caller's running count.
        print(f"  Organization Services ({len(self.org_service_names)}):")  # Section header.
        for name in self.org_service_names:
            details = next(
                (service for service in self.org_services if service["name"] == name), {}
            )  # Look up matching service metadata (type, description) from cached org services list.
            service_type = details.get("type", "custom")  # Service type defaults to "custom" when missing.
            description = details.get("description", "")  # Optional description annotation.
            if description:
                print(f"    [{index}] {name} ({service_type}) - {description}")  # Rich label with description.
            else:
                print(f"    [{index}] {name} ({service_type})")  # Compact label without description.
            index += 1  # Advance index for next entry across all category sections.
        return index  # Hand running index back to caller for subsequent sections.

    def _get_service_selection(self, services: list[str], default_index: int | None) -> str:
        """Read service selection from user input."""
        while True:
            try:
                prompt = f"\nSelect service index (0-{len(services)}) or enter custom"
                if default_index is not None:
                    prompt += f" [default: {default_index} ({self.DEFAULT_SERVICE})]: "
                else:
                    prompt += ": "

                selection = InputUtils.safe_input(prompt, context="service_ping_service_selection").strip()

                if not selection:
                    if default_index is not None:
                        service = services[default_index]
                        print(f"!? Using default service: {service}")
                        return service
                    print("Please enter a service name or select from the list")
                    continue

                try:
                    selected_index = int(selection)
                    if selected_index == len(services):
                        return self._prompt_custom_service()

                    if 0 <= selected_index < len(services):
                        service = services[selected_index]
                        self._print_service_source(service)
                        return service

                    print(f"Please enter a number between 0 and {len(services)}")
                except ValueError:
                    print(f"!? Custom service: {selection}")
                    return selection
            except KeyboardInterrupt:
                print("\nOperation cancelled")
                raise

    def _print_service_source(self, service: str) -> None:
        """Print service source label for selected service."""
        if service in self.org_service_names:
            print(f"!? Selected organization service: {service}")
            details = next((record for record in self.org_services if record["name"] == service), {})
            if details.get("description"):
                print(f"  Description: {details['description']}")
            if details.get("type"):
                print(f"  Type: {details['type']}")
        elif service in self.device_services:
            print(f"!? Selected device configuration service: {service}")
        else:
            print(f"!? Selected default/custom service: {service}")

    def _prompt_custom_service(self) -> str:
        """Prompt for a required custom service name."""
        while True:
            service = InputUtils.safe_input(
                "Enter custom service name: ",
                context="service_ping_custom_service",
            ).strip()
            if service:
                print(f"!? Custom service: {service}")
                return service
            print("Service name cannot be empty")

    def _prompt_required_service(self) -> str:
        """Prompt for service name when discovery returns no services."""
        print("\n-> No services found in organization or device configuration")
        while True:
            service = InputUtils.safe_input(
                "Enter service name: ",
                context="service_ping_required_service",
            ).strip()
            if service:
                print(f"!? Custom service: {service}")
                return service
            print("Service is required. Please enter a service name.")

    def _prompt_for_ping_parameters(self) -> dict[str, Any]:
        """Prompt for host/count/size/node ping parameters."""
        host = InputUtils.safe_input(
            "\nEnter target host/IP to ping [default: 8.8.8.8]: ",
            context="service_ping_host",
        ).strip()
        if not host:
            host = self.DEFAULT_HOST
            print(f"!? Using default destination: {host}")

        count = self._prompt_for_count()
        size = self._prompt_for_size()
        node = self._prompt_for_node()

        return {"host": host, "count": count, "size": size, "node": node}

    def _prompt_for_count(self) -> int:
        """Prompt for ICMP count with sane fallback."""
        count_input = InputUtils.safe_input(
            "Enter ping count [default: 4]: ",
            context="service_ping_count",
        ).strip()
        try:
            count = int(count_input) if count_input else self.DEFAULT_COUNT
            return max(1, count)
        except ValueError:
            return self.DEFAULT_COUNT

    def _prompt_for_size(self) -> int:
        """Prompt for ICMP payload size with range clamping."""
        size_input = InputUtils.safe_input(
            "Enter packet size in bytes [default: 56]: ",
            context="service_ping_size",
        ).strip()
        try:
            size = int(size_input) if size_input else self.DEFAULT_SIZE
            return max(self.MIN_SIZE, min(size, self.MAX_SIZE))
        except ValueError:
            return self.DEFAULT_SIZE

    def _prompt_for_node(self) -> str | None:
        """Prompt for optional HA node identifier."""
        node_input = (
            InputUtils.safe_input(
                "Enter HA node (node0/node1) [optional]: ",
                context="service_ping_node",
            )
            .strip()
            .lower()
        )
        return node_input if node_input in ["node0", "node1"] else None

    def _build_payload(self, service: str, tenant: str | None, params: dict[str, Any]) -> dict[str, Any]:
        """Compose the service ping payload body for Mist API."""
        payload = {
            "host": params["host"],
            "service": service,
            "count": params["count"],
            "size": params["size"],
        }

        if tenant:
            payload["tenant"] = tenant
        if params["node"]:
            payload["node"] = params["node"]

        return payload

    def _display_configuration(self, payload: dict[str, Any]) -> None:
        """Display selected service ping configuration before execution."""
        print("\n" + "-" * 50)
        print("Service Ping Configuration:")
        print(f"  Host: {payload['host']}")
        print(f"  Service: {payload['service']}")
        print(f"  Count: {payload['count']}")
        print(f"  Size: {payload['size']} bytes")
        if payload.get("tenant"):
            print(f"  Tenant: {payload['tenant']}")
        if payload.get("node"):
            print(f"  HA Node: {payload['node']}")
        print("-" * 50)

        self._debug_validate_service(payload["service"])

    def _debug_validate_service(self, service: str) -> None:
        """Print helpful debug annotation for selected service."""
        if not self.debug_mode:
            return

        known_services = ["web-session", "LANS", "RBO_SSH"]
        if service in known_services:
            print(f"[DEBUG] Using known valid service: {service}")
        else:
            print(f"[DEBUG] Using custom service: {service} (may not exist on device)")
