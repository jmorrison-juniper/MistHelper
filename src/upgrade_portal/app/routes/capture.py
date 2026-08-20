"""The capture routes: the start, the progress poll, the read, and the page.

Why:
    A capture reads a whole site. A large site takes minutes, and a request that
    waits that long dies at the proxy. `contracts/http-api.md` therefore splits
    the work in two. `POST /api/sites/<site_id>/captures` answers 202 at once and
    hands the reading to a worker thread. The browser then polls
    `GET /api/captures/<id>/status` every 30 seconds. The portal sends no
    server-sent event, because the existing event bus caps at ten subscribers.

Route names:
    Another module renders the page and the browser script against these names,
    so the names are a contract and no rename is safe: `capture.start_capture`,
    `capture.capture_status`, `capture.read_capture`, and `capture.capture_page`.

Seams:
    Three parts of this feature arrive beside this module. The collection work,
    the stored capture reader, and the site lock all travel through a seam: an
    injected callable in the application configuration first, then a late import
    of the real module. Nothing here imports either module while this module
    loads, so the portal starts today and picks up each module on the day it
    lands. A contract test injects a stand-in and reaches no network.

Where the progress lives:
    In this process, in one guarded dictionary. The status of a running capture
    is worth nothing after a restart, because the capture died with the worker.
    A finished capture lives in the store instead, and the status route reads it
    from there once the progress record is gone.
"""

from __future__ import annotations  # Every annotation stays text, so a name may appear before its class.

import logging  # The portal logs with the standard library only.
import threading  # One worker thread for each capture, and one guard for the progress store.
import uuid  # Names a run that the operator started without one.
from collections.abc import Callable  # Types each injected seam.
from typing import Any  # A capture document and an injected seam are both free-form.

from flask import Blueprint, Response, jsonify, request  # The web framework of the portal.

from ...runtime import identity  # The real session guard. No copy of it lives here.
from ..factory import json_error  # The one error envelope that the contract allows.
from .select import (  # The sibling module owns these rules, so no copy of them lives here.
    find_attribute,
    find_site,
    injected_seam,
    load_optional_module,
    lock_banner_context,
    org_display_name,
    read_site_locks,
    render_page,
    resolve_org,
)

logger = logging.getLogger(__name__)  # One logger for each module keeps the source visible in the log.

capture_bp = Blueprint("capture", __name__)  # No URL prefix, because the paths span `/captures` and `/api`.

# Each route declares a full path, so a reader finds the whole path in one place.
START_PATH = "/api/sites/<site_id>/captures"  # The start of one capture.
STATUS_PATH = "/api/captures/<capture_id>/status"  # The poll target of the browser.
READ_PATH = "/api/captures/<capture_id>"  # The whole capture document.
PAGE_PATH = "/captures/<capture_id>"  # The human view of one capture.

CAPTURE_TEMPLATE = "capture/capture.html"  # The page that starts a capture and shows its progress.

RUNNER_KEY = "CAPTURE_RUNNER"  # The seam for the collection work.
LOADER_KEY = "CAPTURE_LOADER"  # The seam for the stored capture reader.

STORE_MODULE = "capture.store"  # Built by the storage work of this phase.
ASSEMBLY_MODULE = "capture.assembly"  # Built by the assembly work of this phase.
COLLECTOR_MODULE = "capture.collector"  # The module that reads a whole site.

LOADER_ATTRIBUTES = ("load_capture", "read_capture", "get_capture")  # The first match wins.
KEY_ATTRIBUTES = ("capture_key", "build_capture_key")  # The identifier shape belongs to the assembly module.
COLLECTOR_ATTRIBUTES = ("run_capture", "collect_capture", "capture_site")  # The same rule for the collector.

TIER_FIELD = "tier"  # The body field that names the data tier.
RUN_FIELD = "run_id"  # The body field that names the owning run.
ROLE_FIELD = "role"  # The body field that names the half of the run.

TIER_STANDARD = 2  # The device state and the client lists.
TIER_EXTRA = 3  # Tier 2, the port state, the radio state, and the alarms.
KNOWN_TIERS = (TIER_STANDARD, TIER_EXTRA)  # Any other value is a refusal.
DEFAULT_ROLE = "pre"  # `contracts/http-api.md` names the pre-check half as the default.
FIRST_ORDINAL = 1  # The first capture of a run.
RUN_PREFIX = "run-"  # `runtime/runs.py` builds a run key with this prefix.
KEY_PREFIX = "cap-"  # `data-model.md:45` names this prefix for a capture key.

# `contracts/http-api.md` lists these six section names in the status body, and
# `capture/capture.html` renders one row for each name.
SECTION_NAMES = ("devices", "clients_wired", "clients_wireless", "clients_guest", "extras", "alarms")  # Row order.
EXTRA_SECTIONS = ("extras", "alarms")  # Tier 2 reads neither of these two.

