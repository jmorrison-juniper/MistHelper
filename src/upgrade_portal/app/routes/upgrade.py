"""The upgrade routes: the run, the options, the start, the poll, and the stop.

Why:
    Stage three of the operator journey sends the upgrade. FR-033 to FR-038 guard
    the start behind typed text and behind a saved pre-check. FR-038a to FR-038i
    guard the stop behind a second typed word. FR-039 to FR-041 ask the run page
    to refresh itself every 30 seconds and to show each device on its own. Every
    rule of those three groups reaches the operator through one of the handlers
    below.

Route names:
    The templates and the browser script render against these endpoint names, so
    the names are a contract and no rename is safe: `upgrade.create_run`,
    `upgrade.save_options`, `upgrade.start_run`, `upgrade.run_status`,
    `upgrade.run_page`, `upgrade.options_page`, `upgrade.confirm_page`, and
    `upgrade.stop_run`.

Two paths, one new run:
    `contracts/http-api.md` section 5 names `POST /api/sites/<site_id>/runs` and
    carries the site in the path. `tasks.md` T151 names `POST /api/runs` and
    carries no site at all. The contract wins, because the browser code and the
    contract tests both read the contract, and because the site lock check of
    T182 and the `RunSpec` record both need a site identifier. The task path
    still binds to the same handler, which reads the site out of the signed
    session instead. `select.list_sites` already settles this exact class of
    conflict the same way, so the two documents agree and neither path repeats a
    line of logic.

Seams:
    Three parts of this feature arrive beside this module: the run record store,
    the run driver, and the cancel work of a stop. Each one travels through a
    seam, which is an injected object in the application configuration. Nothing
    here imports either module while this module loads, so the portal starts
    today and picks up each module on the day its wiring lands. A contract test
    injects a stand-in and reaches no cloud, no ArangoDB server, and no Redis
    server.

Where a run record lives:
    In the injected store when the configuration holds one, and in one guarded
    dictionary in this process when it does not. `capture/store.py` publishes
    `write_run` and publishes no run reader, so it does not satisfy the two
    method shape that `runtime/signals.RunRecordStore` asks for. The memory store
    keeps every route working until that reader lands.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

import logging  # The portal logs with the standard library only.
import threading  # One guard for the memory run store, which a driver thread also writes.
import time  # Issue #2187 previews the moment that a schedule duration names.
from collections.abc import Iterable, Mapping  # The version answer arrives in more than one shape.
from datetime import UTC, datetime  # The same preview needs a readable moment.
from typing import Any, NamedTuple  # A run record is free-form, and the lock read carries two fixed fields.

from flask import Blueprint, Response, current_app, jsonify, request, session  # The framework of the portal.

from ...runtime import identity  # The real session guard. No copy of it lives here.
from ...runtime.runs import (  # The record layer owns every rule below, so no copy of one lives here.
    RunRecordBuilder,
    RunSpec,
    RunState,
    RunStateMachine,
    RunStatusView,
    RunTransitionError,
)
from ...runtime.signals import (  # The stop request rides inside the run record, visible to every worker.
    ConfirmationRequiredError,
    RunNotFoundError,
    RunNotStoppableError,
    StopOutcome,
    StopRequestError,
    StopRequestStore,
)
from ..factory import build_error_envelope, json_error  # The one error envelope that the contract allows.
from .select import (  # The sibling module owns these rules, so no copy of them lives here.
    LOCK_STATE_FREE,
    LOCK_STATE_LOCKED,
    LOCK_STATE_UNKNOWN,
    SELECTED_SITE_KEY,
    find_attribute,
    find_site,
    load_optional_module,
    lock_banner_context,
    read_site_locks,
    render_page,
    resolve_org,
)

logger = logging.getLogger(__name__)  # One logger for each module keeps the source visible in the log.

upgrade_bp = Blueprint("upgrade", __name__)  # No URL prefix, because the paths span `/runs` and `/api`.

# Each route declares a full path, so a reader finds the whole path in one place.
CREATE_PATH = "/api/sites/<site_id>/runs"  # `contracts/http-api.md` section 5 names this path.
CREATE_ALT_PATH = "/api/runs"  # `tasks.md` T151 names this path, and it reads the site from the session.
OPTIONS_API_PATH = "/api/runs/<run_id>/options"  # The saved target list and the three upgrade options.
VERSIONS_PATH = "/api/runs/<run_id>/versions"  # `contracts/http-api.md` section 5 names this path.
START_PATH = "/api/runs/<run_id>/start"  # The one begin action of a run.
STATUS_PATH = "/api/runs/<run_id>/status"  # The poll target of the browser.
STOP_PATH = "/api/runs/<run_id>/stop"  # The one stop action of a run.
RUN_PAGE_PATH = "/runs/<run_id>"  # The live run view with the phase list and the device table.
OPTIONS_PAGE_PATH = "/runs/<run_id>/options"  # The page that picks a version for each device.
CONFIRM_PAGE_PATH = "/runs/<run_id>/confirm"  # The page that reads the typed word `CONFIRM`.

OPTIONS_TEMPLATE = "upgrade/options.html"  # The version picker and the three option controls.
CONFIRM_TEMPLATE = "upgrade/confirm.html"  # The last page before the portal sends anything.
PROGRESS_TEMPLATE = "upgrade/progress.html"  # The live run view, which includes the stop partial.

RUN_STORE_KEY = "RUN_STORE"  # The seam for the run record store.
LAUNCHER_KEY = "RUN_LAUNCHER"  # The seam that hands one prepared record to the run driver.
STOP_RUNNER_KEY = "STOP_RUNNER"  # The seam for the cancel work of a stop.
PRECHECK_ADOPTER_KEY = "PRECHECK_ADOPTER"  # The seam that reads and links a standalone pre-check.
OPTIONS_BUILDER_KEY = "UPGRADE_OPTIONS_BUILDER"  # The seam for `upgrade/options.py`.
OPTIONS_VIEW_KEY = "UPGRADE_OPTIONS_VIEW"  # The seam for the device rows of the options page.
VERSIONS_KEY = "UPGRADE_VERSIONS"  # The version list of each model, for the options page.
VERSIONS_MODULE = "upgrade.options"  # The module that reads the version list of each model.
VERSIONS_ATTRIBUTES = ("read_model_versions",)  # The reader name that the module above publishes.
VIEW_ATTRIBUTES = ("build_options_view",)  # The builder of the device rows of the options page.
RECORD_ATTRIBUTES = ("build_options_record",)  # The builder of the stored target list.
ADVANCED_ATTRIBUTES = ("advanced_option_values",)  # The reader of the advanced control text of one run.
OPTION_RECORD_ATTRIBUTES = ("build_option_record",)  # The mapper of one request body onto a stored record.
SELECTED_TYPES_ATTRIBUTES = ("selected_device_types",)  # The validator of selected upgrade types.
VIEW_VERSIONS_FIELD = "versions_by_model"  # The render keyword that `options.html` reads.
BY_MODEL_FIELD = "by_model"  # `contracts/http-api.md` section 5 fixes this answer field.

STORE_READ = "read_run"  # The reader that `runtime/signals.RunRecordStore` asks for.
STORE_WRITE = "write_run"  # The writer of the same shape.
STORE_SITE_RUNS = "runs_for_site"  # The site scan that FR-037 asks for. A store may publish none.

ADOPT_READ = "newest_precheck"  # The reader the adopter seam publishes for the newest pre-check.
ADOPT_WRITE = "write_capture_edge"  # The writer the adopter seam publishes for the pre edge.
ROLE_PRE = "pre"  # Delta H3 fixes this role for the edge from a run to its adopted pre-check.

CONFIRM_FIELD = "confirm"  # The body field that carries the typed word, for both the start and the stop.
CONFIRM_TEXT = "CONFIRM"  # FR-033 fixes this exact text and this exact letter case for the start.
TIER_FIELD = "tier"  # The body field that names the data tier of the pre-check capture.
TIER_STANDARD = 2  # The device state and the client lists.
TIER_EXTRA = 3  # Tier 2, the port state, the radio state, and the alarms.
KNOWN_TIERS = (TIER_STANDARD, TIER_EXTRA)  # Any other value falls back to the standard tier.

TARGETS_FIELD = "targets"  # The body field that carries one row for each device.
WARNINGS_FIELD = "warnings"  # The answer field that carries one sentence for each warning.
PRE_CAPTURE_FIELD = "pre_capture_id"  # The run record field that names the saved pre-check.

SITE_LOCKED_CODE = "site_locked"  # Another operator holds the site, so this run may not act on it.
SITE_NOT_CHOSEN_CODE = "site_not_chosen"  # The request named no site and the session holds none.
ORG_NOT_CHOSEN_CODE = "org_not_chosen"  # The session holds no organization, so no run may start.
RUN_NOT_FOUND_CODE = "run_not_found"  # `contracts/http-api.md` fixes this code for every run path.
BAD_OPTION_CODE = "bad_option"  # `contracts/http-api.md` fixes this code for the options call.
CONFIRMATION_REQUIRED_CODE = "confirmation_required"  # The operator typed the wrong word.
PRE_CAPTURE_MISSING_CODE = "pre_capture_missing"  # No verified pre-check exists, so no start may run.
TARGETS_MISSING_CODE = "upgrade_targets_missing"  # The saved plan names no device, so the start would send nothing.
RUN_NOT_READY_CODE = "run_not_ready"  # The run has not reached the confirmation stage.
RUN_NOT_STOPPABLE_CODE = "run_not_stoppable"  # The run already reached a state that a stop cannot change.
RUN_WRITE_FAILED_CODE = "run_write_failed"  # The store refused the write, so the operator must retry.
UPGRADE_RUNNING_CODE = "upgrade_already_running"  # FR-037: one run of this site has not reached a final state.
LOCK_STORE_DOWN_CODE = "lock_store_unreachable"  # `contracts/site-lock.md:116` refuses a write the lock cannot guard.

SITE_LOCKED_MESSAGE = "Another operator holds this site. Ask that operator before you try again."  # The cure.
SITE_NOT_CHOSEN_MESSAGE = "Choose a site before you start a run."  # Names the missing step.
ORG_NOT_CHOSEN_MESSAGE = "Choose an organization before you start a run."  # Names the missing step.
RUN_NOT_FOUND_MESSAGE = "The portal holds no run with that identifier."  # No cure exists.
CONFIRM_REQUIRED_MESSAGE = "The start control needs the exact text CONFIRM."  # Names the word and the case.
STOP_REQUIRED_MESSAGE = "The stop control needs the exact text STOP."  # Names the word and the case.
PRE_CAPTURE_MISSING_MESSAGE = "Save a verified pre-check capture before you start the upgrade."  # The cure.
TARGETS_MISSING_MESSAGE = "The saved plan names no device. Choose a version on the options page and save it."  # Cure.
RUN_NOT_READY_MESSAGE = (
    "The run is not ready to start. Open the upgrade options, save the plan, then confirm the upgrade."  # The cure.
)
RUN_WRITE_FAILED_MESSAGE = "The portal could not write the run record. Try again."  # The cure.
UPGRADE_RUNNING_MESSAGE = "An upgrade already runs at this site. Open that run before you start a new one."  # Cure.
LOCK_STORE_DOWN_MESSAGE = (  # Warning: a guess here can start a second upgrade on a live site.
    "The portal cannot reach the site lock store, so it cannot tell whether "
    "another operator holds this site. Wait, then try again."
)
NO_LAUNCHER_MESSAGE = "The portal cannot send an upgrade yet, because the run driver is not wired."  # The gap.
STOP_RECORDED_MESSAGE = "The portal recorded the stop and starts no further device."  # Claims no cancel.

OK_STATUS = 200  # The read or the write succeeded.
CREATED_STATUS = 201  # The portal created one run record.
ACCEPTED_STATUS = 202  # The portal took the work and answered before it ended.
BAD_REQUEST_STATUS = 400  # The portal could not read the request.
NOT_FOUND_STATUS = 404  # No such run.
CONFLICT_STATUS = 409  # The site is held, the pre-check is missing, or the run cannot stop.
SERVER_ERROR_STATUS = 500  # A part of the portal is missing, so the write cannot run.
UNAVAILABLE_STATUS = 503  # `contracts/http-api.md:133` fixes this status for an unreadable lock store.

# The run record of a live run lives here while no store is injected. The driver
# thread writes and the poll reads, so both take the guard.
_RUNS: dict[str, dict[str, Any]] = {}  # One entry for each run this process created.
_RUN_GUARD = threading.Lock()  # Held for the whole of one read and one write.


class MemoryRunStore:
    """Holds every run record of this process in one guarded dictionary.

    Why:
        `runtime/signals.RunRecordStore` asks for a reader and a writer.
        `capture/store.py` publishes `write_run` and publishes no reader, so it
        does not satisfy that shape today. This store keeps the start route, the
        poll route, and the stop route working until the reader lands, and the
        `RUN_STORE` seam replaces it with no change to any handler below.
    """

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return one run record, or None when no run holds the identifier.

        Args:
            run_id: The run key.

        Returns:
            A copy of the record, or None.
        """
        with _RUN_GUARD:  # The driver thread may write while this read runs.
            held = _RUNS.get(run_id)  # An absent key reads as None, never a fault.
            return dict(held) if held is not None else None  # A copy stops a caller edit of the stored record.

    def write_run(self, run: dict[str, Any]) -> bool:
        """Write one run record and report the true result.

        Args:
            run: The whole record, with the changed fields already in place.

        Returns:
            True when the store holds the record, False when the record names no run.
        """
        key = str(run.get("run_id", ""))  # The record names its own key, so no caller repeats it.
        if not key:  # A record with no key cannot be read back, so the write is a defect.
            logger.error("upgrade: a run record carries no run_id, so the portal wrote nothing")  # Names the gap.
            return False  # The caller answers the write failure to the operator.
        with _RUN_GUARD:  # The poll may read while this write runs.
            _RUNS[key] = dict(run)  # A copy stops a later edit of the caller dictionary.
        return True  # The record is readable from this moment.

    def runs_for_site(self, site_id: str) -> list[dict[str, Any]]:
        """Return every run record that this process holds for one site.

        Why:
            FR-037 asks the portal to find a run that already acts on the site.
            The two method shape of `runtime/signals.RunRecordStore` answers one
            run at a time, so it cannot answer that question. This third method
            is optional, and `site_run_records` reads it through the same seam,
            so the store that lands later publishes the same name and no handler
            changes.

        Args:
            site_id: The site that the new run wants to act on.

        Returns:
            A copy of each record of that site, in no fixed order.
        """
        with _RUN_GUARD:  # The driver thread may write while this scan runs.
            held = list(_RUNS.values())  # One list copy, so the scan drops the guard before it filters.
        return [dict(record) for record in held if record.get("site_id") == site_id]  # A copy for each row.


