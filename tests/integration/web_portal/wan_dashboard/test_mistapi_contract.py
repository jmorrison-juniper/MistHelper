"""Check the installed Mist SDK contract used by the WAN dashboard."""

from __future__ import annotations

import inspect

import mistapi

SDK_METHODS = (
    mistapi.api.v1.self.self.getSelf,
    mistapi.api.v1.orgs.orgs.getOrg,
    mistapi.api.v1.orgs.sites.listOrgSites,
    mistapi.api.v1.orgs.inventory.getOrgInventory,
    mistapi.api.v1.orgs.deviceprofiles.getOrgDeviceProfile,
    mistapi.api.v1.orgs.gatewaytemplates.getOrgGatewayTemplate,
    mistapi.api.v1.orgs.stats.listOrgDevicesStats,
    mistapi.api.v1.orgs.stats.searchOrgSwOrGwPorts,
    mistapi.api.v1.sites.devices.getSiteDevice,
    mistapi.api.v1.sites.devices.searchSiteDevices,
    mistapi.api.v1.sites.stats.getSiteDeviceStats,
    mistapi.api.v1.orgs.stats.searchOrgPeerPathStats,
    mistapi.api.v1.sites.insights.getSiteInsightMetricsForGateway,
    mistapi.api.v1.sites.insights.getSiteInsightMetricsForDevice,
    mistapi.api.v1.sites.sle.getSiteSleSummaryTrend,
    mistapi.api.v1.sites.sle.listSiteSleImpactedInterfaces,
    mistapi.api.v1.sites.sle.getSiteSleThreshold,
)


class TestMistSdkSignatures:
    """Prove that dashboard SDK calls use explicit supported arguments."""

    def test_all_documented_methods_accept_the_shared_session_first(self) -> None:
        """Every documented SDK method receives the injected APISession explicitly."""
        assert len(SDK_METHODS) == 17  # Count the distinct documented SDK methods.
        for method in SDK_METHODS:  # Check each installed SDK method.
            parameters = tuple(inspect.signature(method).parameters.values())  # Read its public signature.
            assert parameters[0].name == "mist_session"  # Reuse the shared portal session.
            assert parameters[0].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD  # Avoid hidden variadic calls.

    def test_sdk_version_remains_within_the_supported_minor_release(self) -> None:
        """The installed dependency exposes the expected stable API version."""
        assert mistapi.__version__.startswith("0.64.")  # Keep compatibility with the pinned project dependency.
