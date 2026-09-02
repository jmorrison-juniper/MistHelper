"""The device comparison between two upgrade captures.

Why:
    An operator reads a comparison to answer one question. Did the upgrade
    change anything that the operator did not ask for? A device row therefore
    reports the exact fields that differ, with the value before and the value
    after. It never reports a single true or false flag.

    The module excludes ``uptime`` from the change test. A reboot resets the
    uptime of every upgraded device, so an uptime test marks the whole site
    changed and hides the real differences. The gate reads ``uptime``
    separately, so nothing is lost.

    The module reads the section digests first. Two captures of a quiet site
    carry the same device digest, and the comparison then skips the whole
    device section and names it in ``skipped_sections``. This short circuit is
    the reason a large site renders in seconds. Never compare a section that
    the digests already prove equal.

    A skipped section holds no row, but it still holds devices. The comparison
    therefore counts the devices of the skipped section and reports the count
    in ``proved_unchanged``. The digest proves every one of those devices
    unchanged. Without that count the page shows a bare zero, and an operator
    reads the zero as an empty site rather than as a quiet one.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# The four device outcomes of data-model.md section 7.2.
OUTCOME_UNCHANGED = "unchanged"
OUTCOME_CHANGED = "changed"
OUTCOME_ADDED = "added"
OUTCOME_REMOVED = "removed"

DEVICE_OUTCOMES = (OUTCOME_UNCHANGED, OUTCOME_CHANGED, OUTCOME_ADDED, OUTCOME_REMOVED)

FIELD_VERSION = "version"

# The compared fields of data-model.md section 7.2, in report order.
DEVICE_FIELDS = ("status", FIELD_VERSION, "model", "name", "ip", "vc_role", "num_members")

# WHY: A reboot resets the uptime of every upgraded device. A comparison that
# reads uptime marks each device changed and buries the real differences.
FIELD_UPTIME = "uptime"
EXCLUDED_DEVICE_FIELDS = (FIELD_UPTIME,)

# The digest section names that the capture assembly writes.
SECTION_DEVICES = "devices"
SECTION_EXTRAS = "extras"
SECTION_WHOLE = "whole"

DIGESTS_KEY = "digests"
DEVICE_INDEX_KEY = "device_index"
NAME_KEY = "name"

# WHY: One absent field and one empty field mean the same thing to an operator.
# A shared stand in value keeps an absent field out of the change list.
ABSENT_VALUE = ""


# ---------------------------------------------------------------------------
# View records
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class FieldChange:
    """One field of one device with the value before and the value after.

    Why:
        The operator needs the two values, not the word ``changed``. A record
        that carries both values serves the table, the export, and the log. All
        three then report the same pair without a second read of the captures.

    Attributes:
        field: The name of the compared field.
        before: The value in the pre-check capture.
        after: The value in the post-check capture.
    """

    field: str
    before: Any
    after: Any

    def to_dict(self) -> dict[str, Any]:
        """Return the change as a plain dictionary.

        Why:
            The route lane serializes the comparison to JSON, and the export
            writes the same three values. One converter serves both.

        Returns:
            A dictionary with ``field``, ``before``, and ``after``.
        """
        return {"field": self.field, "before": self.before, "after": self.after}


@dataclass(frozen=True, slots=True)
class DeviceDelta:
    """One device of the union of the two device index maps.

    Why:
        The comparison reports every device once, whichever capture holds it.
        The outcome names the reason the device is in the report, and the
        change list holds the detail for a ``changed`` device only.

    Attributes:
        mac: The device address, in lower case with no separator.
        outcome: One value of ``DEVICE_OUTCOMES``.
        name: The device name, from the later capture that holds the device.
        changes: Each differing field. Empty for every outcome but ``changed``.
    """

    mac: str
    outcome: str
    name: str = ""
    changes: tuple[FieldChange, ...] = ()

    @property
    def version_changed(self) -> bool:
        """Return whether the firmware version differs.

        Why:
            The statistics roll-up counts the devices that took new firmware.
            The count reads this one property, so the field name lives in one
            place.

        Returns:
            True when the change list holds the ``version`` field.
        """
        return any(change.field == FIELD_VERSION for change in self.changes)

    def to_dict(self) -> dict[str, Any]:
        """Return the device difference as a plain dictionary.

        Why:
            The comparison endpoint of ``contracts/http-api.md`` returns
            ``device_deltas`` as JSON. The same shape feeds the export.

        Returns:
            A dictionary with ``mac``, ``outcome``, ``name``, and ``changes``.
        """
        return {
            "mac": self.mac,
            "outcome": self.outcome,
            "name": self.name,
            "changes": [change.to_dict() for change in self.changes],
        }


@dataclass(frozen=True, slots=True)
class DeviceComparison:
    """The device result of one comparison.

    Why:
        The skipped section list travels with the deltas. A caller that reads
        an empty delta list must tell an equal site apart from a site that the
        digest short circuit never compared.

        The proved count travels beside them. A digest match proves every
        device of the section unchanged, so the count states how many devices
        the match covered. A caller that reports a bare zero instead tells the
        operator that the site is empty, which is a different fact.

    Attributes:
        deltas: One entry for each device, sorted by address.
        skipped_sections: Each section whose digest matched.
        proved_unchanged: The devices that a matching digest proved unchanged.
            Zero when the comparison read the rows itself.
    """

    deltas: tuple[DeviceDelta, ...] = ()
    skipped_sections: tuple[str, ...] = ()
    proved_unchanged: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Return the device result as a plain dictionary.

        Why:
            The route lane merges this dictionary into the comparison body,
            so the two key names match the contract exactly. The proved count
            stays out of the dictionary, because the contract names two keys
            here and reports every count in the statistics object.

        Returns:
            A dictionary with ``device_deltas`` and ``skipped_sections``.
        """
        return {
            "device_deltas": [delta.to_dict() for delta in self.deltas],
            "skipped_sections": list(self.skipped_sections),
        }


