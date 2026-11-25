"""Tests for the ledger binding and the SDK error mute."""

from __future__ import annotations

import logging  # Capture the SDK records the way a console handler sees them.
from types import SimpleNamespace  # Build small session doubles.
from unittest.mock import Mock  # A Redis client double for the real ledger.

import pytest  # Capture the console output.
import requests  # Build a real HTTP session for the adapter lookup.
from mistapi.__api_response import console as sdk_console  # The SDK console that prints error lines.
from requests.adapters import HTTPAdapter  # The default adapter has no ledger.

from src.interfaces.wan_performance.collection.request_admission import AdmittedAdapter, RequestLedger  # Real classes.
from src.operations.exporting.ex_hardware_inventory.scope.session import AdmissionBinding, SdkErrorMute  # Units.

ORG_ID = "11111111-1111-4111-8111-111111111111"  # An invented organization.


def admitted_session(org_id: str | None = None) -> tuple[SimpleNamespace, RequestLedger]:
    """Build a session double whose HTTP session mounts the real admission adapter."""
    ledger = RequestLedger(Mock(), org_id)  # The real ledger with a fake Redis client.
    inner = requests.Session()  # A real session, so the real adapter lookup runs.
    inner.mount("https://", AdmittedAdapter(ledger, 30))  # The CLI mounts the adapter in the same way.
    return SimpleNamespace(_session=inner), ledger  # The SDK keeps its HTTP session in this attribute.


class TestAdmissionBinding:
    """The binding sets the ledger organization inside the block and restores it afterward."""

    def test_sets_and_restores_the_ledger_organization(self) -> None:
        """The ledger holds the run organization only inside the block."""
        session, ledger = admitted_session()  # The ledger starts with no organization.
        with AdmissionBinding(session, ORG_ID):  # Bind the run organization.
            assert ledger.org_id == ORG_ID  # A site request now has an organization.
        assert ledger.org_id is None  # The earlier value is back.

    def test_restores_an_earlier_organization(self) -> None:
        """An organization that was set before the block returns after it."""
        session, ledger = admitted_session("22222222-2222-4222-8222-222222222222")  # An earlier value.
        with AdmissionBinding(session, ORG_ID):  # Bind a different organization.
            assert ledger.org_id == ORG_ID  # The run organization wins inside the block.
        assert ledger.org_id == "22222222-2222-4222-8222-222222222222"  # The earlier value returns.

    def test_restores_when_the_block_raises(self) -> None:
        """An error inside the block still restores the ledger."""
        session, ledger = admitted_session()  # The ledger starts with no organization.
        with pytest.raises(RuntimeError):  # The block fails on purpose.
            with AdmissionBinding(session, ORG_ID):  # Bind the run organization.
                raise RuntimeError("boom")  # Fail inside the block.
        assert ledger.org_id is None  # The restore ran on the error path.

    def test_the_ledger_rejects_a_site_request_without_the_binding_and_accepts_it_with_the_binding(self) -> None:
        """The binding changes the real ledger decision for a site request."""
        session, ledger = admitted_session()  # A real ledger with no organization.
        request = requests.Request("GET", "https://api.mist.com/api/v1/sites/s1/devices").prepare()  # A site call.
        request.headers["Authorization"] = "Token synthetic"  # The ledger refuses an anonymous request.
        with pytest.raises(ConnectionError):  # No organization, so the ledger fails closed.
            ledger.admit(request)  # The request has no tenant context.
        with AdmissionBinding(session, ORG_ID):  # Bind the run organization.
            ledger.client.eval.return_value = 1  # The fake Redis grants the reservation.
            ledger.admit(request)  # The same request now passes.
        assert ledger.client.eval.call_count == 1  # Exactly one reservation reached the store.

    def test_does_nothing_when_the_session_has_no_ledger(self) -> None:
        """A session with the default adapter and a session without an HTTP session both pass."""
        plain = SimpleNamespace(_session=requests.Session())  # The default adapter has no ledger.
        assert isinstance(plain._session.get_adapter("https://api.mist.com/"), HTTPAdapter)  # The setup is right.
        with AdmissionBinding(plain, ORG_ID):  # No ledger to bind.
            pass  # The block runs unchanged.
        with AdmissionBinding(SimpleNamespace(), ORG_ID):  # A session with no HTTP session at all.
            pass  # The block runs unchanged.

    def test_ignores_an_adapter_table_that_raises(self) -> None:
        """A session whose adapter lookup raises counts as having no ledger."""

        class Broken:
            """An HTTP session double with no usable adapter table."""

            def get_adapter(self, url: str) -> object:
                """Raise the error that requests raises for an unknown scheme."""
                raise requests.exceptions.InvalidSchema(url)  # A ValueError subclass.

        with AdmissionBinding(SimpleNamespace(_session=Broken()), ORG_ID):  # The lookup fails.
            pass  # The block still runs.


