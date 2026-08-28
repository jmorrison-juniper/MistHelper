"""The comparison routes and the history routes of the upgrade capture portal.

Why:
    Section 6 of ``contracts/http-api.md`` gives the operator three ways to
    read one comparison. A machine reads ``GET /api/comparisons``. A person
    reads ``GET /compare``. A record keeper downloads
    ``GET /api/comparisons/export``. All three must report the same numbers,
    so each route builds the comparison with the same three calls into the
    compare package and counts nothing on its own. The same section holds the
    history, because a comparison and a history read the same stored captures.

Route names:
    ``review.compare_captures`` answers ``GET /api/comparisons``.
    ``review.download_comparison`` answers ``GET /api/comparisons/export``.
    ``review.compare_page`` answers ``GET /compare``.
    ``review.capture_history`` answers ``GET /api/sites/<site_id>/history``.
    ``review.run_history`` answers ``GET /api/sites/<site_id>/runs/history``.
    ``review.history_page`` answers ``GET /history``.

A free read:
    FR-032, FR-081, and FR-082 let any person read the history. No history
    route asks for a typed word, and no history route reads the site lock. A
    read that waited for a lock would hide the record from the operator who
    most needs it, which is the operator watching somebody else's upgrade.

One filter bar, two tables:
    Rule 6 of ``contracts/ui-testids.md`` allows one value of a test
    identifier for each page, and ``added`` belongs to the device outcomes and
    to the client outcomes. Two filter bars would print
    ``compare-filter-added`` twice, so the page carries one bar that holds the
    union of the two outcome sets. The route hands the chosen outcome to the
    table that owns it and hands ``all`` to the other table. The rows match
    ``build_view``, and the log stays quiet for an outcome that only one table
    knows.

Seams:
    The capture read and the capture list arrive through the application
    config, so a contract test needs no database. The module falls back to
    ``capture.store`` when the config holds nothing. That fallback loads late,
    because ``capture.store`` imports the database driver at module level and
    the portal must start without it.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib import import_module
from inspect import signature
from types import ModuleType
from typing import Any
from urllib.parse import urlencode

from flask import Blueprint, Response, current_app, jsonify, render_template, request
from jinja2 import TemplateNotFound

from ...compare import clients as client_compare
from ...compare import diff as device_compare
from ...compare import download as compare_download
from ...compare import render as compare_render
from ...compare import statistics as compare_statistics
from ...runtime import identity
from ..factory import json_error

logger = logging.getLogger(__name__)

review_bp = Blueprint("review", __name__)  # No URL prefix, because the paths span `/compare` and `/api`.


# ---------------------------------------------------------------------------
# The contract values
# ---------------------------------------------------------------------------

COMPARISONS_API_PATH = "/api/comparisons"
COMPARISONS_EXPORT_API_PATH = "/api/comparisons/export"
COMPARE_PAGE_PATH = "/compare"

# Section 6 of `contracts/http-api.md` names the capture history endpoint and the
# history page. The contract names no run history path at all, so
# `tasks.md` T205 supplies the need and this module supplies the spelling. The
# path sits below the site and below `runs`, because `POST
# /api/sites/<site_id>/runs` already means "create a run" in section 5, and one
# path with two meanings would read as a trap.
HISTORY_API_PATH = "/api/sites/<site_id>/history"
RUN_HISTORY_API_PATH = "/api/sites/<site_id>/runs/history"
HISTORY_PAGE_PATH = "/history"

BEFORE_FIELD = "before"
AFTER_FIELD = "after"
FORMAT_FIELD = "format"
SCOPE_FIELD = "scope"
OUTCOME_FIELD = "outcome"
SITE_ID_FIELD = "site_id"
SITE_NAME_FIELD = "site_name"
CAPTURE_ID_FIELD = "capture_id"
STARTED_AT_FIELD = "started_at"
CAPTURES_FIELD = "captures"
RUNS_FIELD = "runs"
TOTAL_FIELD = "total"
LIMIT_FIELD = "limit"
OFFSET_FIELD = "offset"
SCHEMA_VERSION_FIELD = "schema_version"
UNKNOWN_VERSION = "unknown"

# The count names of `data-model.md` line 179, as `capture/assembly.py` writes
# them into the `counts` map of every capture document.
COUNTS_FIELD = "counts"
DEVICE_COUNT_FIELD = "device_count"
CLIENT_COUNT_FIELD = "client_count"
DEVICE_TOTAL_KEY = "devices_total"
CLIENT_COUNT_KEYS = ("clients_wired", "clients_wireless", "clients_guest")

# Section 6 of `contracts/http-api.md` sets the two page defaults. The two bounds
# are the portal's own, because the contract sets none and an unbounded limit
# lets one request read the whole unlimited retention of FR-032 in one answer.
DEFAULT_HISTORY_LIMIT = 25
SMALLEST_HISTORY_LIMIT = 1
LARGEST_HISTORY_LIMIT = 200
DEFAULT_HISTORY_OFFSET = 0
LARGEST_HISTORY_OFFSET = 1_000_000

# Section 6 of `contracts/http-api.md` names the six fields of one history
# row. A row that drops one of them still answers with the name, because a
# reader that meets a missing name reports a fault instead of an empty cell.
# The size is there for FR-032b, which watches the growth of an unlimited store.
#
# The two counts are not in that list. A history of an upgrade that cannot say
# how many devices and how many clients the site held is of little use, so the
# row carries both. Each one comes off the stored `counts` map, and neither one
# costs a second read.
HISTORY_ROW_DEFAULTS: dict[str, Any] = {
    "capture_id": "",
    "role": "",
    "started_at": "",
    "capture_status": "",
    "actor_email": "",
    "stored_size_bytes": 0,
    DEVICE_COUNT_FIELD: 0,
    CLIENT_COUNT_FIELD: 0,
}

COMPARE_TEMPLATE = "review/compare.html"
COMPARE_SELECT_TEMPLATE = "review/compare_select.html"
HISTORY_TEMPLATE = "review/history.html"
FALLBACK_TEMPLATE = "layout.html"

# The short moment of one history row. The store writes
# `datetime.now(tz=UTC).isoformat()`, which holds 32 characters and wraps across
# four lines in the narrow moment column of issue #2106. The short form holds 20
# characters and fits one line. The page keeps the stored value in a `title`
# attribute, so the operator still reads the second and the microsecond.
MOMENT_TEXTS_FIELD = "moment_texts"
MOMENT_TEXT_FORMAT = "%Y-%m-%d %H:%M UTC"

COMPARE_PAGE_TITLE = "Capture comparison"
PICKER_PAGE_TITLE = "Choose two captures"
HISTORY_PAGE_TITLE = "Capture history"

OK_STATUS = 200
BAD_REQUEST_STATUS = 400
NOT_FOUND_STATUS = 404
CONFLICT_STATUS = 409
SERVER_ERROR_STATUS = 500

# The refusal codes of section 6 of `contracts/http-api.md`.
# Each message sits beside its code, because `factory.ERROR_MESSAGES` holds the
# site lock sentence for 409 and that sentence names the wrong fault here.
CAPTURE_NOT_FOUND = "capture_not_found"
CAPTURE_NOT_FOUND_MESSAGE = "The portal holds no capture with that identifier."
CAPTURE_NOT_VERIFIED = "capture_not_verified"
CAPTURE_NOT_VERIFIED_MESSAGE = "A comparison reads a verified capture only."
SCHEMA_TOO_NEW = "schema_version_too_new"
SCHEMA_TOO_NEW_MESSAGE = (
    "This record comes from a later version of the portal. This portal is too old to show it. Upgrade the portal."
)
CAPTURE_SITE_MISMATCH = "capture_site_mismatch"
CAPTURE_SITE_MISMATCH_MESSAGE = "The two captures name different sites."
COMPARISON_UNAVAILABLE = "comparison_unavailable"
COMPARISON_UNAVAILABLE_MESSAGE = "The portal cannot read a capture right now."
BAD_FORMAT_MESSAGE = "Ask for the csv format or the json format."
BAD_SCOPE_MESSAGE = "Ask for the differences scope or the full scope."
# WHY: The download module names the fault. One map turns that name into the
# words that the operator reads, so the route holds no branch of its own.
_EXPORT_MESSAGES: dict[str, str] = {
    compare_download.ERROR_BAD_FORMAT: BAD_FORMAT_MESSAGE,
    compare_download.ERROR_BAD_SCOPE: BAD_SCOPE_MESSAGE,
}
_REFUSALS: dict[str, tuple[int, str, str]] = {
    CAPTURE_NOT_FOUND: (NOT_FOUND_STATUS, CAPTURE_NOT_FOUND, CAPTURE_NOT_FOUND_MESSAGE),
    CAPTURE_NOT_VERIFIED: (CONFLICT_STATUS, CAPTURE_NOT_VERIFIED, CAPTURE_NOT_VERIFIED_MESSAGE),
    # Section 6 of `contracts/http-api.md` fixes the status and the code. The store
    # gate at `capture/store.py` runs before the state gate, so this reason can
    # reach the route in place of `capture_not_verified`. Without this row the
    # reason falls to the 500 default, and a record that one portal upgrade
    # would open reads as a server fault. The code is explicit here, because
    # `factory.ERROR_CODES[409]` gives the bare word `conflict` and that word
    # cannot tell a locked site from a record of a later release.
    SCHEMA_TOO_NEW: (CONFLICT_STATUS, SCHEMA_TOO_NEW, SCHEMA_TOO_NEW_MESSAGE),
}

# WHY: The store also reports `database_unreachable`, and section 6 names no
# status for it. A read that the portal cannot perform is a portal fault, so it
# answers 500 rather than blaming the request.
_DEFAULT_REFUSAL = (SERVER_ERROR_STATUS, COMPARISON_UNAVAILABLE, COMPARISON_UNAVAILABLE_MESSAGE)


# ---------------------------------------------------------------------------
# The seams
# ---------------------------------------------------------------------------

CAPTURE_LOADER_KEY = "CAPTURE_LOADER"
CAPTURE_LISTER_KEY = "CAPTURE_LISTER"
RUN_LISTER_KEY = "RUN_LISTER"

PACKAGE_ROOT = __name__.rsplit(".", maxsplit=3)[0]
STORE_MODULE = "capture.store"
LOADER_ATTRIBUTES = ("load_capture_for_comparison",)
LISTER_ATTRIBUTES = ("list_captures",)
QUERY_ATTRIBUTES = ("CaptureQuery",)

# The run list of the capture store. `list_runs` answers a `RunListPage`, which
# carries `runs` and `total` under the same two names as `CaptureListPage`, so
# one page reader serves both histories.
RUN_LISTER_ATTRIBUTES = ("list_runs",)
RUN_QUERY_ATTRIBUTES = ("RunQuery",)

# The history view of the compare package. The name is read at call time rather
# than imported at module level. A portal whose render module has not grown the
# builder yet therefore answers the history page instead of failing to start.
HISTORY_VIEW_ATTRIBUTE = "build_history_view"
ROWS_KEY = "rows"
WINDOW_KEY = "window"


def load_optional_module(suffix: str) -> ModuleType | None:
    """Import one module of this package, or report that it is absent.

    Why:
        The capture store imports the database driver at module level. A
        top-level import here would stop the whole portal on a host that holds
        no driver, so the import waits until a request needs the store.

    Args:
        suffix: The module path below the package root.

    Returns:
        The module, or None when the import fails.
    """
    try:  # The module is absent on a host with no database driver.
        return import_module(f"{PACKAGE_ROOT}.{suffix}")
    except ImportError:  # Expected on a lean host, so this is not a fault.
        logger.info("review: the module %s is not available", suffix)
        return None


def find_attribute(module: ModuleType | None, names: tuple[str, ...]) -> Callable[..., Any] | None:
    """Return the first callable of one module that carries one of these names.

    Why:
        A seam names more than one candidate, so a rename in the store does not
        break the route on the same day.

    Args:
        module: The module to read, or None.
        names: The candidate names, in order of preference.

    Returns:
        The first callable found, or None.
    """
    if module is None:
        return None
    for name in names:  # The first match wins.
        candidate: Any = getattr(module, name, None)
        if callable(candidate):
            found: Callable[..., Any] = candidate
            return found
    return None


def injected_seam(config_key: str) -> Callable[..., Any] | None:
    """Return the callable that the application config holds under one key.

    Why:
        A contract test injects a stand-in through the config, so the test
        needs no database, no network, and no lock server.

    Args:
        config_key: The config key of the seam.

    Returns:
        The injected callable, or None when the config holds no callable.
    """
    candidate: Any = current_app.config.get(config_key)
    return candidate if callable(candidate) else None


def store_capture_rows(site_id: str, limit: int = DEFAULT_HISTORY_LIMIT, offset: int = DEFAULT_HISTORY_OFFSET) -> Any:
    """Read one page of capture rows from the capture store.

    Why:
        The store takes one query record rather than loose values, so the
        fallback builds that record here and keeps the store shape out of the
        page code. The two window values carry a default, so the picker still
        calls this reader with the site alone.

    Args:
        site_id: The site to narrow to. An empty value reads every site.
        limit: The largest number of rows to read.
        offset: The number of rows to step over first.

    Returns:
        The store page, or an empty tuple when the store is absent.
    """
    module = load_optional_module(STORE_MODULE)
    lister = find_attribute(module, LISTER_ATTRIBUTES)
    query_class = find_attribute(module, QUERY_ATTRIBUTES)
    if lister is None or query_class is None:
        return ()
    return lister(query_class(site_id=site_id, limit=limit, offset=offset))


def store_run_rows(site_id: str, limit: int = DEFAULT_HISTORY_LIMIT, offset: int = DEFAULT_HISTORY_OFFSET) -> Any:
    """Read one page of run rows from the capture store.

    Why:
        The run history walks the same site index as the capture history, so
        the fallback mirrors ``store_capture_rows`` exactly. The store owns the
        query, and this route owns no count and no sort order of its own.

    Args:
        site_id: The site to narrow to. An empty value reads every site.
        limit: The largest number of rows to read.
        offset: The number of rows to step over first.

    Returns:
        The store page, or an empty tuple when the run list is absent.
    """
    module = load_optional_module(STORE_MODULE)
    lister = find_attribute(module, RUN_LISTER_ATTRIBUTES)
    query_class = find_attribute(module, RUN_QUERY_ATTRIBUTES)
    if lister is None or query_class is None:  # The store has not grown the run list yet.
        logger.info("review: the capture store offers no run list, so the run history is empty")
        return ()
    return lister(query_class(site_id=site_id, limit=limit, offset=offset))


def capture_loader() -> Callable[..., Any] | None:
    """Return the reader that loads one capture for a comparison.

    Why:
        The injected seam wins over the store, so a test never reaches a
        database and a running portal still reads real records.

    Returns:
        The reader, or None when no reader is available.
    """
    injected = injected_seam(CAPTURE_LOADER_KEY)
    if injected is not None:
        return injected
    return find_attribute(load_optional_module(STORE_MODULE), LOADER_ATTRIBUTES)


def capture_lister() -> Callable[..., Any]:
    """Return the reader that fills the two capture pickers and the history.

    Why:
        The picker always renders, even with no rows, so this seam falls back
        to the store rather than to None and the page needs no extra branch.

    Returns:
        The reader.
    """
    injected = injected_seam(CAPTURE_LISTER_KEY)
    return injected if injected is not None else store_capture_rows


def run_lister() -> Callable[..., Any]:
    """Return the reader that fills the run history.

    Why:
        The run history renders with no rows in the same way as the capture
        history, so this seam falls back to the store rather than to None.

    Returns:
        The reader.
    """
    injected = injected_seam(RUN_LISTER_KEY)
    return injected if injected is not None else store_run_rows


# ---------------------------------------------------------------------------
# The capture pair
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CapturePair:
    """Two captures that may join a comparison, or the refusal that stopped them.

    Why:
        All three routes read the same two captures and refuse for the same
        three reasons. One record carries the success and the refusal together,
        so each route holds one branch and the refusal rules live in one place.

    Attributes:
        before: The pre-check capture, or None on a refusal.
        after: The post-check capture, or None on a refusal.
        status: The HTTP status of the refusal.
        code: The error code of the refusal.
        message: The sentence that names the refusal.
    """

    before: Mapping[str, Any] | None = None
    after: Mapping[str, Any] | None = None
    status: int = OK_STATUS
    code: str = ""
    message: str = ""

    def both(self) -> tuple[Mapping[str, Any], Mapping[str, Any]] | None:
        """Return the two captures together, or None when the read failed.

        Why:
            A caller that reads the two fields one at a time repeats the same
            test twice. One call answers once and keeps the type plain.

        Returns:
            The pre-check capture and the post-check capture, or None.
        """
        if self.before is None or self.after is None:
            return None
        return self.before, self.after


def text_field(record: Mapping[str, Any], name: str) -> str:
    """Return one text field of one stored record.

    Why:
        A partial capture drops a field, and the routes must still answer. A
        reader that returns an empty string keeps the type tests out of the
        route bodies.

    Args:
        record: One stored record.
        name: The field name.

    Returns:
        The field value as text, or an empty string.
    """
    value = record.get(name)
    return value if isinstance(value, str) else ""


def read_capture(loader: Callable[..., Any], capture_id: str) -> tuple[Mapping[str, Any] | None, str]:
    """Read one capture that may join a comparison.

    Why:
        The store answers with a record that carries the document and the
        verdict. A test stand-in answers with the document alone. Reading both
        shapes here keeps a stand-in small and keeps the route unchanged.

    Args:
        loader: The capture reader.
        capture_id: The business key of the capture.

    Returns:
        The capture and an empty reason, or the refused record and the reason.
        A record travels beside a refusal whenever the store held one, so a
        caller can report the schema version that it met.
    """
    answer: Any = loader(capture_id)
    if isinstance(answer, Mapping):  # A stand-in hands back the document itself.
        return answer, ""
    document: Any = getattr(answer, "capture", None)
    record = document if isinstance(document, Mapping) else None
    if record is not None and bool(getattr(answer, "comparable", True)):
        return record, ""
    reason: Any = getattr(answer, "reason", "")
    return record, reason if isinstance(reason, str) and reason else CAPTURE_NOT_FOUND


def refuse(reason: str, capture_id: str, record: Mapping[str, Any] | None = None) -> CapturePair:
    """Return the refusal that one store reason asks for.

    Why:
        The store names the fault and the route names the status. Mapping the
        two in one table stops a route from inventing a status of its own.

        The store hands back the refused record for a record of a later
        release, so the log names the schema version that this release met.
        Without that number an operator cannot tell which release wrote the
        record and cannot judge how far behind this portal sits.

    Args:
        reason: The store reason.
        capture_id: The capture that the portal refused.
        record: The refused record, when the store held one.

    Returns:
        The refusal record.
    """
    status, code, message = _REFUSALS.get(reason, _DEFAULT_REFUSAL)
    found = record.get(SCHEMA_VERSION_FIELD, UNKNOWN_VERSION) if record else UNKNOWN_VERSION
    logger.info("review: the portal refused capture %s with %s at schema version %s", capture_id, code, found)
    return CapturePair(status=status, code=code, message=message)


def same_site(before: Mapping[str, Any], after: Mapping[str, Any]) -> bool:
    """Return whether the two captures name the same site.

    Why:
        A comparison across two sites reports every device as added and every
        device as removed, which reads as a total outage. An absent name proves
        no disagreement, so a partial capture never triggers the refusal.

    Args:
        before: The pre-check capture.
        after: The post-check capture.

    Returns:
        True when the two names agree, or when either name is absent.
    """
    left = text_field(before, SITE_ID_FIELD)
    right = text_field(after, SITE_ID_FIELD)
    if not left or not right:
        return True
    return left == right


def read_pair(before_id: str, after_id: str) -> CapturePair:
    """Read the two captures of one comparison.

    Why:
        The verification test runs before the site test, because the store
        hands out no document at all for an unverified capture and the route
        therefore cannot read that capture's site.

    Args:
        before_id: The business key of the pre-check capture.
        after_id: The business key of the post-check capture.

    Returns:
        The two captures, or the refusal.
    """
    loader = capture_loader()
    if loader is None:
        logger.warning("review: the portal found no capture reader")
        return CapturePair(
            status=SERVER_ERROR_STATUS, code=COMPARISON_UNAVAILABLE, message=COMPARISON_UNAVAILABLE_MESSAGE
        )
    before, before_reason = read_capture(loader, before_id)
    if before_reason or before is None:
        return refuse(before_reason or CAPTURE_NOT_FOUND, before_id, before)
    after, after_reason = read_capture(loader, after_id)
    if after_reason or after is None:
        return refuse(after_reason or CAPTURE_NOT_FOUND, after_id, after)
    if not same_site(before, after):
        logger.warning("review: the two captures name different sites")
        return CapturePair(status=BAD_REQUEST_STATUS, code=CAPTURE_SITE_MISMATCH, message=CAPTURE_SITE_MISMATCH_MESSAGE)
    return CapturePair(before=before, after=after)


# ---------------------------------------------------------------------------
# The comparison itself
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ComparisonParts:
    """The two captures and the three results that every route needs.

    Why:
        The endpoint, the page, and the download show the same comparison. One
        record carries the whole result, so no route repeats a count and the
        three answers can never disagree.

    Attributes:
        before: The pre-check capture.
        after: The post-check capture.
        devices: The device half of the comparison.
        clients: The client half of the comparison.
        statistics: The statistics roll-up.
    """

    before: Mapping[str, Any]
    after: Mapping[str, Any]
    devices: device_compare.DeviceComparison
    clients: client_compare.ClientComparison
    statistics: compare_statistics.ComparisonStatistics

    @property
    def skipped_sections(self) -> tuple[str, ...]:
        """Return every section that a digest match skipped.

        Why:
            The header names each skip once, and the two halves each hold their
            own list. Joining them here keeps the join out of the page code.

        Returns:
            The device skips followed by the client skips.
        """
        return (*self.devices.skipped_sections, *self.clients.skipped_sections)


def build_parts(before: Mapping[str, Any], after: Mapping[str, Any]) -> ComparisonParts:
    """Compare two captures and roll up the statistics.

    Why:
        This is the one place that calls the compare package. A second caller
        would let two routes report two different numbers for one comparison.

    Args:
        before: The pre-check capture.
        after: The post-check capture.

    Returns:
        The whole comparison result.
    """
    devices = device_compare.compare_devices(before, after)
    clients = client_compare.compare_clients(before, after)
    elapsed = compare_statistics.elapsed_seconds_between(before, after)
    statistics = compare_statistics.build_statistics(devices, clients, elapsed)
    return ComparisonParts(before, after, devices, clients, statistics)


# ---------------------------------------------------------------------------
# The single filter bar
# ---------------------------------------------------------------------------

# WHY: The bar holds the union of the two outcome sets. `added` belongs to both
# sets, and rule 6 of the identifier contract allows one `compare-filter-added`
# for each page, so the union keeps it once.
FILTER_CHOICES: tuple[str, ...] = (
    compare_render.FILTER_ALL,
    *device_compare.DEVICE_OUTCOMES,
    *(name for name in client_compare.CLIENT_OUTCOMES if name not in device_compare.DEVICE_OUTCOMES),
)

_FILTER_LABELS = {
    compare_render.FILTER_ALL: "All rows",
    device_compare.OUTCOME_UNCHANGED: "Unchanged",
    device_compare.OUTCOME_CHANGED: "Changed",
    device_compare.OUTCOME_ADDED: "Added",
    device_compare.OUTCOME_REMOVED: "Removed",
    client_compare.OUTCOME_PRESENT: "Present",
    client_compare.OUTCOME_MOVED: "Moved",
    client_compare.OUTCOME_MISSING: "Missing",
}


@dataclass(frozen=True, slots=True)
class FilterChoice:
    """One control of the single filter bar.

    Why:
        A template must build no name and no address, because a template that
        builds a name drifts from the browser test. The record carries the
        words, the test identifier, and the link, ready to print.

    Attributes:
        outcome: The outcome name, or ``all``.
        label: The words that the page shows.
        test_id: The test identifier of this control.
        href: The address that applies this filter.
        active: True when this filter is in force.
    """

    outcome: str
    label: str
    test_id: str
    href: str
    active: bool


def build_link(path: str, values: Mapping[str, str]) -> str:
    """Return one portal address with its query values.

    Why:
        A capture identifier and a filter name travel in the address bar, so
        the builder escapes them rather than joining raw text.

    Args:
        path: The portal path.
        values: The query values.

    Returns:
        The address.
    """
    return path + "?" + urlencode(dict(values))


def table_filter(chosen: str, allowed: tuple[str, ...]) -> str:
    """Return the filter value that one table can use.

    Why:
        ``missing`` is a client outcome and never a device outcome. Handing it
        to the device table would make the table fall back to ``all`` and log a
        warning about a value that the page offered on purpose.

    Args:
        chosen: The filter in force.
        allowed: The filter values of this table.

    Returns:
        The chosen value, or ``all`` when this table does not know it.
    """
    return chosen if chosen in allowed else compare_render.FILTER_ALL


def build_filter_choices(chosen: str, ids: Mapping[str, str]) -> tuple[FilterChoice, ...]:
    """Return one control for each outcome of the filter bar.

    Why:
        The bar prints in a fixed order, so the same control sits in the same
        place on every comparison page.

    Args:
        chosen: The filter in force.
        ids: The two capture identifiers, under their query names.

    Returns:
        One record for each filter control.
    """
    return tuple(
        FilterChoice(
            outcome=name,
            label=_FILTER_LABELS.get(name, name),
            test_id=compare_render.filter_test_id(name),
            href=build_link(COMPARE_PAGE_PATH, {**ids, OUTCOME_FIELD: name}),
            active=name == chosen,
        )
        for name in FILTER_CHOICES
    )


# ---------------------------------------------------------------------------
# The pages
# ---------------------------------------------------------------------------


def render_page(name: str, **context: Any) -> str:
    """Render one template, and fall back to the shell page when it is absent.

    Why:
        The portal grows one template at a time. A missing template shows the
        shell page and a log line rather than a server error.

    Args:
        name: The template name.
        context: The values that the template shows.

    Returns:
        The rendered page.
    """
    try:
        return render_template(name, **context)
    except TemplateNotFound:
        logger.warning("review: the template %s is absent, so the portal showed the shell page", name)
        return render_template(FALLBACK_TEMPLATE, **context)


def plain_rows(value: Any) -> list[dict[str, Any]]:
    """Return one plain dictionary for each usable row of one store answer.

    Why:
        A store page, a plain list, and an empty tuple all reach this reader,
        and a page must render for all three. Turning every shape into one
        list here keeps the type tests out of the page code.

    Args:
        value: The rows that a store page or a stand-in gave back.

    Returns:
        One plain dictionary for each usable row.
    """
    if not isinstance(value, Iterable) or isinstance(value, str | Mapping):
        return []
    return [dict(row) for row in value if isinstance(row, Mapping)]


def read_capture_rows(site_id: str) -> list[dict[str, Any]]:
    """Return the capture rows that the two pickers offer.

    Why:
        The picker must render even when the store answers with nothing, so
        this reader turns every shape into a plain list and never raises.

    Args:
        site_id: The site to narrow to. An empty value reads every site.

    Returns:
        One plain dictionary for each usable row.
    """
    page: Any = capture_lister()(site_id)
    return plain_rows(getattr(page, CAPTURES_FIELD, page))


def render_picker(before_id: str, after_id: str, notice: str = "") -> str:
    """Render the page that asks for the two captures.

    Why:
        An operator reaches ``/compare`` from the navigation with no query
        values. The picker asks for the two captures rather than showing an
        error for a request that named nothing.

    Args:
        before_id: The pre-check identifier that the request carried.
        after_id: The post-check identifier that the request carried.
        notice: The sentence that names a refusal, or an empty string.

    Returns:
        The rendered page.
    """
    return render_page(
        COMPARE_SELECT_TEMPLATE,
        page_title=PICKER_PAGE_TITLE,
        signed_in=True,
        captures=read_capture_rows(request.args.get(SITE_ID_FIELD, "")),
        before_id=before_id,
        after_id=after_id,
        notice=notice,
        action_path=COMPARE_PAGE_PATH,
    )


def build_download_links(ids: Mapping[str, str]) -> dict[str, str]:
    """Return the four download addresses of one comparison.

    Why:
        The page offers the differences file and the full file, each in two
        formats. The two older addresses name no scope, so a link that an
        operator saved before the full scope arrived still works.

    Args:
        ids: The two capture identifiers, under ``before`` and ``after``.

    Returns:
        The four addresses, under the names that the template prints.
    """
    path = COMPARISONS_EXPORT_API_PATH
    full = {SCOPE_FIELD: compare_download.SCOPE_FULL}
    return {
        "csv_href": build_link(path, {**ids, FORMAT_FIELD: compare_download.FORMAT_CSV}),
        "json_href": build_link(path, {**ids, FORMAT_FIELD: compare_download.FORMAT_JSON}),
        "full_csv_href": build_link(path, {**ids, FORMAT_FIELD: compare_download.FORMAT_CSV, **full}),
        "full_json_href": build_link(path, {**ids, FORMAT_FIELD: compare_download.FORMAT_JSON, **full}),
    }


def build_export_context(parts: ComparisonParts) -> compare_download.ExportContext:
    """Return the reading that the full download needs.

    Why:
        The full file names the site, the organization, the two moments, and
        every statistic. The route already holds all of that, so it hands the
        whole reading over and the download counts nothing again.

    Args:
        parts: The whole comparison result.

    Returns:
        The two captures and the flat statistics.
    """
    return compare_download.ExportContext(
        before=parts.before,
        after=parts.after,
        statistics=parts.statistics.to_dict(),
    )


def build_page_context(parts: ComparisonParts, chosen: str) -> dict[str, Any]:
    """Return every value that the comparison page shows.

    Why:
        The page holds no rule of its own, so the route builds each section
        here and the template prints what this function decided.

    Args:
        parts: The whole comparison result.
        chosen: The filter in force.

    Returns:
        The template context.
    """
    ids = {
        BEFORE_FIELD: text_field(parts.before, CAPTURE_ID_FIELD),
        AFTER_FIELD: text_field(parts.after, CAPTURE_ID_FIELD),
    }
    device_outcome = table_filter(chosen, compare_render.DEVICE_FILTERS)
    client_outcome = table_filter(chosen, compare_render.CLIENT_FILTERS)
    return {
        "page_title": COMPARE_PAGE_TITLE,
        "signed_in": True,
        "header": compare_render.build_header(parts.before, parts.after, parts.skipped_sections),
        "devices": compare_render.build_device_section(parts.devices, device_outcome),
        "clients": compare_render.build_client_section(parts.clients, client_outcome),
        "statistics": compare_render.build_statistics_section(parts.statistics),
        "filters": build_filter_choices(chosen, ids),
        **build_download_links(ids),
    }


def render_comparison(parts: ComparisonParts) -> str:
    """Render the comparison of two captures.

    Why:
        The filter arrives in the address bar, so the route normalizes it once
        and hands the same value to the bar and to both tables.

    Args:
        parts: The whole comparison result.

    Returns:
        The rendered page.
    """
    chosen = compare_render.normalize_filter(request.args.get(OUTCOME_FIELD, ""), FILTER_CHOICES)
    return render_page(COMPARE_TEMPLATE, **build_page_context(parts, chosen))


def build_attachment(result: compare_download.ExportResult) -> tuple[Response, int]:
    """Return one download as a file attachment.

    Why:
        The browser must save the file rather than show it, so the answer
        carries the disposition header and the file name that the export chose.

    Args:
        result: The export result.

    Returns:
        The file answer and its status.
    """
    response = Response(result.body, mimetype=result.media_type)
    response.headers["Content-Disposition"] = 'attachment; filename="' + result.filename + '"'
    logger.info("review: the portal sent a comparison download named %s", result.filename)
    return response, OK_STATUS


# ---------------------------------------------------------------------------
# The history page window
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PageWindow:
    """The page of history rows that one request asked for, and its neighbors.

    Why:
        Retention is unlimited under FR-032, so one site can hold thousands of
        capture rows. The window carries the two neighbor addresses ready to
        print, because a template that builds an address of its own drifts
        away from the browser test that clicks it.

    Attributes:
        limit: The largest number of rows on this page.
        offset: The number of rows before this page.
        total: The number of rows that the whole history holds.
        previous_href: The earlier page, or an empty string when none exists.
        next_href: The later page, or an empty string when none exists.
    """

    limit: int = DEFAULT_HISTORY_LIMIT
    offset: int = DEFAULT_HISTORY_OFFSET
    total: int = 0
    previous_href: str = ""
    next_href: str = ""


def bounded_int(raw: str, fallback: int, smallest: int, largest: int) -> int:
    """Return one query value as a whole number inside its two bounds.

    Why:
        A query value arrives as text that any person can edit in the address
        bar. Text that is not a number, or a number outside the bounds, must
        give the documented default rather than a server error.

    Args:
        raw: The text that the request carried.
        fallback: The value to use when the text is not a whole number.
        smallest: The smallest value the portal accepts.
        largest: The largest value the portal accepts.

    Returns:
        The value, held inside the two bounds.
    """
    try:
        value = int(raw)
    except (TypeError, ValueError):  # Any person can type a word into the address bar.
        return fallback
    return min(max(value, smallest), largest)


def read_window_values() -> tuple[int, int]:
    """Return the page size and the page start that the request asked for.

    Why:
        Section 6 of ``contracts/http-api.md`` sets the two defaults, and all
        three history routes must read them the same way. One reader keeps the
        two endpoints and the page on one page size.

    Returns:
        The page size and the page start.
    """
    limit = bounded_int(
        request.args.get(LIMIT_FIELD, ""), DEFAULT_HISTORY_LIMIT, SMALLEST_HISTORY_LIMIT, LARGEST_HISTORY_LIMIT
    )
    offset = bounded_int(
        request.args.get(OFFSET_FIELD, ""), DEFAULT_HISTORY_OFFSET, DEFAULT_HISTORY_OFFSET, LARGEST_HISTORY_OFFSET
    )
    return limit, offset


def page_href(site_id: str, limit: int, offset: int) -> str:
    """Return the address of one history page.

    Why:
        The site travels in the address bar beside the two window values, so
        the next page and the earlier page stay on the same site. The builder
        escapes each value rather than joining raw text.

    Args:
        site_id: The site to narrow to. An empty value reads every site.
        limit: The page size to carry onward.
        offset: The page start of the wanted page.

    Returns:
        The address of that page.
    """
    values = {LIMIT_FIELD: str(limit), OFFSET_FIELD: str(offset)}
    if site_id:  # An organization wide history carries no site.
        values[SITE_ID_FIELD] = site_id
    return build_link(HISTORY_PAGE_PATH, values)


def build_window(site_id: str, limit: int, offset: int, total: int) -> PageWindow:
    """Return the page window with its two neighbor addresses.

    Why:
        Task T206 asks for the next page and the earlier page. An empty
        address states plainly that the page does not exist, so the template
        hides that one control and never offers a dead link.

    Args:
        site_id: The site to narrow to. An empty value reads every site.
        limit: The page size in force.
        offset: The page start in force.
        total: The number of rows that the whole history holds.

    Returns:
        The window record.
    """
    earlier = page_href(site_id, limit, max(offset - limit, DEFAULT_HISTORY_OFFSET)) if offset > 0 else ""
    later = page_href(site_id, limit, offset + limit) if offset + limit < total else ""
    return PageWindow(limit=limit, offset=offset, total=total, previous_href=earlier, next_href=later)


# ---------------------------------------------------------------------------
# The history rows
# ---------------------------------------------------------------------------


def call_lister(lister: Callable[..., Any], site_id: str, limit: int, offset: int) -> Any:
    """Call one list seam with the page window when the seam accepts it.

    Why:
        The store fallback pages inside the database, and it declares both
        window names. A contract stand-in often takes the site alone, and two
        extra keywords would raise ``TypeError`` there. The probe reads the
        seam once and passes only what the seam declares.

    Args:
        lister: The list seam.
        site_id: The site to narrow to. An empty value reads every site.
        limit: The page size in force.
        offset: The page start in force.

    Returns:
        The store page, or whatever shape the stand-in gave back.
    """
    try:
        parameters = signature(lister).parameters
    except (TypeError, ValueError):  # A builtin or a stand-in that declares nothing.
        return lister(site_id)
    if LIMIT_FIELD in parameters and OFFSET_FIELD in parameters:
        return lister(site_id, limit=limit, offset=offset)
    return lister(site_id)


def read_store_page(
    lister: Callable[..., Any], rows_name: str, site_id: str, limit: int, offset: int
) -> tuple[list[dict[str, Any]], int]:
    """Return one page of stored rows and the count of the whole history.

    Why:
        ``CaptureListPage`` and ``RunListPage`` carry their rows under
        different names and their count under the same name, so one reader
        serves both histories and neither route counts anything itself.

    Args:
        lister: The list seam.
        rows_name: The attribute that holds the rows on the store page.
        site_id: The site to narrow to. An empty value reads every site.
        limit: The page size in force.
        offset: The page start in force.

    Returns:
        The rows of this page, and the count of the whole history.
    """
    page: Any = call_lister(lister, site_id, limit, offset)
    rows = plain_rows(getattr(page, rows_name, page))
    total: Any = getattr(page, TOTAL_FIELD, None)
    return rows, total if isinstance(total, int) else len(rows)


def whole_number(value: Any) -> int:
    """Return one count as a whole number, or zero for anything else.

    Why:
        A stored count arrives from a database driver, so it can be a string,
        a float, or absent. A page that added a string to an integer would
        stop the whole history over one bad row.

    Args:
        value: The stored count.

    Returns:
        The count, or zero.
    """
    if isinstance(value, bool):  # A boolean is an integer in Python, and no count is a boolean.
        return 0
    if isinstance(value, int):
        return value
    return 0


def row_counts(row: Mapping[str, Any]) -> dict[str, int]:
    """Return the device count and the client count of one history row.

    Why:
        The history exists to show what a site held before an upgrade and
        after it, so the two counts belong on every row. A direct name wins,
        because a later projection may compute the counts in the database.
        The stored ``counts`` map of ``capture/assembly.py`` supplies the rest,
        so no row costs a second read of the whole capture.

    Args:
        row: One stored row.

    Returns:
        The two counts, under the two row names.
    """
    counts = row.get(COUNTS_FIELD)
    stored: Mapping[str, Any] = counts if isinstance(counts, Mapping) else {}
    devices = row.get(DEVICE_COUNT_FIELD, stored.get(DEVICE_TOTAL_KEY))
    clients = row.get(CLIENT_COUNT_FIELD)
    if clients is None:  # No direct name, so add the three client groups of the capture.
        clients = sum(whole_number(stored.get(name)) for name in CLIENT_COUNT_KEYS)
    return {DEVICE_COUNT_FIELD: whole_number(devices), CLIENT_COUNT_FIELD: whole_number(clients)}


def history_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Return one history row that carries every field the contract names.

    Why:
        Section 6 of ``contracts/http-api.md`` promises six names on every
        row. A partial capture drops one of them, and a reader that meets a
        missing name reports a fault instead of showing an empty cell. The
        row keeps any further store field, because the contract reads as a
        smallest set and a later release can add a name.

        The two counts come last, because the store carries them inside the
        ``counts`` map and a default of zero would otherwise hide a real
        number.

    Args:
        row: One stored row.

    Returns:
        The row, with a default under every absent contract name.
    """
    shaped = dict(HISTORY_ROW_DEFAULTS)
    shaped.update(row)
    shaped.update(row_counts(row))  # The two counts run last, because a `counts` map fills them.
    return shaped


