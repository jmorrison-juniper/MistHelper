"""Unit tests for the cloud submitter and the request readers of the wiring.

Why:
    Issue #1996 reports that ``app/wiring.py`` sits at 83 percent, under the 90
    percent floor that the aggregate hides. The audit of 2026-08-20 found defect
    11 and defect 12 in this same module. The uncovered half of a module is where
    a defect survives, and this module is the one that decides whether a firmware
    call leaves the portal at all.

    ``CloudUpgradeSubmitter`` is the sharpest example. `RunDriverDeps.submit`
    accepts None, and a driver built that way walks every phase and takes both
    captures while no firmware call ever leaves. Every refusal path of this class
    must therefore report one plain sentence rather than an exception, and no
    path may report success after the cloud refused.

    Issue #4020 changed the shape of this class. ``submit(record) -> bool`` sent
    every family of the site in one call, so a refused gateway group could not
    hold back the switch group that followed it. The class now answers
    ``submit_phase(record, phase) -> str | None``, which the driver calls once
    for each cascade phase, and a phase sends firmware only after the phase above
    it settled.

Warning:
    No test in this file reaches a cloud. Every test replaces ``load_module``,
    which is the one place where this module meets the upgrade seam.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from src.interfaces.portals.upgrade_portal.app import wiring
from src.interfaces.portals.upgrade_portal.upgrade.driver import PHASE_ORDER

RUN_ID = "11111111-1111-1111-1111-111111111111"
UPGRADE_ID = "22222222-2222-2222-2222-222222222222"
MAC_SWITCH = "209339051780"

ACCEPTED_STATUS = (200, 202)
REFUSED_STATUS = 400

GATEWAY_PHASE = "gateways"
SWITCH_PHASE = "switches"


def answer(status: int = 200, upgrade_id: str = UPGRADE_ID) -> Any:
    """Return one stand-in for the submission record of the upgrade seam.

    Args:
        status: The HTTP status that the cloud answered.
        upgrade_id: The cloud identifier of the call.

    Returns:
        One record with the four fields that `_submission_row` reads.
    """
    return SimpleNamespace(upgrade_id=upgrade_id, scope="site", accepted=(MAC_SWITCH,), raw_status=status)


def plan_for(device_type: str) -> Any:
    """Return one stand-in upgrade plan of one device family.

    Args:
        device_type: The family the plan holds, for example ``gateway``.

    Returns:
        One object with the ``targets`` attribute that `plan_phase` reads.
    """
    return SimpleNamespace(targets=(SimpleNamespace(device_type=device_type),))


def walk_phases(submitter: Any, record: dict[str, Any]) -> list[str]:
    """Drive one submitter the way the cascade drives it and name each phase.

    Why:
        The driver sends one phase, settles it, and only then sends the next
        phase. This helper repeats that loop with no gate and no cloud, so a
        test can read which phases reached the submitter before the run stopped.

    Args:
        submitter: The submitter under test.
        record: The run record.

    Returns:
        The phase names that reached the submitter, in the order of the cascade.
    """
    seen: list[str] = []  # The phases the cascade handed to the submitter.
    for phase in PHASE_ORDER:  # The driver walks this same fixed order.
        seen.append(phase)
        if submitter.submit_phase(record, phase) is not None:  # A sentence stops the run at once.
            break  # Issue #4020: no later family may receive a destructive write.
    return seen


def service_that(invoke: Any) -> Any:
    """Return a stand-in upgrade seam module.

    Args:
        invoke: The callable that stands in for ``invoke_upgrade``.

    Returns:
        One module-like object with the two names the wiring reads.
    """
    return SimpleNamespace(invoke_upgrade=invoke, ACCEPTED_STATUS=ACCEPTED_STATUS)


def install_modules(monkeypatch: pytest.MonkeyPatch, table: dict[str, Any]) -> None:
    """Replace the module loader of the wiring with a fixed table.

    Args:
        monkeypatch: The pytest patch helper.
        table: The module to answer for each module name.
    """
    monkeypatch.setattr(wiring, "load_module", table.get)


class TestTheSubmitterRefuses:
    """Tests for every path where no firmware call may leave the portal."""

    def test_reports_a_reason_when_the_run_builds_no_plan(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A run with no plan never reads as a sent upgrade.

        Why:
            A silent success here would carry the run into the settle phases and
            both captures while no firmware call ever left. The driver must fail
            the run instead.

        Args:
            monkeypatch: The pytest patch helper.
        """
        monkeypatch.setattr(wiring, "build_plans", lambda record: ())
        record: dict[str, Any] = {"run_id": RUN_ID}
        assert wiring.CloudUpgradeSubmitter(object()).submit_phase(record, GATEWAY_PHASE) == wiring.NO_PLAN_REASON

    def test_reports_a_reason_when_the_upgrade_seam_is_absent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A host with no upgrade seam sends nothing and says so.

        Args:
            monkeypatch: The pytest patch helper.
        """
        monkeypatch.setattr(wiring, "build_plans", lambda record: (plan_for("gateway"),))
        install_modules(monkeypatch, {})
        record: dict[str, Any] = {"run_id": RUN_ID}
        reason = wiring.CloudUpgradeSubmitter(object()).submit_phase(record, GATEWAY_PHASE)
        assert reason == wiring.PHASE_REFUSED_REASON.format(phase=GATEWAY_PHASE)
        assert record["upgrades"] == []

    def test_reports_a_reason_when_the_cloud_call_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A cloud fault ends the phase and never reads as an accepted write.

        Args:
            monkeypatch: The pytest patch helper.
        """

        def explode(session: Any, plan: Any) -> Any:
            """Raise the way a timed out cloud call does.

            Args:
                session: The cloud session.
                plan: The plan to send.

            Raises:
                RuntimeError: Always.
            """
            raise RuntimeError("the cloud did not answer")

        monkeypatch.setattr(wiring, "build_plans", lambda record: (plan_for("gateway"),))
        install_modules(monkeypatch, {wiring.SERVICE_MODULE: service_that(explode)})
        record: dict[str, Any] = {"run_id": RUN_ID}
        reason = wiring.CloudUpgradeSubmitter(object()).submit_phase(record, GATEWAY_PHASE)
        assert reason == wiring.PHASE_REFUSED_REASON.format(phase=GATEWAY_PHASE)
        assert record["upgrades"] == []

    def test_reports_a_reason_when_the_cloud_refuses(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A refused status never reads as an accepted call.

        Why:
            The seam never raises for a cloud error status. It records the true
            status instead, so this module owns the decision. A refused group
            carries no identifier that the stop path could use.

        Args:
            monkeypatch: The pytest patch helper.
        """
        monkeypatch.setattr(wiring, "build_plans", lambda record: (plan_for("gateway"),))
        install_modules(
            monkeypatch,
            {wiring.SERVICE_MODULE: service_that(lambda session, plan: answer(REFUSED_STATUS))},
        )
        record: dict[str, Any] = {"run_id": RUN_ID}
        reason = wiring.CloudUpgradeSubmitter(object()).submit_phase(record, GATEWAY_PHASE)
        assert reason == wiring.PHASE_REFUSED_REASON.format(phase=GATEWAY_PHASE)
        assert record["upgrades"] == []


class TestTheSubmitterSends:
    """Tests for the paths where the cloud accepted at least one call."""

    def test_reports_none_and_keeps_the_cloud_identifier(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An accepted call writes the row that the stop path reads.

        Args:
            monkeypatch: The pytest patch helper.
        """
        monkeypatch.setattr(wiring, "build_plans", lambda record: (plan_for("gateway"),))
        install_modules(
            monkeypatch,
            {wiring.SERVICE_MODULE: service_that(lambda session, plan: answer())},
        )
        record: dict[str, Any] = {"run_id": RUN_ID}
        assert wiring.CloudUpgradeSubmitter(object()).submit_phase(record, GATEWAY_PHASE) is None
        assert record["upgrades"] == [
            {"upgrade_id": UPGRADE_ID, "scope": "site", "accepted": [MAC_SWITCH], "raw_status": 200}
        ]

    def test_a_phase_with_no_plan_sends_nothing_and_stops_no_run(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A site that holds no gateway reaches the cloud for no gateway.

        Why:
            FR-058 skips an absent family. The submitter must therefore answer
            None without one cloud call, so the driver marks the phase skipped
            and opens the next gate.

        Args:
            monkeypatch: The pytest patch helper.
        """
        sent: list[Any] = []  # Any entry here would be a firmware call for a family the site does not hold.
        monkeypatch.setattr(wiring, "build_plans", lambda record: (plan_for("switch"),))
        install_modules(
            monkeypatch,
            {wiring.SERVICE_MODULE: service_that(lambda session, plan: sent.append(plan) or answer())},
        )
        record: dict[str, Any] = {"run_id": RUN_ID}
        assert wiring.CloudUpgradeSubmitter(object()).submit_phase(record, GATEWAY_PHASE) is None
        assert sent == []

    def test_a_refused_gateway_group_sends_no_switch_firmware(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Issue #4020: a refused family holds the firmware of every later family.

        Why:
            This test replaces ``test_keeps_the_group_that_worked_when_another
            _group_fails``, which asserted the defect. That test accepted one
            refused group followed by one accepted group and reported success,
            because the old ``submit`` sent every family of the site in one
            comprehension. Measured against that code, this same selection
            produced ``calls == ["gateways", "switches"]`` with a true result.
            The switch firmware therefore left the portal while the gateways of
            the site had taken none, which is the outage this issue repairs.

            The replacement is deliberate. The old assertion cannot hold beside
            the new one, because the two describe opposite behavior.

        Args:
            monkeypatch: The pytest patch helper.
        """
        plans = (plan_for("gateway"), plan_for("switch"))  # One family for each of the first two phases.
        calls: list[str] = []  # Records the family of every plan that reached the cloud seam.

        def send(session: Any, plan: Any) -> Any:
            """Answer one cloud call and record the family it carried.

            Args:
                session: The cloud session.
                plan: The plan the submitter sent.

            Returns:
                A refused answer for the gateways, and an accepted answer for
                every other family.
            """
            phase = wiring.plan_phase(plan)
            calls.append(phase)
            return answer(REFUSED_STATUS) if phase == GATEWAY_PHASE else answer()

        monkeypatch.setattr(wiring, "build_plans", lambda record: plans)
        install_modules(monkeypatch, {wiring.SERVICE_MODULE: service_that(send)})
        record: dict[str, Any] = {"run_id": RUN_ID}
        seen = walk_phases(wiring.CloudUpgradeSubmitter(object()), record)
        assert calls == ["gateways"]  # The switch firmware never left the portal.
        assert seen == ["gateways"]  # The cascade stopped before the switch phase.
        assert record["upgrades"] == []  # A refused group leaves no identifier for the stop path.

    def test_an_accepted_gateway_phase_keeps_its_rows_when_the_switches_fail(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A later refusal never drops the identifiers of the family above it.

        Why:
            The gateways are already writing firmware when the switch call is
            refused. The stop path needs the gateway upgrade identifier to
            cancel that work, so the record must keep it.

        Args:
            monkeypatch: The pytest patch helper.
        """
        plans = (plan_for("gateway"), plan_for("switch"))

        def send(session: Any, plan: Any) -> Any:
            """Accept the gateway call and refuse the switch call.

            Args:
                session: The cloud session.
                plan: The plan the submitter sent.

            Returns:
                The cloud answer for this family.
            """
            return answer() if wiring.plan_phase(plan) == GATEWAY_PHASE else answer(REFUSED_STATUS)

        monkeypatch.setattr(wiring, "build_plans", lambda record: plans)
        install_modules(monkeypatch, {wiring.SERVICE_MODULE: service_that(send)})
        record: dict[str, Any] = {"run_id": RUN_ID}
        seen = walk_phases(wiring.CloudUpgradeSubmitter(object()), record)
        assert seen == ["gateways", "switches"]  # The gateways settled, so the switches tried.
        assert len(record["upgrades"]) == 1  # The accepted gateway row survived the switch refusal.

    def test_accepts_the_second_accepted_status(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The cloud may answer 202, and the seam names both codes.

        Args:
            monkeypatch: The pytest patch helper.
        """
        monkeypatch.setattr(wiring, "build_plans", lambda record: (plan_for("switch"),))
        install_modules(
            monkeypatch,
            {wiring.SERVICE_MODULE: service_that(lambda session, plan: answer(202))},
        )
        assert wiring.CloudUpgradeSubmitter(object()).submit_phase({"run_id": RUN_ID}, SWITCH_PHASE) is None


class TestBoundStore:
    """Tests for the reader that keeps one run store for the whole run."""

    def test_answers_the_default_with_no_route_module(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """No route module means no seam, so the default store stands.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install_modules(monkeypatch, {})
        default = object()
        assert wiring.bound_store(default) is default  # type: ignore[arg-type]

    def test_answers_the_default_when_the_seam_read_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A seam that needs an application answers None outside a request.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install_modules(monkeypatch, {wiring.UPGRADE_ROUTES: SimpleNamespace(run_store=lambda: None)})
        monkeypatch.setattr(wiring, "read_safely", lambda read, subject: None)
        default = object()
        assert wiring.bound_store(default) is default  # type: ignore[arg-type]

    def test_answers_the_seam_store_when_one_exists(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An injected store wins, so the driver writes where the poll reads.

        Why:
            A driver that held a second store would write where the poll route
            never reads, and the run would look frozen on the progress page.

        Args:
            monkeypatch: The pytest patch helper.
        """
        injected = object()
        install_modules(monkeypatch, {wiring.UPGRADE_ROUTES: SimpleNamespace(run_store=lambda: injected)})
        monkeypatch.setattr(wiring, "read_safely", lambda read, subject: injected)
        assert wiring.bound_store(object()) is injected  # type: ignore[arg-type]


class TestCurrentOperator:
    """Tests for the one accessor of the signed session."""

    def test_answers_none_with_no_identity_module(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A host with no identity module reports an absent operator.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install_modules(monkeypatch, {})
        assert wiring.current_operator() is None

    def test_answers_the_record_of_the_present_request(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The accessor returns what the identity module holds.

        Args:
            monkeypatch: The pytest patch helper.
        """
        record = SimpleNamespace(cloud_session=object())
        install_modules(monkeypatch, {wiring.IDENTITY_MODULE: SimpleNamespace(current_session=lambda: record)})
        monkeypatch.setattr(wiring, "read_safely", lambda read, subject: read())
        assert wiring.current_operator() is record


class TestTheStorageBootstrapRunsOnce:
    """Tests for the guard that keeps the bootstrap to one run for each process.

    Why:
        A contract test builds one application for each test, and every
        application called the bootstrap. Each call reached
        ``DatabaseConfig.from_env``, which resolves the database host and the
        lock store host to decide the standalone mode. On a runner where the host
        name does not resolve quickly, each call took about 20 seconds, and the
        whole test job reached its 15 minute limit and reported as a test
        failure. Issue #2036 holds that record.

        Every step of the bootstrap repeats without harm, so one run for each
        process is enough.
    """

    def test_calls_the_store_one_time_for_many_applications(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Five calls reach the capture store one time.

        Args:
            monkeypatch: The pytest patch helper.
        """
        wiring.reset_storage_bootstrap()
        seen: list[str] = []
        store = SimpleNamespace(bootstrap_storage=lambda: seen.append("run") or "report")
        install_modules(monkeypatch, {wiring.CAPTURE_STORE_MODULE: store})
        for _ in range(5):  # Five applications, as a contract file builds.
            wiring.prepare_storage()
        assert len(seen) == 1

    def test_a_reset_lets_the_next_application_build_again(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A worker that meets a database restart can clear the guard.

        Args:
            monkeypatch: The pytest patch helper.
        """
        wiring.reset_storage_bootstrap()
        seen: list[str] = []
        store = SimpleNamespace(bootstrap_storage=lambda: seen.append("run") or "report")
        install_modules(monkeypatch, {wiring.CAPTURE_STORE_MODULE: store})
        wiring.prepare_storage()
        wiring.reset_storage_bootstrap()
        wiring.prepare_storage()
        assert len(seen) == 2

    def test_a_failed_bootstrap_never_retries_on_every_application(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A store that raises still costs one call and not one for each application.

        Why:
            The guard is set before the call, so a raise leaves no retry loop.
            A store that is out of reach is the exact case that made the runner
            stall, so the guard must hold for it above every other case.

        Args:
            monkeypatch: The pytest patch helper.
        """
        wiring.reset_storage_bootstrap()
        seen: list[str] = []

        def explode() -> Any:
            """Raise the way an unreachable store does.

            Returns:
                Never returns.

            Raises:
                RuntimeError: Always.
            """
            seen.append("run")
            raise RuntimeError("the document store is out of reach")

        install_modules(monkeypatch, {wiring.CAPTURE_STORE_MODULE: SimpleNamespace(bootstrap_storage=explode)})
        for _ in range(4):
            wiring.prepare_storage()
        assert len(seen) == 1

    def test_an_absent_store_still_leaves_a_portal_that_reads(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A host with no capture store builds an application and raises nothing.

        Args:
            monkeypatch: The pytest patch helper.
        """
        wiring.reset_storage_bootstrap()
        install_modules(monkeypatch, {})
        wiring.prepare_storage()  # Raises nothing, which is the whole assertion.
        assert wiring._STORAGE_PREPARED is True  # WHY: prove the absent store still completed setup.
        wiring.reset_storage_bootstrap()
