"""Join the parts of the upgrade path into the seams that the routes read.

Why:
    Every part of the upgrade path exists and nothing holds them together. The
    start route reads one callable out of `current_app.config`, finds nothing,
    writes one error line, and answers as if the work started. An operator who
    types CONFIRM therefore reads a normal answer while no upgrade leaves the
    portal. This module builds the missing objects and writes them into the
    configuration, so the route finds the work it already asks for.

    Every import here happens inside a function. Importing this module opens no
    socket, reads no environment file, and connects to no store. A connection
    opens at the first call and never before, so a test that imports the factory
    reaches no network.

    Every value lands with `setdefault`. The wiring fills a gap and never
    replaces a choice, so a test that injects a stand-in keeps the stand-in.

    Warning: the bindings record and the capture job both hold a cloud session,
    and a log of either record can leak its API token. Never log either record
    as a whole.
"""

import logging  # The portal logs with the standard library only.
import threading  # The run mirror below is read by the poll while the driver writes.
import time  # The event window of the settle gate reads the wall clock.
from collections.abc import Callable, Mapping, MutableMapping  # The shapes the driver and the store declare.
from importlib import import_module  # Imports each collaborator late, at the first call.
from types import ModuleType  # The return type of a late import.
from typing import Any  # A late import answers with untyped objects.

from flask import Flask  # The configuration that carries every seam lives on this object.

from .config import read_post_check_mode  # Reads the environment at call time, so an import opens nothing.

logger = logging.getLogger(__name__)  # One logger for each module keeps the source visible in the log.

# The package name comes from the module name, so the imports work whether the
# caller imports `src.upgrade_portal` or `upgrade_portal`. This rule matches
# `app/factory.py`, which reads the same two levels.
PACKAGE_NAME = __name__.rsplit(".", maxsplit=2)[0]  # Two levels up from `app.wiring`.
ROUTES_PACKAGE = __name__.rsplit(".", maxsplit=1)[0] + ".routes"  # A sibling package of this module.

DRIVER_MODULE = f"{PACKAGE_NAME}.upgrade.driver"  # Owns `RunDriver`, `RunDriverDeps`, and `lock_heartbeat`.
PHASE_GATE_MODULE = f"{PACKAGE_NAME}.upgrade.phase_gate"  # Owns the settle gate and its two cloud readers.
EVENTS_MODULE = f"{PACKAGE_NAME}.upgrade.events"  # Owns the reconnect event catalogue.
OPTIONS_MODULE = f"{PACKAGE_NAME}.upgrade.options"  # Maps the stored rows onto the upgrade seam records.
STOP_MODULE = f"{PACKAGE_NAME}.upgrade.stop"  # Owns every cancel call and the outcome record of a stop.
LOCK_MODULE = f"{PACKAGE_NAME}.runtime.lock"  # Owns `LockRecord`, which decodes the session text.
RUNS_MODULE = f"{PACKAGE_NAME}.runtime.runs"  # Owns `RunStateMachine`, the only legal path into `failed`.
CAPTURE_STORE_MODULE = f"{PACKAGE_NAME}.capture.store"  # Owns `bootstrap_storage`, which creates the collections.
IDENTITY_MODULE = f"{PACKAGE_NAME}.runtime.identity"  # Owns the operator record of the present request.
STORE_MODULE = f"{PACKAGE_NAME}.capture.store"  # Owns the document store calls.
ASSEMBLY_MODULE = f"{PACKAGE_NAME}.capture.assembly"  # Owns the one true form of a capture key.
SELECT_ROUTES = f"{ROUTES_PACKAGE}.select"  # Owns the reader of the site lock records of the session.
CAPTURE_ROUTES = f"{ROUTES_PACKAGE}.capture"  # Owns the capture runner seam.
UPGRADE_ROUTES = f"{ROUTES_PACKAGE}.upgrade"  # Owns the reader of the run store seam.

# `upgrade/options.py` and `upgrade/stop.py` both import this module under the
# same absolute name, so the portal already needs it on the import path.
SERVICE_MODULE = "src.firmware.upgrade_service"  # Owns `plan_upgrade` and `invoke_upgrade`.

# These two names repeat the constants of `app/routes/upgrade.py`. The wiring
# reads no route module at import time, and the contract tests repeat the same
# two texts, so one literal in each place keeps the import graph flat.
RUN_STORE_KEY = "RUN_STORE"  # The seam that holds the run record store.
LAUNCHER_KEY = "RUN_LAUNCHER"  # The seam that hands one prepared record to the run driver.
STOP_RUNNER_KEY = "STOP_RUNNER"  # The seam that cancels the remaining devices of one run at the cloud.

POST_CHECK_ORDINAL = 2  # The second capture of a run. `driver.post_check_request` sends this value.

# WHY: The storage bootstrap runs once for each process. Every step of it repeats
# without harm, and a second run costs a database host probe that is not free.
# `prepare_storage` holds the whole reason, and `reset_storage_bootstrap` clears
# this flag for a test and for a worker that meets a database restart.
_STORAGE_PREPARED = False
POST_CHECK_ROLE = "post"  # The role of that second capture.
DEFAULT_TIER = 2  # The standard data tier, which the run record carries.
SITE_SCAN_LIMIT = 200  # The largest number of runs that one site scan reads back.
RUN_FAILED_STAGE = "upgrade"  # The stage name that `upgrade/driver.STAGE_UPGRADE` writes for the same step.

SESSION_FIELD = "session"  # The bindings key that carries the cloud session.
EMAIL_FIELD = "actor_email"  # The bindings key that carries the operator address.
RUNNER_FIELD = "runner"  # The bindings key that carries the bound capture runner.
LOCK_FIELD = "lock"  # The bindings key that carries the decoded site lock record.
STORE_FIELD = "store"  # The bindings key that carries the run store of the seam.

