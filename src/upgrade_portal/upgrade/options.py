"""The version list, the option mapping, and the gateway family split of one run.

Why:
    The operator picks a target version for each device and one value for each
    upgrade option. Those choices must reach ``src/firmware/upgrade_service.py``
    in the exact shape that the cloud accepts. This module holds that mapping in
    one place, so the route layer stays thin and a test proves each rule with no
    cloud call.

    The module reads the inventory with the virtual chassis parameter omitted.
    Decision D11 splits the two views of a stack. A capture needs every physical
    member, so ``src/upgrade_portal/capture/devices.py`` sends ``vc=True``. An
    upgrade targets the logical device, so this path sends no ``vc`` value at
    all. Sending both views to one cloud call would upgrade a member twice.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import partial
from typing import Any

import mistapi

from src.firmware.upgrade_service import (
    SCOPE_ORG,
    SCOPE_SITE,
    STRATEGY_DEFAULT,
    DeviceTarget,
    GatewayFamily,
    UpgradeOptions,
    classify_gateway,
    list_available_versions,
)
from src.upgrade_portal.capture.devices import (
    HTTP_STATUS_NONE,
    REASON_READ_FAILED,
    guard_page_count,
    normalize_device_mac,
    resolve_page_limit,
)

logger = logging.getLogger(__name__)

SECTION_UPGRADE_INVENTORY = "upgrade_inventory"

ERROR_BAD_OPTION = "bad_option"

DEVICE_TYPE_AP = "ap"
DEVICE_TYPE_SWITCH = "switch"
DEVICE_TYPE_GATEWAY = "gateway"

STATE_PENDING = "pending"

# The existing bulk flow offers these four values. ``big_bang`` and ``serial``
# appear at ``src/firmware/bulk_ap_upgrader.py:972-974``, ``rrm`` appears at
# ``src/firmware/bulk_ap_upgrader.py:995``, and ``src/firmware/bulk_switch_upgrader.py:21-23``
# names the first three again. FR-016 asks for the same list.
STRATEGY_CHOICES = ("big_bang", "canary", "rrm", "serial")

# FR-018 asks the portal to preselect the same default that the bulk flow uses.
# The seam already carries those defaults, so this module reads them instead of
# repeating them. One term, one meaning.
DEFAULT_OPTIONS = UpgradeOptions()

WARNING_MIXED_FAMILY = "The site holds two gateway families. The portal reports the result of each family on its own."
WARNING_SAME_VERSION = "One device already runs the version that you chose. The portal still sends the upgrade."

_BOOLEAN_WORDS: Mapping[str, bool] = {
    "true": True,
    "false": False,
    "yes": True,
    "no": False,
    "on": True,
    "off": False,
    "1": True,
    "0": False,
}


class BadOptionError(ValueError):
    """One upgrade option holds a value that the portal refuses.

    Why:
        ``contracts/http-api.md:207`` answers ``POST /api/runs/<id>/options``
        with the error code ``bad_option``. The route layer needs one exception
        that already carries that code, so no route repeats the mapping. The
        message names the field and never repeats the value, because a refused
        value comes straight from the browser.

    Attributes:
        code: Always ``bad_option``. The route layer copies it into the answer.
        field: The name of the option that failed.
    """

    def __init__(self, field: str) -> None:
        """Build the refusal for one named option.

        Args:
            field: The name of the option that failed.
        """
        self.code = ERROR_BAD_OPTION
        self.field = field
        super().__init__(f"the upgrade option {field} holds a value that the portal refuses")


@dataclass(frozen=True, slots=True)
class InventoryRead:
    """The devices of one site and the reasons that the read lost data.

    Why:
        The upgrade path needs the same honest partial report that the capture
        path uses. A silent empty list would offer the operator no device and
        look like a site with no hardware.

    Attributes:
        records: The inventory rows, one for each logical device.
        partial_reasons: One entry for each fault. Empty after a whole read.
    """

    records: list[dict[str, Any]]
    partial_reasons: list[dict[str, Any]]


def _partial_reason(reason: str, http_status: int) -> dict[str, Any]:
    """Build one entry of ``partial_reasons`` for the upgrade inventory.

    Why:
        Rule 5 at ``data-model.md:195`` states the three fields of an entry.
        One builder keeps every entry the same shape.

    Args:
        reason: The machine name of the fault.
        http_status: The HTTP status of the answer, or zero.

    Returns:
        One partial reason entry.
    """
    return {"section": SECTION_UPGRADE_INVENTORY, "reason": reason, "http_status": http_status}


def _read_paged(session: Any, call: Any) -> InventoryRead:
    """Run one paged cloud read and turn a fault into a partial reason.

    Why:
        ``mistapi.get_all`` answers an unknown body shape with an empty list and
        raises nothing (``.venv/Lib/site-packages/mistapi/__pagination.py:55``).
        The upgrade view would then show no device and look complete. This
        wrapper repeats the guard that ``src/upgrade_portal/capture/devices.py``
        uses, so a short read becomes a named reason.

    Args:
        session: The cloud session. The caller owns it.
        call: A callable that runs the first page of the read.

    Returns:
        The records and the reasons of the read.
    """
    try:
        response = call()
        records = mistapi.get_all(mist_session=session, response=response)
    except Exception as error:  # A cloud fault marks the read partial and never stops the run.
        logger.warning("Upgrade portal failed the upgrade inventory read: %s", error)
        return InventoryRead([], [_partial_reason(REASON_READ_FAILED, HTTP_STATUS_NONE)])
    rows = [dict(record) for record in records]
    logger.debug("Upgrade portal read %s logical device(s) for the upgrade view", len(rows))
    return InventoryRead(rows, guard_page_count(SECTION_UPGRADE_INVENTORY, len(rows), response))


def read_upgrade_inventory(session: Any, org_id: str, site_id: str, page_limit: int | None = None) -> InventoryRead:
    """Read every logical device of one site for the upgrade view.

    Why:
        Decision D11 states that an upgrade targets the logical device. The call
        therefore omits the virtual chassis parameter. ``getOrgInventory`` builds
        its query with ``if vc:``, so an omitted value sends nothing and the
        cloud returns one row for each stack instead of one row for each member.
        A read with ``vc=True`` would offer the operator four members of one
        stack and send four upgrades to one logical device.

    Args:
        session: The cloud session. The caller owns it.
        org_id: The organization that owns the site.
        site_id: The site to read.
        page_limit: The page size. None reads the shared page size.

    Returns:
        The inventory records and the reasons of the read.
    """
    limit = page_limit if page_limit is not None else resolve_page_limit()
    logger.info("Upgrade portal reads the logical devices of site %s for an upgrade", site_id)
    call = partial(
        mistapi.api.v1.orgs.inventory.getOrgInventory,
        session,
        org_id,
        site_id=site_id,
        limit=limit,
    )
    return _read_paged(session, call)


def collect_models(devices: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    """Return the model of each device, with no repeat.

    Why:
        The version read takes a model list and answers with one version list
        for each model. A repeated model would ask the cloud for the same answer
        twice.

    Args:
        devices: The inventory rows.

    Returns:
        The models in alphabetical order.
    """
    models = {str(device.get("model", "")).strip() for device in devices}
    models.discard("")
    return tuple(sorted(models))


def read_model_versions(
    session: Any,
    site_id: str,
    devices: Sequence[Mapping[str, Any]],
) -> Mapping[str, tuple[str, ...]]:
    """Return the version list of each model that the site holds.

    Why:
        The operator picks one version for each device, so the portal needs the
        list before it shows the choice. One read serves every model, because a
        read for each model would spend the rate limit for no gain.

    Args:
        session: The cloud session. The caller owns it.
        site_id: The site to read.
        devices: The inventory rows that name the models.

    Returns:
        The version list of each model.
    """
    models = collect_models(devices)
    logger.info("Upgrade portal reads the available versions of %s model(s) at site %s", len(models), site_id)
    return list_available_versions(session, site_id, models)


def build_version_options(
    devices: Sequence[Mapping[str, Any]],
    by_model: Mapping[str, tuple[str, ...]],
) -> list[dict[str, Any]]:
    """Build one version choice row for each device.

    Why:
        The options page needs a ``upgrade-version-select-{mac}`` control for
        each device. The control needs the model, the version that runs now, and
        the versions that the cloud offers. This function joins the inventory to
        the version list, so the template holds no lookup logic.

    Args:
        devices: The inventory rows.
        by_model: The version list of each model.

    Returns:
        One row for each device, in the order that the inventory returned.
    """
    rows: list[dict[str, Any]] = []
    for device in devices:
        model = str(device.get("model", "")).strip()
        rows.append(
            {
                "mac": normalize_device_mac(device.get("mac")),
                "name": str(device.get("name", "")).strip(),
                "device_type": str(device.get("type", "")).strip().lower(),
                "model": model,
                "version_before": str(device.get("version", "")).strip(),
                "versions": list(by_model.get(model, ())),
            }
        )
    logger.debug("Upgrade portal offers a version choice for %s device(s)", len(rows))
    return rows


def _read_boolean(payload: Mapping[str, Any], field: str, fallback: bool) -> bool:
    """Map one radio group value onto a boolean.

    Why:
        A radio group posts text, and a JSON client posts a real boolean. Both
        must reach the same field. Every other value is a fault of the caller,
        so the function refuses it instead of guessing.

    Args:
        payload: The request body.
        field: The name of the option.
        fallback: The value to use when the body names no value.

    Returns:
        The chosen boolean.

    Raises:
        BadOptionError: If the body holds a value that no rule maps.
    """
    if field not in payload or payload[field] is None:
        return fallback
    value = payload[field]
    if isinstance(value, bool):
        return value
    word = str(value).strip().lower()
    if word not in _BOOLEAN_WORDS:
        raise BadOptionError(field)
    return _BOOLEAN_WORDS[word]


def _read_strategy(payload: Mapping[str, Any]) -> str:
    """Map the strategy control onto the cloud strategy value.

    Why:
        The cloud refuses the whole call when the strategy names a value that it
        does not know, and the refusal names no field. The portal therefore
        checks the value before it builds the body.

    Args:
        payload: The request body.

    Returns:
        The chosen strategy.

    Raises:
        BadOptionError: If the body names a strategy that the bulk flow never
            offers.
    """
    value = payload.get("strategy")
    if value is None:
        return STRATEGY_DEFAULT
    word = str(value).strip().lower()
    if word not in STRATEGY_CHOICES:
        raise BadOptionError("strategy")
    return word


def _read_start_time(payload: Mapping[str, Any]) -> int | None:
    """Map the start time control onto epoch seconds.

    Why:
        The cloud reads ``start_time`` as epoch seconds. A text value or a
        negative value would reach the cloud and schedule the upgrade at a
        moment that nobody chose.

    Args:
        payload: The request body.

    Returns:
        The chosen moment in epoch seconds, or None for an immediate start.

    Raises:
        BadOptionError: If the value is not a whole number of seconds.
    """
    value = payload.get("start_time")
    if value is None or not str(value).strip():
        return None
    word = str(value).strip()
    if isinstance(value, bool) or not word.isdigit():
        raise BadOptionError("start_time")
    return int(word)


def build_options(payload: Mapping[str, Any]) -> UpgradeOptions:
    """Map the interface controls onto the seam option record.

    Why:
        ``contracts/http-api.md:209-216`` fixes the body of the options call.
        The seam holds the four fields that the cloud reads. This function is
        the only place that joins the two, so a new control changes one file.

    Args:
        payload: The request body of ``POST /api/runs/<run_id>/options``.

    Returns:
        The finished option record.

    Raises:
        BadOptionError: If any option holds a value that no rule maps.
    """
    logger.info("Upgrade portal maps %s upgrade option field(s)", len(payload))
    options = UpgradeOptions(
        reboot=_read_boolean(payload, "reboot", DEFAULT_OPTIONS.reboot),
        junos_file_action=_read_boolean(payload, "junos_file_action", DEFAULT_OPTIONS.junos_file_action),
        strategy=_read_strategy(payload),
        start_time=_read_start_time(payload),
    )
    logger.debug("Upgrade portal chose the strategy %s with reboot %s", options.strategy, options.reboot)
    return options


def resolve_family_scope(device_type: str, device: Mapping[str, Any]) -> tuple[str | None, str]:
    """Return the gateway family and the cloud scope of one device.

    Why:
        ``data-model.md:281-289`` states that a session smart router always uses
        the organization scope, because its cancel path exists at that scope
        alone. Every other device uses the site scope. The family field stays
        null unless the device is a gateway, so a switch never carries a gateway
        word.

    Args:
        device_type: The device type in lower case.
        device: The inventory row. ``classify_gateway`` reads ``type`` and
            ``model`` from it.

    Returns:
        The gateway family and the scope of the device.
    """
    if device_type != DEVICE_TYPE_GATEWAY:
        return None, SCOPE_SITE
    family = classify_gateway(device)
    if family is GatewayFamily.SSR:
        logger.debug("Upgrade portal sends a session smart router at the organization scope")
        return family.value, SCOPE_ORG
    return family.value, SCOPE_SITE


def _uptime_of(device: Mapping[str, Any]) -> int | None:
    """Return the uptime of one device in seconds.

    Why:
        The settle gate compares the uptime that it reads now against the uptime
        that the run recorded before the upgrade. A device that carries no
        reading must stay null, because a null reading is not a zero reading.
        A stored zero would make every later reading look larger and the gate
        would never see the reboot.

    Args:
        device: The device record. The caller merges the statistics into the
            inventory row before it calls this module.

    Returns:
        The uptime in whole seconds, or None when the record holds no reading.
    """
    value = device.get("uptime")
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return int(value)


def _last_seen_of(device: Mapping[str, Any]) -> int | None:
    """Return the moment that the cloud last heard from one device.

    Why:
        The settle gate needs an absolute anchor. The uptime of a device is
        nullable, so a device whose uptime never arrives can never show a
        fall, and it waits to the phase deadline. The cloud raises this moment
        each time it hears from the device, so a later moment proves that the
        device returned. The value stays null when the record holds no
        reading, because a stored zero sits at the start of the epoch and
        every later record would look newer.

    Args:
        device: The device record. The caller merges the statistics into the
            inventory row before it calls this module.

    Returns:
        The moment in epoch seconds, or None when the record holds no reading.
    """
    value = device.get("last_seen")
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return int(value)


def _target_identity(device: Mapping[str, Any], version_target: str) -> dict[str, Any]:
    """Build the naming fields of one target entry.

    Args:
        device: The device record.
        version_target: The version that the operator chose.

    Returns:
        The naming fields of ``data-model.md`` section 4.2.
    """
    return {
        "mac": normalize_device_mac(device.get("mac")),
        "name": str(device.get("name", "")).strip(),
        "device_type": str(device.get("type", "")).strip().lower(),
        "model": str(device.get("model", "")).strip(),
        "version_before": str(device.get("version", "")).strip(),
        "version_target": version_target,
    }


def _target_progress(device: Mapping[str, Any]) -> dict[str, Any]:
    """Build the progress fields of one target entry.

    Why:
        Every progress field starts empty. The run driver and the settle gate
        fill them later. One builder keeps every entry the same shape, so the
        status view never meets a missing key. The two ``before`` fields are
        the anchors of the settle gate, and each one holds a null when the
        record carried no reading.

    Args:
        device: The device record.

    Returns:
        The progress fields of ``data-model.md`` section 4.2.
    """
    return {
        "version_after": None,
        "upgrade_id": None,
        "state": STATE_PENDING,
        "uptime_before": _uptime_of(device),
        "last_seen_before": _last_seen_of(device),
        "reboot_seen_at": None,
        "settled_at": None,
    }


def build_target_entry(device: Mapping[str, Any], version_target: str) -> dict[str, Any]:
    """Build one entry of the run ``targets`` list.

    Why:
        ``data-model.md`` section 4.2 fixes the base fields of an entry, and
        the settle gate adds ``last_seen_before`` as its absolute anchor. One
        builder writes every field, so no later writer invents a key and no
        reader meets a missing key.

    Args:
        device: The device record.
        version_target: The version that the operator chose for this device.

    Returns:
        One finished target entry.
    """
    entry = _target_identity(device, version_target)
    entry["gateway_family"], entry["scope"] = resolve_family_scope(entry["device_type"], device)
    entry.update(_target_progress(device))
    return entry


def _resolve_choice(
    index: Mapping[str, Mapping[str, Any]],
    choice: Mapping[str, Any],
) -> tuple[Mapping[str, Any], str]:
    """Find the device of one browser choice.

    Why:
        The browser posts a MAC address and a version. A MAC address that the
        site does not hold is a fault of the caller, and an upgrade of an
        unknown device would reach the wrong site.

    Args:
        index: The devices of the site, keyed by the normalized MAC address.
        choice: One entry of the ``targets`` list in the request body.

    Returns:
        The device record and the chosen version.

    Raises:
        BadOptionError: If the MAC address is unknown or the version is empty.
    """
    mac = normalize_device_mac(choice.get("mac"))
    version = str(choice.get("version_target", "")).strip()
    if not mac or mac not in index:
        raise BadOptionError("mac")
    if not version:
        raise BadOptionError("version_target")
    return index[mac], version


def build_targets(
    devices: Sequence[Mapping[str, Any]],
    choices: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Build the run ``targets`` list from the browser choices.

    Why:
        The run record holds one entry for each device that the run upgrades.
        The entry carries the family and the scope, so the stop path and the
        status view need no second lookup.

    Args:
        devices: The inventory rows of the site.
        choices: The ``targets`` list of the request body. Each entry holds a
            ``mac`` value and a ``version_target`` value.

    Returns:
        One target entry for each choice, in the order of the request.

    Raises:
        BadOptionError: If a choice names an unknown device or no version.
    """
    index = {normalize_device_mac(device.get("mac")): device for device in devices}
    logger.info("Upgrade portal builds %s upgrade target(s)", len(choices))
    entries = [build_target_entry(*_resolve_choice(index, choice)) for choice in choices]
    logger.debug("Upgrade portal built targets for %s device type(s)", len({row["device_type"] for row in entries}))
    return entries


