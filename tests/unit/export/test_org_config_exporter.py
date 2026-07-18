"""Unit tests for src.export.org_config_exporter.

Why:
    #878 tranche 19 -- un-omit org_config_exporter.py and drive it to 100% line
    and branch coverage. Every public delegator plus each MSP-export branch
    (auto-pick, prompt, cancel, out-of-range, empty payload, non-list payload,
    apisession-None, exception, >10 summary, etc.) has a matching test here so
    behavior regressions surface immediately.
"""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import mistapi
import pytest

from src.export.org_config_exporter import OrgConfigExporter


@pytest.fixture
def fake_mh(monkeypatch):
    """Install a fake ``MistHelper`` module into ``sys.modules``.

    Why:
        ``org_config_exporter`` lazy-imports MistHelper inside every helper to
        avoid circular loads. Injecting a MagicMock-populated stand-in lets us
        assert delegation targets without importing the real 3k-line module.
    """
    mh = ModuleType("MistHelper")
    mh.OrgExportUtils = MagicMock()
    mh.msp_privileges = []
    mh.InputUtils = MagicMock()
    mh.apisession = MagicMock()
    mh.DataExporter = MagicMock()
    monkeypatch.setitem(sys.modules, "MistHelper", mh)
    return mh


class TestPublicDelegators:
    """Cover the four thin delegator wrappers around ``OrgExportUtils.export_data``."""

    def test_psks(self, fake_mh):
        """``psks`` delegates to ``listOrgPsks`` with sort_key='name'."""
        OrgConfigExporter.psks()
        fake_mh.OrgExportUtils.export_data.assert_called_once_with(
            api_call=mistapi.api.v1.orgs.psks.listOrgPsks,
            data_type="psks",
            sort_key="name",
        )

    def test_webhooks(self, fake_mh):
        """``webhooks`` delegates to ``listOrgWebhooks``."""
        OrgConfigExporter.webhooks()
        fake_mh.OrgExportUtils.export_data.assert_called_once_with(
            api_call=mistapi.api.v1.orgs.webhooks.listOrgWebhooks,
            data_type="webhooks",
            sort_key="name",
        )

    def test_wlans(self, fake_mh):
        """``wlans`` delegates to ``listOrgWlans`` sorted by ssid."""
        OrgConfigExporter.wlans()
        fake_mh.OrgExportUtils.export_data.assert_called_once_with(
            api_call=mistapi.api.v1.orgs.wlans.listOrgWlans,
            data_type="wlans",
            sort_key="ssid",
        )

    def test_mx_edges(self, fake_mh):
        """``mx_edges`` delegates to ``listOrgMxEdges``."""
        OrgConfigExporter.mx_edges()
        fake_mh.OrgExportUtils.export_data.assert_called_once_with(
            api_call=mistapi.api.v1.orgs.mxedges.listOrgMxEdges,
            data_type="mx edges",
            sort_key="name",
        )


class TestMspEntryPoint:
    """Exercise the three ``msp()`` branches (no privileges / cancel / success)."""

    def test_no_msp_privileges(self, fake_mh):
        """When ``msp_privileges`` is empty, the guidance banner runs and we abort."""
        fake_mh.msp_privileges = []
        with patch.object(OrgConfigExporter, "_show_no_msp_access_guidance") as guide:
            OrgConfigExporter.msp()
        guide.assert_called_once()

    def test_msp_cancelled_selection(self, fake_mh):
        """When ``_select_msp_to_query`` returns None, no export is invoked."""
        fake_mh.msp_privileges = [{"msp_id": "a", "msp_name": "A", "role": "admin"}]
        with (
            patch.object(OrgConfigExporter, "_select_msp_to_query", return_value=None),
            patch.object(OrgConfigExporter, "_fetch_and_export_msp_orgs") as fetch,
        ):
            OrgConfigExporter.msp()
        fetch.assert_not_called()

    def test_msp_success_path(self, fake_mh):
        """A valid selection triggers ``_fetch_and_export_msp_orgs``."""
        selected = {"msp_id": "a", "msp_name": "A", "role": "admin"}
        fake_mh.msp_privileges = [selected]
        with (
            patch.object(OrgConfigExporter, "_select_msp_to_query", return_value=selected),
            patch.object(OrgConfigExporter, "_fetch_and_export_msp_orgs") as fetch,
        ):
            OrgConfigExporter.msp()
        fetch.assert_called_once_with(selected)


class TestShowNoMspAccessGuidance:
    """Snapshot the guidance banner so the login/token hints never silently vanish."""

    def test_prints_banner(self, capsys):
        """The banner should surface the login command and the token pitfall."""
        OrgConfigExporter._show_no_msp_access_guidance()
        out = capsys.readouterr().out
        assert "MSP ACCESS NOT AVAILABLE" in out
        assert "python MistHelper.py --login" in out
        assert "Organization-scoped API tokens CANNOT access MSP APIs." in out


