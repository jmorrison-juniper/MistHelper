"""
Unit tests for OrgTicketManager (Menus 188-193).

Covers: list tickets, create ticket, add comment (text and file),
update ticket, view ticket detail, export ticket details,
ticket selector, and edge cases (blank subject, blank ticket ID, no changes).
"""

import csv
from unittest.mock import MagicMock

import pytest

import MistHelper

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _stub_org_id(monkeypatch):
    """Patch ConfigUtils to return a fixed org_id without prompting."""
    monkeypatch.setattr(  # Override org ID resolution to avoid interactive prompt
        MistHelper.ConfigUtils,
        "get_cached_or_prompted_org_id",
        lambda: "org-test-1",
    )


def _make_api_response(data):
    """Build a MagicMock that mimics a mistapi APIResponse."""
    resp = MagicMock()  # Create mock API response object
    resp.data = data  # Set data attribute to provided dict/list
    resp.status_code = 200  # Simulate successful HTTP status
    return resp  # Return configured mock


# ---------------------------------------------------------------------------
# Menu 188 -- list_tickets
# ---------------------------------------------------------------------------


class TestListTickets:
    """Tests for OrgTicketManager.list_tickets (Menu 188)."""

    def test_list_tickets_exports_csv(self, monkeypatch, tmp_path):
        """Verify list_tickets writes a CSV with ticket records."""
        _stub_org_id(monkeypatch)  # Fix org_id to avoid prompt
        monkeypatch.chdir(tmp_path)  # Write output to temp directory

        sample_tickets = [  # Two sample ticket records for export
            {"id": "t1", "subject": "AP offline", "status": "open", "type": "problem", "created_at": 1700000000},
            {"id": "t2", "subject": "Slow WiFi", "status": "closed", "type": "question", "created_at": 1700000100},
        ]

        def fake_list(session, org_id, **kwargs):
            """Stub listOrgTickets that returns sample data."""
            return _make_api_response(sample_tickets)  # Return mock response with sample data

        monkeypatch.setattr(  # Replace real API call with stub
            MistHelper.mistapi.api.v1.orgs.tickets,
            "listOrgTickets",
            fake_list,
        )
        monkeypatch.setattr(  # Bypass pagination helper to return raw data
            MistHelper.mistapi,
            "get_all",
            lambda response, mist_session: sample_tickets,
        )

        MistHelper.OrgTicketManager.list_tickets()  # Execute the menu operation

        csv_path = tmp_path / "data" / "OrgTickets.csv"  # Expected output path
        assert csv_path.exists(), f"Expected CSV at {csv_path}"  # Verify file was created

        with open(csv_path, newline="", encoding="utf-8") as fh:  # Read the CSV output
            rows = list(csv.DictReader(fh))  # Parse CSV into list of dicts

        assert len(rows) == 2  # Should have 2 ticket rows
        ids = [r["id"] for r in rows]  # Extract ticket IDs from output
        assert "t1" in ids and "t2" in ids  # Both tickets should be present

    def test_list_tickets_empty_result(self, monkeypatch, tmp_path):
        """Verify list_tickets handles empty API response gracefully."""
        _stub_org_id(monkeypatch)  # Fix org_id to avoid prompt
        monkeypatch.chdir(tmp_path)  # Write output to temp directory

        def fake_list(session, org_id, **kwargs):
            """Stub that returns empty results."""
            return _make_api_response([])  # Return empty list

        monkeypatch.setattr(  # Replace real API call with stub
            MistHelper.mistapi.api.v1.orgs.tickets,
            "listOrgTickets",
            fake_list,
        )
        monkeypatch.setattr(  # Return empty data from pagination
            MistHelper.mistapi,
            "get_all",
            lambda response, mist_session: [],
        )

        MistHelper.OrgTicketManager.list_tickets()  # Should not raise

        csv_path = tmp_path / "data" / "OrgTickets.csv"  # Check output path
        assert not csv_path.exists()  # No CSV should be written for empty data


# ---------------------------------------------------------------------------
# Menu 189 -- create_ticket
# ---------------------------------------------------------------------------