class TestSdkErrorMute:
    """The mute hides SDK error lines only inside its block."""

    @staticmethod
    def capture() -> tuple[logging.Handler, list[logging.LogRecord]]:
        """Attach a handler to the SDK logger and return it with its record list."""
        records: list[logging.LogRecord] = []  # The records that a console handler would print.

        class Collector(logging.Handler):
            """Keep each record that reaches the handler."""

            def emit(self, record: logging.LogRecord) -> None:
                """Store one record."""
                records.append(record)  # Keep it for the assertions.

        handler = Collector()  # A fresh handler for each test.
        logging.getLogger("mistapi").addHandler(handler)  # The same logger that the SDK uses.
        return handler, records  # The caller removes the handler in a finally block.

    def test_drops_error_records_only_inside_the_block(self) -> None:
        """An error record is dropped inside the block, and a warning is kept."""
        handler, records = self.capture()  # Watch the SDK logger.
        sdk_logger = logging.getLogger("mistapi")  # The logger of the SDK.
        previous_level = sdk_logger.level  # The test sets a level and restores it.
        sdk_logger.setLevel(logging.DEBUG)  # Make sure the records pass the logger level.
        try:  # Always detach the handler.
            with SdkErrorMute():  # The mute is on.
                sdk_logger.error("hidden error")  # Dropped by the filter.
                sdk_logger.warning("kept warning")  # Below the error level.
            sdk_logger.error("visible error")  # The mute is off again.
        finally:  # Leave the shared logger as it was.
            sdk_logger.removeHandler(handler)  # Detach the test handler.
            sdk_logger.setLevel(previous_level)  # Restore the level.
        messages = [record.getMessage() for record in records]  # What the handler saw.
        assert "hidden error" not in messages  # The mute worked.
        assert "kept warning" in messages  # A warning is not an error text.
        assert "visible error" in messages  # The mute ended with the block.

    def test_turns_the_sdk_console_off_and_restores_its_level(self, capsys: pytest.CaptureFixture[str]) -> None:
        """The direct SDK print stops inside the block and returns after it."""
        level = sdk_console.level  # The level before the mute.
        with SdkErrorMute():  # The mute is on.
            assert sdk_console.level == 0  # Level 0 turns the print off.
            sdk_console.error("hidden console error")  # The SDK would print this line.
        assert sdk_console.level == level  # The level is back.
        inside = capsys.readouterr().out  # Everything printed so far.
        assert "hidden console error" not in inside  # Nothing was printed inside the block.
        sdk_console.error("visible console error")  # The mute is off again.
        assert "visible console error" in capsys.readouterr().out  # The SDK prints again.

    def test_restores_when_the_block_raises(self) -> None:
        """An error inside the block still removes the filter and restores the level."""
        level = sdk_console.level  # The level before the mute.
        filters_before = list(logging.getLogger("mistapi").filters)  # The filters before the mute.
        with pytest.raises(RuntimeError):  # The block fails on purpose.
            with SdkErrorMute():  # The mute is on.
                raise RuntimeError("boom")  # Fail inside the block.
        assert sdk_console.level == level  # The level is back.
        assert list(logging.getLogger("mistapi").filters) == filters_before  # The filter is gone.
