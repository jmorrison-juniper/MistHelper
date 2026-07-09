"""Unit tests for extracted SiteExportUtils module (Pattern 1 constructor injection)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from src.export.site_export_utils import SiteExportUtils


class _ApiCallWithLimit:
    """Simple callable emulating a mistapi endpoint with limit support."""

    __name__ = "listMockSiteData"

    def __call__(self, apisession, site_id, limit=1000, **kwargs):  # type: ignore[no-untyped-def]
        return {"site_id": site_id, "limit": limit, "kwargs": kwargs}


def _build_exporter(select_site_return: str | None = "site-1") -> tuple[SiteExportUtils, MagicMock]:
    """Construct a SiteExportUtils instance with mocked dependencies via Pattern 1 constructor injection."""
    exporter_mock = MagicMock()
    get_all_mock = MagicMock(
        side_effect=[
            [{"id": "site-1", "name": "My Site"}],
            [{"name": "b"}, {"name": "a"}],
        ]
    )

    mistapi_dependency = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(
                    sites=SimpleNamespace(
                        listOrgSites=MagicMock(return_value={"status": "ok"}),
                    )
                )
            )
        ),
        get_all=get_all_mock,
    )

    exporter = SiteExportUtils(
        apisession=object(),
        PromptUtils=SimpleNamespace(select_site=MagicMock(return_value=select_site_return)),
        ConfigUtils=SimpleNamespace(
            get_cached_or_prompted_org_id=MagicMock(return_value="org-1"),
            check_stop_signal=MagicMock(return_value=False),
        ),
        DataProcessingUtils=SimpleNamespace(
            flatten_nested_fields=MagicMock(side_effect=lambda rows: rows),
            escape_multiline=MagicMock(side_effect=lambda rows: rows),
            get_unique_keys=MagicMock(return_value=["name"]),
        ),
        DataExporter=SimpleNamespace(write_with_format_selection=exporter_mock),
        TimeUtils=SimpleNamespace(
            get_dynamic_lookback_hours=MagicMock(return_value=24), log_dynamic_lookback=MagicMock()
        ),
        EnhancedSSHRunner=SimpleNamespace(
            sanitize_filename=MagicMock(side_effect=lambda value: value.replace(" ", "_"))
        ),
        InsightMetricsUtils=SimpleNamespace(
            export_const_insight_metrics=MagicMock(), get_by_scope=MagicMock(return_value=[])
        ),
        PacketCaptureManager=SimpleNamespace(
            validate_mac_address=MagicMock(return_value=True),
            normalize_mac_address=MagicMock(return_value="aa:bb:cc:dd:ee:ff"),
        ),
        APICoreFetchUtils=SimpleNamespace(all_sites_with_limit=MagicMock(return_value=[])),
        check_fn=MagicMock(return_value=False),
        PrettyTable=SimpleNamespace,
        tqdm=MagicMock(side_effect=lambda rows, **kwargs: rows),
        mistapi=mistapi_dependency,
    )

    return exporter, exporter_mock


def test_export_data_returns_early_when_no_site_selected() -> None:
    """Generic export helper should exit cleanly when no site is selected."""
    exporter, exporter_mock = _build_exporter(select_site_return=None)

    exporter._export_data(api_call=_ApiCallWithLimit(), data_type="test data")

    exporter_mock.assert_not_called()


def test_export_data_sorts_and_writes_output() -> None:
    """Generic export helper should sort rows and write expected filename."""
    exporter, exporter_mock = _build_exporter(select_site_return="site-1")

    exporter._export_data(api_call=_ApiCallWithLimit(), data_type="test data", sort_key="name")

    exporter_mock.assert_called_once()
    saved_rows, saved_filename = exporter_mock.call_args[0]
    assert saved_filename == "SiteTestdata_My_Site.csv"
    assert [row["name"] for row in saved_rows] == ["a", "b"]
