"""The device reads of one upgrade capture.

Why:
    A capture must hold every physical device of a site, and two cloud calls
    hold the parts. The inventory names each device and each chassis member.
    The statistics hold the firmware version, the state, and the uptime. This
    module runs both reads and joins them into one flat map.

    Two cloud defaults make a quiet loss easy, so the module guards both. The
    statistics call answers with access points only when the caller omits the
    type, and the cloud reports no error. The page helper answers with an
    empty list when the response shape changes, and it raises nothing. Each
    guard turns a quiet loss into a partial reason that the operator reads.
"""

from __future__ import annotations

import importlib
import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import partial
from typing import Any

import mistapi

from src.upgrade_portal.capture.clients import normalize_mac

logger = logging.getLogger(__name__)

SECTION_INVENTORY = "devices_inventory"
SECTION_STATISTICS = "devices_statistics"

# The statistics call answers with access points only when the caller omits
# the type. The SDK adds the query parameter only when the value is present
# (.venv/Lib/site-packages/mistapi/api/v1/sites/stats.py:1070), so an omitted
# type sends nothing and the cloud applies its own default of "ap". Every read
# in this module sends this constant.
STATISTICS_TYPE = "all"

VC_ROLE_STANDALONE = "standalone"

REASON_READ_FAILED = "read_failed"
REASON_SHORT_READ = "page_count_mismatch"
REASON_UNKNOWN_SHAPE = "unexpected_response_shape"
REASON_TYPE_GAP = "device_type_gap"
# The SDK catches every HTTP fault and answers with a response object, so a
# refusal arrives here as a readable answer and never as a raised fault.
REASON_ERROR_STATUS = "cloud_error_status"

# A fault outside an HTTP answer carries no status, so the entry reports zero.
HTTP_STATUS_NONE = 0

# The HTTP range that counts as a read.
_STATUS_FLOOR = 200
_STATUS_CEILING = 300

MIN_PAGE_LIMIT = 1
MAX_PAGE_LIMIT = 1000
FALLBACK_PAGE_LIMIT = 1000

# A stack with no reported member count still holds one physical device.
DEFAULT_MEMBER_COUNT = 1


@dataclass(frozen=True, slots=True)
class DeviceRead:
    """The result of one device call group.

    Why:
        A capture must tell a whole read from a short read. A bare list cannot
        carry that difference, so the read returns the records and the reasons
        together. The assembly step copies the reasons into ``partial_reasons``
        and marks the capture partial.

    Attributes:
        section: The section name that each partial reason entry carries.
        records: The records that the cloud returned. Empty after a failure.
        partial_reasons: One entry for each fault. Empty after a whole read.
    """

    section: str
    records: list[dict[str, Any]]
    partial_reasons: list[dict[str, Any]]


def normalize_device_mac(value: Any) -> str:
    """Return the index key for one address value.

    Why:
        The whole capture package follows one address rule, and
        ``clients.normalize_mac`` holds it. This function delegates to that
        one rule instead of repeating it.

        A second copy of the rule would let the two modules drift. A drifted
        rule is silent. The inventory read and the statistics read would spell
        one address two ways. The join in ``_index_entry`` would then miss, and
        every chassis member would lose its firmware version, its state, and
        its role. The capture would still look complete.

        The delegation also makes a malformed address an empty key rather than
        a stray one. The caller drops a record that gets an empty key, because
        an empty key matches every other malformed record.

    Args:
        value: The address value from a cloud record.

    Returns:
        The 12 hexadecimal characters of the address in lower case. An empty
        string when the value is absent or is not an address.
    """
    return normalize_mac(value)


def _text(value: Any) -> str:
    """Return one index field as text.

    Args:
        value: The raw value from a cloud record.

    Returns:
        The value as text. An absent value returns an empty string.
    """
    return "" if value is None else str(value)


def _whole_number(value: Any) -> int:
    """Return one index field as a whole number.

    Why:
        The cloud sends a null value for a device that never reported. A null
        value must not stop the index build, so the reader answers with zero.

    Args:
        value: The raw value from a cloud record.

    Returns:
        The value as a whole number, or zero when the value is not a number.
    """
    try:
        return int(value)
    except (TypeError, ValueError):  # A null value and a text value both mean "not reported".
        return 0