class TestCreateTicket:
    """Tests for OrgTicketManager.create_ticket (Menu 189)."""

    def test_create_ticket_success(self, monkeypatch):
        """Verify create_ticket calls API with correct body."""
        _stub_org_id(monkeypatch)  # Fix org_id to avoid prompt

        input_responses = iter(
            [  # Simulate user inputs in order
                "AP keeps rebooting",  # Subject
                "2",  # Type selection (problem)
                "Happens every morning",  # Comment
            ]
        )
        monkeypatch.setattr(  # Override safe_input to return scripted responses
            MistHelper.InputUtils,
            "safe_input",
            lambda prompt, default_value="", allow_empty=True, context="unknown": next(input_responses),
        )

        captured = {}  # Capture API call arguments

        def fake_create(session, org_id, body):
            """Stub createOrgTicket to capture the request body."""
            captured["org_id"] = org_id  # Record org_id passed to API
            captured["body"] = body  # Record request body for assertion
            return _make_api_response({"id": "new-ticket-1", "status": "open"})  # Return success

        monkeypatch.setattr(  # Replace real API call with stub
            MistHelper.mistapi.api.v1.orgs.tickets,
            "createOrgTicket",
            fake_create,
        )

        MistHelper.OrgTicketManager.create_ticket()  # Execute the menu operation

        assert captured["org_id"] == "org-test-1"  # Verify correct org was used
        assert captured["body"]["subject"] == "AP keeps rebooting"  # Verify subject was passed
        assert captured["body"]["type"] == "problem"  # Verify type selection (2 = problem)
        assert captured["body"]["comment"] == "Happens every morning"  # Verify comment was included

    def test_create_ticket_blank_subject_cancels(self, monkeypatch, capsys):
        """Verify create_ticket aborts when subject is blank."""
        _stub_org_id(monkeypatch)  # Fix org_id to avoid prompt

        monkeypatch.setattr(  # Override safe_input to return blank subject
            MistHelper.InputUtils,
            "safe_input",
            lambda prompt, default_value="", allow_empty=True, context="unknown": "",
        )

        fake_create = MagicMock()  # Mock API function to verify it's NOT called
        monkeypatch.setattr(  # Replace real API call with mock
            MistHelper.mistapi.api.v1.orgs.tickets,
            "createOrgTicket",
            fake_create,
        )

        MistHelper.OrgTicketManager.create_ticket()  # Execute with blank subject

        fake_create.assert_not_called()  # API should not be called when subject is blank
        output = capsys.readouterr().out  # Capture printed output
        assert "cancelled" in output.lower()  # User should see cancellation message


# ---------------------------------------------------------------------------
# Menu 190 -- add_comment
# ---------------------------------------------------------------------------


