"""Unit tests that make the three repaired route handlers name the cause of a failure.

Why:
    Issue #2926 part C covers three broad exception handlers in
    `app/routes/upgrade.py`. Each one caught `Exception`, bound no name, and
    wrote one warning line that named the site or the run and nothing else. The
    operator therefore read "did not answer" and could not tell a refused token
    from a timeout from a key fault inside the seam. The run record and the page
    looked the same in every case, so the support path started with a guess.

    Each test here drives one failure into one guarded block and then reads the
    log that the handler wrote. A test passes only when the rendered log holds
    the class and the message of the exception that arrived. The return value of
    each handler stays under test as well, because the repair must change the
    diagnostic alone and never the control flow that the page depends on.

    No test reaches Flask, the cloud, or a store. Each one replaces the seam that
    the handler already reads, so the decision of the handler is the only
    behavior under measurement.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

import logging  # The tests read the records that the route logger emitted.
from typing import Any  # A run record and an options answer are both free-form.

import pytest  # The test framework, which supplies `caplog` and `monkeypatch`.

from src.interfaces.portals.upgrade_portal.app.routes import upgrade  # The module under test.
from src.interfaces.portals.upgrade_portal.runtime.runs import RunState  # The state model of one run.

# WHY: The logger name of the three handlers, so `caplog` reads their records alone.
ROUTE_LOGGER = "src.interfaces.portals.upgrade_portal.app.routes.upgrade"

# WHY: The identifier shape that the cloud uses, with an obviously fake body.
ORG_ID = "00000000-0000-0000-0000-0000000000aa"
SITE_ID = "00000000-0000-0000-0000-0000000000bb"
RUN_ID = "00000000-0000-0000-0000-0000000000cc"

# WHY: One rare word for each guarded block, so a match in the log proves the cause reached it.
INVENTORY_SENTINEL = "the inventory seam refused with a sentinel fault"
LOCK_SENTINEL = "the session lock field held a sentinel fault"

# WHY: A state name that no member of the run model carries, so `read_state` raises for real.
UNKNOWN_STATE = "a-state-that-no-model-member-names"


class InventorySeamFault(RuntimeError):
    """The class that the options builder raises in these tests.

    Why:
        A named class proves that the log holds the class of the exception and
        not only its message. A test that reads the message alone would pass
        against a handler that logged `str(error)` with no traceback.
    """


class SessionLockFault(RuntimeError):
    """The class that the session lock read raises in these tests."""


def read_exception_log(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    """Return the route records that carry a formatted exception.

    Why:
        A handler that binds the exception and reports it sets `exc_info` on the
        record. A handler that writes a bare warning does not. This reader is
        therefore the one measurement that separates a repaired handler from a
        blind one.

    Args:
        caplog: The capture fixture of the running test.

    Returns:
        Each record of the route logger that holds exception information.
    """
    records = [record for record in caplog.records if record.name == ROUTE_LOGGER]  # The route records alone.
    return [record for record in records if record.exc_info is not None]  # Only the ones that carry a cause.


def fake_run_record() -> dict[str, Any]:
    """Return the smallest run record that the three handlers read.

    Returns:
        A record that names one organization, one site, and one run.
    """
    return {"run_id": RUN_ID, "site_id": SITE_ID, "org_id": ORG_ID}  # The three names the handlers read.


class TestOptionsViewReportsTheInventoryFault:
    """The options view must name the fault that ended the site inventory read."""

    @pytest.fixture
    def failing_builder(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Point the options view at a builder that raises and at no injected map.

        Why:
            `options_view` keeps the earlier answer when the configuration holds
            a ready version map or when the browser holds no session. The test
            must defeat both of those exits, so the fresh read runs and the
            guarded call raises.

        Args:
            monkeypatch: The patch fixture of the running test.
        """

        def refuse(*_args: Any, **_kwargs: Any) -> Any:
            """Raise the sentinel fault in place of the cloud inventory read."""
            raise InventorySeamFault(INVENTORY_SENTINEL)  # The cause that the handler must name.

        monkeypatch.setattr(upgrade, "injected_object", lambda _key: None)  # No ready map and no injected builder.
        monkeypatch.setattr(upgrade, "cloud_session", lambda: object())  # A signed-in browser, so the read runs.
        monkeypatch.setattr(upgrade, "module_attribute", lambda _names: refuse)  # The module answers the raiser.

    def test_the_log_names_the_class_and_the_message_of_the_fault(
        self, failing_builder: None, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A failed inventory read must write the class and the message of the cause."""
        with caplog.at_level(logging.DEBUG, logger=ROUTE_LOGGER):  # Read every record of the route logger.
            upgrade.options_view(fake_run_record())  # The guarded call raises inside this function.
        assert read_exception_log(caplog), "the options view wrote no record that carries the cause"
        assert InventorySeamFault.__name__ in caplog.text  # The class of the fault reaches the operator.
        assert INVENTORY_SENTINEL in caplog.text  # The message of the fault reaches the operator.

    def test_the_failed_read_still_keeps_the_earlier_answer(self, failing_builder: None) -> None:
        """The repair must change the log alone and never the answer that the page draws."""
        record = fake_run_record()  # A record with no stored row, which is the shape of a new run.
        answer = upgrade.options_view(record)  # The handler swallows the fault and answers the kept view.
        assert answer == upgrade.kept_options_view(record, [], {})  # The same five fields as before the repair.


class TestSessionLockBindReportsTheStoreFault:
    """The session lock bind must name the fault that ended the session read."""

    @pytest.fixture
    def failing_lock_read(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Point the lock bind at a session read that raises.

        Args:
            monkeypatch: The patch fixture of the running test.
        """

        def refuse(_site_id: str) -> Any:
            """Raise the sentinel fault in place of the session lock read."""
            raise SessionLockFault(LOCK_SENTINEL)  # The cause that the handler must name.

        monkeypatch.setattr(upgrade, "session_lock_record", refuse)  # The guarded read now raises.

    def test_the_log_names_the_class_and_the_message_of_the_fault(
        self, failing_lock_read: None, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A damaged session field must write the class and the message of the cause."""
        with caplog.at_level(logging.DEBUG, logger=ROUTE_LOGGER):  # Read every record of the route logger.
            upgrade.bind_session_lock_to_run(fake_run_record())  # The guarded read raises inside this function.
        assert read_exception_log(caplog), "the lock bind wrote no record that carries the cause"
        assert SessionLockFault.__name__ in caplog.text  # The class of the fault reaches the operator.
        assert LOCK_SENTINEL in caplog.text  # The message of the fault reaches the operator.

    def test_the_failed_bind_still_ends_the_start_with_no_raise(self, failing_lock_read: None) -> None:
        """The repair must keep the rule that a lock fault never ends a confirmed run."""
        assert upgrade.bind_session_lock_to_run(fake_run_record()) is None  # The start continues as before.


class TestRunNotStartedReportsTheStateFault:
    """The reschedule rule must name the fault that an unmodeled state raised."""

    def test_the_log_names_the_class_and_the_refused_state(self, caplog: pytest.LogCaptureFixture) -> None:
        """An unmodeled state must write the class of the fault and the refused name."""
        record = fake_run_record() | {"state": UNKNOWN_STATE}  # `read_state` refuses this name for real.
        with caplog.at_level(logging.DEBUG, logger=ROUTE_LOGGER):  # Read every record of the route logger.
            upgrade.run_not_started(record)  # The guarded read raises inside this function.
        assert read_exception_log(caplog), "the reschedule rule wrote no record that carries the cause"
        assert "RunTransitionError" in caplog.text  # The class of the fault reaches the operator.
        assert UNKNOWN_STATE in caplog.text  # The refused state name reaches the operator.

    def test_an_unmodeled_state_still_refuses_the_reschedule(self) -> None:
        """The repair must keep the safe answer, which refuses every later control."""
        record = fake_run_record() | {"state": UNKNOWN_STATE}  # The same damaged record.
        assert upgrade.run_not_started(record) is False  # A run of unknown state stays unreschedulable.

    def test_a_modeled_state_reaches_no_handler_at_all(self) -> None:
        """A healthy record must take the normal path, so the guard measures a real fault only."""
        record = fake_run_record() | {"state": RunState.CREATED.value}  # The first state of the chain.
        assert upgrade.run_not_started(record) is True  # A new run has sent nothing to the cloud.
