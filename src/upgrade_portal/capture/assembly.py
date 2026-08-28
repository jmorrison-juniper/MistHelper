"""Assemble one upgrade capture document from the section reads.

Why:
    The readers in this package each answer one question. ``devices`` answers
    what the site holds, ``clients`` answers who uses it, and ``extras`` answers
    the tier 3 detail. No reader owns the stored document, because a reader that
    also owned the document would need every other reader. This module owns the
    document instead. It owns the key, the digests, the counts, the validation
    rules of ``data-model.md`` section 3.7, and the partial path.

    This module also owns the fan-out. A capture runs six call groups at one
    time through ``runtime/pools.py``. The pages inside one group stay
    sequential, because the cloud paginates with a cursor and a parallel page
    fetch inside one group would corrupt the sequence. The parallelism is
    between groups only.
"""

from __future__ import annotations

import hashlib  # SHA-256 for each section digest
import json  # Canonical JSON form of a section
import logging  # Action logging per Constitution VII
import threading  # Semaphore type of the shared worker shape
import time  # Monotonic clock, so the duration is measured and never estimated
import uuid  # Fresh nonce for the key of a run-less capture
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Final

from src.upgrade_portal.capture.clients import ClientRecord, normalize_mac
from src.upgrade_portal.capture.extras import ExtraSection
from src.upgrade_portal.runtime.pools import CapturePool, CaptureWorker

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# The document constants
# ---------------------------------------------------------------------------

SCHEMA_VERSION: Final[int] = 1
KEY_PREFIX: Final[str] = "cap-"

# WHAT: the prefix that a run key carries.
# WHY: runtime/runs.py builds a run key as "run-" plus 32 hexadecimal digits.
#      The capture key holds the same 32 digits, so the two keys read as a pair.
RUN_KEY_PREFIX: Final[str] = "run-"

ROLE_PRE: Final[str] = "pre"
ROLE_POST: Final[str] = "post"
FIRST_ORDINAL: Final[int] = 1

TIER_STANDARD: Final[int] = 2
TIER_EXTRA: Final[int] = 3

STATUS_COMPLETE: Final[str] = "complete"
STATUS_PARTIAL: Final[str] = "partial"
STATUS_FAILED: Final[str] = "failed"

REASON_READ_FAILED: Final[str] = "read_failed"
REASON_GROUP_FAILED: Final[str] = "call_group_failed"
HTTP_STATUS_NONE: Final[int] = 0

REASON_FIELDS: Final[frozenset[str]] = frozenset({"section", "reason", "http_status"})

# ---------------------------------------------------------------------------
# The digest constants
# ---------------------------------------------------------------------------

SECTION_DEVICES: Final[str] = "devices"
SECTION_WIRED: Final[str] = "clients_wired"
SECTION_WIRELESS: Final[str] = "clients_wireless"
SECTION_GUEST: Final[str] = "clients_guest"
SECTION_EXTRAS: Final[str] = "extras"
DIGEST_WHOLE: Final[str] = "whole"

# WHAT: the digest names that every capture holds.
# WHY: data-model.md section 3.2 names six keys. These four are the keys that
#      every tier holds. The "extras" key joins the map at tier 3 only, and the
#      "whole" key covers whichever keys are present.
BASE_DIGEST_SECTIONS: Final[tuple[str, ...]] = (SECTION_DEVICES, SECTION_WIRED, SECTION_WIRELESS, SECTION_GUEST)

# WHAT: the field names that never enter a digest.
# WHY: data-model.md:88 names the volatile list. A digest that kept "uptime"
#      would report a change on every capture and make the comparison useless.
VOLATILE_FIELDS: Final[frozenset[str]] = frozenset({"timestamp", "last_seen", "uptime", "_ts"})

# WHAT: the text that marks a counter of bytes or of packets.
# WHY: the cloud names a counter "tx_bytes", "rx_pkts", and several other forms.
#      A name test on the marker catches every form without a field list.
VOLATILE_MARKERS: Final[tuple[str, ...]] = ("bytes", "packets", "pkts")

# ---------------------------------------------------------------------------
# The report section names
# ---------------------------------------------------------------------------

SECTION_ALARMS: Final[str] = "alarms"  # The alarm row of the progress report.

# WHAT: the six report rows of contracts/http-api.md section "capture progress".
# WHY: a report row and a digest key are two different things, and this module
#      owns both. The stored document keeps the alarm records inside "extras",
#      because data-model.md section 3.5 nests them there and one digest covers
#      the whole extra set. The report splits the alarm row out, because an open
#      alarm blocks an upgrade and the operator watches that one read on its
#      own. A shared row would hide a slow alarm read behind four other reads.
#      The order matches the row order of the capture page.
SECTION_NAMES: Final[tuple[str, ...]] = BASE_DIGEST_SECTIONS + (SECTION_EXTRAS, SECTION_ALARMS)  # Six rows.

# ---------------------------------------------------------------------------
# The count constants
# ---------------------------------------------------------------------------

# WHAT: the nine count names of data-model.md:179.
# WHY: the summary line and the comparison heading read these names. The builder
#      returns these names and no others, so a later reader needs no membership
#      test.
COUNT_KEYS: Final[tuple[str, ...]] = (
    "devices_total",
    "devices_connected",
    "devices_disconnected",
    "gateways",
    "switches",
    "access_points",
    "clients_wired",
    "clients_wireless",
    "clients_guest",
)