def short_moment(value: Any) -> str:
    """Return one stored moment in a short form that fits one line.

    Why:
        ``capture/assembly.py`` writes ``datetime.now(tz=UTC).isoformat()``,
        which holds 32 characters. Issue #2106 measured that text across four
        lines in the moment column, and one row then stood 113 pixels tall. The
        short form holds the day and the minute, which is enough to tell two
        captures apart. The page keeps the stored text in a ``title``
        attribute, so the second and the microsecond stay reachable.

        A value this reader cannot parse comes back unchanged. A later release
        of the store may write another shape, and a page that dropped the value
        would leave the operator with an empty cell.

    Args:
        value: The moment as the store holds it.

    Returns:
        The short moment, the value unchanged, or an empty text.
    """
    if not isinstance(value, str):  # A partial record can hold None under this name.
        return ""
    try:
        moment = datetime.fromisoformat(value)  # Reads the offset form and the trailing Z form.
    except ValueError:  # A shape this reader does not know stays as it stands.
        return value
    if moment.tzinfo is None:  # The store writes UTC, so a moment with no zone is already UTC.
        moment = moment.replace(tzinfo=UTC)
    return moment.astimezone(UTC).strftime(MOMENT_TEXT_FORMAT)  # One zone for every row.


def moment_texts(rows: Iterable[Mapping[str, Any]]) -> dict[str, str]:
    """Return the short moment of each history row, under the row key.

    Why:
        ``compare/render.py`` owns the columns of the table, and its row record
        is frozen. The page therefore reads the short moment from a map beside
        the view model, keyed by the capture identifier that each row already
        carries. A row with no identifier reaches no entry, because one empty
        key would serve two rows and the page would then show the moment of the
        wrong capture.

    Args:
        rows: The history rows of this page.

    Returns:
        The capture identifier and the short moment of each row.
    """
    logger.info("review: the portal shapes the moment text of the history rows")  # Before the work.
    texts = {
        capture_id: short_moment(row.get(STARTED_AT_FIELD))  # The row key reaches the short text.
        for row in rows
        if (capture_id := text_field(row, CAPTURE_ID_FIELD))  # A row with no key reaches no entry.
    }
    logger.debug("review: the portal shaped %s moment texts", len(texts))  # After the work.
    return texts


