"""Unit tests for site analytics configurator extraction."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from src.analytics.site_analytics_configurator import SiteAnalyticsConfigurator, SiteAnalyticsConfiguratorDeps


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
