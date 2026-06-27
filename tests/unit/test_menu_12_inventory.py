"""Unit tests for Menu 12 - Organization Inventory Export.

Tests verify that OrgInventoryExporter.inventory() correctly wires
APIDataFetcher with the expected parameters and integrates with the
PROGRESS_EMITTER lifecycle. All API calls are mocked.

Covers: FR-001, FR-005, US1, US4 from spec-024.
"""

from unittest.mock import MagicMock

import MistHelper


class TestInventoryAPIDataFetcherWiring:
    """Verify OrgInventoryExporter passes correct params to APIDataFetcher."""

    def test_creates_fetcher_with_correct_params(self, monkeypatch):
        """FR-001: APIDataFetcher receives api_call, filename, sort_key, limit."""
        captured_kwargs: dict = {}

        class MockFetcher:
            def __init__(self, **kwargs):
                captured_kwargs.update(kwargs)

            def execute(self):
                pass

        monkeypatch.setattr(MistHelper, "APIDataFetcher", MockFetcher)
        monkeypatch.setattr(MistHelper, "PROGRESS_EMITTER", None)

        MistHelper.OrgInventoryExporter.inventory()

        assert captured_kwargs["title"] == "Org Inventory:"
        assert captured_kwargs["api_call"] is MistHelper.mistapi.api.v1.orgs.inventory.getOrgInventory
        assert captured_kwargs["filename"] == "OrgInventory.csv"
        assert captured_kwargs["sort_key"] == "model"
        assert captured_kwargs["limit"] == 1000

    def test_calls_execute_exactly_once(self, monkeypatch):
        """US1: execute() is called exactly once per invocation."""
        mock_instance = MagicMock()

        class MockFetcher:
            def __init__(self, **kwargs):
                pass

            def execute(self):
                mock_instance.execute()

        monkeypatch.setattr(MistHelper, "APIDataFetcher", MockFetcher)
        monkeypatch.setattr(MistHelper, "PROGRESS_EMITTER", None)

        MistHelper.OrgInventoryExporter.inventory()

        mock_instance.execute.assert_called_once()

    def test_handles_empty_api_response(self, monkeypatch):
        """US1 Scenario 3: Empty result does not crash."""
        execute_called = False

        class MockFetcher:
            def __init__(self, **kwargs):
                pass

            def execute(self):
                nonlocal execute_called
                execute_called = True

        monkeypatch.setattr(MistHelper, "APIDataFetcher", MockFetcher)
        monkeypatch.setattr(MistHelper, "PROGRESS_EMITTER", None)

        MistHelper.OrgInventoryExporter.inventory()

        assert execute_called


class TestInventoryProgressEmitter:
    """Verify PROGRESS_EMITTER lifecycle calls during Menu 12 export."""

    def test_emits_start_and_complete(self, monkeypatch):
        """US4: emit_progress_start and emit_progress_complete called."""
        mock_emitter = MagicMock()

        class MockFetcher:
            def __init__(self, **kwargs):
                pass

            def execute(self):
                pass

        monkeypatch.setattr(MistHelper, "APIDataFetcher", MockFetcher)
        monkeypatch.setattr(MistHelper, "PROGRESS_EMITTER", mock_emitter)

        MistHelper.OrgInventoryExporter.inventory()

        mock_emitter.emit_progress_start.assert_called_once_with("12", "inventory", 1)
        mock_emitter.emit_progress_complete.assert_called_once()
        call_args = mock_emitter.emit_progress_complete.call_args
        assert call_args[0][0].menu_option == "12"  # Issue #470: identity now bundled in ProgressContext.
        assert call_args[0][0].operation_name == "inventory"  # ProgressContext.operation_name.
        assert call_args[0][0].total == 1  # ProgressContext.total.
        assert call_args[0][1] == 1  # processed count (now second positional arg).
        assert call_args[0][2] is False  # was_stopped flag (now third positional arg).
        assert isinstance(call_args[0][3], float)  # duration seconds (now fourth positional arg).

    def test_handles_no_emitter_gracefully(self, monkeypatch):
        """US4 Scenario 3: No exception when PROGRESS_EMITTER is None."""

        class MockFetcher:
            def __init__(self, **kwargs):
                pass

            def execute(self):
                pass

        monkeypatch.setattr(MistHelper, "APIDataFetcher", MockFetcher)
        monkeypatch.setattr(MistHelper, "PROGRESS_EMITTER", None)

        MistHelper.OrgInventoryExporter.inventory()
