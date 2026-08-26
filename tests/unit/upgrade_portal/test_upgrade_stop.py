"""Unit tests for the stop control of one upgrade run.

Why:
    A stop is the most dangerous control in the portal. Two rules protect the
    operator. The portal never interrupts a device that writes firmware, and
    the portal never claims a stop that it cannot prove. These tests hold the
    three outcome lists and the plain message to both rules.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.firmware.upgrade_service import CancelOutcome, DeviceTarget, GatewayFamily, PlanRoute, UpgradePlan
from src.upgrade_portal.runtime.signals import ConfirmationRequiredError, StopOutcome
from src.upgrade_portal.upgrade import stop

RUN_ID = "run-" + "b" * 32
MAC_ONE = "5c5b350e0001"
MAC_TWO = "5c5b350e0002"
MAC_THREE = "5c5b350e0003"


class FakeRunStore:
    """Hold one run record in memory for the record test."""

    def __init__(self, record: dict[str, Any]) -> None:
        """Hold the record this store answers with.

        Args:
            record: The run record.
        """
        self.record = record
        self.writes = 0

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return the stored record.

        Args:
            run_id: The run key. This store holds one run only.

        Returns:
            A copy of the record.
        """
        return dict(self.record)

    def write_run(self, run: dict[str, Any]) -> bool:
        """Store one record.

        Args:
            run: The whole record.

        Returns:
            Always True.
        """
        self.record = dict(run)
        self.writes += 1
        return True


def make_target(mac: str) -> DeviceTarget:
    """Return one device target for a plan.

    Args:
        mac: The device MAC address.

    Returns:
        A switch target with a version before and a version after.
    """
    return DeviceTarget(
        mac=mac,
        name=f"sw-{mac[-4:]}",
        device_type="switch",
        model="EX4400-48P",
        version_before="23.4R2-S2.1",
        version_target="23.4R2-S3.9",
        site_id="site-1",
    )


def make_plan(macs: tuple[str, ...], scope: str = "site") -> UpgradePlan:
    """Return one upgrade plan that holds the named devices.

    Args:
        macs: The MAC address of each device of the plan.
        scope: The plan scope, `site` or `org`.

    Returns:
        The plan.
    """
    route = PlanRoute(scope=scope, endpoint="upgradeSiteDevices", scope_id="site-1")
    return UpgradePlan(route=route, targets=tuple(make_target(mac) for mac in macs), body={}, warnings=())


def make_stop_target(macs: tuple[str, ...], upgrade_id: str = "up-1") -> stop.StopTarget:
    """Return one stop target for the named devices.

    Args:
        macs: The MAC address of each device of the plan.
        upgrade_id: The cloud identifier of the upgrade.

    Returns:
        The stop target.
    """
    return stop.StopTarget(plan=make_plan(macs), upgrade_id=upgrade_id, family=GatewayFamily.JUNOS)


def result(
    cancelled: tuple[str, ...] = (),
    writing: tuple[str, ...] = (),
    blocked: tuple[str, ...] = (),
    status_known: bool = True,
) -> stop.TargetResult:
    """Return one plan result with the three groups filled.

    Args:
        cancelled: Devices the cloud stopped.
        writing: Devices that write firmware now.
        blocked: Devices with no cancel call.
        status_known: True when the portal read the device state first.

    Returns:
        The result of one plan.
    """
    outcome = CancelOutcome(cancelled, writing, blocked, "")
    return stop.TargetResult(outcome, status_known=status_known)


