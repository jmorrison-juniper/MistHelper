"""Unit tests for the WAN edge scorecard operation."""

from __future__ import annotations  # Keep annotations import-safe in tests.

from types import SimpleNamespace  # Build compact dependency doubles.
from typing import Any  # Type the fake shared fetcher kwargs.
from unittest.mock import MagicMock, patch  # Isolate the operation from network and disk.

from src.mist.intelligence.reports.wan_edge_scorecard.client import WanEdgeGatewayStatsClient
from src.mist.intelligence.reports.wan_edge_scorecard.scorecard import WanEdgeScorecard


class _ResponseBackedFetcher:
    """Minimal shared fetcher double for client HTTP status tests."""

    def __init__(self, title: str, api_call: Any, filename: str, sort_key: str | None, **kwargs: Any) -> None:
        """Store the API call and keyword arguments like APIDataFetcher."""
        self.title = title  # Keep the title to match the shared fetcher constructor.
        self.api_call = api_call  # Keep the callable so the test response drives the result.
        self.filename = filename  # Keep the filename to match the shared fetcher constructor.
        self.sort_key = sort_key  # Keep the sort key to match the shared fetcher constructor.
        self.kwargs = kwargs  # Keep query parameters so assertions can inspect them.
        self.org_id = ""  # Match the shared fetcher public attribute that the client sets.
        self.rawdata: list[dict[str, str]] = []  # Match the shared fetcher output attribute.

    def _fetch_api_data(self) -> bool:
        """Fetch once and return false for an HTTP error response."""
        response = self.api_call("session", self.org_id, **self.kwargs)  # Exercise the configured API callable.
        if response.status_code >= 400:  # Match shared fetcher behavior for HTTP 4xx and 5xx failures.
            self.rawdata = []  # Ensure the client sees no rows after a failed response.
            return False  # Signal that the shared fetch failed.
        self.rawdata = [{"id": "gw-ok"}]  # Provide one row for non-error tests if needed.
        return True  # Signal that the shared fetch succeeded.


def test_build_reports_outputs_one_row_per_gateway(gateway_stats_sample: list[dict[str, object]]) -> None:
    """Each gateway statistics row becomes one scorecard row."""
    gateway_rows, dhcp_rows, site_rows, org_score = WanEdgeScorecard.build_reports(gateway_stats_sample)  # Build rows.
    assert len(gateway_rows) == 3  # One gateway row exists for each fixture row.
    assert len(dhcp_rows) == 3  # Three DHCP pools exist across the fixtures.
    assert len(site_rows) == 2  # Two sites exist across the fixtures.
    assert org_score.gateway_count == 3  # The organization summary uses the gateway rows.


def test_missing_optional_gateway_fields_do_not_fail() -> None:
    """Missing optional fields produce empty values and no exception."""
    gateway_rows, dhcp_rows, _site_rows, _org_score = WanEdgeScorecard.build_reports([{"id": "gw-empty"}])  # Build row.
    row = gateway_rows[0]  # Inspect the only gateway row.
    assert row.gateway_id == "gw-empty"  # Required identity is preserved.
    assert row.dhcp_pool_count == 0  # Missing dhcpd_stat yields zero pools.
    assert row.worst_pool_utilization_percent is None  # No DHCP pools produce no worst percent.
    assert dhcp_rows == []  # Missing DHCP data writes no pool rows.


def test_live_gateway_shape_uses_site_lookup_and_device_name() -> None:
    """The live gateway stats shape can fill the gateway and site names."""
    gateway_rows, _dhcp_rows, site_rows, org_score = WanEdgeScorecard.build_reports(  # Build live-like rows.
        [
            {
                "id": "gw-live",
                "site_id": "site-live",
                "device_name": "Morrison WAN",
                "model": "SRX",
                "version": "22.4R1",
                "config_status": None,
                "uptime": 172800,
            }
        ],
        {"site-live": "Morrison House Site"},
    )

    assert gateway_rows[0].gateway_name == "Morrison WAN"  # WHY: device_name is the live display name fallback.
    assert gateway_rows[0].site == "Morrison House Site"  # WHY: live stats carry site_id but no site_name.
    assert site_rows[0].config_unknown_count == 1  # WHY: absent config_status must not count as a failure.
    assert site_rows[0].config_success_percent == 0.0  # WHY: no known config rows leaves no success score.
    assert org_score.config_unknown_count == 1  # WHY: the organization summary uses the same unknown handling.


def test_absent_dhcpd_stat_sets_gateway_pool_count_zero(gateway_stats_sample: list[dict[str, object]]) -> None:
    """A gateway without dhcpd_stat stays in the gateway scorecard."""
    gateway_rows, _dhcp_rows, _site_rows, _org_score = WanEdgeScorecard.build_reports(
        gateway_stats_sample
    )  # Build rows.
    row = next(item for item in gateway_rows if item.gateway_id == "gw-2")  # Select the fixture without dhcpd_stat.
    assert row.dhcp_pool_count == 0  # Missing DHCP statistics count as zero pools.


