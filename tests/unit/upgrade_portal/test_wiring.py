"""Prove the seam wiring of the upgrade portal joins the parts it claims to join.

Why:
    The defect this module guards against is silence. A run that finds no
    launcher answers exactly like a run that started, so no browser and no log
    line tells the operator that no upgrade left the portal. These tests read the
    wiring straight, without a cloud, a store, or a socket.

    The most important test states the T183 rule: the same site lock heartbeat
    must sit in `RunDriverDeps.heartbeat` and in `PhaseGateDeps.progress`. The
    settle gate blocks for up to 1800 seconds inside one call while the lock
    lives 300 seconds, so only the 20-second poll loop of the gate can renew it.
"""

import logging  # The tests read the warning lines that the wiring writes.
from collections.abc import Iterator  # The shape of the fixture that empties the run mirror.
from typing import Any  # The stand-ins hold free-form records.

import pytest  # The test framework of the project.

from src.upgrade_portal.app import factory, wiring  # The units under test.
from src.upgrade_portal.upgrade import driver, phase_gate  # The two seats of the shared heartbeat.

SITE_ID = "site-a"  # One site name for every test of this module.
ORG_ID = "org-a"  # One organization name for every test of this module.
RUN_ID = "run-1"  # One run key for every test of this module.
BROWSER_ID = "browser000000001"  # The URL-safe shape of 16 to 128 characters that the identity guard demands.

RUN_COLLECTION_NAME = "upgrade_runs"  # The collection that `capture/store.py` names for a run record.


class StoreAnswer:
    """Stand for the result record that `capture/store.write_run` answers.

    Why:
        The wiring reads two names off that record and reads nothing else, so a
        two field stand-in states exactly the contract the wiring depends on.
    """

    def __init__(self, verified: bool = False, backup_written: bool = False) -> None:
        """Hold the two results of one write.

        Args:
            verified: True when the database read the record back unchanged.
            backup_written: True when the CSV backup holds the record.
        """
        self.verified = verified  # The durable result of the document store.
        self.backup_written = backup_written  # The result of the fallback file.


class StoreHandle:
    """Stand for a database handle that answers one run record.

    Why:
        `DocumentRunStore.read_run` walks a handle, a collection, and a get
        call. A test of the read order needs all three, and none of them may
        open a socket.
    """

    def __init__(self, row: dict[str, Any] | None) -> None:
        """Hold the one row that every read answers.

        Args:
            row: The record the get call answers, or None for an absent run.
        """
        self.row = row  # The whole answer of this stand-in database.

    def collection(self, name: str) -> Any:
        """Answer this same object for any collection name.

        Args:
            name: The collection name. One row answers every name.

        Returns:
            This object, which also carries the get call.
        """
        del name  # One row answers every collection of this stand-in.
        return self

    def get(self, run_id: str) -> dict[str, Any] | None:
        """Answer the held row for any run key.

        Args:
            run_id: The run key. One row answers every key.

        Returns:
            The held row, which may be None.
        """
        del run_id  # One row answers every key of this stand-in.
        return self.row


@pytest.fixture(autouse=True)
def empty_run_mirror() -> Iterator[None]:
    """Empty the run mirror of the wiring around every test of this module.

    Why:
        The mirror is one table for the whole process. A record that one test
        writes would answer the read of the next test, and two tests below prove
        that an unreachable store reads as an unknown run. A leaked record would
        turn both of them green for the wrong reason. The table is private on
        purpose, because no shipped caller may empty it.

    Yields:
        Nothing. The test runs between the two clearing steps.
    """
    wiring._MIRROR.clear()  # The table is private, because no shipped caller may empty it.
    yield
    wiring._MIRROR.clear()  # The next test of any module then starts with an empty table.


class StubRunner:
    """Record each capture job that the bridge sends, and answer nothing.

    Why:
        `driver.CaptureStarter` blocks on the runner, so a test must prove the
        bridge calls it straight and never spawns a second thread.
    """

    def __init__(self) -> None:
        """Start with no recorded job."""
        self.jobs: list[dict[str, Any]] = []  # Every job that the bridge sent.

    def __call__(self, job: dict[str, Any]) -> None:
        """Record one capture job.

        Args:
            job: The eleven field job that the collector reads.
        """
        self.jobs.append(dict(job))  # A copy, because the caller may edit its own record.


