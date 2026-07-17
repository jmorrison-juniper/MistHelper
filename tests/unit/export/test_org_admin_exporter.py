"""Unit tests for OrgAdminExporter (issue #878 tranche 3 -- un-omit).

Covers the seven static methods on ``src.export.org_admin_exporter``:
``api_tokens``, ``admins``, ``sso``, ``_fetch_license_payload`` (wrapper +
raw GET fallback + missing-session branch), ``_fetch_license_records``
(list-normalisation branch), ``licenses`` (empty/success/error paths) and
``usage``.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.export.org_admin_exporter import OrgAdminExporter


def _make_mh(**extra):
    """Assemble a stub MistHelper module with the attributes each method touches."""
    apidata_fetcher = MagicMock(name="APIDataFetcher")
    apidata_fetcher.return_value.execute = MagicMock()
    defaults = {
        "APIDataFetcher": apidata_fetcher,
        "OrgExportUtils": MagicMock(name="OrgExportUtils"),
        "ConfigUtils": MagicMock(name="ConfigUtils"),
        "DataExporter": MagicMock(name="DataExporter"),
        "apisession": MagicMock(name="apisession"),
    }
    defaults.update(extra)
    return SimpleNamespace(**defaults)


# ---------- api_tokens ----------


def test_api_tokens_delegates_to_apidata_fetcher_execute() -> None:
    """api_tokens must instantiate APIDataFetcher with the token endpoint and run it."""
    fake_mh = _make_mh()
    with patch("src.export.org_admin_exporter.importlib.import_module", return_value=fake_mh):
        OrgAdminExporter.api_tokens()
    fake_mh.APIDataFetcher.assert_called_once()
    kwargs = fake_mh.APIDataFetcher.call_args.kwargs
    assert kwargs["filename"] == "OrgApiTokens.csv"
    assert kwargs["sort_key"] == "name"
    fake_mh.APIDataFetcher.return_value.execute.assert_called_once_with()


# ---------- admins ----------


def test_admins_delegates_to_apidata_fetcher_execute() -> None:
    """admins must instantiate APIDataFetcher with the admins endpoint and run it."""
    fake_mh = _make_mh()
    with patch("src.export.org_admin_exporter.importlib.import_module", return_value=fake_mh):
        OrgAdminExporter.admins()
    kwargs = fake_mh.APIDataFetcher.call_args.kwargs
    assert kwargs["filename"] == "OrgAdmins.csv"
    fake_mh.APIDataFetcher.return_value.execute.assert_called_once_with()


# ---------- sso ----------


def test_sso_delegates_to_orgexportutils_export_data() -> None:
    """sso must delegate to OrgExportUtils.export_data with data_type='sso'."""
    fake_mh = _make_mh()
    with patch("src.export.org_admin_exporter.importlib.import_module", return_value=fake_mh):
        OrgAdminExporter.sso()
    fake_mh.OrgExportUtils.export_data.assert_called_once()
    assert fake_mh.OrgExportUtils.export_data.call_args.kwargs["data_type"] == "sso"


# ---------- _fetch_license_payload ----------


def test_fetch_license_payload_uses_wrapper_when_present() -> None:
    """When listOrgLicenses exists on mistapi the wrapper path paginates via get_all."""
    fake_mh = _make_mh()
    fake_response = MagicMock(name="wrapperResponse")
    fake_licenses_ns = MagicMock(name="licensesNS")
    fake_licenses_ns.listOrgLicenses.return_value = fake_response
    fake_mistapi = MagicMock(name="mistapi")
    fake_mistapi.api.v1.orgs.licenses = fake_licenses_ns
    fake_mistapi.get_all.return_value = [{"id": "L1"}]

    with (
        patch("src.export.org_admin_exporter.mistapi", fake_mistapi),
        patch("src.export.org_admin_exporter.importlib.import_module", return_value=fake_mh),
    ):
        result = OrgAdminExporter._fetch_license_payload("org-uuid")

    fake_licenses_ns.listOrgLicenses.assert_called_once_with(fake_mh.apisession, "org-uuid", limit=1000)
    fake_mistapi.get_all.assert_called_once_with(response=fake_response, mist_session=fake_mh.apisession)
    assert result == [{"id": "L1"}]


def test_fetch_license_payload_raw_get_fallback_when_wrapper_absent() -> None:
    """When listOrgLicenses is missing the helper issues a raw GET and unwraps .data."""
    fake_mh = _make_mh()
    fake_mh.apisession.mist_get.return_value = SimpleNamespace(data=[{"id": "L2"}])
    fake_mistapi = MagicMock(name="mistapi")
    fake_mistapi.api.v1.orgs.licenses = SimpleNamespace()  # No listOrgLicenses attribute.

    with (
        patch("src.export.org_admin_exporter.mistapi", fake_mistapi),
        patch("src.export.org_admin_exporter.importlib.import_module", return_value=fake_mh),
    ):
        result = OrgAdminExporter._fetch_license_payload("org-uuid")

    fake_mh.apisession.mist_get.assert_called_once_with("/api/v1/orgs/org-uuid/licenses")
    assert result == [{"id": "L2"}]


def test_fetch_license_payload_raw_get_defaults_none_data_to_empty_list() -> None:
    """Raw GET fallback with .data=None must return an empty list, not None."""
    fake_mh = _make_mh()
    fake_mh.apisession.mist_get.return_value = SimpleNamespace(data=None)
    fake_mistapi = MagicMock(name="mistapi")
    fake_mistapi.api.v1.orgs.licenses = SimpleNamespace()

    with (
        patch("src.export.org_admin_exporter.mistapi", fake_mistapi),
        patch("src.export.org_admin_exporter.importlib.import_module", return_value=fake_mh),
    ):
        result = OrgAdminExporter._fetch_license_payload("org-uuid")

    assert result == []


def test_fetch_license_payload_raises_when_session_not_initialized() -> None:
    """Raw GET path requires an initialised session; None must raise ValueError."""
    fake_mh = _make_mh(apisession=None)
    fake_mistapi = MagicMock(name="mistapi")
    fake_mistapi.api.v1.orgs.licenses = SimpleNamespace()

    with (
        patch("src.export.org_admin_exporter.mistapi", fake_mistapi),
        patch("src.export.org_admin_exporter.importlib.import_module", return_value=fake_mh),
    ):
        with pytest.raises(ValueError, match="API session not initialized"):
            OrgAdminExporter._fetch_license_payload("org-uuid")


# ---------- _fetch_license_records ----------


def test_fetch_license_records_passes_list_through_untouched() -> None:
    """A list payload is returned as-is."""
    with patch.object(OrgAdminExporter, "_fetch_license_payload", return_value=[{"id": 1}, {"id": 2}]):
        assert OrgAdminExporter._fetch_license_records("org-uuid") == [{"id": 1}, {"id": 2}]


def test_fetch_license_records_wraps_non_list_payload_into_list() -> None:
    """A dict payload is normalised into a single-element list."""
    with patch.object(OrgAdminExporter, "_fetch_license_payload", return_value={"id": "solo"}):
        assert OrgAdminExporter._fetch_license_records("org-uuid") == [{"id": "solo"}]


# ---------- licenses ----------


def test_licenses_writes_empty_csv_when_no_records() -> None:
    """No records -> empty CSV write, no DataProcessing pipeline."""
    fake_mh = _make_mh()
    fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-uuid"
    with (
        patch("src.export.org_admin_exporter.importlib.import_module", return_value=fake_mh),
        patch.object(OrgAdminExporter, "_fetch_license_records", return_value=[]),
    ):
        OrgAdminExporter.licenses()
    fake_mh.DataExporter.write_with_format_selection.assert_called_once_with(
        [], "OrgLicenses.csv", api_function_name="listOrgLicenses"
    )


def test_licenses_flattens_escapes_and_writes_on_success() -> None:
    """Non-empty records flow through the DataProcessingUtils pipeline before writing."""
    fake_mh = _make_mh()
    fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-uuid"
    with (
        patch("src.export.org_admin_exporter.DataProcessingUtils") as fake_dpu,
        patch("src.export.org_admin_exporter.importlib.import_module", return_value=fake_mh),
        patch.object(OrgAdminExporter, "_fetch_license_records", return_value=[{"id": "L1"}]),
    ):
        fake_dpu.flatten_nested_fields.return_value = [{"flat": True}]
        fake_dpu.escape_multiline.return_value = [{"safe": True}]
        OrgAdminExporter.licenses()
    fake_dpu.flatten_nested_fields.assert_called_once_with([{"id": "L1"}])
    fake_dpu.escape_multiline.assert_called_once_with([{"flat": True}])
    fake_mh.DataExporter.write_with_format_selection.assert_called_once_with(
        [{"safe": True}], "OrgLicenses.csv", api_function_name="listOrgLicenses"
    )


def test_licenses_best_effort_empty_write_on_fetch_failure_then_reraises() -> None:
    """A fetch error triggers a best-effort empty write and re-raises."""
    fake_mh = _make_mh()
    fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-uuid"
    boom = RuntimeError("fetch failed")
    with (
        patch("src.export.org_admin_exporter.importlib.import_module", return_value=fake_mh),
        patch.object(OrgAdminExporter, "_fetch_license_records", side_effect=boom),
    ):
        with pytest.raises(RuntimeError, match="fetch failed"):
            OrgAdminExporter.licenses()
    fake_mh.DataExporter.write_with_format_selection.assert_called_once_with([], "OrgLicenses.csv")


def test_licenses_swallows_secondary_write_failure() -> None:
    """If the best-effort cleanup write also fails, the primary error still propagates."""
    fake_mh = _make_mh()
    fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-uuid"
    fake_mh.DataExporter.write_with_format_selection.side_effect = OSError("disk full")
    with (
        patch("src.export.org_admin_exporter.importlib.import_module", return_value=fake_mh),
        patch.object(OrgAdminExporter, "_fetch_license_records", side_effect=RuntimeError("primary")),
    ):
        with pytest.raises(RuntimeError, match="primary"):
            OrgAdminExporter.licenses()


# ---------- usage ----------


def test_usage_delegates_to_apidata_fetcher_execute(capsys: pytest.CaptureFixture[str]) -> None:
    """usage must run APIDataFetcher for the by-site usage endpoint and print completion."""
    fake_mh = _make_mh()
    with patch("src.export.org_admin_exporter.importlib.import_module", return_value=fake_mh):
        OrgAdminExporter.usage()
    kwargs = fake_mh.APIDataFetcher.call_args.kwargs
    assert kwargs["filename"] == "OrgUsage"
    fake_mh.APIDataFetcher.return_value.execute.assert_called_once_with()
    assert "License usage data exported to OrgUsage" in capsys.readouterr().out