def test_dhcp_pool_rows_include_percent_and_threshold(gateway_stats_sample: list[dict[str, object]]) -> None:
    """DHCP pool rows include leased, total, percent, and threshold status."""
    _gateway_rows, dhcp_rows, _site_rows, _org_score = WanEdgeScorecard.build_reports(
        gateway_stats_sample
    )  # Build rows.
    voice = next(row for row in dhcp_rows if row.pool_name == "voice")  # Select the high-use pool.
    assert voice.leased == 85  # Leased count comes from num_leased.
    assert voice.total == 100  # Total count comes from num_ips.
    assert voice.percent == 85.0  # Percent is calculated from leased and total.
    assert voice.over_threshold is True  # The default threshold is 80 percent.


def test_vpn_peer_up_false_counts_as_down(gateway_stats_sample: list[dict[str, object]]) -> None:
    """VPN peers with up false increase the down count."""
    gateway_rows, _dhcp_rows, _site_rows, _org_score = WanEdgeScorecard.build_reports(
        gateway_stats_sample
    )  # Build rows.
    row = next(item for item in gateway_rows if item.gateway_id == "gw-1")  # Select the mixed VPN fixture.
    assert row.vpn_peers_up == 1  # One peer reports up true.
    assert row.vpn_peers_down == 1  # One peer reports up false.


def test_bgp_peer_established_and_not_established_counts(gateway_stats_sample: list[dict[str, object]]) -> None:
    """BGP states are separated into established and not established counts."""
    gateway_rows, _dhcp_rows, _site_rows, _org_score = WanEdgeScorecard.build_reports(
        gateway_stats_sample
    )  # Build rows.
    row = next(item for item in gateway_rows if item.gateway_id == "gw-1")  # Select the mixed BGP fixture.
    assert row.bgp_peers_established == 1  # One peer reports established.
    assert row.bgp_peers_not_established == 1  # One peer reports active.


def test_site_scorecard_percentages(gateway_stats_sample: list[dict[str, object]]) -> None:
    """Site percentages are calculated from the gateway rows."""
    _gateway_rows, _dhcp_rows, site_rows, _org_score = WanEdgeScorecard.build_reports(
        gateway_stats_sample
    )  # Build rows.
    alpha = next(row for row in site_rows if row.site_id == "site-a")  # Select the two-gateway site.
    assert alpha.gateway_count == 2  # Alpha has two gateways.
    assert alpha.config_success_percent == 100.0  # Both Alpha gateways have successful config states.
    assert alpha.config_unknown_count == 0  # All Alpha gateways have known config status.
    assert alpha.version_compliance_percent == 100.0  # Both Alpha gateways match the predominant version.
    assert alpha.wan_edge_uptime_percent == 50.0  # One Alpha gateway has at least one day of uptime.


def test_cluster_state_problem_reduces_potential_anomalies() -> None:
    """Cluster state problems reduce the Potential Anomalies score."""
    gateway_rows, _dhcp_rows, site_rows, org_score = WanEdgeScorecard.build_reports(
        [
            {
                "id": "gw-cluster",
                "site_id": "site-cluster",
                "site_name": "Cluster Site",
                "name": "Cluster-WAN-1",
                "version": "22.4R1",
                "config_status": "success",
                "uptime": 172800,
                "cluster_peer_state": "peer_down",
            }
        ]
    )  # Build one site with a clear cluster problem word.
    assert gateway_rows[0].cluster_peer_state == "peer_down"  # Confirm the score input is present.
    assert site_rows[0].potential_anomalies_percent == 0.0  # The site score shows the cluster anomaly.
    assert org_score.potential_anomalies_percent == 0.0  # The organization score uses the same rule.


def test_organization_summary_percentages(gateway_stats_sample: list[dict[str, object]]) -> None:
    """Organization percentages are calculated from all gateway rows."""
    _gateway_rows, _dhcp_rows, _site_rows, org_score = WanEdgeScorecard.build_reports(
        gateway_stats_sample
    )  # Build rows.
    assert org_score.gateway_count == 3  # The organization summary sees all gateways.
    assert org_score.site_count == 2  # The organization summary sees both sites.
    assert org_score.config_success_percent == 66.67  # Two of three gateways have successful config states.
    assert org_score.version_compliance_percent == 66.67  # Two of three gateways match the predominant version.