_MEMORY_STORE = MemoryRunStore()  # One store for the whole process, built once at load.


# --------------------------------------------------------------------------
# The seams.
# --------------------------------------------------------------------------


def injected_object(config_key: str) -> Any | None:
    """Return the object that the application configuration holds for one seam.

    Why:
        `select.injected_seam` accepts a callable only, and the run store is an
        object with two methods. This function keeps the same rule for a seam of
        that shape, so a contract test injects a stand-in and reaches no server.

    Args:
        config_key: The configuration key of the seam.

    Returns:
        The injected object, or None when the configuration holds none.
    """
    return current_app.config.get(config_key)  # An unset key reads as None, which every caller expects.


def run_store() -> Any:
    """Return the store that reads and writes one run record.

    Returns:
        The injected store when it carries both methods, or the memory store.
    """
    injected = injected_object(RUN_STORE_KEY)  # A contract test injects the store and reaches no database.
    if injected is None:  # No wiring yet, which is the normal state of an early portal.
        return _MEMORY_STORE  # Every route still works inside this process.
    if not all(callable(getattr(injected, name, None)) for name in (STORE_READ, STORE_WRITE)):  # Wrong shape.
        logger.error("upgrade: the injected run store holds no %s and no %s pair", STORE_READ, STORE_WRITE)
        return _MEMORY_STORE  # A wrong shape must not break a run, so the memory store answers instead.
    return injected  # The real store, which every worker of the portal shares.


def run_launcher() -> Any | None:
    """Return the callable that hands one prepared run record to the run driver.

    Why:
        `upgrade/driver.py` needs a store, a phase gate, a capture starter, and
        an upgrade submitter. The wiring of those four belongs to the driver
        work, not to a route. One seam keeps that wiring in one place and lets
        this module answer the start today.

    Returns:
        The injected launcher, or None while the driver is not wired.
    """
    candidate = injected_object(LAUNCHER_KEY)  # The driver work injects one callable here.
    return candidate if callable(candidate) else None  # A value that is not callable counts as unset.


def stop_runner() -> Any | None:
    """Return the callable that performs the cancel work of one stop.

    Returns:
        The injected runner, or None while the cancel work is not wired.
    """
    candidate = injected_object(STOP_RUNNER_KEY)  # The stop work injects one callable here.
    return candidate if callable(candidate) else None  # A value that is not callable counts as unset.


def precheck_adopter() -> Any | None:
    """Return the object that reads and links a standalone pre-check.

    Why:
        Delta H3 asks the run create call to adopt the newest verified
        standalone pre-check of the site. The adoption reads the newest key and
        writes one edge, so it sits behind a seam and a contract test injects a
        stand-in that reaches no database.

    Returns:
        The injected adopter with both methods, or None when none is wired.
    """
    candidate = injected_object(PRECHECK_ADOPTER_KEY)  # The wiring injects one adopter here.
    if candidate is None:  # No wiring yet, so the run create call adopts no pre-check.
        return None  # The creation then leaves the pre-check field empty.
    if not all(callable(getattr(candidate, name, None)) for name in (ADOPT_READ, ADOPT_WRITE)):  # Wrong shape.
        logger.error("upgrade: the injected pre-check adopter holds no %s and no %s pair", ADOPT_READ, ADOPT_WRITE)
        return None  # A wrong shape must not break a run, so the creation adopts nothing.
    return candidate  # The real adopter, which reads the newest pre-check and writes the edge.


def options_builder() -> Any | None:
    """Return the callable that turns one request body into a target list.

    Why:
        `upgrade/options.py` reads the site inventory before it builds a target,
        so it needs a cloud session that no route layer holds. The seam keeps
        that read with the module that owns it.

    Returns:
        The injected builder, or None while that wiring is not in place.
    """
    candidate = injected_object(OPTIONS_BUILDER_KEY)  # The options work injects one callable here.
    return candidate if callable(candidate) else None  # A value that is not callable counts as unset.


# --------------------------------------------------------------------------
# The request body and the current operator.
# --------------------------------------------------------------------------


def request_body() -> dict[str, Any]:
    """Read the body of the current request as a dictionary.

    Why:
        The portal script posts JSON, and a plain form post carries the same
        fields. A body of another shape reads as an empty body, so a route
        answers its own refusal and never a fault page.

    Returns:
        The body fields, or an empty dictionary.
    """
    payload: Any = request.get_json(silent=True)  # A body that is not JSON reads as None, never a fault.
    if isinstance(payload, dict):  # The browser script path.
        return payload  # The fields arrive as the script sent them.
    return dict(request.form)  # The plain form path, and an empty dictionary for an empty body.