SECTION_PENDING = "pending"  # The section is waiting for its turn.
SECTION_DONE = "done"  # The section is read.
SECTION_SKIPPED = "skipped"  # This tier does not read the section at all.
SECTION_FAILED = "failed"  # The read of this section did not finish.

STATE_PENDING = "pending"  # The capture is queued and has read nothing yet.
STATE_COLLECTING = "collecting"  # The capture is reading the cloud.
STATE_VERIFIED = "verified"  # The portal read the stored key back unchanged.
STATE_FAILED = "failed"  # The capture stopped before it wrote anything.

# The seven fields that `tasks.md` T059 names, and the identifier that the
# contract sample carries beside them. The status body holds these fields and no
# other, so an internal field of the progress record never reaches the browser.
STATUS_FIELDS = (  # A field that is absent here never reaches the browser.
    "capture_id",
    "state",
    "percent",
    "sections",
    "counts",
    "partial_reasons",
    "verified",
    "message",
)

START_PERCENT = 0  # A capture that has read nothing shows no progress.
WHOLE_PERCENT = 100  # A finished capture shows the whole bar.
POLL_SECONDS = 30  # Decision D3 of the plan fixes this period.

# The progress store keeps the newest captures only. A portal that runs for
# weeks would otherwise hold one record for every capture it ever started.
PROGRESS_LIMIT = 200  # Two hundred records cover a whole day of work at a small cost.

BAD_TIER_CODE = "bad_tier"  # `contracts/http-api.md` fixes this code for an unknown tier.
SITE_NOT_FOUND_CODE = "site_not_found"  # The same code that the inventory route answers.
SITE_LOCKED_CODE = "site_locked"  # Another operator holds the site.
CAPTURE_NOT_FOUND_CODE = "capture_not_found"  # No such capture.
CAPTURE_NOT_VERIFIED_CODE = "capture_not_verified"  # `contracts/http-api.md:176` fixes this code.
CAPTURE_TOO_NEW_CODE = "schema_version_too_new"  # `capture.store.REASON_SCHEMA_TOO_NEW` names this refusal.

BAD_TIER_MESSAGE = "Choose the data tier 2 or the data tier 3."  # Names both legal values.
SITE_NOT_FOUND_MESSAGE = "The portal found no such site in this organization."  # Names the scope.
SITE_LOCKED_MESSAGE = "Another operator holds this site. Wait for that run to end."  # Names the cure.
CAPTURE_NOT_FOUND_MESSAGE = "The portal holds no capture with that identifier."  # No cure.
CAPTURE_NOT_VERIFIED_MESSAGE = "The portal did not read this capture back, so it may not be compared."  # Why.
CAPTURE_TOO_NEW_MESSAGE = "A later version of the portal wrote this capture. Upgrade the portal to read it."  # Cure.

START_MESSAGE = "The portal queued the capture."  # The first panel text.
COLLECTING_MESSAGE = "The portal is reading the site."  # The panel text while the worker runs.
NO_COLLECTOR_MESSAGE = "The portal cannot read a site yet, because the collection module is missing."  # Gap.
FAILED_MESSAGE = "The capture stopped. Read the portal log for the cause."  # The cause stays in the log.

OK_STATUS = 200  # The read succeeded.
ACCEPTED_STATUS = 202  # The portal took the work and answered before it ended.
BAD_REQUEST_STATUS = 400  # The portal could not read the request.
NOT_FOUND_STATUS = 404  # No such site, or no such capture.
CONFLICT_STATUS = 409  # The site is held, or the capture is not fit to compare.
SERVER_ERROR_STATUS = 500  # A part of the portal is missing, so the read cannot run.

# Every refusal that the stored capture reader reports. A reason that is absent
# here is a fault of the portal, so the caller reads 500 and never a 404 that
# would send the operator to start the whole capture again.
REFUSAL_STATUS: dict[str, int] = {  # One status for each reason the store reports.
    CAPTURE_NOT_FOUND_CODE: NOT_FOUND_STATUS,
    CAPTURE_NOT_VERIFIED_CODE: CONFLICT_STATUS,
    CAPTURE_TOO_NEW_CODE: CONFLICT_STATUS,  # The record is present, so the fault is not the request.
}
REFUSAL_MESSAGE: dict[str, str] = {  # One text for each reason, in the words of the operator.
    CAPTURE_NOT_FOUND_CODE: CAPTURE_NOT_FOUND_MESSAGE,
    CAPTURE_NOT_VERIFIED_CODE: CAPTURE_NOT_VERIFIED_MESSAGE,
    CAPTURE_TOO_NEW_CODE: CAPTURE_TOO_NEW_MESSAGE,
}