class TestAddComment:
    """Tests for OrgTicketManager.add_comment (Menu 190)."""

    def test_add_text_comment(self, monkeypatch):
        """Verify add_comment sends text-only comment via API."""
        _stub_org_id(monkeypatch)  # Fix org_id to avoid prompt

        monkeypatch.setattr(  # Bypass ticket selector -- return fixed ID directly
            MistHelper.OrgTicketManager,
            "_select_ticket",
            staticmethod(lambda org_id: "ticket-uuid-123"),
        )

        input_responses = iter(
            [  # Simulate user inputs in order
                "Please investigate ASAP",  # Comment text
                "",  # No file attachment
            ]
        )
        monkeypatch.setattr(  # Override safe_input to return scripted responses
            MistHelper.InputUtils,
            "safe_input",
            lambda prompt, default_value="", allow_empty=True, context="unknown": next(input_responses),
        )

        captured = {}  # Capture API call arguments

        def fake_add_comment(session, org_id, ticket_id, body):
            """Stub addOrgTicketComment to capture the request."""
            captured["ticket_id"] = ticket_id  # Record ticket ID
            captured["body"] = body  # Record comment body
            return _make_api_response({})  # Return success

        monkeypatch.setattr(  # Replace real API call with stub
            MistHelper.mistapi.api.v1.orgs.tickets,
            "addOrgTicketComment",
            fake_add_comment,
        )

        MistHelper.OrgTicketManager.add_comment()  # Execute the menu operation

        assert captured["ticket_id"] == "ticket-uuid-123"  # Verify correct ticket targeted
        assert captured["body"]["comment"] == "Please investigate ASAP"  # Verify comment text

    def test_add_comment_with_file(self, monkeypatch, tmp_path):
        """Verify add_comment uses multipart API when file is attached."""
        _stub_org_id(monkeypatch)  # Fix org_id to avoid prompt

        monkeypatch.setattr(  # Bypass ticket selector -- return fixed ID directly
            MistHelper.OrgTicketManager,
            "_select_ticket",
            staticmethod(lambda org_id: "ticket-uuid-456"),
        )

        test_file = tmp_path / "screenshot.png"  # Create a test file for attachment
        test_file.write_text("fake image data")  # Write some content to make it a real file

        input_responses = iter(
            [  # Simulate user inputs in order
                "See attached screenshot",  # Comment text
                str(test_file),  # File path to attach
            ]
        )
        monkeypatch.setattr(  # Override safe_input to return scripted responses
            MistHelper.InputUtils,
            "safe_input",
            lambda prompt, default_value="", allow_empty=True, context="unknown": next(input_responses),
        )

        captured = {}  # Capture API call arguments

        def fake_add_file(session, org_id, ticket_id, comment=None, file=None):
            """Stub addOrgTicketCommentFile to capture the multipart request."""
            captured["ticket_id"] = ticket_id  # Record ticket ID
            captured["comment"] = comment  # Record comment text
            captured["file"] = file  # Record file path
            return _make_api_response({})  # Return success

        monkeypatch.setattr(  # Replace multipart API call with stub
            MistHelper.mistapi.api.v1.orgs.tickets,
            "addOrgTicketCommentFile",
            fake_add_file,
        )

        MistHelper.OrgTicketManager.add_comment()  # Execute the menu operation

        assert captured["ticket_id"] == "ticket-uuid-456"  # Verify correct ticket targeted
        assert captured["comment"] == "See attached screenshot"  # Verify comment text passed
        assert captured["file"] == str(test_file)  # Verify file path passed

    def test_add_comment_blank_ticket_id_cancels(self, monkeypatch, capsys):
        """Verify add_comment aborts when no ticket is selected."""
        _stub_org_id(monkeypatch)  # Fix org_id to avoid prompt

        monkeypatch.setattr(  # Bypass ticket selector -- return empty to simulate cancel
            MistHelper.OrgTicketManager,
            "_select_ticket",
            staticmethod(lambda org_id: ""),
        )

        fake_api = MagicMock()  # Mock to verify API is NOT called
        monkeypatch.setattr(  # Replace API call with mock
            MistHelper.mistapi.api.v1.orgs.tickets,
            "addOrgTicketComment",
            fake_api,
        )

        MistHelper.OrgTicketManager.add_comment()  # Execute with blank ID

        fake_api.assert_not_called()  # API should not be called
        output = capsys.readouterr().out  # Capture printed output
        assert "cancelled" in output.lower()  # User should see cancellation message

    def test_add_comment_no_content_cancels(self, monkeypatch, capsys):
        """Verify add_comment aborts when neither comment nor file is provided."""
        _stub_org_id(monkeypatch)  # Fix org_id to avoid prompt

        monkeypatch.setattr(  # Bypass ticket selector -- return fixed ID directly
            MistHelper.OrgTicketManager,
            "_select_ticket",
            staticmethod(lambda org_id: "ticket-uuid-789"),
        )

        input_responses = iter(
            [  # Simulate user inputs
                "",  # Empty comment
                "",  # No file path
            ]
        )
        monkeypatch.setattr(  # Override safe_input to return scripted responses
            MistHelper.InputUtils,
            "safe_input",
            lambda prompt, default_value="", allow_empty=True, context="unknown": next(input_responses),
        )

        fake_api = MagicMock()  # Mock to verify API is NOT called
        monkeypatch.setattr(  # Replace API call with mock
            MistHelper.mistapi.api.v1.orgs.tickets,
            "addOrgTicketComment",
            fake_api,
        )

        MistHelper.OrgTicketManager.add_comment()  # Execute with no content

        fake_api.assert_not_called()  # API should not be called
        output = capsys.readouterr().out  # Capture printed output
        assert "cancelled" in output.lower()  # User should see cancellation message

    def test_add_comment_missing_file_falls_back(self, monkeypatch, capsys):
        """Verify add_comment falls back to text-only when file path doesn't exist."""
        _stub_org_id(monkeypatch)  # Fix org_id to avoid prompt

        monkeypatch.setattr(  # Bypass ticket selector -- return fixed ID directly
            MistHelper.OrgTicketManager,
            "_select_ticket",
            staticmethod(lambda org_id: "ticket-uuid-abc"),
        )

        input_responses = iter(
            [  # Simulate user inputs
                "Here is my comment",  # Comment text
                "/nonexistent/path/file.txt",  # File path that doesn't exist
            ]
        )
        monkeypatch.setattr(  # Override safe_input to return scripted responses
            MistHelper.InputUtils,
            "safe_input",
            lambda prompt, default_value="", allow_empty=True, context="unknown": next(input_responses),
        )

        captured = {}  # Capture API call arguments

        def fake_add_comment(session, org_id, ticket_id, body):
            """Stub addOrgTicketComment for text-only fallback."""
            captured["ticket_id"] = ticket_id  # Record ticket ID
            captured["body"] = body  # Record comment body
            return _make_api_response({})  # Return success

        monkeypatch.setattr(  # Replace text comment API with stub
            MistHelper.mistapi.api.v1.orgs.tickets,
            "addOrgTicketComment",
            fake_add_comment,
        )

        MistHelper.OrgTicketManager.add_comment()  # Execute with nonexistent file

        assert captured["ticket_id"] == "ticket-uuid-abc"  # Should fall back to text comment
        assert captured["body"]["comment"] == "Here is my comment"  # Comment text preserved
        output = capsys.readouterr().out  # Capture printed output
        assert "not found" in output.lower()  # User should see warning about missing file


