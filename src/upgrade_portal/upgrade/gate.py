"""The settle gate that decides when one upgraded device is ready again.

Why:
    An upgrade is not finished when the cloud reports the job complete. The
    device must reboot, return, and report the new firmware. A gate that
    guesses too early sends the post-check while devices are still down, and
    the comparison then reports a loss that never happened.

    The gate needs three signals before it calls one device settled.

    1. A reconnect event arrives from the event poll.

    2. The uptime decreased and, together with that, the version changed. A
       device that reached the gate with no earlier uptime is the exception.
       The gate cannot prove a fall against a value it never read, so that
       device settles on the version change alone and the gate warns.

    3. An extra wait of 60 seconds passes after signal 2. An access point
       waits a further 60 seconds, because its statistics and its uptime need
       longer to reflect a fresh boot.

    The decision is pure. ``advance`` takes the readings and returns the new
    progress record, and it never sleeps. The clock sits behind an injected
    callable on ``SettleGate``, so a test drives time forward with a counter
    and waits no real seconds.

    The statistics poll reads the whole fleet with one call every 20 seconds.
    A per-device poll would multiply the call count by the device count and
    would exhaust the hourly quota at ``src/utils/rate_limiting.py:56``.

    A statistics record can be older than the upgrade that the gate watches,
    because the cloud can serve a copy that it cached earlier. That copy holds
    the uptime and the version from before the reboot. It can settle a device
    that never rebooted, and it can delay a device that did reboot. FR-046 at
    ``spec.md:525`` therefore asks the gate to ignore such a record.

    The gate compares the ``last_seen`` value of each record against the
    highest ``last_seen`` that it already read for the same device. A record
    that does not raise that mark repeats a snapshot that the gate read
    before, so it holds no new evidence and the gate drops it.

    Both values of that comparison come from the cloud, and both come from the
    same field of the same device. FR-045 at ``spec.md:523`` forbids a
    comparison between a cloud timestamp and the local clock, because the two
    machines keep separate clocks and a difference between them would make the
    result wrong. A record with no ``last_seen`` is never stale, because an
    absent value is no evidence. That rule follows ``uptime_decreased``.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from functools import partial
from typing import Any

import mistapi

from src.firmware.upgrade_service import GatewayFamily, read_upgrade_status
from src.upgrade_portal.capture.devices import (
    HTTP_STATUS_NONE,
    REASON_READ_FAILED,
    guard_page_count,
    normalize_device_mac,
    resolve_page_limit,
)

logger = logging.getLogger(__name__)

SECTION_GATE_STATISTICS = "upgrade_gate_statistics"

# The statistics call answers with access points only when the caller omits
# the type. The SDK adds the query parameter only when the value is present
# (.venv/Lib/site-packages/mistapi/api/v1/orgs/stats.py:460), and the vendor
# default is "ap" (the same file, line 427). A gate that read access points
# only would wait for ever on a switch.
STATISTICS_TYPE = "all"

# Warning: this parameter adds fields and can make each answer much larger.
# The vendor calls it a list of ADDITIONAL fields
# (.venv/Lib/site-packages/mistapi/api/v1/orgs/stats.py:439). It adds fields
# such as "ports" and "bgp_peers". It does not remove the base fields. This
# value therefore holds the four fields that the gate reads, which keeps the
# answer at its base size and asks for no large extra section. The SDK sends
# the value as text, so a caller passes text and never a Python list.
STATISTICS_FIELDS = "mac,version,uptime,last_seen"

# One poll of the whole fleet every 20 seconds is 180 calls each hour. The
# event poll of the run adds a second stream of the same rate, so the pair
# stays at 360 calls each hour. That is 7.2 percent of the 5000 call quota at
# src/utils/rate_limiting.py:56.
POLL_INTERVAL_SECONDS = 20
SECONDS_PER_HOUR = 3600
HOURLY_CALL_QUOTA = 5000
MAX_CALLS_PER_HOUR = 360

# The two waits below are the choice of this feature. The vendor publishes no
# settle time for a switch or a gateway
# (specs/1823-upgrade-capture-portal/research/settle-gate-apis.md:881).
SETTLE_WAIT_SECONDS = 60
ACCESS_POINT_EXTRA_WAIT_SECONDS = 60

DEVICE_TYPE_ACCESS_POINT = "ap"

# The three outcome tokens of the version check. FR-051 at ``spec.md:536`` asks
# the portal to mark a device that returns on a version that nobody requested.
# A device that reports no version yet holds its own token, because it is still
# settling. A false alarm would send an operator to a device that is well.
OUTCOME_VERSION_MATCH = "version_match"
OUTCOME_VERSION_MISMATCH = "version_mismatch"
OUTCOME_VERSION_PENDING = "version_pending"

# The field names of one target row of the run record. ``upgrade/options.py``
# writes the requested version under ``version_target`` and opens the reported
# version as null under ``version_after``. No writer fills ``version_outcome``
# on a stored row, because no writer fills ``version_after`` on a stored row
# either. The run page and the browser script each compute the verdict, and both
# read this name.
# Warning: a writer of ``version_outcome`` can break the seven keys that
# ``contracts/http-api.md`` fixes. ``RunStatusView`` copies every stored key of
# a target row to the browser, so that writer would add an eighth key.
FIELD_VERSION_TARGET = "version_target"
FIELD_VERSION_AFTER = "version_after"
FIELD_VERSION_OUTCOME = "version_outcome"


@dataclass(frozen=True, slots=True)
class GateTarget:
    """The fixed facts about one device that the gate compares against.

    Why:
        The gate needs the state of the device before the upgrade started.
        The run record holds these values, and they never change while the
        run continues. Holding them apart from the progress record keeps the
        moving state small and keeps the decision function pure.

        ``uptime_before`` holds a null, because the pre-check may read a
        device whose statistics record carried no uptime. A zero in its place
        would make every later reading look larger, the gate would never see
        a decrease, and the device would wait to the phase deadline.

        ``last_seen_before`` is the absolute anchor. The cloud raises that
        moment each time it hears from the device, so a device whose uptime
        never arrives can still prove that it returned. The field carries a
        default, because a caller that holds no anchor must still build a
        target, and a null anchor proves nothing on its own.

    Attributes:
        mac: The device address in lower case with no separator.
        device_type: ``ap``, ``switch``, or ``gateway``.
        version_before: The firmware version read before the upgrade.
        uptime_before: The uptime in seconds read before the upgrade. None
            when the pre-check read no uptime for this device.
        last_seen_before: The moment that the cloud last heard from the device
            before the upgrade, in epoch seconds of the cloud. None when the
            pre-check read no moment for this device.
    """

    mac: str
    device_type: str
    version_before: str
    uptime_before: int | None
    last_seen_before: int | None = None


@dataclass(frozen=True, slots=True)
class GateReading:
    """One statistics reading of one device.

    Why:
        The uptime is nullable in the vendor schema. A null reading means
        "no reading", never zero, so this record keeps the null and lets the
        decision function retry. A reader that turned a null into zero would
        see a decrease and would settle a device that never rebooted.

        The ``last_seen`` value dates the record on the clock of the cloud, so
        the gate can drop a record that repeats an earlier snapshot. The gate
        compares that value against an earlier ``last_seen`` and never against
        the local clock.

    Attributes:
        mac: The device address in lower case with no separator.
        version: The firmware version. Empty when the cloud reported none.
        uptime: The uptime in seconds. None when the cloud reported null.
        last_seen: The moment that the cloud last heard from the device, in
            epoch seconds of the cloud. None when the record carried no value.
    """

    mac: str
    version: str
    uptime: int | None
    last_seen: int | None = None


@dataclass(frozen=True, slots=True)
class GateSignals:
    """The observations of one poll round for one device.

    Why:
        The gate reads two sources: the event poll and the statistics poll.
        One record for both keeps the decision function at four parameters
        and lets a caller pass a round with either source missing.

    Attributes:
        reconnected: True when a reconnect event arrived in this round.
        reading: The statistics reading of this round, or None when the poll
            returned no record for this device.
    """

    reconnected: bool = False
    reading: GateReading | None = None


@dataclass(frozen=True, slots=True)
class GateProgress:
    """The signals that one device has produced so far.

    Why:
        The three signals arrive at different times and in any order, so the
        gate must remember them. Every field only moves forward, which makes
        a repeated round harmless and makes a retry safe.

        ``last_seen_at`` follows that same rule. It only rises, so a record
        that repeats an earlier snapshot can never move the gate a second
        time. The mark holds a cloud value, which lets the staleness test
        compare two cloud values and use no local clock.

    Attributes:
        reconnected: True after the reconnect event arrived.
        reboot_at: The clock reading when the uptime decreased and the
            version changed together. None until both hold.
        settled_at: The clock reading when the extra wait finished.
        version_after: The version that the device reported at ``reboot_at``.
        last_seen_at: The highest ``last_seen`` value that the gate read for
            this device. None before the first record that carries one.
    """

    reconnected: bool = False
    reboot_at: float | None = None
    settled_at: float | None = None
    version_after: str | None = None
    last_seen_at: int | None = None


@dataclass(frozen=True, slots=True)
class FleetRead:
    """The result of one statistics poll of the whole fleet.

    Why:
        A poll that fails must not stop the run. The read returns the
        readings and the reasons together, so the driver keeps the progress
        it already has and marks the round partial.

    Attributes:
        readings: One reading for each device, keyed by the address.
        partial_reasons: One entry for each fault. Empty after a whole read.
    """

    readings: dict[str, GateReading]
    partial_reasons: list[dict[str, Any]]


def polls_per_hour(interval_seconds: int) -> int:
    """Return the number of calls that one poll stream makes in one hour.

    Why:
        The budget of this feature must stay checkable rather than stated.
        A test calls this function and compares the answer against
        ``MAX_CALLS_PER_HOUR`` and against the quota, so a change of the
        interval that breaks the budget fails the build.

    Args:
        interval_seconds: The wait between two calls of one stream.

    Returns:
        The number of calls in one hour.

    Raises:
        ValueError: When the interval is zero or less.
    """
    if interval_seconds <= 0:
        raise ValueError("The poll interval must be greater than zero seconds.")
    return SECONDS_PER_HOUR // interval_seconds


def settle_wait_seconds(device_type: str) -> int:
    """Return the extra wait that one device type needs after its reboot.

    Why:
        An access point reports its statistics and its uptime later than a
        switch or a gateway. A gate that used one wait for every type would
        call an access point settled too early. Its record would still hold
        the values from before the reboot.

    Args:
        device_type: ``ap``, ``switch``, or ``gateway``.

    Returns:
        The wait in seconds that follows the reboot signal.
    """
    if str(device_type).strip().lower() == DEVICE_TYPE_ACCESS_POINT:
        return SETTLE_WAIT_SECONDS + ACCESS_POINT_EXTRA_WAIT_SECONDS
    return SETTLE_WAIT_SECONDS


def uptime_decreased(uptime_before: int | None, uptime_now: int | None) -> bool:
    """Report whether the uptime fell below the value read before the upgrade.

    Why:
        The test is "current is less than previous". It is never "current is
        near zero". A device that reboots quickly already reports a small
        positive uptime by the time the poll reads it, so a near-zero test
        misses the reboot and the gate waits for ever.

        A null is not zero. A null current reading means the device reported
        nothing, and a null earlier value means the pre-check read nothing.
        Both answer False, because neither can prove a fall.

        Warning: False here means "no proof" and can hide a real reboot. A
        caller that holds no earlier uptime must reach its verdict another way,
        or the device waits to the phase deadline.

    Args:
        uptime_before: The uptime in seconds read before the upgrade, or None
            when the pre-check read none.
        uptime_now: The uptime in seconds of the current reading, or None.

    Returns:
        True only when two real readings show a fall.
    """
    if uptime_before is None or uptime_now is None:  # A null is never zero, so it proves nothing.
        return False  # The caller retries or applies the version-only rule.
    return uptime_now < uptime_before  # Two real readings, so the comparison is meaningful.


def version_changed(version_before: str, version_now: str) -> bool:
    """Report whether one reading shows a different firmware version.

    Why:
        An empty version is no reading, never a change. A gate that counted
        an empty value as a change would settle a device from a record that
        the cloud had not filled yet.

    Args:
        version_before: The firmware version read before the upgrade.
        version_now: The firmware version of the current reading.

    Returns:
        True only when the reading holds a version that differs.
    """
    return bool(version_now) and version_now != version_before  # An empty reading is no change.


def normalize_version(value: Any) -> str:
    """Return one firmware version in the form that every comparison reads.

    Why:
        The operator picks a version from a list, and the device reports a
        version of its own. The two values travel through different systems,
        so one can arrive with a leading space or with a different case. A raw
        comparison would then report a mismatch that no operator can repair.

        The rule stays narrow: remove the surrounding whitespace and remove the
        case. It changes no inner character, so ``23.4R2-S3.9`` and
        ``23.4R2.13`` stay different versions. The run page repeats this same
        rule with the Jinja filters ``trim`` and ``lower``, so the page and the
        code can never disagree.

    Args:
        value: The raw version value. A null and a number both reach here.

    Returns:
        The version with no surrounding whitespace and no upper case. An empty
        string when the value holds no reading.
    """
    if value is None:  # A null is no reading, and str(None) would give the word None.
        return ""  # An empty string is the one form that every rule below reads as absent.
    return str(value).strip().lower()  # Lower case, never casefold, so the Jinja `lower` filter agrees.


def version_outcome(version_target: Any, version_after: Any) -> str:
    """Return the outcome token of the version check of one device.

    Why:
        FR-051 states the rule. The run records the version that a device
        reports after the upgrade, and nothing compared that reading against
        the version that the operator asked for. A device that stayed on its
        old firmware therefore read as a success.

        A device that reports no version is not a mismatch. It is still
        settling, so it holds a token of its own. A row that carries no
        requested version proves nothing either, which follows the rule of
        ``uptime_decreased``: an absent value is no evidence.

    Args:
        version_target: The version that the operator picked for this device.
        version_after: The version that the device reports now.

    Returns:
        One of ``version_match``, ``version_mismatch``, or ``version_pending``.
    """
    requested = normalize_version(version_target)  # The choice of the operator, in the shared form.
    reported = normalize_version(version_after)  # The reading of the device, in the shared form.
    if not reported or not requested:  # An absent value on either side proves nothing at all.
        return OUTCOME_VERSION_PENDING  # The device is still settling, so the page shows no alarm.
    if reported == requested:  # The device returned on the firmware that the run requested.
        return OUTCOME_VERSION_MATCH  # The upgrade did what the operator asked.
    return OUTCOME_VERSION_MISMATCH  # The device runs firmware that nobody requested.


def version_matches(version_target: Any, version_after: Any) -> bool:
    """Report whether one device returned on the version that the run requested.

    Why:
        A caller that needs one boolean must not repeat the token names, and
        must not build a second comparison rule. This reader asks
        ``version_outcome``, so the two answers can never drift apart. An
        absent reading answers False, because no reading proves no match.

    Args:
        version_target: The version that the operator picked for this device.
        version_after: The version that the device reports now.

    Returns:
        True only when both values are present and equal after normalization.
    """
    return version_outcome(version_target, version_after) == OUTCOME_VERSION_MATCH  # One rule, one place.


def target_version_outcome(entry: Mapping[str, Any]) -> str:
    """Return the version outcome of one target row of the run record.

    Why:
        The run record keeps the requested version and the reported version on
        the same target row, so the check needs no second lookup and no extra
        cloud call. The reader takes a plain mapping, because the run record
        holds plain mappings for the document store.

    Args:
        entry: One entry of the ``targets`` list of a run record.

    Returns:
        One of ``version_match``, ``version_mismatch``, or ``version_pending``.
    """
    return version_outcome(entry.get(FIELD_VERSION_TARGET), entry.get(FIELD_VERSION_AFTER))  # Both on the row.


def reading_uptime(value: Any) -> int | None:
    """Return the uptime of one record as a whole number, or None.

    Why:
        The vendor marks ``uptime`` nullable, and a text value arrives from
        some records. Both mean "no reading". This reader keeps them apart
        from zero, because zero is a real value that would look like a fresh
        reboot.

    Args:
        value: The raw uptime value from a statistics record.

    Returns:
        The uptime in seconds, or None when the record reported no number.
    """
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):  # A text value means "not reported", never zero.
        return None


def reading_last_seen(value: Any) -> int | None:
    """Return the last seen moment of one record as a whole number, or None.

    Why:
        The vendor marks ``last_seen`` nullable and calls it a timestamp in
        epoch seconds (``documentation/api/orgs/GET_orgs_org_id_stats_devices``
        ``.md:1083``). The gate dates every record with this value, so a record
        that carries no value must stay apart from a record that reports zero.

    Args:
        value: The raw ``last_seen`` value from a statistics record.

    Returns:
        The moment in epoch seconds, or None when the record reported none.
    """
    return reading_uptime(value)  # Both fields hold a whole number of seconds or hold no reading at all.


def reading_is_stale(last_seen_before: int | None, last_seen_now: int | None) -> bool:
    """Report whether one statistics record repeats a snapshot already read.

    Why:
        FR-046 at ``spec.md:525`` asks the gate to ignore a statistics record
        that is older than the upgrade. The cloud can serve a copy that it
        cached before the reboot, and that copy holds the old uptime and the
        old version together.

        Both values of this test come from the ``last_seen`` field of the
        cloud for the same device, so the test needs no shared clock. FR-045
        at ``spec.md:523`` forbids a comparison between a cloud timestamp and
        the local clock.

        A null on either side answers False. An absent value is no evidence,
        which is the rule of ``uptime_decreased``. A gate that read a null as
        stale would drop every record of that device and would wait to the
        phase deadline.

    Args:
        last_seen_before: The highest moment that the gate already read for
            this device, or None before the first record that carried one.
        last_seen_now: The moment of the current record, or None.

    Returns:
        True only when two real values show that the record is not newer.
    """
    if last_seen_before is None or last_seen_now is None:  # A null proves nothing about the age of the record.
        return False  # The caller uses the record, because an absent value is no evidence.
    return last_seen_now <= last_seen_before  # An equal moment repeats the snapshot that the gate already read.


def last_seen_advanced(last_seen_before: int | None, last_seen_now: int | None) -> bool:
    """Report whether the cloud heard from one device after the pre-check.

    Why:
        This is the absolute anchor. The uptime of a device is nullable, so a
        device whose uptime never arrives can never satisfy the fall test, and
        it waits to the phase deadline. The cloud raises ``last_seen`` each
        time it hears from the device, so a later moment proves the return.
        Both values are cloud moments for the same device, so the test reads
        no local clock, which FR-045 at ``spec.md:523`` requires. A null on
        either side answers False, because an absent value is no evidence.

    Args:
        last_seen_before: The moment that the pre-check read, or None.
        last_seen_now: The moment of the current record, or None.

    Returns:
        True only when two real values show a later moment.
    """
    if last_seen_before is None or last_seen_now is None:  # A null is no proof that the device returned.
        return False  # The caller keeps the uptime rule and waits for the next round.
    return last_seen_now > last_seen_before  # The cloud heard from the device after the pre-check snapshot.


def reading_from_record(record: Mapping[str, Any]) -> GateReading | None:
    """Build one gate reading from one statistics record.

    Why:
        The gate joins its readings to the run targets on the address, so the
        address must follow the one rule that the capture package holds. A
        record with no usable address matches every other malformed record,
        so this builder drops it.

        The builder also keeps the ``last_seen`` value of the record, because
        FR-046 dates every record against the cloud and never against the
        local clock.

    Args:
        record: One record from the device statistics call.

    Returns:
        The reading, or None when the record carries no usable address.
    """
    mac = normalize_device_mac(record.get("mac"))
    if not mac:
        return None
    version = record.get("version")
    text = "" if version is None else str(version)
    uptime = reading_uptime(record.get("uptime"))  # A null stays a null, because zero would look like a fresh boot.
    last_seen = reading_last_seen(record.get("last_seen"))  # The moment that dates this record on the cloud clock.
    return GateReading(mac=mac, version=text, uptime=uptime, last_seen=last_seen)  # One reading for the gate rules.


def _screen_reading(progress: GateProgress, reading: GateReading | None) -> tuple[GateProgress, GateReading | None]:
    """Drop one statistics record that repeats a snapshot the gate already read.

    Why:
        FR-046 at ``spec.md:525`` asks the gate to ignore a record that is
        older than the upgrade. The gate holds the highest ``last_seen`` of
        each device, so it dates every later record against the cloud alone
        and never against the local clock.

        A record that carries no ``last_seen`` passes and leaves the mark
        alone. The gate cannot date that record, and an absent value is no
        evidence. A gate that dropped such a record would stall the device
        until the phase deadline on every round.

    Args:
        progress: The signals recorded so far.
        reading: The statistics reading of this round, or None.

    Returns:
        The progress with the mark raised, and the reading that the gate uses.
        That reading is None when this round holds no usable record.
    """
    if reading is None:  # The poll returned no record for this device this round.
        return progress, None
    if reading_is_stale(progress.last_seen_at, reading.last_seen):  # The cloud repeated an earlier snapshot.
        logger.debug("Upgrade gate ignored a stale statistics record for device %s", reading.mac)
        return progress, None
    if reading.last_seen is None:  # No moment to record, so the mark stays where it is.
        return progress, reading
    return replace(progress, last_seen_at=reading.last_seen), reading  # A newer record raises the mark.


def _warn_version_only(mac: str) -> None:
    """Name the device that settled on the firmware version change alone.

    Why:
        The gate cannot prove a fall against an uptime that nobody read, so
        that device uses the weakest signal of the three. An operator who
        reads the log after a run must find which device used it.

    Args:
        mac: The device address.
    """
    logger.warning(
        "Upgrade gate holds no earlier uptime for device %s, so it settled on the version change alone",
        mac,
    )


def _anchor_proves_reboot(target: GateTarget, reading: GateReading) -> bool:
    """Report whether the cloud moment proves the reboot of one device.

    Why:
        The fall test proved nothing here, because one of the two uptime
        readings is missing, and the device would wait to the phase deadline.
        The cloud raises ``last_seen`` each time it hears from the device, so a
        moment later than the pre-check moment proves that the device returned.
        The log line names the device, because an operator must know which proof
        the run used.

    Args:
        target: The state of the device before the upgrade.
        reading: The statistics reading of this round.

    Returns:
        True when the cloud moment rose above the pre-check moment.
    """
    if not last_seen_advanced(target.last_seen_before, reading.last_seen):  # A null or an older moment is no proof.
        return False  # The device waits for a reading that carries an uptime or a later moment.
    logger.info("Upgrade gate proved the reboot of device %s from its cloud moment", target.mac)  # The anchor path.
    return True  # The absolute anchor holds, so the reboot is proven with no uptime.


def _reboot_is_proven(target: GateTarget, reading: GateReading) -> bool:
    """Report whether one reading proves that the device rebooted.

    Why:
        The firmware version half already holds here, so this rule answers the
        uptime half alone. Three paths can prove it, and the rule tries them
        from the strongest to the weakest.

        The fall of two real uptime readings is the strongest. The cloud moment
        is next, and it runs whenever the fall test lacked a reading on either
        side. The version change alone is the weakest, and it runs last, so a
        device with no earlier uptime still gets the cloud moment first. T141
        forbids a settle on a version change that no other signal supports, and
        this order keeps that path as the final resort of a device that the
        pre-check never measured.

        A real pair of uptime readings that did not fall is evidence against a
        reboot, and it keeps its verdict against both weaker paths.

    Args:
        target: The state of the device before the upgrade.
        reading: The statistics reading of this round.

    Returns:
        True when one of the three paths proves the reboot.
    """
    if uptime_decreased(target.uptime_before, reading.uptime):  # Two real readings show the fall.
        return True  # The strongest path, and the one that every healthy device meets first.
    if target.uptime_before is not None and reading.uptime is not None:  # A real pair that did not fall.
        return False  # Neither weaker path may overrule two real readings.
    if _anchor_proves_reboot(target, reading):  # One uptime is missing, so try the absolute anchor.
        return True  # The cloud heard from the device after the pre-check moment.
    if target.uptime_before is None:  # No earlier uptime and no later moment, so nothing else can prove it.
        _warn_version_only(target.mac)  # Name the device that uses the weakest signal.
        return True  # The version-only path, which this gate held before the anchor arrived.
    return False  # A real earlier uptime and no current one, so wait for a reading that carries it.


def _note_reboot(target: GateTarget, progress: GateProgress, reading: GateReading | None, now: float) -> GateProgress:
    """Record the second signal when one reading proves the reboot.

    Why:
        The second signal needs both halves in one reading. An uptime that
        fell alone can follow a counter reset, and a version that changed
        alone can follow a record that the cloud updated before the reboot.
        The version half runs here, and ``_reboot_is_proven`` holds the three
        paths that can prove the second half.

    Args:
        target: The state of the device before the upgrade.
        progress: The signals recorded so far.
        reading: The statistics reading of this round, or None.
        now: The clock reading of this round.

    Returns:
        The progress with the reboot recorded, or the progress unchanged.
    """
    if reading is None or not version_changed(target.version_before, reading.version):  # No record, or no new version.
        return progress
    if not _reboot_is_proven(target, reading):  # No path proved the reboot, so wait for the next round.
        return progress
    logger.info("Upgrade gate saw device %s reboot to version %s", target.mac, reading.version)
    return replace(progress, reboot_at=now, version_after=reading.version)


def _note_settled(target: GateTarget, progress: GateProgress, now: float) -> GateProgress:
    """Record the third signal when the extra wait finished.

    Args:
        target: The state of the device before the upgrade.
        progress: The signals recorded so far.
        now: The clock reading of this round.

    Returns:
        The progress with the settle time recorded, or unchanged.
    """
    if progress.reboot_at is None:
        return progress
    if now - progress.reboot_at < settle_wait_seconds(target.device_type):
        return progress
    logger.info("Upgrade gate settled device %s", target.mac)
    return replace(progress, settled_at=now)


def advance(target: GateTarget, progress: GateProgress, signals: GateSignals, now: float) -> GateProgress:
    """Apply one round of observations to the progress of one device.

    Why:
        A decision function that takes readings and returns a verdict is far
        easier to test than one that sleeps. This function holds every gate
        rule, it never calls the cloud, and it never waits. The caller owns
        the clock and the poll cadence.

        The order of the signals is fixed. The reconnect event opens the
        gate, the statistics prove the reboot, and the wait follows the
        proof.

        A stale statistics record never reaches the reboot rule. The screen
        runs first and drops a record that repeats a snapshot the gate read
        before, so a copy that the cloud cached before the reboot can neither
        settle a device nor delay one.

    Args:
        target: The state of the device before the upgrade.
        progress: The signals recorded so far.
        signals: The observations of this round.
        now: The clock reading of this round.

    Returns:
        The progress after this round. The same record when nothing moved.
    """
    if progress.settled_at is not None:
        return progress
    seen = replace(progress, reconnected=True) if signals.reconnected else progress
    if not seen.reconnected:
        return seen
    seen, fresh = _screen_reading(seen, signals.reading)  # FR-046 drops a record that repeats an old snapshot.
    if seen.reboot_at is None:
        return _note_reboot(target, seen, fresh, now)
    return _note_settled(target, seen, now)


def is_settled(progress: GateProgress) -> bool:
    """Report whether one device passed all three signals.

    Args:
        progress: The signals recorded so far.

    Returns:
        True after the extra wait finished.
    """
    return progress.settled_at is not None


def _partial_reason(reason: str, http_status: int) -> dict[str, Any]:
    """Build one entry of ``partial_reasons`` for the gate section.

    Why:
        Rule 5 at ``data-model.md:195`` states the three fields of an entry.
        One builder keeps every entry of this module the same shape.

    Args:
        reason: The machine name of the fault.
        http_status: The HTTP status of the answer, or zero.

    Returns:
        One partial reason entry.
    """
    return {"section": SECTION_GATE_STATISTICS, "reason": reason, "http_status": http_status}


def _readings_of(records: Sequence[Mapping[str, Any]]) -> dict[str, GateReading]:
    """Turn the records of one poll into a map from address to reading.

    Args:
        records: The records that the statistics call returned.

    Returns:
        One reading for each record that carries a usable address.
    """
    readings: dict[str, GateReading] = {}
    for record in records:
        reading = reading_from_record(record)
        if reading is not None:
            readings[reading.mac] = reading
    return readings


def read_fleet_statistics(
    session: Any,
    org_id: str,
    site_id: str | None = None,
    page_limit: int | None = None,
) -> FleetRead:
    """Read the statistics of the whole fleet with one call.

    Why:
        The gate polls every 20 seconds while a run settles. One call for the
        whole fleet costs 180 calls each hour whatever the device count. A
        per-device poll would cost 180 calls each hour for each device and
        would pass the quota at ``src/utils/rate_limiting.py:56`` after 27
        devices. This function therefore takes no device address.

        The call always sends the type, because the cloud answers with
        access points only when the type is absent and reports no error.

    Args:
        session: The cloud session.
        org_id: The organization that owns the devices.
        site_id: The site to read. None reads every site of the organization.
        page_limit: The page size. None reads the shared page size.

    Returns:
        The readings and the reasons of one poll.
    """
    limit = page_limit if page_limit is not None else resolve_page_limit()
    call = partial(
        mistapi.api.v1.orgs.stats.listOrgDevicesStats,
        session,
        org_id,
        type=STATISTICS_TYPE,
        site_id=site_id,
        fields=STATISTICS_FIELDS,
        limit=limit,
    )
    try:
        response = call()
        records = mistapi.get_all(mist_session=session, response=response)
    except Exception as error:  # A failed poll marks the round partial and never stops the run.
        logger.warning("Upgrade gate failed the fleet statistics read: %s", type(error).__name__)
        return FleetRead({}, [_partial_reason(REASON_READ_FAILED, HTTP_STATUS_NONE)])
    rows = [dict(record) for record in records]
    logger.debug("Upgrade gate read %s device statistics records", len(rows))
    return FleetRead(_readings_of(rows), guard_page_count(SECTION_GATE_STATISTICS, len(rows), response))


def reboot_hint(status: Mapping[str, Any]) -> frozenset[str]:
    """Return the addresses that the upgrade job reports as mid-reboot.

    Why:
        The upgrade job carries ``targets.reboot_in_progress``, so one call
        tells the gate which devices are rebooting. The gate builds nothing
        on the statistics ``status`` field, which the vendor schema leaves
        with no description and no enumeration.

        The hint is an aid, never a signal. A device still needs the three
        signals of ``advance`` before it settles.

    Args:
        status: The record that ``read_upgrade_status`` returned.

    Returns:
        The addresses in lower case with no separator. Empty when the job
        reports none.
    """
    values = status.get("reboot_in_progress")
    if values is None:
        targets = status.get("targets")
        values = targets.get("reboot_in_progress") if isinstance(targets, Mapping) else None
    if isinstance(values, str) or not isinstance(values, Sequence):
        return frozenset()
    return frozenset(mac for mac in (normalize_device_mac(value) for value in values) if mac)


def read_reboot_hint(
    session: Any,
    scope: str,
    identifier: str,
    upgrade_id: str,
    family: GatewayFamily = GatewayFamily.JUNOS,
) -> frozenset[str]:
    """Read the reboot hint of one upgrade job with one call.

    Args:
        session: The cloud session.
        scope: ``site`` or ``org``.
        identifier: The site identifier or the organization identifier.
        upgrade_id: The upgrade job that the cloud returned.
        family: The gateway family that selects the endpoint.

    Returns:
        The addresses that the job reports as mid-reboot.
    """
    status = read_upgrade_status(session, scope, identifier, upgrade_id, family)
    return reboot_hint(status)


class SettleGate:
    """The settle gate of one run, with its clock injected.

    Why:
        The gate rules are pure, yet a caller still needs a clock. Holding
        the clock behind a callable lets a test drive time forward with a
        counter and prove the 60-second wait and the 120-second wait without
        sleeping. The default reads the wall clock in epoch seconds, which
        matches the timestamps of the cloud records and lets the driver write
        an ISO stamp from the same value.
    """

    def __init__(self, clock: Callable[[], float] | None = None) -> None:
        """Build one gate.

        Args:
            clock: A callable that returns the current time in seconds. None
                reads the wall clock.
        """
        self._clock: Callable[[], float] = time.time if clock is None else clock

    def now(self) -> float:
        """Return the current clock reading.

        Returns:
            The time in seconds from the injected clock.
        """
        return self._clock()

    def observe(self, target: GateTarget, progress: GateProgress, signals: GateSignals) -> GateProgress:
        """Apply one round of observations with the clock of this gate.

        Args:
            target: The state of the device before the upgrade.
            progress: The signals recorded so far.
            signals: The observations of this round.

        Returns:
            The progress after this round.
        """
        return advance(target, progress, signals, self._clock())


__all__ = [
    "ACCESS_POINT_EXTRA_WAIT_SECONDS",
    "DEVICE_TYPE_ACCESS_POINT",
    "FIELD_VERSION_AFTER",
    "FIELD_VERSION_OUTCOME",
    "FIELD_VERSION_TARGET",
    "HOURLY_CALL_QUOTA",
    "MAX_CALLS_PER_HOUR",
    "OUTCOME_VERSION_MATCH",
    "OUTCOME_VERSION_MISMATCH",
    "OUTCOME_VERSION_PENDING",
    "POLL_INTERVAL_SECONDS",
    "SECONDS_PER_HOUR",
    "SECTION_GATE_STATISTICS",
    "SETTLE_WAIT_SECONDS",
    "STATISTICS_FIELDS",
    "STATISTICS_TYPE",
    "FleetRead",
    "GateProgress",
    "GateReading",
    "GateSignals",
    "GateTarget",
    "SettleGate",
    "advance",
    "is_settled",
    "last_seen_advanced",
    "normalize_version",
    "polls_per_hour",
    "read_fleet_statistics",
    "read_reboot_hint",
    "reading_from_record",
    "reading_is_stale",
    "reading_last_seen",
    "reading_uptime",
    "reboot_hint",
    "settle_wait_seconds",
    "target_version_outcome",
    "uptime_decreased",
    "version_changed",
    "version_matches",
    "version_outcome",
]