class TestSelectMspToQuery:
    """Cover single/multi MSP prompt paths plus the two invalid-input branches."""

    def test_single_msp_auto_pick(self, fake_mh, capsys):
        """A single MSP is auto-selected without prompting."""
        selected = {"msp_id": "a", "msp_name": "Solo MSP", "role": "admin"}
        fake_mh.msp_privileges = [selected]
        result = OrgConfigExporter._select_msp_to_query()
        assert result is selected
        assert "Using MSP: Solo MSP" in capsys.readouterr().out

    def test_multi_msp_valid_choice(self, fake_mh):
        """User picks index 2 from a list of three MSPs."""
        fake_mh.msp_privileges = [
            {"msp_id": "1", "msp_name": "First", "role": "admin"},
            {"msp_id": "2", "msp_name": "Second", "role": "read"},
            {"msp_id": "3", "msp_name": "Third", "role": "admin"},
        ]
        fake_mh.InputUtils.safe_input.return_value = "2"
        result = OrgConfigExporter._select_msp_to_query()
        assert result == fake_mh.msp_privileges[1]

    def test_multi_msp_bad_input(self, fake_mh, capsys):
        """Non-numeric input triggers the ValueError branch and returns None."""
        fake_mh.msp_privileges = [
            {"msp_id": "1", "msp_name": "First", "role": "admin"},
            {"msp_id": "2", "msp_name": "Second", "role": "read"},
        ]
        fake_mh.InputUtils.safe_input.return_value = "not-a-number"
        result = OrgConfigExporter._select_msp_to_query()
        assert result is None
        assert "Invalid input" in capsys.readouterr().out

    def test_multi_msp_systemexit_input(self, fake_mh, capsys):
        """``safe_input`` raising SystemExit is treated as bad input, not fatal."""
        fake_mh.msp_privileges = [
            {"msp_id": "1", "msp_name": "First", "role": "admin"},
            {"msp_id": "2", "msp_name": "Second", "role": "read"},
        ]
        fake_mh.InputUtils.safe_input.side_effect = SystemExit()
        result = OrgConfigExporter._select_msp_to_query()
        assert result is None
        assert "Invalid input" in capsys.readouterr().out

    def test_multi_msp_out_of_range(self, fake_mh, capsys):
        """A numeric choice outside the MSP list returns None."""
        fake_mh.msp_privileges = [
            {"msp_id": "1", "msp_name": "First", "role": "admin"},
            {"msp_id": "2", "msp_name": "Second", "role": "read"},
        ]
        fake_mh.InputUtils.safe_input.return_value = "99"
        result = OrgConfigExporter._select_msp_to_query()
        assert result is None
        assert "Invalid selection" in capsys.readouterr().out


class TestFetchAndExportMspOrgs:
    """Cover apisession-None / exception / success paths for the MSP-orgs fetch."""

    def test_apisession_is_none(self, fake_mh, capsys):
        """When ``apisession`` is None, we log an error and abort before calling the API."""
        fake_mh.apisession = None
        selected = {"msp_id": "a", "msp_name": "A"}
        OrgConfigExporter._fetch_and_export_msp_orgs(selected)
        assert "No active API session" in capsys.readouterr().out

    def test_exception_during_fetch(self, fake_mh, capsys):
        """A raised exception is caught, logged, and printed for the operator."""
        selected = {"msp_id": "a", "msp_name": "A"}
        with patch("mistapi.api.v1.msps.orgs.listMspOrgs", side_effect=RuntimeError("boom")):
            OrgConfigExporter._fetch_and_export_msp_orgs(selected)
        out = capsys.readouterr().out
        assert "Error fetching MSP organizations" in out
        assert "boom" in out

    def test_success_calls_write(self, fake_mh):
        """A well-formed API response flows into ``_write_msp_orgs_csv``."""
        selected = {"msp_id": "a", "msp_name": "A"}
        response = MagicMock()
        response.data = [{"id": "org1", "name": "Org1"}]
        with (
            patch("mistapi.api.v1.msps.orgs.listMspOrgs", return_value=response),
            patch.object(OrgConfigExporter, "_write_msp_orgs_csv") as write,
        ):
            OrgConfigExporter._fetch_and_export_msp_orgs(selected)
        write.assert_called_once_with([{"id": "org1", "name": "Org1"}], "a", "A")

    def test_success_extract_none_skips_write(self, fake_mh):
        """When the payload extractor returns None, the write helper is skipped."""
        selected = {"msp_id": "a", "msp_name": "A"}
        response = MagicMock(spec=[])  # no ``data`` attribute -> extractor returns None
        with (
            patch("mistapi.api.v1.msps.orgs.listMspOrgs", return_value=response),
            patch.object(OrgConfigExporter, "_write_msp_orgs_csv") as write,
        ):
            OrgConfigExporter._fetch_and_export_msp_orgs(selected)
        write.assert_not_called()