class RefusingRunner:
    """Raise on every call, to prove the bridge answers None instead of dying.

    Why:
        The runner runs on the driver thread. A fault that escapes would end the
        thread with no state change, so the run would look frozen forever.
    """

    def __call__(self, job: dict[str, Any]) -> None:
        """Raise, whatever the job holds.

        Args:
            job: The capture job. This runner reads none of it.

        Raises:
            RuntimeError: Always.
        """
        raise RuntimeError("The site did not answer.")  # The bridge must hold this fault.


def sample_record() -> dict[str, Any]:
    """Build one run record with the fields the wiring reads.

    Why:
        Every test needs the same small record, and a shared builder keeps the
        field names in one place.

    Returns:
        The run record.
    """
    return {  # The fields that the wiring reads out of a run record.
        "run_id": RUN_ID,  # Names the run in each log line.
        "org_id": ORG_ID,  # Both cloud readers narrow to this organization.
        "site_id": SITE_ID,  # The site of the lock and of the capture.
        "site_name": "Site A",  # The readable name that a page shows.
        "org_name": "Org A",  # The readable name that a page shows.
        "tier": 2,  # The data tier of the capture.
        "targets": (),  # No device, so no upgrade plan can be built.
        "options": {},  # The default upgrade choices.
    }


def test_import_opens_no_socket() -> None:
    """The import of the wiring module must reach no network.

    Why:
        The factory imports this module at load. A socket at import time would
        make every test and every start of the portal wait on a server.
    """
    module = wiring.load_module("src.upgrade_portal.app.wiring")  # The autouse fixture blocks every socket.
    assert module is not None  # A socket call would have raised instead.


def test_load_module_answers_none_for_an_absent_module() -> None:
    """A missing collaborator writes one warning and never raises.

    Why:
        The portal is built in stages, so a module can arrive later. A missing
        module must leave every other seam working.
    """
    assert wiring.load_module("src.upgrade_portal.no_such_module") is None  # One warning, no fault.


def test_install_seams_fills_the_launcher_and_the_store() -> None:
    """A fresh application must hold both seams that no route can build alone.

    Why:
        `routes/upgrade.launch_run` reads `RUN_LAUNCHER` and answers as if the
        run started when the seam is empty. That silence is the whole defect.
    """
    app = factory.create_app()  # The factory calls `install_seams` inside `arm_application`.
    assert callable(app.config.get(wiring.LAUNCHER_KEY))  # Without this the confirmed run sends nothing.
    assert isinstance(app.config.get(wiring.RUN_STORE_KEY), wiring.DocumentRunStore)  # The durable store.


def test_install_seams_keeps_an_injected_value() -> None:
    """A caller that already chose a seam value must keep it.

    Why:
        Every contract test injects its own store and its own launcher. A wiring
        that replaced them would drive the tests onto a live cloud.
    """
    app = factory.create_app()  # Already armed once, with both seams filled.
    app.config[wiring.LAUNCHER_KEY] = "the choice of the test"  # A caller sets its own value.
    wiring.install_seams(app)  # A second arm must change nothing.
    assert app.config[wiring.LAUNCHER_KEY] == "the choice of the test"  # `setdefault`, never a replacement.


def test_install_seams_fills_the_stop_runner() -> None:
    """The cancel seam must hold the cancel worker.

    Why:
        The stop route reads `STOP_RUNNER`. An empty seam makes that route
        record the request and then claim a stop that cancelled no device.
        `CloudUpgradeSubmitter.submit` now writes the cloud identifier of each
        accepted call onto the run record, so the worker has a true answer.
    """
    app = factory.create_app()  # The armed application, with the seams in place.
    assert app.config.get("STOP_RUNNER") is wiring.cancel_run  # The route then cancels at the cloud.
    assert app.config.get("UPGRADE_OPTIONS_BUILDER") is None  # The route resolves the builder from the module.


def test_the_same_heartbeat_reaches_both_seats() -> None:
    """One heartbeat object must sit in the driver and in the settle gate.

    Why:
        This is the T183 rule. The settle gate blocks for up to 1800 seconds in
        one call and the site lock lives 300 seconds, so only the 20-second poll
        loop inside the gate can renew the lock. A heartbeat that reached the
        driver alone would beat twice for each phase and the lock would lapse.
    """
    deps = wiring.build_driver_deps(driver, sample_record(), bindings_with_lock())  # The whole build.
    assert deps is not None  # A missing collaborator would have answered None.
    assert isinstance(deps.heartbeat, driver.LockHeartbeat)  # The first seat, which the driver beats.
    assert deps.gate._deps.progress is deps.heartbeat  # The second seat, inside the 20-second poll loop.


