"""Tests for SiteWebhookDeliveriesExporter, the menu 199 delivery-audit export.

Why:
    The module holds three risk areas that had no test. The webhook listing
    reaches the Mist API. The selection guard indexes a list from operator
    input. The export path wraps the search call in a broad error handler that
    keeps the menu loop alive. This module covers all three. Every Mist call is
    mocked, so no test reaches the live cloud.
"""

from __future__ import annotations

import importlib
from typing import Any
from unittest.mock import MagicMock, patch

import mistapi
import pytest

from src.export.site_webhook_deliveries_exporter import SiteWebhookDeliveriesExporter
from src.utils.input_utils import InputUtils

# WHY: two rows exercise both the in-range and the out-of-range selection guards.
_WEBHOOKS: list[dict[str, Any]] = [
    {"id": "wh-1", "name": "Alarms"},  # WHY: a normal row with both fields present.
    {"id": "wh-2", "name": "Audit"},  # WHY: a second row makes index two valid.
]


@pytest.fixture
def fake_mh() -> Any:
    """Return a MistHelper stand-in with the collaborators the exporter reads.

    Why:
        The exporter resolves ``apisession``, ``SiteDeviceExporter``, and
        ``DataExporter`` through a lazy ``importlib.import_module`` call. One
        stub covers all three and records what the exporter wrote.
    """
    module = MagicMock()  # WHY: a MagicMock auto-creates each attribute the exporter reads.
    module.apisession = MagicMock()  # WHY: the SDK calls receive this as their first argument.
    return module  # WHY: each test patches import_module to return this object.


class TestResolveWebhookChoice:
    """Cover the selection guard, which converts operator input into a list index."""

    def test_a_non_numeric_answer_is_rejected(self) -> None:
        """A word must not reach ``int()``, which would raise into the menu loop."""
        # WHY: the guard runs before any conversion, so no exception escapes.
        assert SiteWebhookDeliveriesExporter._resolve_webhook_choice("first", _WEBHOOKS) is None

    def test_an_empty_answer_is_rejected(self) -> None:
        """An immediate Enter press must abort rather than select row one."""
        # WHY: an empty string is not a digit, so the first guard catches it.
        assert SiteWebhookDeliveriesExporter._resolve_webhook_choice("", _WEBHOOKS) is None

    def test_zero_is_rejected(self) -> None:
        """Index zero is the lower boundary and must not wrap to the last row."""
        # WHY: Python would map index -1 to the last row, so the guard must reject zero.
        assert SiteWebhookDeliveriesExporter._resolve_webhook_choice("0", _WEBHOOKS) is None

    def test_one_past_the_end_is_rejected(self) -> None:
        """The upper boundary must abort rather than raise IndexError."""
        # WHY: the list holds two rows, so three is the first invalid selection.
        assert SiteWebhookDeliveriesExporter._resolve_webhook_choice("3", _WEBHOOKS) is None

    def test_the_first_row_resolves(self) -> None:
        """The lowest valid selection maps to the zero-based first row."""
        # WHY: the operator sees one-based numbering, so one must select index zero.
        assert SiteWebhookDeliveriesExporter._resolve_webhook_choice("1", _WEBHOOKS) == ("wh-1", "Alarms")

    def test_the_last_row_resolves(self) -> None:
        """The highest valid selection maps to the final row."""
        # WHY: the upper boundary must be inclusive, so two selects the second row.
        assert SiteWebhookDeliveriesExporter._resolve_webhook_choice("2", _WEBHOOKS) == ("wh-2", "Audit")

    def test_a_webhook_without_a_name_falls_back_to_its_identifier(self) -> None:
        """A nameless webhook must still yield a label for the output filename."""
        nameless = [{"id": "wh-3"}]  # WHY: the Mist API omits the name when it is unset.
        # WHY: the identifier is the only stable label left, so the exporter reuses it.
        assert SiteWebhookDeliveriesExporter._resolve_webhook_choice("1", nameless) == ("wh-3", "wh-3")

    def test_a_webhook_without_an_identifier_yields_an_empty_string(self) -> None:
        """A malformed row must not raise, because the caller logs and continues."""
        malformed = [{"name": "Broken"}]  # WHY: mimic a row that lost its identifier.
        # WHY: the exporter returns an empty identifier so the API call fails visibly.
        assert SiteWebhookDeliveriesExporter._resolve_webhook_choice("1", malformed) == ("", "Broken")