def read_site_name(rows: Sequence[Mapping[str, Any]]) -> str:
    """Return the site name that the history rows carry.

    Why:
        The page names the site in its heading, and the store already carries
        the name on each row. Reading it here saves a second cloud call, and
        an organization wide history simply shows no name.

    Args:
        rows: The rows of this page.

    Returns:
        The first site name found, or an empty string.
    """
    for row in rows:
        name = text_field(row, SITE_NAME_FIELD)
        if name:
            return name
    return ""


def call_builder(builder: Callable[..., Any], rows: list[dict[str, Any]], window: PageWindow) -> Any:
    """Call the history view builder with the window when it accepts one.

    Why:
        The route owns the page window and the compare package owns the view.
        The probe lets the two land in either order, because a call with a
        keyword that the builder does not declare would raise ``TypeError``.

    Args:
        builder: The view builder of the compare package.
        rows: The rows of this page.
        window: The page window in force.

    Returns:
        The history view.
    """
    try:
        parameters = signature(builder).parameters
    except (TypeError, ValueError):  # A builtin or a stand-in that declares nothing.
        return builder(rows)
    if WINDOW_KEY in parameters:
        return builder(rows, window=window)
    return builder(rows)


def build_history(rows: list[dict[str, Any]], window: PageWindow) -> Any:
    """Return the view that the history template prints.

    Why:
        ``compare.render.build_history_view`` owns the columns and the stored
        size of FR-032b. The name is read at call time, so a portal whose
        render module has not grown the builder yet still answers the page
        with the plain rows instead of a server error.

    Args:
        rows: The rows of this page.
        window: The page window in force.

    Returns:
        The history view, or a plain record of the rows and the window.
    """
    builder: Any = getattr(compare_render, HISTORY_VIEW_ATTRIBUTE, None)
    if not callable(builder):
        logger.warning("review: the compare render module holds no %s", HISTORY_VIEW_ATTRIBUTE)
        return {ROWS_KEY: rows, WINDOW_KEY: window}
    return call_builder(builder, rows, window)


