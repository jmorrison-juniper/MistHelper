"""Service ping discovery and payload composition helpers extracted from MistHelper.py."""

from __future__ import annotations  # WHY: PEP 563 postponed annotations for forward refs.

import logging  # WHY: emit before/after action logs for discovery and prompts.
from dataclasses import dataclass  # WHY: frozen dataclass keeps injected deps immutable.
from typing import Any  # WHY: injected utility modules are opaque to type checker.

apisession: Any = None  # WHY: lazily-bound apisession assigned via configure_* injection.
mistapi: Any = None  # WHY: lazily-bound mistapi module assigned via injection.
APITenantFetchUtils: Any = None  # WHY: lazily-bound tenant utility class.
ConfigUtils: Any = None  # WHY: lazily-bound config utility helper.
APIFetchUtils: Any = None  # WHY: lazily-bound API fetch helper class.
InputUtils: Any = None  # WHY: lazily-bound input helper for safe prompts.

_MAX_TENANT_SOURCES = 5  # WHY: constant caps tenant discovery source count for filtering loops.
_KNOWN_DEBUG_SERVICES = ("web-session", "LANS", "RBO_SSH")  # WHY: hardcoded debug allow-list for validate.
_HA_NODES = ("node0", "node1")  # WHY: only these HA node identifiers are accepted for ping payload.


@dataclass(frozen=True)  # WHY: frozen keeps injected dependencies immutable across module usage.
class ServicePingDiscoveryDependencies:  # WHY: define ServicePingDiscoveryDependencies type.
    """Immutable bundle of dependencies injected into the discovery module."""

    apisession: Any  # WHY: authenticated mist api session handle.
    mistapi: Any  # WHY: mistapi module used to reach device/stats endpoints.
    api_tenant_fetch_utils: Any  # WHY: class used to build per-source tenant utility instances.
    config_utils: Any  # WHY: helper providing cached org id lookup.
    api_fetch_utils: Any  # WHY: helper class exposing organization_services staticmethod.
    input_utils: Any  # WHY: helper providing safe_input for prompts.


def configure_service_ping_discovery_dependencies(  # WHY: public configure entrypoint signature.
    deps: ServicePingDiscoveryDependencies,  # WHY: single dataclass keeps signature under param limit.
) -> None:
    """Configure discovery module dependencies from the orchestration layer."""
    global apisession, mistapi, APITenantFetchUtils  # WHY: module-level bindings for helper functions.
    global ConfigUtils, APIFetchUtils, InputUtils  # WHY: separate line keeps global count under limit.
    apisession = deps.apisession  # WHY: publish injected apisession to module scope.
    mistapi = deps.mistapi  # WHY: publish injected mistapi module to module scope.
    APITenantFetchUtils = deps.api_tenant_fetch_utils  # WHY: publish tenant utility class.
    ConfigUtils = deps.config_utils  # WHY: publish config utility class.
    APIFetchUtils = deps.api_fetch_utils  # WHY: publish api fetch utility class.
    InputUtils = deps.input_utils  # WHY: publish input utility class.


