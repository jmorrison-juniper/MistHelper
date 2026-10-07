"""Join the parts of the upgrade path into the seams that the routes read.

Why:
    Every part of the upgrade path exists and nothing holds them together. The
    start route reads one callable out of `current_app.config`, finds nothing,
    writes one error line, and answers as if the work started. An operator who
    types CONFIRM therefore reads a normal answer while no upgrade leaves the
    portal. This module builds the missing objects and writes them into the
    configuration, so the route finds the work it already asks for.

    The database classes load with this module, but their constructors run only
    through the request provider. Importing this module opens no socket, reads
    no environment file, and connects to no store.

    Every value lands with `setdefault`. The wiring fills a gap and never
    replaces a choice, so a test that injects a stand-in keeps the stand-in.

    Warning: the bindings record and the capture job both hold a cloud session,
    and a log of either record can leak its API token. Never log either record
    as a whole.
"""

import logging  # The portal logs with the standard library only.
import threading  # The run mirror below is read by the poll while the driver writes.
import time  # The event window of the settle gate reads the wall clock.
from collections.abc import Callable, Mapping, MutableMapping, Sequence  # The shapes the driver and the store declare.
from dataclasses import dataclass  # Holds one request-owned resource graph.
from importlib import import_module  # Imports each collaborator late, at the first call.
from types import ModuleType  # The return type of a late import.
from typing import Any  # A late import answers with untyped objects.

from flask import Flask, current_app, g  # The configuration and request context carry every seam.

from src.foundation.persistence.db import DatabaseConfig  # Build the real database settings.
from src.foundation.persistence.db.router import DatabaseRouter  # Use the real database lifecycle boundary.
from src.interfaces.portals.upgrade_portal.api.run_controls import (
    E2EFactoryOverrides,
)  # Type the complete test-only dependency set.
from src.interfaces.portals.upgrade_portal.app.config import (
    read_post_check_mode,
)  # Reads the environment at call time, so an import opens nothing.
from src.interfaces.portals.upgrade_portal.persistence.actions import (
    ActionRepository,
)  # Keep run actions in the authoritative document store.

logger = logging.getLogger(__name__)  # One logger for each module keeps the source visible in the log.

# The package name comes from the module name, so the imports work whether the
# caller imports `src.interfaces.portals.upgrade_portal` or `upgrade_portal`. This rule matches
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
# Phase 2 T-006/T-008: Module paths for Phase 2 services.
CAPTURE_SERVICE_MODULE = f"{PACKAGE_NAME}.capture.service"  # Owns CaptureService with pre/post-upgrade capture capture.
UPGRADE_SERVICE_MODULE = (
    f"{PACKAGE_NAME}.upgrade.service"  # Owns UpgradeService with serial/parallel firmware upgrade orchestration.
)
# Phase 3 T-010/T-012: Module paths for Phase 3 services (settle gate, comparison).
SETTLE_GATE_SERVICE_MODULE = (
    f"{PACKAGE_NAME}.settle.service"  # Owns SettleGateService for post-upgrade device validation.
)
COMPARISON_SERVICE_MODULE = (
    f"{PACKAGE_NAME}.compare.service"  # Owns ComparisonService for pre/post-upgrade capture comparison.
)

# `upgrade/options.py` and `upgrade/stop.py` both import this module under the
# same absolute name, so the portal already needs it on the import path.
SERVICE_MODULE = "src.operations.execution.firmware.upgrade_service"  # Owns `plan_upgrade` and `invoke_upgrade`.

# These two names repeat the constants of `app/routes/upgrade.py`. The wiring
# reads no route module at import time, and the contract tests repeat the same
# two texts, so one literal in each place keeps the import graph flat.
RUN_STORE_KEY = "RUN_STORE"  # The seam that holds the run record store.
LAUNCHER_KEY = "RUN_LAUNCHER"  # The seam that hands one prepared record to the run driver.
STOP_RUNNER_KEY = "STOP_RUNNER"  # The seam that cancels the remaining devices of one run at the cloud.
PRECHECK_ADOPTER_KEY = "PRECHECK_ADOPTER"  # The seam that reads and links a standalone pre-check.
# Phase 2 T-006/T-008/T-009: Phase 2 service seams for capture and upgrade orchestration.
CAPTURE_SERVICE_KEY = "CAPTURE_SERVICE"  # The seam that holds the CaptureService for pre/post-upgrade captures.
UPGRADE_SERVICE_KEY = "UPGRADE_SERVICE"  # The seam that holds the UpgradeService for firmware upgrade orchestration.
# Phase 3 T-010/T-012: Phase 3 service seams for settle gate and comparison.
SETTLE_GATE_SERVICE_KEY = "SETTLE_GATE_SERVICE"  # The seam that holds SettleGateService.
COMPARISON_SERVICE_KEY = "COMPARISON_SERVICE"  # The seam that holds ComparisonService.
PORTAL_DEPENDENCY_PROVIDER_KEY = "PORTAL_DEPENDENCY_PROVIDER"  # Holds lazy request resource construction.

POST_CHECK_ORDINAL = 2  # The second capture of a run. `driver.post_check_request` sends this value.

# Issue #4020: the driver names a cascade phase, and an upgrade plan names a
# device family. This map is the one join between the two words, so the phase
# loop and the submitter never disagree about which firmware write belongs to
# which gate. The client phase holds no device, so it takes no entry.
PLAN_PHASE_BY_DEVICE_TYPE: Mapping[str, str] = {
    "gateway": "gateways",  # Every other family of the site sits downstream of this one.
    "switch": "switches",  # The access points and the wired clients sit downstream of this one.
    "ap": "aps",  # Only the wireless clients sit downstream of this one.
}

# Issue #4020: these two sentences reach the run page, so they name the loss in
# plain words and hold no host, no token, and no cloud body.
NO_PLAN_REASON = "The run built no upgrade plan, so no firmware call left the portal."
PHASE_REFUSED_REASON = "The cloud refused the {phase} upgrade call, so the run stops before the next phase."
UNROUTABLE_PLAN_REASON = (
    "The run built an upgrade plan with no single supported device family, so no firmware call left the portal."
)
STOP_REQUESTED_REASON = "An operator asked to stop the run before the next firmware call."
ACCEPTED_ROW_STORE_REASON = (
    "The portal could not persist an accepted upgrade call, so the run stops before the next firmware call."
)

# WHY: The storage bootstrap runs once for each process. Every step of it repeats
# without harm, and a second run costs a database host probe that is not free.
# `prepare_storage` holds the whole reason, and `reset_storage_bootstrap` clears
# this flag for a test and for a worker that meets a database restart.
_STORAGE_PREPARED = False
POST_CHECK_ROLE = "post"  # The role of that second capture.
DEFAULT_TIER = 2  # The standard data tier, which the run record carries.
EXTRA_TIER = 3  # The tier that also reads the ports, the radios, and the alarms.
KNOWN_TIERS = (DEFAULT_TIER, EXTRA_TIER)  # Issue #2640: every tier a stored capture may name.
SITE_SCAN_LIMIT = 200  # The largest number of runs that one site scan reads back.
RUN_FAILED_STAGE = "upgrade"  # The stage name that `upgrade/driver.STAGE_UPGRADE` writes for the same step.