# ---------------------------------------------------------------------------
# The digest short circuit
# ---------------------------------------------------------------------------


def section_digest(capture: Mapping[str, Any], section: str) -> str:
    """Return the digest of one section of one capture.

    Why:
        A capture at tier 2 carries no ``extras`` digest, and an older record
        may carry no digest map at all. A reader that returns an empty string
        for every gap keeps the callers free of type tests.

    Args:
        capture: One capture document.
        section: The section name, such as ``devices``.

    Returns:
        The digest text, or an empty string when the capture holds none.
    """
    digests = capture.get(DIGESTS_KEY)
    if not isinstance(digests, Mapping):
        return ""
    value = digests.get(section)
    return value if isinstance(value, str) else ""


def digest_matches(before: Mapping[str, Any], after: Mapping[str, Any], section: str) -> bool:
    """Return whether one section of the two captures holds the same digest.

    Why:
        A matching digest proves the section is equal, so the comparison can
        skip it. An absent digest proves nothing, so this function refuses to
        call an absent digest a match. A wrong skip hides a real difference.

    Args:
        before: The pre-check capture.
        after: The post-check capture.
        section: The section name to test.

    Returns:
        True only when both captures hold the same non-empty digest.
    """
    before_digest = section_digest(before, section)
    after_digest = section_digest(after, section)
    if not before_digest or not after_digest:
        return False
    return before_digest == after_digest


def matched_sections(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    sections: Iterable[str],
) -> tuple[str, ...]:
    """Return each named section whose digest matched.

    Why:
        The client comparison and the device comparison each skip their own
        sections. One helper builds the ``skipped_sections`` list of the
        comparison body, so the two lanes report the same way.

    Args:
        before: The pre-check capture.
        after: The post-check capture.
        sections: The section names to test, in report order.

    Returns:
        The matching section names, in the order given.
    """
    return tuple(section for section in sections if digest_matches(before, after, section))


# ---------------------------------------------------------------------------
# The device comparison
# ---------------------------------------------------------------------------