class ServicePingDiscoveryMixin:  # WHY: define ServicePingDiscoveryMixin type.
    """Discovery and payload-composition mixin for ServicePingManager."""

    def _fetch_all_tenants(self) -> None:  # WHY: define _fetch_all_tenants helper.
        """Fetch tenants from all available tenant sources."""
        print("\n-> Fetching organization tenants...")  # WHY: user-facing status header for org fetch.
        self._fetch_org_tenants()  # WHY: populate self.org_tenants from mist API.
        print("-> Fetching site tenants...")  # WHY: user-facing status header for site fetch.
        self._fetch_site_tenants()  # WHY: populate self.site_tenants from mist API.
        print("-> Fetching service policy tenants...")  # WHY: user-facing status header for policy fetch.
        self._fetch_policy_tenants()  # WHY: populate self.policy_tenants from mist API.
        print("-> Fetching gateway template tenants...")  # WHY: user-facing status header for template fetch.
        self._fetch_template_tenants()  # WHY: populate self.template_tenants from mist API.

    def _fetch_org_tenants(self) -> None:  # WHY: define _fetch_org_tenants helper.
        """Fetch organization-level tenants."""
        tenants = self._tenant_utils().organization_tenants()  # WHY: call injected utility for org tenants.
        self._store_tenant_source("org_tenants", tenants, "organization-level")  # WHY: unified assign+log.

    def _fetch_site_tenants(self) -> None:  # WHY: define _fetch_site_tenants helper.
        """Fetch site-level tenants."""
        if self.site_id is None:  # WHY: site id required for site-scoped tenant API.
            return  # WHY: early exit on precondition failure.
        tenants = self._tenant_utils().site_tenants(self.site_id)  # WHY: call injected utility with site.
        self._store_tenant_source("site_tenants", tenants, "site-level")  # WHY: unified assign+log.

    def _fetch_policy_tenants(self) -> None:  # WHY: define _fetch_policy_tenants helper.
        """Fetch service-policy tenants."""
        tenants = self._tenant_utils().service_policy_tenants(self.site_id)  # WHY: policy tenants per site.
        self._store_tenant_source("policy_tenants", tenants, "service policy")  # WHY: unified assign+log.

    def _fetch_template_tenants(self) -> None:  # WHY: define _fetch_template_tenants helper.
        """Fetch gateway-template tenants."""
        tenants = self._tenant_utils().gateway_template_tenants(self.site_id)  # WHY: template tenants call.
        self._store_tenant_source("template_tenants", tenants, "gateway template")  # WHY: unified assign+log.

    @staticmethod
    def _tenant_utils() -> Any:  # WHY: define _tenant_utils helper.
        """Build a per-call tenant utility instance with injected deps."""
        return APITenantFetchUtils(apisession, ConfigUtils.get_cached_or_prompted_org_id)  # WHY: fresh utils.

    def _store_tenant_source(
        self, attr: str, tenants: list[str], label: str
    ) -> None:  # WHY: define _store_tenant_source helper.
        """Store tenants on attribute and emit operator + debug summaries."""
        if not tenants:  # WHY: skip attribute mutation when discovery returned empty.
            print(f"   -> No {label} tenants found")  # WHY: user-facing empty-source status.
            return  # WHY: early exit on precondition failure.
        setattr(self, attr, tenants)  # WHY: assign discovered list to named attribute.
        print(f"   -> Found {len(tenants)} {label} tenants")  # WHY: user-facing count status.
        self._debug_print(f"{label.capitalize()} tenants: {tenants}")  # WHY: verbose debug detail.

    def _fetch_all_services(self) -> None:  # WHY: define _fetch_all_services helper.
        """Fetch services from org and device configuration."""
        print("\n-> Fetching organization services...")  # WHY: user-facing status header for org fetch.
        self._fetch_org_services()  # WHY: populate org service caches.
        print("-> Fetching device configuration for additional options...")  # WHY: status for device fetch.
        self._fetch_device_config()  # WHY: populate device tenant/service caches.

    def _fetch_org_services(self) -> None:  # WHY: define _fetch_org_services helper.
        """Fetch organization-level services."""
        services = APIFetchUtils.organization_services()  # WHY: call injected utility for org services.
        if not services:  # WHY: skip caches when discovery returned empty.
            print("   -> No organization-level services found")  # WHY: user-facing empty-source status.
            return  # WHY: early exit on precondition failure.
        self.org_services = services  # WHY: cache raw org service list for later detail lookup.
        self.org_service_names = [
            service["name"] for service in services if service.get("name")
        ]  # WHY: derive name-only view once for reuse in prompts.
        print(f"   -> Found {len(self.org_service_names)} organization-level services")  # WHY: status.
        self._debug_print(f"Organization services: {self.org_service_names}")  # WHY: verbose debug detail.

    def _fetch_device_config(self) -> None:  # WHY: define _fetch_device_config helper.
        """Fetch device configuration and extract tenant/service discovery values."""
        try:
            device_config = self._retrieve_device_config()  # WHY: isolate API call for cleaner error path.
            self._extract_from_device_config(device_config)  # WHY: extract tenants/services from config.
            self._extract_from_device_stats()  # WHY: append services observed in live stats payload.
        except Exception as error:  # WHY: any API error must not abort discovery flow.
            logging.warning("Could not fetch device configuration: %s", error)  # WHY: warn but continue.
            self._debug_print(f"Config error: {error}")  # WHY: verbose debug detail for operators.
            print("!? Cannot retrieve device configuration")  # WHY: user-facing failure message.

    def _retrieve_device_config(self) -> dict[str, Any]:  # WHY: define _retrieve_device_config helper.
        """Call getSiteDevice and return the config payload dict."""
        logging.info(
            "Fetching device configuration for site %s device %s", self.site_id, self.device_id
        )  # WHY: before-action log for API call.
        response = mistapi.api.v1.sites.devices.getSiteDevice(
            apisession, self.site_id, self.device_id
        )  # WHY: single mist API round trip for device config.
        device_config = getattr(response, "data", {})  # WHY: tolerate responses without data attribute.
        logging.debug(
            "Device configuration retrieved with %d top-level keys", len(device_config.keys())
        )  # WHY: after-action summary.
        self._debug_print(f"Device config keys: {list(device_config.keys())}")  # WHY: verbose debug detail.
        return device_config  # WHY: hand payload back to caller for extraction.

    def _extract_from_device_config(
        self, config: dict[str, Any]
    ) -> None:  # WHY: define _extract_from_device_config helper.
        """Extract tenant and service names from device configuration payload."""
        tenants_set: set[str] = set()  # WHY: dedup discovered tenant names across sections.
        services_set: set[str] = set()  # WHY: dedup discovered service names across sections.
        logging.info("Extracting tenants/services from service_policies + routing_instances")  # WHY: log.
        self._collect_from_service_policies(config, tenants_set, services_set)  # WHY: policy walker.
        self._collect_from_routing_instances(config, tenants_set)  # WHY: routing walker.
        self._collect_from_router_config(config.get("router", {}), tenants_set, services_set)  # WHY: router.
        logging.debug(
            "Raw discovery counts: tenants=%d services=%d", len(tenants_set), len(services_set)
        )  # WHY: after-action raw count summary before filtering system names.
        self.device_tenants = self._sorted_non_system(tenants_set)  # WHY: strip system, sort deterministic.
        self.device_services = self._sorted_non_system(services_set)  # WHY: strip system, sort deterministic.
        self._report_device_config_results()  # WHY: emit operator summary of discovered names.

    @staticmethod
    def _sorted_non_system(names: set[str]) -> list[str]:  # WHY: define _sorted_non_system helper.
        """Return sorted names excluding empty and system underscore-prefixed values."""
        return sorted(name for name in names if name and not name.startswith("_"))  # WHY: filter+sort.

    @staticmethod
    def _collect_from_service_policies(
        config: dict[str, Any], tenants_set: set[str], services_set: set[str]
    ) -> None:  # WHY: define _collect_from_service_policies helper.
        """Walk the service_policies list extracting tenant names and inner service names."""
        for policy in config.get("service_policies", []):  # WHY: iterate policy entries safely.
            if not isinstance(policy, dict):  # WHY: skip malformed non-dict list entries.
                continue
            tenant_name = policy.get("tenant")  # WHY: optional tenant key on each policy entry.
            if tenant_name:  # WHY: only record truthy tenant names.
                tenants_set.add(tenant_name)  # WHY: add discovered tenant to dedup set.
            ServicePingDiscoveryMixin._extract_services_from_policy(
                policy, services_set
            )  # WHY: pull inner service names via shared helper.

    @staticmethod
    def _collect_from_routing_instances(
        config: dict[str, Any], tenants_set: set[str]
    ) -> None:  # WHY: define _collect_from_routing_instances helper.
        """Walk routing_instances extracting tenant names, skipping system underscore names."""
        for instance in config.get("routing_instances", []):  # WHY: iterate routing entries safely.
            if not isinstance(instance, dict):  # WHY: skip malformed non-dict list entries.
                continue
            name = instance.get("name")  # WHY: routing instance name doubles as tenant identifier.
            if name and not str(name).startswith("_"):  # WHY: keep only operator-defined names.
                tenants_set.add(str(name))  # WHY: add operator-defined routing instance to set.

    @staticmethod
    def _extract_services_from_policy(
        policy: dict[str, Any], services_set: set[str]
    ) -> None:  # WHY: define _extract_services_from_policy helper.
        """Extract service names from a policy object."""
        services = policy.get("services", [])  # WHY: optional services key on each policy.
        if not isinstance(services, list):  # WHY: skip malformed non-list values defensively.
            return  # WHY: early exit on precondition failure.
        for service_item in services:  # WHY: iterate every service reference in the policy.
            ServicePingDiscoveryMixin._add_service_reference(service_item, services_set)  # WHY: helper.

    @staticmethod
    def _add_service_reference(
        service_item: Any, services_set: set[str]
    ) -> None:  # WHY: define _add_service_reference helper.
        """Add a service reference (dict or str) to the discovery set."""
        if isinstance(service_item, dict):  # WHY: dict form carries a name key.
            service_name = service_item.get("name")  # WHY: pull service name from dict form.
            if service_name:  # WHY: skip empty names.
                services_set.add(str(service_name))  # WHY: record discovered service name.
            return  # WHY: early exit on precondition failure.
        if isinstance(service_item, str):  # WHY: bare-string form is also permitted upstream.
            services_set.add(service_item)  # WHY: record raw string service reference.

    @staticmethod
    def _collect_from_router_config(
        router: dict[str, Any], tenants: set[str], services: set[str]
    ) -> None:  # WHY: define _collect_from_router_config helper.
        """Extract tenant/service names from router configuration section."""
        if not isinstance(router, dict):  # WHY: skip malformed router payload.
            return  # WHY: early exit on precondition failure.
        ServicePingDiscoveryMixin._collect_named_items(
            router.get("tenants", []), tenants
        )  # WHY: walk router.tenants list.
        ServicePingDiscoveryMixin._collect_named_items(
            router.get("services", []), services
        )  # WHY: walk router.services list.

    @staticmethod
    def _collect_named_items(items: list[Any], sink: set[str]) -> None:  # WHY: define _collect_named_items helper.
        """Add name field of dict items to sink; skip non-dicts and empty names."""
        for entry in items:  # WHY: iterate raw list entries defensively.
            if not isinstance(entry, dict):  # WHY: skip non-dict entries.
                continue
            name = entry.get("name")  # WHY: pull optional name.
            if name:  # WHY: skip empty names.
                sink.add(str(name))  # WHY: record discovered name.

    def _extract_from_device_stats(self) -> None:  # WHY: define _extract_from_device_stats helper.
        """Extract service names from device stats payload."""
        try:
            stats_data = self._retrieve_device_stats()  # WHY: isolate API call for cleaner error path.
            self._merge_stats_services(stats_data)  # WHY: append any new service names discovered.
        except Exception as error:  # WHY: any API error must be non-fatal.
            logging.debug(
                "Device stats retrieval failed for site %s device %s: %s",
                self.site_id,
                self.device_id,
                error,
            )  # WHY: after-action failure log.
            self._debug_print(f"Could not fetch stats: {error}")  # WHY: verbose debug detail.

    def _retrieve_device_stats(self) -> dict[str, Any]:  # WHY: define _retrieve_device_stats helper.
        """Call getSiteDeviceStats and return the stats payload dict."""
        logging.info(
            "Fetching device stats for service discovery on site %s device %s",
            self.site_id,
            self.device_id,
        )  # WHY: before-action log.
        response = mistapi.api.v1.sites.stats.getSiteDeviceStats(
            apisession, self.site_id, self.device_id
        )  # WHY: single mist API round trip for device stats.
        stats_data = getattr(response, "data", {})  # WHY: tolerate responses without data attribute.
        logging.debug(
            "Device stats retrieved with %d top-level keys", len(stats_data.keys())
        )  # WHY: after-action summary.
        self._debug_print(f"Stats keys: {list(stats_data.keys())}")  # WHY: verbose debug detail.
        return stats_data  # WHY: hand payload back for merge step.

    def _merge_stats_services(self, stats_data: dict[str, Any]) -> None:  # WHY: define _merge_stats_services helper.
        """Append any new non-system service names from stats to device_services."""
        for service_stat in stats_data.get("service_stat", []):  # WHY: iterate service_stat entries.
            name = self._service_stat_name(service_stat)  # WHY: extract candidate name safely.
            if name and name not in self.device_services:  # WHY: skip duplicates already recorded.
                self.device_services.append(name)  # WHY: append new discovered service name.
                self.device_services.sort()  # WHY: keep list deterministic after each insert.

    @staticmethod
    def _service_stat_name(service_stat: Any) -> str | None:  # WHY: define _service_stat_name helper.
        """Return a valid non-system service name from stats entry or None."""
        if not isinstance(service_stat, dict):  # WHY: skip malformed non-dict entries.
            return None
        raw = service_stat.get("name")  # WHY: pull optional name key.
        if not raw or str(raw).startswith("_"):  # WHY: skip empty and system underscore names.
            return None
        return str(raw)  # WHY: normalize to str for downstream comparison.

    def _report_device_config_results(self) -> None:  # WHY: define _report_device_config_results helper.
        """Print summary of discovered tenant/service values from device config."""
        self._debug_print(f"Found tenants from device: {self.device_tenants}")  # WHY: verbose detail.
        self._debug_print(f"Found services from device: {self.device_services}")  # WHY: verbose detail.
        if self.device_tenants:  # WHY: pick between count message and empty-source message.
            print(f"   -> Found {len(self.device_tenants)} tenants from device configuration")
        else:
            print("   -> No tenants found in device configuration")
        if self.device_services:  # WHY: pick between count message and empty-source message.
            print(f"   -> Found {len(self.device_services)} additional services from device configuration")
        else:
            print("   -> No additional services found in device configuration")

    def _build_combined_tenants(self) -> list[str]:  # WHY: define _build_combined_tenants helper.
        """Build merged tenant list with deterministic precedence and defaults."""
        combined = list(self.org_tenants)  # WHY: seed with organization tenants (highest precedence).
        sources = [
            self.site_tenants,
            self.policy_tenants,
            self.template_tenants,
            self.device_tenants,
        ]  # WHY: precedence-ordered list of source lists to merge next.
        for source in sources:  # WHY: preserve source ordering while merging.
            self._append_new_items(source, combined)  # WHY: append unseen items.
        if self.DEFAULT_TENANT not in combined:  # WHY: always include documented default fallback.
            combined.append(self.DEFAULT_TENANT)  # WHY: append documented default tenant.
            self._debug_print(f"Added default tenant: {self.DEFAULT_TENANT}")  # WHY: verbose debug detail.
        self._debug_print(f"Combined tenant list: {combined}")  # WHY: verbose debug detail.
        return combined  # WHY: hand merged list back to caller.

    def _build_combined_services(self) -> list[str]:  # WHY: define _build_combined_services helper.
        """Build merged service list with deterministic precedence and defaults."""
        combined = list(self.org_service_names)  # WHY: seed with org service names.
        self._append_new_items(self.device_services, combined)  # WHY: merge device services unseen items.
        if self.DEFAULT_SERVICE not in combined:  # WHY: always include documented default fallback.
            combined.append(self.DEFAULT_SERVICE)  # WHY: append documented default service.
            self._debug_print(f"Added default service: {self.DEFAULT_SERVICE}")  # WHY: verbose debug detail.
        self._debug_print(f"Combined service list: {combined}")  # WHY: verbose debug detail.
        return combined  # WHY: hand merged list back to caller.

    @staticmethod
    def _append_new_items(source: list[str], sink: list[str]) -> None:  # WHY: define _append_new_items helper.
        """Append items from source to sink when not already present, preserving order."""
        for item in source:  # WHY: iterate in source order.
            if item not in sink:  # WHY: skip duplicates already merged.
                sink.append(item)  # WHY: append new item preserving order.

    def _prompt_for_tenant(self, available_tenants: list[str]) -> str | None:  # WHY: define _prompt_for_tenant helper.
        """Prompt for tenant selection from discovered list."""
        if not available_tenants:  # WHY: fall back to manual entry when discovery empty.
            return self._prompt_manual_tenant()
        print("\nAvailable Tenants:")  # WHY: user-facing prompt header.
        self._display_tenant_categories(available_tenants)  # WHY: render source-grouped list.
        default_index = self._default_index(available_tenants, self.DEFAULT_TENANT)  # WHY: default idx.
        print(f"  [{len(available_tenants)}] Skip tenant selection")  # WHY: sentinel skip option.
        return self._get_tenant_selection(available_tenants, default_index)  # WHY: read + parse selection.

    @staticmethod
    def _default_index(items: list[str], default_value: str) -> int | None:  # WHY: define _default_index helper.
        """Return the index of default_value in items or None when absent."""
        return items.index(default_value) if default_value in items else None  # WHY: presence lookup.

    def _display_tenant_categories(
        self, all_tenants: list[str]
    ) -> None:  # WHY: define _display_tenant_categories helper.
        """Display tenants grouped by discovery source, each within its own category section."""
        categories = self._build_tenant_categories(all_tenants)  # WHY: compute ordered category tuples.
        index = 0  # WHY: running global index shown to operator across all sections.
        for label, items, suffix in categories:  # WHY: iterate ordered category tuples.
            index = self._print_indexed_category(label, items, suffix, index)  # WHY: print + advance.

    def _build_tenant_categories(
        self, all_tenants: list[str]
    ) -> list[tuple[str, list[str], str]]:  # WHY: define _build_tenant_categories helper.
        """Return the ordered list of (header_label, filtered_items, suffix_text) sections."""
        sources = self._categorize_tenant_sources(all_tenants)  # WHY: precomputed per-source unique lists.
        return [
            self._category_tuple("Organization Tenants", sources["org"], "(org networks)"),
            self._category_tuple("Site Tenants", sources["site"], "(site networks)"),
            self._category_tuple("Service Policy Tenants", sources["policy"], "(service policies)"),
            self._category_tuple("Gateway Template Tenants", sources["template"], "(gateway templates)"),
            self._category_tuple("Device Configuration Tenants", sources["device"], "(device config)"),
            self._category_tuple("Additional Tenants", sources["remaining"], "(default/custom)"),
        ]  # WHY: fixed order matches operator expectation.

    def _categorize_tenant_sources(
        self, all_tenants: list[str]
    ) -> dict[str, list[str]]:  # WHY: define _categorize_tenant_sources helper.
        """Partition tenants into per-source unique lists preserving precedence."""
        org = list(self.org_tenants)  # WHY: base source (highest precedence, no filtering).
        site = self._filter_unique(self.site_tenants, org)  # WHY: site-only after org.
        policy = self._filter_unique(self.policy_tenants, org, site)  # WHY: policy-only after org+site.
        template = self._filter_unique(
            self.template_tenants, org, site, policy
        )  # WHY: template-only after prior sources.
        device = self._filter_unique(
            self.device_tenants, org, site, policy, template
        )  # WHY: device-only after prior sources.
        remaining = self._filter_unique(
            all_tenants, org, site, policy, template, device
        )  # WHY: anything else (default/custom).
        return {
            "org": org,
            "site": site,
            "policy": policy,
            "template": template,
            "device": device,
            "remaining": remaining,
        }  # WHY: named dict keeps caller readable and avoids positional confusion.

    @staticmethod
    def _category_tuple(
        title: str, items: list[str], suffix: str
    ) -> tuple[str, list[str], str]:  # WHY: define _category_tuple helper.
        """Compose a (header, items, suffix) tuple with formatted header line."""
        return (f"  {title} ({len(items)}):", items, suffix)  # WHY: standard indented header format.

    @staticmethod
    def _filter_unique(source: list[str], *exclude_lists: list[str]) -> list[str]:  # WHY: define _filter_unique helper.
        """Return items from source that do not appear in any of exclude_lists."""
        excluded: set[str] = set()  # WHY: union set for O(1) membership tests.
        for exclude in exclude_lists:  # WHY: fold each exclude list into union set.
            excluded.update(exclude)
        return [item for item in source if item not in excluded]  # WHY: preserve source order.

    @staticmethod
    def _print_indexed_category(
        label: str, items: list[str], suffix: str, index: int
    ) -> int:  # WHY: define _print_indexed_category helper.
        """Print a labeled category section with indexed entries, return next index."""
        if not items:  # WHY: skip empty section header entirely (legacy behavior).
            return index
        print(label)  # WHY: print section header line.
        for name in items:  # WHY: enumerate entries with running global index.
            print(f"    [{index}] {name} {suffix}")  # WHY: indexed line with provenance suffix.
            index += 1  # WHY: advance global index for next entry.
        return index  # WHY: hand next available index to caller.

    def _get_tenant_selection(
        self, tenants: list[str], default_index: int | None
    ) -> str | None:  # WHY: define _get_tenant_selection helper.
        """Read tenant selection from user input."""
        while True:  # WHY: retry loop until valid selection or skip/cancel.
            try:
                selection = self._read_tenant_selection_input(tenants, default_index)  # WHY: prompt.
                result = self._resolve_tenant_selection(selection, tenants, default_index)  # WHY: parse.
                if result.handled:  # WHY: sentinel indicates loop should exit with value/None.
                    return result.value
            except KeyboardInterrupt:  # WHY: allow user to abort selection cleanly.
                print("\nOperation cancelled")  # WHY: user-facing abort message.
                raise

    def _read_tenant_selection_input(
        self, tenants: list[str], default_index: int | None
    ) -> str:  # WHY: define _read_tenant_selection_input helper.
        """Build tenant prompt string and read/trim user input."""
        prompt = f"\nSelect tenant index (0-{len(tenants)})"  # WHY: base prompt with valid range.
        if default_index is not None:  # WHY: annotate default when present.
            prompt += f" [default: {default_index} ({self.DEFAULT_TENANT})]: "
        else:
            prompt += " [default: skip]: "  # WHY: annotate skip fallback when no default.
        return InputUtils.safe_input(prompt, context="service_ping_tenant_selection").strip()  # WHY: read.

    def _resolve_tenant_selection(  # WHY: begin _resolve_tenant_selection signature.
        self, selection: str, tenants: list[str], default_index: int | None
    ) -> _SelectionOutcome:
        """Convert raw tenant selection text into a resolved outcome."""
        if not selection:  # WHY: blank input applies default or skips.
            return self._tenant_default_outcome(tenants, default_index)
        try:
            selected_index = int(selection)  # WHY: parse numeric selection.
        except ValueError:  # WHY: non-numeric input requires retry.
            print("Please enter a valid number")
            return _SelectionOutcome(handled=False, value=None)
        return self._tenant_index_outcome(selected_index, tenants)  # WHY: dispatch by parsed index.

    def _tenant_default_outcome(
        self, tenants: list[str], default_index: int | None
    ) -> _SelectionOutcome:  # WHY: define _tenant_default_outcome helper.
        """Return outcome for blank tenant selection input."""
        if default_index is None:  # WHY: no default configured -> caller should exit with None.
            return _SelectionOutcome(handled=True, value=None)
        tenant = tenants[default_index]  # WHY: pick default entry.
        print(f"!? Using default tenant: {tenant}")  # WHY: user-facing default confirmation.
        return _SelectionOutcome(handled=True, value=tenant)  # WHY: exit loop with default.

    def _tenant_index_outcome(
        self, selected_index: int, tenants: list[str]
    ) -> _SelectionOutcome:  # WHY: define _tenant_index_outcome helper.
        """Return outcome for numeric tenant selection index."""
        if selected_index == len(tenants):  # WHY: sentinel value maps to skip.
            print("!? Skipping tenant selection")  # WHY: user-facing skip confirmation.
            return _SelectionOutcome(handled=True, value=None)
        if 0 <= selected_index < len(tenants):  # WHY: valid range -> resolve and print source.
            tenant = tenants[selected_index]
            self._print_tenant_source(tenant)  # WHY: annotate provenance for operator.
            return _SelectionOutcome(handled=True, value=tenant)
        print(f"Please enter a number between 0 and {len(tenants)}")  # WHY: out-of-range retry hint.
        return _SelectionOutcome(handled=False, value=None)  # WHY: stay in loop for retry.

    def _print_tenant_source(self, tenant: str) -> None:  # WHY: define _print_tenant_source helper.
        """Print tenant source label for selected tenant."""
        for source, label in self._tenant_source_lookup():  # WHY: table-driven dispatch flattens branches.
            if tenant in source:  # WHY: first matching source wins for provenance annotation.
                print(f"!? Selected {label}: {tenant}")
                return  # WHY: early exit on precondition failure.
        print(f"!? Selected default/custom tenant: {tenant}")  # WHY: fallback provenance line.

    def _tenant_source_lookup(self) -> list[tuple[list[str], str]]:  # WHY: define _tenant_source_lookup helper.
        """Return ordered (source_list, label) pairs for tenant provenance lookup."""
        return [
            (self.org_tenants, "organization tenant"),
            (self.site_tenants, "site tenant"),
            (self.policy_tenants, "service policy tenant"),
            (self.template_tenants, "gateway template tenant"),
            (self.device_tenants, "device configuration tenant"),
        ]  # WHY: same precedence as discovery / display.

    def _prompt_manual_tenant(self) -> str | None:  # WHY: define _prompt_manual_tenant helper.
        """Prompt manual tenant entry when discovery returns no tenants."""
        print("\n-> No tenants found in any configuration source")  # WHY: user-facing empty status.
        manual = InputUtils.safe_input(
            "-> Enter tenant name manually (or press Enter to skip): ",
            context="service_ping_tenant_manual",
        ).strip()  # WHY: read manual tenant string.
        if manual:  # WHY: truthy value means operator supplied a tenant.
            print(f"!? Manual tenant: {manual}")  # WHY: confirm manual choice.
            return manual
        print("-> Proceeding without tenant (may cause service ping to fail)")  # WHY: warn no tenant.
        return None

    def _prompt_for_service(self, available_services: list[str]) -> str:  # WHY: define _prompt_for_service helper.
        """Prompt for service selection from discovered list."""
        if not available_services:  # WHY: fall back to required-entry loop when discovery empty.
            return self._prompt_required_service()
        print("\nAvailable Services:")  # WHY: user-facing prompt header.
        self._display_service_categories(available_services)  # WHY: render source-grouped list.
        default_index = self._default_index(available_services, self.DEFAULT_SERVICE)  # WHY: default idx lookup.
        print(f"  [{len(available_services)}] Enter custom service name")  # WHY: sentinel custom option.
        return self._get_service_selection(available_services, default_index)  # WHY: read + parse.

    def _display_service_categories(
        self, all_services: list[str]
    ) -> None:  # WHY: define _display_service_categories helper.
        """Display services grouped by discovery source with org section using rich labels."""
        index = self._print_org_services_section(0)  # WHY: org section uses per-service detail formatting.
        device_only = self._filter_unique(
            self.device_services, self.org_service_names
        )  # WHY: device-only after excluding org services.
        index = self._print_indexed_category(
            f"  Device Configuration Services ({len(device_only)}):",
            device_only,
            "(device config)",
            index,
        )  # WHY: print device-only section using shared helper.
        remaining = self._filter_unique(
            all_services, self.org_service_names, self.device_services
        )  # WHY: anything not previously listed.
        self._print_indexed_category(
            f"  Additional Services ({len(remaining)}):",
            remaining,
            "(default/custom)",
            index,
        )  # WHY: print remaining section (index no longer needed afterward).

    def _print_org_services_section(self, start_index: int) -> int:  # WHY: define _print_org_services_section helper.
        """Print the Organization Services section with rich `(type) - description` labels."""
        if not self.org_service_names:  # WHY: skip empty section header entirely.
            return start_index
        print(f"  Organization Services ({len(self.org_service_names)}):")  # WHY: section header.
        index = start_index  # WHY: local running index starts at caller's running count.
        for name in self.org_service_names:  # WHY: iterate names for indexed display.
            details = self._service_details_for(name)  # WHY: lookup metadata by name.
            self._print_org_service_line(index, name, details)  # WHY: format+print one entry.
            index += 1  # WHY: advance index for next entry across sections.
        return index  # WHY: hand running index back to caller.

    def _service_details_for(self, name: str) -> dict[str, Any]:  # WHY: define _service_details_for helper.
        """Return cached org-service metadata dict for name (empty dict when missing)."""
        return next(
            (service for service in self.org_services if service["name"] == name), {}
        )  # WHY: first-match dict lookup with default.

    @staticmethod
    def _print_org_service_line(
        index: int, name: str, details: dict[str, Any]
    ) -> None:  # WHY: define _print_org_service_line helper.
        """Print one org-service entry with type and optional description."""
        service_type = details.get("type", "custom")  # WHY: type defaults to custom when missing.
        description = details.get("description", "")  # WHY: description is optional annotation.
        if description:  # WHY: pick rich label with description when present.
            print(f"    [{index}] {name} ({service_type}) - {description}")
        else:
            print(f"    [{index}] {name} ({service_type})")  # WHY: compact label without description.

    def _get_service_selection(
        self, services: list[str], default_index: int | None
    ) -> str:  # WHY: define _get_service_selection helper.
        """Read service selection from user input."""
        while True:  # WHY: retry loop until valid selection or custom entry.
            try:
                selection = self._read_service_selection_input(services, default_index)  # WHY: prompt.
                result = self._resolve_service_selection(selection, services, default_index)  # WHY: parse.
                if result.handled:  # WHY: sentinel indicates loop should exit with value.
                    return result.value  # WHY: service selection always resolves to string.
            except KeyboardInterrupt:  # WHY: allow user to abort selection cleanly.
                print("\nOperation cancelled")  # WHY: user-facing abort message.
                raise

    def _read_service_selection_input(
        self, services: list[str], default_index: int | None
    ) -> str:  # WHY: define _read_service_selection_input helper.
        """Build service prompt string and read/trim user input."""
        prompt = f"\nSelect service index (0-{len(services)}) or enter custom"  # WHY: base prompt.
        if default_index is not None:  # WHY: annotate default when present.
            prompt += f" [default: {default_index} ({self.DEFAULT_SERVICE})]: "
        else:
            prompt += ": "  # WHY: no annotation when no default.
        return InputUtils.safe_input(prompt, context="service_ping_service_selection").strip()  # WHY: read.

    def _resolve_service_selection(  # WHY: begin _resolve_service_selection signature.
        self, selection: str, services: list[str], default_index: int | None
    ) -> _ServiceOutcome:
        """Convert raw service selection text into a resolved outcome."""
        if not selection:  # WHY: blank input applies default or reprompts.
            return self._service_default_outcome(services, default_index)
        try:
            selected_index = int(selection)  # WHY: parse numeric selection.
        except ValueError:  # WHY: non-numeric input is accepted as free-form custom service name.
            print(f"!? Custom service: {selection}")
            return _ServiceOutcome(handled=True, value=selection)
        return self._service_index_outcome(selected_index, services)  # WHY: dispatch by parsed index.

    def _service_default_outcome(
        self, services: list[str], default_index: int | None
    ) -> _ServiceOutcome:  # WHY: define _service_default_outcome helper.
        """Return outcome for blank service selection input."""
        if default_index is None:  # WHY: no default -> operator must enter something.
            print("Please enter a service name or select from the list")
            return _ServiceOutcome(handled=False, value="")
        service = services[default_index]  # WHY: pick default entry.
        print(f"!? Using default service: {service}")  # WHY: user-facing default confirmation.
        return _ServiceOutcome(handled=True, value=service)  # WHY: exit loop with default.

    def _service_index_outcome(
        self, selected_index: int, services: list[str]
    ) -> _ServiceOutcome:  # WHY: define _service_index_outcome helper.
        """Return outcome for numeric service selection index."""
        if selected_index == len(services):  # WHY: sentinel value maps to custom-service prompt.
            return _ServiceOutcome(handled=True, value=self._prompt_custom_service())
        if 0 <= selected_index < len(services):  # WHY: valid range -> resolve and print source.
            service = services[selected_index]
            self._print_service_source(service)  # WHY: annotate provenance for operator.
            return _ServiceOutcome(handled=True, value=service)
        print(f"Please enter a number between 0 and {len(services)}")  # WHY: out-of-range retry hint.
        return _ServiceOutcome(handled=False, value="")  # WHY: stay in loop for retry.

    def _print_service_source(self, service: str) -> None:  # WHY: define _print_service_source helper.
        """Print service source label for selected service."""
        if service in self.org_service_names:  # WHY: org services get rich metadata annotation.
            self._print_org_service_source(service)
            return  # WHY: early exit on precondition failure.
        if service in self.device_services:  # WHY: device-config services get simple label.
            print(f"!? Selected device configuration service: {service}")
            return  # WHY: early exit on precondition failure.
        print(f"!? Selected default/custom service: {service}")  # WHY: fallback provenance line.

    def _print_org_service_source(self, service: str) -> None:  # WHY: define _print_org_service_source helper.
        """Print the rich provenance annotation for an org-service selection."""
        print(f"!? Selected organization service: {service}")  # WHY: user-facing provenance line.
        details = self._service_details_for(service)  # WHY: lookup metadata by name.
        if details.get("description"):  # WHY: description only printed when present.
            print(f"  Description: {details['description']}")
        if details.get("type"):  # WHY: type only printed when present.
            print(f"  Type: {details['type']}")

    def _prompt_custom_service(self) -> str:  # WHY: define _prompt_custom_service helper.
        """Prompt for a required custom service name."""
        return self._prompt_nonempty_service(
            "Enter custom service name: ",
            "service_ping_custom_service",
            "Service name cannot be empty",
        )  # WHY: shared nonempty prompt loop.

    def _prompt_required_service(self) -> str:  # WHY: define _prompt_required_service helper.
        """Prompt for service name when discovery returns no services."""
        print("\n-> No services found in organization or device configuration")  # WHY: empty status.
        return self._prompt_nonempty_service(
            "Enter service name: ",
            "service_ping_required_service",
            "Service is required. Please enter a service name.",
        )  # WHY: shared nonempty prompt loop.

    @staticmethod
    def _prompt_nonempty_service(
        prompt: str, context: str, empty_hint: str
    ) -> str:  # WHY: define _prompt_nonempty_service helper.
        """Prompt loop that returns first non-empty trimmed service name."""
        while True:  # WHY: keep asking until operator supplies a value.
            service = InputUtils.safe_input(prompt, context=context).strip()  # WHY: read + trim.
            if service:  # WHY: truthy means non-empty acceptable value.
                print(f"!? Custom service: {service}")  # WHY: confirm accepted value.
                return service
            print(empty_hint)  # WHY: retry hint for empty input.

    def _prompt_for_ping_parameters(self) -> dict[str, Any]:  # WHY: define _prompt_for_ping_parameters helper.
        """Prompt for host/count/size/node ping parameters."""
        host = self._prompt_for_host()  # WHY: read + default target host.
        count = self._prompt_for_count()  # WHY: read + default ping count.
        size = self._prompt_for_size()  # WHY: read + clamp payload size.
        node = self._prompt_for_node()  # WHY: read + validate optional HA node.
        return {"host": host, "count": count, "size": size, "node": node}  # WHY: bundle for payload.

    def _prompt_for_host(self) -> str:  # WHY: define _prompt_for_host helper.
        """Prompt for target host with documented default fallback."""
        host = InputUtils.safe_input(
            "\nEnter target host/IP to ping [default: 8.8.8.8]: ",
            context="service_ping_host",
        ).strip()  # WHY: read + trim.
        if host:  # WHY: user-supplied value takes precedence.
            return host
        print(f"!? Using default destination: {self.DEFAULT_HOST}")  # WHY: user-facing default note.
        return self.DEFAULT_HOST  # WHY: hand documented default back.

    def _prompt_for_count(self) -> int:  # WHY: define _prompt_for_count helper.
        """Prompt for ICMP count with sane fallback."""
        count_input = InputUtils.safe_input(
            "Enter ping count [default: 4]: ",
            context="service_ping_count",
        ).strip()  # WHY: read + trim.
        try:
            count = int(count_input) if count_input else self.DEFAULT_COUNT  # WHY: default when blank.
            return max(1, count)  # WHY: enforce minimum 1 packet.
        except ValueError:  # WHY: non-numeric input falls back to default.
            return self.DEFAULT_COUNT

    def _prompt_for_size(self) -> int:  # WHY: define _prompt_for_size helper.
        """Prompt for ICMP payload size with range clamping."""
        size_input = InputUtils.safe_input(
            "Enter packet size in bytes [default: 56]: ",
            context="service_ping_size",
        ).strip()  # WHY: read + trim.
        try:
            size = int(size_input) if size_input else self.DEFAULT_SIZE  # WHY: default when blank.
            return max(self.MIN_SIZE, min(size, self.MAX_SIZE))  # WHY: clamp to allowed range.
        except ValueError:  # WHY: non-numeric input falls back to default.
            return self.DEFAULT_SIZE

    def _prompt_for_node(self) -> str | None:  # WHY: define _prompt_for_node helper.
        """Prompt for optional HA node identifier."""
        node_input = (
            InputUtils.safe_input(
                "Enter HA node (node0/node1) [optional]: ",
                context="service_ping_node",
            )
            .strip()
            .lower()
        )  # WHY: normalize case before allow-list check.
        return node_input if node_input in _HA_NODES else None  # WHY: only accept allow-list values.

    def _build_payload(
        self, service: str, tenant: str | None, params: dict[str, Any]
    ) -> dict[str, Any]:  # WHY: define _build_payload helper.
        """Compose the service ping payload body for Mist API."""
        payload: dict[str, Any] = {
            "host": params["host"],
            "service": service,
            "count": params["count"],
            "size": params["size"],
        }  # WHY: required fields for mist api call.
        if tenant:  # WHY: tenant is optional per mist api contract.
            payload["tenant"] = tenant
        if params["node"]:  # WHY: HA node is optional per mist api contract.
            payload["node"] = params["node"]
        return payload  # WHY: hand assembled payload back to caller.

    def _display_configuration(self, payload: dict[str, Any]) -> None:  # WHY: define _display_configuration helper.
        """Display selected service ping configuration before execution."""
        print("\n" + "-" * 50)  # WHY: user-facing separator.
        print("Service Ping Configuration:")  # WHY: section header.
        print(f"  Host: {payload['host']}")  # WHY: user-facing detail.
        print(f"  Service: {payload['service']}")  # WHY: user-facing detail.
        print(f"  Count: {payload['count']}")  # WHY: user-facing detail.
        print(f"  Size: {payload['size']} bytes")  # WHY: user-facing detail.
        if payload.get("tenant"):  # WHY: only render tenant line when present.
            print(f"  Tenant: {payload['tenant']}")
        if payload.get("node"):  # WHY: only render node line when present.
            print(f"  HA Node: {payload['node']}")
        print("-" * 50)  # WHY: user-facing separator.
        self._debug_validate_service(payload["service"])  # WHY: emit debug note about service choice.

    def _debug_validate_service(self, service: str) -> None:  # WHY: define _debug_validate_service helper.
        """Print helpful debug annotation for selected service."""
        if not self.debug_mode:  # WHY: annotation only useful in debug mode.
            return  # WHY: early exit on precondition failure.
        if service in _KNOWN_DEBUG_SERVICES:  # WHY: allow-list of known-valid services for debug.
            print(f"[DEBUG] Using known valid service: {service}")
        else:
            print(f"[DEBUG] Using custom service: {service} (may not exist on device)")


@dataclass(frozen=True)  # WHY: frozen keeps selection outcome immutable.
class _SelectionOutcome:  # WHY: define _SelectionOutcome type.
    """Outcome of parsing a raw tenant selection input line."""

    handled: bool  # WHY: True when loop should terminate with value.
    value: str | None  # WHY: resolved tenant name or None when skipped.


@dataclass(frozen=True)  # WHY: frozen keeps selection outcome immutable.
class _ServiceOutcome:  # WHY: define _ServiceOutcome type.
    """Outcome of parsing a raw service selection input line."""

    handled: bool  # WHY: True when loop should terminate with value.
    value: str  # WHY: resolved service name (always string for service prompts).