def test_fetch_client_uses_list_org_devices_stats_gateway_type() -> None:
    """The fetch seam uses listOrgDevicesStats with type gateway through APIDataFetcher."""
    fetcher = MagicMock(name="APIDataFetcherInstance")  # Capture the shared fetcher behavior.
    fetcher._fetch_api_data.return_value = True  # Simulate a successful shared fetch.
    fetcher.rawdata = [{"id": "gw-1"}]  # Provide rows from the shared fetcher.
    fetcher_factory = MagicMock(return_value=fetcher)  # Capture the shared fetcher construction.
    fake_mistapi = MagicMock(name="mistapi")  # Provide a Mist SDK double.
    fake_host = SimpleNamespace(mistapi=fake_mistapi, APIDataFetcher=fetcher_factory)  # Provide resolver dependencies.
    with patch("src.mist.intelligence.reports.wan_edge_scorecard.client.SourceDependencyResolver", fake_host):
        rows = WanEdgeGatewayStatsClient.fetch_gateway_stats("org-1")  # Fetch rows through the client seam.
    assert rows == [{"id": "gw-1"}]  # Pagination result is returned to the caller.
    assert fetcher.org_id == "org-1"  # Confirm the fetch-only seam does not prompt for the org id.
    fetcher._fetch_api_data.assert_called_once_with()  # Confirm shared pagination and retry behavior was reused.
    fetcher_factory.assert_called_once_with(
        title="WAN Edge Gateway Stats:",
        api_call=fake_mistapi.api.v1.orgs.stats.listOrgDevicesStats,
        filename="WanEdgeScorecardSource.csv",
        sort_key="site_id",
        type="gateway",
        status="all",
        fields="*",
        limit=1000,
    )  # Confirm the required endpoint and gateway filter.


def test_fetch_client_returns_empty_rows_for_http_4xx_response() -> None:
    """The client returns no rows when the shared fetch receives an HTTP 4xx response."""
    api_call = MagicMock(return_value=SimpleNamespace(status_code=404))  # Return a concrete client error response.
    fake_mistapi = SimpleNamespace(
        api=SimpleNamespace(v1=SimpleNamespace(orgs=SimpleNamespace(stats=SimpleNamespace())))
    )
    fake_mistapi.api.v1.orgs.stats.listOrgDevicesStats = api_call  # Attach the endpoint used by the client.
    fake_host = SimpleNamespace(
        apisession="session",
        mistapi=fake_mistapi,
        APIDataFetcher=lambda **kwargs: _ResponseBackedFetcher(**kwargs),
    )  # Provide the resolver dependencies used by the client.
    with patch("src.mist.intelligence.reports.wan_edge_scorecard.client.SourceDependencyResolver", fake_host):
        rows = WanEdgeGatewayStatsClient.fetch_gateway_stats("org-1")  # Fetch through the client seam.
    assert rows == []  # The client must not return stale rows after an HTTP 4xx failure.
    api_call.assert_called_once_with(
        "session", "org-1", type="gateway", status="all", fields="*", limit=1000
    )  # The error test proves the exact gateway query was sent.


def test_fetch_client_returns_empty_rows_for_http_5xx_response() -> None:
    """The client returns no rows when the shared fetch receives an HTTP 5xx response."""
    api_call = MagicMock(return_value=SimpleNamespace(status_code=503))  # Return a concrete server error response.
    fake_mistapi = SimpleNamespace(
        api=SimpleNamespace(v1=SimpleNamespace(orgs=SimpleNamespace(stats=SimpleNamespace())))
    )
    fake_mistapi.api.v1.orgs.stats.listOrgDevicesStats = api_call  # Attach the endpoint used by the client.
    fake_host = SimpleNamespace(
        apisession="session",
        mistapi=fake_mistapi,
        APIDataFetcher=lambda **kwargs: _ResponseBackedFetcher(**kwargs),
    )  # Provide the resolver dependencies used by the client.
    with patch("src.mist.intelligence.reports.wan_edge_scorecard.client.SourceDependencyResolver", fake_host):
        rows = WanEdgeGatewayStatsClient.fetch_gateway_stats("org-1")  # Fetch through the client seam.
    assert rows == []  # The client must not return stale rows after an HTTP 5xx failure.
    api_call.assert_called_once_with(
        "session", "org-1", type="gateway", status="all", fields="*", limit=1000
    )  # The error test proves the exact gateway query was sent.


def test_run_exports_three_reports_and_prints_summary(gateway_stats_sample: list[dict[str, object]], capsys) -> None:
    """The operation exports all three required report files."""
    exporter = MagicMock(name="DataExporter")  # Capture export calls without touching disk.
    config = SimpleNamespace(get_cached_or_prompted_org_id=MagicMock(return_value="org-1"))  # Provide org id.
    fake_host = SimpleNamespace(DataExporter=exporter, ConfigUtils=config)  # Provide operation dependencies.
    with patch("src.mist.intelligence.reports.wan_edge_scorecard.scorecard.SourceDependencyResolver", fake_host):
        with patch(
            "src.mist.intelligence.reports.wan_edge_scorecard.scorecard.WanEdgeGatewayStatsClient.fetch_gateway_stats",
            return_value=gateway_stats_sample,
        ):
            with patch(
                "src.mist.intelligence.reports.wan_edge_scorecard.scorecard.SiteNameLookup.fetch",
                return_value={"site-a": "Alpha", "site-b": "Beta"},
            ):
                WanEdgeScorecard.run()  # Run the operation with isolated dependencies.
    filenames = [call.args[1] for call in exporter.write_with_format_selection.call_args_list]  # Read targets.
    assert filenames == ["WanEdgeScorecard.csv", "WanEdgeDhcpPools.csv", "WanEdgeScorecardBySite.csv"]  # Files.
    assert "WAN Edge Scorecard Summary" in capsys.readouterr().out  # Summary is printed for the operator.
