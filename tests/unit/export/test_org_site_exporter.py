"""Unit tests for ``src.export.org_site_exporter.OrgSiteExporter``.

Why: Exercises every branch of the 5 static methods on OrgSiteExporter so that
un-omitting the module in ``[tool.coverage.run].omit`` keeps overall coverage
above the 90% gate. The module resolves its cross-class collaborators lazily
via ``importlib.import_module("MistHelper")``; tests inject a fake ``MistHelper``
module via ``sys.modules`` monkeypatching to control those collaborators.
"""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def fake_mh(monkeypatch):
    """Install a fake MistHelper module that the exporter resolves lazily.

    Why: OrgSiteExporter uses ``importlib.import_module("MistHelper")`` inside
    each method to fetch APIDataFetcher, ConfigUtils, APICoreFetchUtils,
    DataExporter, ProgressContext, PROGRESS_EMITTER, OUTPUT_FORMAT, and
    apisession. Replacing the module lets tests observe and control these
    interactions without importing the real monolith.
    """
    mh = ModuleType("MistHelper")
    mh.APIDataFetcher = MagicMock()
    mh.ConfigUtils = MagicMock()
    mh.APICoreFetchUtils = MagicMock()
    mh.DataExporter = MagicMock()
    mh.ProgressContext = MagicMock()
    mh.PROGRESS_EMITTER = None
    mh.OUTPUT_FORMAT = "csv"
    mh.apisession = MagicMock()
    monkeypatch.setitem(sys.modules, "MistHelper", mh)
    return mh


class TestSites:
    """Cover OrgSiteExporter.sites branches."""

    def test_default_csv_no_emitter(self, fake_mh):
        """CSV backend + no emitter uses APIDataFetcher with SiteList filename."""
        from src.export.org_site_exporter import OrgSiteExporter

        OrgSiteExporter.sites()

        fake_mh.APIDataFetcher.assert_called_once()
        kwargs = fake_mh.APIDataFetcher.call_args.kwargs
        assert kwargs["filename"] == "SiteList"
        assert kwargs["sort_key"] == "name"
        assert kwargs["limit"] == 1000
        fake_mh.APIDataFetcher.return_value.execute.assert_called_once()

    def test_sqlite_format(self, fake_mh):
        """OUTPUT_FORMAT=sqlite is accepted (log-only branch)."""
        from src.export.org_site_exporter import OrgSiteExporter

        fake_mh.OUTPUT_FORMAT = "sqlite"
        OrgSiteExporter.sites()

        fake_mh.APIDataFetcher.return_value.execute.assert_called_once()

    def test_with_emitter(self, fake_mh):
        """PROGRESS_EMITTER receives start + complete when present."""
        from src.export.org_site_exporter import OrgSiteExporter

        emitter = MagicMock()
        fake_mh.PROGRESS_EMITTER = emitter
        ctx_sentinel = MagicMock()
        fake_mh.ProgressContext = MagicMock(return_value=ctx_sentinel)

        OrgSiteExporter.sites()

        emitter.emit_progress_start.assert_called_once_with("11", "sites", 1)
        emitter.emit_progress_complete.assert_called_once()
        args = emitter.emit_progress_complete.call_args.args
        assert args[0] is ctx_sentinel
        assert args[1] == 1
        assert args[2] is False


