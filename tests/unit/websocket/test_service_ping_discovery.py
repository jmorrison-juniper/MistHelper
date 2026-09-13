"""Unit tests for extracted service ping discovery and payload helpers.

Covers src/websocket/service_ping_discovery.py: ``ServicePingDiscoveryMixin`` and
the ``configure_service_ping_discovery_dependencies`` DI entrypoint. The mixin
is the sole discovery/prompt/payload surface used by ServicePingManager, so
these tests pin the branching of every helper — including empty discovery,
malformed device payloads, out-of-range selections, KeyboardInterrupt, and the
HA-node allow-list — to prevent silent regressions during future refactors.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.websocket import service_ping_discovery as spd
from src.websocket.service_ping_discovery import (
    ServicePingDiscoveryDependencies,
    ServicePingDiscoveryMixin,
    _SelectionOutcome,
    _ServiceOutcome,
    configure_service_ping_discovery_dependencies,
)


class _DiscoveryHarness(ServicePingDiscoveryMixin):
    """Small harness class exposing discovery mixin behavior for tests."""

    DEFAULT_HOST = "8.8.8.8"
    DEFAULT_COUNT = 4
    DEFAULT_SIZE = 56
    MIN_SIZE = 56
    MAX_SIZE = 65535
    DEFAULT_TENANT = "testing-tools"
    DEFAULT_SERVICE = "web-session"

    def __init__(self) -> None:
        """Seed instance state so mixin helpers have every attribute they touch."""
        self.debug_mode = False
        self.site_id = "site-1"
        self.device_id = "device-1"
        self.org_tenants: list[str] = ["org-a"]
        self.site_tenants: list[str] = ["site-a"]
        self.policy_tenants: list[str] = ["policy-a"]
        self.template_tenants: list[str] = ["template-a"]
        self.device_tenants: list[str] = ["device-a"]
        self.org_services: list[dict[str, Any]] = [{"name": "svc-a", "type": "custom"}]
        self.org_service_names: list[str] = ["svc-a"]
        self.device_services: list[str] = ["svc-b"]
        self.debug_messages: list[str] = []

    def _debug_print(self, message: str) -> None:
        """Capture debug prints into a list for assertion-friendly inspection."""
        self.debug_messages.append(message)


class _TenantUtils:
    """Fake tenant utility used to control discovery outputs."""

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        """Ignore any injected dependencies — tests only care about the returned lists."""

    def organization_tenants(self) -> list[str]:
        """Return canned org tenants for discovery."""
        return ["org-a", "org-b"]

    def site_tenants(self, _site_id: str) -> list[str]:
        """Return canned site tenants for discovery."""
        return ["site-a", "site-b"]

    def service_policy_tenants(self, _site_id: str) -> list[str]:
        """Return canned service policy tenants for discovery."""
        return ["policy-a", "policy-b"]

    def gateway_template_tenants(self, _site_id: str) -> list[str]:
        """Return canned gateway template tenants for discovery."""
        return ["template-a", "template-b"]


class _EmptyTenantUtils:
    """Fake tenant utility returning empty lists to exercise the empty-source branch."""

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        """Ignore any injected dependencies."""

    def organization_tenants(self) -> list[str]:
        """Return empty org tenants."""
        return []

    def site_tenants(self, _site_id: str) -> list[str]:
        """Return empty site tenants."""
        return []

    def service_policy_tenants(self, _site_id: str) -> list[str]:
        """Return empty policy tenants."""
        return []

    def gateway_template_tenants(self, _site_id: str) -> list[str]:
        """Return empty template tenants."""
        return []


def _configure_discovery(
    *,
    safe_inputs: list[str] | None = None,
    tenant_utils_cls: Any = _TenantUtils,
    org_services: list[dict[str, Any]] | None = None,
    getSiteDevice: MagicMock | None = None,
    getSiteDeviceStats: MagicMock | None = None,
) -> tuple[MagicMock, MagicMock, MagicMock]:
    """Configure extracted discovery dependencies and return input/device/stats mocks."""
    safe_input_mock = MagicMock(side_effect=safe_inputs or [])
    get_device_mock = getSiteDevice or MagicMock()
    get_stats_mock = getSiteDeviceStats or MagicMock()
    configure_service_ping_discovery_dependencies(
        ServicePingDiscoveryDependencies(
            apisession=object(),
            mistapi=SimpleNamespace(
                api=SimpleNamespace(
                    v1=SimpleNamespace(
                        sites=SimpleNamespace(
                            devices=SimpleNamespace(getSiteDevice=get_device_mock),
                            stats=SimpleNamespace(getSiteDeviceStats=get_stats_mock),
                        )
                    )
                )
            ),
            api_tenant_fetch_utils=tenant_utils_cls,
            config_utils=SimpleNamespace(get_cached_or_prompted_org_id=MagicMock(return_value="org-1")),
            api_fetch_utils=SimpleNamespace(
                organization_services=MagicMock(
                    return_value=org_services if org_services is not None else [{"name": "svc-a"}]
                )
            ),
            input_utils=SimpleNamespace(safe_input=safe_input_mock),
        )
    )
    return safe_input_mock, get_device_mock, get_stats_mock


# ---------------------------------------------------------------------------
# Module-level DI + dataclasses
# ---------------------------------------------------------------------------


def test_configure_publishes_all_dependencies_to_module_scope() -> None:
    """configure_service_ping_discovery_dependencies wires all fields into module globals."""
    marker_apisession = object()
    marker_mistapi = object()
    marker_tenant = object()
    marker_config = object()
    marker_fetch = object()
    marker_input = object()
    configure_service_ping_discovery_dependencies(
        ServicePingDiscoveryDependencies(
            apisession=marker_apisession,
            mistapi=marker_mistapi,
            api_tenant_fetch_utils=marker_tenant,
            config_utils=marker_config,
            api_fetch_utils=marker_fetch,
            input_utils=marker_input,
        )
    )
    assert spd.apisession is marker_apisession
    assert spd.mistapi is marker_mistapi
    assert spd.APITenantFetchUtils is marker_tenant
    assert spd.ConfigUtils is marker_config
    assert spd.APIFetchUtils is marker_fetch
    assert spd.InputUtils is marker_input


def test_selection_outcome_dataclass_is_frozen_and_carries_fields() -> None:
    """_SelectionOutcome stores handled/value and is immutable."""
    outcome = _SelectionOutcome(handled=True, value="v")
    assert outcome.handled is True
    assert outcome.value == "v"
    with pytest.raises(FrozenInstanceError):
        outcome.value = "x"  # type: ignore[misc]


def test_service_outcome_dataclass_is_frozen_and_carries_fields() -> None:
    """_ServiceOutcome stores handled/value and is immutable."""
    outcome = _ServiceOutcome(handled=True, value="svc")
    assert outcome.handled is True
    assert outcome.value == "svc"
    with pytest.raises(FrozenInstanceError):
        outcome.value = "x"  # type: ignore[misc]


def test_module_constants_are_expected_values() -> None:
    """Module-level constants match documented allow-lists and caps."""
    assert spd._MAX_TENANT_SOURCES == 5
    assert spd._KNOWN_DEBUG_SERVICES == ("web-session", "LANS", "RBO_SSH")
    assert spd._HA_NODES == ("node0", "node1")


# ---------------------------------------------------------------------------
# Tenant fetch helpers
# ---------------------------------------------------------------------------


def test_fetch_all_tenants_populates_every_source(capsys) -> None:
    """_fetch_all_tenants delegates to each per-source helper and prints status headers."""
    _configure_discovery()
    harness = _DiscoveryHarness()
    harness.org_tenants = []
    harness.site_tenants = []
    harness.policy_tenants = []
    harness.template_tenants = []
    harness._fetch_all_tenants()
    out = capsys.readouterr().out
    assert "Fetching organization tenants" in out
    assert "Fetching site tenants" in out
    assert "Fetching service policy tenants" in out
    assert "Fetching gateway template tenants" in out
    assert harness.org_tenants == ["org-a", "org-b"]
    assert harness.site_tenants == ["site-a", "site-b"]
    assert harness.policy_tenants == ["policy-a", "policy-b"]
    assert harness.template_tenants == ["template-a", "template-b"]


def test_fetch_site_tenants_early_returns_when_site_id_missing() -> None:
    """_fetch_site_tenants must not call utility when site_id is None."""
    _configure_discovery()
    harness = _DiscoveryHarness()
    harness.site_id = None
    harness.site_tenants = ["preserved"]
    harness._fetch_site_tenants()
    assert harness.site_tenants == ["preserved"]  # unchanged


def test_store_tenant_source_skips_empty_and_prints_status(capsys) -> None:
    """_store_tenant_source: empty list prints no-found status and does not mutate attribute."""
    _configure_discovery()
    harness = _DiscoveryHarness()
    harness.some_attr = ["preserved"]  # type: ignore[attr-defined]
    harness._store_tenant_source("some_attr", [], "site-level")
    assert "No site-level tenants found" in capsys.readouterr().out
    assert harness.some_attr == ["preserved"]  # type: ignore[attr-defined]


def test_store_tenant_source_populates_attribute_and_logs_debug(capsys) -> None:
    """_store_tenant_source: non-empty list assigns attr + prints count + emits debug."""
    _configure_discovery()
    harness = _DiscoveryHarness()
    harness._store_tenant_source("policy_tenants", ["p1", "p2"], "service policy")
    out = capsys.readouterr().out
    assert "Found 2 service policy tenants" in out
    assert harness.policy_tenants == ["p1", "p2"]
    assert any("Service policy tenants" in msg for msg in harness.debug_messages)


def test_tenant_utils_builds_fresh_instance_via_injected_class() -> None:
    """_tenant_utils returns a new APITenantFetchUtils instance each call."""
    _configure_discovery()
    utils1 = ServicePingDiscoveryMixin._tenant_utils()
    utils2 = ServicePingDiscoveryMixin._tenant_utils()
    assert utils1 is not utils2
    assert isinstance(utils1, _TenantUtils)


# ---------------------------------------------------------------------------
# Service fetch helpers
# ---------------------------------------------------------------------------


def test_fetch_all_services_prints_status_and_calls_both_helpers(capsys) -> None:
    """_fetch_all_services prints org+device headers and invokes each helper."""
    _configure_discovery(org_services=[])
    harness = _DiscoveryHarness()
    # Force device_config to fail cleanly so we hit the exception branch of _fetch_device_config
    _configure_discovery(
        org_services=[],
        getSiteDevice=MagicMock(side_effect=RuntimeError("boom")),
    )
    harness._fetch_all_services()
    out = capsys.readouterr().out
    assert "Fetching organization services" in out
    assert "Fetching device configuration" in out


def test_fetch_org_services_empty_prints_status(capsys) -> None:
    """_fetch_org_services: empty list prints message and leaves caches untouched."""
    _configure_discovery(org_services=[])
    harness = _DiscoveryHarness()
    harness.org_services = [{"name": "preserved"}]
    harness.org_service_names = ["preserved"]
    harness._fetch_org_services()
    assert "No organization-level services found" in capsys.readouterr().out
    assert harness.org_services == [{"name": "preserved"}]


def test_fetch_org_services_populates_caches(capsys) -> None:
    """_fetch_org_services: non-empty list caches raw list + name list and skips nameless entries."""
    _configure_discovery(org_services=[{"name": "s1"}, {"type": "no-name"}, {"name": "s2"}])
    harness = _DiscoveryHarness()
    harness._fetch_org_services()
    assert harness.org_service_names == ["s1", "s2"]
    assert "Found 2 organization-level services" in capsys.readouterr().out


def test_fetch_device_config_swallows_exception_and_prints_warning(capsys) -> None:
    """_fetch_device_config: any exception is logged as warning; user-facing message printed."""
    _configure_discovery(getSiteDevice=MagicMock(side_effect=RuntimeError("network boom")))
    harness = _DiscoveryHarness()
    harness._fetch_device_config()
    assert "Cannot retrieve device configuration" in capsys.readouterr().out
    assert any("Config error" in msg for msg in harness.debug_messages)


def test_fetch_device_config_success_path_populates_device_lists(capsys) -> None:
    """_fetch_device_config: happy path pulls tenants/services from config and stats."""
    device_resp = SimpleNamespace(
        data={
            "service_policies": [{"tenant": "tconf", "services": [{"name": "sconf"}]}],
            "routing_instances": [{"name": "rt-a"}, {"name": "_system"}],
            "router": {"tenants": [{"name": "rt-b"}], "services": [{"name": "rt-svc"}]},
        }
    )
    stats_resp = SimpleNamespace(data={"service_stat": [{"name": "sstats"}]})
    _configure_discovery(
        getSiteDevice=MagicMock(return_value=device_resp),
        getSiteDeviceStats=MagicMock(return_value=stats_resp),
    )
    harness = _DiscoveryHarness()
    harness.device_tenants = []
    harness.device_services = []
    harness._fetch_device_config()
    assert "tconf" in harness.device_tenants
    assert "rt-a" in harness.device_tenants
    assert "rt-b" in harness.device_tenants
    assert "_system" not in harness.device_tenants
    assert "sconf" in harness.device_services
    assert "rt-svc" in harness.device_services
    assert "sstats" in harness.device_services
    out = capsys.readouterr().out
    assert "Found 3 tenants from device configuration" in out


def test_retrieve_device_config_tolerates_missing_data_attribute() -> None:
    """_retrieve_device_config: getattr default kicks in when response has no .data."""
    _configure_discovery(getSiteDevice=MagicMock(return_value=object()))
    harness = _DiscoveryHarness()
    result = harness._retrieve_device_config()
    assert result == {}


# ---------------------------------------------------------------------------
# Config-extraction helpers
# ---------------------------------------------------------------------------


def test_sorted_non_system_filters_empty_and_underscore_prefixed() -> None:
    """_sorted_non_system drops empty strings and _-prefixed names then sorts result."""
    result = ServicePingDiscoveryMixin._sorted_non_system({"b", "a", "", "_sys", "c"})
    assert result == ["a", "b", "c"]


def test_collect_from_service_policies_skips_non_dict_entries() -> None:
    """_collect_from_service_policies: non-dict entries are skipped, dict tenants/services collected."""
    tenants: set[str] = set()
    services: set[str] = set()
    config = {"service_policies": [{"tenant": "t1", "services": [{"name": "s1"}]}, "not-a-dict", {}]}
    ServicePingDiscoveryMixin._collect_from_service_policies(config, tenants, services)
    assert tenants == {"t1"}
    assert services == {"s1"}


def test_collect_from_routing_instances_keeps_only_operator_names() -> None:
    """_collect_from_routing_instances: skips non-dict and underscore-prefixed names."""
    tenants: set[str] = set()
    config = {"routing_instances": [{"name": "keep"}, {"name": "_skip"}, "bad", {"name": ""}, {"other": "x"}]}
    ServicePingDiscoveryMixin._collect_from_routing_instances(config, tenants)
    assert tenants == {"keep"}


def test_extract_services_from_policy_bad_services_type_early_returns() -> None:
    """_extract_services_from_policy: non-list services key triggers early return with no side effects."""
    services: set[str] = set()
    ServicePingDiscoveryMixin._extract_services_from_policy({"services": "not-a-list"}, services)
    assert services == set()


def test_add_service_reference_handles_dict_str_and_other() -> None:
    """_add_service_reference: dict form uses name, str form recorded raw, other types ignored."""
    services: set[str] = set()
    ServicePingDiscoveryMixin._add_service_reference({"name": "dict-svc"}, services)
    ServicePingDiscoveryMixin._add_service_reference({"name": ""}, services)  # dict with empty name → skip
    ServicePingDiscoveryMixin._add_service_reference("str-svc", services)
    ServicePingDiscoveryMixin._add_service_reference(42, services)  # int → ignored
    ServicePingDiscoveryMixin._add_service_reference({"other": "x"}, services)  # dict without name → skip
    assert services == {"dict-svc", "str-svc"}


def test_collect_from_router_config_non_dict_early_returns() -> None:
    """_collect_from_router_config: non-dict router argument short-circuits without side effects."""
    tenants: set[str] = set()
    services: set[str] = set()
    ServicePingDiscoveryMixin._collect_from_router_config("not-a-dict", tenants, services)  # type: ignore[arg-type]
    assert tenants == set()
    assert services == set()


def test_collect_from_router_config_populates_from_named_lists() -> None:
    """_collect_from_router_config: pulls tenants + services from dict router payload."""
    tenants: set[str] = set()
    services: set[str] = set()
    router = {"tenants": [{"name": "rt-1"}], "services": [{"name": "rs-1"}]}
    ServicePingDiscoveryMixin._collect_from_router_config(router, tenants, services)
    assert tenants == {"rt-1"}
    assert services == {"rs-1"}


def test_collect_named_items_skips_non_dict_and_empty_names() -> None:
    """_collect_named_items only accepts dicts with a truthy name."""
    sink: set[str] = set()
    ServicePingDiscoveryMixin._collect_named_items([{"name": "ok"}, "bad", {"name": ""}, {}], sink)
    assert sink == {"ok"}


# ---------------------------------------------------------------------------
# Stats extraction helpers
# ---------------------------------------------------------------------------


def test_extract_from_device_stats_swallows_exception(capsys) -> None:
    """_extract_from_device_stats: an exception on stats retrieval is logged to debug and swallowed."""
    _configure_discovery(getSiteDeviceStats=MagicMock(side_effect=RuntimeError("no stats")))
    harness = _DiscoveryHarness()
    harness._extract_from_device_stats()  # must not raise
    assert any("Could not fetch stats" in m for m in harness.debug_messages)


def test_merge_stats_services_appends_and_dedups_and_sorts() -> None:
    """_merge_stats_services: appends new names, skips duplicates, and re-sorts device_services."""
    _configure_discovery()
    harness = _DiscoveryHarness()
    harness.device_services = ["c-existing"]
    stats_data = {"service_stat": [{"name": "b-new"}, {"name": "a-new"}, {"name": "c-existing"}]}
    harness._merge_stats_services(stats_data)
    assert harness.device_services == ["a-new", "b-new", "c-existing"]


def test_service_stat_name_filters_bad_shapes_and_system_names() -> None:
    """_service_stat_name: non-dict, missing name, empty name, and _-prefixed all return None."""
    assert ServicePingDiscoveryMixin._service_stat_name("bad") is None
    assert ServicePingDiscoveryMixin._service_stat_name({}) is None
    assert ServicePingDiscoveryMixin._service_stat_name({"name": ""}) is None
    assert ServicePingDiscoveryMixin._service_stat_name({"name": "_sys"}) is None
    assert ServicePingDiscoveryMixin._service_stat_name({"name": "good"}) == "good"


def test_retrieve_device_stats_tolerates_missing_data_attribute() -> None:
    """_retrieve_device_stats: getattr default kicks in when response has no .data."""
    _configure_discovery(getSiteDeviceStats=MagicMock(return_value=object()))
    harness = _DiscoveryHarness()
    result = harness._retrieve_device_stats()
    assert result == {}


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def test_report_device_config_results_both_populated(capsys) -> None:
    """_report_device_config_results: emits count messages when both lists are populated."""
    _configure_discovery()
    harness = _DiscoveryHarness()
    harness.device_tenants = ["t1", "t2"]
    harness.device_services = ["s1"]
    harness._report_device_config_results()
    out = capsys.readouterr().out
    assert "Found 2 tenants from device configuration" in out
    assert "Found 1 additional services from device configuration" in out


def test_report_device_config_results_both_empty(capsys) -> None:
    """_report_device_config_results: emits no-found messages when both lists are empty."""
    _configure_discovery()
    harness = _DiscoveryHarness()
    harness.device_tenants = []
    harness.device_services = []
    harness._report_device_config_results()
    out = capsys.readouterr().out
    assert "No tenants found in device configuration" in out
    assert "No additional services found in device configuration" in out


# ---------------------------------------------------------------------------
# Combined list builders
# ---------------------------------------------------------------------------


def test_build_combined_tenants_preserves_order_and_adds_default() -> None:
    """_build_combined_tenants: merges sources in precedence order and appends default."""
    _configure_discovery()
    harness = _DiscoveryHarness()
    combined = harness._build_combined_tenants()
    assert combined == ["org-a", "site-a", "policy-a", "template-a", "device-a", "testing-tools"]


def test_build_combined_tenants_default_already_present_not_reappended() -> None:
    """_build_combined_tenants: default is not double-appended if already present."""
    _configure_discovery()
    harness = _DiscoveryHarness()
    harness.org_tenants = ["testing-tools", "org-a"]
    combined = harness._build_combined_tenants()
    assert combined.count("testing-tools") == 1


def test_build_combined_services_preserves_order_and_adds_default() -> None:
    """_build_combined_services: merges org + device and appends default."""
    _configure_discovery()
    harness = _DiscoveryHarness()
    combined = harness._build_combined_services()
    assert combined == ["svc-a", "svc-b", "web-session"]


def test_build_combined_services_default_already_present_not_reappended() -> None:
    """_build_combined_services: default is not double-appended if already present."""
    _configure_discovery()
    harness = _DiscoveryHarness()
    harness.org_service_names = ["web-session", "svc-a"]
    combined = harness._build_combined_services()
    assert combined.count("web-session") == 1


def test_append_new_items_preserves_order_and_dedups() -> None:
    """_append_new_items: appends items missing from sink, preserving order."""
    sink = ["a"]
    ServicePingDiscoveryMixin._append_new_items(["a", "b", "c", "b"], sink)
    assert sink == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# Tenant prompt: full loop coverage
# ---------------------------------------------------------------------------


def test_prompt_for_tenant_no_available_falls_back_to_manual(capsys) -> None:
    """_prompt_for_tenant: empty list delegates to _prompt_manual_tenant."""
    _configure_discovery(safe_inputs=["manual-t"])
    harness = _DiscoveryHarness()
    result = harness._prompt_for_tenant([])
    assert result == "manual-t"
    assert "Manual tenant: manual-t" in capsys.readouterr().out


def test_prompt_for_tenant_default_index_present_blank_returns_default(capsys) -> None:
    """_prompt_for_tenant: blank input returns the DEFAULT_TENANT entry when present in list."""
    _configure_discovery(safe_inputs=[""])
    harness = _DiscoveryHarness()
    result = harness._prompt_for_tenant(["a", harness.DEFAULT_TENANT])
    assert result == harness.DEFAULT_TENANT
    assert "Using default tenant" in capsys.readouterr().out


def test_prompt_for_tenant_valid_numeric_index_returns_value(capsys) -> None:
    """_prompt_for_tenant: valid numeric index returns matching tenant + prints source."""
    _configure_discovery(safe_inputs=["0"])
    harness = _DiscoveryHarness()
    result = harness._prompt_for_tenant(["org-a", "site-a"])
    assert result == "org-a"
    assert "organization tenant" in capsys.readouterr().out


def test_prompt_for_tenant_skip_sentinel_returns_none(capsys) -> None:
    """_prompt_for_tenant: entering N (list length) skips selection."""
    _configure_discovery(safe_inputs=["2"])
    harness = _DiscoveryHarness()
    result = harness._prompt_for_tenant(["a", "b"])
    assert result is None
    assert "Skipping tenant selection" in capsys.readouterr().out


def test_prompt_for_tenant_out_of_range_reprompts_then_returns(capsys) -> None:
    """_prompt_for_tenant: out-of-range numeric loops back and reprompts."""
    _configure_discovery(safe_inputs=["999", "0"])
    harness = _DiscoveryHarness()
    result = harness._prompt_for_tenant(["org-a"])
    assert result == "org-a"
    assert "Please enter a number between" in capsys.readouterr().out


def test_prompt_for_tenant_non_numeric_reprompts_then_returns(capsys) -> None:
    """_prompt_for_tenant: non-numeric loops back and prints a valid-number hint."""
    _configure_discovery(safe_inputs=["abc", "0"])
    harness = _DiscoveryHarness()
    result = harness._prompt_for_tenant(["org-a"])
    assert result == "org-a"
    assert "Please enter a valid number" in capsys.readouterr().out


def test_prompt_for_tenant_keyboardinterrupt_raises(capsys) -> None:
    """_prompt_for_tenant: KeyboardInterrupt is re-raised after user-facing cancel line."""
    safe_input = MagicMock(side_effect=KeyboardInterrupt())
    _configure_discovery()
    spd.InputUtils = SimpleNamespace(safe_input=safe_input)
    harness = _DiscoveryHarness()
    with pytest.raises(KeyboardInterrupt):
        harness._prompt_for_tenant(["a"])
    assert "Operation cancelled" in capsys.readouterr().out


def test_tenant_default_outcome_no_default_configured_returns_none() -> None:
    """_tenant_default_outcome: no default index -> handled=True, value=None (skip)."""
    _configure_discovery()
    harness = _DiscoveryHarness()
    result = harness._tenant_default_outcome(["a"], None)
    assert result == _SelectionOutcome(handled=True, value=None)


def test_read_tenant_selection_input_no_default_annotates_skip() -> None:
    """_read_tenant_selection_input: absent default index annotates '[default: skip]'."""
    safe_input, _, _ = _configure_discovery(safe_inputs=["7"])
    harness = _DiscoveryHarness()
    result = harness._read_tenant_selection_input(["a", "b"], None)
    assert result == "7"
    prompt = safe_input.call_args.args[0]
    assert "default: skip" in prompt


def test_print_tenant_source_falls_through_to_custom(capsys) -> None:
    """_print_tenant_source: tenant not found in any source falls through to default/custom line."""
    _configure_discovery()
    harness = _DiscoveryHarness()
    harness._print_tenant_source("unknown")
    assert "default/custom tenant: unknown" in capsys.readouterr().out


def test_prompt_manual_tenant_blank_returns_none(capsys) -> None:
    """_prompt_manual_tenant: blank input returns None + prints proceed-without-tenant warning."""
    _configure_discovery(safe_inputs=[""])
    harness = _DiscoveryHarness()
    result = harness._prompt_manual_tenant()
    assert result is None
    assert "Proceeding without tenant" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Tenant category display helpers
# ---------------------------------------------------------------------------


def test_display_tenant_categories_prints_ordered_sections(capsys) -> None:
    """_display_tenant_categories: prints per-source labeled sections with running index."""
    _configure_discovery()
    harness = _DiscoveryHarness()
    harness._display_tenant_categories(["org-a", "site-a", "policy-a", "template-a", "device-a", "extra"])
    out = capsys.readouterr().out
    assert "Organization Tenants" in out
    assert "Site Tenants" in out
    assert "Additional Tenants" in out


def test_category_tuple_has_expected_shape() -> None:
    """_category_tuple: returns (header, items, suffix) with '  Title (N):' formatting."""
    result = ServicePingDiscoveryMixin._category_tuple("Title", ["a", "b"], "(suffix)")
    assert result == ("  Title (2):", ["a", "b"], "(suffix)")


def test_filter_unique_excludes_union_of_lists() -> None:
    """_filter_unique: excludes items appearing in any of the *exclude_lists arguments."""
    result = ServicePingDiscoveryMixin._filter_unique(["a", "b", "c", "d"], ["a"], ["c"])
    assert result == ["b", "d"]


def test_print_indexed_category_skips_empty_section(capsys) -> None:
    """_print_indexed_category: empty items list returns index unchanged and prints nothing."""
    next_idx = ServicePingDiscoveryMixin._print_indexed_category("Label", [], "(suffix)", 5)
    assert next_idx == 5
    assert capsys.readouterr().out == ""


def test_print_indexed_category_prints_header_then_entries(capsys) -> None:
    """_print_indexed_category: prints header, then each entry with running index and suffix."""
    next_idx = ServicePingDiscoveryMixin._print_indexed_category("Label:", ["x", "y"], "(s)", 3)
    assert next_idx == 5
    out = capsys.readouterr().out
    assert "Label:" in out
    assert "[3] x (s)" in out
    assert "[4] y (s)" in out


def test_default_index_present_and_absent() -> None:
    """_default_index: returns index when default present, None when absent."""
    assert ServicePingDiscoveryMixin._default_index(["a", "b", "c"], "b") == 1
    assert ServicePingDiscoveryMixin._default_index(["a", "b"], "missing") is None


# ---------------------------------------------------------------------------
# Service prompt: full loop coverage
# ---------------------------------------------------------------------------


def test_prompt_for_service_no_available_delegates_to_required(capsys) -> None:
    """_prompt_for_service: empty list delegates to _prompt_required_service."""
    _configure_discovery(safe_inputs=["req-svc"])
    harness = _DiscoveryHarness()
    result = harness._prompt_for_service([])
    assert result == "req-svc"
    assert "Custom service: req-svc" in capsys.readouterr().out


def test_prompt_for_service_blank_default_returns_default(capsys) -> None:
    """_prompt_for_service: blank input picks DEFAULT_SERVICE when present."""
    _configure_discovery(safe_inputs=[""])
    harness = _DiscoveryHarness()
    result = harness._prompt_for_service(["svc-a", harness.DEFAULT_SERVICE])
    assert result == harness.DEFAULT_SERVICE
    assert "Using default service" in capsys.readouterr().out


def test_prompt_for_service_blank_no_default_reprompts_then_accepts(capsys) -> None:
    """_prompt_for_service: blank input with no default prints hint and reprompts."""
    _configure_discovery(safe_inputs=["", "0"])
    harness = _DiscoveryHarness()
    result = harness._prompt_for_service(["only-svc"])
    assert result == "only-svc"
    assert "Please enter a service name" in capsys.readouterr().out


def test_prompt_for_service_valid_index_returns_and_prints_source(capsys) -> None:
    """_prompt_for_service: valid numeric index returns service and prints source annotation."""
    _configure_discovery(safe_inputs=["0"])
    harness = _DiscoveryHarness()
    result = harness._prompt_for_service(["svc-a", "svc-b"])
    assert result == "svc-a"
    assert "organization service" in capsys.readouterr().out


def test_prompt_for_service_custom_sentinel_delegates_to_prompt(capsys) -> None:
    """_prompt_for_service: N-index triggers custom-service prompt loop."""
    _configure_discovery(safe_inputs=["2", "custom-svc"])
    harness = _DiscoveryHarness()
    result = harness._prompt_for_service(["a", "b"])
    assert result == "custom-svc"
    assert "Custom service: custom-svc" in capsys.readouterr().out


def test_prompt_for_service_non_numeric_returns_as_custom_immediately(capsys) -> None:
    """_prompt_for_service: non-numeric input is accepted as a custom service name (no reprompt)."""
    _configure_discovery(safe_inputs=["free-form"])
    harness = _DiscoveryHarness()
    result = harness._prompt_for_service(["a"])
    assert result == "free-form"
    assert "Custom service: free-form" in capsys.readouterr().out


def test_prompt_for_service_out_of_range_reprompts(capsys) -> None:
    """_prompt_for_service: out-of-range numeric reprompts with helpful hint."""
    _configure_discovery(safe_inputs=["99", "0"])
    harness = _DiscoveryHarness()
    result = harness._prompt_for_service(["a"])
    assert result == "a"
    assert "Please enter a number between" in capsys.readouterr().out


def test_prompt_for_service_keyboardinterrupt_raises(capsys) -> None:
    """_prompt_for_service: KeyboardInterrupt is re-raised after user-facing cancel line."""
    _configure_discovery()
    spd.InputUtils = SimpleNamespace(safe_input=MagicMock(side_effect=KeyboardInterrupt()))
    harness = _DiscoveryHarness()
    with pytest.raises(KeyboardInterrupt):
        harness._prompt_for_service(["a"])
    assert "Operation cancelled" in capsys.readouterr().out


def test_read_service_selection_input_no_default_no_annotation() -> None:
    """_read_service_selection_input: absent default index → prompt without default annotation."""
    safe_input, _, _ = _configure_discovery(safe_inputs=["x"])
    harness = _DiscoveryHarness()
    harness._read_service_selection_input(["a", "b"], None)
    prompt = safe_input.call_args.args[0]
    assert "[default" not in prompt


def test_service_default_outcome_no_default_returns_unhandled(capsys) -> None:
    """_service_default_outcome: absent default_index -> handled=False (reprompt required)."""
    _configure_discovery()
    harness = _DiscoveryHarness()
    result = harness._service_default_outcome(["a"], None)
    assert result == _ServiceOutcome(handled=False, value="")
    assert "Please enter a service name" in capsys.readouterr().out


def test_print_service_source_device_only_branch(capsys) -> None:
    """_print_service_source: service in device_services (not org) prints device-config label."""
    _configure_discovery()
    harness = _DiscoveryHarness()
    harness._print_service_source("svc-b")
    assert "device configuration service: svc-b" in capsys.readouterr().out


def test_print_service_source_falls_through_to_custom(capsys) -> None:
    """_print_service_source: unknown service prints default/custom label."""
    _configure_discovery()
    harness = _DiscoveryHarness()
    harness._print_service_source("unknown-svc")
    assert "default/custom service: unknown-svc" in capsys.readouterr().out


def test_print_org_service_source_with_description_and_type(capsys) -> None:
    """_print_org_service_source: rich annotation includes Description + Type when present."""
    _configure_discovery()
    harness = _DiscoveryHarness()
    harness.org_services = [{"name": "svc-a", "type": "web", "description": "the service"}]
    harness._print_org_service_source("svc-a")
    out = capsys.readouterr().out
    assert "organization service: svc-a" in out
    assert "Description: the service" in out
    assert "Type: web" in out


def test_print_org_service_source_without_description_or_type(capsys) -> None:
    """_print_org_service_source: missing description/type skips those lines."""
    _configure_discovery()
    harness = _DiscoveryHarness()
    harness.org_services = [{"name": "svc-a"}]
    harness._print_org_service_source("svc-a")
    out = capsys.readouterr().out
    assert "organization service: svc-a" in out
    assert "Description:" not in out
    assert "Type:" not in out


def test_print_org_services_section_empty_returns_start_index(capsys) -> None:
    """_print_org_services_section: no org names -> returns start index and prints nothing."""
    _configure_discovery()
    harness = _DiscoveryHarness()
    harness.org_service_names = []
    result = harness._print_org_services_section(5)
    assert result == 5
    assert capsys.readouterr().out == ""


def test_print_org_service_line_with_description(capsys) -> None:
    """_print_org_service_line: description present -> rich formatted line."""
    ServicePingDiscoveryMixin._print_org_service_line(2, "svc", {"type": "t", "description": "d"})
    assert "[2] svc (t) - d" in capsys.readouterr().out


def test_print_org_service_line_without_description(capsys) -> None:
    """_print_org_service_line: description absent -> compact label with default 'custom' type."""
    ServicePingDiscoveryMixin._print_org_service_line(3, "svc", {})
    assert "[3] svc (custom)" in capsys.readouterr().out


def test_service_details_for_missing_returns_empty_dict() -> None:
    """_service_details_for: missing name returns empty dict via next() default."""
    _configure_discovery()
    harness = _DiscoveryHarness()
    assert harness._service_details_for("nope") == {}


def test_display_service_categories_prints_all_sections(capsys) -> None:
    """_display_service_categories: prints org + device-only + additional sections."""
    _configure_discovery()
    harness = _DiscoveryHarness()
    harness._display_service_categories(["svc-a", "svc-b", "extra"])
    out = capsys.readouterr().out
    assert "Organization Services" in out
    assert "Device Configuration Services" in out
    assert "Additional Services" in out


def test_prompt_custom_service_loops_until_nonempty(capsys) -> None:
    """_prompt_custom_service: empty input reprompts until a non-empty value is provided."""
    _configure_discovery(safe_inputs=["", "  ", "final-svc"])
    harness = _DiscoveryHarness()
    result = harness._prompt_custom_service()
    assert result == "final-svc"
    out = capsys.readouterr().out
    assert out.count("Service name cannot be empty") == 2


def test_prompt_required_service_loops_until_nonempty(capsys) -> None:
    """_prompt_required_service: empty input reprompts with required-service hint."""
    _configure_discovery(safe_inputs=["", "svc-final"])
    harness = _DiscoveryHarness()
    result = harness._prompt_required_service()
    assert result == "svc-final"
    out = capsys.readouterr().out
    assert "No services found" in out
    assert "Service is required" in out


# ---------------------------------------------------------------------------
# Ping parameter prompts
# ---------------------------------------------------------------------------


def test_prompt_for_host_uses_default_on_blank(capsys) -> None:
    """_prompt_for_host: blank input returns DEFAULT_HOST + prints default confirmation."""
    _configure_discovery(safe_inputs=[""])
    harness = _DiscoveryHarness()
    result = harness._prompt_for_host()
    assert result == harness.DEFAULT_HOST
    assert "Using default destination" in capsys.readouterr().out


def test_prompt_for_host_returns_user_value() -> None:
    """_prompt_for_host: non-blank input returned verbatim."""
    _configure_discovery(safe_inputs=["1.2.3.4"])
    harness = _DiscoveryHarness()
    assert harness._prompt_for_host() == "1.2.3.4"


def test_prompt_for_count_valid_input() -> None:
    """_prompt_for_count: valid numeric input honored, clamped to at least 1."""
    _configure_discovery(safe_inputs=["10"])
    harness = _DiscoveryHarness()
    assert harness._prompt_for_count() == 10


def test_prompt_for_count_zero_clamped_to_one() -> None:
    """_prompt_for_count: zero input clamped up to 1 (minimum packet count)."""
    _configure_discovery(safe_inputs=["0"])
    harness = _DiscoveryHarness()
    assert harness._prompt_for_count() == 1


def test_prompt_for_count_blank_returns_default() -> None:
    """_prompt_for_count: blank input returns DEFAULT_COUNT (via inline conditional)."""
    _configure_discovery(safe_inputs=[""])
    harness = _DiscoveryHarness()
    assert harness._prompt_for_count() == harness.DEFAULT_COUNT


def test_prompt_for_count_non_numeric_returns_default() -> None:
    """_prompt_for_count: non-numeric ValueError falls back to DEFAULT_COUNT."""
    _configure_discovery(safe_inputs=["abc"])
    harness = _DiscoveryHarness()
    assert harness._prompt_for_count() == harness.DEFAULT_COUNT


def test_prompt_for_size_clamps_to_range() -> None:
    """_prompt_for_size: values outside [MIN_SIZE, MAX_SIZE] are clamped to the range."""
    _configure_discovery(safe_inputs=["10"])
    harness = _DiscoveryHarness()
    assert harness._prompt_for_size() == harness.MIN_SIZE
    _configure_discovery(safe_inputs=["99999999"])
    assert harness._prompt_for_size() == harness.MAX_SIZE
    _configure_discovery(safe_inputs=["512"])
    assert harness._prompt_for_size() == 512


def test_prompt_for_size_blank_returns_default() -> None:
    """_prompt_for_size: blank input returns DEFAULT_SIZE."""
    _configure_discovery(safe_inputs=[""])
    harness = _DiscoveryHarness()
    assert harness._prompt_for_size() == harness.DEFAULT_SIZE


def test_prompt_for_size_non_numeric_returns_default() -> None:
    """_prompt_for_size: ValueError falls back to DEFAULT_SIZE."""
    _configure_discovery(safe_inputs=["abc"])
    harness = _DiscoveryHarness()
    assert harness._prompt_for_size() == harness.DEFAULT_SIZE


def test_prompt_for_node_accepts_allowlist_values() -> None:
    """_prompt_for_node: only 'node0'/'node1' (any case) accepted; anything else -> None."""
    _configure_discovery(safe_inputs=["NODE1"])
    harness = _DiscoveryHarness()
    assert harness._prompt_for_node() == "node1"
    _configure_discovery(safe_inputs=["node2"])
    assert harness._prompt_for_node() is None
    _configure_discovery(safe_inputs=[""])
    assert harness._prompt_for_node() is None


def test_prompt_for_ping_parameters_end_to_end() -> None:
    """_prompt_for_ping_parameters: bundles host/count/size/node prompts into single dict."""
    _configure_discovery(safe_inputs=["1.1.1.1", "5", "128", "node0"])
    harness = _DiscoveryHarness()
    params = harness._prompt_for_ping_parameters()
    assert params == {"host": "1.1.1.1", "count": 5, "size": 128, "node": "node0"}


# ---------------------------------------------------------------------------
# Payload composition + display + debug validation
# ---------------------------------------------------------------------------


def test_build_payload_omits_tenant_and_node_when_missing() -> None:
    """_build_payload: omits tenant and node when tenant is None / node empty."""
    _configure_discovery()
    harness = _DiscoveryHarness()
    payload = harness._build_payload("svc", None, {"host": "h", "count": 1, "size": 2, "node": None})
    assert payload == {"host": "h", "service": "svc", "count": 1, "size": 2}


def test_build_payload_includes_tenant_and_node_when_present() -> None:
    """_build_payload: adds tenant + node fields when they are truthy."""
    _configure_discovery()
    harness = _DiscoveryHarness()
    payload = harness._build_payload("svc", "t1", {"host": "h", "count": 1, "size": 2, "node": "node1"})
    assert payload["tenant"] == "t1"
    assert payload["node"] == "node1"


def test_display_configuration_prints_all_fields_when_present(capsys) -> None:
    """_display_configuration: prints host/service/count/size plus optional tenant/node when present."""
    _configure_discovery()
    harness = _DiscoveryHarness()
    payload = {
        "host": "h",
        "service": "svc",
        "count": 4,
        "size": 56,
        "tenant": "t1",
        "node": "node1",
    }
    harness._display_configuration(payload)
    out = capsys.readouterr().out
    assert "Host: h" in out
    assert "Service: svc" in out
    assert "Count: 4" in out
    assert "Size: 56 bytes" in out
    assert "Tenant: t1" in out
    assert "HA Node: node1" in out


def test_display_configuration_skips_optional_lines_when_absent(capsys) -> None:
    """_display_configuration: absent tenant/node keys → those lines are omitted."""
    _configure_discovery()
    harness = _DiscoveryHarness()
    payload = {"host": "h", "service": "svc", "count": 1, "size": 56}
    harness._display_configuration(payload)
    out = capsys.readouterr().out
    assert "Tenant:" not in out
    assert "HA Node:" not in out


def test_debug_validate_service_no_op_when_debug_off(capsys) -> None:
    """_debug_validate_service: no-op when debug_mode is False."""
    _configure_discovery()
    harness = _DiscoveryHarness()
    harness.debug_mode = False
    harness._debug_validate_service("web-session")
    assert "[DEBUG]" not in capsys.readouterr().out


def test_debug_validate_service_prints_known_line_for_allowlist(capsys) -> None:
    """_debug_validate_service: debug ON + allowlisted service prints known-valid line."""
    _configure_discovery()
    harness = _DiscoveryHarness()
    harness.debug_mode = True
    harness._debug_validate_service("web-session")
    assert "known valid service: web-session" in capsys.readouterr().out


def test_debug_validate_service_prints_custom_line_for_others(capsys) -> None:
    """_debug_validate_service: debug ON + non-allowlisted service prints custom warning line."""
    _configure_discovery()
    harness = _DiscoveryHarness()
    harness.debug_mode = True
    harness._debug_validate_service("random")
    assert "custom service: random" in capsys.readouterr().out