def target_warnings(entries: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    """Return the plain sentences that the operator reads before the start.

    Why:
        FR-020 asks the portal to report each gateway family on its own when one
        site holds both. A device that already runs the chosen version also
        deserves a word, because the operator may have picked the wrong row.

    Args:
        entries: The finished target entries.

    Returns:
        One sentence for each warning. Empty when nothing needs a word.
    """
    families = {row.get("gateway_family") for row in entries if row.get("gateway_family")}
    repeats = [row for row in entries if row.get("version_before") and row["version_before"] == row["version_target"]]
    warnings: list[str] = []
    if len(families) > 1:
        warnings.append(WARNING_MIXED_FAMILY)
    if repeats:
        warnings.append(WARNING_SAME_VERSION)
    return tuple(warnings)


def to_device_targets(entries: Sequence[Mapping[str, Any]], site_id: str) -> tuple[DeviceTarget, ...]:
    """Turn the stored target entries into the seam record.

    Why:
        ``plan_upgrade`` takes ``DeviceTarget`` values and groups them by device
        type, by family, and by version. The run record stores plain mappings so
        that the document store can write them. This function bridges the two
        shapes in one place.

    Args:
        entries: The stored target entries.
        site_id: The site that owns every device.

    Returns:
        One seam record for each entry.
    """
    return tuple(
        DeviceTarget(
            mac=str(entry["mac"]),
            name=str(entry.get("name", "")),
            device_type=str(entry["device_type"]),
            model=str(entry.get("model", "")),
            version_before=str(entry.get("version_before", "")),
            version_target=str(entry["version_target"]),
            site_id=site_id,
        )
        for entry in entries
    )


__all__ = [
    "DEFAULT_OPTIONS",
    "DEVICE_TYPE_AP",
    "DEVICE_TYPE_GATEWAY",
    "DEVICE_TYPE_SWITCH",
    "ERROR_BAD_OPTION",
    "SECTION_UPGRADE_INVENTORY",
    "STATE_PENDING",
    "STRATEGY_CHOICES",
    "WARNING_MIXED_FAMILY",
    "WARNING_SAME_VERSION",
    "BadOptionError",
    "InventoryRead",
    "build_options",
    "build_target_entry",
    "build_targets",
    "build_version_options",
    "collect_models",
    "read_model_versions",
    "read_upgrade_inventory",
    "resolve_family_scope",
    "target_warnings",
    "to_device_targets",
]