class TestSitesListApi:
    """Cover OrgSiteExporter.sites_list_api branches."""

    def test_cache_hit_short_circuits(self, fake_mh):
        """Existing cache file skips API + write."""
        from src.export.org_site_exporter import OrgSiteExporter

        with patch("src.export.org_site_exporter.os.path.exists", return_value=True):
            OrgSiteExporter.sites_list_api()

        fake_mh.APICoreFetchUtils.all_sites_with_limit.assert_not_called()
        fake_mh.DataExporter.write_with_format_selection.assert_not_called()

    def test_empty_sites_returns_early(self, fake_mh):
        """Empty site list logs + returns without writing."""
        from src.export.org_site_exporter import OrgSiteExporter

        fake_mh.APICoreFetchUtils.all_sites_with_limit.return_value = []
        with patch("src.export.org_site_exporter.os.path.exists", return_value=False):
            OrgSiteExporter.sites_list_api()

        fake_mh.DataExporter.write_with_format_selection.assert_not_called()

    def test_happy_path_writes_output(self, fake_mh):
        """Non-empty list flows through flatten/escape/write."""
        from src.export.org_site_exporter import OrgSiteExporter

        raw = [{"id": "s1"}, {"id": "s2"}]
        fake_mh.APICoreFetchUtils.all_sites_with_limit.return_value = raw
        with (
            patch("src.export.org_site_exporter.os.path.exists", return_value=False),
            patch("src.export.org_site_exporter.DataProcessingUtils") as dpu,
        ):
            dpu.flatten_nested_fields.return_value = raw
            dpu.escape_multiline.return_value = raw
            OrgSiteExporter.sites_list_api()

        # flatten is called twice (see line 85 comment "Flatten again post-merge")
        assert dpu.flatten_nested_fields.call_count == 2
        dpu.escape_multiline.assert_called_once()
        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with(raw, "SiteList_ListAPI.csv")


class TestSitesWithLocation:
    """Cover OrgSiteExporter.sites_with_location."""

    def test_writes_flattened_sites(self, fake_mh):
        """Fetches sites, flattens, escapes, writes to SitesWithLocations.csv."""
        from src.export.org_site_exporter import OrgSiteExporter

        raw = [{"id": "s1", "name": "site1"}]
        fake_mh.APICoreFetchUtils.all_sites_with_limit.return_value = raw
        with patch("src.export.org_site_exporter.DataProcessingUtils") as dpu:
            dpu.flatten_nested_fields.return_value = raw
            dpu.escape_multiline.return_value = raw
            OrgSiteExporter.sites_with_location()

        fake_mh.ConfigUtils.get_cached_or_prompted_org_id.assert_called_once()
        dpu.flatten_nested_fields.assert_called_once_with(raw)
        dpu.escape_multiline.assert_called_once_with(raw)
        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with(raw, "SitesWithLocations.csv")


class TestCurrentGuests:
    """Cover OrgSiteExporter.current_guests."""

    def test_writes_current_guests_csv(self, fake_mh):
        """Calls guest search API, flattens, writes to OrgCurrentGuests.csv."""
        from src.export.org_site_exporter import OrgSiteExporter

        guests = [{"mac": "aa:bb:cc"}]
        fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org1"
        with (
            patch(
                "src.export.org_site_exporter.mistapi.api.v1.orgs.guests.searchOrgGuestAuthorization",
                return_value=MagicMock(),
            ) as search,
            patch(
                "src.export.org_site_exporter.mistapi.get_all",
                return_value=guests,
            ) as get_all,
            patch("src.export.org_site_exporter.DataProcessingUtils") as dpu,
        ):
            dpu.flatten_nested_fields.return_value = guests
            dpu.escape_multiline.return_value = guests
            OrgSiteExporter.current_guests()

        search.assert_called_once_with(fake_mh.apisession, "org1", limit=1000)
        get_all.assert_called_once()
        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with(guests, "OrgCurrentGuests.csv")


class TestHistoricalGuests:
    """Cover OrgSiteExporter.historical_guests."""

    def test_seven_day_window(self, fake_mh):
        """Historical guests use a 7-day window ending now."""
        from src.export.org_site_exporter import OrgSiteExporter

        guests = [{"mac": "dd:ee:ff"}]
        fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org2"
        with (
            patch("src.export.org_site_exporter.time.time", return_value=1_000_000),
            patch(
                "src.export.org_site_exporter.mistapi.api.v1.orgs.guests.searchOrgGuestAuthorization",
                return_value=MagicMock(),
            ) as search,
            patch(
                "src.export.org_site_exporter.mistapi.get_all",
                return_value=guests,
            ),
            patch("src.export.org_site_exporter.DataProcessingUtils") as dpu,
        ):
            dpu.flatten_nested_fields.return_value = guests
            dpu.escape_multiline.return_value = guests
            OrgSiteExporter.historical_guests()

        # end=1_000_000, start = end - 7*24*3600 = 395_200
        search.assert_called_once_with(fake_mh.apisession, "org2", limit=1000, start=395_200, end=1_000_000)
        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with(guests, "OrgHistoricalGuests.csv")