_PROGRESS: dict[str, dict[str, Any]] = {}  # The live progress of each capture of this process.
_PROGRESS_GUARD = threading.Lock()  # The worker writes and the poll reads, so both take the guard.


# --------------------------------------------------------------------------
# The progress store.
# --------------------------------------------------------------------------


def section_map(tier: int) -> dict[str, str]:
    """Build the first section map of one capture.

    Why:
        The capture page renders one row for each of the six sections before the
        reading starts. A tier 2 capture never reads the extra sections, so the
        page shows those two as skipped and the operator waits for four rows.

    Args:
        tier: The data tier of the capture.

    Returns:
        One state for each section name.
    """
    skipped = tier < TIER_EXTRA  # Tier 2 reads neither extra section.
    return {  # One row for each name, so the page paints the whole list at once.
        name: SECTION_SKIPPED if skipped and name in EXTRA_SECTIONS else SECTION_PENDING for name in SECTION_NAMES
    }


def blank_status(capture_id: str, tier: int) -> dict[str, Any]:
    """Build the progress record of one capture that has read nothing yet.

    Args:
        capture_id: The identifier of the capture.
        tier: The data tier of the capture.

    Returns:
        The progress record.
    """
    return {  # The contract fixes each name below, so the poll needs no second shape.
        "capture_id": capture_id,
        "state": STATE_PENDING,
        "percent": START_PERCENT,
        "sections": section_map(tier),
        "counts": {},
        "partial_reasons": [],
        "verified": False,
        "message": START_MESSAGE,
    }


def opening_record(job: dict[str, Any]) -> dict[str, Any]:
    """Build the first progress record of one started capture.

    Why:
        The page shows the site, the run, and the tier while the capture runs,
        and the poll body must show none of them. Both readings come from this
        one record, because `status_body` drops every field the contract omits.

    Args:
        job: The capture job that the start route built.

    Returns:
        The progress record.
    """
    record = blank_status(str(job["capture_id"]), int(job[TIER_FIELD]))  # The empty shape first.
    record.update({name: job[name] for name in (TIER_FIELD, RUN_FIELD, ROLE_FIELD, "site_id")})  # Page fields.
    return record  # The poll drops the four page fields again.


def trim_progress() -> None:
    """Drop the oldest progress records once the store passes its limit.

    Why:
        A portal that runs for weeks would otherwise hold one record for every
        capture it ever started. The caller already holds the guard.
    """
    while len(_PROGRESS) > PROGRESS_LIMIT:  # A plain dictionary keeps the insertion order.
        _PROGRESS.pop(next(iter(_PROGRESS)))  # The oldest record goes first.


def open_progress(capture_id: str, record: dict[str, Any]) -> None:
    """Add one progress record to the store.

    Args:
        capture_id: The identifier of the capture.
        record: The first progress record of that capture.
    """
    with _PROGRESS_GUARD:  # The worker thread reads the same store.
        _PROGRESS[capture_id] = record  # The poll finds the record before the worker starts.
        trim_progress()  # The oldest records leave under the same guard.


def record_status(capture_id: str, **changes: Any) -> None:
    """Write new values into the progress record of one capture.

    Why:
        The worker reports its progress from another thread. One guarded writer
        keeps the poll and the worker from reading a half-written record.

    Args:
        capture_id: The identifier of the capture.
        **changes: The fields to write.
    """
    with _PROGRESS_GUARD:  # The poll reads this store from another thread.
        record = _PROGRESS.get(capture_id)  # A trimmed record reads as None.
        if record is not None:  # A capture the store dropped needs no update.
            record.update(changes)  # The poll then answers the new values.


def read_progress(capture_id: str) -> dict[str, Any] | None:
    """Read a copy of the progress record of one capture.

    Args:
        capture_id: The identifier of the capture.

    Returns:
        A copy of the record, or None when the store holds no record.
    """
    with _PROGRESS_GUARD:  # The worker writes this store from another thread.
        record = _PROGRESS.get(capture_id)  # A restart and a trim both empty this store.
        return dict(record) if record is not None else None  # A copy, so no caller writes the store.


def status_body(record: dict[str, Any]) -> dict[str, Any]:
    """Cut one progress record down to the fields the contract names.

    Why:
        The progress record also holds the site, the tier, and the run, which the
        page reads and the poll does not. One filter keeps every internal field
        out of the browser.

    Args:
        record: The progress record.

    Returns:
        The status body.
    """
    return {name: record[name] for name in STATUS_FIELDS if name in record}  # An absent field stays absent.


# --------------------------------------------------------------------------
# The seams.
# --------------------------------------------------------------------------