SESSION_FIELD = "session"  # The bindings key that carries the cloud session.
EMAIL_FIELD = "actor_email"  # The bindings key that carries the operator address.
RUNNER_FIELD = "runner"  # The bindings key that carries the bound capture runner.
LOCK_FIELD = "lock"  # The bindings key that carries the decoded site lock record.
STORE_FIELD = "store"  # The bindings key that carries the run store of the seam.
APP_CONTEXT_FIELD = "app_context"  # The bindings key that rebuilds a context in the driver thread.


class PortalDependencyError(RuntimeError):
    """Report that an authenticated request cannot construct its resources."""


class PortalAuthenticationError(PortalDependencyError):
    """Report that the request has no usable authenticated Mist session."""


@dataclass(frozen=True, slots=True)
class PortalRequestDependencies:
    """Hold one authenticated operator and its request-owned database router."""

    operator: Any  # Keep the validated operator record for future request integrations.
    cloud_session: Any  # Borrow the registry-owned Mist session without taking ownership.
    database_router: DatabaseRouter  # Own one real router until Flask request teardown.


class PortalDependencyProvider:
    """Construct one authenticated resource graph when a request first needs it."""

    def resolve(self) -> PortalRequestDependencies:
        """Return one cached resource graph for the active request."""
        cached = getattr(g, "portal_dependencies", None)  # Reuse one graph within the request only.
        if isinstance(cached, PortalRequestDependencies):  # A second integration must use the same router.
            return cached  # Flask teardown owns the single cached router.
        operator = current_operator()  # Validate the signed browser and registry record before storage access.
        cloud_session = getattr(operator, "cloud_session", None)  # Read the borrowed session without copying it.
        if operator is None or not self._session_is_usable(cloud_session):  # Refuse absent and stale identities.
            logger.warning("wiring: request dependency authentication failed")  # Record no identity detail.
            raise PortalAuthenticationError("The operator session is unavailable.")  # Storage stays unopened.
        dependencies = self._construct(operator, cloud_session)  # Build the owned resource after authentication.
        g.database_router = dependencies.database_router  # Existing factory teardown closes this owned router.
        g.portal_dependencies = dependencies  # Keep repeated resolution inside this request stable.
        return dependencies  # Future issue #3977 integrations read this explicit boundary.

    @staticmethod
    def _construct(operator: Any, cloud_session: Any) -> PortalRequestDependencies:
        """Construct one real database router for an authenticated request."""
        logger.info("wiring: construct the request database router")  # Record the external resource action.
        try:
            database_config = DatabaseConfig.from_env()  # Resolve the real database settings at request time.
            database_router = DatabaseRouter(database_config)  # Open the real request-owned database boundary.
        except Exception as fault:
            logger.error(
                "wiring: request database router construction failed (%s)",
                type(fault).__name__,
            )  # Report the safe fault type only.
            raise PortalDependencyError("The portal database resources are unavailable.") from fault
        dependencies = PortalRequestDependencies(
            operator=operator,
            cloud_session=cloud_session,
            database_router=database_router,
        )  # Bind the borrowed and owned resources in one immutable record.
        logger.debug("wiring: constructed one request database router")  # Confirm one owned resource.
        return dependencies  # The caller publishes ownership only after construction succeeds.

    @staticmethod
    def _session_is_usable(cloud_session: Any) -> bool:
        """Return whether the borrowed Mist session still exposes request methods."""
        return callable(getattr(cloud_session, "get", None)) and callable(
            getattr(cloud_session, "post", None)
        )  # Both methods exist on an active mistapi session.


def request_dependencies() -> PortalRequestDependencies:
    """Resolve the authenticated request resources for future route integration."""
    provider = current_app.config.get(PORTAL_DEPENDENCY_PROVIDER_KEY)  # Read the installed construction rule.
    if not isinstance(provider, PortalDependencyProvider):  # A missing provider is an application wiring fault.
        logger.error("wiring: the request dependency provider is unavailable")  # Name the failed boundary.
        raise PortalDependencyError("The portal request resources are unavailable.")  # Refuse an invalid setup.
    return provider.resolve()  # Construction and caching stay inside one lifecycle owner.


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


def forget_run(run_id: str) -> None:
    """Remove one run from the process mirror after durable cleanup."""
    key = str(run_id)  # Use the same key as the document store.
    with _MIRROR_GUARD:  # The poll thread may read while cleanup removes the entry.
        _MIRROR.pop(key, None)  # An absent key already satisfies the cleanup result.


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
        the run readable as far as the memory of the driver reaches. The store
        must never turn a poll into a 500 answer.
    """

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return one run record, or None when no store and no mirror holds it.

        Why:
            The database answers first, so a mirrored copy can never hide a
            newer stored row. A database that is absent or silent then falls
            back to the mirror. A run that reads as absent stops the whole
            upgrade journey while every write reports that it landed.

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

    def delete_run(self, run_id: str) -> bool:
        """Delete one planned run and remove its process mirror."""
        store = load_module(STORE_MODULE)  # Load the production database boundary only when cleanup runs.
        if store is None:  # A missing store cannot prove durable cleanup.
            return False  # Fail closed and retain the plan.
        try:  # The store owns the database delete operation.
            deleted = bool(store.delete_run(run_id))  # Remove only the requested durable run.
        except Exception as fault:  # A cleanup fault must remain visible to the caller.
            logger.warning("wiring: the delete of run %s failed with %s", run_id, type(fault).__name__)
            return False  # Do not remove the mirror after an unverified delete.
        if deleted:  # The durable record no longer exists.
            forget_run(run_id)  # Prevent a database outage from resurrecting the deleted plan.
        return deleted  # Report the verified cleanup result.

    def compare_and_set_run(
        self,
        run_id: str,
        expected_version: int,
        replacement: dict[str, Any],
    ) -> bool:
        """Replace one database run only when its application version matches."""
        store = load_module(STORE_MODULE)  # Load the production database boundary without a socket at import.
        if store is None:  # A mirror cannot coordinate two workers.
            return False  # Fail closed when the production store is absent.
        try:  # The database action is one atomic AQL statement.
            database: Any = store.connect_database()  # Open the same database that stores run documents.
            if database is None:  # A file fallback cannot provide compare-and-set.
                return False  # Fail closed instead of claiming an atomic update.
            query = (
                "FOR run IN @@collection "
                "FILTER run._key == @key AND run.record_version == @expected "
                "REPLACE run WITH @replacement IN @@collection RETURN NEW"
            )  # Arango evaluates the filter and replacement in one transaction.
            bind_vars = {  # Bind every value, including the collection name.
                "@collection": store.RUN_COLLECTION,
                "key": run_id,
                "expected": expected_version,
                "replacement": dict(replacement),
            }
            logger.info("wiring: compare and replace the run %s", run_id)  # Log before the atomic action.
            rows = list(database.aql.execute(query, bind_vars=bind_vars))  # Run one atomic conditional replace.
        except Exception as fault:  # A failed coordination write must stop the cloud action.
            logger.warning("wiring: the compare and replace of run %s failed with %s", run_id, type(fault).__name__)
            return False  # Do not use the mirror or the backup file for coordination.
        if not rows:  # A stale version or absent row changed nothing.
            return False  # Report the lost comparison without updating the mirror.
        mirror_run(replacement)  # Cache only a database-confirmed replacement.
        logger.debug("wiring: the compare and replace of run %s succeeded", run_id)  # Log after the action.
        return True  # The database returned the replacement document.

    def runs_for_site(self, site_id: str) -> list[dict[str, Any]]:
        """Return one small row for each run that the store holds for one site.

        Why:
            FR-037 asks the portal to find a run that already acts on the site.
            The two call shape answers one run at a time. This third call is
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
            logger.info("wiring: scan stored runs for site %s", site_id)  # Log before the document store query.
            page: Any = store.list_runs(store.RunQuery(site_id=site_id, limit=SITE_SCAN_LIMIT))
        except Exception as fault:  # A create call must survive an unreachable store.
            logger.warning("wiring: the site scan of %s failed with %s", site_id, type(fault).__name__)
            return mirrored_site_runs(site_id)  # The lock check of the route still guards a second operator.
        if not page.database_available:  # An unavailable database gives the mirror authority for this process.
            return mirrored_site_runs(site_id)  # The local runs still guard FR-037 in standalone mode.
        rows = [dict(row) for row in page.runs]  # The page contract holds its stored run records in `runs`.
        logger.debug("wiring: the site scan of %s found %d stored runs", site_id, len(rows))  # Log the result count.
        return rows  # An available empty page proves that the database holds no matching run.