# ---------------------------------------------------------------------------
# The routes
# ---------------------------------------------------------------------------


@review_bp.get(COMPARISONS_API_PATH)
@identity.require_session
def compare_captures() -> tuple[Response, int]:
    """Answer the comparison of two captures as JSON.

    Why:
        Section 6 documents no filter value for this endpoint, and
        ``ComparisonView.to_dict`` emits the filtered rows. The endpoint
        therefore builds the view with the default ``all``, so the body always
        holds every difference.

    Returns:
        The comparison body, or the refusal.
    """
    pair = read_pair(request.args.get(BEFORE_FIELD, ""), request.args.get(AFTER_FIELD, ""))
    both = pair.both()
    if both is None:
        return json_error(pair.status, pair.code, pair.message)
    parts = build_parts(*both)
    view = compare_render.build_view(both, parts.devices, parts.clients, parts.statistics)
    return jsonify(view.to_dict()), OK_STATUS


@review_bp.get(COMPARISONS_EXPORT_API_PATH)
@identity.require_session
def download_comparison() -> tuple[Response, int]:
    """Answer the comparison of two captures as a file attachment.

    Why:
        The download module owns the format rule and the column list, so the
        route reads the two captures, asks for the file, and passes the refusal
        straight on.

    Returns:
        The file answer, or the refusal.
    """
    pair = read_pair(request.args.get(BEFORE_FIELD, ""), request.args.get(AFTER_FIELD, ""))
    both = pair.both()
    if both is None:
        return json_error(pair.status, pair.code, pair.message)
    parts = build_parts(*both)
    wanted = request.args.get(FORMAT_FIELD, "")
    scope = request.args.get(SCOPE_FIELD, compare_download.SCOPE_DIFFERENCES)
    context = build_export_context(parts)
    result = compare_download.export_comparison(parts.devices, parts.clients, wanted, scope, context)
    if not result.ok:
        return json_error(BAD_REQUEST_STATUS, result.error, _EXPORT_MESSAGES.get(result.error, BAD_FORMAT_MESSAGE))
    return build_attachment(result)