def capture_loader() -> Callable[..., Any] | None:
    """Return the callable that reads one stored capture.

    Returns:
        The injected reader, the reader of the store module, or None when
        neither exists yet.
    """
    injected = injected_seam(LOADER_KEY)  # A contract test injects the reader and reaches no database.
    return injected or find_attribute(load_optional_module(STORE_MODULE), LOADER_ATTRIBUTES)  # The real store.


def capture_runner() -> Callable[..., Any]:
    """Return the callable that performs the collection work.

    Why:
        A contract test injects a stand-in here and reads no cloud. The default
        runner reaches the collection module through the same seam rule, so this
        module needs no change on the day that module lands.

    Returns:
        The injected runner, or the runner that calls the collection module.
    """
    return injected_seam(RUNNER_KEY) or default_runner  # The stand-in of a test wins over the real work.


def build_capture_id(run_id: str) -> str:
    """Build the identifier of one new capture.

    Why:
        `data-model.md:45` fixes the form `cap-{run_hex}-{ordinal:02d}`, and the
        assembly module owns that form. This function asks that module first, so
        the identifier the browser reads is the key the store writes.

    Args:
        run_id: The key of the owning run.

    Returns:
        The capture identifier.
    """
    builder = find_attribute(load_optional_module(ASSEMBLY_MODULE), KEY_ATTRIBUTES)  # None before that module lands.
    if builder is not None:  # The assembly module owns the one true form.
        return str(builder(run_id, FIRST_ORDINAL))  # The store writes the key this call returns.
    tail = run_id[len(RUN_PREFIX) :] if run_id.startswith(RUN_PREFIX) else run_id  # The same rule, spelled out.
    return f"{KEY_PREFIX}{tail.lower()}-{FIRST_ORDINAL:02d}"  # The lower case matches the key of the store.


def default_runner(job: dict[str, Any]) -> None:
    """Read one whole site through the collection module.

    Why:
        The collection module arrives beside this one. Until it lands, a start
        must still answer 202 and must still leave a record the operator can
        read, so this function marks the capture failed and names the cause.

    Args:
        job: The capture job that the start route built.
    """
    capture_id = str(job.get("capture_id", ""))  # The record that this worker reports on.
    collector = find_attribute(load_optional_module(COLLECTOR_MODULE), COLLECTOR_ATTRIBUTES)  # None until built.
    if collector is None:  # The collection module is not built yet.
        logger.error("capture: no collection module, so the capture %s cannot read the site", capture_id)  # Gap.
        record_status(capture_id, state=STATE_FAILED, message=NO_COLLECTOR_MESSAGE)  # The page names the gap.
        return  # The page then shows the fault instead of a bar that never moves.
    record_status(capture_id, state=STATE_COLLECTING, message=COLLECTING_MESSAGE)  # The bar starts to move.
    try:  # The collection reads a network, so any fault must stay inside the worker.
        collector(job)  # The whole read of one site runs here.
    except Exception:  # A worker that raises would leave the page waiting for ever.
        logger.exception("capture: the capture %s stopped", capture_id)  # The cause stays in the log.
        record_status(capture_id, state=STATE_FAILED, message=FAILED_MESSAGE)  # The page shows the short text.


def start_worker(job: dict[str, Any]) -> None:
    """Hand one capture job to a worker thread.

    Why:
        FR-021 to FR-028 describe a read of a whole site, which takes minutes.
        The runner binds here, inside the request, so the worker needs no
        application context and no second lookup of the seam.

    Args:
        job: The capture job that the start route built.
    """
    runner = capture_runner()  # Bound now, because the worker sees no request.
    worker = threading.Thread(  # A daemon thread never holds the portal open at shutdown.
        target=runner, args=(job,), name=f"capture-{job['capture_id']}", daemon=True
    )
    worker.start()  # The route answers 202 on the next line of its own body.


# --------------------------------------------------------------------------
# The request body of the start route.
# --------------------------------------------------------------------------


def request_body() -> dict[str, Any]:
    """Read the body of the current request as a dictionary.

    Why:
        The start button posts JSON, and a plain form post carries the same
        fields. A body of another shape reads as an empty body, so the route
        answers the tier refusal and never a fault page.

    Returns:
        The body fields, or an empty dictionary.
    """
    payload: Any = request.get_json(silent=True)  # A body that is not JSON reads as None, never a fault.
    if isinstance(payload, dict):  # The browser script path.
        return payload  # The fields arrive as the script sent them.
    return dict(request.form)  # The plain form path, and an empty dictionary for an empty body.