@pytest.fixture
def calls(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Replace the two cloud calls of the stop path.

    Why:
        A unit test must reach no network. The two names live in the module
        namespace, so a patch of the module reaches every call site.

    Args:
        monkeypatch: The pytest patch helper.

    Returns:
        The call log and the answers the doubles return.
    """
    log: dict[str, Any] = {
        "cancel": [],
        "status": [],
        "cancel_answer": CancelOutcome((MAC_ONE,), (), (), "cancelled"),
        "cancel_error": None,
        "status_error": None,
        # The seam answers the normalized status. The field `status_known` states
        # that the answer was an upgrade job and not a device statistics list.
        "status_answer": {"upgrade_id": "up-1", "reboot_in_progress": (), "targets": {}, "status_known": True},
    }

    def fake_status(session: Any, scope: str, identifier: str, upgrade_id: str, family: Any) -> Any:
        log["status"].append((scope, identifier, upgrade_id, family))
        if log["status_error"] is not None:
            raise log["status_error"]
        return log["status_answer"]

    def fake_cancel(session: Any, plan: Any, upgrade_id: str, last_status: Any = None) -> CancelOutcome:
        log["cancel"].append((upgrade_id, last_status))
        if log["cancel_error"] is not None:
            raise log["cancel_error"]
        answer = log["cancel_answer"]
        return answer(plan) if callable(answer) else answer

    monkeypatch.setattr(stop, "read_upgrade_status", fake_status)
    monkeypatch.setattr(stop, "cancel_upgrade", fake_cancel)
    return log


class TestConfirmation:
    """The stop control needs the exact typed word STOP."""

    def test_the_exact_word_passes(self) -> None:
        """The word STOP raises nothing."""
        assert stop.require_confirmation("STOP") is None

    @pytest.mark.parametrize("typed", ["stop", "Stop", "STOP ", " STOP", "", "STOPP", "yes"])
    def test_any_other_word_refuses(self, typed: str) -> None:
        """Every other text refuses the stop.

        Args:
            typed: The text the operator typed.
        """
        with pytest.raises(ConfirmationRequiredError):
            stop.require_confirmation(typed)

    def test_a_wrong_word_reaches_no_cancel_call(self, calls: dict[str, Any]) -> None:
        """A refused confirmation stops before the first cloud call.

        Args:
            calls: The call log of the two cloud doubles.
        """
        with pytest.raises(ConfirmationRequiredError):
            stop.stop_run(object(), [make_stop_target((MAC_ONE,))], "stop")
        assert calls["cancel"] == []

    def test_the_message_names_the_word(self) -> None:
        """The refusal names the exact text the operator must type."""
        with pytest.raises(ConfirmationRequiredError, match="STOP"):
            stop.require_confirmation("no")


class TestOutcomeLists:
    """The stop reports three device lists and never mixes them."""

    def test_a_clean_stop_lists_every_device_as_cancelled(self) -> None:
        """Every device the cloud stopped appears in the cancelled list."""
        outcome = stop.merge_results([result(cancelled=(MAC_ONE, MAC_TWO))])
        assert outcome.cancelled == (MAC_ONE, MAC_TWO)
        assert outcome.already_writing == ()
        assert outcome.no_cancel_available == ()

    def test_a_writing_device_never_reaches_the_cancelled_list(self) -> None:
        """A device in mid-write stays out of the cancelled list."""
        outcome = stop.merge_results([result(cancelled=(MAC_ONE,), writing=(MAC_TWO,))])
        assert outcome.cancelled == (MAC_ONE,)
        assert outcome.already_writing == (MAC_TWO,)

    def test_a_device_with_no_cancel_call_reaches_its_own_list(self) -> None:
        """A family with no cancel call fills the third list."""
        outcome = stop.merge_results([result(blocked=(MAC_THREE,))])
        assert outcome.no_cancel_available == (MAC_THREE,)
        assert outcome.cancelled == ()

    def test_two_plans_join_into_one_answer(self) -> None:
        """The operator reads one answer for the whole run."""
        first = result(cancelled=(MAC_ONE,))
        second = result(writing=(MAC_TWO,), blocked=(MAC_THREE,))
        outcome = stop.merge_results([first, second])
        assert outcome.cancelled == (MAC_ONE,)
        assert outcome.already_writing == (MAC_TWO,)
        assert outcome.no_cancel_available == (MAC_THREE,)

    def test_a_writing_device_wins_over_a_cancelled_claim(self) -> None:
        """One plan that claims a stop never overrides a mid-write report."""
        first = result(cancelled=(MAC_ONE,))
        second = result(writing=(MAC_ONE,))
        outcome = stop.merge_results([first, second])
        assert outcome.cancelled == ()
        assert outcome.already_writing == (MAC_ONE,)

    def test_the_lists_hold_each_device_once(self) -> None:
        """Two plans that name one device report that device once."""
        outcome = stop.merge_results([result(cancelled=(MAC_ONE,)), result(cancelled=(MAC_ONE,))])
        assert outcome.cancelled == (MAC_ONE,)

    def test_the_answer_carries_the_run_record_shape(self) -> None:
        """The outcome writes the four keys the run record holds."""
        outcome = stop.merge_results([result(cancelled=(MAC_ONE,))])
        assert set(outcome.to_record()) == {"cancelled", "already_writing", "no_cancel_available", "message"}


class TestMidFlashMessage:
    """The message states plainly that a device in mid-write finishes."""

    def test_one_writing_device_reads_in_plain_words(self) -> None:
        """The message names the never-interrupt rule and the one device."""
        message = stop.stop_message(stop.StopCounts(cancelled=2, already_writing=1))
        assert "never interrupts a write" in message
        assert "1 device that writes firmware now finishes the upgrade." in message

    def test_many_writing_devices_read_in_plain_words(self) -> None:
        """The message counts every device that finishes the upgrade."""
        message = stop.stop_message(stop.StopCounts(cancelled=0, already_writing=3))
        assert "3 devices that write firmware now finish the upgrade." in message

    def test_no_writing_device_leaves_the_rule_out(self) -> None:
        """A stop that caught every device says nothing about a write."""
        message = stop.stop_message(stop.StopCounts(cancelled=4))
        assert "writes firmware" not in message
        assert message == "The portal cancelled the upgrade for 4 devices."

    def test_a_stop_that_caught_nothing_says_so(self) -> None:
        """The message never hides an empty result."""
        message = stop.stop_message(stop.StopCounts())
        assert message == "The portal cancelled no device."

    def test_a_missing_cancel_call_reads_in_plain_words(self) -> None:
        """The message says that a device with no cancel call continues."""
        message = stop.stop_message(stop.StopCounts(no_cancel_available=2))
        assert "no cancel call for 2 devices, so those devices continue the upgrade." in message

    def test_an_unread_state_admits_the_doubt(self) -> None:
        """The portal never claims a stop that it could not prove."""
        message = stop.stop_message(stop.StopCounts(cancelled=1, status_unknown=1))
        assert "could not read the device state first" in message
        assert "may still finish the upgrade" in message

    def test_every_sentence_stays_short(self) -> None:
        """No sentence of the message runs past the writing guide limit."""
        message = stop.stop_message(stop.StopCounts(2, 2, 2, 1))
        sentences = [part for part in message.split(". ") if part]
        assert all(len(part.split()) <= 25 for part in sentences)

    def test_the_message_reaches_the_outcome(self) -> None:
        """The merged outcome carries the message the counts produce."""
        outcome = stop.merge_results([result(cancelled=(MAC_ONE,), writing=(MAC_TWO,))])
        assert "1 device that writes firmware now finishes the upgrade." in outcome.message


class TestCancelOnePlan:
    """One cancel call reads the state first and never raises."""

    def test_the_portal_reads_the_state_before_the_cancel(self, calls: dict[str, Any]) -> None:
        """The status read supplies the mid-write list to the cancel call.

        Args:
            calls: The call log of the two cloud doubles.
        """
        stop.cancel_target(object(), make_stop_target((MAC_ONE,)))
        assert calls["status"][0][:3] == ("site", "site-1", "up-1")
        assert calls["cancel"][0][1] == calls["status_answer"]

    def test_a_failed_status_read_still_cancels(self, calls: dict[str, Any]) -> None:
        """A status read that fails never blocks the cancel call.

        Args:
            calls: The call log of the two cloud doubles.
        """
        calls["status_error"] = RuntimeError("The cloud timed out.")
        answer = stop.cancel_target(object(), make_stop_target((MAC_ONE,)))
        assert calls["cancel"][0][1] is None
        assert answer.status_known is False

    def test_a_read_that_answers_no_upgrade_job_counts_as_unknown(self, calls: dict[str, Any]) -> None:
        """A read that answered still leaves the device state unknown.

        Why:
            The organization-scope read of a session smart router answers
            device statistics, and the seam marks that answer with
            `status_known` set to false. A test for `None` alone would call
            that answer a good read, and the operator would then see the word
            stopped for a device that may still write firmware.

        Args:
            calls: The call log of the two cloud doubles.
        """
        calls["status_answer"] = {"upgrade_id": "up-1", "devices": [], "status_known": False}
        answer = stop.cancel_target(object(), make_stop_target((MAC_ONE,)))
        assert answer.status_known is False

    def test_a_read_of_a_real_upgrade_job_counts_as_known(self, calls: dict[str, Any]) -> None:
        """A read that named an upgrade job is a good read.

        Args:
            calls: The call log of the two cloud doubles.
        """
        answer = stop.cancel_target(object(), make_stop_target((MAC_ONE,)))
        assert answer.status_known is True

    def test_a_failed_status_read_adds_the_doubt_to_the_message(self, calls: dict[str, Any]) -> None:
        """The run message admits that the portal read no device state.

        Args:
            calls: The call log of the two cloud doubles.
        """
        calls["status_error"] = RuntimeError("The cloud timed out.")
        outcome = stop.stop_run(object(), [make_stop_target((MAC_ONE,))], "STOP")
        assert "could not read the device state first" in outcome.message

    def test_a_failed_cancel_call_claims_no_stop(self, calls: dict[str, Any]) -> None:
        """A cancel that raises leaves every device of that plan running.

        Args:
            calls: The call log of the two cloud doubles.
        """
        calls["cancel_error"] = RuntimeError("The cloud refused the connection.")
        answer = stop.cancel_target(object(), make_stop_target((MAC_ONE, MAC_TWO)))
        assert answer.outcome.cancelled == ()
        assert answer.outcome.already_writing == (MAC_ONE, MAC_TWO)

    def test_one_failed_plan_never_ends_the_whole_stop(self, calls: dict[str, Any]) -> None:
        """The other plans of the run still reach a cancel call.

        Args:
            calls: The call log of the two cloud doubles.
        """
        calls["cancel_answer"] = lambda plan: CancelOutcome(stop.plan_macs(plan), (), (), "")
        calls["cancel_error"] = None
        targets = [make_stop_target((MAC_ONE,), "up-1"), make_stop_target((MAC_TWO,), "up-2")]
        outcome = stop.stop_run(object(), targets, "STOP")
        assert len(calls["cancel"]) == 2
        assert outcome.cancelled == (MAC_ONE, MAC_TWO)

    def test_plan_macs_reads_every_device_of_the_plan(self) -> None:
        """The helper returns one MAC address for each target."""
        assert stop.plan_macs(make_plan((MAC_ONE, MAC_TWO))) == (MAC_ONE, MAC_TWO)

    def test_a_failed_status_read_returns_no_status(self, calls: dict[str, Any]) -> None:
        """The reader answers with None and never raises.

        Args:
            calls: The call log of the two cloud doubles.
        """
        calls["status_error"] = OSError("The connection closed.")
        assert stop.read_last_status(object(), make_stop_target((MAC_ONE,))) is None


class TestStopRunAndRecord:
    """The run record holds the answer, so a page reload shows the same words."""

    def test_the_outcome_reaches_the_run_record(self, calls: dict[str, Any]) -> None:
        """The stop request of the record holds the three lists and the message.

        Args:
            calls: The call log of the two cloud doubles.
        """
        store = FakeRunStore(
            {
                "_key": RUN_ID,
                "run_id": RUN_ID,
                "state": "stopping",
                "stop_request": {"requested_by": "sam@example.com", "requested_at": "t0"},
            },
        )
        outcome = stop.stop_run_and_record(store, RUN_ID, object(), [make_stop_target((MAC_ONE,))], "STOP")
        held = store.record["stop_request"]["outcome"]
        assert held["cancelled"] == [MAC_ONE]
        assert held["message"] == outcome.message

    def test_the_record_keeps_the_operator_who_asked(self, calls: dict[str, Any]) -> None:
        """The outcome never replaces the owner of the stop request.

        Args:
            calls: The call log of the two cloud doubles.
        """
        store = FakeRunStore(
            {
                "_key": RUN_ID,
                "run_id": RUN_ID,
                "state": "stopping",
                "stop_request": {"requested_by": "sam@example.com", "requested_at": "t0"},
            },
        )
        stop.stop_run_and_record(store, RUN_ID, object(), [make_stop_target((MAC_ONE,))], "STOP")
        assert store.record["stop_request"]["requested_by"] == "sam@example.com"

    def test_a_wrong_word_writes_nothing(self, calls: dict[str, Any]) -> None:
        """A refused confirmation leaves the run record untouched.

        Args:
            calls: The call log of the two cloud doubles.
        """
        store = FakeRunStore({"run_id": RUN_ID, "state": "stopping", "stop_request": None})
        with pytest.raises(ConfirmationRequiredError):
            stop.stop_run_and_record(store, RUN_ID, object(), [make_stop_target((MAC_ONE,))], "no")
        assert store.writes == 0

    def test_the_answer_is_the_shared_outcome_value(self, calls: dict[str, Any]) -> None:
        """The stop returns the value the run record already understands.

        Args:
            calls: The call log of the two cloud doubles.
        """
        outcome = stop.stop_run(object(), [make_stop_target((MAC_ONE,))], "STOP")
        assert isinstance(outcome, StopOutcome)