# ---------------------------------------------------------------------------
# Menu 191 -- update_ticket
# ---------------------------------------------------------------------------


class TestUpdateTicket:
    """Tests for OrgTicketManager.update_ticket (Menu 191)."""

    def test_update_ticket_success(self, monkeypatch):
        """Verify update_ticket sends correct fields to API."""
        _stub_org_id(monkeypatch)  # Fix org_id to avoid prompt

        monkeypatch.setattr(  # Bypass ticket selector -- return fixed ID directly
            MistHelper.OrgTicketManager,
            "_select_ticket",
            staticmethod(lambda org_id: "ticket-uuid-update"),
        )

        input_responses = iter(
            [  # Simulate user inputs in order
                "Updated subject line",  # New subject
                "closed",  # New status
                "",  # Skip type change
            ]
        )
        monkeypatch.setattr(  # Override safe_input to return scripted responses
            MistHelper.InputUtils,
            "safe_input",
            lambda prompt, default_value="", allow_empty=True, context="unknown": next(input_responses),
        )

        captured = {}  # Capture API call arguments

        def fake_update(session, org_id, ticket_id, body):
            """Stub updateOrgTicket to capture the request."""
            captured["ticket_id"] = ticket_id  # Record ticket ID
            captured["body"] = body  # Record update body
            return _make_api_response({"id": ticket_id, "status": "closed"})  # Return success

        monkeypatch.setattr(  # Replace real API call with stub
            MistHelper.mistapi.api.v1.orgs.tickets,
            "updateOrgTicket",
            fake_update,
        )

        MistHelper.OrgTicketManager.update_ticket()  # Execute the menu operation

        assert captured["ticket_id"] == "ticket-uuid-update"  # Verify correct ticket targeted
        assert captured["body"]["subject"] == "Updated subject line"  # Verify subject change
        assert captured["body"]["status"] == "closed"  # Verify status change
        assert "type" not in captured["body"]  # Type was skipped (blank input)

    def test_update_ticket_blank_id_cancels(self, monkeypatch, capsys):
        """Verify update_ticket aborts when no ticket is selected."""
        _stub_org_id(monkeypatch)  # Fix org_id to avoid prompt

        monkeypatch.setattr(  # Bypass ticket selector -- return empty to simulate cancel
            MistHelper.OrgTicketManager,
            "_select_ticket",
            staticmethod(lambda org_id: ""),
        )

        fake_update = MagicMock()  # Mock to verify API is NOT called
        monkeypatch.setattr(  # Replace API call with mock
            MistHelper.mistapi.api.v1.orgs.tickets,
            "updateOrgTicket",
            fake_update,
        )

        MistHelper.OrgTicketManager.update_ticket()  # Execute with cancelled selection

        fake_update.assert_not_called()  # API should not be called
        output = capsys.readouterr().out  # Capture printed output
        assert "cancelled" in output.lower()  # User should see cancellation message

    def test_update_ticket_no_changes_cancels(self, monkeypatch, capsys):
        """Verify update_ticket aborts when all fields are left blank."""
        _stub_org_id(monkeypatch)  # Fix org_id to avoid prompt

        monkeypatch.setattr(  # Bypass ticket selector -- return fixed ID directly
            MistHelper.OrgTicketManager,
            "_select_ticket",
            staticmethod(lambda org_id: "ticket-uuid-no-change"),
        )

        input_responses = iter(
            [  # Simulate user inputs
                "",  # Skip subject
                "",  # Skip status
                "",  # Skip type
            ]
        )
        monkeypatch.setattr(  # Override safe_input to return scripted responses
            MistHelper.InputUtils,
            "safe_input",
            lambda prompt, default_value="", allow_empty=True, context="unknown": next(input_responses),
        )

        fake_update = MagicMock()  # Mock to verify API is NOT called
        monkeypatch.setattr(  # Replace API call with mock
            MistHelper.mistapi.api.v1.orgs.tickets,
            "updateOrgTicket",
            fake_update,
        )

        MistHelper.OrgTicketManager.update_ticket()  # Execute with no changes

        fake_update.assert_not_called()  # API should not be called
        output = capsys.readouterr().out  # Capture printed output
        assert "cancelled" in output.lower() or "no changes" in output.lower()  # User should see message