def tier_number(value: Any) -> int | None:
    """Read one tier field as a whole number.

    Why:
        A JSON body carries the tier as a number and a plain form post carries
        the same field as text. A true reads as the whole number 1 in Python, so
        a boolean must never pass as a tier.

    Args:
        value: The raw field value.

    Returns:
        The whole number, or None when the value is not one.
    """
    if isinstance(value, bool):  # A true would otherwise read as the tier 1.
        return None  # No boolean names a tier.
    if isinstance(value, str) and value.isdigit():  # The plain form path.
        return int(value)  # A form field arrives as text only.
    return value if isinstance(value, int) else None  # Text and every other shape read as no tier.


def read_tier(body: dict[str, Any]) -> int | None:
    """Read the data tier out of one request body.

    Why:
        `contracts/http-api.md` names 2 and 3, and names 2 as the default. Every
        other value is a refusal, so a typed 5 never starts a read that the
        portal cannot finish.

    Args:
        body: The request body.

    Returns:
        The tier, or None when the body names a value the portal does not read.
    """
    tier = tier_number(body.get(TIER_FIELD, TIER_STANDARD))  # An absent field reads as the default tier.
    return tier if tier in KNOWN_TIERS else None  # None never sits in the known tiers.


def job_context(site: dict[str, Any], org_id: str) -> dict[str, Any]:
    """Read the four job fields that only the request thread can supply.

    Why:
        The worker thread holds no request, so `runtime/identity.py` and a cloud
        read both answer nothing there. The route therefore reads all four
        values now. The cloud session holds an API token inside it, so no caller
        may log this record, or the job that carries it, as a whole.

    Args:
        site: The site record that `find_site` answered with.
        org_id: The organization that holds the site.

    Returns:
        The cloud session, the operator address, and both readable names.
    """
    record = identity.current_session()  # The guard ran first, so this record exists.
    site_id = str(site.get("id", ""))  # The identifier fills in when the record carries no name.
    return {  # Four values that the worker cannot read for itself.
        "cloud_session": record.cloud_session if record is not None else None,
        "actor_email": record.owner.actor_email if record is not None else "",
        "org_name": org_display_name(org_id),
        "site_name": str(site.get("name", site_id)),
    }


def build_job(site: dict[str, Any], org_id: str, tier: int, body: dict[str, Any]) -> dict[str, Any]:
    """Build the capture job that the worker reads.

    Args:
        site: The site record of the site the capture reads.
        org_id: The organization that holds the site.
        tier: The data tier of the capture.
        body: The request body, which may name the run and the role.

    Returns:
        The capture job.
    """
    run_id = str(body.get(RUN_FIELD) or f"{RUN_PREFIX}{uuid.uuid4().hex}")  # A start with no run names its own.
    return {  # The worker reads these eleven fields and nothing else.
        "capture_id": build_capture_id(run_id),
        "run_id": run_id,
        "ordinal": FIRST_ORDINAL,
        "role": str(body.get(ROLE_FIELD) or DEFAULT_ROLE),
        "org_id": org_id,
        "site_id": str(site.get("id", "")),
        "tier": tier,
        **job_context(site, org_id),
    }


def permitted_site(site_id: str, org_id: str) -> dict[str, Any] | None:
    """Return the record of one site that the chosen organization holds.

    Why:
        Two refusals share one answer: an operator that picked no organization,
        and an operator that named a site of another organization. A different
        answer for each would tell the caller that the site exists. One reader
        holds that rule, so the route reads as the list of refusals only.

    Args:
        site_id: The site the path named.
        org_id: The organization of the session, or an empty value.

    Returns:
        The site record, or None when either refusal applies.
    """
    if not org_id:  # The operator has picked no organization at all.
        return None  # The route then answers the refusal of an unknown site.
    return find_site(site_id, org_id)  # None means the organization holds no such site.


def actor_address() -> str:
    """Return the address of the signed-in operator.

    Why:
        The lock check must know who asks, so it can tell the holder apart from
        every other operator. `runtime/identity.current_owner` owns the session
        read, so no copy of that rule lives here.

    Returns:
        The address, or an empty string when no session owner exists.
    """
    owner = identity.current_owner()  # The session guard already refused an unsigned request.
    return owner.actor_email if owner is not None else ""  # An empty address never reaches a log record.