@review_bp.get(COMPARE_PAGE_PATH)
@identity.require_session
def compare_page() -> str:
    """Render the human view of one comparison.

    Why:
        The page takes the same two query values as the endpoint. A request
        that names neither capture reaches the picker instead of a refusal,
        because the operator has not asked for anything yet.

    Returns:
        The rendered page.
    """
    before_id = request.args.get(BEFORE_FIELD, "").strip()
    after_id = request.args.get(AFTER_FIELD, "").strip()
    if not before_id or not after_id:
        return render_picker(before_id, after_id)
    pair = read_pair(before_id, after_id)
    both = pair.both()
    if both is None:
        return render_picker(before_id, after_id, pair.message)
    return render_comparison(build_parts(*both))


@review_bp.get(HISTORY_API_PATH)
@identity.require_session
def capture_history(site_id: str) -> tuple[Response, int]:
    """Answer the capture history of one site as JSON.

    Why:
        Section 6 of ``contracts/http-api.md`` names this path, sets the two
        page defaults, and sets the two body names. FR-032 lets any person read
        the record, so the route reads no lock and asks for no typed word.

    Args:
        site_id: The site of the path.

    Returns:
        The rows of this page and the count of the whole history.
    """
    limit, offset = read_window_values()
    rows, total = read_store_page(capture_lister(), CAPTURES_FIELD, site_id, limit, offset)
    logger.info("review: the portal listed %s capture rows of %s for one site", len(rows), total)
    return jsonify({CAPTURES_FIELD: [history_row(row) for row in rows], TOTAL_FIELD: total}), OK_STATUS