# ---------------------------------------------------------------------------
# PK Strategy coverage
# ---------------------------------------------------------------------------


class TestPKStrategies:
    """Verify primary key strategies are defined for all ticket endpoints."""

    @pytest.mark.parametrize(
        "endpoint",
        [
            "listOrgTickets",
            "getOrgTicket",
            "createOrgTicket",
            "updateOrgTicket",
            "addOrgTicketComment",
        ],
    )
    def test_pk_strategy_defined(self, endpoint):
        """Each ticket endpoint must have a PK strategy entry."""
        strategies = MistHelper.ENDPOINT_PRIMARY_KEY_STRATEGIES  # Access the global PK strategies dict
        assert endpoint in strategies, f"Missing PK strategy for {endpoint}"  # Verify entry exists
        assert "type" in strategies[endpoint]  # Verify strategy has a type field
        assert "primary_key" in strategies[endpoint]  # Verify strategy has primary_key field


# ---------------------------------------------------------------------------
# Menu registration coverage
# ---------------------------------------------------------------------------


class TestMenuRegistration:
    """Verify ticket operations are registered in menu_actions."""

    @pytest.mark.parametrize(
        "menu_num,expected_fn",
        [
            ("188", "list_tickets"),
            ("189", "create_ticket"),
            ("190", "add_comment"),
            ("191", "update_ticket"),
            ("192", "view_ticket"),
            ("193", "export_ticket_details"),
        ],
    )
    def test_menu_entry_exists(self, menu_num, expected_fn):
        """Each ticket menu number must be registered with the correct function."""
        actions = MistHelper.menu_actions  # Access the global menu_actions dict
        assert menu_num in actions, f"Menu {menu_num} not registered"  # Verify entry exists
        fn = actions[menu_num][0]  # Get the function/lambda from the tuple
        assert expected_fn in fn.__name__ or expected_fn in str(fn)  # Verify correct function bound


# ---------------------------------------------------------------------------
# Menu 192 -- view_ticket
# ---------------------------------------------------------------------------