def held_by_other(org_id: str, site_id: str) -> str | None:
    """Return the address of a lock holder that is not the current operator.

    Why:
        The documented journey asks one operator to take the site lock and then
        take the pre-check capture. A presence-only test refuses that operator
        their own capture, so the primary journey cannot finish. The holder
        therefore passes every check here, and a second operator still reads
        409 `site_locked`. `upgrade.held_by_other` keeps this same rule, so the
        two routes answer one question one way.

    The unreachable store:
        `read_site_locks` answers an empty index when the lock store is
        unreachable, so an unknown state reads as free and the capture starts.
        That choice is correct for a capture and stays.
        `contracts/site-lock.md:130` asks a read to continue when the store is
        unreachable. `contracts/site-lock.md:139` states that the lock does not
        gate a capture on its own, because a capture reads only and two captures
        do no harm. A capture that refused on an unreachable store would break
        both lines. The upgrade start makes the opposite choice, because it
        writes firmware to a device.

    Args:
        org_id: The organization that holds the site.
        site_id: The site the capture reads.

    Returns:
        The address of the other operator, or None when the capture may start.
    """
    holder = read_site_locks(org_id, [site_id]).get(site_id)  # None means free, and None also means unknown.
    if not holder or holder == actor_address():  # The operator that holds the lock may take their own capture.
        return None  # The caller starts the capture.
    logger.info("capture: the site %s is held by %s", site_id, identity.email_digest(holder))  # Digest only.
    return holder  # The caller answers 409 and names no address in the log.


# --------------------------------------------------------------------------
# The stored capture.
# --------------------------------------------------------------------------


def stored_section_state(name: str, tier: int, lost: set[str]) -> str:
    """Name the state of one section of a stored capture.

    Args:
        name: The section name.
        tier: The data tier of the stored capture.
        lost: The sections that the capture did not read.

    Returns:
        The section state.
    """
    if name in lost:  # The capture named this section in its partial reasons.
        return SECTION_FAILED  # The page then shows a red row.
    if tier < TIER_EXTRA and name in EXTRA_SECTIONS:  # Tier 2 reads neither extra section.
        return SECTION_SKIPPED  # A skipped row is no fault.
    return SECTION_DONE  # Every other section read to its end.


def lost_sections(document: dict[str, Any]) -> set[str]:
    """Name every section that one stored capture did not read.

    Args:
        document: The stored capture document.

    Returns:
        The section names inside the partial reasons.
    """
    reasons: Any = document.get("partial_reasons") or []  # A capture that lost nothing holds an empty list.
    return {str(entry.get("section", "")) for entry in reasons if isinstance(entry, dict)}  # A name may repeat.


def stored_progress(document: dict[str, Any], comparable: bool) -> dict[str, Any]:
    """Build the progress fields of one capture that already ended.

    Args:
        document: The stored capture document.
        comparable: True when the portal read the key back unchanged.

    Returns:
        The fields that a finished capture reports.
    """
    tier = int(document.get(TIER_FIELD, TIER_STANDARD))  # A document with no tier reads as tier 2.
    lost = lost_sections(document)  # Every section that this capture did not read.
    return {
        "state": str(document.get("capture_status", STATE_VERIFIED)),  # The store names the end state.
        "percent": WHOLE_PERCENT,  # A stored capture read all that it was going to read.
        "sections": {name: stored_section_state(name, tier, lost) for name in SECTION_NAMES},
        "counts": document.get("counts") or {},  # An older document may hold no counts.
        "partial_reasons": document.get("partial_reasons") or [],  # An empty list means nothing was lost.
        "verified": comparable,  # The read-back result of the store.
        "message": "",  # A capture that ended needs no progress message.
    }


def stored_page_fields(document: dict[str, Any], tier: int) -> dict[str, Any]:
    """Build the three fields that the capture page reads and the poll drops.

    Args:
        document: The stored capture document.
        tier: The data tier of the capture.

    Returns:
        The tier, the run, and the site of one stored capture.
    """
    return {
        TIER_FIELD: tier,  # The tier list of the page opens on this value.
        RUN_FIELD: str(document.get(RUN_FIELD, "")),  # The link back to the owning run.
        "site_id": str(document.get("site_id", "")),  # The site that this capture read.
    }


def stored_status(document: dict[str, Any], comparable: bool) -> dict[str, Any]:
    """Build the status body of one capture that the store already holds.

    Why:
        The progress store lives in the worker process only. After a restart the
        operator still opens the page of a finished capture, and the answer then
        comes from the store instead.

    Args:
        document: The stored capture document.
        comparable: True when the portal read the key back unchanged.

    Returns:
        The status body, and the three page fields that `status_body` drops.
    """
    tier = int(document.get(TIER_FIELD, TIER_STANDARD))  # A document with no tier reads as tier 2.
    record = blank_status(str(document.get("capture_id", "")), tier)  # The shape of a live record.
    record.update(stored_progress(document, comparable))  # The finished values replace the empty ones.
    record.update(stored_page_fields(document, tier))  # `status_body` drops these three again.
    return record  # One record answers the page and the poll.


