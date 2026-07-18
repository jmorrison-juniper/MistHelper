"""Unit tests for OrgTicketManager (100% line + branch coverage).

Why:
    Verifies the full 6-operation ticket lifecycle (list, create, add-comment,
    update, view, export-details) plus all 15 private helpers. Every
    ``importlib.import_module("MistHelper")`` call is patched with a
    ``SimpleNamespace`` fake so no real MistHelper live-globals load.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.org.org_ticket_manager import OrgTicketManager


def _make_mh(**extra):
    """Build a fake ``mh`` namespace with the collaborators OrgTicketManager uses.

    Why:
        The class reaches every collaborator (``InputUtils``, ``ConfigUtils``,
        ``mistapi``, ``apisession``, ``APIDataFetcher``, ``DataExporter``) via a
        lazy ``importlib.import_module("MistHelper")`` call inside each method
        that needs them. A single ``SimpleNamespace`` matches all attribute
        lookups without importing the real module.

    Args:
        **extra: overrides for individual attributes.

    Returns:
        SimpleNamespace populated with MagicMock collaborators.
    """
    defaults = {
        "APIDataFetcher": MagicMock(name="APIDataFetcher"),
        "DataExporter": MagicMock(name="DataExporter"),
        "ConfigUtils": MagicMock(name="ConfigUtils"),
        "InputUtils": MagicMock(name="InputUtils"),
        "mistapi": MagicMock(name="mistapi"),
        "apisession": MagicMock(name="apisession"),
    }
    defaults.update(extra)
    return SimpleNamespace(**defaults)


# ---------- list_tickets ----------


def test_list_tickets_success_delegates_to_api_data_fetcher(caplog):
    """list_tickets calls APIDataFetcher(...).execute() with the right args."""
    fake_mh = _make_mh()
    fetcher_instance = fake_mh.APIDataFetcher.return_value
    caplog.set_level("INFO")
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        OrgTicketManager.list_tickets()
    fake_mh.APIDataFetcher.assert_called_once()
    fetcher_instance.execute.assert_called_once_with()
    kwargs = fake_mh.APIDataFetcher.call_args.kwargs
    assert kwargs["title"] == "Organization Support Tickets:"
    assert kwargs["filename"] == "OrgTickets.csv"
    assert kwargs["sort_key"] == "created_at"
    assert kwargs["duration"] == "365d"


def test_list_tickets_reraises_on_error(caplog):
    """list_tickets logs then re-raises upstream errors."""
    fake_mh = _make_mh()
    fake_mh.APIDataFetcher.return_value.execute.side_effect = RuntimeError("boom")
    caplog.set_level("ERROR")
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        with pytest.raises(RuntimeError, match="boom"):
            OrgTicketManager.list_tickets()
    assert "Failed to export org tickets" in caplog.text


# ---------- create_ticket ----------


def test_create_ticket_blank_subject_cancels(capsys):
    """create_ticket aborts when subject is blank."""
    fake_mh = _make_mh()
    fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"
    fake_mh.InputUtils.safe_input.return_value = ""
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        OrgTicketManager.create_ticket()
    assert "subject is required" in capsys.readouterr().out


def test_create_ticket_full_flow_with_comment():
    """create_ticket assembles body with subject/type/comment and submits."""
    fake_mh = _make_mh()
    fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"
    # sequence: subject, type-index, comment
    fake_mh.InputUtils.safe_input.side_effect = ["My subject", "2", "hello"]
    api_response = SimpleNamespace(data={"id": "t-1", "status": "open"})
    fake_mh.mistapi.api.v1.orgs.tickets.createOrgTicket.return_value = api_response
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        OrgTicketManager.create_ticket()
    body = fake_mh.mistapi.api.v1.orgs.tickets.createOrgTicket.call_args.args[2]
    assert body == {"subject": "My subject", "type": "problem", "comment": "hello"}


def test_create_ticket_flow_without_comment():
    """create_ticket omits comment when user gives empty string."""
    fake_mh = _make_mh()
    fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"
    fake_mh.InputUtils.safe_input.side_effect = ["Subj", "1", ""]
    fake_mh.mistapi.api.v1.orgs.tickets.createOrgTicket.return_value = SimpleNamespace(
        data={"id": "t-1", "status": "open"}
    )
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        OrgTicketManager.create_ticket()
    body = fake_mh.mistapi.api.v1.orgs.tickets.createOrgTicket.call_args.args[2]
    assert "comment" not in body


# ---------- add_comment ----------


def test_add_comment_cancels_when_no_ticket_selected(capsys):
    """add_comment prints cancellation when no ticket is chosen."""
    fake_mh = _make_mh()
    fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"
    fake_mh.mistapi.api.v1.orgs.tickets.listOrgTickets.return_value = SimpleNamespace(data=[])
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        OrgTicketManager.add_comment()
    assert "no ticket selected" in capsys.readouterr().out


def test_add_comment_cancels_when_no_comment_or_file(capsys):
    """add_comment aborts if user gives neither comment nor file path."""
    fake_mh = _make_mh()
    fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"
    fake_mh.mistapi.api.v1.orgs.tickets.listOrgTickets.return_value = SimpleNamespace(
        data=[{"id": "t-1", "subject": "s", "status": "open", "type": "question"}]
    )
    # selection "1" then blank comment, blank file
    fake_mh.InputUtils.safe_input.side_effect = ["1", "", ""]
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        OrgTicketManager.add_comment()
    assert "provide a comment or file" in capsys.readouterr().out


def test_add_comment_success_text_only(tmp_path):
    """add_comment submits text-only when file_path is blank."""
    fake_mh = _make_mh()
    fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"
    fake_mh.mistapi.api.v1.orgs.tickets.listOrgTickets.return_value = SimpleNamespace(
        data=[{"id": "t-1", "subject": "s", "status": "open", "type": "question"}]
    )
    fake_mh.InputUtils.safe_input.side_effect = ["1", "text comment", ""]
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        OrgTicketManager.add_comment()
    fake_mh.mistapi.api.v1.orgs.tickets.addOrgTicketComment.assert_called_once()


# ---------- update_ticket ----------


def test_update_ticket_cancels_when_no_ticket_selected(capsys):
    """update_ticket prints cancellation on no selection."""
    fake_mh = _make_mh()
    fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"
    fake_mh.mistapi.api.v1.orgs.tickets.listOrgTickets.return_value = SimpleNamespace(data=[])
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        OrgTicketManager.update_ticket()
    assert "no ticket selected" in capsys.readouterr().out


def test_update_ticket_cancels_when_no_fields_changed(capsys):
    """update_ticket aborts if user provides no updates."""
    fake_mh = _make_mh()
    fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"
    fake_mh.mistapi.api.v1.orgs.tickets.listOrgTickets.return_value = SimpleNamespace(
        data=[{"id": "t-1", "subject": "s", "status": "open", "type": "question"}]
    )
    # selection=1, then subject blank, status blank, type blank
    fake_mh.InputUtils.safe_input.side_effect = ["1", "", "", ""]
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        OrgTicketManager.update_ticket()
    assert "No changes specified" in capsys.readouterr().out


def test_update_ticket_success_updates_selected_fields(capsys):
    """update_ticket calls updateOrgTicket with only user-provided fields."""
    fake_mh = _make_mh()
    fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"
    fake_mh.mistapi.api.v1.orgs.tickets.listOrgTickets.return_value = SimpleNamespace(
        data=[{"id": "t-1", "subject": "s", "status": "open", "type": "question"}]
    )
    fake_mh.InputUtils.safe_input.side_effect = ["1", "new subject", "closed", ""]
    fake_mh.mistapi.api.v1.orgs.tickets.updateOrgTicket.return_value = SimpleNamespace(data={"ok": True})
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        OrgTicketManager.update_ticket()
    body = fake_mh.mistapi.api.v1.orgs.tickets.updateOrgTicket.call_args.args[3]
    assert body == {"subject": "new subject", "status": "closed"}


# ---------- _prompt_subject / _prompt_ticket_type / _prompt_ticket_id ----------


def test_prompt_subject_returns_input_value():
    """_prompt_subject returns whatever InputUtils.safe_input yields."""
    fake_mh = _make_mh()
    fake_mh.InputUtils.safe_input.return_value = "my subj"
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        assert OrgTicketManager._prompt_subject() == "my subj"


def test_prompt_ticket_type_valid_choice():
    """_prompt_ticket_type maps '3' -> 'incident'."""
    fake_mh = _make_mh()
    fake_mh.InputUtils.safe_input.return_value = "3"
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        assert OrgTicketManager._prompt_ticket_type() == "incident"


def test_prompt_ticket_type_non_numeric_defaults_to_question():
    """_prompt_ticket_type falls back to 'question' on non-numeric input."""
    fake_mh = _make_mh()
    fake_mh.InputUtils.safe_input.return_value = "abc"
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        assert OrgTicketManager._prompt_ticket_type() == "question"


def test_prompt_ticket_type_out_of_range_defaults_to_question():
    """_prompt_ticket_type falls back to default when index is out of range."""
    fake_mh = _make_mh()
    fake_mh.InputUtils.safe_input.return_value = "99"
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        assert OrgTicketManager._prompt_ticket_type() == "question"


def test_prompt_ticket_id_returns_input_value():
    """_prompt_ticket_id returns whatever InputUtils yields."""
    fake_mh = _make_mh()
    fake_mh.InputUtils.safe_input.return_value = "abc-123"
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        assert OrgTicketManager._prompt_ticket_id() == "abc-123"


# ---------- _print_ticket_created_summary ----------


def test_print_ticket_created_summary(capsys):
    """_print_ticket_created_summary prints ID, subject, type and status."""
    OrgTicketManager._print_ticket_created_summary({"id": "t-1", "status": "open"}, "subj", "problem")
    out = capsys.readouterr().out
    assert "t-1" in out
    assert "subj" in out
    assert "problem" in out
    assert "open" in out


def test_print_ticket_created_summary_missing_id_status(capsys):
    """_print_ticket_created_summary tolerates missing id/status."""
    OrgTicketManager._print_ticket_created_summary({}, "subj", "question")
    out = capsys.readouterr().out
    assert "unknown" in out
    assert "open" in out


# ---------- _submit_create_ticket ----------


def test_submit_create_ticket_reraises_on_api_error(capsys):
    """_submit_create_ticket logs, prints and re-raises API errors."""
    fake_mh = _make_mh()
    fake_mh.mistapi.api.v1.orgs.tickets.createOrgTicket.side_effect = RuntimeError("api down")
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        with pytest.raises(RuntimeError, match="api down"):
            OrgTicketManager._submit_create_ticket("org-1", {"subject": "s"}, "s", "problem")
    assert "Error creating ticket" in capsys.readouterr().out


# ---------- _build_update_body ----------


def test_build_update_body_returns_only_provided_fields():
    """_build_update_body includes only fields the user filled in."""
    fake_mh = _make_mh()
    fake_mh.InputUtils.safe_input.side_effect = ["new sub", "", "problem"]
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        result = OrgTicketManager._build_update_body()
    assert result == {"subject": "new sub", "type": "problem"}


# ---------- _update_via_api ----------


def test_update_via_api_success_prints_changes(capsys):
    """_update_via_api prints each changed field."""
    fake_mh = _make_mh()
    fake_mh.mistapi.api.v1.orgs.tickets.updateOrgTicket.return_value = SimpleNamespace(data={"ok": True})
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        OrgTicketManager._update_via_api("org-1", "t-1", {"subject": "x"})
    out = capsys.readouterr().out
    assert "updated successfully" in out
    assert "subject: x" in out


def test_update_via_api_reraises_on_error(capsys):
    """_update_via_api logs, prints, and re-raises API errors."""
    fake_mh = _make_mh()
    fake_mh.mistapi.api.v1.orgs.tickets.updateOrgTicket.side_effect = RuntimeError("x")
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        with pytest.raises(RuntimeError):
            OrgTicketManager._update_via_api("org-1", "t-1", {"subject": "x"})
    assert "Error updating ticket" in capsys.readouterr().out


# ---------- _prompt_comment_and_file ----------


def test_prompt_comment_and_file_returns_tuple():
    """_prompt_comment_and_file returns (comment, file_path)."""
    fake_mh = _make_mh()
    fake_mh.InputUtils.safe_input.side_effect = ["hello", "/tmp/a.txt"]
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        assert OrgTicketManager._prompt_comment_and_file() == ("hello", "/tmp/a.txt")


# ---------- _submit_comment ----------


def test_submit_comment_with_valid_file_uses_multipart(tmp_path, capsys):
    """_submit_comment picks addOrgTicketCommentFile when file exists."""
    fake_mh = _make_mh()
    file_path = tmp_path / "attach.txt"
    file_path.write_text("data")
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        OrgTicketManager._submit_comment("org-1", "t-1", "hello", str(file_path))
    fake_mh.mistapi.api.v1.orgs.tickets.addOrgTicketCommentFile.assert_called_once()
    assert "with attachment" in capsys.readouterr().out


def test_submit_comment_with_missing_file_falls_back_to_text(capsys):
    """_submit_comment warns and submits text-only when path is missing."""
    fake_mh = _make_mh()
    with (
        patch("os.path.isfile", return_value=False),
        patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh),
    ):
        OrgTicketManager._submit_comment("org-1", "t-1", "hello", "/nope/x")
    out = capsys.readouterr().out
    assert "File not found" in out
    fake_mh.mistapi.api.v1.orgs.tickets.addOrgTicketComment.assert_called_once()


def test_submit_comment_no_file_submits_text_only():
    """_submit_comment goes text-only when no file path was given."""
    fake_mh = _make_mh()
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        OrgTicketManager._submit_comment("org-1", "t-1", "hello", "")
    fake_mh.mistapi.api.v1.orgs.tickets.addOrgTicketComment.assert_called_once()


def test_submit_comment_with_file_and_no_text_passes_none(tmp_path):
    """_submit_comment passes ``comment=None`` when comment_text is empty."""
    fake_mh = _make_mh()
    file_path = tmp_path / "a.txt"
    file_path.write_text("x")
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        OrgTicketManager._submit_comment("org-1", "t-1", "", str(file_path))
    kwargs = fake_mh.mistapi.api.v1.orgs.tickets.addOrgTicketCommentFile.call_args.kwargs
    assert kwargs["comment"] is None


# ---------- _submit_text_comment ----------


def test_submit_text_comment_calls_api(capsys):
    """_submit_text_comment sends addOrgTicketComment with body dict."""
    fake_mh = _make_mh()
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        OrgTicketManager._submit_text_comment("org-1", "t-1", "hi")
    args = fake_mh.mistapi.api.v1.orgs.tickets.addOrgTicketComment.call_args.args
    assert args[3] == {"comment": "hi"}
    assert "Comment added" in capsys.readouterr().out


# ---------- view_ticket ----------


def test_view_ticket_cancels_when_no_ticket_selected(capsys):
    """view_ticket prints cancellation when no ticket chosen."""
    fake_mh = _make_mh()
    fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"
    fake_mh.mistapi.api.v1.orgs.tickets.listOrgTickets.return_value = SimpleNamespace(data=[])
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        OrgTicketManager.view_ticket()
    assert "no ticket selected" in capsys.readouterr().out


def test_view_ticket_prints_details_on_success(capsys):
    """view_ticket calls fetch + display when ticket found."""
    fake_mh = _make_mh()
    fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"
    fake_mh.mistapi.api.v1.orgs.tickets.listOrgTickets.return_value = SimpleNamespace(
        data=[{"id": "t-1", "subject": "s", "status": "open", "type": "question"}]
    )
    fake_mh.mistapi.api.v1.orgs.tickets.getOrgTicket.return_value = SimpleNamespace(
        data={"id": "t-1", "subject": "s", "status": "open", "type": "question"}
    )
    fake_mh.InputUtils.safe_input.return_value = "1"
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        OrgTicketManager.view_ticket()
    assert "Ticket" in capsys.readouterr().out


def test_view_ticket_empty_detail_prints_message(capsys):
    """view_ticket prints 'Could not retrieve' when detail is empty."""
    fake_mh = _make_mh()
    fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"
    fake_mh.mistapi.api.v1.orgs.tickets.listOrgTickets.return_value = SimpleNamespace(
        data=[{"id": "t-1", "subject": "s", "status": "open", "type": "question"}]
    )
    fake_mh.mistapi.api.v1.orgs.tickets.getOrgTicket.side_effect = RuntimeError("nope")
    fake_mh.InputUtils.safe_input.return_value = "1"
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        OrgTicketManager.view_ticket()
    assert "Could not retrieve" in capsys.readouterr().out


# ---------- export_ticket_details ----------


def test_export_ticket_details_no_tickets(capsys):
    """export_ticket_details prints 'No tickets' when list is empty."""
    fake_mh = _make_mh()
    fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"
    fake_mh.mistapi.api.v1.orgs.tickets.listOrgTickets.return_value = SimpleNamespace(data=[])
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        OrgTicketManager.export_ticket_details()
    assert "No tickets found" in capsys.readouterr().out


def test_export_ticket_details_writes_when_details_exist():
    """export_ticket_details writes CSV via DataExporter."""
    fake_mh = _make_mh()
    fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"
    fake_mh.mistapi.api.v1.orgs.tickets.listOrgTickets.return_value = SimpleNamespace(data=[{"id": "t-1"}])
    fake_mh.mistapi.api.v1.orgs.tickets.getOrgTicket.return_value = SimpleNamespace(data={"id": "t-1", "subject": "s"})
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        OrgTicketManager.export_ticket_details()
    fake_mh.DataExporter.write_with_format_selection.assert_called_once()


def test_export_ticket_details_no_details_retrieved(capsys):
    """export_ticket_details prints message when no details are collected."""
    fake_mh = _make_mh()
    fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"
    fake_mh.mistapi.api.v1.orgs.tickets.listOrgTickets.return_value = SimpleNamespace(data=[{"id": "t-1"}])
    fake_mh.mistapi.api.v1.orgs.tickets.getOrgTicket.side_effect = RuntimeError("nope")
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        OrgTicketManager.export_ticket_details()
    assert "No ticket details could be retrieved" in capsys.readouterr().out


# ---------- _select_ticket ----------


def test_select_ticket_returns_empty_when_no_tickets():
    """_select_ticket returns '' when there are no tickets."""
    fake_mh = _make_mh()
    fake_mh.mistapi.api.v1.orgs.tickets.listOrgTickets.return_value = SimpleNamespace(data=[])
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        assert OrgTicketManager._select_ticket("org-1") == ""


def test_select_ticket_manual_id_path():
    """_select_ticket returns _prompt_ticket_id result when user picks 'm'."""
    fake_mh = _make_mh()
    fake_mh.mistapi.api.v1.orgs.tickets.listOrgTickets.return_value = SimpleNamespace(
        data=[{"id": "t-1", "subject": "s", "status": "o", "type": "q"}]
    )
    fake_mh.InputUtils.safe_input.side_effect = ["m", "manual-id"]
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        assert OrgTicketManager._select_ticket("org-1") == "manual-id"


def test_select_ticket_numeric_choice():
    """_select_ticket resolves numeric input via _resolve_ticket_choice."""
    fake_mh = _make_mh()
    fake_mh.mistapi.api.v1.orgs.tickets.listOrgTickets.return_value = SimpleNamespace(
        data=[{"id": "t-1", "subject": "s", "status": "o", "type": "q"}]
    )
    fake_mh.InputUtils.safe_input.return_value = "1"
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        assert OrgTicketManager._select_ticket("org-1") == "t-1"


def test_select_ticket_blank_input_cancels():
    """_select_ticket returns '' when user leaves prompt blank."""
    fake_mh = _make_mh()
    fake_mh.mistapi.api.v1.orgs.tickets.listOrgTickets.return_value = SimpleNamespace(
        data=[{"id": "t-1", "subject": "s", "status": "o", "type": "q"}]
    )
    fake_mh.InputUtils.safe_input.return_value = ""
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        assert OrgTicketManager._select_ticket("org-1") == ""


# ---------- _fetch_tickets_for_selection ----------


def test_fetch_tickets_for_selection_prints_when_empty(capsys):
    """_fetch_tickets_for_selection prints message when API returns []."""
    fake_mh = _make_mh()
    fake_mh.mistapi.api.v1.orgs.tickets.listOrgTickets.return_value = SimpleNamespace(data=[])
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        assert OrgTicketManager._fetch_tickets_for_selection("org-1") == []
    assert "No tickets found" in capsys.readouterr().out


def test_fetch_tickets_for_selection_handles_api_error(capsys):
    """_fetch_tickets_for_selection returns [] and prints error on exception."""
    fake_mh = _make_mh()
    fake_mh.mistapi.api.v1.orgs.tickets.listOrgTickets.side_effect = RuntimeError("x")
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        assert OrgTicketManager._fetch_tickets_for_selection("org-1") == []
    assert "Error fetching tickets" in capsys.readouterr().out


# ---------- _render_ticket_list_table ----------


def test_render_ticket_list_table_prints_rows(capsys):
    """_render_ticket_list_table prints one row per ticket."""
    OrgTicketManager._render_ticket_list_table(
        [
            {"status": "open", "type": "problem", "subject": "abc"},
            {},
        ]
    )
    out = capsys.readouterr().out
    assert "open" in out
    assert "problem" in out
    assert "abc" in out
    assert "(no subject)" in out
    assert "unknown" in out


# ---------- _resolve_ticket_choice ----------


def test_resolve_ticket_choice_valid_returns_id(capsys):
    """_resolve_ticket_choice returns id and prints subject on valid pick."""
    result = OrgTicketManager._resolve_ticket_choice(
        "1",
        [{"id": "t-1", "subject": "s"}],
    )
    assert result == "t-1"
    assert "Selected" in capsys.readouterr().out


def test_resolve_ticket_choice_non_numeric(capsys):
    """_resolve_ticket_choice returns '' on non-numeric input."""
    assert OrgTicketManager._resolve_ticket_choice("abc", [{"id": "t-1"}]) == ""
    assert "Invalid selection" in capsys.readouterr().out


def test_resolve_ticket_choice_out_of_range(capsys):
    """_resolve_ticket_choice returns '' on out-of-range index."""
    assert OrgTicketManager._resolve_ticket_choice("5", [{"id": "t-1"}]) == ""
    assert "Invalid selection" in capsys.readouterr().out


# ---------- _fetch_ticket_detail ----------


def test_fetch_ticket_detail_returns_data():
    """_fetch_ticket_detail returns ticket dict on success."""
    fake_mh = _make_mh()
    fake_mh.mistapi.api.v1.orgs.tickets.getOrgTicket.return_value = SimpleNamespace(data={"id": "t-1"})
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        assert OrgTicketManager._fetch_ticket_detail("org-1", "t-1") == {"id": "t-1"}


def test_fetch_ticket_detail_returns_empty_dict_on_error(capsys):
    """_fetch_ticket_detail returns {} and prints on failure."""
    fake_mh = _make_mh()
    fake_mh.mistapi.api.v1.orgs.tickets.getOrgTicket.side_effect = RuntimeError("x")
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        assert OrgTicketManager._fetch_ticket_detail("org-1", "t-1") == {}
    assert "Error fetching ticket" in capsys.readouterr().out


def test_fetch_ticket_detail_returns_empty_when_data_none():
    """_fetch_ticket_detail returns {} when SDK data is None."""
    fake_mh = _make_mh()
    fake_mh.mistapi.api.v1.orgs.tickets.getOrgTicket.return_value = SimpleNamespace(data=None)
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        assert OrgTicketManager._fetch_ticket_detail("org-1", "t-1") == {}


# ---------- _fetch_all_ticket_summaries ----------


def test_fetch_all_ticket_summaries_returns_list():
    """_fetch_all_ticket_summaries returns SDK data list."""
    fake_mh = _make_mh()
    fake_mh.mistapi.api.v1.orgs.tickets.listOrgTickets.return_value = SimpleNamespace(data=[{"id": "t-1"}])
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        assert OrgTicketManager._fetch_all_ticket_summaries("org-1") == [{"id": "t-1"}]


def test_fetch_all_ticket_summaries_reraises_on_error(capsys):
    """_fetch_all_ticket_summaries re-raises API error after logging."""
    fake_mh = _make_mh()
    fake_mh.mistapi.api.v1.orgs.tickets.listOrgTickets.side_effect = RuntimeError("x")
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        with pytest.raises(RuntimeError):
            OrgTicketManager._fetch_all_ticket_summaries("org-1")
    assert "Error fetching tickets" in capsys.readouterr().out


def test_fetch_all_ticket_summaries_none_data_returns_empty():
    """_fetch_all_ticket_summaries yields [] when SDK data is None."""
    fake_mh = _make_mh()
    fake_mh.mistapi.api.v1.orgs.tickets.listOrgTickets.return_value = SimpleNamespace(data=None)
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        assert OrgTicketManager._fetch_all_ticket_summaries("org-1") == []


# ---------- _collect_ticket_details ----------


def test_collect_ticket_details_skips_ticket_without_id(capsys):
    """_collect_ticket_details skips tickets that have no id."""
    fake_mh = _make_mh()
    fake_mh.mistapi.api.v1.orgs.tickets.getOrgTicket.return_value = SimpleNamespace(data={"id": "t-1", "subject": "s"})
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        details = OrgTicketManager._collect_ticket_details("org-1", [{}, {"id": "t-1"}])
    assert len(details) == 1


def test_collect_ticket_details_returns_empty_for_all_failed(capsys):
    """_collect_ticket_details returns [] when every fetch fails."""
    fake_mh = _make_mh()
    fake_mh.mistapi.api.v1.orgs.tickets.getOrgTicket.side_effect = RuntimeError("x")
    with patch("src.org.org_ticket_manager.importlib.import_module", return_value=fake_mh):
        assert OrgTicketManager._collect_ticket_details("org-1", [{"id": "t-1"}]) == []


# ---------- _display_ticket_detail ----------


def test_display_ticket_detail_prints_metadata_and_comments(capsys):
    """_display_ticket_detail prints subject, id, comments."""
    OrgTicketManager._display_ticket_detail(
        {
            "subject": "s",
            "id": "t-1",
            "status": "open",
            "type": "problem",
            "comments": [
                {
                    "author": "a",
                    "created_at": "2026-01-01",
                    "comment": "hi",
                    "attachments": [{"name": "f.txt"}],
                }
            ],
        }
    )
    out = capsys.readouterr().out
    assert "s" in out
    assert "t-1" in out
    assert "hi" in out
    assert "Attachment" in out


# ---------- _render_comments_block ----------


def test_render_comments_block_no_comments(capsys):
    """_render_comments_block prints 'No comments' when list is empty."""
    OrgTicketManager._render_comments_block([])
    assert "No comments" in capsys.readouterr().out


def test_render_comments_block_prints_each_comment(capsys):
    """_render_comments_block prints author, timestamp, body, attachments."""
    OrgTicketManager._render_comments_block(
        [
            {
                "author": "a",
                "created_at": "t1",
                "comment": "hello",
                "attachments": [{"name": "x.txt"}],
            },
            {"attachments": None},
        ]
    )
    out = capsys.readouterr().out
    assert "hello" in out
    assert "x.txt" in out
    assert "unknown" in out
    assert "(no text)" in out


def test_render_comments_block_uses_content_url_when_no_name(capsys):
    """_render_comments_block falls back to content_url when name missing."""
    OrgTicketManager._render_comments_block(
        [
            {
                "author": "a",
                "created_at": "t1",
                "comment": "hi",
                "attachments": [{"content_url": "http://x"}, {}],
            }
        ]
    )
    out = capsys.readouterr().out
    assert "http://x" in out
    assert "file" in out