# WHY: `capture/store.connect_database` answers None whenever ArangoDB is
# unreachable, and `capture/store.write_run` still reports success because it
# wrote the CSV backup. The run then reads back as absent. The progress page
# shows no run, the confirm page holds the begin button shaded, and FR-035
# refuses every start, while each write reports that it landed. This mirror
# holds the runs of the present process, so a portal with no database still
# drives a whole upgrade. The database answers first on every read, so a
# mirrored copy can never hide a newer stored row.
_MIRROR: dict[str, dict[str, Any]] = {}  # The runs of this process, oldest first.
_MIRROR_GUARD = threading.Lock()  # The driver thread writes while the poll reads.
MIRROR_LIMIT = 200  # A portal that runs for weeks must not grow without bound.


def mirror_run(run: dict[str, Any]) -> None:
    """Hold one run record in the memory of the present process.

    Why:
        The mirror answers the read that an unreachable database cannot. Only a
        record that already landed reaches this table, so the mirror never
        claims a run that no store holds.

    Args:
        run: The whole record, with the changed fields already in place.
    """
    key = str(run.get("run_id", ""))  # The record names its own key, as the store rows do.
    if not key:  # A record with no key can never be read back, so it belongs in no table.
        return  # The caller already reported the write result of the store itself.
    with _MIRROR_GUARD:  # The poll thread reads this table while the driver writes.
        _MIRROR[key] = dict(run)  # A copy stops a later edit of the caller dictionary.
        while len(_MIRROR) > MIRROR_LIMIT:  # The oldest run leaves first, as a queue does.
            _MIRROR.pop(next(iter(_MIRROR)))  # A dictionary holds its keys in write order.


def mirrored_run(run_id: str) -> dict[str, Any] | None:
    """Return one run record from the memory of the present process.

    Args:
        run_id: The run key.

    Returns:
        A copy of the record, or None when this process holds no such run.
    """
    with _MIRROR_GUARD:  # The driver thread may write while this read runs.
        held = _MIRROR.get(run_id)  # An absent key reads as None, never a fault.
    return dict(held) if held is not None else None  # A copy stops a caller edit of the held record.


def mirrored_site_runs(site_id: str) -> list[dict[str, Any]]:
    """Return every run of one site from the memory of the present process.

    Args:
        site_id: The site that a new run wants to act on.

    Returns:
        A copy of each record of that site, in write order.
    """
    with _MIRROR_GUARD:  # One list copy, so the scan drops the guard before it filters.
        held = list(_MIRROR.values())
    return [dict(row) for row in held if row.get("site_id") == site_id]  # A copy for each row.


def load_module(name: str) -> ModuleType | None:
    """Import one module late and report a failure as None.

    Why:
        This module must open no socket when the factory imports it, so every
        import happens at the first call. A module that is absent or that raises
        while it loads writes one warning, and every other seam keeps working.

    Args:
        name: The absolute module name.

    Returns:
        The module, or None when the import failed.
    """
    try:  # A broken module may raise anything at all while it loads.
        return import_module(name)  # The late import keeps the portal startable.
    except Exception as fault:  # A missing collaborator must never stop the portal.
        logger.warning("wiring: the module %s did not import: %s", name, type(fault).__name__)  # The class only.
        return None  # The caller names the gap in its own answer.