def load_stored(capture_id: str) -> Any:
    """Read one stored capture through the seam.

    Args:
        capture_id: The identifier of the capture.

    Returns:
        The record that the store answers with, or None when no reader exists.
    """
    loader = capture_loader()  # None while the store module is still building.
    if loader is None:  # The portal cannot answer this read at all.
        logger.error("capture: the store module is not built, so the read cannot run")  # The cause of the 500.
        return None  # The caller turns this into a fault, never a 404.
    return loader(capture_id)  # The store answers with its own record shape.


def stored_body(capture_id: str) -> dict[str, Any] | None:
    """Read the status body of one stored capture.

    Args:
        capture_id: The identifier of the capture.

    Returns:
        The status body, or None when the store holds no such capture.
    """
    load = load_stored(capture_id)  # None when no reader exists.
    document: Any = getattr(load, "capture", None) if load is not None else None  # The stored fields.
    if not isinstance(document, dict):  # No such capture, or an unreachable store.
        return None  # The status route then answers the 404 of the contract.
    return stored_status(document, bool(getattr(load, "comparable", False)))  # A missing flag reads as false.


def refusal_for(load: Any) -> tuple[Response, int]:
    """Turn one refused store read into the error envelope.

    Why:
        `capture/store.py` names each refusal with the error code of this route,
        so the code passes straight on. A reason this module does not know is a
        fault of the portal, and a 404 there would send the operator to start the
        whole capture again for nothing.

    Args:
        load: The record that the store answered with, or None.

    Returns:
        The refusal envelope and its status.
    """
    reason = str(getattr(load, "reason", "")) if load is not None else ""  # A missing reader holds no reason.
    if reason not in REFUSAL_STATUS:  # An unreachable store, or a reason from a later version.
        logger.error("capture: the capture read failed for the reason %s", reason or "unknown")  # The cause.
        return json_error(SERVER_ERROR_STATUS)  # A fault of the portal, so the operator waits and retries.
    return json_error(REFUSAL_STATUS[reason], reason, REFUSAL_MESSAGE[reason])  # The store named the code.


# --------------------------------------------------------------------------
# The routes.
# --------------------------------------------------------------------------


def launch_capture(site: dict[str, Any], org_id: str, tier: int, body: dict[str, Any]) -> tuple[Response, int]:
    """Open the progress record, start the worker, and answer 202.

    Why:
        The refusals belong to the route and the work belongs here, so the route
        reads as the list of refusals that `contracts/http-api.md` names.

    Args:
        site: The site record of the site the capture reads.
        org_id: The organization that holds the site.
        tier: The data tier of the capture.
        body: The request body, which may name the run and the role.

    Returns:
        The capture identifier and the path the browser polls.
    """
    job = build_job(site, org_id, tier, body)  # The worker reads this job and nothing else.
    capture_id = str(job["capture_id"])  # The browser polls this identifier.
    site_id = str(job["site_id"])  # One named field, because the job as a whole holds the cloud session.
    open_progress(capture_id, opening_record(job))  # The record exists before the poll can ask for it.
    start_worker(job)  # The reading runs beside this request.
    logger.info("capture: started the capture %s of the site %s at tier %s", capture_id, site_id, tier)  # Audit.
    status_url = f"/api/captures/{capture_id}/status"  # The path that the browser polls every 30 seconds.
    return jsonify({"capture_id": capture_id, "status_url": status_url}), ACCEPTED_STATUS  # 202, work continues.


@capture_bp.post(START_PATH)
@identity.require_session
def start_capture(site_id: str) -> tuple[Response, int]:
    """Start one capture of one site, and answer before the reading ends.

    Why:
        FR-021 to FR-028 describe a read of a whole site. The portal answers 202
        and hands the work to a worker thread, so the browser never waits for a
        read that takes minutes. Every check below runs before the worker starts.

    Args:
        site_id: The site the path named.

    Returns:
        The capture identifier and its status path, or the refusal envelope.
    """
    org_id = resolve_org(None) or ""  # An empty value means the operator has picked no organization.
    site = permitted_site(site_id, org_id)  # None means no pick, or a site of another organization.
    if site is None:  # The route reads the record once here, because the worker cannot read it later.
        return json_error(NOT_FOUND_STATUS, SITE_NOT_FOUND_CODE, SITE_NOT_FOUND_MESSAGE)  # T058 fixes this.
    body = request_body()  # An empty body reads as tier 2, which the contract names as the default.
    tier = read_tier(body)  # None means the body named a tier the portal does not read.
    if tier is None:  # FR-021 refuses every tier other than 2 and 3.
        return json_error(BAD_REQUEST_STATUS, BAD_TIER_CODE, BAD_TIER_MESSAGE)  # T058 fixes this code too.
    if held_by_other(org_id, site_id):  # The operator that holds the lock still takes their own capture.
        return json_error(CONFLICT_STATUS, SITE_LOCKED_CODE, SITE_LOCKED_MESSAGE)  # The holder must end first.
    return launch_capture(site, org_id, tier, body)  # Every check passed, so the reading starts.