class TestWriteMspOrgsCsv:
    """Cover empty-payload and populated-payload write flows."""

    def test_empty_orgs_data_writes_empty_csv(self, fake_mh, capsys):
        """Empty payload still writes an empty CSV so consumers get a fresh file."""
        OrgConfigExporter._write_msp_orgs_csv([], "msp-1", "MSP One")
        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with([], "MspOrganizations.csv")
        assert "No organizations found under this MSP" in capsys.readouterr().out

    def test_populated_orgs_data_writes_and_summarizes(self, fake_mh, capsys):
        """Populated payload is flattened + tagged + summarized."""
        orgs = [{"id": "01234567abcdef", "name": "Org1"}]
        OrgConfigExporter._write_msp_orgs_csv(orgs, "msp-1", "MSP One")
        fake_mh.DataExporter.write_with_format_selection.assert_called_once()
        args, _ = fake_mh.DataExporter.write_with_format_selection.call_args
        written_records, filename = args
        assert filename == "MspOrganizations.csv"
        assert written_records[0]["msp_id"] == "msp-1"
        assert written_records[0]["msp_name"] == "MSP One"
        out = capsys.readouterr().out
        assert "1 organizations exported to MspOrganizations.csv" in out
        assert "Organizations under MSP One" in out


class TestExtractMspOrgsPayload:
    """Cover the four possible shapes of the ``listMspOrgs`` response."""

    def test_none_response(self, capsys):
        """A None response returns None and prints the failure banner."""
        assert OrgConfigExporter._extract_msp_orgs_payload(None) is None
        assert "Failed to retrieve MSP organizations" in capsys.readouterr().out

    def test_response_without_data_attr(self, capsys):
        """Responses missing ``.data`` return None."""
        response = MagicMock(spec=[])
        assert OrgConfigExporter._extract_msp_orgs_payload(response) is None
        assert "Failed to retrieve MSP organizations" in capsys.readouterr().out

    def test_non_list_data_wrapped(self):
        """Dict payloads are wrapped in a single-element list."""
        response = MagicMock()
        response.data = {"id": "org1"}
        result = OrgConfigExporter._extract_msp_orgs_payload(response)
        assert result == [{"id": "org1"}]

    def test_empty_non_list_data_returns_empty_list(self):
        """Falsy non-list payloads (e.g., empty dict) return ``[]``."""
        response = MagicMock()
        response.data = {}
        assert OrgConfigExporter._extract_msp_orgs_payload(response) == []

    def test_list_data_passthrough(self):
        """A list payload is returned unchanged."""
        response = MagicMock()
        response.data = [{"id": "org1"}, {"id": "org2"}]
        assert OrgConfigExporter._extract_msp_orgs_payload(response) == [{"id": "org1"}, {"id": "org2"}]


class TestProcessMspOrgs:
    """Verify the flatten + escape + tagging pipeline attaches MSP identity fields."""

    def test_flatten_escape_and_tag(self):
        """Each processed record must carry the parent msp_id and msp_name."""
        orgs = [{"id": "org1", "name": "Org1"}, {"id": "org2", "name": "Org2"}]
        with (
            patch(
                "src.export.org_config_exporter.DataProcessingUtils.flatten_nested_fields",
                side_effect=lambda x: x,
            ) as flatten,
            patch(
                "src.export.org_config_exporter.DataProcessingUtils.escape_multiline",
                side_effect=lambda x: x,
            ) as escape,
        ):
            result = OrgConfigExporter._process_msp_orgs(orgs, "msp-1", "MSP One")
        flatten.assert_called_once_with(orgs)
        escape.assert_called_once()
        assert all(r["msp_id"] == "msp-1" for r in result)
        assert all(r["msp_name"] == "MSP One" for r in result)


class TestPrintMspOrgsSummary:
    """Cover the short-list branch and the ">10 → and N more" summary tail."""

    def test_prints_first_ten_only(self, capsys):
        """<=10 orgs prints them all with no 'and N more' tail."""
        orgs = [{"name": f"Org{i}", "id": f"abcdef{i:02d}00000"} for i in range(5)]
        OrgConfigExporter._print_msp_orgs_summary("MSP One", orgs)
        out = capsys.readouterr().out
        assert "Organizations under MSP One" in out
        assert "and" not in out.split("\n")[-2]

    def test_prints_first_ten_and_more(self, capsys):
        """More than 10 orgs prints only 10 rows plus the 'and N more' tail."""
        orgs = [{"name": f"Org{i}", "id": f"abcdef{i:02d}00000"} for i in range(15)]
        OrgConfigExporter._print_msp_orgs_summary("MSP Big", orgs)
        out = capsys.readouterr().out
        assert "and 5 more" in out

    def test_missing_fields_use_defaults(self, capsys):
        """Missing ``name``/``id`` gracefully fall back to Unknown/N/A."""
        OrgConfigExporter._print_msp_orgs_summary("MSP Empty", [{}])
        out = capsys.readouterr().out
        assert "Unknown" in out


def test_smoke_module_symbols():
    """Guardrail: ensure the public API surface stays intact."""
    from src.export import org_config_exporter as mod

    for attr in ("psks", "webhooks", "wlans", "mx_edges", "msp"):
        assert hasattr(mod.OrgConfigExporter, attr)