class TestSelectWebhookId:
    """Cover the listing call and the empty-site guard."""

    def test_a_site_without_webhooks_aborts(self, fake_mh: Any) -> None:
        """A site with no webhooks has nothing to search, so the prompt must not run."""
        with (
            patch.object(mistapi, "get_all", return_value=[]),
            patch.object(mistapi.api.v1.sites.webhooks, "listSiteWebhooks", return_value={"result": []}),
            patch.object(importlib, "import_module", return_value=fake_mh),
            patch.object(InputUtils, "safe_input") as prompt_spy,
        ):
            assert SiteWebhookDeliveriesExporter._select_webhook_id("site-1") is None
        prompt_spy.assert_not_called()  # WHY: an empty list gives the operator nothing to pick.

    def test_the_listing_call_receives_the_session_and_site(self, fake_mh: Any) -> None:
        """The listing call must target the resolved site, not a cached one."""
        with (
            patch.object(mistapi, "get_all", return_value=_WEBHOOKS),
            patch.object(mistapi.api.v1.sites.webhooks, "listSiteWebhooks", return_value={"result": []}) as list_spy,
            patch.object(importlib, "import_module", return_value=fake_mh),
            patch.object(InputUtils, "safe_input", return_value="1"),
        ):
            SiteWebhookDeliveriesExporter._select_webhook_id("site-1")  # WHY: drive the listing call.
        # WHY: the contract is the session first and the site identifier second.
        list_spy.assert_called_once_with(fake_mh.apisession, "site-1")

    def test_a_valid_pick_returns_the_identifier_and_name(self, fake_mh: Any) -> None:
        """A valid answer must flow through the guard to the caller unchanged."""
        with (
            patch.object(mistapi, "get_all", return_value=_WEBHOOKS),
            patch.object(mistapi.api.v1.sites.webhooks, "listSiteWebhooks", return_value={"result": []}),
            patch.object(importlib, "import_module", return_value=fake_mh),
            patch.object(InputUtils, "safe_input", return_value="2"),
        ):
            result = SiteWebhookDeliveriesExporter._select_webhook_id("site-1")
        assert result == ("wh-2", "Audit")  # WHY: the second row must reach the search call.


class TestPersistSiteWebhookDeliveries:
    """Cover the persistence path, including the empty-response branch."""

    def test_an_empty_response_writes_nothing(self, fake_mh: Any) -> None:
        """A webhook that never fired is legitimate and must not create a file."""
        with patch.object(importlib, "import_module", return_value=fake_mh):
            SiteWebhookDeliveriesExporter._persist_site_webhook_deliveries([], "Site", "Hook")
        # WHY: a scheduled run must stay quiet rather than emit an empty file.
        fake_mh.DataExporter.write_with_format_selection.assert_not_called()

    def test_spaces_in_the_names_do_not_reach_the_filename(self, fake_mh: Any) -> None:
        """A site or webhook name with a space must yield a portable filename."""
        with patch.object(importlib, "import_module", return_value=fake_mh):
            SiteWebhookDeliveriesExporter._persist_site_webhook_deliveries(
                [{"status": 200}], "Head Office", "Alarm Hook"
            )
        args, _ = fake_mh.DataExporter.write_with_format_selection.call_args  # WHY: read the filename.
        # WHY: the exporter replaces each space so the path stays portable across shells.
        assert args[1] == "SiteWebhookDeliveries_Head_Office_Alarm_Hook.csv"

    def test_the_operation_name_reaches_the_writer(self, fake_mh: Any) -> None:
        """The operationId selects the primary key strategy, so it must reach the writer."""
        with patch.object(importlib, "import_module", return_value=fake_mh):
            SiteWebhookDeliveriesExporter._persist_site_webhook_deliveries([{"status": 200}], "Site", "Hook")
        _, kwargs = fake_mh.DataExporter.write_with_format_selection.call_args  # WHY: read the keyword.
        # WHY: a wrong name would pick the wrong primary key strategy and duplicate rows.
        assert kwargs["api_function_name"] == "searchSiteWebhooksDeliveries"