def confirmation_text() -> str:
    """Return the word that the operator typed into a confirmation control.

    Returns:
        The typed text, without a trim and without a case change.
    """
    return str(request_body().get(CONFIRM_FIELD, ""))  # FR-034 names the letter case, so nothing changes here.


def chosen_tier() -> int:
    """Return the data tier that the new run reads.

    Returns:
        The tier from the body when the body names a known tier, or tier 2.
    """
    raw = request_body().get(TIER_FIELD, TIER_STANDARD)  # An absent field means the standard tier.
    try:  # A browser may send the tier as text, and a hand-typed body may send anything.
        number = int(raw)  # The record holds a number, so the text form converts here.
    except (TypeError, ValueError):  # A value of another shape is a caller defect, not a fault.
        return TIER_STANDARD  # The standard tier is the safe default of the contract.
    return number if number in KNOWN_TIERS else TIER_STANDARD  # An unknown number falls back the same way.


def actor_address() -> str:
    """Return the address of the signed-in operator.

    Returns:
        The address, or an empty string when no session owner exists.
    """
    owner = identity.current_owner()  # The session guard already refused an unsigned request.
    return owner.actor_email if owner is not None else ""  # An empty address never reaches a log record.


def browser_key() -> str:
    """Return the browser identifier of the signed-in operator.

    Why:
        FR-038 accepts one begin action for each run, even across several tabs.
        The record holds the browser that created the run, so a later read names
        the tab group that owns it.

    Returns:
        The browser identifier, or an empty string when no session owner exists.
    """
    owner = identity.current_owner()  # The same owner that `actor_address` reads.
    return owner.browser_id if owner is not None else ""  # An empty value still writes a valid record.


# --------------------------------------------------------------------------
# The run record.
# --------------------------------------------------------------------------


def load_run(run_id: str) -> dict[str, Any] | None:
    """Read one run record through the store seam.

    Args:
        run_id: The run key.

    Returns:
        The record, or None when the store holds no run with that key.
    """
    record: Any = run_store().read_run(run_id)  # The seam answers None for an absent key.
    return record if isinstance(record, dict) else None  # A damaged record reads as no record at all.


def save_run(record: dict[str, Any]) -> bool:
    """Write one run record through the store seam.

    Args:
        record: The whole record, with the changed fields already in place.

    Returns:
        True when the store holds the record.
    """
    written = bool(run_store().write_run(record))  # The store reports the true result, never a guess.
    if not written:  # The operator must learn that the portal kept nothing.
        logger.error("upgrade: the store refused the run record %s", record.get("run_id", ""))  # Names the run.
    return written  # The caller answers 500 when this value is False.


def run_not_found() -> tuple[Response, int]:
    """Answer the one refusal that every run path shares.

    Returns:
        The 404 answer with the contract code.
    """
    return json_error(NOT_FOUND_STATUS, RUN_NOT_FOUND_CODE, RUN_NOT_FOUND_MESSAGE)  # One code for every run path.


def write_failed() -> tuple[Response, int]:
    """Answer a store that refused a write.

    Returns:
        The 500 answer with a code that names the cure.
    """
    return json_error(SERVER_ERROR_STATUS, RUN_WRITE_FAILED_CODE, RUN_WRITE_FAILED_MESSAGE)  # Retry is the cure.


# --------------------------------------------------------------------------
# The site lock.
# --------------------------------------------------------------------------


class SiteLockRead(NamedTuple):
    """Holds what the portal learned about one site lock.

    Why:
        A holder address alone answers two states. A free site and a site the
        portal could not read both answer None, so a write path that reads only
        an address treats a dead lock store as a free site. Issue #1827 reports
        that exact failure. These two fields carry the third state, so every
        write path can refuse what it cannot read.
    """

    state: str  # One of `free`, `locked`, or `unknown`, as `select.site_lock_state` names them.
    holder: str  # The address of the holder, and an empty string for the other two states.


LOCK_FREE = SiteLockRead(LOCK_STATE_FREE, "")  # The store answered and named no holder.
LOCK_UNKNOWN = SiteLockRead(LOCK_STATE_UNKNOWN, "")  # The store did not answer, so the portal cannot tell.


def lock_holder(org_id: str, site_id: str) -> SiteLockRead:
    """Return what the lock store knows about one site.

    Why:
        `contracts/site-lock.md:116` refuses an upgrade start that the lock
        cannot guard, and `select.read_site_locks` answers an empty index when
        the store does not answer. This function tests membership, as
        `select.site_lock_state` already does, so an absent entry reads
        `unknown` and never `free`.

    Args:
        org_id: The organization that holds the site.
        site_id: The site the run acts on.

    Returns:
        The lock state and the holder address of that site.
    """
    locks = read_site_locks(org_id, [site_id])  # An unreachable store answers an empty index and raises nothing.
    if site_id not in locks:  # The lock store named no state for this site.
        return LOCK_UNKNOWN  # The portal cannot tell, so it must not report free.
    holder = locks[site_id]  # A None value means the store answered and found no lock.
    return SiteLockRead(LOCK_STATE_LOCKED, holder) if holder else LOCK_FREE  # An address names the holder.


def site_locked_refusal(holder: str) -> tuple[Response, int]:
    """Answer a site that another operator holds, and name that operator.

    Why:
        T182 asks the refusal to name the holder, so the second operator knows
        whom to ask. `json_error` carries no `details` key, so the answer takes
        the envelope builder instead. `contracts/http-api.md:132` fixes
        `details.actor_email` for the same refusal on the lock path.

    Args:
        holder: The address of the operator that holds the lock.

    Returns:
        The 409 answer with the contract code and the holder address.
    """
    body = build_error_envelope(SITE_LOCKED_CODE, SITE_LOCKED_MESSAGE, {"actor_email": holder})  # Names the holder.
    return jsonify(body), CONFLICT_STATUS  # The browser reads the code and shows the address.


def lock_store_down_refusal() -> tuple[Response, int]:
    """Answer a lock store that the portal cannot read.

    Why:
        `contracts/site-lock.md:116` refuses the upgrade with 503 and forbids a
        fallback lock. The answer names no operator, because the portal read
        nothing and any address here would be a guess.

    Returns:
        The 503 answer with the contract code and the cure.
    """
    return json_error(UNAVAILABLE_STATUS, LOCK_STORE_DOWN_CODE, LOCK_STORE_DOWN_MESSAGE)  # Waiting is the cure.


def held_by_other(org_id: str, site_id: str) -> SiteLockRead:
    """Return the lock state that stops the current operator.

    Why:
        The operator that already holds the lock must pass every check of this
        module. Without this rule the start route would refuse the one operator
        that the lock exists to protect. An unknown state passes no operator,
        because the portal cannot name who holds the site.

    Args:
        org_id: The organization that holds the site.
        site_id: The site the run acts on.

    Returns:
        The free state when the caller may continue, and the blocking state
        otherwise.
    """
    found = lock_holder(org_id, site_id)  # Three states, so a dead store never reads as a free site.
    if found.holder and found.holder == actor_address():  # The current operator may always continue.
        return LOCK_FREE  # The caller runs the action.
    if found.state == LOCK_STATE_LOCKED:  # Another operator holds this site right now.
        logger.info("upgrade: the site %s is held by %s", site_id, identity.email_digest(found.holder))  # Digest.
    return found  # The caller turns this state into the documented refusal.


def lock_refusal(org_id: str, site_id: str) -> tuple[Response, int] | None:
    """Return the refusal that the site lock puts on one write, or None.

    Why:
        Three write routes share one rule. One function holds that rule, so no
        route can read an unknown state as a free site. Warning: a write that
        skips this check can start a second upgrade on a live site.

    Args:
        org_id: The organization that holds the site.
        site_id: The site the write acts on.

    Returns:
        The 409 answer, the 503 answer, or None when the write may run.
    """
    found = held_by_other(org_id, site_id)  # One read for both refusals below.
    if found.state == LOCK_STATE_UNKNOWN:  # The lock store did not answer about this site.
        logger.warning("upgrade: the lock store did not answer about the site %s, so the write stops", site_id)
        return lock_store_down_refusal()  # `contracts/site-lock.md:116` refuses the write and adds no fallback.
    if found.state == LOCK_STATE_LOCKED:  # A second operator holds the site.
        return site_locked_refusal(found.holder)  # The refusal names that operator.
    return None  # The store answered, and the site is free for this operator.


# --------------------------------------------------------------------------
# The run that a site already holds (FR-037).
# --------------------------------------------------------------------------


def site_run_records(site_id: str) -> list[dict[str, Any]]:
    """Return every run record that the store holds for one site.

    Why:
        `runtime/signals.RunRecordStore` asks for a reader and a writer only, so
        a store of that shape can hold no site scan. FR-037 must not break such
        a store and must not guess, so an absent scan answers an empty list and
        the create call continues.

    Args:
        site_id: The site that the new run wants to act on.

    Returns:
        One record for each run of that site, or an empty list.
    """
    scan = getattr(run_store(), STORE_SITE_RUNS, None)  # An absent method reads as None, never a fault.
    if not callable(scan):  # The store holds the two method shape and nothing more.
        logger.info("upgrade: the run store publishes no %s, so no site scan runs", STORE_SITE_RUNS)  # The gap.
        return []  # No scan means no refusal, because a guess would stop honest work.
    try:  # The store sits on a network and may not answer.
        found: Any = scan(site_id)  # The store owns the query and the order of the rows.
    except Exception:  # A create call must survive an unreachable store.
        logger.warning("upgrade: the run store did not answer the site scan of %s", site_id)  # No trace.
        return []  # Continue, because the lock check below still guards a second operator.
    return [record for record in found if isinstance(record, dict)]  # A damaged row reads as no row.