@capture_bp.get(STATUS_PATH)
@identity.require_session
def capture_status(capture_id: str) -> tuple[Response, int]:
    """Report the progress of one capture.

    Why:
        The browser polls this endpoint every 30 seconds. The body holds the
        seven fields that the capture page paints, and holds no internal field,
        so the server render and the poll never disagree.

    Args:
        capture_id: The capture the path named.

    Returns:
        The status body, or the refusal envelope.
    """
    record = read_progress(capture_id)  # None after a restart, and None for an identifier the portal never issued.
    if record is not None:  # The live path, while the worker of this process still runs.
        return jsonify(status_body(record)), OK_STATUS  # The seven fields of T059, and no other.
    body = stored_body(capture_id)  # The store answers for a capture that ended before the restart.
    if body is None:  # Neither store holds this identifier.
        return json_error(NOT_FOUND_STATUS, CAPTURE_NOT_FOUND_CODE, CAPTURE_NOT_FOUND_MESSAGE)  # T060 fixes this.
    return jsonify(status_body(body)), OK_STATUS  # The same filter, so both paths answer one shape.


@capture_bp.get(READ_PATH)
@identity.require_session
def read_capture(capture_id: str) -> tuple[Response, int]:
    """Hand over one whole capture document.

    Why:
        FR-029 to FR-032b bind the comparison and the download to this one read.
        A capture that the portal never read back answers 409, because a
        comparison of a document that may never have reached the store would
        report a change that never happened.

    Args:
        capture_id: The capture the path named.

    Returns:
        The capture document, or the refusal envelope.
    """
    load = load_stored(capture_id)  # None when the store module is missing.
    document: Any = getattr(load, "capture", None) if load is not None else None  # The whole stored document.
    if load is None or not getattr(load, "comparable", False) or not isinstance(document, dict):  # Three refusals.
        return refusal_for(load)  # The store names the code, so the route passes it straight on.
    return jsonify(document), OK_STATUS  # The whole document, because the comparison reads every field.


@capture_bp.get(PAGE_PATH)
@identity.require_session
def capture_page(capture_id: str) -> str:
    """Show the human view of one capture.

    Why:
        One page covers the whole life of one capture. It starts the capture, it
        shows the progress, and it shows the result. The page renders even for a
        capture the portal does not know, because the operator reaches this page
        from a link that the start route answered a moment earlier.

    Args:
        capture_id: The capture the path named.

    Returns:
        The rendered page.
    """
    return render_page(CAPTURE_TEMPLATE, **page_context(capture_id))  # One page for the whole life of a capture.


def page_status(capture_id: str) -> dict[str, Any]:
    """Return the status record that the capture page paints.

    Why:
        A page that starts a capture knows no capture yet. An empty record keeps
        `portal.js` quiet, because it polls only while the progress region names
        a capture.

    Args:
        capture_id: The capture the path named.

    Returns:
        The live record, the stored record, or an empty record.
    """
    known = read_progress(capture_id) or stored_body(capture_id)  # None before the first start.
    return known or blank_status("", TIER_STANDARD)  # An empty panel, and no identifier to poll.


def page_context(capture_id: str) -> dict[str, Any]:
    """Build the values that the capture page reads.

    Why:
        The page paints the fields that the poll paints, so the first render and
        the first poll never disagree.

        The page also includes the site lock banner. FR-072 gives one site to
        one operator, so the operator must read the lock state before the start
        control. `select.lock_banner_context` owns every rule of that banner.

    Args:
        capture_id: The capture the path named.

    Returns:
        The template context.
    """
    status = page_status(capture_id)  # An empty record before the first start.
    site_id = status.get("site_id") or request.args.get("site_id", "")  # A start page names its site in the query.
    context: dict[str, Any] = {
        "capture_id": status["capture_id"],  # An empty value stops the poll before it starts.
        "status": status_body(status),  # The same filter that the poll answers with.
        "tier": status.get(TIER_FIELD, TIER_STANDARD),  # The tier list opens on this value.
        "site_id": site_id,  # The start button posts to the site named here.
        "run_id": status.get(RUN_FIELD, ""),  # The link back to the owning run.
        "role": status.get(ROLE_FIELD, DEFAULT_ROLE),  # The half of the run that this capture covers.
        "poll_interval_seconds": POLL_SECONDS,  # Decision D3 of the plan fixes this period.
    }
    context.update(lock_banner_context(resolve_org(None) or "", site_id))  # The included banner reads these six.
    return context