def _device_index(capture: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    """Return the device index of one capture, with every bad row dropped.

    Why:
        A capture that failed part way carries a partial document. The
        comparison must report the devices it does hold and must not raise on
        a row of the wrong type.

    Args:
        capture: One capture document.

    Returns:
        The device index, keyed by address.
    """
    index = capture.get(DEVICE_INDEX_KEY)
    if not isinstance(index, Mapping):
        return {}
    return {str(mac): row for mac, row in index.items() if isinstance(row, Mapping)}


def _field_value(record: Mapping[str, Any], name: str) -> Any:
    """Return one compared field of one device row.

    Why:
        A capture drops an empty field, so the same device reads as ``None``
        in one capture and as an empty string in the other. Both become the
        same stand in value, and the device stays ``unchanged``.

    Args:
        record: One device index row.
        name: The field name.

    Returns:
        The field value, or the stand in value when the field is absent.
    """
    value = record.get(name)
    return ABSENT_VALUE if value is None else value


def _field_changes(before: Mapping[str, Any], after: Mapping[str, Any]) -> tuple[FieldChange, ...]:
    """Return each compared field that differs between two device rows.

    Why:
        The field list is fixed and excludes ``uptime``. This function walks the
        fixed list and never the keys of the rows. A new capture field
        therefore stays out of the change test until somebody adds it on
        purpose.

    Args:
        before: The device row of the pre-check capture.
        after: The device row of the post-check capture.

    Returns:
        One entry for each differing field, in ``DEVICE_FIELDS`` order.
    """
    changes: list[FieldChange] = []
    for name in DEVICE_FIELDS:
        old_value = _field_value(before, name)
        new_value = _field_value(after, name)
        if old_value != new_value:
            changes.append(FieldChange(field=name, before=old_value, after=new_value))
    return tuple(changes)


def _device_name(record: Mapping[str, Any] | None) -> str:
    """Return the name of one device row.

    Why:
        The table shows a name, because an operator does not read addresses.
        A row without a name still needs a row, so the reader returns an empty
        string rather than raising.

    Args:
        record: One device index row, or None.

    Returns:
        The device name, or an empty string.
    """
    if record is None:
        return ""
    name = record.get(NAME_KEY)
    return name if isinstance(name, str) else ""


def _compare_one_device(
    mac: str,
    before_row: Mapping[str, Any] | None,
    after_row: Mapping[str, Any] | None,
) -> DeviceDelta:
    """Return the difference record of one device.

    Why:
        The four outcomes come from the presence of the two rows and from the
        change list. Deciding all four in one place keeps the caller short and
        keeps the rule out of the loop.

    Args:
        mac: The device address.
        before_row: The row of the pre-check capture, or None.
        after_row: The row of the post-check capture, or None.

    Returns:
        One device difference record.
    """
    if before_row is None:
        return DeviceDelta(mac=mac, outcome=OUTCOME_ADDED, name=_device_name(after_row))
    if after_row is None:
        return DeviceDelta(mac=mac, outcome=OUTCOME_REMOVED, name=_device_name(before_row))
    changes = _field_changes(before_row, after_row)
    outcome = OUTCOME_CHANGED if changes else OUTCOME_UNCHANGED
    return DeviceDelta(mac=mac, outcome=outcome, name=_device_name(after_row), changes=changes)


def _proved_unchanged_count(before: Mapping[str, Any], after: Mapping[str, Any]) -> int:
    """Return how many devices a matching device digest proved unchanged.

    Why:
        A matching digest proves the two device sections equal, so every
        device in the section is unchanged. The comparison reads no row, so
        the count must come from the size of the section instead. A count of
        zero would read as an empty site, which is a different fact.

        The reader takes the larger of the two sizes. The digest proves the
        two sections equal, so the larger size is the true size. A stored
        document that lost a row then never lowers the count.

    Args:
        before: The pre-check capture.
        after: The post-check capture.

    Returns:
        The device count of the proved section.
    """
    before_total = len(_device_index(before))  # WHY: The same reader drops a bad row here and in the comparison.
    after_total = len(_device_index(after))  # WHY: The post-check size is the count the operator asked for.
    return max(before_total, after_total)  # WHY: A partial document must never lower a proved count.


def compare_devices(before: Mapping[str, Any], after: Mapping[str, Any]) -> DeviceComparison:
    """Compare the devices of two captures.

    Why:
        This is the device half of the comparison. The digest test runs first,
        because a matching digest proves the section equal and a large site
        then costs nothing. Only a real difference reaches the field test.

    Args:
        before: The pre-check capture.
        after: The post-check capture.

    Returns:
        The device differences, or an empty list with ``devices`` named in
        ``skipped_sections`` and the proved count beside it.
    """
    if digest_matches(before, after, SECTION_DEVICES):
        logger.info("Upgrade portal skipped the %s section, because the two digests match", SECTION_DEVICES)
        proved = _proved_unchanged_count(before, after)  # WHY: The count replaces the bare zero on the page.
        logger.debug("Upgrade portal proved %s devices unchanged in the %s section", proved, SECTION_DEVICES)
        return DeviceComparison(skipped_sections=(SECTION_DEVICES,), proved_unchanged=proved)
    before_index = _device_index(before)
    after_index = _device_index(after)
    addresses = sorted(set(before_index) | set(after_index))
    deltas = tuple(_compare_one_device(mac, before_index.get(mac), after_index.get(mac)) for mac in addresses)
    logger.info("Upgrade portal compared %s devices", len(deltas))
    return DeviceComparison(deltas=deltas)


def count_outcome(deltas: Iterable[DeviceDelta], outcome: str) -> int:
    """Return how many device records carry one outcome.

    Why:
        The statistics roll-up counts four outcomes the same way. One counter
        keeps the four counts in step and keeps the roll-up short.

    Args:
        deltas: The device difference records.
        outcome: One value of ``DEVICE_OUTCOMES``.

    Returns:
        The number of matching records.
    """
    return sum(1 for delta in deltas if delta.outcome == outcome)


def count_version_changes(deltas: Iterable[DeviceDelta]) -> int:
    """Return how many devices took a different firmware version.

    Why:
        The operator asks one question after an upgrade. How many devices
        really took the new firmware? The count reads the change list, so a
        device that changed only its address is never counted.

    Args:
        deltas: The device difference records.

    Returns:
        The number of devices whose version differs.
    """
    return sum(1 for delta in deltas if delta.version_changed)


__all__ = [
    "ABSENT_VALUE",
    "DEVICE_FIELDS",
    "DEVICE_INDEX_KEY",
    "DEVICE_OUTCOMES",
    "DIGESTS_KEY",
    "EXCLUDED_DEVICE_FIELDS",
    "FIELD_UPTIME",
    "FIELD_VERSION",
    "NAME_KEY",
    "OUTCOME_ADDED",
    "OUTCOME_CHANGED",
    "OUTCOME_REMOVED",
    "OUTCOME_UNCHANGED",
    "SECTION_DEVICES",
    "SECTION_EXTRAS",
    "SECTION_WHOLE",
    "DeviceComparison",
    "DeviceDelta",
    "FieldChange",
    "compare_devices",
    "count_outcome",
    "count_version_changes",
    "digest_matches",
    "matched_sections",
    "section_digest",
]