def test_the_heartbeat_in_the_gate_reports_like_a_progress_reporter() -> None:
    """The heartbeat must answer the call that the poll loop of the gate makes.

    Why:
        The gate reports progress once for each round. Lane 45 made
        `LockHeartbeat` satisfy that protocol by shape alone, and neither
        protocol runs at run time, so a rename in either module would break the
        renewal in silence. This test names the shape instead.
    """
    beat = driver.lock_heartbeat(sample_record(), sample_lock())  # The object of both seats.
    assert callable(beat.report)  # The name that `PhaseGateDeps.progress` calls once for each round.
    assert callable(beat.beat)  # The name that `RunDriverDeps.heartbeat` calls at every wait.
    beat.report(None)  # Rate limited, so this first call reaches no lock store at all.
    deps = phase_gate.PhaseGateDeps(event_reader=None, statistics_reader=None, progress=beat)  # The seat.
    assert deps.progress is beat  # The gate now beats the lock once for each 20-second round.


def bindings_with_lock() -> dict[str, Any]:
    """Build the request bindings that a healthy run would carry.

    Why:
        `request_bindings` needs a request, and these tests hold none. This
        builder writes the same five keys with values that reach no cloud.

    Returns:
        The five bindings that the driver build reads.
    """
    return {  # The five values that only a request thread can read for itself.
        wiring.SESSION_FIELD: object(),  # A stand-in session. No test here performs a cloud call.
        wiring.EMAIL_FIELD: "",  # No address, because a log must never hold one in plain text.
        wiring.RUNNER_FIELD: StubRunner(),  # Records each capture job.
        wiring.LOCK_FIELD: sample_lock(),  # The lock that the heartbeat renews.
        wiring.STORE_FIELD: wiring.DocumentRunStore(),  # The store that the routes also read.
    }


def sample_lock() -> Any:
    """Build one site lock record for the heartbeat to renew.

    Why:
        The record holds a token, so no test may write it to a log. The pair of
        the address and the browser identifier is checked on construction, so
        both halves carry a real looking value.

    Returns:
        The lock record.
    """
    from src.upgrade_portal.runtime import identity, lock  # Late, to match the import rule of the wiring module.

    owner = identity.SessionOwner(actor_email="operator@example.com", browser_id=BROWSER_ID)  # Checked here.
    stamp = "2026-08-19T11:00:00+00:00"  # One fixed moment, so no test reads a real clock.
    return lock.LockRecord(  # The five fields that name one held lock.
        owner=owner,  # The address and the browser identifier travel as one pair.
        lock_token="token-a",  # Never written to a log.
        run_id=RUN_ID,  # The run that this lock protects.
        acquired_at=stamp,  # A heartbeat never moves this field.
        refreshed_at=stamp,  # Every beat moves this field forward.
    )


def test_the_driver_always_holds_a_submitter() -> None:
    """The driver must never run with an empty submitter.

    Why:
        `driver._submit` treats an empty submitter as a success, so the run walks
        every phase and takes both captures while no firmware call ever leaves.
        That is the same silent defect in a second place.
    """
    deps = wiring.build_driver_deps(driver, sample_record(), bindings_with_lock())  # The whole build.
    assert deps is not None  # A missing collaborator would have answered None.
    assert isinstance(deps.submit, wiring.CloudUpgradeSubmitter)  # A real call, never a quiet skip.


def test_a_run_with_no_target_sends_nothing_and_says_so() -> None:
    """A run that builds no plan must report a failure, never a success.

    Why:
        An empty plan list and a sent upgrade must never read the same.
    """
    submitter = wiring.CloudUpgradeSubmitter(object())  # The session is never reached, because no plan is built.
    record = sample_record()  # This record holds no target at all.
    assert submitter.submit(record) is False  # The driver then fails the run and writes the reason.