DEVICE_STATUS_CONNECTED: Final[str] = "connected"
DEVICE_TYPE_COUNTS: Final[dict[str, str]] = {"gateway": "gateways", "switch": "switches", "ap": "access_points"}
CLIENT_GROUPS: Final[tuple[str, ...]] = ("wired", "wireless", "guest")

# ---------------------------------------------------------------------------
# The call group constants
# ---------------------------------------------------------------------------

GROUP_DEVICES: Final[str] = "devices"
GROUP_WIRELESS_STATISTICS: Final[str] = "wireless_statistics"
GROUP_WIRELESS_SEARCH: Final[str] = "wireless_search"
GROUP_WIRED_CLIENTS: Final[str] = "wired_clients"
GROUP_TIER_THREE: Final[str] = "tier_three"

# WHAT: the five call groups that a capture runs.
# WHY: plan.md sizes the capture pool at 4 workers, so the four groups of wave
#      one fill the pool exactly one time. The guest read rides inside the
#      wired group, because the guest call is small and a fifth wave-one group
#      would cost a queue slot for one short call. The port read rides inside
#      the tier 3 group, because `data-model.md` section 3.5 puts the switch
#      ports in the extra tier and a tier 2 capture therefore reads no port.
CALL_GROUPS: Final[tuple[str, ...]] = (
    GROUP_DEVICES,
    GROUP_WIRELESS_STATISTICS,
    GROUP_WIRELESS_SEARCH,
    GROUP_WIRED_CLIENTS,
    GROUP_TIER_THREE,
)

CALL_GROUP_DESCRIPTION: Final[str] = "capture call groups"

# ---------------------------------------------------------------------------
# The validation rule names
# ---------------------------------------------------------------------------

RULE_ORDINAL: Final[str] = "ordinal_below_one"
RULE_ROLE: Final[str] = "role_not_pre_for_first"
RULE_ORDER: Final[str] = "finished_before_started"
RULE_PARTIAL_REASONS: Final[str] = "status_reason_mismatch"
RULE_REASON_FIELDS: Final[str] = "reason_field_missing"
RULE_SIZE: Final[str] = "stored_size_not_positive"
RULE_INDEX_MATCH: Final[str] = "device_index_devices_mismatch"
RULE_DIGEST_COVER: Final[str] = "whole_digest_incomplete"

# WHAT: how many times the size stamp runs.
# WHY: the size number is part of the document, so writing it changes the size.
#      Four rounds let the number settle on its own width.
_SIZE_ROUNDS: Final[int] = 4


# ---------------------------------------------------------------------------
# The small value helpers
# ---------------------------------------------------------------------------


def _text(value: Any) -> str:
    """Return one value as plain text.

    Args:
        value: Any value from a cloud record or from a stored document.

    Returns:
        The text form. An absent value returns an empty string.
    """
    return "" if value is None else str(value)


