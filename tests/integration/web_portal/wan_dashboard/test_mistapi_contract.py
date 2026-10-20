"""Check the installed Mist SDK contract used by the WAN dashboard."""

from __future__ import annotations

import inspect
import logging
from types import SimpleNamespace
from unittest.mock import MagicMock

import mistapi
import pytest

from src.interfaces.portals.wan_dashboard.services import RedisDashboardCache, WanDashboardService

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


class TestWorkerBulkContract:
    """Prove the refresh collector uses only complete, paginated bulk SDK reads."""

    def test_worker_reads_four_bulk_methods_and_counts_complete_pages(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The worker uses the four approved SDK methods and shared pagination."""
        first_page = SimpleNamespace(status_code=200, data=[], next="/next")  # Model one paginated site result.
        final_page = SimpleNamespace(status_code=200, data=[], next=None)  # Model its final page.
        page_reader = MagicMock(return_value=final_page)  # Keep pagination local and deterministic.
        monkeypatch.setattr(mistapi, "get_next", page_reader)  # Replace the SDK page request.
        methods = (  # Keep the approved collection boundary explicit.
            (mistapi.api.v1.orgs.sites, "listOrgSites", first_page),
            (mistapi.api.v1.orgs.stats, "listOrgDevicesStats", SimpleNamespace(status_code=200, data=[], next=None)),
            (mistapi.api.v1.orgs.stats, "searchOrgSwOrGwPorts", SimpleNamespace(status_code=200, data=[], next=None)),
            (mistapi.api.v1.orgs.inventory, "getOrgInventory", SimpleNamespace(status_code=200, data=[], next=None)),
        )
        readers = []  # Keep each mocked endpoint available for exact call assertions.
        for module, name, response in methods:
            reader = MagicMock(return_value=response)  # Return only the synthetic response.
            monkeypatch.setattr(module, name, reader)  # Prevent every Mist network call.
            readers.append(reader)  # Record the four approved methods in their call order.
        session = SimpleNamespace(_apitoken=[], _apitoken_index=-1, _session=None)  # Use a credential-free session.
        service = WanDashboardService(
            session, "org-test", RedisDashboardCache(None)
        )  # Disable Redis in this contract test.
        progress: list[tuple[str, int]] = []  # Record active phases and fully validated page counts.

        snapshot, failure = service.collect_worker_snapshot(
            lambda phase, count: progress.append((phase, count)), lambda: True
        )

        assert failure is None  # All four mocked bulk reads completed.
        assert snapshot is not None and snapshot["data"] == []  # Empty synthetic organization is complete.
        assert [reader.call_count for reader in readers] == [1, 1, 1, 1]  # Make one first-page call per bulk dataset.
        assert all(reader.call_args.kwargs["limit"] == 1000 for reader in readers)  # Keep the approved page size.
        assert page_reader.call_count == 1  # Use the SDK pagination helper for the second site page.
        assert progress[:3] == [("sites", 0), ("sites", 1), ("sites", 2)]  # Count only complete site pages.

    def test_rate_limit_and_http_errors_do_not_return_a_partial_snapshot(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A failed first bulk read returns no snapshot for 429, 4xx, or 5xx."""
        for status, expected in ((429, "rate_limited"), (400, "http_400"), (500, "http_500")):
            reader = MagicMock(return_value=SimpleNamespace(status_code=status, data=[], next=None))
            monkeypatch.setattr(mistapi.api.v1.orgs.sites, "listOrgSites", reader)  # Fail the first bulk read.
            session = SimpleNamespace(_apitoken=[], _apitoken_index=-1, _session=None)  # Use no credentials.
            service = WanDashboardService(session, "org-test", RedisDashboardCache(None))  # Keep the test offline.

            snapshot, failure = service.collect_worker_snapshot(lambda _phase, _count: None, lambda: True)

            assert snapshot is None  # A failed initial page cannot yield an empty success.
            assert failure == expected  # Preserve a safe internal failure code.
            assert reader.call_count == 1  # Do not retry the same token or endpoint.

    def test_failed_later_page_discards_earlier_site_rows(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A failed pagination request discards every earlier page."""
        first_page = SimpleNamespace(status_code=200, data=[{"id": "site-a"}], next="/next")
        failed_page = SimpleNamespace(status_code=500, data=[{"id": "site-b"}], next=None)
        monkeypatch.setattr(
            mistapi.api.v1.orgs.sites, "listOrgSites", MagicMock(return_value=first_page)
        )  # Return one valid page before the failure.
        next_page = MagicMock(return_value=failed_page)  # Fail the next SDK page with a server response.
        monkeypatch.setattr(mistapi, "get_next", next_page)  # Keep the pagination request offline.
        session = SimpleNamespace(_apitoken=[], _apitoken_index=-1, _session=None)  # Use no credentials.
        service = WanDashboardService(session, "org-test", RedisDashboardCache(None))  # Keep the test deterministic.

        snapshot, failure = service.collect_worker_snapshot(lambda _phase, _count: None, lambda: True)

        assert snapshot is None  # A failed second page invalidates the entire snapshot.
        assert failure == "http_500"  # Preserve the safe page failure status.
        assert next_page.call_count == 1  # Stop after the first failed later page.

    def test_repeated_page_link_discards_the_dataset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A repeated SDK page link cannot spin or publish duplicate rows."""
        repeated = SimpleNamespace(status_code=200, data=[{"id": "site-a"}], next="/next")
        monkeypatch.setattr(
            mistapi.api.v1.orgs.sites, "listOrgSites", MagicMock(return_value=repeated)
        )  # Return the same next link on the first page.
        next_page = MagicMock(return_value=repeated)  # Model an SDK response that repeats its link.
        monkeypatch.setattr(mistapi, "get_next", next_page)  # Keep the page request local.
        session = SimpleNamespace(_apitoken=[], _apitoken_index=-1, _session=None)  # Use no credentials.
        service = WanDashboardService(session, "org-test", RedisDashboardCache(None))  # Keep the test deterministic.

        snapshot, failure = service.collect_worker_snapshot(lambda _phase, _count: None, lambda: True)

        assert snapshot is None  # Repeated links make the whole collection incomplete.
        assert failure == "repeated_page"  # Preserve the safe pagination failure code.
        assert next_page.call_count == 1  # Stop before requesting the repeated URL again.

    def test_lost_lease_stops_before_the_first_sdk_request(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A worker without a lease cannot start the first bulk read."""
        reader = MagicMock()  # Observe whether the SDK boundary is reached.
        monkeypatch.setattr(mistapi.api.v1.orgs.sites, "listOrgSites", reader)  # Replace the first bulk method.
        session = SimpleNamespace(_apitoken=[], _apitoken_index=-1, _session=None)  # Use no credentials.
        service = WanDashboardService(session, "org-test", RedisDashboardCache(None))  # Keep the test offline.

        snapshot, failure = service.collect_worker_snapshot(lambda _phase, _count: None, lambda: False)

        assert snapshot is None  # A lease failure cannot produce a snapshot.
        assert failure == "worker_lease_lost"  # Report the exact safe cause.
        assert reader.call_count == 0  # Make no Mist SDK call without the lease.

    def test_failed_response_does_not_log_a_token_or_response_body(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Mist errors expose a safe status code and no credential or payload text."""
        secret = "synthetic-token-value"  # Use only a fictional credential marker.
        reader = MagicMock(
            return_value=SimpleNamespace(
                status_code=403,
                data={"error": secret},
                next=None,
            )
        )  # Model a rejected request whose body repeats the token.
        monkeypatch.setattr(mistapi.api.v1.orgs.sites, "listOrgSites", reader)  # Keep the call offline.
        session = SimpleNamespace(_apitoken=[secret], _apitoken_index=0, _session=None)
        service = WanDashboardService(session, "org-test", RedisDashboardCache(None))  # Use the real request boundary.
        caplog.set_level(logging.WARNING, logger="src.interfaces.portals.wan_dashboard.services")

        snapshot, failure = service.collect_worker_snapshot(lambda _phase, _count: None, lambda: True)

        assert snapshot is None  # A rejected response cannot produce a snapshot.
        assert failure == "http_403"  # Keep only the safe status code.
        assert secret not in caplog.text  # Keep credentials and raw response bodies out of logs.