class TestViewTicket:
    """Tests for OrgTicketManager.view_ticket (Menu 192)."""

    def test_view_ticket_displays_detail(self, monkeypatch, capsys):
        """Verify view_ticket fetches and displays ticket with comments."""
        _stub_org_id(monkeypatch)  # Fix org_id to avoid prompt

        monkeypatch.setattr(  # Bypass ticket selector -- return fixed ID directly
            MistHelper.OrgTicketManager,
            "_select_ticket",
            staticmethod(lambda org_id: "ticket-view-1"),
        )

        sample_detail = {  # Full ticket data with comments for display
            "id": "ticket-view-1",
            "subject": "AP keeps dropping clients",
            "status": "open",
            "type": "problem",
            "created_at": 1700000000,
            "updated_at": 1700001000,
            "comments": [
                {"author": "jmorrison", "created_at": 1700000100, "comment": "Started investigation"},
                {"author": "support", "created_at": 1700000200, "comment": "Collecting logs"},
            ],
        }

        monkeypatch.setattr(  # Mock _fetch_ticket_detail to return sample data
            MistHelper.OrgTicketManager,
            "_fetch_ticket_detail",
            staticmethod(lambda org_id, ticket_id: sample_detail),
        )

        MistHelper.OrgTicketManager.view_ticket()  # Execute the menu operation

        output = capsys.readouterr().out  # Capture printed output
        assert "AP keeps dropping clients" in output  # Subject should be displayed
        assert "jmorrison" in output  # First comment author should appear
        assert "Started investigation" in output  # First comment text should appear
        assert "Collecting logs" in output  # Second comment text should appear

    def test_view_ticket_cancelled(self, monkeypatch, capsys):
        """Verify view_ticket aborts when no ticket is selected."""
        _stub_org_id(monkeypatch)  # Fix org_id to avoid prompt

        monkeypatch.setattr(  # Bypass ticket selector -- return empty to simulate cancel
            MistHelper.OrgTicketManager,
            "_select_ticket",
            staticmethod(lambda org_id: ""),
        )

        MistHelper.OrgTicketManager.view_ticket()  # Execute with cancelled selection

        output = capsys.readouterr().out  # Capture printed output
        assert "cancelled" in output.lower()  # User should see cancellation message


# ---------------------------------------------------------------------------
# Menu 193 -- export_ticket_details
# ---------------------------------------------------------------------------


class TestExportTicketDetails:
    """Tests for OrgTicketManager.export_ticket_details (Menu 193)."""

    def test_export_details_writes_csv(self, monkeypatch, tmp_path):
        """Verify export_ticket_details fetches all tickets and writes CSV."""
        _stub_org_id(monkeypatch)  # Fix org_id to avoid prompt
        monkeypatch.chdir(tmp_path)  # Write output to temp directory

        sample_tickets = [  # Ticket summaries from listOrgTickets
            {"id": "t1", "subject": "AP offline", "status": "open"},
            {"id": "t2", "subject": "Slow WiFi", "status": "closed"},
        ]
        sample_details = {  # Full ticket data keyed by ID for mock lookup
            "t1": {"id": "t1", "subject": "AP offline", "status": "open", "comments": []},
            "t2": {
                "id": "t2",
                "subject": "Slow WiFi",
                "status": "closed",
                "comments": [
                    {"author": "support", "comment": "Resolved", "created_at": 1700000100},
                ],
            },
        }

        def fake_list(session, org_id, **kwargs):
            """Stub listOrgTickets that returns sample summaries."""
            return _make_api_response(sample_tickets)  # Return mock response

        monkeypatch.setattr(  # Replace real list API call with stub
            MistHelper.mistapi.api.v1.orgs.tickets,
            "listOrgTickets",
            fake_list,
        )
        monkeypatch.setattr(  # Mock _fetch_ticket_detail to return sample data by ID
            MistHelper.OrgTicketManager,
            "_fetch_ticket_detail",
            staticmethod(lambda org_id, ticket_id: sample_details.get(ticket_id, {})),
        )

        MistHelper.OrgTicketManager.export_ticket_details()  # Execute the menu operation

        csv_path = tmp_path / "data" / "OrgTicketDetails.csv"  # Expected output path
        assert csv_path.exists(), f"Expected CSV at {csv_path}"  # Verify file was created

        with open(csv_path, newline="", encoding="utf-8") as fh:  # Read the CSV output
            rows = list(csv.DictReader(fh))  # Parse CSV into list of dicts

        assert len(rows) == 2  # Should have 2 ticket detail rows

    def test_export_details_no_tickets(self, monkeypatch, capsys):
        """Verify export_ticket_details handles empty ticket list."""
        _stub_org_id(monkeypatch)  # Fix org_id to avoid prompt

        def fake_list(session, org_id, **kwargs):
            """Stub that returns empty ticket list."""
            return _make_api_response([])  # Return empty list

        monkeypatch.setattr(  # Replace real API call with stub
            MistHelper.mistapi.api.v1.orgs.tickets,
            "listOrgTickets",
            fake_list,
        )

        MistHelper.OrgTicketManager.export_ticket_details()  # Execute with no tickets

        output = capsys.readouterr().out  # Capture printed output
        assert "no tickets" in output.lower()  # User should see empty message