def resolve_page_limit() -> int:
    """Return the page size that one cloud read asks for.

    Why:
        The repository holds one page size at ``MistHelper.py:1133``, and an
        operator tunes it with the ``MIST_PAGE_LIMIT`` variable. A hard coded
        size here would ignore that choice. ``MistHelper`` imports from
        ``src``, so a top level import would build a cycle. The late import
        repeats the idiom at ``src/api/api_core_fetch_utils.py:59``.

    Returns:
        A page size inside the range that the cloud accepts.
    """
    try:
        module = importlib.import_module("MistHelper")
        limit = int(module.DEFAULT_API_PAGE_LIMIT)
    except Exception as error:  # A missing constant must not stop a capture.
        logger.debug("Upgrade portal uses the fallback page size: %s", error)
        return FALLBACK_PAGE_LIMIT
    return max(MIN_PAGE_LIMIT, min(limit, MAX_PAGE_LIMIT))


def _partial_reason(section: str, reason: str, http_status: int) -> dict[str, Any]:
    """Build one entry of ``partial_reasons``.

    Why:
        Rule 5 at ``data-model.md:193`` states the three fields of an entry.
        One builder keeps every entry the same shape.

    Args:
        section: The section that lost data.
        reason: The machine name of the fault.
        http_status: The HTTP status of the answer, or zero.

    Returns:
        One partial reason entry.
    """
    return {"section": section, "reason": reason, "http_status": http_status}


def _payload(response: Any) -> Any:
    """Return the parsed body of one cloud answer.

    Args:
        response: The answer that the SDK built.

    Returns:
        The parsed body, or None when the answer holds no body.
    """
    return getattr(response, "data", None)


def _status_code(response: Any) -> int:
    """Return the HTTP status of one cloud answer.

    Args:
        response: The answer that the SDK built.

    Returns:
        The status, or zero when the answer reports none.
    """
    status = getattr(response, "status_code", None)
    return status if isinstance(status, int) else HTTP_STATUS_NONE


def _known_shape(response: Any) -> bool:
    """Report whether the page helper understands the answer body.

    Why:
        ``mistapi.get_all`` reads a list body and a body that holds
        ``results``. For every other body it returns an empty list, and it
        raises nothing (``.venv/Lib/site-packages/mistapi/__pagination.py:55``).
        A capture must name that case instead of storing zero devices.

    Args:
        response: The answer that the SDK built.

    Returns:
        True when the page helper can read the body.
    """
    payload = _payload(response)
    if isinstance(payload, list):
        return True
    return isinstance(payload, dict) and "results" in payload


def _reported_total(response: Any) -> int | None:
    """Return the record count that the cloud reported.

    Args:
        response: The answer that the SDK built.

    Returns:
        The reported count, or None when the answer reports none.
    """
    payload = _payload(response)
    if not isinstance(payload, dict):
        return None
    total = payload.get("total")
    return total if isinstance(total, int) else None


def _status_reason(status: int) -> str | None:
    """Return the reason that one HTTP status carries, or None after a read.

    Why:
        The SDK catches every HTTP fault and answers with a response object
        (``.venv/Lib/site-packages/mistapi/__api_request.py:228-258``). A
        refusal therefore never reaches an ``except`` block. It arrives here
        with an error body that the page helper cannot read, and the shape
        test alone would name it an unexpected shape. That word tells an
        operator the SDK contract changed, when the true cause is a refused
        call or a lost connection.

    Args:
        status: The HTTP status of the answer, or zero when it holds none.

    Returns:
        The reason word, or None when the status counts as a read.
    """
    if status == HTTP_STATUS_NONE:  # The SDK swallowed a connection fault and built an answer with no status.
        return REASON_READ_FAILED
    if not _STATUS_FLOOR <= status < _STATUS_CEILING:
        return REASON_ERROR_STATUS
    return None