@review_bp.get(RUN_HISTORY_API_PATH)
@identity.require_session
def run_history(site_id: str) -> tuple[Response, int]:
    """Answer the upgrade run history of one site as JSON.

    Why:
        Task T205 asks for this list, and ``data-model.md`` holds the
        ``site_id`` and ``created_at`` index that answers it. The body mirrors
        the capture history, so one browser page reads both lists the same
        way. FR-032 keeps this read free of the lock as well.

    Args:
        site_id: The site of the path.

    Returns:
        The rows of this page and the count of the whole history.
    """
    limit, offset = read_window_values()
    rows, total = read_store_page(run_lister(), RUNS_FIELD, site_id, limit, offset)
    logger.info("review: the portal listed %s run rows of %s for one site", len(rows), total)
    return jsonify({RUNS_FIELD: rows, TOTAL_FIELD: total}), OK_STATUS


@review_bp.get(HISTORY_PAGE_PATH)
@identity.require_session
def history_page() -> str:
    """Render the human view of the capture history.

    Why:
        Section 6 of ``contracts/http-api.md`` asks for the same list as the
        endpoint, for one site or for the whole organization. The site travels
        as a query value rather than in the path, because one page serves both
        views and an absent site means every site.

    Returns:
        The rendered page.
    """
    site_id = request.args.get(SITE_ID_FIELD, "").strip()
    limit, offset = read_window_values()
    rows, total = read_store_page(capture_lister(), CAPTURES_FIELD, site_id, limit, offset)
    shaped = [history_row(row) for row in rows]
    return render_page(
        HISTORY_TEMPLATE,
        page_title=HISTORY_PAGE_TITLE,
        signed_in=True,
        site_name=read_site_name(shaped),
        history_view=build_history(shaped, build_window(site_id, limit, offset, total)),
        moment_texts=moment_texts(shaped),
    )