def precheck_tier_number(raw: Any) -> int:
    """Return one stored capture tier as a whole number.

    Why:
        Issue #2640. The run takes the tier of the pre-check capture it adopts.
        A stored row can hold the tier as text after a hand edit, and a damaged
        row can hold any shape. A capture must still start, so an unusable
        value reads as the standard tier instead of raising.

        A `True` counts as the number 1 in Python, so the boolean test comes
        first. Without it a stored `true` would read as an unknown tier.

    Args:
        raw: The tier field of one stored capture row.

    Returns:
        The tier when the row names a known tier, or the standard tier.
    """
    if isinstance(raw, bool):  # A boolean must never read as the tier number 1.
        return DEFAULT_TIER  # The standard tier is the safe answer for a damaged row.
    try:  # A stored row may hold the tier as text.
        number = int(raw)  # The run record holds a number, so the text form converts here.
    except (TypeError, ValueError):  # A value of another shape is a defect of the writer, not a fault.
        return DEFAULT_TIER  # The run then keeps the standard tier.
    return number if number in KNOWN_TIERS else DEFAULT_TIER  # An unknown number falls back the same way.


class StandalonePrecheckAdopter:
    """Read the newest standalone pre-check of a site and link it to a run.

    Why:
        Delta H3 asks the run create call to adopt the newest verified
        standalone pre-check of the site. This adopter reads that pre-check from
        the capture store and writes the pre edge, so the route stays free of a
        direct store call. Every call catches every fault, because a create call
        must survive an unreachable store (FR-103).
    """

    def newest_precheck(self, site_id: str) -> str:
        """Return the newest standalone pre-check key of one site.

        Args:
            site_id: The site the new run belongs to.

        Returns:
            The pre-check key, or an empty string when the site holds none.
        """
        return self.newest_precheck_tier(site_id)[0]  # The pair reader owns the one store call.

    def newest_precheck_tier(self, site_id: str) -> tuple[str, int]:
        """Return the key and the tier of the newest standalone pre-check.

        Why:
            Issue #2640. The run took the tier of the request body, and the
            upgrade button sends no tier. A run that adopted a tier 3 pre-check
            therefore kept tier 2, and the post-check capture then read no
            radio row and no alarm row. The comparison could not name a radio
            that stayed down after a firmware write.

        Args:
            site_id: The site the new run belongs to.

        Returns:
            The pre-check key and its tier. The key is an empty string and the
            tier is the standard tier when the site holds no pre-check.
        """
        store = load_module(STORE_MODULE)  # Late, so the import of this module opens no socket.
        if store is None:  # The store module is absent, so no site holds a pre-check to adopt.
            return "", DEFAULT_TIER  # The route then creates a run with no adopted pre-check.
        try:  # The store sits on a network and may not answer.
            found: Any = store.latest_standalone_precheck(site_id)  # None when the site holds none.
        except Exception as fault:  # A create call must survive an unreachable store.
            logger.warning("wiring: the pre-check read of site %s failed with %s", site_id, type(fault).__name__)
            return "", DEFAULT_TIER  # The run still stands, and the operator saves a pre-check later.
        if not isinstance(found, Mapping):  # A damaged row reads as no pre-check at all.
            return "", DEFAULT_TIER  # The run then keeps the tier that the request named.
        return str(found.get("capture_id", "")), precheck_tier_number(found.get("tier"))

    def write_capture_edge(self, run_id: str, capture_id: str, role: str) -> None:
        """Write one edge from a run to its adopted pre-check.

        Args:
            run_id: The new run the edge starts at.
            capture_id: The adopted pre-check the edge points at.
            role: The role the edge carries, ``pre`` for an adoption.
        """
        store = load_module(STORE_MODULE)  # Late, for the same reason as the read above.
        if store is None:  # No store module means no edge, and the run still stands.
            return  # The history view then shows the run with no linked pre-check.
        edge = {"run_id": run_id, "capture_id": capture_id, "role": role}  # `write_edge` reads these three fields.
        logger.info("wiring: link the run %s to the pre-check %s", run_id, capture_id)  # BEFORE the edge write.
        try:  # The store sits on a network and may not answer.
            result: Any = store.write_edge(edge)  # The writer proves the edge with a read-back.
        except Exception as fault:  # A create call must survive an unreachable store.
            logger.warning("wiring: the pre edge of the run %s failed with %s", run_id, type(fault).__name__)
            return  # A lost edge hides no capture, because the run names its pre-check field too.
        logger.debug("wiring: the pre edge of the run %s verified %s", run_id, getattr(result, "verified", False))