def guard_page_count(section: str, collected: int, response: Any) -> list[dict[str, Any]]:
    """Compare the collected count against the count that the cloud reported.

    Why:
        ``mistapi.get_all`` returns an empty list for an answer shape that it
        does not know, and it raises nothing. A capture would then store zero
        devices and look complete. This guard reads the status, the answer
        shape, and the reported total, so a refusal and a short read each
        become a partial reason that names its own cause.

    Args:
        section: The section name for a partial reason entry.
        collected: The number of records that the page helper returned.
        response: The answer that the SDK built.

    Returns:
        One partial reason entry, or an empty list after a whole read.
    """
    status = _status_code(response)
    status_reason = _status_reason(status)
    if status_reason is not None:
        logger.warning("Upgrade portal read no records for section %s. The cloud answered %s", section, status)
        return [_partial_reason(section, status_reason, status)]
    if not _known_shape(response):
        logger.warning("Upgrade portal read an unknown shape for section %s, status %s", section, status)
        return [_partial_reason(section, REASON_UNKNOWN_SHAPE, status)]
    total = _reported_total(response)
    if total is None or collected == total:
        return []
    logger.warning("Upgrade portal read %s of %s records for section %s", collected, total, section)
    return [_partial_reason(section, REASON_SHORT_READ, status)]


def _read_group(session: Any, section: str, response_factory: Any) -> DeviceRead:
    """Run one cloud read and turn a fault into a partial reason.

    Why:
        One failed call group must not lose the whole capture. The portal
        records the fault and keeps every other group, because a partial
        record still helps an operator.

    Args:
        session: The cloud session.
        section: The section name for a partial reason entry.
        response_factory: A callable that runs the first page of the read.

    Returns:
        The records and the reasons of one call group.
    """
    try:
        response = response_factory()
        records = mistapi.get_all(mist_session=session, response=response)
    except Exception as error:  # A cloud fault marks one section partial and never stops the capture.
        logger.warning("Upgrade portal failed the %s read: %s", section, error)
        return DeviceRead(section, [], [_partial_reason(section, REASON_READ_FAILED, HTTP_STATUS_NONE)])
    logger.debug("Upgrade portal read %s records for section %s", len(records), section)
    rows = [dict(record) for record in records]
    return DeviceRead(section, rows, guard_page_count(section, len(rows), response))


def read_inventory(session: Any, org_id: str, site_id: str, page_limit: int | None = None) -> DeviceRead:
    """Read every physical device of one site from the inventory.

    Why:
        Decision D11 splits the two views of a stack. An upgrade targets the
        logical device, so the upgrade path omits the virtual chassis
        parameter. A capture must hold every physical member, so this path
        sends ``vc=True`` and each chassis member arrives as its own record.

    Args:
        session: The cloud session.
        org_id: The organization that owns the site.
        site_id: The site to read.
        page_limit: The page size. None reads the shared page size.

    Returns:
        The inventory records and the reasons of the read.
    """
    limit = page_limit if page_limit is not None else resolve_page_limit()
    logger.info("Upgrade portal reads the inventory of site %s with the chassis members", site_id)
    call = partial(
        mistapi.api.v1.orgs.inventory.getOrgInventory,
        session,
        org_id,
        site_id=site_id,
        vc=True,
        limit=limit,
    )
    return _read_group(session, SECTION_INVENTORY, call)


def read_device_statistics(session: Any, site_id: str, page_limit: int | None = None) -> DeviceRead:
    """Read the statistics of every device of one site.

    Why:
        The call answers with access points only when the caller omits the
        type, and the cloud reports no error. A capture would then hold no
        switch and no gateway, and nobody would see the loss. This function
        always sends ``STATISTICS_TYPE``.

    Args:
        session: The cloud session.
        site_id: The site to read.
        page_limit: The page size. None reads the shared page size.

    Returns:
        The statistics records and the reasons of the read.
    """
    limit = page_limit if page_limit is not None else resolve_page_limit()
    logger.info("Upgrade portal reads the device statistics of site %s with type %s", site_id, STATISTICS_TYPE)
    call = partial(
        mistapi.api.v1.sites.stats.listSiteDevicesStats,
        session,
        site_id,
        type=STATISTICS_TYPE,
        limit=limit,
    )
    return _read_group(session, SECTION_STATISTICS, call)


