"""Unit tests for site analytics configurator extraction."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from requests.exceptions import ConnectionError, HTTPError, Timeout

from src.mist.intelligence.analytics import (
    SiteAnalyticsConfigurator as RootSiteAnalyticsConfigurator,
)
from src.mist.intelligence.analytics import (
    SiteAnalyticsConfiguratorDeps as RootSiteAnalyticsConfiguratorDeps,
)
from src.mist.intelligence.analytics.site.site_analytics_configurator import (
    SiteAnalyticsConfigurator,
    SiteAnalyticsConfiguratorDeps,
)


def _build_mistapi_stub() -> SimpleNamespace:
    """Build a minimal mistapi stub object for configurator tests."""
    get_site_setting = MagicMock()
    update_site_settings = MagicMock()
    setting = SimpleNamespace(getSiteSetting=get_site_setting, updateSiteSettings=update_site_settings)
    sites = SimpleNamespace(setting=setting)
    v1 = SimpleNamespace(sites=sites)
    api = SimpleNamespace(v1=v1)
    return SimpleNamespace(api=api)


def _identity_tqdm(items, **_kwargs):
    """Simple tqdm replacement for deterministic unit tests."""
    return items


def _build_deps() -> SiteAnalyticsConfiguratorDeps:
    """Build default dependency object with overridable mocks."""
    return SiteAnalyticsConfiguratorDeps(
        apisession=MagicMock(),
        mistapi=_build_mistapi_stub(),
        get_org_id_fn=MagicMock(return_value="org-123"),
        check_stop_fn=MagicMock(return_value=False),
        safe_input_fn=MagicMock(return_value="CONFIGURE"),
        all_sites_fn=MagicMock(return_value=[]),
        save_data_fn=MagicMock(),
        tqdm_fn=_identity_tqdm,
    )


def test_analytics_root_exports_configurator_classes() -> None:
    """Issue #3992 keeps the canonical configurator classes at the analytics root."""
    assert RootSiteAnalyticsConfigurator is SiteAnalyticsConfigurator
    assert RootSiteAnalyticsConfiguratorDeps is SiteAnalyticsConfiguratorDeps


def test_compare_settings_detects_missing_and_mismatch() -> None:
    """Compare helper should report missing and mismatched values."""
    current = {"enabled": False}
    standard = {"enabled": True, "track_asset": True}

    deviations = SiteAnalyticsConfigurator._compare_settings(current, standard, "rtsa")

    assert len(deviations) == 2
    assert deviations[0]["section"] == "rtsa"


def test_compare_engagement_detects_variance() -> None:
    """Engagement compare should detect non-standard ranges and names."""
    current = {
        "dwell_tags": {"passerby": "1-10"},
        "dwell_tag_names": {"passerby": "Custom"},
        "hours": {"mon": "09:00-17:00"},
    }

    deviations = SiteAnalyticsConfigurator._compare_engagement(current)

    assert len(deviations) >= 3


def test_execute_exits_when_org_missing(capsys) -> None:
    """Execute should stop immediately when no org id is available."""
    deps = _build_deps()
    deps.get_org_id_fn.return_value = None

    SiteAnalyticsConfigurator.execute(deps)

    assert "No organization selected" in capsys.readouterr().out


def test_execute_reports_no_deviations(capsys) -> None:
    """Execute should report compliance when no site deviations are found."""
    deps = _build_deps()
    deps.all_sites_fn.return_value = [{"id": "site-1", "name": "Site One"}]
    deps.mistapi.api.v1.sites.setting.getSiteSetting.return_value = SimpleNamespace(
        status_code=200,
        data={
            "rtsa": SiteAnalyticsConfigurator.STANDARD_RTSA.copy(),
            "rogue": SiteAnalyticsConfigurator.STANDARD_ROGUE.copy(),
            "engagement": {
                "dwell_tags": SiteAnalyticsConfigurator.STANDARD_ENGAGEMENT["dwell_tags"].copy(),
                "dwell_tag_names": SiteAnalyticsConfigurator.STANDARD_ENGAGEMENT["dwell_tag_names"].copy(),
                "hours": SiteAnalyticsConfigurator.STANDARD_ENGAGEMENT["hours"].copy(),
            },
            "analytic": SiteAnalyticsConfigurator.STANDARD_ANALYTIC.copy(),
            "occupancy": SiteAnalyticsConfigurator.STANDARD_OCCUPANCY.copy(),
            "wifi": SiteAnalyticsConfigurator.STANDARD_WIFI.copy(),
        },
    )

    SiteAnalyticsConfigurator.execute(deps)

    assert "All sites are configured with standard analytics settings" in capsys.readouterr().out


def test_execute_cancels_when_confirmation_mismatch(capsys) -> None:
    """Execute should cancel without applying when confirmation text is incorrect."""
    deps = _build_deps()
    deps.safe_input_fn.return_value = "NOPE"
    deps.all_sites_fn.return_value = [{"id": "site-1", "name": "Site One"}]
    deps.mistapi.api.v1.sites.setting.getSiteSetting.return_value = SimpleNamespace(
        status_code=200,
        data={"rtsa": {"enabled": False}},
    )

    SiteAnalyticsConfigurator.execute(deps)

    assert "Operation cancelled" in capsys.readouterr().out
    deps.mistapi.api.v1.sites.setting.updateSiteSettings.assert_not_called()