class CaptureBridge:
    """Take the post-check capture on the driver thread and answer with its key.

    Why:
        `driver.CaptureStarter` blocks. The driver counts on the capture to hold
        the thread until the read of the site ends. The capture beats the site
        lock on each side of that call. The capture route spawns a worker thread
        instead, so this class calls the runner straight and never spawns a
        second thread.

        The runner and the four job fields that only a request can supply are
        bound before the driver thread starts. The worker thread holds no
        request and no application.

        Warning: the held context holds a cloud session, and a log of the
        context or the job can leak its API token. Never log the context or the
        job as a whole.
    """

    def __init__(
        self,
        runner: Callable[..., Any] | None,
        context: Mapping[str, Any],
        app_context: Callable[[], Any] | None = None,
    ) -> None:
        """Hold the bound runner and the fields that every capture of one run shares.

        Args:
            runner: The callable that reads the whole site. None when no runner bound.
            context: The seven job fields that the request thread already read.
            app_context: The factory for a fresh Flask application context.
        """
        self._runner = runner  # Bound inside the request, so this object needs no application.
        self._context = dict(context)  # A copy, because the caller may edit its own record.
        self._app_context = app_context  # The stored-status fallback needs an application context.

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
        routes = load_module(CAPTURE_ROUTES)  # The route owns the progress and stored-status seams.
        if routes is None:  # A missing route cannot open or verify the capture.
            logger.error("wiring: the capture route is absent for run %s", run_id)  # Name the missing seam.
            return None  # The driver writes the failure into the run record.
        job = {**self._context, **self._identity(request, capture_id)}  # Build the complete collector job.
        routes.open_progress(capture_id, routes.opening_record(job))  # Make progress visible before the runner.
        try:  # The read of a whole site holds this thread for minutes and touches a network.
            self._runner(job)  # Blocks until the read ends.
        except Exception as fault:  # The driver thread must write the reason, never die.
            logger.warning("wiring: the capture of the run %s stopped: %s", run_id, type(fault).__name__)
            routes.record_status(  # Keep the failed state visible after a runner fault.
                capture_id,
                state=routes.STATE_FAILED,
                message=routes.FAILED_MESSAGE,
            )
            return None  # The driver then fails the run at the post-capture stage.
        final = self._final_status(routes, capture_id)  # Read the last live or stored capture status.
        if final.get("state") != routes.STATE_VERIFIED or final.get("verified") is not True:  # Require both proofs.
            logger.warning("wiring: the post-check capture of run %s did not verify", run_id)  # Name the failed proof.
            return None  # The driver must not point at unverified evidence.
        logger.debug("wiring: the post-check capture of run %s verified", run_id)  # Confirm the returned key.
        return capture_id  # The run record now points at verified evidence.

    def _final_status(self, routes: Any, capture_id: str) -> dict[str, Any]:
        """Read the final live status, or the stored status after progress trim."""
        live = routes.read_progress(capture_id)  # The live record is the normal completion path.
        if live is not None:  # A live record answers without a database context.
            return live  # Keep the final state and its reason unchanged.
        if self._app_context is None:  # Tests and detached callers may have no stored-status context.
            return {}  # No proof means no capture key.
        with self._app_context():  # The stored reader needs the Flask configuration.
            stored = routes.stored_body(capture_id)  # The durable capture is the fallback proof.
        return stored or {}  # A missing stored record cannot verify the capture.

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
    """Send the upgrade of one phase of one run to the cloud.

    Why:
        `RunDriverDeps.submit` accepts None, and a driver built that way walks
        every phase and takes both captures while no firmware call ever leaves
        the portal. That silence is the exact defect this module repairs, so the
        wiring always builds this object.

        The class holds the session and the durable run store.
        `upgrade_service.plan_upgrade` is pure and groups the devices, and
        `upgrade_service.invoke_upgrade` performs one call for each group and
        never retries.

        Issue #4020: the driver now calls this class once for each phase, and a
        phase sends firmware only after the phase above it settled. One refused
        group inside a phase stops that phase at once and leaves every later
        group of the phase unsent, because the operator cannot tell a refused
        write from a write that the cloud took and lost. Nothing retries, and
        the rows of the groups the cloud already accepted stay in the record so
        the stop path can still cancel them.
    """

    def __init__(self, session: Any, store: Any) -> None:
        """Hold the cloud session and the durable run store.

        Args:
            session: The Mist API session. The request thread read it.
            store: The store that carries accepted rows and stop requests.
        """
        self._session = session  # Bound inside the request, because the driver thread reads no session.
        self._store = store  # The submitter persists each accepted row before another destructive write.

    def submit_phase(self, record: MutableMapping[str, Any], phase: str) -> str | None:
        """Send every upgrade call of one phase and report why the run must stop.

        Args:
            record: The run record. The call writes the cloud identifiers into it.
            phase: The phase name, one of the members of the driver phase order.

        Returns:
            None when the run may carry on, or one plain sentence that names why
            the run must stop before the next phase.
        """
        run_id = str(record.get("run_id", ""))  # The log lines name the run and never the record.
        plans = build_plans(record)  # Pure, so this grouping reaches no cloud.
        if not plans:  # A run with no plan must never read as a sent upgrade.
            logger.error("wiring: the run %s built no upgrade plan, so nothing went to the cloud", run_id)
            return NO_PLAN_REASON  # The driver fails the run and writes this reason.
        routes = tuple(plan_phase(plan) for plan in plans)  # Validate every plan before the first cloud write.
        if any(not route for route in routes):  # An unknown or mixed family has no safe cascade position.
            logger.error("wiring: the run %s built an upgrade plan with no supported phase", run_id)
            return UNROUTABLE_PLAN_REASON  # The driver records the failure and sends no plan.
        mine = tuple(plan for plan, route in zip(plans, routes, strict=True) if route == phase)
        if not mine:  # The site holds no device of this family, so this phase sends nothing.
            logger.info("wiring: the run %s holds no upgrade plan for the %s phase", run_id, phase)
            return None  # An empty family is no failure, and the driver marks the phase skipped.
        return self._send_phase(run_id, record, phase, mine)  # The ordered, fail-closed send of one phase.

    def _send_phase(
        self,
        run_id: str,
        record: MutableMapping[str, Any],
        phase: str,
        plans: tuple[Any, ...],
    ) -> str | None:
        """Send the plans of one phase and stop at the first refusal.

        Why:
            A refused group of a phase means the cloud would not take that
            firmware write. Sending the rest of the phase afterwards would start
            a partial upgrade of a family that the operator believes refused, so
            this loop ends at the first refusal and writes nothing more.

        Args:
            run_id: The run key, for the log line.
            record: The run record, which collects the accepted rows.
            phase: The phase name, for the reason sentence.
            plans: The plans of this phase, in the canonical order.

        Returns:
            None when every plan of the phase went out, or the stop reason.
        """
        for plan in plans:  # The order is the order that `plan_upgrade` fixed.
            stop_reason = self._stop_reason(record)  # A durable operator request blocks this next write.
            if stop_reason is not None:
                return stop_reason  # The driver then uses the normal stopped-run finalization path.
            row = self._send(run_id, plan)
            if row is None:  # The cloud refused or faulted, so this phase stops here.
                self._keep(record, ())  # Keep the stable empty-row shape when the first call was refused.
                logger.error("wiring: the run %s stops, because the %s phase lost one upgrade call", run_id, phase)
                return PHASE_REFUSED_REASON.format(phase=phase)  # The driver fails the run with this sentence.
            store_reason = self._persist_row(record, row)  # The identifier lands before the next plan can leave.
            if store_reason is not None:
                return store_reason  # An unrecorded accepted call makes every later destructive write unsafe.
        logger.info("wiring: the run %s sent %s upgrade call(s) for the %s phase", run_id, len(plans), phase)
        return None  # The driver now settles this phase before the next one sends anything.

    def _stop_reason(self, record: MutableMapping[str, Any]) -> str | None:
        """Copy a durable stop request into the driver record before a cloud write.

        Args:
            record: The run record that the driver owns.

        Returns:
            The visible stop reason, or None when no operator requested a stop.
        """
        run_id = str(record.get("run_id", ""))  # The store key and the safe log value are the run identifier.
        stored = self._store.read_run(run_id)  # The route writes the stop request into this durable record.
        request = stored.get("stop_request") if isinstance(stored, Mapping) else record.get("stop_request")
        if request is None:
            return None  # The next version group may leave only while no durable stop exists.
        record["stop_request"] = request  # The driver then preserves the request through every later save.
        logger.info("wiring: the run %s stops before its next firmware call", run_id)
        return STOP_REQUESTED_REASON

    def _persist_row(self, record: MutableMapping[str, Any], row: Mapping[str, Any]) -> str | None:
        """Persist one accepted row before another destructive call can start.

        Args:
            record: The run record that collects accepted rows.
            row: The accepted cloud response.

        Returns:
            None when the row is durable, or one reason when persistence failed.
        """
        self._keep(record, (row,))  # The in-memory record keeps every accepted family and version group.
        stop_reason = self._stop_reason(record)  # Preserve a stop that arrived while the cloud call was in flight.
        if self._store.write_run(dict(record)):
            return stop_reason  # The caller reports the stop after the accepted row becomes durable.
        logger.error("wiring: the run %s could not persist one accepted upgrade call", record.get("run_id", ""))
        return ACCEPTED_ROW_STORE_REASON

    @staticmethod
    def _keep(record: MutableMapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> None:
        """Add the accepted rows of one phase to the record.

        Why:
            Issue #4020 sends one phase at a time, so a later phase must never
            drop the identifiers of the phase above it. The stop path cancels
            every accepted call, and a replaced list would hide the gateways
            that are already writing firmware.

        Args:
            record: The run record.
            rows: The rows of this phase that the cloud accepted.
        """
        held = record.get("upgrades")  # A first phase finds nothing, and a later phase finds the earlier rows.
        kept = list(held) if isinstance(held, Sequence) and not isinstance(held, str | bytes) else []
        kept.extend(dict(row) for row in rows)  # Plain values only, because the document store writes plain values.
        record["upgrades"] = kept  # The stop path needs the cloud identifier of every accepted call.

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


def plan_phase(plan: Any) -> str:
    """Return the cascade phase that one upgrade plan belongs to.

    Why:
        The driver names a phase, and a plan names a device family. Issue #4020
        joins the two here, so the submitter and the phase loop never disagree
        about which firmware write belongs to which gate.

    Args:
        plan: One `UpgradePlan` of the upgrade seam.

    Returns:
        The phase name, or an empty string when the plan has no single supported
        family.
    """
    targets = tuple(getattr(plan, "targets", ()) or ())  # Treat a missing target collection as an empty plan.
    families = {str(getattr(target, "device_type", "")) for target in targets}  # One plan must hold one family.
    if len(families) != 1:
        return ""  # Empty and mixed plans have no safe place in the destructive cascade.
    return PLAN_PHASE_BY_DEVICE_TYPE.get(next(iter(families)), "")  # Unknown families also fail closed.


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
        The session holds one lock text for each site. The `select.held_record`
        accessor cannot serve here. It demands a lock token in the request body,
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
        `routes/upgrade.launch_run` calls the launcher with no guard of its own.
        A fault here would turn the confirmation into a 500 answer while the
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
        The driver thread holds no request and no application. The signed
        session, the injected capture runner, the run store seam, and the
        operator record all answer nothing there. The launcher reads all of them
        now, inside the request that the operator confirmed.

        Warning: the answer holds a cloud session, and a log of the whole
        record can leak its API token. Never log this record as a whole.

    Args:
        record: The run record, which names the site of the lock.

    Returns:
        The session, the operator address, the runner, the lock, the store, and the context factory.
    """
    operator: Any = current_operator()  # The one accessor of the signed session of the operator.
    routes = load_module(CAPTURE_ROUTES)  # Owns the capture runner seam.
    return {  # Five values that the driver thread cannot read for itself.
        SESSION_FIELD: getattr(operator, "cloud_session", None),  # Holds an API token, so it never reaches a log.
        EMAIL_FIELD: getattr(getattr(operator, "owner", None), "actor_email", ""),  # The operator address.
        RUNNER_FIELD: None if routes is None else read_safely(routes.capture_runner, "the capture runner seam"),
        LOCK_FIELD: read_lock_record(str(record.get("site_id", ""))),  # The lock that the heartbeat renews.
        STORE_FIELD: bound_store(DocumentRunStore()),  # The same store that the poll route reads.
        APP_CONTEXT_FIELD: current_app.app_context,  # The driver rebuilds this context for stored-status reads.
    }


def capture_context(record: Mapping[str, Any], bindings: Mapping[str, Any]) -> dict[str, Any]:
    """Build the seven job fields that every capture of one run shares.

    Why:
        The collector reads eleven fields. Seven of them hold for every capture
        of one run. The wiring builds them once, and the bridge adds the four
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
        gate can renew the lock during the wait. The same object must sit in
        `driver.RunDriverDeps.heartbeat` and in `phase_gate.PhaseGateDeps.progress`.

        One object in both seats keeps one count of the seconds. The beat then
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
    bound = bind_lock_to_run(lock_record, str(record.get("run_id", "")))  # Issue #2648: name the run in the lock.
    return driver.lock_heartbeat(record, bound)  # The key comes from the organization and the site.


def bind_lock_to_run(lock_record: Any, run_id: str) -> Any:
    """Return the site lock record with the run that it protects named.

    Why:
        Issue #2648. The operator takes the site on the capture page, before any
        run exists, so the stored record names no run. The heartbeat refuses to
        renew a lock that names no run, so the lock expired about one minute
        into every run and a second operator could take the site while the first
        run still wrote firmware.

        The bind happens here, at the one place that builds the heartbeat, so
        the driver seat and the settle gate seat share one bound record.

    Args:
        lock_record: The decoded site lock of the session.
        run_id: The run that now holds the site.

    Returns:
        The record that names the run. The same record returns unchanged when
        it already names this run, when the run key is empty, or when the record
        offers no bind call, because a run must never fail on a lock detail.
    """
    if not run_id:  # A record with no run key to write stays as it is.
        logger.warning("wiring: the run record names no run, so the site lock keeps its own name")
        return lock_record  # The heartbeat then reports the empty run, as it does today.
    if getattr(lock_record, "run_id", "") == run_id:  # The lock already names this run.
        return lock_record  # No copy is needed, and the beat compares the same token.
    binder = getattr(lock_record, "bound_to_run", None)  # The call that Issue #2648 added.
    if not callable(binder):  # A stand-in record of an older test offers no bind call.
        logger.warning("wiring: the site lock record takes no run name, so the run %s renews none", run_id)
        return lock_record  # The run still starts, which matches every other gap of this module.
    logger.info("wiring: bind the site lock to the run %s", run_id)  # BEFORE the bind. No token reaches this line.
    bound = binder(run_id)  # The record is frozen, so this answers a copy.
    logger.debug("wiring: the site lock of the run %s now names its run", run_id)  # AFTER the bind.
    return bound


def build_gate_deps(phase_gate: ModuleType, session: Any, record: Mapping[str, Any], heartbeat: Any, store: Any) -> Any:
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
        store: The run store that carries a persisted stop request.

    Returns:
        The dependency record, or None when the event module is absent.
    """
    events = load_module(EVENTS_MODULE)  # Owns the reconnect event catalogue.
    if events is None:  # No catalogue means the gate can read no reconnect signal.
        return None  # The caller names the gap and the run sends nothing.
    org_id = str(record.get("org_id", ""))  # Both readers narrow to this organization.
    reader = phase_gate.CloudReconnectReader(session, org_id, events.EventCatalogue(), time.time)
    counter = phase_gate.CloudStatisticsReader(session, org_id, str(record.get("site_id", "")))

    def stop_requested(run_id: str) -> bool:
        """Read the stop field that the route thread writes while the gate waits."""
        stored = store.read_run(run_id) if store is not None else None
        return isinstance(stored, Mapping) and stored.get("stop_request") is not None

    if heartbeat is None:  # No lock means no beat, so the gate keeps its own log reporter.
        return phase_gate.PhaseGateDeps(event_reader=reader, statistics_reader=counter, stop_requested=stop_requested)
    return phase_gate.PhaseGateDeps(
        event_reader=reader,
        statistics_reader=counter,
        progress=heartbeat,
        stop_requested=stop_requested,
    )


def build_phase_gate(record: Mapping[str, Any], session: Any, heartbeat: Any, store: Any) -> Any:
    """Build the settle gate of one run.

    Args:
        record: The run record, which names the organization and the site.
        session: The cloud session of the operator.
        heartbeat: The site lock heartbeat, or None.
        store: The run store that carries a persisted stop request.

    Returns:
        The settle gate, or None when a collaborator module is absent.
    """
    phase_gate = load_module(PHASE_GATE_MODULE)  # Late, so this module imports no cloud code at load.
    if phase_gate is None:  # No gate module means no cascade at all.
        return None  # The caller names the gap and the run sends nothing.
    deps = build_gate_deps(phase_gate, session, record, heartbeat, store)  # Readers, progress, and stop signal.
    if deps is None:  # The event module is absent.
        return None  # The caller names the gap and the run sends nothing.
    return phase_gate.PhaseSettleGate(deps)  # The deadline stays at the 1800 seconds of the module.


def build_driver_deps(driver: ModuleType, record: Mapping[str, Any], bindings: Mapping[str, Any]) -> Any:
    """Build every collaborator of the driver of one run.

    Why:
        The driver takes one record. A constructor with a store, a gate,
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
    gate = build_phase_gate(
        record, bindings.get(SESSION_FIELD), heartbeat, bindings.get(STORE_FIELD)
    )  # The heartbeat and stop reader sit in the loop.
    if gate is None:  # No gate means no honest cascade, so the run must not start.
        return None  # The caller writes one error line and sends nothing.
    return driver.RunDriverDeps(  # Every field carries its name, so no positional order can drift.
        store=bindings.get(STORE_FIELD),  # The same store that the routes read through the `RUN_STORE` seam.
        gate=gate,  # Blocks for up to 1800 seconds in each phase.
        capture=CaptureBridge(
            bindings.get(RUNNER_FIELD),
            capture_context(record, bindings),
            bindings.get(APP_CONTEXT_FIELD),
        ),
        submit=CloudUpgradeSubmitter(
            bindings.get(SESSION_FIELD),
            bindings.get(STORE_FIELD),
        ),  # Accepted rows and stop requests share the durable run store.
        heartbeat=heartbeat,  # The second seat of the same object. The first seat is the gate progress.
        post_check_mode=read_post_check_mode(),  # The default keeps the automatic second capture of today.
    )


def free_site_lock(record: Mapping[str, Any]) -> None:
    """Give the site back after a run ended before it sent any firmware.

    Why:
        `upgrade/driver.py` frees the lock in the `finally` of a run that
        reached its thread. A run that never reached that thread passes
        through none of it. Without this call the site stays held for the
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
        this process alone still blocks every later run of the same site. The
        start route reads the store and not this memory.

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
        `upgrade_submitting` for good. The file `contracts/http-api.md` line 255
        then answers `upgrade_already_running` to every later start of that site.
        The site then accepts no upgrade again.

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
        the signed session and the injected seams. The thread it starts needs
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


def _install_capture_service(app: Flask) -> None:
    """Install the CaptureService into the Flask config seam for Phase 2 T-006.

    Why:
        Phase 2 T-006 requires pre-upgrade and post-upgrade device captures.
        The CaptureService encapsulates the logic to fetch device inventory,
        network policies, radio settings, and LLDP neighbors from Mist API and
        store them in ArangoDB. The route handler reads the service from the
        Flask config seam (CAPTURE_SERVICE_KEY) so tests can inject a mock.

        The service needs access to: mist_client (to call Mist API), db_router
        (to persist captures to ArangoDB), and audit_logger (to log all capture
        operations). These collaborators are passed to the CaptureService
        constructor and used internally by capture_pre_upgrade() and
        capture_post_upgrade() methods.

    Args:
        app: The Flask application to wire the service into.
    """
    try:
        # WHY: Import the CaptureService class from the capture/service.py module
        capture_service_module = load_module(CAPTURE_SERVICE_MODULE)  # Late import to avoid network at parse time
        if capture_service_module is None:  # The capture service module is not available in this deployment
            logger.warning(
                "wiring: the capture service module is absent, skipping CaptureService installation"
            )  # Only pre-phase2 deployments lack this
            return

        # WHY: Get the audit logger instance to log capture operations before/after
        audit_logger = logging.getLogger("upgrade_portal.audit")  # The audit logger for compliance and debugging

        # WHY: Read the Mist client from the Flask config without inventing an unsupported client
        mist_client = app.config.get("MIST_CLIENT")  # May have been injected by a test
        # WHY: Read the database router from the Flask config because its constructor requires DatabaseConfig
        db_router = app.config.get("DB_ROUTER")  # May have been injected by a test

        # WHY: Instantiate the CaptureService with all required collaborators
        CaptureService = getattr(
            capture_service_module, "CaptureService", None
        )  # The service class from capture/service.py
        if CaptureService is not None:  # The CaptureService class exists
            capture_service = CaptureService(
                mist_client=mist_client,  # The Mist API client for device capture fetching
                db_router=db_router,  # The database router for ArangoDB persistence
                audit_logger=audit_logger,  # The audit logger for compliance recording
            )
            # WHY: Write the service instance to Flask config with setdefault so tests can inject a mock
            app.config.setdefault(CAPTURE_SERVICE_KEY, capture_service)  # Install the seam for routes to use
            logger.info(
                "wiring: CaptureService installed on seam %s for Phase 2 T-006", CAPTURE_SERVICE_KEY
            )  # Record success
        else:
            logger.warning(
                "wiring: CaptureService class not found in %s module", CAPTURE_SERVICE_MODULE
            )  # Unexpected: module exists but class missing
    except Exception as e:  # Catch any unexpected error during service installation
        logger.error("wiring: failed to install CaptureService: %s", str(e))  # Record the error for debugging
        # WHY: Do not raise—a missing CaptureService should not crash the portal, only the capture route should fail


def _install_upgrade_service(app: Flask) -> None:
    """Install the UpgradeService into the Flask config seam for Phase 2 T-008/T-009.

    Why:
        Phase 2 T-008 requires firmware upgrade orchestration with serial/parallel
        strategy support, per-device retry logic, and pause/resume capability.
        The UpgradeService encapsulates the logic to coordinate firmware upgrades
        across multiple devices with rollback support. The route handler reads the
        service from the Flask config seam (UPGRADE_SERVICE_KEY) so tests can inject
        a mock.

        The service needs access to: mist_client (to call Mist API for device
        upgrades), db_router (to persist run status to ArangoDB), and audit_logger
        (to log all state transitions). These collaborators are passed to the
        UpgradeService constructor and used internally by start_upgrade(),
        get_upgrade_status(), and cancel_upgrade() methods.

    Args:
        app: The Flask application to wire the service into.
    """
    try:
        # WHY: Import the UpgradeService class from the upgrade/service.py module
        upgrade_service_module = load_module(UPGRADE_SERVICE_MODULE)  # Late import to avoid network at parse time
        if upgrade_service_module is None:  # The upgrade service module is not available in this deployment
            logger.warning(
                "wiring: the upgrade service module is absent, skipping UpgradeService installation"
            )  # Only pre-phase2 deployments lack this
            return

        # WHY: Get the audit logger instance to log upgrade operations before/after
        audit_logger = logging.getLogger("upgrade_portal.audit")  # The audit logger for compliance and debugging

        # WHY: Read the Mist client from the Flask config without inventing an unsupported client
        mist_client = app.config.get("MIST_CLIENT")  # May have been injected by a test
        # WHY: Read the database router from the Flask config because its constructor requires DatabaseConfig
        db_router = app.config.get("DB_ROUTER")  # May have been injected by a test

        # WHY: Instantiate the UpgradeService with all required collaborators
        UpgradeService = getattr(
            upgrade_service_module, "UpgradeService", None
        )  # The service class from upgrade/service.py
        if UpgradeService is not None:  # The UpgradeService class exists
            upgrade_service = UpgradeService(
                mist_client=mist_client,  # The Mist API client for device firmware upgrade initiation
                db_router=db_router,  # The database router for ArangoDB upgrade status persistence
                audit_logger=audit_logger,  # The audit logger for compliance recording and state transitions
            )
            # WHY: Write the service instance to Flask config with setdefault so tests can inject a mock
            app.config.setdefault(UPGRADE_SERVICE_KEY, upgrade_service)  # Install the seam for routes to use
            logger.info(
                "wiring: UpgradeService installed on seam %s for Phase 2 T-008/T-009", UPGRADE_SERVICE_KEY
            )  # Record success
        else:
            logger.warning(
                "wiring: UpgradeService class not found in %s module", UPGRADE_SERVICE_MODULE
            )  # Unexpected: module exists but class missing
    except Exception as e:  # Catch any unexpected error during service installation
        logger.error("wiring: failed to install UpgradeService: %s", str(e))  # Record the error for debugging
        # WHY: Do not raise—a missing UpgradeService should not crash the portal, only the upgrade route should fail


def _install_settle_gate_service(app: Flask) -> None:
    """Install the SettleGateService into the Flask config seam for Phase 3 T-010.

    Why:
       Phase 3 T-010 requires post-upgrade device validation via settle gate.
       The SettleGateService encapsulates the logic to verify devices have settled
       after firmware upgrade by running 4 parallel checks: ping, API, firmware
       version, and LLDP neighbors. The route handler reads the service from the
       Flask config seam (SETTLE_GATE_SERVICE_KEY) so tests can inject a mock.

       The service needs access to: mist_client (to call Mist API), db_router
       (to persist settle gate results to ArangoDB), and audit_logger (to log
       all settle gate operations). These collaborators are passed to the
       SettleGateService constructor and used internally by wait_for_settle()
       method.

    Args:
       app: The Flask application to wire the service into.
    """
    try:
        # WHY: Import the SettleGateService class from the settle/service.py module
        settle_gate_service_module = load_module(SETTLE_GATE_SERVICE_MODULE)  # Late import
        if settle_gate_service_module is None:  # The settle gate service module is not available in this deployment
            logger.warning(
                "wiring: the settle gate service module is absent, skipping SettleGateService installation"
            )  # Only pre-phase3 deployments lack this
            return

        # WHY: Get the audit logger instance to log settle gate operations before/after
        audit_logger = logging.getLogger("upgrade_portal.audit")  # The audit logger for compliance and debugging

        # WHY: Read the Mist client from the Flask config without inventing an unsupported client
        mist_client = app.config.get("MIST_CLIENT")  # May have been injected by a test
        # WHY: Read the database router from the Flask config because its constructor requires DatabaseConfig
        db_router = app.config.get("DB_ROUTER")  # May have been injected by a test

        # WHY: Instantiate the SettleGateService with all required collaborators
        SettleGateService = getattr(
            settle_gate_service_module, "SettleGateService", None
        )  # The service class from settle/service.py
        if SettleGateService is not None:  # The SettleGateService class exists
            settle_gate_service = SettleGateService(
                mist_client=mist_client,  # The Mist API client for device settle gate checks
                db_router=db_router,  # The database router for ArangoDB settle gate result persistence
                audit_logger=audit_logger,  # The audit logger for compliance recording
            )
            # WHY: Write the service instance to Flask config with setdefault so tests can inject a mock
            app.config.setdefault(SETTLE_GATE_SERVICE_KEY, settle_gate_service)  # Install the seam for routes to use
            logger.info(
                "wiring: SettleGateService installed on seam %s for Phase 3 T-010", SETTLE_GATE_SERVICE_KEY
            )  # Record success
        else:
            logger.warning(
                "wiring: SettleGateService class not found in %s module", SETTLE_GATE_SERVICE_MODULE
            )  # Unexpected: module exists but class missing
    except Exception as e:  # Catch any unexpected error during service installation
        logger.error("wiring: failed to install SettleGateService: %s", str(e))  # Record error
        # WHY: Do not raise—a missing SettleGateService should not crash the portal


def _install_comparison_service(app: Flask) -> None:
    """Install the ComparisonService into the Flask config seam for Phase 3 T-012.

    Why:
       Phase 3 T-012 requires pre/post-upgrade capture comparison with settle
       gate prerequisite enforcement. The ComparisonService encapsulates the logic
       to verify settle gate passed, fetch pre-capture and post-capture captures,
       calculate deltas, and compare key fields. The route handler reads the
       service from the Flask config seam (COMPARISON_SERVICE_KEY) so tests can
       inject a mock.

       The service needs access to: settle_gate_service (to verify prerequisite),
       db_router (to fetch captures and persist comparison results), and
       audit_logger (to log all comparison operations). These collaborators are
       passed to the ComparisonService constructor and used internally by
       compare() method.

    Args:
       app: The Flask application to wire the service into.
    """
    try:
        # WHY: Import the ComparisonService class from the compare/service.py module
        comparison_service_module = load_module(COMPARISON_SERVICE_MODULE)  # Late import to avoid network at parse time
        if comparison_service_module is None:  # The comparison service module is not available in this deployment
            logger.warning(
                "wiring: the comparison service module is absent, skipping ComparisonService installation"
            )  # Only pre-phase3 deployments lack this
            return

        # WHY: Get the audit logger instance to log comparison operations before/after
        audit_logger = logging.getLogger("upgrade_portal.audit")  # The audit logger for compliance and debugging

        # WHY: Read the database router from the Flask config because its constructor requires DatabaseConfig
        db_router = app.config.get("DB_ROUTER")  # May have been injected by a test

        # WHY: Get the SettleGateService from Flask config (installed by _install_settle_gate_service)
        settle_gate_service = app.config.get(SETTLE_GATE_SERVICE_KEY)  # The settle gate service for prerequisite checks

        # WHY: Instantiate the ComparisonService with all required collaborators
        ComparisonService = getattr(
            comparison_service_module, "ComparisonService", None
        )  # The service class from compare/service.py
        if ComparisonService is not None:  # The ComparisonService class exists
            comparison_service = ComparisonService(
                settle_gate_service=settle_gate_service,  # The settle gate service for prerequisite enforcement
                db_router=db_router,  # The database router for ArangoDB capture fetch and result persistence
                audit_logger=audit_logger,  # The audit logger for compliance recording
            )
            # WHY: Write the service instance to Flask config with setdefault so tests can inject a mock
            app.config.setdefault(COMPARISON_SERVICE_KEY, comparison_service)  # Install the seam for routes to use
            logger.info(
                "wiring: ComparisonService installed on seam %s for Phase 3 T-012", COMPARISON_SERVICE_KEY
            )  # Record success
        else:
            logger.warning(
                "wiring: ComparisonService class not found in %s module", COMPARISON_SERVICE_MODULE
            )  # Unexpected: module exists but class missing
    except Exception as e:  # Catch any unexpected error during service installation
        logger.error("wiring: failed to install ComparisonService: %s", str(e))  # Record error
        # WHY: Do not raise—a missing ComparisonService should not crash the portal


def plan_family(plan: Any) -> Any | None:  # WHY: extract family from plan endpoint
    """Return the gateway family that the status read of one plan needs.

    Why:
        `UpgradePlan` holds no family field, and the status read needs one. The
        endpoint of the plan already names the family. The upgrade seam sends
        every session smart router to the organization call, and every other
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
        target at all. The stop then claims nothing for that row.

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
        run record holds the identifier alone. The `build_plans` call is pure, so
        a second call names the same groups again, and `plan_upgrade` puts each
        device in one group only. The address list of a stored row therefore
        names one plan and no other. A run that started before this repair
        already holds that address list, so no stored record needs a new field.

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


def install_seams(  # Install production defaults or one complete isolated dependency set.
    app: Flask, overrides: E2EFactoryOverrides | None = None
) -> None:
    """Write the store, the launcher, the stop runner, and the adopter into the config.

    Why:
        Each value lands with `setdefault`, so a caller that already chose a
        stand-in keeps it. The contract tests inject their own store, their own
        launcher, and their own stop runner after `create_app` returns. The
        injected object always wins over the object this function writes.

        The `STOP_RUNNER` seam stayed empty while no run record held a cloud
        identifier. The `CloudUpgradeSubmitter._keep` helper now writes one row
        for each accepted call, so the seam holds `cancel_run`. FR-038f still
        holds, because a run with no accepted call builds no cancel target and
        `cancel_run` then answers None.

        One seam stays empty on purpose. The `UPGRADE_OPTIONS_BUILDER` seam must
        stay empty. The route resolves that builder from `upgrade/options.py` on
        its own, exactly as the version seam does. A test that names its own
        builder still wins, because the route reads the seam first.

        Phase 2 T-006/T-008/T-009: CaptureService and UpgradeService are wired
        here via setdefault seams so routes can inject them from Flask config.

        An E2E override set replaces every external seam. The E2E branch
        returns before service construction and before storage bootstrap.

    Args:
        app: The application to fill the seams on.
        overrides: The complete E2E dependency set, or None for production.
    """
    if overrides is not None:  # E2E construction must not create one production dependency.
        logger.info("wiring: install the complete E2E dependency set")  # Record the isolated installation.
        values = overrides.config_values()  # Build one explicit map of every required seam.
        for key, value in values.items():  # Install each value before blueprint registration.
            app.config[key] = value  # An explicit E2E value must replace every default.
        logger.debug("wiring: installed %s E2E dependency values", len(values))  # Report a safe count.
        return  # Do not construct production services or start production storage.
    app.config.setdefault(RUN_STORE_KEY, DocumentRunStore())  # Replaces the memory store of the route module.
    app.config.setdefault(LAUNCHER_KEY, start_upgrade_run)  # Without this the confirmed run sends nothing.
    app.config.setdefault(STOP_RUNNER_KEY, cancel_run)  # Without this a stop cancels nothing at the cloud.
    app.config.setdefault(PRECHECK_ADOPTER_KEY, StandalonePrecheckAdopter())  # The run create call adopts a pre-check.
    app.config.setdefault(
        PORTAL_DEPENDENCY_PROVIDER_KEY,
        PortalDependencyProvider(),
    )  # Store construction rules only, after the existing run seams.
    _install_action_repository(app)  # Bind atomic run actions to ArangoDB with no fallback.
    # Phase 2 T-006: Wire CaptureService for pre/post-upgrade device capture capture
    _install_capture_service(app)  # Inject CaptureService into Flask config seam
    # Phase 2 T-008/T-009: Wire UpgradeService for firmware upgrade orchestration
    _install_upgrade_service(app)  # Inject UpgradeService into Flask config seam
    # Phase 3 T-010: Wire SettleGateService for post-upgrade device validation
    _install_settle_gate_service(app)  # Inject SettleGateService into Flask config seam
    # Phase 3 T-012: Wire ComparisonService for pre/post-upgrade capture comparison
    _install_comparison_service(app)  # Inject ComparisonService into Flask config seam
    prepare_storage()  # Without this no capture can verify, so no upgrade can ever start.
    logger.info(
        "wiring: the portal holds the run store, the launcher, the stop runner, the adopter, and the Phase 2-3 services"
    )  # Once.


def _install_action_repository(app: Flask) -> None:
    """Install the ArangoDB-only run action repository."""
    if "RUN_ACTION_STORE" in app.config:
        return
    store = load_module(STORE_MODULE)
    database = None
    if store is not None:
        try:
            database = store.connect_database()
        except Exception as fault:
            logger.warning("wiring: the action store connection failed (%s)", type(fault).__name__)
    repository = ActionRepository(database)
    if database is not None:
        try:
            repository.bootstrap()
        except Exception as fault:
            logger.warning("wiring: the action store bootstrap failed (%s)", type(fault).__name__)
            repository = ActionRepository(None)
    app.config["RUN_ACTION_STORE"] = repository


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
        still leave a portal that reads. The site pages and the history need no
        store. The `bootstrap_storage` call already answers a report rather than
        raising for that case, and this function guards the rest.

        The bootstrap runs once for each process and not once for each
        application. Every step of it repeats without harm, so a second run adds
        nothing. A second run does cost a database probe, and that probe is not
        free. The `DatabaseConfig.from_env` call resolves the database host and
        the lock store host to decide the standalone mode. The `connect_database`
        call repeats that work whenever the store was out of reach before.

        Warning: a contract test builds one application for each test. Without
        this guard a run of the contract suite paid one host probe for each of
        those applications. On a runner where the host name does not resolve
        quickly, each probe took about 20 seconds. The whole job then reached its
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