def test_the_capture_bridge_calls_the_runner_on_this_thread() -> None:
    """The bridge must call the runner straight and answer with the capture key.

    Why:
        The driver counts on the capture to hold the thread, and it beats the
        lock on each side of that call. A second thread would break both.
    """
    runner = StubRunner()  # Records the job that the bridge sends.
    bridge = wiring.CaptureBridge(runner, {"org_id": ORG_ID, "site_id": SITE_ID})  # The shared job fields.
    answer = bridge.start(driver.post_check_request(RUN_ID))  # The second capture of the run.
    assert answer == wiring.build_capture_key(RUN_ID, 2)  # The one true form of the capture key.
    assert runner.jobs[0]["ordinal"] == 2  # The post-check is always the second capture.
    assert runner.jobs[0]["role"] == "post"  # The role that the comparison reads.


def test_the_capture_bridge_holds_a_fault_of_the_runner() -> None:
    """A runner that raises must leave the bridge answering None.

    Why:
        The bridge runs on the driver thread. A fault that escaped would end the
        thread with no state change, so the run would look frozen forever.
    """
    bridge = wiring.CaptureBridge(RefusingRunner(), {})  # The runner raises on every call.
    assert bridge.start(driver.post_check_request(RUN_ID)) is None  # The driver then fails the run.


def test_the_capture_bridge_names_the_gap_when_no_runner_bound() -> None:
    """A bridge with no runner must write one error line and answer None.

    Why:
        A silent skip here would leave the run with no post-check capture and no
        word about the loss, so the comparison page would never open.
    """
    bridge = wiring.CaptureBridge(None, {})  # No runner reached the bindings.
    assert bridge.start(driver.post_check_request(RUN_ID)) is None  # Never a key for a capture that did not run.


def test_the_document_store_answers_none_when_no_database_opens(monkeypatch: pytest.MonkeyPatch) -> None:
    """A store that does not open must read as an unknown run, never as a fault.

    Why:
        The poll route calls the read many times for each run. A fault there
        would turn a slow store into a 500 answer on the operator screen.
    """
    from src.upgrade_portal.capture import store  # Late, to match the import rule of the wiring module.

    monkeypatch.setattr(store, "connect_database", lambda *args, **kwargs: None)  # Standalone mode.
    assert wiring.DocumentRunStore().read_run(RUN_ID) is None  # The caller reads an unknown run.


def test_the_document_store_reports_a_failed_write(monkeypatch: pytest.MonkeyPatch) -> None:
    """A write that did not land must answer False.

    Why:
        A write that answered True while nothing landed would leave the poll
        route reading a stale state forever.
    """
    from src.upgrade_portal.capture import store  # Late, to match the import rule of the wiring module.

    monkeypatch.setattr(store, "write_run", lambda *args, **kwargs: _boom())  # The store refuses the write.
    assert wiring.DocumentRunStore().write_run({"run_id": RUN_ID}) is False  # One warning, no fault.


def _boom() -> Any:
    """Raise, to stand for a store that does not answer.

    Returns:
        Nothing. This function always raises.

    Raises:
        RuntimeError: Always.
    """
    raise RuntimeError("The store did not answer.")  # The wiring must hold this fault.


def test_the_site_scan_answers_an_empty_list_when_the_store_is_silent(monkeypatch: pytest.MonkeyPatch) -> None:
    """A failed site scan must refuse no run.

    Why:
        The scan supports FR-037. A guess from an unreachable store would stop
        honest work, and the site lock already guards a second operator.
    """
    from src.upgrade_portal.capture import store  # Late, to match the import rule of the wiring module.

    monkeypatch.setattr(store, "list_runs", lambda *args, **kwargs: _boom())  # The query does not answer.
    assert wiring.DocumentRunStore().runs_for_site(SITE_ID) == []  # The create route then continues.


def _standalone_store(monkeypatch: pytest.MonkeyPatch, answer: StoreAnswer) -> Any:
    """Point the wiring at a store that opens no database and answers one write.

    Why:
        Every mirror test below needs the same two changes, and a copy in each
        test would hide the one state under test.

    Args:
        monkeypatch: The pytest patching fixture.
        answer: The result record that the write answers.

    Returns:
        The run store adapter under test.
    """
    from src.upgrade_portal.capture import store  # Late, to match the import rule of the wiring module.

    monkeypatch.setattr(store, "connect_database", lambda *args, **kwargs: None)  # Standalone mode.
    monkeypatch.setattr(store, "write_run", lambda *args, **kwargs: answer)  # One fixed write result.
    return wiring.DocumentRunStore()


