"""Unit tests for extracted service ping discovery and payload helpers."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from src.websocket.service_ping_discovery import (
    ServicePingDiscoveryMixin,
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
        self.debug_mode = False
        self.site_id = "site-1"
        self.device_id = "device-1"
        self.org_tenants = ["org-a"]
        self.site_tenants = ["site-a"]
        self.policy_tenants = ["policy-a"]
        self.template_tenants = ["template-a"]
        self.device_tenants = ["device-a"]
        self.org_services = [{"name": "svc-a", "type": "custom"}]
        self.org_service_names = ["svc-a"]
        self.device_services = ["svc-b"]
        self.debug_messages: list[str] = []

    def _debug_print(self, message: str) -> None:
        self.debug_messages.append(message)


class _TenantUtils:
    """Fake tenant utility used to control discovery outputs."""

    def __init__(self, *_args, **_kwargs) -> None:
        pass

    def organization_tenants(self) -> list[str]:
        return ["org-a", "org-b"]

    def site_tenants(self, _site_id: str) -> list[str]:
        return ["site-a", "site-b"]

    def service_policy_tenants(self, _site_id: str) -> list[str]:
        return ["policy-a", "policy-b"]

    def gateway_template_tenants(self, _site_id: str) -> list[str]:
        return ["template-a", "template-b"]


def _configure_discovery_with_defaults(*, safe_inputs: list[str] | None = None) -> MagicMock:
    """Configure extracted discovery dependencies for a test case."""
    safe_input_mock = MagicMock(side_effect=safe_inputs or [])
    configure_service_ping_discovery_dependencies(
        apisession_dependency=object(),
        mistapi_dependency=SimpleNamespace(
            api=SimpleNamespace(
                v1=SimpleNamespace(
                    sites=SimpleNamespace(
                        devices=SimpleNamespace(getSiteDevice=MagicMock()),
                        stats=SimpleNamespace(getSiteDeviceStats=MagicMock()),
                    )
                )
            )
        ),
        api_tenant_fetch_utils=_TenantUtils,
        config_utils=SimpleNamespace(get_cached_or_prompted_org_id=MagicMock(return_value="org-1")),
        api_fetch_utils=SimpleNamespace(organization_services=MagicMock(return_value=[{"name": "svc-a"}])),
        input_utils=SimpleNamespace(safe_input=safe_input_mock),
    )
    return safe_input_mock


def test_build_combined_tenants_deduplicates_and_adds_default() -> None:
    """Combined tenant list preserves source order and appends default when missing."""
    _configure_discovery_with_defaults()
    harness = _DiscoveryHarness()

    combined = harness._build_combined_tenants()

    assert combined == ["org-a", "site-a", "policy-a", "template-a", "device-a", "testing-tools"]


def test_build_combined_services_deduplicates_and_adds_default() -> None:
    """Combined service list preserves source order and appends default when missing."""
    _configure_discovery_with_defaults()
    harness = _DiscoveryHarness()

    combined = harness._build_combined_services()

    assert combined == ["svc-a", "svc-b", "web-session"]


def test_prompt_for_ping_parameters_uses_defaults_for_blank_values() -> None:
    """Blank prompts should fall back to documented service ping defaults."""
    _configure_discovery_with_defaults(safe_inputs=["", "", "", ""])
    harness = _DiscoveryHarness()

    params = harness._prompt_for_ping_parameters()

    assert params == {
        "host": harness.DEFAULT_HOST,
        "count": harness.DEFAULT_COUNT,
        "size": harness.DEFAULT_SIZE,
        "node": None,
    }


def test_build_payload_includes_optional_fields_when_present() -> None:
    """Payload should include tenant and node only when user selected them."""
    _configure_discovery_with_defaults()
    harness = _DiscoveryHarness()

    payload = harness._build_payload(
        "svc-a",
        "tenant-a",
        {"host": "1.1.1.1", "count": 7, "size": 512, "node": "node1"},
    )

    assert payload == {
        "host": "1.1.1.1",
        "service": "svc-a",
        "count": 7,
        "size": 512,
        "tenant": "tenant-a",
        "node": "node1",
    }


def test_fetch_org_site_policy_and_template_tenants_populates_sources() -> None:
    """Discovery fetch helpers should populate all tenant-source lists from the utility layer."""
    _configure_discovery_with_defaults()
    harness = _DiscoveryHarness()
    harness.org_tenants = []
    harness.site_tenants = []
    harness.policy_tenants = []
    harness.template_tenants = []

    harness._fetch_all_tenants()

    assert harness.org_tenants == ["org-a", "org-b"]
    assert harness.site_tenants == ["site-a", "site-b"]
    assert harness.policy_tenants == ["policy-a", "policy-b"]
    assert harness.template_tenants == ["template-a", "template-b"]