class TestDeliveries:
    """Cover the menu entry point, its guards, and its error handler."""

    def test_an_unresolved_site_aborts_before_the_webhook_prompt(self, fake_mh: Any) -> None:
        """A declined site must abort before the exporter lists any webhook."""
        fake_mh.SiteDeviceExporter._resolve_site_for_stats.return_value = None  # WHY: declined site.
        with (
            patch.object(importlib, "import_module", return_value=fake_mh),
            patch.object(SiteWebhookDeliveriesExporter, "_select_webhook_id") as select_spy,
        ):
            SiteWebhookDeliveriesExporter.deliveries()  # WHY: drive the first guard branch.
        select_spy.assert_not_called()  # WHY: the listing call needs a site identifier.

    def test_a_declined_webhook_aborts_before_the_search_call(self, fake_mh: Any) -> None:
        """A declined webhook must abort before the delivery search runs."""
        fake_mh.SiteDeviceExporter._resolve_site_for_stats.return_value = ("site-1", "Branch")
        with (
            patch.object(importlib, "import_module", return_value=fake_mh),
            patch.object(SiteWebhookDeliveriesExporter, "_select_webhook_id", return_value=None),
            patch.object(mistapi.api.v1.sites.webhooks, "searchSiteWebhooksDeliveries") as search_spy,
        ):
            SiteWebhookDeliveriesExporter.deliveries()  # WHY: drive the second guard branch.
        search_spy.assert_not_called()  # WHY: the search call needs a webhook identifier.

    def test_the_search_call_receives_the_site_and_the_webhook(self, fake_mh: Any) -> None:
        """The search must target the resolved site and the chosen webhook."""
        fake_mh.SiteDeviceExporter._resolve_site_for_stats.return_value = ("site-1", "Branch")
        with (
            patch.object(mistapi, "get_all", return_value=[{"status": 200}]),
            patch.object(
                mistapi.api.v1.sites.webhooks,
                "searchSiteWebhooksDeliveries",
                return_value={"result": []},
            ) as search_spy,
            patch.object(importlib, "import_module", return_value=fake_mh),
            patch.object(SiteWebhookDeliveriesExporter, "_select_webhook_id", return_value=("wh-2", "Audit")),
            patch.object(SiteWebhookDeliveriesExporter, "_persist_site_webhook_deliveries"),
        ):
            SiteWebhookDeliveriesExporter.deliveries()  # WHY: drive the happy path.
        # WHY: the contract is the session, then the site, then the webhook.
        search_spy.assert_called_once_with(fake_mh.apisession, "site-1", "wh-2")

    def test_the_site_and_webhook_names_reach_the_persist_call(self, fake_mh: Any) -> None:
        """Both friendly names shape the filename, so both must survive the handoff."""
        fake_mh.SiteDeviceExporter._resolve_site_for_stats.return_value = ("site-1", "Branch")
        rows = [{"status": 200}]  # WHY: one row is enough to reach the persist call.
        with (
            patch.object(mistapi, "get_all", return_value=rows),
            patch.object(
                mistapi.api.v1.sites.webhooks,
                "searchSiteWebhooksDeliveries",
                return_value={"result": []},
            ),
            patch.object(importlib, "import_module", return_value=fake_mh),
            patch.object(SiteWebhookDeliveriesExporter, "_select_webhook_id", return_value=("wh-2", "Audit")),
            patch.object(SiteWebhookDeliveriesExporter, "_persist_site_webhook_deliveries") as persist_spy,
        ):
            SiteWebhookDeliveriesExporter.deliveries()  # WHY: drive the happy path.
        # WHY: a lost name would produce a filename that the operator cannot attribute.
        persist_spy.assert_called_once_with(rows, "Branch", "Audit")

    def test_a_search_error_is_logged_and_not_raised(self, fake_mh: Any, caplog: Any) -> None:
        """A network or SDK failure must be logged, not raised into the menu loop."""
        caplog.set_level("ERROR")  # WHY: the handler reports the failure at ERROR level.
        fake_mh.SiteDeviceExporter._resolve_site_for_stats.return_value = ("site-1", "Branch")
        with (
            patch.object(
                mistapi.api.v1.sites.webhooks,
                "searchSiteWebhooksDeliveries",
                side_effect=RuntimeError("gateway timeout"),
            ),
            patch.object(importlib, "import_module", return_value=fake_mh),
            patch.object(SiteWebhookDeliveriesExporter, "_select_webhook_id", return_value=("wh-2", "Audit")),
        ):
            SiteWebhookDeliveriesExporter.deliveries()  # WHY: must not raise.
        assert "gateway timeout" in caplog.text  # WHY: the operator needs the cause to triage.

    def test_a_paging_error_is_logged_and_not_raised(self, fake_mh: Any, caplog: Any) -> None:
        """A failure inside ``get_all`` must reach the same handler as a call failure."""
        caplog.set_level("ERROR")  # WHY: the handler reports the failure at ERROR level.
        fake_mh.SiteDeviceExporter._resolve_site_for_stats.return_value = ("site-1", "Branch")
        with (
            # WHY: paging is a second network hop, so it fails independently of the call.
            patch.object(mistapi, "get_all", side_effect=ValueError("truncated page")),
            patch.object(
                mistapi.api.v1.sites.webhooks,
                "searchSiteWebhooksDeliveries",
                return_value={"result": []},
            ),
            patch.object(importlib, "import_module", return_value=fake_mh),
            patch.object(SiteWebhookDeliveriesExporter, "_select_webhook_id", return_value=("wh-2", "Audit")),
        ):
            SiteWebhookDeliveriesExporter.deliveries()  # WHY: must not raise.
        assert "truncated page" in caplog.text  # WHY: the paging failure must stay attributable.
