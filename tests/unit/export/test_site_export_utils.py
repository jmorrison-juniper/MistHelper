"""Unit tests for extracted SiteExportUtils module."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from src.export.site_export_utils import SiteExportUtils, configure_site_export_utils_dependencies


class _ApiCallWithLimit:
    """Simple callable emulating a mistapi endpoint with limit support."""

    __name__ = "listMockSiteData"

    def __call__(self, apisession, site_id, limit=1000, **kwargs):  # type: ignore[no-untyped-def]
        return {"site_id": site_id, "limit": limit, "kwargs": kwargs}


def _configure_dependencies(select_site_return: str | None = "site-1") -> tuple[SimpleNamespace, MagicMock]:
    """Configure extracted module dependencies for unit tests."""
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

    configure_site_export_utils_dependencies(
        apisession_dependency=object(),
        prompt_utils=SimpleNamespace(select_site=MagicMock(return_value=select_site_return)),
        config_utils=SimpleNamespace(
            get_cached_or_prompted_org_id=MagicMock(return_value="org-1"),
            check_stop_signal=MagicMock(return_value=False),
        ),
        data_processing_utils=SimpleNamespace(
            flatten_nested_fields=MagicMock(side_effect=lambda rows: rows),
            escape_multiline=MagicMock(side_effect=lambda rows: rows),
            get_unique_keys=MagicMock(return_value=["name"]),
        ),
        data_exporter=SimpleNamespace(write_with_format_selection=exporter_mock),
        time_utils=SimpleNamespace(
            get_dynamic_lookback_hours=MagicMock(return_value=24), log_dynamic_lookback=MagicMock()
        ),
        enhanced_ssh_runner=SimpleNamespace(
            sanitize_filename=MagicMock(side_effect=lambda value: value.replace(" ", "_"))
        ),
        insight_metrics_utils=SimpleNamespace(export_legacy=MagicMock(), get_by_scope=MagicMock(return_value=[])),
        packet_capture_manager=SimpleNamespace(
            validate_mac_address=MagicMock(return_value=True),
            normalize_mac_address=MagicMock(return_value="aa:bb:cc:dd:ee:ff"),
        ),
        api_core_fetch_utils=SimpleNamespace(all_sites_with_limit=MagicMock(return_value=[])),
        is_debug_mode_fn=MagicMock(return_value=False),
        pretty_table_class=SimpleNamespace,
        tqdm_module=MagicMock(side_effect=lambda rows, **kwargs: rows),
        mistapi_dependency=mistapi_dependency,
    )

    return mistapi_dependency, exporter_mock


def test_export_data_returns_early_when_no_site_selected() -> None:
    """Generic export helper should exit cleanly when no site is selected."""
    _, exporter_mock = _configure_dependencies(select_site_return=None)

    SiteExportUtils._export_data(api_call=_ApiCallWithLimit(), data_type="test data")

    exporter_mock.assert_not_called()


def test_export_data_sorts_and_writes_output() -> None:
    """Generic export helper should sort rows and write expected filename."""
    _, exporter_mock = _configure_dependencies(select_site_return="site-1")

    SiteExportUtils._export_data(api_call=_ApiCallWithLimit(), data_type="test data", sort_key="name")

    exporter_mock.assert_called_once()
    saved_rows, saved_filename = exporter_mock.call_args[0]
    assert saved_filename == "SiteTestdata_My_Site.csv"
    assert [row["name"] for row in saved_rows] == ["a", "b"]