def test_a_landed_run_reads_back_with_no_database(monkeypatch: pytest.MonkeyPatch) -> None:
    """A run that reached the CSV backup must still read back in this process.

    Why:
        This is the whole defect. `connect_database` answers None whenever
        ArangoDB is unreachable, while the write reports success because the
        backup file holds the record. The run then read back as absent, so the
        progress page showed no run and FR-035 refused every start forever.
    """
    adapter = _standalone_store(monkeypatch, StoreAnswer(backup_written=True))  # The CSV fallback held it.
    assert adapter.write_run({"run_id": RUN_ID, "site_id": SITE_ID, "state": "created"}) is True
    held = adapter.read_run(RUN_ID)  # The read that the poll route and the three pages all make.
    assert held is not None and held["state"] == "created"  # The operator reads a real run, never a blank page.


def test_a_write_that_landed_nowhere_reaches_no_mirror(monkeypatch: pytest.MonkeyPatch) -> None:
    """A failed write must leave the run unreadable, exactly as the caller was told.

    Why:
        The route answers a write failure to the operator. A mirror that held
        the record anyway would show a run that no store keeps, so a restart of
        the portal would lose work that the screen reported as saved.
    """
    adapter = _standalone_store(monkeypatch, StoreAnswer())  # Neither the database nor the backup held it.
    assert adapter.write_run({"run_id": RUN_ID, "site_id": SITE_ID}) is False  # The caller learns the truth.
    assert adapter.read_run(RUN_ID) is None  # No later read may claim the run exists.


def test_the_stored_row_wins_over_the_mirrored_copy(monkeypatch: pytest.MonkeyPatch) -> None:
    """A database that answers must beat the copy that this process holds.

    Why:
        A second portal worker may advance the run. A mirror that won the read
        would pin the page at the state this process last wrote, so the operator
        would watch a run that never moves.
    """
    from src.upgrade_portal.capture import store  # Late, to match the import rule of the wiring module.

    adapter = _standalone_store(monkeypatch, StoreAnswer(backup_written=True))  # Fill the mirror first.
    adapter.write_run({"run_id": RUN_ID, "site_id": SITE_ID, "state": "created"})
    newer = {"run_id": RUN_ID, "site_id": SITE_ID, "state": "upgrade_running"}  # What a second worker wrote.
    monkeypatch.setattr(store, "connect_database", lambda *args, **kwargs: StoreHandle(newer))  # It answers now.
    monkeypatch.setattr(store, "RUN_COLLECTION", RUN_COLLECTION_NAME, raising=False)
    held = adapter.read_run(RUN_ID)
    assert held is not None and held["state"] == "upgrade_running"  # The stored row wins every time.


def test_the_site_scan_falls_back_to_the_mirrored_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    """A site scan with no database must still find the run this process holds.

    Why:
        FR-037 asks the portal to find a run that already acts on the site. A
        scan that answered empty would let one operator open a second run
        against a site that is already upgrading.
    """
    adapter = _standalone_store(monkeypatch, StoreAnswer(backup_written=True))
    adapter.write_run({"run_id": RUN_ID, "site_id": SITE_ID, "state": "created"})
    rows = adapter.runs_for_site(SITE_ID)  # The scan that the create route makes.
    assert [row["run_id"] for row in rows] == [RUN_ID]  # The site already holds a run.
    assert adapter.runs_for_site("site-b") == []  # A second site still holds none.


def test_the_run_mirror_holds_a_bounded_number_of_runs() -> None:
    """The mirror must drop its oldest run once it reaches the limit.

    Why:
        A portal that runs for weeks writes a record for every state change of
        every run. An unbounded table would grow until the process died.
    """
    for number in range(wiring.MIRROR_LIMIT + 5):  # Five more runs than the table may hold.
        wiring.mirror_run({"run_id": f"run-{number}", "site_id": SITE_ID})
    assert wiring.mirrored_run("run-0") is None  # The oldest run left first.
    assert wiring.mirrored_run(f"run-{wiring.MIRROR_LIMIT + 4}") is not None  # The newest run stayed.