def live_run_at_site(site_id: str) -> str | None:
    """Return the key of a run that already acts on one site.

    Why:
        FR-037 asks the portal to warn before it sends a second upgrade to the
        same site. The site lock answers a different question. The operator that
        started the first run still holds that lock, so that same operator
        passes every lock check and starts a second upgrade over the first.
        `run_is_live` reads `RunStateMachine.TERMINAL`, so no state name is
        written twice and a finished run leaves the site free.

    Args:
        site_id: The site that the new run wants to act on.

    Returns:
        The key of the first unfinished run, or None when every run finished.
    """
    for record in site_run_records(site_id):  # One row for each run that the store holds for this site.
        if run_is_live(record):  # A final run blocks nothing, so switches today and access points tomorrow work.
            return str(record.get("run_id", ""))  # The refusal names this run to the operator.
    return None  # Every run of this site reached a final state.


def already_running_refusal(run_id: str) -> tuple[Response, int]:
    """Answer a site that already runs an upgrade, and name that run.

    Why:
        `site_locked` names a second operator, which is a different fact and the
        exact confusion that FR-037 repairs, so this refusal carries its own
        code. `json_error` holds no `details` key, so the answer takes the
        envelope builder, as `site_locked_refusal` already does.

    Args:
        run_id: The key of the run that has not reached a final state.

    Returns:
        The 409 answer with the FR-037 code and the key of the live run.
    """
    body = build_error_envelope(UPGRADE_RUNNING_CODE, UPGRADE_RUNNING_MESSAGE, {"run_id": run_id})  # Names the run.
    return jsonify(body), CONFLICT_STATUS  # The browser reads the code and opens that run.


def site_refusal(org_id: str, site_id: str) -> tuple[Response, int] | None:
    """Return the refusal that stops a new run on one site, or None.

    Why:
        A create call passes two separate checks. A held site belongs to a
        second operator. A live run belongs to the current operator as often as
        not, so the lock check alone lets that operator open a second run from a
        second tab. One function holds both checks and keeps the handler inside
        the Five-Item Rule.

    Args:
        org_id: The organization that holds the site.
        site_id: The site that the new run wants to act on.

    Returns:
        The refusal answer, or None when the site accepts a new run.
    """
    refusal = lock_refusal(org_id, site_id)  # `contracts/http-api.md` lists 409 site_locked and 503 on this path.
    if refusal is not None:  # Another operator holds the site, or the portal cannot read the lock.
        return refusal  # The answer names the operator to ask, or names the unreadable store.
    live = live_run_at_site(site_id)  # FR-037: the check above never sees the run of the current operator.
    if live:  # One upgrade of this site has not reached a final state.
        logger.info("upgrade: the site %s already runs the upgrade %s", site_id, live)  # Names the live run.
        return already_running_refusal(live)  # The refusal names that run.
    return None  # The site accepts a new run.


# --------------------------------------------------------------------------
# The new run.
# --------------------------------------------------------------------------


def chosen_site(site_id: str | None) -> str | None:
    """Return the site that the new run acts on.

    Why:
        Two paths reach this handler. One carries the site in the path and one
        holds it in the signed session. This function is the single point where
        that difference ends, so the handler below repeats no rule.

    Args:
        site_id: The identifier from the path, or None.

    Returns:
        The site identifier, or None when neither source holds one.
    """
    if site_id:  # The path named the site, so the path wins.
        return site_id  # An explicit value always beats a stored one.
    stored: Any = session.get(SELECTED_SITE_KEY)  # The pick that `select.store_chosen_site` wrote.
    return stored if isinstance(stored, str) and stored else None  # A damaged field reads as no pick.


def readable_site_name(org_id: str, site_id: str, given: str) -> str:
    """Return the site name in words for one new run record.

    Why:
        Issue #2100 asks the three upgrade pages to name the site in words. The
        picker stores the site identifier alone, so a create call that carries no
        name once wrote the identifier into the name field. The cloud holds the
        real name, so this function reads it one time for each new run.

        A silent cloud or an unknown site returns the identifier. The operator
        then reads a value instead of a blank field.

    Args:
        org_id: The organization that holds the site.
        site_id: The site the run acts on.
        given: The name the create body carries, or an empty string.

    Returns:
        The site name in words, or the site identifier.
    """
    if given:  # The caller knows the name already, so no cloud read is needed.
        return given
    logger.info("upgrade: read the name of the site %s for a new run", site_id)  # BEFORE the cloud read.
    try:
        site = find_site(site_id, org_id)  # The sibling module owns every rule of this read.
    except Exception:  # A named site beats a fault, so any failure keeps the identifier.
        logger.warning("upgrade: the site %s did not answer, so the run keeps the identifier", site_id)
        return site_id  # The page still shows a value that an operator can quote.
    name = str(site.get("name", "")).strip() if site else ""  # An unknown site answers None.
    logger.debug("upgrade: the site %s answered the name %s", site_id, name or site_id)  # AFTER the cloud read.
    return name or site_id  # An empty name falls back to the identifier.


def new_run_spec(org_id: str, site_id: str) -> RunSpec:
    """Build the record request for one new run.

    Why:
        The record holds a readable name for the organization and for the site,
        and the picker stores neither name in the session. The body may carry
        both. The site name comes from the cloud when the body carries none, so
        the three upgrade pages name the site in words. The identifier stands in
        when no name exists, so the record never holds an empty name.

    Args:
        org_id: The organization of the current session.
        site_id: The site the run acts on.

    Returns:
        The finished record request.
    """
    body = request_body()  # The picker may send the two readable names with the create call.
    return RunSpec(
        org_id=org_id,  # Every read of this run stays inside this organization.
        org_name=str(body.get("org_name") or org_id),  # The identifier reads better than an empty name.
        site_id=site_id,  # FR-014 binds one run to one site.
        site_name=readable_site_name(org_id, site_id, str(body.get("site_name") or "")),  # Issue #2100.
        actor_email=actor_address(),  # FR-038h asks the record to name the operator.
        browser_id=browser_key(),  # Names the tab group that created the run.
        tier=chosen_tier(),  # The pre-check capture reads this tier.
    )


def adopt_precheck(record: dict[str, Any], site_id: str) -> str:
    """Set the run pre-check field to the newest standalone pre-check.

    Why:
        Delta H3 asks the run create call to adopt the newest verified
        standalone pre-check of the site. The field lands before the save, so
        the stored run names the pre-check at once (FR-103).

    Args:
        record: The new run record, before the save.
        site_id: The site the run belongs to.

    Returns:
        The adopted capture key, or an empty string when the site holds none.
    """
    adopter = precheck_adopter()  # The seam that reads the newest standalone pre-check.
    capture_id = str(adopter.newest_precheck(site_id)) if adopter is not None else ""  # "" means no adoption.
    if capture_id:  # The site holds a standalone pre-check for this run to adopt.
        record[PRE_CAPTURE_FIELD] = capture_id  # The saved run then names the pre-check for the later start.
    return capture_id  # The caller writes the edge after the save proves the run.


def link_adopted_precheck(run_id: str, capture_id: str) -> None:
    """Write the pre edge from one run to its adopted pre-check.

    Why:
        The history view walks the graph from a run to its two captures. The
        edge lands after the save, so it never points at a run the store
        refused (Delta H3, FR-103).

    Args:
        run_id: The new run the edge starts at.
        capture_id: The adopted pre-check the edge points at.
    """
    if not capture_id:  # The run adopted nothing, so there is no edge to write.
        return  # A site with no pre-check leaves the graph unchanged.
    adopter = precheck_adopter()  # The same seam that read the pre-check key.
    if adopter is None:  # No wiring means no edge, and the run still stands.
        return  # The creation already answered the operator.
    logger.info("upgrade: link the run %s to the pre-check %s", run_id, capture_id)  # BEFORE the edge write.
    adopter.write_capture_edge(run_id, capture_id, ROLE_PRE)  # The edge carries the pre role of Delta H3.
    logger.debug("upgrade: the run %s now names the pre-check %s", run_id, capture_id)  # AFTER the edge write.


@upgrade_bp.post(CREATE_PATH)
@upgrade_bp.post(CREATE_ALT_PATH)
@identity.require_session
def create_run(site_id: str | None = None) -> tuple[Response, int]:
    """Create one upgrade run for one site.

    Why:
        FR-014 binds one run to one site. The site lock stops a second operator
        from opening a competing run, and FR-037 stops the current operator from
        sending a second upgrade over a run that still runs.

    Args:
        site_id: The site from the contract path, or None on the task path.

    Returns:
        The new run identifier and its first state, or a refusal.
    """
    org_id = resolve_org(None)  # The session holds the organization, because no path carries one.
    if not org_id:  # No organization means no scope, so no run may exist.
        return json_error(BAD_REQUEST_STATUS, ORG_NOT_CHOSEN_CODE, ORG_NOT_CHOSEN_MESSAGE)
    chosen = chosen_site(site_id)  # The path first, then the signed session.
    if not chosen:  # The task path reached this handler with no stored pick.
        return json_error(BAD_REQUEST_STATUS, SITE_NOT_CHOSEN_CODE, SITE_NOT_CHOSEN_MESSAGE)
    refusal = site_refusal(org_id, chosen)  # The held site check, then the FR-037 live run check.
    if refusal is not None:  # One of the two checks stopped the call.
        return refusal  # The body already names the holder or the live run.
    record = RunRecordBuilder().build(new_run_spec(org_id, chosen))  # The record layer owns every field.
    adopted = adopt_precheck(record, chosen)  # Set the pre-check field before the save (Delta H3).
    logger.info("upgrade: create the run %s for the site %s", record["run_id"], chosen)  # BEFORE the write.
    if not save_run(record):  # The store reports the true result.
        return write_failed()  # The operator retries instead of reading a run that does not exist.
    link_adopted_precheck(record["run_id"], adopted)  # Write the pre edge after the save proved the run.
    logger.info("upgrade: the run %s holds the state %s", record["run_id"], record["state"])  # AFTER the write.
    return jsonify({"run_id": record["run_id"], "state": record["state"]}), CREATED_STATUS


