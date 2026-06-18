"""Unit tests for offender #8 security export service."""

from unittest.mock import MagicMock, patch

from src.refactors.serial_cc.security_events import SecurityEventsService


class DummyDeps:
    """Lightweight dependency bundle for service tests."""

    def __init__(self):
        self.ConfigUtils = MagicMock()
        self.PROGRESS_EMITTER = None
        self.TimeUtils = MagicMock()
        self.CacheUtils = MagicMock()
        self.OrgSiteExporter = MagicMock()
        self.OrgSiteExporter.sites = MagicMock()
        self.DataProcessingUtils = MagicMock()
        self.DataExporter = MagicMock()
        self.FilePathUtils = MagicMock()
        self.mistapi = MagicMock()
        self.apisession = MagicMock()
        self.tqdm = lambda items, **_kwargs: items
        self.csv_freshness_minutes = 60


def _make_dependency_bundle():
    """Create the service dependency bundle used by the resolver patch."""
    return DummyDeps()


@patch("src.refactors.serial_cc.security_events._resolve_runtime_dependencies")
def test_security_events_fast_mode_returns_on_fresh_cache(mock_resolve_runtime_dependencies, capsys):
    """Fast mode exits when all cache files are fresh."""
    deps = _make_dependency_bundle()
    mock_resolve_runtime_dependencies.return_value = deps
    deps.FilePathUtils.get_csv_path.return_value = "C:/tmp/fresh.csv"
    deps.mistapi = MagicMock()
    with (
        patch("src.refactors.serial_cc.security_events.os.path.exists", return_value=True),
        patch("src.refactors.serial_cc.security_events.os.path.getmtime", return_value=0),
        patch("src.refactors.serial_cc.security_events.time.time", return_value=0),
    ):
        SecurityEventsService.execute(fast=True)

    captured = capsys.readouterr()
    assert "cached security data" in captured.out


@patch("src.refactors.serial_cc.security_events._resolve_runtime_dependencies")
def test_security_events_exports_security_policies(mock_resolve_runtime_dependencies):
    """Service exports policy data when API returns records."""
    deps = _make_dependency_bundle()
    mock_resolve_runtime_dependencies.return_value = deps
    deps.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"
    deps.TimeUtils.get_dynamic_lookback_hours.return_value = 168
    deps.mistapi.get_all.return_value = [{"id": "one"}]
    deps.mistapi.api.v1.orgs.secpolicies.listOrgSecPolicies.return_value = MagicMock()
    deps.mistapi.api.v1.orgs.secintelprofiles.listOrgSecIntelProfiles.return_value = MagicMock()
    deps.FilePathUtils.get_csv_path.return_value = "C:/tmp/SiteList.csv"
    deps.DataProcessingUtils.flatten_nested_fields.side_effect = lambda rows: rows
    deps.DataProcessingUtils.escape_multiline.side_effect = lambda rows: rows

    with (
        patch("src.refactors.serial_cc.security_events.open", MagicMock()),
        patch("src.refactors.serial_cc.security_events.csv.DictReader", return_value=[]),
    ):
        SecurityEventsService.execute(fast=False)

    assert deps.DataExporter.save_data_to_output.call_count >= 2


@patch("src.refactors.serial_cc.security_events._resolve_runtime_dependencies")
def test_security_events_exports_rogue_data(mock_resolve_runtime_dependencies):
    """Service combines rogue APs and rogue clients into one export."""
    deps = _make_dependency_bundle()
    mock_resolve_runtime_dependencies.return_value = deps
    deps.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"
    deps.TimeUtils.get_dynamic_lookback_hours.return_value = 168
    deps.mistapi.get_all.side_effect = [[], [], [], []]
    deps.mistapi.api.v1.orgs.secpolicies.listOrgSecPolicies.return_value = MagicMock()
    deps.mistapi.api.v1.orgs.secintelprofiles.listOrgSecIntelProfiles.return_value = MagicMock()
    deps.FilePathUtils.get_csv_path.side_effect = ["C:/tmp/policies.csv", "C:/tmp/secintel.csv", "C:/tmp/SiteList.csv"]
    deps.DataProcessingUtils.flatten_nested_fields.side_effect = lambda rows: rows
    deps.DataProcessingUtils.escape_multiline.side_effect = lambda rows: rows
    deps.CacheUtils.check_and_generate_csv.return_value = None

    site_csv = MagicMock()
    site_csv.__enter__.return_value = MagicMock()
    site_csv.__exit__.return_value = False
    with (
        patch("src.refactors.serial_cc.security_events.open", return_value=site_csv),
        patch("src.refactors.serial_cc.security_events.csv.DictReader", return_value=[]),
    ):
        SecurityEventsService.execute(fast=False)

    assert deps.DataExporter.save_data_to_output.call_count >= 3