def test_a_record_with_no_run_key_reaches_no_mirror() -> None:
    """A record that names no run must reach no table.

    Why:
        A record with no key can never be read back, so a table entry for it
        would only take the place of a run that an operator still watches.
    """
    wiring.mirror_run({"site_id": SITE_ID})  # The one record shape that carries no key.
    assert wiring.mirrored_site_runs(SITE_ID) == []  # The table stayed empty.


def test_the_document_store_matches_the_shape_the_driver_declares() -> None:
    """The store must satisfy the protocol that the driver and the route share.

    Why:
        `upgrade/driver.py` imports `RunRecordStore` from `runtime/signals.py`,
        which is the same protocol `routes/upgrade.py` reads by name. One adapter
        must therefore serve both, or the run and the poll read two stores.
        Neither protocol runs at run time, so this test names the shape.
    """
    store = wiring.DocumentRunStore()  # The one adapter that both callers read.
    assert callable(store.read_run)  # The route poll and the driver save both call this name.
    assert callable(store.write_run)  # The driver writes every state change through this name.
    assert callable(store.runs_for_site)  # The optional site scan that FR-037 asks for.


def test_the_launcher_writes_an_error_when_it_cannot_build_a_driver(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """A launcher that cannot build a driver must name the gap in the log.

    Why:
        The whole defect is a run that sends nothing while it reads as normal.
        Every path that sends nothing must therefore write one error line.
    """
    monkeypatch.setattr(wiring, "build_driver_deps", lambda *args: None)  # A collaborator is missing.
    monkeypatch.setattr(wiring, "request_bindings", lambda record: {})  # No request runs in this test.
    with caplog.at_level(logging.ERROR):  # The reader must find the error, not a quiet return.
        wiring.start_upgrade_run(sample_record())  # The call that `routes/upgrade.launch_run` makes.
    assert RUN_ID in caplog.text  # The line names the run that sent nothing.


def test_the_launcher_starts_one_thread(monkeypatch: pytest.MonkeyPatch) -> None:
    """A healthy launcher must hand the record to exactly one driver.

    Why:
        This is the repair. `routes/upgrade.launch_run` reads this callable, and
        before the repair it read None and the confirmed run sent nothing.
    """
    started: list[dict[str, Any]] = []  # Every record that a driver received.
    monkeypatch.setattr(wiring, "request_bindings", lambda record: {})  # No request runs in this test.
    monkeypatch.setattr(wiring, "build_driver_deps", lambda *args: object())  # A stand-in dependency record.
    monkeypatch.setattr(driver, "RunDriver", lambda deps: _Recorder(started))  # No thread starts in this test.
    wiring.start_upgrade_run(sample_record())  # The call that `routes/upgrade.launch_run` makes.
    assert started[0]["run_id"] == RUN_ID  # The driver received the prepared record, whole.


class _Recorder:
    """Record the record that the launcher hands to the driver.

    Why:
        A real driver would start a thread that reaches a cloud, so the test
        replaces it and reads what the launcher passed.
    """

    def __init__(self, sink: list[dict[str, Any]]) -> None:
        """Hold the list that receives each started record.

        Args:
            sink: The list to append to.
        """
        self._sink = sink  # The test reads this list after the call.

    def start(self, record: dict[str, Any]) -> None:
        """Record one run and start nothing.

        Args:
            record: The prepared run record.
        """
        self._sink.append(dict(record))  # A copy, because the caller may edit its own record.


def test_the_driver_deps_carry_the_post_check_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """The wiring reads the post-check mode and hands it to the driver.

    Why:
        The driver holds the seam and only the wiring can fill it. A build that
        dropped the mode would hold every portal at the default forever, and the
        switch would look broken to the operator who set it.

    Args:
        monkeypatch: The pytest patch helper.
    """
    monkeypatch.delenv("CAPTURE_POST_CHECK_MODE", raising=False)  # The default path needs an absent variable.
    deps = wiring.build_driver_deps(driver, sample_record(), bindings_with_lock())  # The whole build.
    assert deps.post_check_mode == driver.POST_CHECK_AUTOMATIC  # The behavior of today.
    monkeypatch.setenv("CAPTURE_POST_CHECK_MODE", "manual")  # The operator asks for the manual capture.
    held = wiring.build_driver_deps(driver, sample_record(), bindings_with_lock())  # The same build again.
    assert held.post_check_mode == driver.POST_CHECK_MANUAL  # The switch reaches the driver.