def _types_of(records: Sequence[Mapping[str, Any]]) -> set[str]:
    """Return every device type inside one record list.

    Args:
        records: The records of one read.

    Returns:
        The set of device types. An absent type joins no set.
    """
    return {_text(record.get("type")) for record in records if record.get("type")}


def guard_statistics_coverage(
    inventory: Sequence[Mapping[str, Any]], statistics: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    """Report a device type that the statistics read lost.

    Why:
        A capture that holds only access points means the statistics read lost
        the type parameter. The cloud reports no error for that loss, so a
        test alone cannot protect a running capture. The inventory carries
        every type, so a type that the inventory holds and the statistics miss
        proves the loss.

    Args:
        inventory: The inventory records of the site.
        statistics: The statistics records of the site.

    Returns:
        One partial reason entry, or an empty list when both reads agree.
    """
    missing = sorted(_types_of(inventory) - _types_of(statistics))
    if not missing:
        return []
    logger.warning("Upgrade portal read no device statistics for the types %s", ",".join(missing))
    return [_partial_reason(SECTION_STATISTICS, REASON_TYPE_GAP, HTTP_STATUS_NONE)]


def _chassis_view(statistics: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    """Map each device address to the whole device statistics record.

    Why:
        The statistics answer holds one record for a whole stack, under the
        address of the stack. The index needs that record for every member, so
        the join needs the record by address.

    Args:
        statistics: The statistics records of the site.

    Returns:
        A map from a device address to one statistics record.
    """
    view: dict[str, dict[str, Any]] = {}
    for record in statistics:
        key = normalize_device_mac(record.get("mac"))
        if key:
            view[key] = dict(record)
    return view


def _member_view(statistics: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    """Map each chassis member address to its own module statistics.

    Why:
        A stack reports one record for the whole chassis, and the per member
        values live inside ``module_stat``. The member role and the member
        firmware version live there and nowhere else.

    Args:
        statistics: The statistics records of the site.

    Returns:
        A map from a member address to one module statistics record.
    """
    members: dict[str, dict[str, Any]] = {}
    for record in statistics:
        for module in record.get("module_stat") or ():
            key = normalize_device_mac(module.get("mac"))
            if key:
                members[key] = dict(module)
    return members


def _identity_of(record: Mapping[str, Any]) -> dict[str, Any]:
    """Return the five index fields that the inventory owns.

    Args:
        record: One inventory record.

    Returns:
        The identity part of one index entry.
    """
    return {
        "name": _text(record.get("name")),
        "type": _text(record.get("type")),
        "model": _text(record.get("model")),
        "serial": _text(record.get("serial")),
        "site_id": _text(record.get("site_id")),
    }


def _member_reading(module: Mapping[str, Any], chassis: Mapping[str, Any], field: str) -> Any:
    """Return one reading of a chassis member, or the reading of the whole device.

    Why:
        A member that just restarted reports an uptime of zero, and a member
        that never answered reports no version at all. A choice written with
        ``or`` reads both of those as absent and answers with the reading of
        the whole device. A fresh member would then show the uptime of the
        stack, and a silent member would show the version of the stack. Both
        hide a member that missed the upgrade, which is the fault this index
        exists to catch. The choice therefore tests for the reading, not for
        the truth of the reading.

    Args:
        module: The module statistics of one chassis member.
        chassis: The statistics record of the whole device.
        field: The name of the field to read.

    Returns:
        The reading of the member when the member holds one, else the reading
        of the whole device.
    """
    reading = module.get(field)
    if reading is not None:  # The cloud sends a null value for a member that never reported.
        return reading
    return chassis.get(field)


def _state_of(chassis: Mapping[str, Any], module: Mapping[str, Any]) -> dict[str, Any]:
    """Return the four index fields that the statistics own.

    Why:
        A chassis member holds its own firmware version and its own uptime
        inside ``module_stat``. An index that copied the chassis version to
        every member would hide a member that missed the upgrade, and that
        fault is the reason this feature exists.

    Args:
        chassis: The statistics record of the whole device.
        module: The module statistics of one chassis member.

    Returns:
        The state part of one index entry.
    """
    return {
        "version": _text(_member_reading(module, chassis, "version")),
        "status": _text(chassis.get("status")),
        "uptime": _whole_number(_member_reading(module, chassis, "uptime")),
        "ip": _text(chassis.get("ip")),
    }


def _chassis_of(record: Mapping[str, Any], chassis: Mapping[str, Any], module: Mapping[str, Any]) -> dict[str, Any]:
    """Return the three index fields that describe the virtual chassis.

    Why:
        A stack that loses a member keeps the same device count, so the member
        count is the only signal of the loss. The index stores the count as a
        plain field, and the comparison reads it directly.

    Args:
        record: One inventory record.
        chassis: The statistics record of the whole device.
        module: The module statistics of one chassis member.

    Returns:
        The chassis part of one index entry.
    """
    return {
        "vc_role": _text(module.get("vc_role")) or VC_ROLE_STANDALONE,
        "vc_mac": normalize_device_mac(record.get("vc_mac")),
        "num_members": _whole_number(chassis.get("num_members")) or DEFAULT_MEMBER_COUNT,
    }


def _index_entry(
    record: Mapping[str, Any], chassis_view: Mapping[str, Any], member_view: Mapping[str, Any], key: str
) -> dict[str, Any]:
    """Build one value of the device index.

    Why:
        The inventory lists every physical member, and the statistics answer
        for the whole chassis under one address. This function joins the two
        views, so a member entry still carries a version and a state.

    Args:
        record: One inventory record.
        chassis_view: The map from a device address to a statistics record.
        member_view: The map from a member address to a module record.
        key: The index key of this record.

    Returns:
        One index entry with the twelve fields of the data model.
    """
    module = member_view.get(key) or {}
    chassis_key = normalize_device_mac(record.get("vc_mac"))
    chassis = chassis_view.get(key) or chassis_view.get(chassis_key) or {}
    entry = _identity_of(record)
    entry.update(_state_of(chassis, module))
    entry.update(_chassis_of(record, chassis, module))
    return entry


def build_device_index(
    inventory: Sequence[Mapping[str, Any]], statistics: Sequence[Mapping[str, Any]]
) -> dict[str, dict[str, Any]]:
    """Build the flat device map that a comparison reads.

    Why:
        A comparison of two captures is a shallow map comparison over this
        field, which is the reason the field exists. The map holds no
        timestamp, because a timestamp makes every entry look new.

    Args:
        inventory: The inventory records of the site, with the chassis members.
        statistics: The statistics records of the site.

    Returns:
        A map from a device address to one index entry.
    """
    chassis_view = _chassis_view(statistics)
    member_view = _member_view(statistics)
    index: dict[str, dict[str, Any]] = {}
    for record in inventory:
        key = normalize_device_mac(record.get("mac"))
        if key:
            index[key] = _index_entry(record, chassis_view, member_view, key)
    logger.info("Upgrade portal built a device index of %s entries", len(index))
    return index


__all__ = [
    "DEFAULT_MEMBER_COUNT",
    "FALLBACK_PAGE_LIMIT",
    "HTTP_STATUS_NONE",
    "MAX_PAGE_LIMIT",
    "MIN_PAGE_LIMIT",
    "REASON_ERROR_STATUS",
    "REASON_READ_FAILED",
    "REASON_SHORT_READ",
    "REASON_TYPE_GAP",
    "REASON_UNKNOWN_SHAPE",
    "SECTION_INVENTORY",
    "SECTION_STATISTICS",
    "STATISTICS_TYPE",
    "VC_ROLE_STANDALONE",
    "DeviceRead",
    "build_device_index",
    "guard_page_count",
    "guard_statistics_coverage",
    "normalize_device_mac",
    "read_device_statistics",
    "read_inventory",
    "resolve_page_limit",
]