def _whole_number(value: Any) -> int:
    """Return one value as a whole number.

    Why:
        A count and a status code must both be integers in the stored document.
        The cloud sometimes writes a number as text, and a validation rule must
        not fail on that difference alone.

    Args:
        value: Any value that should hold a number.

    Returns:
        The whole number. A value that holds no number returns 0.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _address(value: Any) -> str:
    """Return one hardware address in the single form that the capture compares.

    Why:
        ``clients.normalize_mac`` holds the one true form. The device reader
        keys its index through ``devices.normalize_device_mac``, and that
        function is still a pass-through. This helper runs both sides of every
        address comparison through the same normalizer, so the match holds
        whichever form the index key carries.

    Args:
        value: An address in any cloud form.

    Returns:
        The address in lower case with no separator. A value that holds no
        address returns its own trimmed lower case text.
    """
    normalized = normalize_mac(value)
    return normalized or _text(value).strip().lower()


def _utc_now_text() -> str:
    """Return the present moment as ISO 8601 text in UTC.

    Why:
        ``runtime/runs.py`` stamps a run with the same call. One shared form
        keeps a run and its captures comparable without a parse step.

    Returns:
        The moment, with the UTC offset.
    """
    return datetime.now(tz=UTC).isoformat()


def _moment(value: Any) -> datetime | None:
    """Read one ISO 8601 stamp.

    Args:
        value: The stored stamp text.

    Returns:
        The moment in an aware form, or None when the text holds no stamp.
    """
    try:
        parsed = datetime.fromisoformat(_text(value))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


# ---------------------------------------------------------------------------
# The document parts
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CaptureIdentity:
    """The run that owns one capture and the operator who asked for it.

    Why:
        The Five-Item Rule caps a record at 5 fields, and the capture document
        holds 24 top-level fields. This record carries the four fields that
        answer which run and which operator. The role is not a field, because
        ``data-model.md:189`` derives the role from the ordinal.

    Attributes:
        run_id: The key of the owning run. Empty for a run-less pre-check.
        ordinal: 1 for the pre-check. 2 for the post-check. Higher for a repeat.
        actor_email: The signed-in operator. Never a credential.
        standalone_key: The prebuilt key of a run-less capture. Empty for a run
            capture, which builds its key from the run and the ordinal.
    """

    run_id: str
    ordinal: int = FIRST_ORDINAL
    actor_email: str = ""
    standalone_key: str = ""


@dataclass(frozen=True, slots=True)
class SiteIdentity:
    """The organization and the site that one capture describes.

    Why:
        The document stores a name beside each identifier, so an export reads
        without a second call. One record carries all four, which keeps the
        assembly signature short.

    Attributes:
        org_id: The Mist organization identifier.
        org_name: The organization name for the interface and for an export.
        site_id: The Mist site identifier.
        site_name: The site name for the interface and for an export.
    """

    org_id: str = ""
    org_name: str = ""
    site_id: str = ""
    site_name: str = ""


@dataclass(frozen=True, slots=True)
class CaptureWindow:
    """The measured time window of one capture.

    Why:
        ``data-model.md:58`` asks for a measured duration, never an estimate.
        This record carries the measurement beside the two stamps, so no caller
        can subtract the stamps and call the result a measurement.

    Attributes:
        started_at: ISO 8601 in UTC.
        finished_at: ISO 8601 in UTC.
        duration_seconds: The elapsed time from a monotonic clock.
    """

    started_at: str
    finished_at: str
    duration_seconds: float


@dataclass(frozen=True, slots=True)
class CaptureSections:
    """The read sections that one capture document holds.

    Why:
        The assembly step takes one record instead of four lists, so the
        signature stays inside the Five-Item Rule. The tier is not a field,
        because ``extras`` already states it. An absent ``extras`` is tier 2.

    Attributes:
        device_index: The flat device map of data-model.md section 3.3.
        devices: The full device records.
        clients: The wired, wireless, and guest lists.
        extras: The tier 3 sections. None means tier 2.
    """

    device_index: dict[str, dict[str, Any]] = field(default_factory=dict)
    devices: list[dict[str, Any]] = field(default_factory=list)
    clients: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    extras: dict[str, list[dict[str, Any]]] | None = None


class CaptureTimer:
    """Measures the window of one capture.

    Why:
        A wall clock can step backward, so a duration read from two wall stamps
        can go negative. This timer stamps the wall clock for the record and
        measures the duration with a monotonic clock, so the duration is always
        the true elapsed time.
    """

    def __init__(self) -> None:
        """Stamp the start and begin the measurement."""
        self.started_at: str = _utc_now_text()
        self._monotonic_start: float = time.monotonic()

    def finish(self) -> CaptureWindow:
        """Close the window and report the measurement.

        Returns:
            The two wall stamps and the measured duration in seconds.
        """
        elapsed = round(time.monotonic() - self._monotonic_start, 3)
        return CaptureWindow(self.started_at, _utc_now_text(), elapsed)


def role_for_ordinal(ordinal: int) -> str:
    """Name the role of one ordinal.

    Why:
        Validation rule 2 ties the role to the ordinal. One function owns the
        tie, so the builder and the rule can never disagree.

    Args:
        ordinal: The capture ordinal.

    Returns:
        ``pre`` for the first capture. ``post`` for every later capture.
    """
    return ROLE_PRE if _whole_number(ordinal) <= FIRST_ORDINAL else ROLE_POST


def run_hex(run_id: str) -> str:
    """Return the hexadecimal tail of one run key.

    Why:
        ``runtime/runs.py`` builds a run key as ``run-`` plus 32 hexadecimal
        digits. The capture key holds the same digits, so an operator reads the
        pair without a lookup.

    Args:
        run_id: The run key, with or without the prefix.

    Returns:
        The hexadecimal tail in lower case.
    """
    text = _text(run_id).strip().lower()
    return text[len(RUN_KEY_PREFIX) :] if text.startswith(RUN_KEY_PREFIX) else text


def capture_key(run_id: str, ordinal: int) -> str:
    """Build the key of one capture.

    Why:
        ``data-model.md:45`` names the form. The key holds no slash and no
        colon, so the key sanitizer of the database leaves it alone.

    Args:
        run_id: The key of the owning run.
        ordinal: The capture ordinal.

    Returns:
        The key in the form ``cap-{run_hex}-{ordinal:02d}``.
    """
    return f"{KEY_PREFIX}{run_hex(run_id)}-{_whole_number(ordinal):02d}"


def standalone_capture_key() -> str:
    """Build the key of one run-less capture from a fresh nonce.

    Why:
        Issue 2096 names the defect. A run-less capture built the key from an
        empty run, so it landed under ``cap--01`` and the next run-less capture
        overwrote it. This builder reads a fresh ``uuid4`` hex nonce in place of
        the run, so two run-less captures never collide (D1, FR-096). The key
        keeps the run-capture form, so a reader meets no new shape.

    Returns:
        A key in the form ``cap-{nonce_hex}-01``.
    """
    return f"{KEY_PREFIX}{uuid.uuid4().hex}-{FIRST_ORDINAL:02d}"


def tier_of(sections: CaptureSections) -> int:
    """Name the tier that one section set describes.

    Args:
        sections: The read sections.

    Returns:
        3 when the set holds the extra sections. 2 otherwise.
    """
    return TIER_EXTRA if sections.extras is not None else TIER_STANDARD


# ---------------------------------------------------------------------------
# The canonical form and the digests
# ---------------------------------------------------------------------------


def is_volatile(name: str) -> bool:
    """Report whether one field name changes without a real change in the site.

    Why:
        A digest that kept a volatile field would report a change on every
        capture, and the whole comparison would then be useless.

    Args:
        name: One field name from a record.

    Returns:
        True when the field must leave the digest input.
    """
    lowered = _text(name).lower()
    if lowered in VOLATILE_FIELDS:
        return True
    return any(marker in lowered for marker in VOLATILE_MARKERS)


def strip_volatile(value: Any) -> Any:
    """Remove every volatile field at every depth.

    Why:
        A volatile field hides inside a list of records as often as it sits at
        the top. A shallow strip would leave the counter inside a port list, and
        the section digest would then change on every capture.

    Args:
        value: A section, a record, a list, or a plain value.

    Returns:
        The same shape with every volatile field removed.
    """
    if isinstance(value, Mapping):
        return {key: strip_volatile(item) for key, item in value.items() if not is_volatile(_text(key))}
    if isinstance(value, list | tuple):
        return [strip_volatile(item) for item in value]
    return value


def canonical_text(section: Any) -> str:
    """Return the canonical JSON form of one section, without the volatile fields.

    Why:
        Two captures must produce the same text for the same state. Sorted keys
        remove the key order of the cloud answer, and the tight separators
        remove the whitespace.

    Args:
        section: The section body.

    Returns:
        The canonical text.
    """
    stripped = strip_volatile(section)
    return json.dumps(stripped, sort_keys=True, separators=(",", ":"), default=str, ensure_ascii=True)


def section_digest(section: Any) -> str:
    """Hash the canonical form of one section.

    Args:
        section: The section body.

    Returns:
        The hexadecimal SHA-256 digest.
    """
    return hashlib.sha256(canonical_text(section).encode("utf-8")).hexdigest()


def digest_inputs(sections: CaptureSections) -> dict[str, Any]:
    """Name the body that each digest covers.

    Why:
        The digest names and the document sections are not the same words. The
        document holds one ``clients`` map and the digest holds three client
        names, so one function owns the mapping between them.

    Args:
        sections: The read sections.

    Returns:
        One body for each digest name. The ``extras`` name is absent at tier 2.
    """
    inputs: dict[str, Any] = {
        SECTION_DEVICES: list(sections.devices),
        SECTION_WIRED: list(sections.clients.get("wired", ())),
        SECTION_WIRELESS: list(sections.clients.get("wireless", ())),
        SECTION_GUEST: list(sections.clients.get("guest", ())),
    }
    if sections.extras is not None:
        inputs[SECTION_EXTRAS] = {name: list(rows) for name, rows in sections.extras.items()}
    return inputs


def whole_digest(digests: Mapping[str, str]) -> str:
    """Hash every section digest into the one digest that covers them all.

    Why:
        Validation rule 8 asks whether the whole digest covers every present
        section. A hash over the other digests answers that question with one
        comparison, and it needs no second pass over the records.

    Args:
        digests: The section digests. A ``whole`` entry is ignored.

    Returns:
        The hexadecimal SHA-256 digest of the section digests.
    """
    covered = {name: value for name, value in digests.items() if name != DIGEST_WHOLE}
    return section_digest(covered)


def build_digests(sections: CaptureSections) -> dict[str, str]:
    """Build the digest map of data-model.md section 3.2.

    Args:
        sections: The read sections.

    Returns:
        Six digests at tier 3. Five at tier 2, because ``extras`` is absent.
    """
    digests = {name: section_digest(body) for name, body in digest_inputs(sections).items()}
    digests[DIGEST_WHOLE] = whole_digest(digests)
    return digests


# ---------------------------------------------------------------------------
# The counts
# ---------------------------------------------------------------------------


def _type_counts(entries: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    """Count the devices of each type.

    Args:
        entries: The values of the device index.

    Returns:
        One count for each of the three type names. A type outside the three
        joins no count.
    """
    counts = {name: 0 for name in DEVICE_TYPE_COUNTS.values()}
    for entry in entries:
        name = DEVICE_TYPE_COUNTS.get(_text(entry.get("type")).lower())
        if name is not None:
            counts[name] += 1
    return counts


def _device_counts(index: Mapping[str, Mapping[str, Any]]) -> dict[str, int]:
    """Count the devices by state and by type.

    Why:
        The counts read the device index, not the raw device list. The index
        carries the joined state and the joined type, and validation rule 7
        already holds the two lists to the same members.

    Args:
        index: The device index of the capture.

    Returns:
        The six device counts.
    """
    entries = list(index.values())
    connected = sum(1 for entry in entries if _text(entry.get("status")).lower() == DEVICE_STATUS_CONNECTED)
    counts = {
        "devices_total": len(entries),
        "devices_connected": connected,
        "devices_disconnected": len(entries) - connected,
    }
    counts.update(_type_counts(entries))
    return counts


def build_counts(sections: CaptureSections) -> dict[str, int]:
    """Build the count map of data-model.md section 3.6.

    Why:
        The summary line and the comparison heading read this map. The result
        holds the nine names and no others, so a reader needs no membership
        test and an absent list still reports a zero.

    Args:
        sections: The read sections.

    Returns:
        The nine counts, in the order of ``COUNT_KEYS``.
    """
    counts = _device_counts(sections.device_index)
    for group in CLIENT_GROUPS:
        counts[f"clients_{group}"] = len(sections.clients.get(group, ()))
    return {name: _whole_number(counts.get(name)) for name in COUNT_KEYS}


# ---------------------------------------------------------------------------
# The partial path
# ---------------------------------------------------------------------------


def partial_reason(section: str, reason: str, http_status: int = HTTP_STATUS_NONE) -> dict[str, Any]:
    """Build one entry of ``partial_reasons``.

    Why:
        Validation rule 5 asks every entry for the same three fields. One
        builder owns the shape, so no caller writes a fourth name or drops one.

    Args:
        section: The section that failed.
        reason: A stable machine name for the failure.
        http_status: The status of the cloud call. 0 when no call was made.

    Returns:
        The entry, with the three fields of the data model.
    """
    return {"section": section, "reason": reason, "http_status": _whole_number(http_status)}


def http_status_of(error: BaseException) -> int:
    """Read the HTTP status that one error carries.

    Args:
        error: The error that a section read raised.

    Returns:
        The status code, or 0 when the error carries none.
    """
    status = getattr(error, "status_code", None)
    if status is None:
        status = getattr(getattr(error, "response", None), "status_code", None)
    return _whole_number(status)


def guarded_call(section: str, work: Callable[[], Any]) -> tuple[Any, list[dict[str, Any]]]:
    """Run one section read and turn a failure into one partial reason.

    Why:
        A failed section must never abort the whole capture. A capture that
        lost the alarm list still answers the question that the operator asked,
        so the read returns an empty value and names the loss instead.

    Args:
        section: The section name for the reason entry.
        work: The read. It takes no argument.

    Returns:
        The read result and the reasons. A good read returns no reason. A failed
        read returns None and one reason.
    """
    try:
        return work(), []
    except Exception as error:  # A failed section must never abort the whole capture
        logger.warning("Upgrade portal could not read the section %s: %s", section, type(error).__name__)
        return None, [partial_reason(section, REASON_READ_FAILED, http_status_of(error))]


def report_section(name: str) -> str:
    """Name the report row that one read belongs to.

    Why:
        A partial reason names the read that failed, and a read name is not a
        report row. ``extras.collect_extras`` answers with six tier 3 read
        names, and the report shows two rows for them. This function maps a read
        name to its row, so a failed ``tunnels`` read marks the ``extras`` row
        and a failed ``alarms`` read marks the ``alarms`` row. Without the map,
        the progress display would report every tier 3 failure against one row
        and an operator could not see which read lost the data.

    Args:
        name: A read name, from a partial reason or from a section map.

    Returns:
        The matching name of ``SECTION_NAMES``. A name outside that tuple is a
        tier 3 read, so it returns ``extras``.
    """
    read = _text(name).strip().lower()  # One form, because a caller may pass any case.
    return read if read in SECTION_NAMES else SECTION_EXTRAS  # A tier 3 read shares the extra row.


def extra_reasons(sections: Mapping[str, ExtraSection]) -> list[dict[str, Any]]:
    """Turn every failed tier 3 section into one partial reason.

    Why:
        ``extras`` reports a failure on the section record and leaves the
        document shape to this module. One entry for each failed section keeps
        validation rule 5 true.

    Args:
        sections: The result of ``extras.collect_extras``.

    Returns:
        One entry for each failed section, in the order of the section map.
    """
    return [partial_reason(entry.name, entry.reason, entry.http_status) for entry in sections.values() if entry.failed]


def resolve_status(sections: CaptureSections, reasons: Sequence[Mapping[str, Any]]) -> str:
    """Name the status of one capture.

    Why:
        Validation rule 4 allows ``partial`` only beside a reason. A capture
        that read nothing at all is not partial. It is failed, because a
        comparison against it would report every device as lost.

    Args:
        sections: The read sections.
        reasons: The partial reasons that the reads collected.

    Returns:
        ``complete``, ``partial``, or ``failed``.
    """
    if not reasons:
        return STATUS_COMPLETE
    if sections.devices or any(sections.clients.values()):
        return STATUS_PARTIAL
    return STATUS_FAILED


# ---------------------------------------------------------------------------
# The call groups
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CallGroup:
    """One capture call group and the reads inside it.

    Why:
        The pool runs a work item, not a function name. This record pairs the
        group name with its reads, so a failure still names the group that lost
        the data.

    Attributes:
        name: One name from ``CALL_GROUPS``.
        work: Every read of this group, in one callable that takes no argument.
    """

    name: str
    work: Callable[[], Any]


@dataclass(frozen=True, slots=True)
class GroupResult:
    """The outcome of one call group.

    Attributes:
        name: The group name.
        value: The read result. None after a failure.
        reasons: One partial reason for each failure inside this group.
    """

    name: str
    value: Any = None
    reasons: list[dict[str, Any]] = field(default_factory=list)


# WHAT: the shape of the pool call that runs the groups.
# WHY: a test passes its own runner, so no test imports MistHelper and no test
#      opens a socket. The default stays the one pool the repository owns.
GroupExecutor = Callable[[list[Any], CaptureWorker, str], tuple[list[Any], list[Any]]]


def sequential_reads(readers: Sequence[Callable[[], Any]]) -> list[Any]:
    """Run the reads of one call group in order.

    Why:
        The cloud paginates with a cursor. Two page fetches of one call at the
        same time corrupt the sequence and drop rows. Every read inside one
        group therefore runs in order, and the parallelism stays between the
        groups.

    Args:
        readers: The reads of this group, in the order they must run.

    Returns:
        One result for each read, in the same order.
    """
    return [read() for read in readers]


def _group_worker(item: CallGroup, connection_semaphore: threading.Semaphore) -> GroupResult:
    """Run one call group under the shared pool.

    Args:
        item: The call group to run.
        connection_semaphore: The semaphore that the shared executor supplies.
            The capture pool already holds the budget, so this worker does not
            take a second slot.

    Returns:
        The group outcome. The result is always truthy, because the executor
        counts a falsy result as failed.
    """
    del connection_semaphore  # The capture pool holds the budget for this worker
    value, reasons = guarded_call(item.name, item.work)
    return GroupResult(item.name, value, reasons)


def _lost_group(item: CallGroup) -> GroupResult:
    """Report one call group that the pool never finished.

    Args:
        item: The call group that the pool returned as failed.

    Returns:
        An empty outcome with one partial reason.
    """
    logger.warning("Upgrade portal lost the capture call group %s", item.name)
    return GroupResult(item.name, None, [partial_reason(item.name, REASON_GROUP_FAILED)])


def run_call_groups(groups: Sequence[CallGroup], executor: GroupExecutor | None = None) -> dict[str, GroupResult]:
    """Run every call group at one time and collect the outcomes.

    Why:
        Six groups at one time hold the capture inside the 3-second render
        target for a large site. The pool bounds the work in flight, so the
        capture keeps its share of the hourly call budget.

    Args:
        groups: One entry for each call group.
        executor: The pool call. None runs the shared capture pool.

    Returns:
        One outcome for each group, by group name.
    """
    run: GroupExecutor = executor if executor is not None else CapturePool.execute
    successful, failed = run(list(groups), _group_worker, CALL_GROUP_DESCRIPTION)
    results: dict[str, GroupResult] = {result.name: result for result in successful}
    for item in failed:
        results[item.name] = _lost_group(item)
    return results


def group_reasons(results: Mapping[str, GroupResult]) -> list[dict[str, Any]]:
    """Collect the partial reasons of every call group.

    Args:
        results: The result of ``run_call_groups``.

    Returns:
        Every reason, in group order.
    """
    return [reason for result in results.values() for reason in result.reasons]


def group_value(results: Mapping[str, GroupResult], name: str, default: Any = None) -> Any:
    """Read the result of one call group.

    Args:
        results: The result of ``run_call_groups``.
        name: The group name.
        default: The value for a group that failed or never ran.

    Returns:
        The group result, or the default.
    """
    result = results.get(name)
    if result is None or result.value is None:
        return default
    return result.value


# ---------------------------------------------------------------------------
# The client rows
# ---------------------------------------------------------------------------


def fill_device_names(
    records: Sequence[ClientRecord], device_index: Mapping[str, Mapping[str, Any]]
) -> list[dict[str, Any]]:
    """Flatten the client records and name the device that serves each client.

    Why:
        The client reader leaves ``device_name`` empty on purpose, because the
        client calls answer with an address and no name. The moved-client report
        shows a name, so the assembly step fills the name from the device index.

    Args:
        records: The client records of one list.
        device_index: The device index of the same capture.

    Returns:
        One flat row for each record. A row whose serving device is outside the
        index keeps no device name.
    """
    names = {_address(key): _text(entry.get("name")) for key, entry in device_index.items()}
    rows: list[dict[str, Any]] = []
    for record in records:
        row = record.to_dict()
        name = names.get(_address(row.get("device_mac")), "")
        if name:
            row["device_name"] = name
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# The size stamp
# ---------------------------------------------------------------------------


def measure_size_bytes(document: Mapping[str, Any]) -> int:
    """Measure the stored size of one document.

    Why:
        ``data-model.md:62`` asks for the measured size, and validation rule 6
        asks for a size above zero. The store owns the definition of the size,
        and this function repeats it: the byte count of the canonical JSON text
        of the document body, in UTF-8. The body drops every field whose name
        starts with an underscore, because the writer and the server add those
        fields after the caller builds the document. The two modules therefore
        report the same number, and a read-back never disagrees with the write.

        The measurement stays here rather than calling the store, because the
        store imports the database driver and the exporter. An assembly step
        must run without a database at hand.

    Args:
        document: The capture document.

    Returns:
        The size in bytes.
    """
    body = {key: value for key, value in document.items() if not key.startswith("_")}
    return len(json.dumps(body, sort_keys=True, separators=(",", ":"), default=str, ensure_ascii=True).encode("utf-8"))


def stamp_size(document: Mapping[str, Any]) -> dict[str, Any]:
    """Write the measured size into the document.

    Why:
        The size number lives inside the document it measures, so the first
        measurement changes the answer. A few rounds let the number settle on
        its own width.

        The loop stops the moment the number repeats. A whole capture is a
        document of several megabytes, and every round serializes all of it, so
        a round that cannot change the answer is pure waste. The number settles
        after two rounds for almost every capture, and it settles after three
        rounds when the width of the number grows. ``capture/store.py`` already
        stops early, so this loop now matches it and both report one number.

    Args:
        document: The capture document.

    Returns:
        A copy of the document with ``stored_size_bytes`` set.
    """
    stamped = dict(document)
    for _round in range(_SIZE_ROUNDS):
        size = measure_size_bytes(stamped)  # One whole serialization of the document
        if size == stamped.get("stored_size_bytes"):  # The width settled, so a later round reads the same number
            break
        stamped["stored_size_bytes"] = size  # The new number may change its own width, so measure again
    return stamped


# ---------------------------------------------------------------------------
# The document builder
# ---------------------------------------------------------------------------


def _identity_fields(identity: CaptureIdentity, site: SiteIdentity) -> dict[str, Any]:
    """Build the identity fields of one capture document.

    Args:
        identity: The run, the ordinal, and the operator.
        site: The organization and the site.

    Returns:
        The eleven identity fields.
    """
    key = identity.standalone_key or capture_key(identity.run_id, identity.ordinal)  # A nonce key wins for no run.
    return {
        "_key": key,
        "capture_id": key,
        "schema_version": SCHEMA_VERSION,
        "run_id": identity.run_id,
        "ordinal": _whole_number(identity.ordinal),
        "role": role_for_ordinal(identity.ordinal),
        "org_id": site.org_id,
        "org_name": site.org_name,
        "site_id": site.site_id,
        "site_name": site.site_name,
        "actor_email": identity.actor_email,
    }


def _window_fields(window: CaptureWindow) -> dict[str, Any]:
    """Build the time fields of one capture document.

    Args:
        window: The measured window.

    Returns:
        The two stamps and the measured duration.
    """
    return {
        "started_at": window.started_at,
        "finished_at": window.finished_at,
        "duration_seconds": window.duration_seconds,
    }


def _status_fields(sections: CaptureSections, reasons: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the tier and the status fields of one capture document.

    Args:
        sections: The read sections.
        reasons: The partial reasons that the reads collected.

    Returns:
        The tier, the status, the reasons, and a size placeholder.
    """
    return {
        "tier": tier_of(sections),
        "capture_status": resolve_status(sections, reasons),
        "partial_reasons": reasons,
        "stored_size_bytes": 0,
    }