def test_apply_site_config_success() -> None:
    """Site update helper should return SUCCESS when API update succeeds."""
    deps = _build_deps()
    deps.mistapi.api.v1.sites.setting.getSiteSetting.return_value = SimpleNamespace(status_code=200, data={})
    deps.mistapi.api.v1.sites.setting.updateSiteSettings.return_value = SimpleNamespace(status_code=200)

    site = {
        "site_id": "site-1",
        "site_name": "Site One",
        "rtsa_deviation": True,
        "rogue_deviation": False,
        "engagement_deviation": False,
        "analytic_deviation": False,
        "occupancy_deviation": False,
        "wifi_deviation": False,
    }

    result = SiteAnalyticsConfigurator._apply_site_config(site, deps)

    assert result["status"] == "SUCCESS"
    assert "rtsa" in result["sections_updated"]


@pytest.mark.parametrize("failure_type", [ConnectionError, Timeout, HTTPError])
def test_scan_transport_failure_logs_and_skips_site(
    failure_type: type[Exception], caplog: pytest.LogCaptureFixture
) -> None:
    """Transport failures preserve the per-site scan recovery path."""
    deps = _build_deps()
    failure = failure_type("scan unavailable")
    deps.mistapi.api.v1.sites.setting.getSiteSetting.side_effect = failure
    assert SiteAnalyticsConfigurator._scan_single_site({"id": "site-1", "name": "Site One"}, deps) is None
    assert "Error scanning Site One: scan unavailable" in caplog.text
    record = next(record for record in caplog.records if record.exc_info)
    assert record.exc_info[1] is failure
    deps.mistapi.api.v1.sites.setting.updateSiteSettings.assert_not_called()


@pytest.mark.parametrize("failure_type", [NameError, TypeError, AttributeError, RuntimeError])
def test_scan_programming_error_propagates(failure_type: type[Exception]) -> None:
    """A defective scan call must not classify a site as absent or compliant."""
    deps = _build_deps()
    deps.mistapi.api.v1.sites.setting.getSiteSetting.side_effect = failure_type("scan defect")
    with pytest.raises(failure_type, match="scan defect"):
        SiteAnalyticsConfigurator._scan_single_site({"id": "site-1", "name": "Site One"}, deps)
    deps.mistapi.api.v1.sites.setting.updateSiteSettings.assert_not_called()


@pytest.mark.parametrize("stage", ["fetch", "update"])
@pytest.mark.parametrize("failure_type", [ConnectionError, Timeout, HTTPError])
def test_apply_transport_failure_records_error(
    stage: str, failure_type: type[Exception], caplog: pytest.LogCaptureFixture
) -> None:
    """Expected request failures retain the ERROR result and exception detail."""
    deps = _build_deps()
    settings = deps.mistapi.api.v1.sites.setting
    settings.getSiteSetting.return_value = SimpleNamespace(status_code=200, data={})
    failure = failure_type("request unavailable")
    target = settings.getSiteSetting if stage == "fetch" else settings.updateSiteSettings
    target.side_effect = failure
    site = {
        "site_id": "site-1",
        "site_name": "Site One",
        **{
            f"{section}_deviation": False
            for section in ("rtsa", "rogue", "engagement", "analytic", "occupancy", "wifi")
        },
    }
    result = SiteAnalyticsConfigurator._apply_site_config(site, deps)
    assert result["status"] == "ERROR"
    assert result["error"] == "request unavailable"
    assert "Error updating Site One: request unavailable" in caplog.text
    record = next(record for record in caplog.records if record.exc_info)
    assert record.exc_info[1] is failure
    if stage == "fetch":
        settings.updateSiteSettings.assert_not_called()


@pytest.mark.parametrize("failure_type", [NameError, TypeError, AttributeError, RuntimeError])
def test_apply_programming_error_propagates(failure_type: type[Exception]) -> None:
    """Programming errors from the SDK call must reach the workflow caller."""
    deps = _build_deps()
    deps.mistapi.api.v1.sites.setting.getSiteSetting.side_effect = failure_type("apply defect")
    with pytest.raises(failure_type, match="apply defect"):
        SiteAnalyticsConfigurator._apply_site_config({"site_id": "site-1", "site_name": "Site One"}, deps)
    deps.mistapi.api.v1.sites.setting.updateSiteSettings.assert_not_called()


def test_apply_missing_deviation_propagates_without_update() -> None:
    """An incomplete internal deviation record must not become an ordinary API failure."""
    deps = _build_deps()
    deps.mistapi.api.v1.sites.setting.getSiteSetting.return_value = SimpleNamespace(status_code=200, data={})
    with pytest.raises(KeyError, match="rtsa_deviation"):
        SiteAnalyticsConfigurator._apply_site_config({"site_id": "site-1", "site_name": "Site One"}, deps)
    deps.mistapi.api.v1.sites.setting.updateSiteSettings.assert_not_called()
