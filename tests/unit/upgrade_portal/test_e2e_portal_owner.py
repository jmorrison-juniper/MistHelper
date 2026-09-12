"""Test the portal ownership record that issue #2260 asked for.

A browser run that ends on a timeout never reaches its teardown, so the portal
outlives the run and holds the port. Every later run on that port then reported
a stray listener, and an operator had to find the process by hand.

The suite now records the portal it starts. A later run reads that record, stops
the process it names, and reclaims the port.

Warning: the reclaim never stops a listener that this suite did not record. A
portal container on the same port is a state of the workstation, and the suite
must name it rather than end it.
"""

from __future__ import annotations

import importlib.util
import logging
import os
import sys
from pathlib import Path
from types import ModuleType

import pytest

# The conftest that holds the reclaim. A conftest is not importable by name, so
# these tests load it by path, the same way the conftest loads its own settings.
_CONFTEST_PATH = Path(__file__).resolve().parents[3] / "tests" / "e2e" / "upgrade_portal" / "conftest.py"


@pytest.fixture(name="portal_conftest")
def fixture_portal_conftest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Load the browser conftest and point its record at a temporary file."""
    logging.info("Loading the browser conftest from %s", _CONFTEST_PATH)  # Report before the load.
    name = "upgrade_portal_e2e_conftest_owner"  # One fixed name, so a second load reuses the entry.
    spec = importlib.util.spec_from_file_location(name, _CONFTEST_PATH)
    assert spec is not None and spec.loader is not None, "the browser conftest must be loadable"
    module = importlib.util.module_from_spec(spec)
    # WHY: the conftest defines a slotted dataclass, and `dataclasses` reads the module
    # back out of `sys.modules` while it builds the class.
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    monkeypatch.setattr(module, "SERVER_OWNER_PATH", tmp_path / "portal.pid")  # No shared file.
    monkeypatch.setattr(module, "RECLAIM_TRIES", 2)  # Two tries keep every test quick.
    monkeypatch.setattr(module, "RECLAIM_PAUSE_SECONDS", 0.0)  # No test waits on a real clock.
    logging.debug("Loaded the browser conftest")  # Record the load after the work.
    return module


class TestTheOwnerRecord:
    """The suite records the portal it starts, and it forgets it on a clean stop."""

    def test_a_started_portal_writes_its_identifier(self, portal_conftest: ModuleType) -> None:
        """A portal that answered MUST write its process identifier."""
        logging.info("Checking that a started portal writes its identifier")  # Report the plan.

        portal_conftest._record_owner(_StandInProcess(4321))

        assert portal_conftest.SERVER_OWNER_PATH.read_text(encoding="utf-8") == "4321"

    def test_a_stopped_portal_forgets_its_identifier(self, portal_conftest: ModuleType) -> None:
        """A clean stop MUST remove the record, because the portal owns nothing now."""
        logging.info("Checking that a stopped portal forgets its identifier")  # Report the plan.
        portal_conftest._record_owner(_StandInProcess(4321))

        portal_conftest._forget_owner()

        assert not portal_conftest.SERVER_OWNER_PATH.exists(), "a stopped portal must leave no record"

    def test_forgetting_twice_never_raises(self, portal_conftest: ModuleType) -> None:
        """A second forget MUST do nothing, because a teardown can run twice."""
        logging.info("Checking the second forget")  # Report the plan before the work.

        portal_conftest._forget_owner()
        portal_conftest._forget_owner()

    def test_an_unwritable_record_never_stops_a_run(self, portal_conftest: ModuleType) -> None:
        """A record the suite cannot write MUST NOT raise, because the run still works.

        Why:
            The record is a convenience for the next run. A workstation with an
            unwritable temporary folder must still run the browser tests.
        """
        logging.info("Checking the unwritable record path")  # Report the plan.
        portal_conftest.SERVER_OWNER_PATH = portal_conftest.SERVER_OWNER_PATH / "no-such-folder" / "portal.pid"

        portal_conftest._record_owner(_StandInProcess(4321))  # WHY: this must not raise.


class TestReadingTheRecord:
    """A damaged record or an absent record must answer nothing, not raise."""

    def test_a_written_record_reads_back(self, portal_conftest: ModuleType) -> None:
        """The reader MUST answer the identifier that the writer wrote."""
        logging.info("Checking the read of a written record")  # Report the plan.
        portal_conftest._record_owner(_StandInProcess(9876))

        assert portal_conftest._recorded_owner() == 9876

    def test_no_record_answers_nothing(self, portal_conftest: ModuleType) -> None:
        """A first run on a workstation MUST read no owner."""
        logging.info("Checking the read with no record present")  # Report the plan.

        assert portal_conftest._recorded_owner() is None

    @pytest.mark.parametrize("text", ["", "   ", "not-a-number", "12.5", "-1x"])
    def test_a_damaged_record_answers_nothing(self, portal_conftest: ModuleType, text: str) -> None:
        """A record that names no process MUST answer nothing, not raise."""
        logging.info("Checking the read of the damaged record %r", text)  # Report the plan.
        portal_conftest.SERVER_OWNER_PATH.write_text(text, encoding="utf-8")

        # WHY: a damaged record must never become a process identifier that the suite stops.
        assert portal_conftest._recorded_owner() is None


class TestReclaimingThePort:
    """The reclaim stops a recorded portal, and it never stops anything else."""

    def test_no_record_refuses_the_reclaim(self, portal_conftest: ModuleType) -> None:
        """A listener that this suite never recorded MUST NOT be stopped.

        Why:
            A portal container on the same port is a state of the workstation.
            The suite must name it and stop, never end it.
        """
        logging.info("Checking that an unrecorded listener survives")  # Report the plan.
        stopped: list[int] = []  # Records every stop the reclaim attempted.
        portal_conftest.os = _StandInOs(stopped)  # type: ignore[attr-defined]

        assert portal_conftest._stop_stale_owner() is False, "an unrecorded listener must not be stopped"
        assert stopped == [], "the reclaim must stop no process it did not record"

    def test_a_recorded_portal_is_stopped_and_the_port_frees(
        self, portal_conftest: ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A recorded portal MUST be stopped, and the reclaim MUST report success."""
        logging.info("Checking the reclaim of a recorded portal")  # Report the plan.
        stopped: list[int] = []
        monkeypatch.setattr(portal_conftest, "os", _StandInOs(stopped))
        monkeypatch.setattr(portal_conftest, "_probe_port", lambda port: False)  # The port is free.
        portal_conftest._record_owner(_StandInProcess(3333))

        assert portal_conftest._stop_stale_owner() is True, "the reclaim must report the free port"
        assert stopped == [3333], "the reclaim must stop the recorded process"
        assert not portal_conftest.SERVER_OWNER_PATH.exists(), "a reclaimed port must leave no record"

    def test_a_port_that_never_frees_reports_a_failure(
        self, portal_conftest: ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A port that stays held MUST report a failure, so the caller names it."""
        logging.info("Checking the reclaim of a port that stays held")  # Report the plan.
        monkeypatch.setattr(portal_conftest, "os", _StandInOs([]))
        monkeypatch.setattr(portal_conftest, "_probe_port", lambda port: True)  # The port stays held.
        portal_conftest._record_owner(_StandInProcess(3333))

        assert portal_conftest._stop_stale_owner() is False, "a held port must report a failure"

    def test_an_absent_process_still_frees_the_port(
        self, portal_conftest: ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A record that names a dead process MUST NOT raise.

        Why:
            The process can end between the read and the stop. That is the state
            the reclaim wants, so it must not become a failure.
        """
        logging.info("Checking the reclaim against an absent process")  # Report the plan.
        monkeypatch.setattr(portal_conftest, "os", _StandInOs([], raises=True))
        monkeypatch.setattr(portal_conftest, "_probe_port", lambda port: False)
        portal_conftest._record_owner(_StandInProcess(3333))

        assert portal_conftest._stop_stale_owner() is True, "an absent process leaves a free port"


class TestTheMessageNamesTheSuite:
    """The refusal must tell the reader where the record lives."""

    def test_the_message_names_the_record(self, portal_conftest: ModuleType) -> None:
        """The stray listener message MUST name the record file.

        Why:
            The first report of issue #2260 sent the reader to look for a portal
            container. The record tells the reader which case they are in.
        """
        logging.info("Checking the stray listener message")  # Report the plan.

        assert ".pid" in portal_conftest.STRAY_LISTENER_MESSAGE, "the message must name the record file"
        assert "container" in portal_conftest.STRAY_LISTENER_MESSAGE, "the message must name the common cause"


class _StandInProcess:
    """One started process, with the identifier that the record reads."""

    def __init__(self, pid: int) -> None:
        """Store the process identifier that the record writes."""
        self.pid = pid  # The only attribute that the record reads.


class _StandInOs:
    """A stand-in for the `os` module that records every stop request."""

    def __init__(self, stopped: list[int], raises: bool = False) -> None:
        """Store the log and whether the stop reports an absent process."""
        self._stopped = stopped  # The ordered log of every stop the reclaim attempted.
        self._raises = raises  # True when the stop must report an absent process.

    def kill(self, pid: int, number: int) -> None:
        """Record one stop request, or report that the process is gone."""
        del number  # The signal number never changes the outcome of these tests.
        if self._raises:  # The process ended between the read and this call.
            raise ProcessLookupError(f"no process {pid}")
        self._stopped.append(pid)  # Keep the identifier for the assertion.

    def __getattr__(self, name: str) -> object:
        """Answer every other attribute from the real module."""
        return getattr(os, name)  # The conftest reads `os.environ` as well.