# --------------------------------------------------------------------------
# The options.
# --------------------------------------------------------------------------


def built_options(record: dict[str, Any], body: dict[str, Any]) -> dict[str, Any]:
    """Build the target list and the option record for one run.

    Why:
        The browser sends only a MAC address and a target version for each
        device, but the run driver reads the device type, the gateway family,
        and the scope. `upgrade/options.py` fills those fields from the site
        inventory, so this function reaches that module first. The body itself
        remains the answer when no cloud session or no inventory answers, which
        keeps a test and an offline view working.

    Args:
        record: The stored run record.
        body: The request body of the save call.

    Returns:
        A mapping with the target list, the option record, and the warnings.

    Raises:
        ValueError: When one option holds a value that the portal refuses.
    """
    reader = module_attribute(SELECTED_TYPES_ATTRIBUTES)
    selected_types = list(reader(body)) if callable(reader) else ["ap", "switch", "gateway"]
    builder = options_builder()  # A test injects one callable here.
    if builder is not None:
        answer: Any = builder(record, body)
        built = dict(answer)
        built["selected_types"] = selected_types
        return built
    composed = composed_options(record, body)  # The module owns the inventory read and the family.
    if composed is not None:
        composed["selected_types"] = selected_types
        return composed
    rows = body.get(TARGETS_FIELD)  # No inventory answered, so the body carries what the page showed.
    targets = [dict(row) for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []
    return {
        TARGETS_FIELD: targets,
        "options": plain_options(body),
        "selected_types": selected_types,
        WARNINGS_FIELD: [],
    }


def plain_options(body: dict[str, Any]) -> dict[str, Any]:
    """Read the upgrade option record out of one request body.

    Why:
        `contracts/http-api.md` section 5 fixes the options body. `built_options`
        reads `targets` on its own, so this function reads every option field
        beside it.

        `upgrade/options.py` owns every mapping rule and every refusal, so this
        function reaches that module first. Issue #2156 needs it: the advanced
        controls live in that module alone, and a body that skipped it would
        store three fields and drop every advanced choice with no word to the
        operator. The three basic fields stand only while that module does not
        import, which is the same rule that every other seam of this route
        follows.

    Args:
        body: The request body of the options call.

    Returns:
        The option record that the store keeps.

    Raises:
        ValueError: When one option holds a value that the portal refuses.
    """
    mapper = module_attribute(OPTION_RECORD_ATTRIBUTES)  # The module owns every rule and every refusal.
    if callable(mapper):
        record: Any = mapper(body)  # A refused value raises, and `save_options` maps it to `bad_option`.
        return dict(record)
    return {  # No module, so the three fields that the contract names by hand.
        "reboot": bool(body.get("reboot", True)),  # The cloud reboots an access point on its own.
        "junos_file_action": bool(body.get("junos_file_action", False)),  # A copy only, until the operator asks.
        "strategy": str(body.get("strategy") or "big_bang"),  # The contract names this value as the default.
    }


@upgrade_bp.post(OPTIONS_API_PATH)
@identity.require_session
def save_options(run_id: str) -> tuple[Response, int]:
    """Save the target versions and the three upgrade options of one run.

    Args:
        run_id: The run key.

    Returns:
        The saved target list and the warning list, or a refusal.
    """
    record = load_run(run_id)  # The run must exist before it holds an option.
    if record is None:  # A stale link and a hand-typed path both reach this route.
        return run_not_found()  # One code for every run path.
    logger.info("upgrade: save the options of the run %s", run_id)  # BEFORE the change.
    try:  # A refused option is a caller defect, not a fault of the portal.
        built = built_options(record, request_body())  # The options module owns every rule when it is wired.
    except ValueError as failure:  # `options.BadOptionError` is a `ValueError`, so one clause catches both.
        logger.info("upgrade: the run %s refused an option: %s", run_id, failure)  # No value reaches the log.
        return json_error(BAD_REQUEST_STATUS, BAD_OPTION_CODE, str(failure))
    record[TARGETS_FIELD] = built.get(TARGETS_FIELD, [])  # The run record holds one entry for each device.
    record["options"] = built.get("options", {})  # The three fields the cloud reads.
    record["selected_types"] = list(built.get("selected_types", ["ap", "switch", "gateway"]))
    warnings = list(built.get(WARNINGS_FIELD, []))  # One sentence for each device the operator must look at.
    record[WARNINGS_FIELD] = warnings  # Persist so the confirm page can show the same warning list.
    prepare_confirmation(record)  # A verified adopted pre-check completes the stages before the typed confirmation.
    if not save_run(record):  # The store reports the true result.
        return write_failed()  # The operator retries instead of reading a choice that was never kept.
    logger.info("upgrade: the run %s holds %s targets", run_id, len(record[TARGETS_FIELD]))  # AFTER the change.
    return (
        jsonify(
            {
                TARGETS_FIELD: record[TARGETS_FIELD],
                "selected_types": record["selected_types"],
                WARNINGS_FIELD: warnings,
            }
        ),
        OK_STATUS,
    )


def prepare_confirmation(record: dict[str, Any]) -> None:
    """Move a verified pre-check run to the confirmation stage.

    Why:
        A standalone capture is verified before the portal attaches it to a new
        run. The capture route cannot move that new run through its history.
        Saving its target plan is the first point where the portal knows that
        the verified pre-check and the upgrade plan belong together.

    Args:
        record: The run record that may now be ready for confirmation.
    """
    if not record.get(PRE_CAPTURE_FIELD) or not record.get(
        TARGETS_FIELD
    ):  # A missing reading or plan cannot reach confirmation.
        return  # The start route gives the operator the matching refusal.
    machine = RunStateMachine()  # One state machine owns every valid move.
    if machine.read_state(record) is not RunState.CREATED:  # A repeated save must keep its existing stage.
        return  # The record already reflects the operator journey.
    for state in (RunState.PRE_CAPTURE_RUNNING, RunState.PRE_CAPTURE_DONE, RunState.AWAITING_CONFIRMATION):
        machine.advance(record, state)  # Preserve the complete state history before the confirmation gate.
    logger.info("upgrade: the run %s is ready for confirmation", record["run_id"])  # AFTER the final state change.


# --------------------------------------------------------------------------
# The available versions.
# --------------------------------------------------------------------------


def version_list(versions: Any) -> list[str]:
    """Turn the version value of one model into a plain list of text.

    Why:
        `upgrade/options.py` answers a tuple, a test injects a list, and a
        damaged record holds a single word. The picker draws one control for
        each entry, so a value that is not a list must never reach the template
        as one.

    Args:
        versions: The version value of one model, of any type.

    Returns:
        The version list, with every entry a plain string.
    """
    if isinstance(versions, str) or not isinstance(versions, Iterable):  # One word is not a list of words.
        return [str(versions)] if versions else []  # A single value still gives the operator one choice.
    return [str(one) for one in versions]  # A tuple, a list, and a set all pass through this line.


def version_index(answer: Any) -> dict[str, list[str]]:
    """Turn one version answer into the map that the contract fixes.

    Why:
        Two sources answer this read. The configuration holds a ready map, and
        the options module holds a reader that builds one. Both arrive here, so
        the body of this route and the picker of the page hold the same shape. A
        value of any other shape reads as no version, because a picker with no
        option is safer than a picker that shows a version the cloud never named.

    Args:
        answer: The value that the seam gave, of any type.

    Returns:
        The version list of each model, with every name and every value text.
    """
    if not isinstance(answer, Mapping):  # A callable, a None, and a list all reach this line.
        return {}  # The route answers an empty map and the page shows an empty picker.
    return {str(model): version_list(versions) for model, versions in answer.items()}  # One entry for each model.


def cloud_session() -> Any:
    """Return the Mist session of the signed-in operator.

    Why:
        `upgrade/options.py` reads the cloud, so it needs the session that the
        sign-in built. The registry holds that session against the browser pair,
        so no route and no run record ever carries a credential.

    Returns:
        The cloud session, or None when the registry holds no record.
    """
    owner = identity.current_session()  # The guard already admitted this request, so a record exists.
    return getattr(owner, "cloud_session", None)  # A missing record answers None, and the read then fails.


def read_versions(record: dict[str, Any]) -> dict[str, list[str]]:
    """Return the version list of each model that one run may install.

    Why:
        The injected value wins over the late import, so a contract test reaches
        no cloud. `upgrade/options.py` may not be loadable in every stage of the
        build, so the import happens inside this call and never at load time.

    Args:
        record: The run record that names the site and the target devices.

    Returns:
        The version list of each model, empty when no source answers.
    """
    seam: Any = injected_object(VERSIONS_KEY)  # A ready map and a callable both arrive here.
    if seam is None:  # No stand-in is injected, so ask the module that owns the read.
        seam = find_attribute(load_optional_module(VERSIONS_MODULE), VERSIONS_ATTRIBUTES)
    if not callable(seam):  # A ready map and a missing module both stop on this line.
        return version_index(seam)  # None reads as an empty map, and a map passes through.
    site_id = str(record.get("site_id", ""))  # FR-014 binds one run to one site, so one site scopes the read.
    targets = record.get(TARGETS_FIELD, [])  # Each row names the model that the reader groups the answer by.
    try:  # The reader reaches the cloud, and the cloud refuses and times out.
        return version_index(seam(cloud_session(), site_id, targets))  # The module owns every call parameter.
    except Exception:  # A picker with no version beats a page that shows a fault to the operator.
        logger.warning("upgrade: the version read of the site %s did not answer", site_id)  # No stack trace.
        return {}  # The operator retries the page, and the run record keeps every earlier choice.


def module_attribute(names: tuple[str, ...]) -> Any:
    """Return the first named attribute of the options module, or None.

    Why:
        Three seams of this route reach `upgrade/options.py`, and each one must
        survive a build stage in which that module does not import. One helper
        holds the late import, so each caller reads one line instead of three.

    Args:
        names: The attribute names to look for, in order of preference.

    Returns:
        The attribute, or None when the module or the name is absent.
    """
    return find_attribute(load_optional_module(VERSIONS_MODULE), names)  # A missing module answers None.


def advanced_values(record: dict[str, Any]) -> dict[str, str]:
    """Return the text that each advanced upgrade control shows.

    Why:
        Issue #2156 draws nine advanced controls, and a saved run must reopen
        with every choice still shown. `upgrade/options.py` owns the storage
        shape of those choices, so it owns the flattening. This seam keeps the
        route working through a build stage in which that module does not
        import, the same rule that every other seam of this route follows.

    Args:
        record: The stored run record.

    Returns:
        The text of each advanced control, or an empty mapping when the module
        is absent. Every control then shows the cloud default.
    """
    reader = module_attribute(ADVANCED_ATTRIBUTES)  # The module owns every rule of the shape.
    if not callable(reader):  # A missing module must draw an empty control, never a fault page.
        return {}
    values: Any = reader(record.get("options", {}))  # One flat mapping of text values.
    shown = dict(values)
    _add_schedule_preview(shown, record.get("options", {}))  # Issue #2187 names the moment behind each duration.
    return shown


def _add_schedule_preview(shown: dict[str, str], options: Mapping[str, Any]) -> None:
    """Add the moment that each schedule duration names, if the run started now.

    Why:
        Issue #2187 replaces the epoch second with a duration. The operator
        reads the intent on the confirmation page, and the intent alone does not
        say when the firmware moves. This preview names the moment as well.

        The text carries the word "about" and the condition of the start,
        because the operator has not started the job yet. A page that named one
        exact moment would state a falsehood the moment the operator paused.

    Args:
        shown: The control text of the run. The function changes it in place.
        options: The stored option record of the run.
    """
    schedule = options.get("schedule") if isinstance(options.get("schedule"), Mapping) else {}
    now = int(time.time())  # The preview counts from this read, and the start moves it.
    for field in ("start_time", "reboot_at"):
        seconds = schedule.get(f"{field}_after") if isinstance(schedule, Mapping) else None
        if not isinstance(seconds, int):
            continue  # A run with no duration shows no preview line.
        moment = datetime.fromtimestamp(now + seconds, tz=UTC)
        shown[f"{field}_preview"] = f"about {moment.strftime('%Y-%m-%d %H:%M UTC')} if you start now"


def options_view(record: dict[str, Any]) -> dict[str, Any]:
    """Build the device rows and the version map that the options page draws.

    Why:
        The page drew only the rows that the run record already held, and a new
        run holds none. The page therefore showed no device, the browser found
        no version control to read, and the saved target list stayed empty. This
        function reads the site inventory once, so the operator sees a device on
        the first view and sees the same version list on every later view. A
        ready map, a missing module, and a signed-out session each keep the
        earlier answer, so no test and no offline view reaches the cloud.

    Args:
        record: The stored run record.

    Returns:
        The `targets` rows and the `versions_by_model` map that the page reads.
    """
    stored = list(record.get(TARGETS_FIELD) or [])  # A second view holds the choice of the first one.
    ready = version_index(injected_object(VERSIONS_KEY))  # A test injects the map, so no cloud read runs.
    session = cloud_session()  # The sign-in built this session, and the record never carries one.
    builder = injected_object(OPTIONS_VIEW_KEY) or module_attribute(VIEW_ATTRIBUTES)  # The seam, then the module.
    if ready or session is None or not callable(builder):  # Any one of the three already answers the page.
        return {
            TARGETS_FIELD: stored,
            VIEW_VERSIONS_FIELD: ready,
            "type_selections": {},
            "selected_types": list(record.get("selected_types", ["ap", "switch", "gateway"])),
        }
    site_id = str(record.get("site_id", ""))  # FR-014 binds one run to one site, so one site scopes the read.
    try:  # The builder reaches the cloud, and the cloud refuses and times out.
        answer = dict(builder(session, str(record.get("org_id", "")), site_id))
    except Exception:  # A page with no row beats a page that shows a fault to the operator.
        logger.warning("upgrade: the inventory read of the site %s did not answer", site_id)  # No stack trace.
        return {
            TARGETS_FIELD: stored,
            VIEW_VERSIONS_FIELD: ready,
            "type_selections": {},
            "selected_types": list(record.get("selected_types", ["ap", "switch", "gateway"])),
        }
    selected_types = record.get("selected_types")
    if not isinstance(selected_types, list):
        selected_types = answer.get("selected_types")
    return {
        TARGETS_FIELD: stored or list(answer.get(TARGETS_FIELD, [])),  # A saved choice outranks a fresh read.
        VIEW_VERSIONS_FIELD: version_index(answer.get(VIEW_VERSIONS_FIELD)),  # One version list for each model.
        "type_selections": dict(answer.get("type_selections", {})),
        "selected_types": list(selected_types) if isinstance(selected_types, list) else ["ap", "switch", "gateway"],
    }


def composed_options(record: dict[str, Any], body: dict[str, Any]) -> dict[str, Any] | None:
    """Build the stored target list from the browser choices and the site read.

    Why:
        The browser sends only a MAC address and a target version for each
        device, but `to_device_targets` reads the device type and the run driver
        reads the gateway family, the scope, and the first uptime. Only a site
        read fills those fields. A thin row would reach the driver, raise a key
        fault inside the plan builder, and send no device to the cloud.

    Args:
        record: The stored run record.
        body: The request body of the save call.

    Returns:
        The full record, or None when no session and no site read answers.

    Raises:
        ValueError: When one choice names an unknown device or a refused option.
    """
    session = cloud_session()  # The sign-in built this session, and the record never carries one.
    builder = module_attribute(RECORD_ATTRIBUTES)  # The module owns every rule of the mapping.
    if session is None or not callable(builder):  # No session and no module both fall back to the body.
        return None
    site_id = str(record.get("site_id", ""))  # FR-014 binds one run to one site, so one site scopes the read.
    try:  # The builder reaches the cloud, and the cloud refuses and times out.
        answer: Any = builder(session, str(record.get("org_id", "")), site_id, body)
    except ValueError:  # A refused option must reach the operator as a named field, not as a silent echo.
        raise
    except Exception as failure:  # An unavailable current read must not turn stale browser data into a plan.
        logger.warning("upgrade: the inventory read of the site %s did not answer", site_id)  # No stack trace.
        raise ValueError("the current target availability could not be verified") from failure
    return dict(answer) if answer else None  # An empty answer means the read named no device.


@upgrade_bp.get(VERSIONS_PATH)
@identity.require_session
def run_versions(run_id: str) -> tuple[Response, int]:
    """Answer the version list of each model that one run may install.

    Why:
        `contracts/http-api.md` section 5 fixes this path, and
        `upgrade/options.html` states that this body fills the picker. The page
        renders before the cloud answers, so the picker needs a second read that
        it can repeat.

    Args:
        run_id: The run key.

    Returns:
        The version list of each model, or the refusal that names the missing run.
    """
    record = load_run(run_id)  # The run must exist before the portal reads a version for it.
    if record is None:  # A stale link and a hand-typed path both reach this route.
        return run_not_found()  # `contracts/http-api.md` fixes this one code for every run path.
    by_model = read_versions(record)  # Empty while no seam is injected and the module is absent.
    logger.info("upgrade: the run %s may install a version of %s model(s)", run_id, len(by_model))  # AFTER.
    return jsonify({BY_MODEL_FIELD: by_model}), OK_STATUS  # The picker reads one list for each model.


# --------------------------------------------------------------------------
# The start.
# --------------------------------------------------------------------------


def start_refusal(record: dict[str, Any]) -> tuple[Response, int] | None:
    """Report the first rule that refuses the start of one run.

    Why:
        FR-033 to FR-035 guard the start with three separate rules. One function
        holds all three in their documented order, so the handler below stays
        inside the size limit and a reader finds every refusal in one place. A
        fourth rule guards the plan itself, because a start that sends nothing
        would still report a complete run and the operator would read that run
        as an upgrade of the whole site.

    Args:
        record: The run record the operator asks to start.

    Returns:
        The refusal answer, or None when every rule passes.
    """
    if confirmation_text() != CONFIRM_TEXT:  # FR-034 refuses any other text and any other letter case.
        return json_error(BAD_REQUEST_STATUS, CONFIRMATION_REQUIRED_CODE, CONFIRM_REQUIRED_MESSAGE)
    if not record.get(PRE_CAPTURE_FIELD):  # FR-035 refuses a start with no saved pre-check.
        return json_error(CONFLICT_STATUS, PRE_CAPTURE_MISSING_CODE, PRE_CAPTURE_MISSING_MESSAGE)
    refusal = lock_refusal(str(record.get("org_id", "")), str(record.get("site_id", "")))  # T182 asks for this.
    if refusal is not None:  # Another operator holds the site, or the portal cannot read the lock.
        return refusal  # Warning: without this line a second upgrade can reach a live site.
    if not record.get(TARGETS_FIELD):  # An operator who saved no version reaches this line.
        return json_error(CONFLICT_STATUS, TARGETS_MISSING_CODE, TARGETS_MISSING_MESSAGE)
    return None  # Every rule passed, so the handler sends the upgrade.


def launch_run(record: dict[str, Any]) -> None:
    """Hand one prepared run record to the run driver.

    Why:
        The driver needs a store, a phase gate, a capture starter, and an upgrade
        submitter. That wiring belongs to the driver work, so this function only
        calls the seam and names the gap while the seam is unset. FR-038 needs no
        guard here, because `RunDriver.start` answers with the live thread when
        one already owns the run.

    Args:
        record: The run record, already in the state `upgrade_submitting`.
    """
    launcher = run_launcher()  # None while the driver wiring is not in place.
    if launcher is None:  # The portal must still answer, and the operator must still learn the truth.
        logger.error("upgrade: %s so the run %s sent nothing", NO_LAUNCHER_MESSAGE, record["run_id"])  # The gap.
        return  # The poll then shows the run held at `upgrade_submitting`.
    launcher(record)  # The driver owns every phase from this moment.


@upgrade_bp.post(START_PATH)
@identity.require_session
def start_run(run_id: str) -> tuple[Response, int]:
    """Send the upgrade of one run after the operator types the word `CONFIRM`.

    Why:
        FR-038 accepts one begin action for each run, even across several browser
        tabs. A second call therefore reports the state that the run already
        holds and sends nothing.

    Args:
        run_id: The run key.

    Returns:
        The state the run now holds, or a refusal.
    """
    record = load_run(run_id)  # The run must exist before it starts.
    if record is None:  # A stale link and a hand-typed path both reach this route.
        return run_not_found()  # One code for every run path.
    refusal = start_refusal(record)  # The three rules of FR-033 to FR-035, plus the lock check of T182.
    if refusal is not None:  # One rule refused, and the answer already names which one.
        return refusal  # The operator reads the code and the cure.
    machine = RunStateMachine()  # One state model distinguishes a duplicate from a premature start.
    current = machine.read_state(record)  # The stored state decides whether this call may send firmware.
    if current is not RunState.AWAITING_CONFIRMATION:  # Only this state may start a new firmware submission.
        if (
            current in RunStateMachine.CHAIN[RunStateMachine.CHAIN.index(RunState.UPGRADE_SUBMITTING) :]
        ):  # Firmware submission already began.
            logger.info(
                "upgrade: the run %s already started, so this call sent nothing", run_id
            )  # AFTER the state read.
            return jsonify({"state": current.value}), ACCEPTED_STATUS  # A duplicate start stays idempotent.
        logger.warning(
            "upgrade: the run %s cannot start from the state %s", run_id, current.value
        )  # The record needs recovery.
        return json_error(CONFLICT_STATUS, RUN_NOT_READY_CODE, RUN_NOT_READY_MESSAGE)  # Name the next operator action.
    logger.info("upgrade: start the run %s", run_id)  # BEFORE the state change.
    machine.advance(record, RunState.UPGRADE_SUBMITTING)  # The confirmation state permits this one move.
    if not save_run(record):  # The store reports the true result.
        return write_failed()  # No upgrade goes out while the record says the run never started.
    logger.info("upgrade: the run %s holds the state %s", run_id, record["state"])  # AFTER the state change.
    launch_run(record)  # The driver owns every phase from this moment.
    return jsonify({"state": record["state"]}), ACCEPTED_STATUS


# --------------------------------------------------------------------------
# The status poll and the pages.
# --------------------------------------------------------------------------


@upgrade_bp.get(STATUS_PATH)
@identity.require_session
def run_status(run_id: str) -> tuple[Response, int]:
    """Answer the state of one run for the browser poll.

    Why:
        FR-039 asks the page to refresh every 30 seconds with no operator
        action, so this route answers from the run record alone and reads no
        cloud. `RunStatusView` owns the whole body shape, so no field of the
        contract is built twice.

    Args:
        run_id: The run key.

    Returns:
        The status body, or the run refusal.
    """
    record = load_run(run_id)  # One read of the shared record, and no cloud call at all.
    if record is None:  # A poll may outlive the run it watches.
        return run_not_found()  # One code for every run path.
    return jsonify(RunStatusView().build(record)), OK_STATUS  # The view owns every field of the body.


def run_is_live(record: dict[str, Any]) -> bool:
    """Report whether a stop can still change one run.

    Why:
        `RunStateMachine.read_state` refuses a name outside the model, which is
        the correct rule at the edge of a write. A page read must not fault on
        the same name, so an unknown state counts as a run that no stop reaches.

    Args:
        record: The run record the page shows.

    Returns:
        True while the run still accepts a stop.
    """
    try:  # An absent run and a damaged record both reach this line.
        state = RunStateMachine.read_state(record)  # Refuses any name outside the model.
    except RunTransitionError:  # No state at all, so the page offers no stop control.
        return False  # The safe answer, because a stop would reach nothing.
    return state not in RunStateMachine.TERMINAL  # A final run accepts no stop.


def site_labels(record: dict[str, Any]) -> dict[str, str]:
    """Build the two site values that one upgrade page shows.

    Why:
        Issue #2100 asks the options page, the confirm page, and the run page to
        name the site in words. Each page also keeps the site identifier, because
        an operator quotes that identifier in a support case.

        A record with an empty stored name falls back to the identifier. The
        operator then reads a value instead of a blank field.

    Args:
        record: The run record the page shows. May be empty.

    Returns:
        The site name and the site identifier of the page.
    """
    site_id = str(record.get("site_id", ""))  # FR-014 binds one run to one site.
    stored = str(record.get("site_name", "")).strip()  # A stored blank must not reach the page.
    logger.debug("upgrade: the site %s reads as the name %s", site_id, stored or site_id)  # A poll renders this.
    return {"site_name": stored or site_id, "site_id": site_id}  # Both values reach every one of the three pages.


def stop_control_state(record: dict[str, Any]) -> dict[str, Any]:
    """Build the two values that the stop partial reads.

    Why:
        `upgrade/progress.html` includes `upgrade/stop.html`, so the run page
        must carry the partial values as well as its own. FR-038a shows the stop
        control while an upgrade runs and hides it once the run is final.

    Args:
        record: The run record the page shows.

    Returns:
        The stop outcome record and the availability of the stop control.
    """
    request_record = StopRequestStore(run_store()).read(str(record.get("run_id", "")))  # None until a stop.
    outcome = request_record.outcome if request_record is not None else None  # None until the cancels report.
    held = outcome.to_record() if outcome is not None else None  # The template holds a default for None.
    return {"stop_outcome": held, "stop_available": run_is_live(record)}


def run_lock_banner(record: dict[str, Any]) -> dict[str, Any]:
    """Build the six values that the site lock banner of a run page reads.

    Why:
        `select.lock_banner_context` owns every rule of the banner, and it needs
        an organization and a site. A run page names a run alone, so this
        function reads the two values from the run record. The session cannot
        answer instead, because an operator may open a run of one site while the
        session names another site.

        An absent run leaves both values empty, which renders the banner in the
        `site_unknown` state. That is the answer `contracts/site-lock.md` asks a
        page with no site to show, so a missing run still renders.

    Args:
        record: The run record the page shows. May be empty.

    Returns:
        The template context of the banner.
    """
    org_id = str(record.get("org_id", ""))  # The run record carries its own scope, as the status route does.
    site_id = str(record.get("site_id", ""))  # FR-014 binds one run to one site.
    return lock_banner_context(org_id, site_id)


@upgrade_bp.get(RUN_PAGE_PATH)
@identity.require_session
def run_page(run_id: str) -> str:
    """Render the live run view of one run.

    Why:
        The page includes the site lock banner. FR-072 gives one site to one
        operator, so the operator must read who holds the site. The run record
        names its own organization and site, and the session names neither once
        the operator opens a run in a second tab.

    Args:
        run_id: The run key.

    Returns:
        The rendered page.
    """
    record = load_run(run_id) or {}  # An absent run still renders, so the operator reads a page and not a fault.
    poll_seconds = current_app.config.get("POLL_INTERVAL_SECONDS", 30)  # Decision D3 fixes this period.
    logger.info("upgrade: show the run page of %s", run_id)  # One line for each page read.
    context = {
        **site_labels(record),  # Issue #2100 names the site in words and keeps the identifier.
        **stop_control_state(record),  # The two values that the included stop partial reads.
        **run_lock_banner(record),  # The six values that the included lock banner reads.
    }  # One merged dict, because the banner repeats `site_id` and a second splat of it would fault.
    return render_page(
        PROGRESS_TEMPLATE,
        run_id=run_id,  # The page builds every control identifier from this value.
        status=RunStatusView().build(record),  # The same body that the poll answers.
        poll_interval_seconds=poll_seconds,  # The script reads this through `data-poll-seconds`.
        **context,  # The site labels, the stop partial values, and the lock banner values.
    )


@upgrade_bp.get(OPTIONS_PAGE_PATH)
@identity.require_session
def options_page(run_id: str) -> str:
    """Render the version picker and the three option controls of one run.

    Why:
        The page includes the site lock banner, because a saved option writes to
        the site. FR-072 gives one site to one operator, so the operator must
        read who holds the site before the save call. The rows come from
        `options_view`, because a new run holds no row of its own and the
        operator must still see every device of the site.

    Args:
        run_id: The run key.

    Returns:
        The rendered page.
    """
    record = load_run(run_id) or {}  # An absent run still renders an empty picker.
    view = options_view(record)  # The site inventory fills a new run, and a saved choice outranks it.
    logger.info("upgrade: show the options page of %s with %s device(s)", run_id, len(view[TARGETS_FIELD]))
    context = {
        **site_labels(record),  # Issue #2100 names the site in words and keeps the identifier.
        **run_lock_banner(record),  # The six values that the included lock banner reads.
    }  # One merged dict, because the banner repeats `site_id` and a second splat of it would fault.
    return render_page(
        OPTIONS_TEMPLATE,
        run_id=run_id,  # The page builds every control identifier from this value.
        targets=view[TARGETS_FIELD],  # One row for each device of the site.
        versions_by_model=view[VIEW_VERSIONS_FIELD],  # One version list for each model of those rows.
        type_selections=view.get("type_selections", {}),  # The safe common targets of each device type.
        options=record.get("options", {}),  # The three controls show the saved choice.
        advanced=advanced_values(record),  # Issue #2156 reopens every advanced control with its saved value.
        warnings=[],  # The save call answers the warnings, so the first read of the page shows none.
        **context,  # The site labels and the lock banner values.
    )


@upgrade_bp.get(CONFIRM_PAGE_PATH)
@identity.require_session
def confirm_page(run_id: str) -> str:
    """Render the last page before the portal sends any upgrade.

    Why:
        FR-035 keeps the begin control locked until a verified pre-check exists.
        The template defaults `pre_capture_verified` to false, so this route
        names the value and the page never unlocks by accident.

    Args:
        run_id: The run key.

    Returns:
        The rendered page.
    """
    record = load_run(run_id) or {}  # An absent run renders a locked page, which is the safe answer.
    logger.info("upgrade: show the confirmation page of %s", run_id)  # One line for each page read.
    return render_page(
        CONFIRM_TEMPLATE,
        run_id=run_id,  # The page builds every control identifier from this value.
        targets=record.get(TARGETS_FIELD, []),  # The operator reads the whole list one last time.
        options=record.get("options", {}),  # The three controls show the saved choice.
        advanced=advanced_values(record),  # Issue #2156 names every advanced control before the firmware moves.
        warnings=record.get(WARNINGS_FIELD, []),  # Issue #2003: the last page repeats the saved warning list.
        pre_capture_id=record.get(PRE_CAPTURE_FIELD),  # Names the saved pre-check, or None.
        pre_capture_verified=bool(record.get(PRE_CAPTURE_FIELD)),  # FR-035 unlocks the control on this value.
        **site_labels(record),  # Issue #2100 names the site in words and keeps the identifier.
    )


# --------------------------------------------------------------------------
# The stop.
# --------------------------------------------------------------------------


def stop_refusal(failure: StopRequestError) -> tuple[Response, int]:
    """Map one stop request failure onto the documented answer.

    Why:
        `runtime/signals.py` already carries the machine code on each error
        class, so this function maps the class to a status and repeats no code.
        The 409 of a run that cannot stop reads `run_not_stoppable`, which is a
        different word from the 409 `site_locked` of a held site, so the browser
        tells the two apart.

    Args:
        failure: The error that the stop store raised.

    Returns:
        The refusal answer.
    """
    if isinstance(failure, ConfirmationRequiredError):  # FR-038b refuses any other word and any other case.
        return json_error(BAD_REQUEST_STATUS, CONFIRMATION_REQUIRED_CODE, STOP_REQUIRED_MESSAGE)
    if isinstance(failure, RunNotFoundError):  # The run never existed, or it left the store.
        return run_not_found()  # One code for every run path.
    if isinstance(failure, RunNotStoppableError):  # The run already reached a final state.
        return json_error(CONFLICT_STATUS, RUN_NOT_STOPPABLE_CODE, str(failure))
    return json_error(SERVER_ERROR_STATUS, failure.code, str(failure))  # The store refused the write itself.


def stop_lock_refusal(record: dict[str, Any]) -> tuple[Response, int] | None:
    """Refuse a stop when a different operator holds the site of the run.

    Why:
        FR-038i binds the stop control to the operator that holds the site lock.
        Without this check any signed-in operator cancels the upgrade of any
        other operator. The run record names its own organization and its own
        site, so this check reads no value out of the session and no value out
        of the request body.

    Args:
        record: The run record that the stop acts on.

    Returns:
        The 409 answer that names the holder, the 503 answer for an unreadable
        lock store, or None when the stop may run.
    """
    org_id = str(record.get("org_id", ""))  # The run record carries its own scope.
    site_id = str(record.get("site_id", ""))  # FR-014 binds one run to one site.
    if not org_id or not site_id:  # An absent run and a damaged record both reach here.
        return None  # The stop store still answers `run_not_found` for a run it does not hold.
    return lock_refusal(org_id, site_id)  # The refusal names the operator to ask, or names the unreadable store.


def cancel_outcome(run_id: str) -> StopOutcome:
    """Run the cancel work of one stop and return what it achieved.

    Why:
        FR-038f forbids a claim of a cancel that never happened. While the cancel
        work is not wired, the three lists therefore stay empty and the message
        states only what the portal did do, which is to stop starting devices.

    Args:
        run_id: The run key.

    Returns:
        The cancelled list, the continuing list, the gap list, and one sentence.
    """
    runner = stop_runner()  # The stop work injects one callable here.
    if runner is None:  # No cancel call went out, so the answer must claim none.
        return StopOutcome(message=STOP_RECORDED_MESSAGE)  # Three empty lists and one true sentence.
    answer: Any = runner(run_id)  # The module owns every cancel call and every device name.
    return answer if isinstance(answer, StopOutcome) else StopOutcome(message=STOP_RECORDED_MESSAGE)


def move_to_stopping(record: dict[str, Any]) -> str:
    """Move one run into the state `stopping` and write the record.

    Why:
        `StopRequestStore.request` writes the request and the change time only,
        and it leaves `state` to the state machine on purpose. The contract
        answers `{"state": "stopping"}`, so this function performs that move.

    Args:
        record: The run record that now holds the stop request.

    Returns:
        The state the run holds after the move.
    """
    try:  # A run that reached a final state between the two reads must not raise a fault page.
        RunStateMachine().advance(record, RunState.STOPPING)
    except RunTransitionError:  # The run already stops, or it already finished.
        return str(record.get("state", ""))  # The operator reads the true state, whatever it is.
    save_run(record)  # A failed write leaves the request in place, and the driver still reads it.
    return str(record.get("state", ""))  # The contract answers this value to the browser.


def outcome_is_recorded(record: Mapping[str, Any]) -> bool:
    """Report whether the run record already names the outcome of its stop.

    Why:
        Two layers can write this one value. `stop.stop_run_and_record` writes
        it whenever a cancel call reaches the cloud, and the stop route writes
        it on every other path. This reader lets the route see the earlier
        write and skip a second write of the same value.

    Args:
        record: The run record, read after the cancel work finished.

    Returns:
        True when the stop request of the record names an outcome.
    """
    request = record.get("stop_request")  # `StopRequest.to_record` holds a null here until a cancel reports.
    return isinstance(request, Mapping) and request.get("outcome") is not None  # A null means no write yet.


def record_stop_outcome(store: Any, run_id: str, outcome: StopOutcome) -> dict[str, Any]:
    """Write the outcome of one stop unless the cancel layer already wrote it.

    Why:
        FR-038h asks the record to hold the whole stop. `stop.stop_run_and_record`
        owns that write, but it runs only when the run holds an accepted upgrade
        call and a cloud session. An operator who stops a run before the first
        accepted call reaches neither, so this route keeps its own write for that
        path. The route reads the record here in any case, because the state move
        below needs the record that the cancel layer may have changed.

    Args:
        store: The run record store of this request.
        run_id: The run key.
        outcome: The three device lists and the message of this stop.

    Returns:
        The run record as it stands after the write.
    """
    written = load_run(run_id) or {}  # The cancel layer writes through a store of its own, so read the record.
    if outcome_is_recorded(written):  # `stop.stop_run_and_record` already wrote this same value.
        return written  # One write saved, and the record already answers FR-038h.
    StopRequestStore(store).record_outcome(run_id, outcome)  # FR-038h records the whole stop.
    return load_run(run_id) or {}  # Read again, because this write changed the record.


@upgrade_bp.post(STOP_PATH)
@identity.require_session
def stop_run(run_id: str) -> tuple[Response, int]:
    """Stop one running upgrade after the operator types the word `STOP`.

    Why:
        FR-038c cancels every device that has not started, and FR-038d never
        interrupts a device that already writes firmware. FR-038i lets only the
        operator that holds the site lock reach this control. The record read
        therefore runs first, because the record names the site of the run. The
        stop store records the request next, so the driver reads it even when
        the cancel calls take time.

    Args:
        run_id: The run key.

    Returns:
        The state of the run and the outcome of the cancel work, or a refusal.
    """
    record = load_run(run_id) or {}  # Read first, because the record names the site the lock guards.
    refusal = stop_lock_refusal(record)  # FR-038i binds this control to the operator that holds the site.
    if refusal is not None:  # Another operator holds the site, so this stop writes nothing at all.
        return refusal  # The 409 answer names that operator.
    store = run_store()  # One store serves the request, the outcome, and the state move.
    logger.info("upgrade: stop the run %s", run_id)  # BEFORE the change.
    try:  # Every refusal of the stop store carries its own machine code.
        StopRequestStore(store).request(run_id, actor_address(), confirmation_text())
    except StopRequestError as failure:  # One clause catches all four documented failures.
        return stop_refusal(failure)  # The answer names the code and the cure.
    outcome = cancel_outcome(run_id)  # FR-038e names each cancelled and each continuing device.
    written = record_stop_outcome(store, run_id, outcome)  # The cancel layer may have written the outcome.
    state = move_to_stopping(written)  # The contract answers `stopping`, so the state moves here.
    logger.info("upgrade: the run %s holds the state %s", run_id, state)  # AFTER the change.
    return jsonify({"state": state, "outcome": outcome.to_record()}), OK_STATUS