def _body_fields(sections: CaptureSections) -> dict[str, Any]:
    """Build the read fields of one capture document.

    Args:
        sections: The read sections.

    Returns:
        The digests, the device index, the devices, the clients, the counts, and
        the extra sections at tier 3.
    """
    body: dict[str, Any] = {
        "digests": build_digests(sections),
        "device_index": {key: dict(entry) for key, entry in sections.device_index.items()},
        "devices": [dict(record) for record in sections.devices],
        "clients": {name: list(sections.clients.get(name, ())) for name in CLIENT_GROUPS},
        "counts": build_counts(sections),
    }
    if sections.extras is not None:
        body[SECTION_EXTRAS] = {name: list(rows) for name, rows in sections.extras.items()}
    return body


def build_capture(
    identity: CaptureIdentity,
    site: SiteIdentity,
    window: CaptureWindow,
    sections: CaptureSections,
    partial_reasons: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Assemble one capture document.

    Why:
        The stored document is the only record that a comparison reads. One
        builder owns every top-level field of ``data-model.md`` section 3.1, so
        no caller can leave a field out and no caller can invent one.

    Args:
        identity: The run, the ordinal, and the operator.
        site: The organization and the site.
        window: The measured time window.
        sections: The read sections.
        partial_reasons: The reasons that the reads collected. None means every
            read finished.

    Returns:
        The capture document, with the size measured.
    """
    reasons = [dict(entry) for entry in partial_reasons or ()]
    document: dict[str, Any] = _identity_fields(identity, site)
    document.update(_window_fields(window))
    document.update(_status_fields(sections, reasons))
    document.update(_body_fields(sections))
    return stamp_size(document)


# ---------------------------------------------------------------------------
# The validation rules of data-model.md section 3.7
# ---------------------------------------------------------------------------


def _rule_ordinal(document: Mapping[str, Any]) -> bool:
    """Check rule 1. The ordinal is 1 or greater.

    Args:
        document: The capture document.

    Returns:
        True when the rule holds.
    """
    return _whole_number(document.get("ordinal")) >= FIRST_ORDINAL


def _rule_role(document: Mapping[str, Any]) -> bool:
    """Check rule 2. The role is ``pre`` when the ordinal is 1.

    Args:
        document: The capture document.

    Returns:
        True when the rule holds.
    """
    if _whole_number(document.get("ordinal")) != FIRST_ORDINAL:
        return True
    return _text(document.get("role")) == ROLE_PRE


def _rule_order(document: Mapping[str, Any]) -> bool:
    """Check rule 3. The finish is not earlier than the start.

    Args:
        document: The capture document.

    Returns:
        True when the rule holds.
    """
    started = _moment(document.get("started_at"))
    finished = _moment(document.get("finished_at"))
    if started is None or finished is None:
        return False
    return finished >= started


def _rule_partial_reasons(document: Mapping[str, Any]) -> bool:
    """Check rule 4. The status and the reason list agree.

    Args:
        document: The capture document.

    Returns:
        True when the rule holds.
    """
    status = _text(document.get("capture_status"))
    reasons = document.get("partial_reasons") or []
    if status == STATUS_COMPLETE:
        return not reasons
    return status != STATUS_PARTIAL or bool(reasons)


def _rule_reason_fields(document: Mapping[str, Any]) -> bool:
    """Check rule 5. Each reason holds the three named fields.

    Args:
        document: The capture document.

    Returns:
        True when the rule holds.
    """
    reasons = document.get("partial_reasons") or []
    return all(REASON_FIELDS <= set(entry) for entry in reasons)


def _rule_size(document: Mapping[str, Any]) -> bool:
    """Check rule 6. The stored size is above zero.

    Args:
        document: The capture document.

    Returns:
        True when the rule holds.
    """
    return _whole_number(document.get("stored_size_bytes")) > 0


def _rule_index_match(document: Mapping[str, Any]) -> bool:
    """Check rule 7. The device index and the device list hold the same members.

    Why:
        This rule is the sharp one. A device in the index but not in the list
        would show a change that no record explains. A device in the list but
        not in the index would never enter a comparison at all.

    Args:
        document: The capture document.

    Returns:
        True when the rule holds.
    """
    index_keys = {_address(key) for key in document.get("device_index") or {}}
    device_keys = {_address(record.get("mac")) for record in document.get("devices") or []}
    return index_keys == device_keys


def _rule_digest_cover(document: Mapping[str, Any]) -> bool:
    """Check rule 8. The whole digest covers every present section.

    Args:
        document: The capture document.

    Returns:
        True when the rule holds.
    """
    digests: dict[str, str] = dict(document.get("digests") or {})
    expected = set(BASE_DIGEST_SECTIONS)
    if SECTION_EXTRAS in document:
        expected.add(SECTION_EXTRAS)
    covered = set(digests) - {DIGEST_WHOLE}
    return covered == expected and digests.get(DIGEST_WHOLE) == whole_digest(digests)


# WHAT: the eight rules of data-model.md section 3.7, in that order.
# WHY: one table holds the rule name beside its test, so a caller reads a stable
#      machine name and never a sentence that a rewrite could change.
_RULES: Final[tuple[tuple[str, Callable[[Mapping[str, Any]], bool]], ...]] = (
    (RULE_ORDINAL, _rule_ordinal),
    (RULE_ROLE, _rule_role),
    (RULE_ORDER, _rule_order),
    (RULE_PARTIAL_REASONS, _rule_partial_reasons),
    (RULE_REASON_FIELDS, _rule_reason_fields),
    (RULE_SIZE, _rule_size),
    (RULE_INDEX_MATCH, _rule_index_match),
    (RULE_DIGEST_COVER, _rule_digest_cover),
)


def validate_capture(document: Mapping[str, Any]) -> list[str]:
    """Name every validation rule that one document breaks.

    Why:
        A document that breaks a rule must not reach the comparison, because a
        comparison over a broken document reports a change that never happened.
        The result names the rules, so a caller reports them all at one time.

    Args:
        document: The capture document.

    Returns:
        One stable rule name for each broken rule. An empty list means the
        document holds every rule.
    """
    broken = [name for name, holds in _RULES if not holds(document)]
    if broken:
        logger.warning("Upgrade portal capture %s broke the rules %s", _text(document.get("capture_id")), broken)
    return broken


__all__ = [
    "BASE_DIGEST_SECTIONS",
    "CALL_GROUPS",
    "CALL_GROUP_DESCRIPTION",
    "COUNT_KEYS",
    "DIGEST_WHOLE",
    "GROUP_DEVICES",
    "GROUP_TIER_THREE",
    "GROUP_WIRED_CLIENTS",
    "GROUP_WIRELESS_SEARCH",
    "GROUP_WIRELESS_STATISTICS",
    "HTTP_STATUS_NONE",
    "REASON_GROUP_FAILED",
    "REASON_READ_FAILED",
    "ROLE_POST",
    "ROLE_PRE",
    "RULE_DIGEST_COVER",
    "RULE_INDEX_MATCH",
    "RULE_ORDER",
    "RULE_ORDINAL",
    "RULE_PARTIAL_REASONS",
    "RULE_REASON_FIELDS",
    "RULE_ROLE",
    "RULE_SIZE",
    "SCHEMA_VERSION",
    "SECTION_ALARMS",
    "SECTION_DEVICES",
    "SECTION_EXTRAS",
    "SECTION_GUEST",
    "SECTION_NAMES",
    "SECTION_WIRED",
    "SECTION_WIRELESS",
    "STATUS_COMPLETE",
    "STATUS_FAILED",
    "STATUS_PARTIAL",
    "TIER_EXTRA",
    "TIER_STANDARD",
    "VOLATILE_FIELDS",
    "VOLATILE_MARKERS",
    "CallGroup",
    "CaptureIdentity",
    "CaptureSections",
    "CaptureTimer",
    "CaptureWindow",
    "GroupExecutor",
    "GroupResult",
    "SiteIdentity",
    "build_capture",
    "build_counts",
    "build_digests",
    "canonical_text",
    "capture_key",
    "digest_inputs",
    "extra_reasons",
    "fill_device_names",
    "group_reasons",
    "group_value",
    "guarded_call",
    "http_status_of",
    "is_volatile",
    "measure_size_bytes",
    "partial_reason",
    "report_section",
    "resolve_status",
    "role_for_ordinal",
    "run_call_groups",
    "run_hex",
    "section_digest",
    "sequential_reads",
    "stamp_size",
    "standalone_capture_key",
    "strip_volatile",
    "tier_of",
    "validate_capture",
    "whole_digest",
]