class DocumentRunStore:
    """Read and write one run record in the document store.

    Why:
        `routes/upgrade.py` and `upgrade/driver.py` both declare the same two
        calls, and `capture/store.py` publishes the write alone. Without a read
        the portal keeps every run in the memory of one process, so a second
        worker answers that the run does not exist. This class adds the read and
        holds the two calls together, which is the shape both callers declare.

        Every call catches every fault. A store that does not answer must leave
        the run readable as far as the memory of the driver reaches, and must
        never turn a poll into a 500 answer.
    """

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return one run record, or None when no store and no mirror holds it.

        Why:
            The database answers first, so a mirrored copy can never hide a
            newer stored row. A database that is absent or silent then falls
            back to the mirror, because a run that reads as absent stops the
            whole upgrade journey while every write reports that it landed.

        Args:
            run_id: The run key, which is also the document key.

        Returns:
            A copy of the record, or None.
        """
        store = load_module(STORE_MODULE)  # Late, so the import of this module opens no socket.
        if store is None:  # The store module is absent, so only this process can answer.
            return mirrored_run(run_id)  # The runs of this process still read back.
        try:  # The store sits on a network and may not answer.
            handle: Any = store.connect_database()  # None in standalone mode, or when the server is silent.
            found: Any = None if handle is None else handle.collection(store.RUN_COLLECTION).get(run_id)
        except Exception as fault:  # A poll must answer, whatever the store did.
            logger.warning("wiring: the read of the run %s failed with %s", run_id, type(fault).__name__)
            return mirrored_run(run_id)  # Name the run, never the host.
        return dict(found) if isinstance(found, Mapping) else mirrored_run(run_id)  # A damaged row reads as no row.

    def write_run(self, run: dict[str, Any]) -> bool:
        """Write one whole run record and report the true result.

        Why:
            A record that landed also reaches the mirror, so this process can
            read the run back while the database is unreachable. A write that
            landed nowhere reaches no table, so the mirror never holds a run
            that the operator was told the portal did not keep.

        Args:
            run: The whole record, with the changed fields already in place.

        Returns:
            True when the record reached the database or the fallback file.
        """
        store = load_module(STORE_MODULE)  # Late, for the same reason as the read above.
        run_id = str(run.get("run_id", ""))  # The log line names the run and never the record.
        if store is None:  # The store module is absent, so nothing holds the record.
            return False  # The caller answers the write failure to the operator.
        try:  # The store sits on a network and may not answer.
            answer: Any = store.write_run(dict(run))  # A copy stops a later edit of the caller dictionary.
        except Exception as fault:  # A driver thread must never die on a store fault.
            logger.warning("wiring: the write of the run %s failed with %s", run_id, type(fault).__name__)
            return False  # The driver writes the reason into the record it still holds.
        landed = bool(getattr(answer, "verified", False) or getattr(answer, "backup_written", False))
        if landed:  # The record is durable, so this process may also answer it from memory.
            mirror_run(run)  # The poll then reads the run back with no database at all.
        return landed

    def runs_for_site(self, site_id: str) -> list[dict[str, Any]]:
        """Return one small row for each run that the store holds for one site.

        Why:
            FR-037 asks the portal to find a run that already acts on the site,
            and the two call shape answers one run at a time. This third call is
            optional, and `routes/upgrade.site_run_records` reads it by name, so
            a store that publishes none still works.

        Args:
            site_id: The site that the new run wants to act on.

        Returns:
            One row for each run of that site, or an empty list.
        """
        store = load_module(STORE_MODULE)  # Late, for the same reason as the two calls above.
        if store is None:  # No store module means no scan, and the route continues without one.
            return mirrored_site_runs(site_id)  # The runs of this process still guard FR-037.
        try:  # The scan is one query on a network store.
            page: Any = store.list_runs(store.RunQuery(site_id=site_id, limit=SITE_SCAN_LIMIT))
        except Exception as fault:  # A create call must survive an unreachable store.
            logger.warning("wiring: the site scan of %s failed with %s", site_id, type(fault).__name__)
            return mirrored_site_runs(site_id)  # The lock check of the route still guards a second operator.
        rows = [dict(row) for row in getattr(page, "rows", ())]  # The row holds the run key and the state.
        return rows or mirrored_site_runs(site_id)  # An empty answer may mean a database with nothing in it.


class CaptureBridge:
    """Take the post-check capture on the driver thread and answer with its key.

    Why:
        `driver.CaptureStarter` blocks. The driver counts on the capture to hold
        the thread until the read of the site ends, and it beats the site lock on
        each side of that call. The capture route spawns a worker thread instead,
        so this class calls the runner straight and never spawns a second thread.

        The runner and the four job fields that only a request can supply are
        bound before the driver thread starts, because the worker thread holds no
        request and no application.

        Warning: the held context holds a cloud session, and a log of the
        context or the job can leak its API token. Never log the context or the
        job as a whole.
    """

    def __init__(self, runner: Callable[..., Any] | None, context: Mapping[str, Any]) -> None:
        """Hold the bound runner and the fields that every capture of one run shares.

        Args:
            runner: The callable that reads the whole site. None when no runner bound.
            context: The seven job fields that the request thread already read.
        """
        self._runner = runner  # Bound inside the request, so this object needs no application.
        self._context = dict(context)  # A copy, because the caller may edit its own record.

    def start(self, request: Mapping[str, Any]) -> str | None:
        """Take one capture and return its key.

        Args:
            request: The run key, the ordinal, and the role, from the driver.

        Returns:
            The capture key, or None when the capture did not run.
        """
        run_id = str(request.get("run_id", ""))  # The log line names the run and never the job.
        ordinal = int(request.get("ordinal", POST_CHECK_ORDINAL))  # The post-check is always the second capture.
        capture_id = build_capture_key(run_id, ordinal)  # The assembly module owns the one true form.
        if self._runner is None or not capture_id:  # No runner, or no key builder, means no capture.
            logger.error("wiring: the run %s could not take the post-check capture", run_id)  # Name the gap.
            return None  # The driver writes the reason into the run record.
        try:  # The read of a whole site holds this thread for minutes and touches a network.
            self._runner({**self._context, **self._identity(request, capture_id)})  # Blocks until the read ends.
        except Exception as fault:  # The driver thread must write the reason, never die.
            logger.warning("wiring: the capture of the run %s stopped: %s", run_id, type(fault).__name__)
            return None  # The driver then fails the run at the post-capture stage.
        return capture_id  # The run record now points at the second capture of the pair.

    def _identity(self, request: Mapping[str, Any], capture_id: str) -> dict[str, Any]:
        """Build the four job fields that name one capture inside its run.

        Args:
            request: The run key, the ordinal, and the role, from the driver.
            capture_id: The key that the assembly module built.

        Returns:
            The four naming fields of the job.
        """
        return {  # The seven shared fields and these four make the eleven the collector reads.
            "capture_id": capture_id,  # The key that the store writes and the browser reads.
            "run_id": str(request.get("run_id", "")),  # The run that owns both captures of the pair.
            "ordinal": int(request.get("ordinal", POST_CHECK_ORDINAL)),  # Always 2 for the post-check.
            "role": str(request.get("role", POST_CHECK_ROLE)),  # Always the word post for the post-check.
        }


class CloudUpgradeSubmitter:
    """Send the upgrade of one run to the cloud.

    Why:
        `RunDriverDeps.submit` accepts None, and a driver built that way walks
        every phase and takes both captures while no firmware call ever leaves
        the portal. That silence is the exact defect this module repairs, so the
        wiring always builds this object.

        The class holds the session alone. `upgrade_service.plan_upgrade` is pure
        and groups the devices, and `upgrade_service.invoke_upgrade` performs one
        call for each group and never retries.
    """

    def __init__(self, session: Any) -> None:
        """Hold the cloud session of the operator who confirmed the run.

        Args:
            session: The Mist API session. The request thread read it.
        """
        self._session = session  # Bound inside the request, because the driver thread reads no session.

    def submit(self, record: MutableMapping[str, Any]) -> bool:
        """Send every upgrade call of one run and report whether the cloud took one.

        Args:
            record: The run record. The call writes the cloud identifiers into it.

        Returns:
            True when the cloud accepted at least one call.
        """
        run_id = str(record.get("run_id", ""))  # The log lines name the run and never the record.
        plans = build_plans(record)  # Pure, so this grouping reaches no cloud.
        if not plans:  # A run with no plan must never read as a sent upgrade.
            logger.error("wiring: the run %s built no upgrade plan, so nothing went to the cloud", run_id)
            return False  # The driver fails the run and writes the reason.
        sent = [entry for entry in (self._send(run_id, plan) for plan in plans) if entry is not None]
        record["upgrades"] = sent  # The stop path needs the cloud identifier of each accepted call.
        logger.info("wiring: the run %s sent %s of %s upgrade call(s)", run_id, len(sent), len(plans))
        return bool(sent)  # One accepted call is enough to carry the run into the settle phases.

    def _send(self, run_id: str, plan: Any) -> dict[str, Any] | None:
        """Send one upgrade call and return what the cloud answered.

        Args:
            run_id: The run key, for the log line.
            plan: One group of devices that share a family and a scope.

        Returns:
            The cloud identifier and the counts, or None when the cloud refused.
        """
        service = load_module(SERVICE_MODULE)  # Late, so this module imports no cloud code at load.
        if service is None:  # The upgrade seam is absent, so no call can leave.
            return None  # The caller reads an empty list and fails the run.
        try:  # One cloud call, which may time out or refuse.
            answer: Any = service.invoke_upgrade(self._session, plan)  # Never retries, by design of the seam.
        except Exception as fault:  # One refused group must not hide the groups that worked.
            logger.warning("wiring: the run %s could not send one upgrade call: %s", run_id, type(fault).__name__)
            return None  # The count of sent calls then names the loss.
        if int(getattr(answer, "raw_status", 0)) not in service.ACCEPTED_STATUS:  # The cloud refused this group.
            logger.warning("wiring: the cloud refused one upgrade call of the run %s", run_id)  # No body, no host.
            return None  # A refused group carries no identifier that the stop path could use.
        return _submission_row(answer)  # The record now holds what the stop path needs.


def _submission_row(answer: Any) -> dict[str, Any]:
    """Copy one cloud answer into the plain fields that a store can write.

    Why:
        The seam answers with a frozen record, and the document store writes
        plain values only. This function holds the one mapping between the two.

    Args:
        answer: The `UpgradeSubmission` that the seam returned.

    Returns:
        The cloud identifier, the scope, and the accepted addresses.
    """
    return {  # The stop path reads the identifier and the scope out of this row.
        "upgrade_id": getattr(answer, "upgrade_id", None),  # None when the cloud named no identifier.
        "scope": str(getattr(answer, "scope", "")),  # The word site or the word org.
        "accepted": [str(address) for address in getattr(answer, "accepted", ())],  # The addresses that went out.
        "raw_status": int(getattr(answer, "raw_status", 0)),  # The true status, never a success flag.
    }


def build_plans(record: Mapping[str, Any]) -> tuple[Any, ...]:
    """Group the targets of one run into the cloud calls that the upgrade needs.

    Why:
        The cloud offers one call for each family and scope, so a mixed selection
        needs several calls. The grouping is pure and reaches no cloud, so a run
        that holds a bad option fails here and sends nothing at all.

    Args:
        record: The run record, which holds the targets and the options.

    Returns:
        One plan for each group, or an empty tuple when the grouping failed.
    """
    options = load_module(OPTIONS_MODULE)  # Late, so this module imports no cloud code at load.
    service = load_module(SERVICE_MODULE)  # The same rule for the upgrade seam.
    if options is None or service is None:  # A missing part means no plan and no call.
        return ()  # The caller names the gap and fails the run.
    site_id = str(record.get("site_id", ""))  # Every device of one run belongs to one site.
    try:  # A stored row may hold a value that no rule maps.
        targets: Any = options.to_device_targets(record.get("targets", ()), site_id)  # The seam record shape.
        # The operator chose this moment when they saved the options, and the save call bounded it then. A run
        # that waits for confirmation past its own start time must still upgrade, so no clock reaches this call.
        choices: Any = options.build_options(record.get("options", {}), now=None)  # The four fields the cloud reads.
        plans: Any = service.plan_upgrade(targets, choices, str(record.get("org_id", "")), site_id)
    except Exception as fault:  # A bad option must fail the run and never send a partial upgrade.
        logger.warning("wiring: the run plan failed with %s", type(fault).__name__)  # The class name only.
        return ()  # The caller fails the run before any device changes.
    return tuple(plans)  # One plan for each family and scope of the selection.


def build_capture_key(run_id: str, ordinal: int) -> str:
    """Build the key of one capture of one run.

    Why:
        `routes/capture.build_capture_id` fixes the ordinal at 1, so the
        post-check needs the assembly module straight. Both callers then write
        the same form, and the comparison finds the pair without a search.

    Args:
        run_id: The run key that owns the capture.
        ordinal: The place of the capture inside the run.

    Returns:
        The capture key, or an empty text when the assembly module is absent.
    """
    assembly = load_module(ASSEMBLY_MODULE)  # Late, so this module imports no capture code at load.
    if assembly is None:  # No builder means no key that the store would accept.
        return ""  # The caller reads this as a capture that did not start.
    return str(assembly.capture_key(run_id, ordinal))  # The one true form of `data-model.md`.


def read_lock_record(site_id: str) -> Any:
    """Return the site lock record that the signed session of the operator holds.

    Why:
        The session holds one lock text for each site, and `select.held_record`
        cannot serve here because it demands a lock token in the request body
        while the start body carries the confirmation word alone. This function
        reads the same session field, so the portal keeps one source of the lock
        and never invents a second one.

    Args:
        site_id: The site that the run acts on.

    Returns:
        The decoded lock record, or None when the session holds none.
    """
    routes = load_module(SELECT_ROUTES)  # Late, so the factory imports no route module through this one.
    lock = load_module(LOCK_MODULE)  # Owns the decoder of the stored text.
    if routes is None or lock is None:  # A missing part means the run renews no lock.
        return None  # The caller names the gap and the run still starts.
    stored: Any = read_safely(lambda: routes.stored_lock_records().get(site_id), "the site lock of the session")
    if not isinstance(stored, str):  # The operator holds no lock on this site.
        logger.warning("wiring: the session holds no site lock for the site %s", site_id)  # No token in the log.
        return None  # The browser then renews the lock alone, as it does today.
    return lock.LockRecord.from_json(stored)  # None as well when the text is damaged.


def read_safely(read: Callable[[], Any], subject: str) -> Any:
    """Perform one read of the request and answer None when it did not work.

    Why:
        `routes/upgrade.launch_run` calls the launcher with no guard of its own,
        so a fault here would turn the confirmation into a 500 answer while the
        run record already sits in the store. Every read of the request therefore
        answers None instead of raising, and the caller names the gap.

    Args:
        read: The call that reads one value out of the present request.
        subject: The plain name of the value, for the log line.

    Returns:
        The value, or None when the read did not work.
    """
    try:  # A read outside a request, or a seam that raises, must not stop the run.
        return read()  # The common path, inside the request that the operator confirmed.
    except Exception as fault:  # The launcher must survive every one of these reads.
        logger.warning("wiring: the portal could not read %s: %s", subject, type(fault).__name__)
        return None  # The caller treats this as an absent value.


def bound_store(default: DocumentRunStore) -> Any:
    """Return the run store that the routes read, so the driver writes to the same one.

    Why:
        A test injects its own store into the `RUN_STORE` seam. A driver that
        held a second store would write where the poll route never reads, and the
        run would look frozen. Reading the seam keeps one store for the whole run.

    Args:
        default: The store to use when the seam read did not work.

    Returns:
        The store of the seam, or the given default.
    """
    routes = load_module(UPGRADE_ROUTES)  # Owns the reader of the seam and its own fallback.
    if routes is None:  # No route module means no seam to read.
        return default  # The driver still writes through the document store.
    found = read_safely(routes.run_store, "the run store seam")  # Needs an application, so it reads now.
    return default if found is None else found  # An unset seam already answers with a working store.


def current_operator() -> Any:
    """Return the operator record of the request that runs now.

    Why:
        The launcher and the stop seam both need the signed session of the
        operator. A second reader would answer with a second session, so both
        callers read through this one accessor.

    Returns:
        The operator record, or None when the request holds no signed session.
    """
    identity = load_module(IDENTITY_MODULE)  # Owns the operator record of the present request.
    if identity is None:  # The identity module is absent, so no session reads.
        return None  # Both callers treat this answer as an absent operator.
    return read_safely(identity.current_session, "the operator record")  # None outside a signed request.


def request_bindings(record: Mapping[str, Any]) -> dict[str, Any]:
    """Read every value that only the request thread can supply.

    Why:
        The driver thread holds no request and no application, so the signed
        session, the injected capture runner, the run store seam, and the
        operator record all answer nothing there. The launcher reads all of them
        now, inside the request that the operator confirmed.

        Warning: the answer holds a cloud session, and a log of the whole
        record can leak its API token. Never log this record as a whole.

    Args:
        record: The run record, which names the site of the lock.

    Returns:
        The session, the operator address, the runner, the lock, and the store.
    """
    operator: Any = current_operator()  # The one accessor of the signed session of the operator.
    routes = load_module(CAPTURE_ROUTES)  # Owns the capture runner seam.
    return {  # Five values that the driver thread cannot read for itself.
        SESSION_FIELD: getattr(operator, "cloud_session", None),  # Holds an API token, so it never reaches a log.
        EMAIL_FIELD: getattr(getattr(operator, "owner", None), "actor_email", ""),  # The operator address.
        RUNNER_FIELD: None if routes is None else read_safely(routes.capture_runner, "the capture runner seam"),
        LOCK_FIELD: read_lock_record(str(record.get("site_id", ""))),  # The lock that the heartbeat renews.
        STORE_FIELD: bound_store(DocumentRunStore()),  # The same store that the poll route reads.
    }


def capture_context(record: Mapping[str, Any], bindings: Mapping[str, Any]) -> dict[str, Any]:
    """Build the seven job fields that every capture of one run shares.

    Why:
        The collector reads eleven fields. Seven of them hold for every capture
        of one run, so the wiring builds them once and the bridge adds the four
        that name one capture inside the run.

    Args:
        record: The run record.
        bindings: What the request thread already read.

    Returns:
        The seven shared job fields.
    """
    return {  # Warning: this record holds a cloud session, so no caller may log it whole.
        "org_id": str(record.get("org_id", "")),  # The organization that owns the site.
        "site_id": str(record.get("site_id", "")),  # The site that the capture reads.
        "tier": int(record.get("tier", DEFAULT_TIER)),  # The data tier that the operator chose.
        "cloud_session": bindings.get(SESSION_FIELD),  # The session that the collector reads the site with.
        "actor_email": bindings.get(EMAIL_FIELD, ""),  # The operator that the capture belongs to.
        "org_name": str(record.get("org_name", "")),  # The readable name that a page shows.
        "site_name": str(record.get("site_name", "")),  # The readable name that a page shows.
    }


def build_heartbeat(driver: ModuleType, record: Mapping[str, Any], lock_record: Any) -> Any:
    """Build the one site lock heartbeat that the driver and the settle gate share.

    Why:
        The settle gate blocks for up to 1800 seconds inside one call, and the
        site lock lives 300 seconds. Only the 20-second poll loop inside that
        gate can renew the lock during the wait, so the same object must sit in
        `driver.RunDriverDeps.heartbeat` and in `phase_gate.PhaseGateDeps.progress`.

        One object in both seats keeps one count of the seconds, so the beat
        stays rate limited at its 60-second interval however many callers ask.

    Args:
        driver: The already imported driver module.
        record: The run record, which names the organization and the site.
        lock_record: The decoded site lock, or None when the session holds none.

    Returns:
        The heartbeat, or None when the operator holds no lock on the site.
    """
    if lock_record is None:  # A run with no lock still runs, and the browser renews the lock alone.
        logger.warning("wiring: the run %s holds no site lock, so it renews none", record.get("run_id", ""))
        return None  # Both seats then read None, which both callers accept.
    return driver.lock_heartbeat(record, lock_record)  # The key comes from the organization and the site.


def build_gate_deps(phase_gate: ModuleType, session: Any, record: Mapping[str, Any], heartbeat: Any) -> Any:
    """Build the collaborators of the settle gate of one run.

    Why:
        The gate reads two cloud sources and reports the progress of each round.
        The heartbeat sits in the progress seat, because that seat is the only
        call inside the 20-second poll loop of the gate.

    Args:
        phase_gate: The already imported settle gate module.
        session: The cloud session of the operator.
        record: The run record, which names the organization and the site.
        heartbeat: The site lock heartbeat, or None.

    Returns:
        The dependency record, or None when the event module is absent.
    """
    events = load_module(EVENTS_MODULE)  # Owns the reconnect event catalogue.
    if events is None:  # No catalogue means the gate can read no reconnect signal.
        return None  # The caller names the gap and the run sends nothing.
    org_id = str(record.get("org_id", ""))  # Both readers narrow to this organization.
    reader = phase_gate.CloudReconnectReader(session, org_id, events.EventCatalogue(), time.time)
    counter = phase_gate.CloudStatisticsReader(session, org_id, str(record.get("site_id", "")))
    if heartbeat is None:  # No lock means no beat, so the gate keeps its own log reporter.
        return phase_gate.PhaseGateDeps(event_reader=reader, statistics_reader=counter)
    return phase_gate.PhaseGateDeps(event_reader=reader, statistics_reader=counter, progress=heartbeat)


def build_phase_gate(record: Mapping[str, Any], session: Any, heartbeat: Any) -> Any:
    """Build the settle gate of one run.

    Args:
        record: The run record, which names the organization and the site.
        session: The cloud session of the operator.
        heartbeat: The site lock heartbeat, or None.

    Returns:
        The settle gate, or None when a collaborator module is absent.
    """
    phase_gate = load_module(PHASE_GATE_MODULE)  # Late, so this module imports no cloud code at load.
    if phase_gate is None:  # No gate module means no cascade at all.
        return None  # The caller names the gap and the run sends nothing.
    deps = build_gate_deps(phase_gate, session, record, heartbeat)  # The readers and the progress seat.
    if deps is None:  # The event module is absent.
        return None  # The caller names the gap and the run sends nothing.
    return phase_gate.PhaseSettleGate(deps)  # The deadline stays at the 1800 seconds of the module.


def build_driver_deps(driver: ModuleType, record: Mapping[str, Any], bindings: Mapping[str, Any]) -> Any:
    """Build every collaborator of the driver of one run.

    Why:
        The driver takes one record, because a constructor with a store, a gate,
        a capture, a submitter, a clock, a heartbeat, and a mode would pass the
        parameter limit. The clock stays at the default, which reads the wall
        clock.

    Args:
        driver: The already imported driver module.
        record: The run record.
        bindings: What the request thread already read.

    Returns:
        The dependency record, or None when a collaborator could not be built.
    """
    heartbeat = build_heartbeat(driver, record, bindings.get(LOCK_FIELD))  # One object for two seats.
    gate = build_phase_gate(record, bindings.get(SESSION_FIELD), heartbeat)  # The heartbeat sits in the loop.
    if gate is None:  # No gate means no honest cascade, so the run must not start.
        return None  # The caller writes one error line and sends nothing.
    return driver.RunDriverDeps(  # Every field carries its name, so no positional order can drift.
        store=bindings.get(STORE_FIELD),  # The same store that the routes read through the `RUN_STORE` seam.
        gate=gate,  # Blocks for up to 1800 seconds in each phase.
        capture=CaptureBridge(bindings.get(RUNNER_FIELD), capture_context(record, bindings)),
        submit=CloudUpgradeSubmitter(bindings.get(SESSION_FIELD)),  # Without this the run sends no firmware.
        heartbeat=heartbeat,  # The second seat of the same object. The first seat is the gate progress.
        post_check_mode=read_post_check_mode(),  # The default keeps the automatic second capture of today.
    )


def free_site_lock(record: Mapping[str, Any]) -> None:
    """Give the site back after a run ended before it sent any firmware.

    Why:
        `upgrade/driver.py` frees the lock in the `finally` of a run that
        reached its thread. A run that never reached that thread passes
        through none of it, so without this call the site stays held for the
        whole 3600-second lease while nothing upgrades it.

    Args:
        record: The prepared run record, which names the organization and the
            site.
    """
    site_id = str(record.get("site_id", ""))
    lock = load_module(LOCK_MODULE)  # Owns the key builder and the release.
    held = read_lock_record(site_id)  # None when the session holds no readable lock text.
    if lock is None or held is None:  # Nothing to release, or no way to release it.
        return  # The lease then expires on its own, which is the behavior of a portal with no session.
    key = lock.build_key(str(record.get("org_id", "")), site_id)  # The key the heartbeat would have renewed.
    released = read_safely(lambda: lock.release_site_lock(key, held), "the release of the site lock")
    if released is None:  # A takeover already moved the lock, or the lock store did not answer.
        return  # `read_safely` already named the fault type, and no run holds the site.
    logger.info("wiring: the portal gave the lock of the site %s back", site_id)


def write_failed_state(runs: ModuleType, record: dict[str, Any], reason: str) -> None:
    """Move one run record to the failed state and store it.

    Why:
        The state and the store must agree. A record that reads `failed` in
        this process alone still blocks every later run of the same site,
        because the start route reads the store and not this memory.

    Args:
        runs: The `runtime.runs` module, already imported.
        record: The prepared run record. The call edits it in place.
        reason: One plain sentence for the operator. Never a credential.
    """
    run_id = str(record.get("run_id", ""))
    try:  # A run that already holds a final state accepts no second failure.
        runs.RunStateMachine().fail(record, RUN_FAILED_STAGE, reason)
    except runs.RunTransitionError:  # A final state already, or a state name outside the model.
        logger.warning("wiring: the run %s accepts no failed state, so the wiring wrote none", run_id)
        return  # The state that the record already holds is the one that stands.
    if not bound_store(DocumentRunStore()).write_run(record):  # The same store the start route reads.
        logger.error("wiring: the failed state of the run %s reached no store", run_id)


def abandon_run(record: dict[str, Any], reason: str) -> None:
    """Fail one run that never reached its driver, and give the site back.

    Why:
        `routes/upgrade.launch_run` writes the run record before it calls this
        launcher, and the operator already holds the site lock. A launcher that
        returns without both of these calls leaves the record at
        `upgrade_submitting` for good. `contracts/http-api.md` line 255 then
        answers `upgrade_already_running` to every later start of that site, so
        the site accepts no upgrade again.

        The failed state is honest here. `upgrade/driver.py` sends the firmware
        from its own thread, which this path never reaches, so no device
        received anything.

    Args:
        record: The prepared run record, already written to the store.
        reason: One plain sentence for the operator. Never a credential.
    """
    run_id = str(record.get("run_id", ""))
    runs = load_module(RUNS_MODULE)  # Reachable even when the driver module is not.
    if runs is None:  # Without the state machine the record keeps the state the route wrote.
        logger.error("wiring: no run state module, so the run %s keeps its present state", run_id)
    else:
        write_failed_state(runs, record, reason)
    free_site_lock(record)  # The site goes back even when the state write did not land.


def start_upgrade_run(record: dict[str, Any]) -> None:
    """Start the one thread that owns one prepared run.

    Why:
        `routes/upgrade.launch_run` reads this callable out of the `RUN_LAUNCHER`
        seam. The route calls it inside the request, so this function may read
        the signed session and the injected seams, and the thread it starts needs
        neither.

    Args:
        record: The prepared run record, already written to the store.
    """
    run_id = str(record.get("run_id", ""))  # The log lines name the run and never the record.
    driver = load_module(DRIVER_MODULE)  # Late, so the factory imports no driver at load.
    if driver is None:  # The driver module is absent, so nothing can carry the run.
        logger.error("wiring: no driver module, so the run %s sent nothing", run_id)  # Name the gap.
        abandon_run(record, "The portal found no upgrade driver, so it sent no firmware.")
        return  # The poll then reads a failed run, and the site accepts a new one.
    deps = build_driver_deps(driver, record, request_bindings(record))  # Reads the request while it exists.
    if deps is None:  # A collaborator is missing, and a half built driver would upgrade nothing.
        logger.error("wiring: the run %s could not build its driver, so it sent nothing", run_id)  # Name the gap.
        abandon_run(record, "The portal could not build the upgrade driver, so it sent no firmware.")
        return  # The poll then reads a failed run, and the site accepts a new one.
    driver.RunDriver(deps).start(record)  # A second start of the same run finds the first thread.
    logger.info("wiring: the run %s owns a driver thread", run_id)  # The first line of a healthy run.


def plan_family(plan: Any) -> Any:
    """Return the gateway family that the status read of one plan needs.

    Why:
        `UpgradePlan` holds no family field, and the status read needs one. The
        endpoint of the plan already names the family, because the upgrade seam
        sends every session smart router to the organization call and every other
        device to the site call.

    Args:
        plan: One upgrade plan of the run.

    Returns:
        The family of the plan, or None when the upgrade seam module is absent.
    """
    service = load_module(SERVICE_MODULE)  # Owns both endpoint names and the family list.
    if service is None:  # No seam module means no family and no cancel call.
        return None  # `build_plans` already answered with no plan, so no caller reaches this.
    if str(getattr(plan, "endpoint", "")) == service.ENDPOINT_ORG_SSRS:  # The organization call of a router.
        return service.GatewayFamily.SSR  # The status read then uses the router call.
    return service.GatewayFamily.JUNOS  # Every other device rides the site device call.


def target_for_row(stop: ModuleType, plans: Mapping[frozenset[str], Any], row: Mapping[str, Any]) -> Any:
    """Build one cancel target out of one stored upgrade row.

    Why:
        FR-038f forbids a claim of a cancel that never happened. A row that names
        no cloud identifier, and a row that matches no plan, therefore build no
        target at all, and the stop then claims nothing for that row.

    Args:
        stop: The already imported stop module.
        plans: Every plan of the run, keyed by the address set of the plan.
        row: One stored upgrade row.

    Returns:
        The cancel target, or None when the row reaches no cancel call.
    """
    upgrade_id = row.get("upgrade_id")  # None when the cloud named no identifier.
    addresses = frozenset(str(address) for address in row.get("accepted") or ())  # The devices that went out.
    plan = plans.get(addresses)  # The one group that holds exactly these devices.
    if not upgrade_id or plan is None:  # Nothing here can reach a cancel call at the cloud.
        return None  # The caller drops the row, so the stop claims no cancel for it.
    return stop.StopTarget(plan=plan, upgrade_id=str(upgrade_id), family=plan_family(plan))


def stop_targets(stop: ModuleType, record: Mapping[str, Any]) -> list[Any]:
    """Pair every accepted upgrade call of one run with the plan that sent it.

    Why:
        The cancel call needs the plan and the cloud identifier together, and the
        run record holds the identifier alone. `build_plans` is pure, so a second
        call names the same groups again, and `plan_upgrade` puts each device in
        one group only. The address list of a stored row therefore names one plan
        and no other. A run that started before this repair already holds that
        address list, so no stored record needs a new field.

    Args:
        stop: The already imported stop module.
        record: The run record, which holds the targets, the choices, and the rows.

    Returns:
        One cancel target for each row that names both an identifier and a plan.
    """
    plans: dict[frozenset[str], Any] = {}  # One entry for each group that the run planned.
    for plan in build_plans(record):  # Pure, so this rebuild names the same groups as the start did.
        plans[frozenset(str(mac) for mac in stop.plan_macs(plan))] = plan  # The address set names the group.
    rows = record.get("upgrades") or ()  # Empty until the cloud accepts a first upgrade call.
    built = (target_for_row(stop, plans, row) for row in rows if isinstance(row, Mapping))  # One try for each row.
    return [target for target in built if target is not None]  # A row that names no plan cancels nothing.


def cancel_run(run_id: str) -> Any:
    """Cancel the remaining devices of one run at the cloud.

    Why:
        `routes/upgrade.cancel_outcome` reads this callable out of the
        `STOP_RUNNER` seam and guards it with nothing. Every read here therefore
        answers None instead of raising, and the route then keeps its own honest
        answer, which claims no cancelled device.

    Args:
        run_id: The run key that the operator asked to stop.

    Returns:
        The stop outcome, or None when no cancel call went out.
    """
    stop = load_module(STOP_MODULE)  # Late, so this module imports no cloud code at load.
    store = bound_store(DocumentRunStore())  # The same store that the route and the driver read.
    record = read_safely(lambda: store.read_run(run_id), "the run of the stop")  # None when the run is absent.
    targets = [] if stop is None or record is None else stop_targets(stop, record)  # Empty before a first call.
    session = getattr(current_operator(), "cloud_session", None)  # Holds an API token, so no log holds it.
    if stop is None or not targets or session is None:  # FR-038f: no call went out, so claim no cancel.
        logger.warning("wiring: the stop of the run %s cancelled nothing at the cloud", run_id)  # Name the gap.
        return None  # The route then answers with its own three empty lists.
    runner = stop.stop_run_and_record  # Bound here, because the guard above proved the module loaded.
    word = stop.STOP_CONFIRMATION_TEXT  # The route already read this word, so the seam repeats it.
    reason = "the cancel calls of the stop"  # The subject of the one warning line of a failed cancel.
    return read_safely(lambda: runner(store, run_id, session, targets, word), reason)  # None on any fault.


def install_seams(app: Flask) -> None:
    """Write the store, the launcher, and the stop runner into the configuration.

    Why:
        Each value lands with `setdefault`, so a caller that already chose a
        stand-in keeps it. The contract tests inject their own store, their own
        launcher, and their own stop runner after `create_app` returns, so the
        injected object always wins over the object this function writes.

        The `STOP_RUNNER` seam stayed empty while no run record held a cloud
        identifier. `CloudUpgradeSubmitter.submit` now writes one row for each
        accepted call, so the seam holds `cancel_run`. FR-038f still holds,
        because a run with no accepted call builds no cancel target and
        `cancel_run` then answers None.

        One seam stays empty on purpose. `UPGRADE_OPTIONS_BUILDER` must stay
        empty, because the route resolves that builder from `upgrade/options.py`
        on its own, exactly as the version seam does. A test that names its own
        builder still wins, because the route reads the seam first.

    Args:
        app: The application to fill the seams on.
    """
    app.config.setdefault(RUN_STORE_KEY, DocumentRunStore())  # Replaces the memory store of the route module.
    app.config.setdefault(LAUNCHER_KEY, start_upgrade_run)  # Without this the confirmed run sends nothing.
    app.config.setdefault(STOP_RUNNER_KEY, cancel_run)  # Without this a stop cancels nothing at the cloud.
    prepare_storage()  # Without this no capture can verify, so no upgrade can ever start.
    logger.info("wiring: the portal holds the run store, the run launcher, and the stop runner")  # One per start.


def prepare_storage() -> None:
    """Create the collections and the indexes that the capture store needs.

    Why:
        `capture/store.py:637 bootstrap_storage` states that "the portal calls
        this function on every start". No caller existed, so the collections
        never appeared. A capture then wrote through the router, which answers a
        success envelope after a file fallback, and the read-back of the store
        reported `document_absent`. Every capture therefore failed to verify.

        That single gap closed the whole write half of the feature. The start
        route refuses an upgrade until the run holds a verified pre-check
        capture, so no upgrade could ever start against a fresh database.

        The call cannot stop the portal. A database that is out of reach must
        still leave a portal that reads, because the site pages and the history
        need no store. `bootstrap_storage` already answers a report rather than
        raising for that case, and this function guards the rest.

        The bootstrap runs once for each process and not once for each
        application. Every step of it repeats without harm, so a second run adds
        nothing. A second run does cost a database probe, and that probe is not
        free: `DatabaseConfig.from_env` resolves the database host and the lock
        store host to decide the standalone mode, and `connect_database` repeats
        that work whenever the store was out of reach before.

        Warning: a contract test builds one application for each test. Without
        this guard a run of the contract suite paid one host probe for each of
        those applications. On a runner where the host name does not resolve
        quickly, each probe took about 20 seconds, and the whole job reached its
        15 minute limit and reported as a test failure. Issue #2036 holds that
        record.
    """
    global _STORAGE_PREPARED
    if _STORAGE_PREPARED:  # One process needs the collections built one time.
        return
    _STORAGE_PREPARED = True  # Set before the call, so a raise never leaves a retry loop.
    store = load_module(CAPTURE_STORE_MODULE)  # None while the capture store is absent.
    if store is None:  # A portal with no capture store still serves every read page.
        logger.warning("wiring: the capture store is absent, so the portal created no collection")
        return
    try:  # A store that cannot answer must not stop a portal that still reads.
        report = store.bootstrap_storage()
    except Exception as fault:  # The class name alone, because a driver message may carry a connection string.
        logger.warning("wiring: the storage bootstrap failed (%s)", type(fault).__name__)
        return
    logger.info("wiring: the storage bootstrap reported %s", report)


def reset_storage_bootstrap() -> None:
    """Let the next application build the collections again.

    Why:
        `prepare_storage` runs once for each process. A test that wants to read
        the bootstrap call needs the guard cleared first, and a long-lived worker
        needs it cleared after a database restart.
    """
    global _STORAGE_PREPARED
    _STORAGE_PREPARED = False