# ---------------------------------------------------------------------------
# _select_ticket helper
# ---------------------------------------------------------------------------


class TestSelectTicket:
    """Tests for OrgTicketManager._select_ticket helper."""

    def test_select_by_index(self, monkeypatch):
        """Verify _select_ticket returns correct ticket when user picks by index."""
        sample_tickets = [  # Two tickets for selection list
            {"id": "t-sel-1", "subject": "First ticket", "status": "open", "type": "problem"},
            {"id": "t-sel-2", "subject": "Second ticket", "status": "closed", "type": "question"},
        ]

        def fake_list(session, org_id, **kwargs):
            """Stub listOrgTickets for selector."""
            return _make_api_response(sample_tickets)  # Return mock response

        monkeypatch.setattr(  # Replace real API call with stub
            MistHelper.mistapi.api.v1.orgs.tickets,
            "listOrgTickets",
            fake_list,
        )
        monkeypatch.setattr(  # Override safe_input to select second ticket by index
            MistHelper.InputUtils,
            "safe_input",
            lambda prompt, default_value="", allow_empty=True, context="unknown": "2",
        )

        result = MistHelper.OrgTicketManager._select_ticket("org-test-1")  # Execute selector

        assert result == "t-sel-2"  # Should return the second ticket's ID

    def test_select_empty_cancels(self, monkeypatch):
        """Verify _select_ticket returns empty when user presses enter."""
        sample_tickets = [  # One ticket for selection list
            {"id": "t-cancel", "subject": "Cancel test", "status": "open", "type": "problem"},
        ]

        def fake_list(session, org_id, **kwargs):
            """Stub listOrgTickets for cancel test."""
            return _make_api_response(sample_tickets)  # Return mock response

        monkeypatch.setattr(  # Replace real API call with stub
            MistHelper.mistapi.api.v1.orgs.tickets,
            "listOrgTickets",
            fake_list,
        )
        monkeypatch.setattr(  # Override safe_input to return blank (cancel)
            MistHelper.InputUtils,
            "safe_input",
            lambda prompt, default_value="", allow_empty=True, context="unknown": "",
        )

        result = MistHelper.OrgTicketManager._select_ticket("org-test-1")  # Execute selector

        assert result == ""  # Should return empty string for cancellation

    def test_select_no_tickets(self, monkeypatch, capsys):
        """Verify _select_ticket returns empty when no tickets exist."""

        def fake_list(session, org_id, **kwargs):
            """Stub listOrgTickets returning empty list."""
            return _make_api_response([])  # Return empty list

        monkeypatch.setattr(  # Replace real API call with stub
            MistHelper.mistapi.api.v1.orgs.tickets,
            "listOrgTickets",
            fake_list,
        )

        result = MistHelper.OrgTicketManager._select_ticket("org-test-1")  # Execute selector

        assert result == ""  # Should return empty string
        output = capsys.readouterr().out  # Capture printed output
        assert "no tickets" in output.lower()  # User should see empty message
