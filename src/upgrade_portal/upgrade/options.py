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
import os
import re
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from functools import partial
from typing import Any

import mistapi

from src.firmware.upgrade_service import (
    MESH_UPGRADE_CHOICES,
    NODE_ORDER_CHOICES,
    SCOPE_ORG,
    SCOPE_SITE,
    STRATEGY_CANARY,
    STRATEGY_DEFAULT,
    CanaryOptions,
    DeviceTarget,
    GatewayFamily,
    PeerToPeerOptions,
    RrmOptions,
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

# The clock of the browser and the clock of the portal rarely agree to the
# second, and an operator who chooses "now" sends a moment that may already be a
# few seconds old. This window keeps that ordinary difference out of the refusal.
START_TIME_GRACE_SECONDS = 120

# A millisecond epoch pasted into the field reads as a moment tens of thousands
# of years ahead. The cloud accepts it and the upgrade never runs, so the
# operator waits for work that can never start. One year of lead time covers
# every real maintenance window and still refuses that mistake.
START_TIME_HORIZON_SECONDS = 365 * 24 * 60 * 60

WARNING_MIXED_FAMILY = "The site holds two gateway families. The portal reports the result of each family on its own."
WARNING_SAME_VERSION = "One device already runs the version that you chose. The portal still sends the upgrade."
WARNING_NO_COMMON_CANDIDATE = "No common compatible version exists for the {device_type} devices."

SUPPORTED_DEVICE_TYPES = (DEVICE_TYPE_AP, DEVICE_TYPE_SWITCH, DEVICE_TYPE_GATEWAY)
TYPE_DISPLAY_NAMES = {
    DEVICE_TYPE_AP: "access point",
    DEVICE_TYPE_SWITCH: "switch",
    DEVICE_TYPE_GATEWAY: "gateway",
}
TYPE_OVERRIDE_VARIABLES = {
    DEVICE_TYPE_AP: "CAPTURE_DEFAULT_AP_VERSION",
    DEVICE_TYPE_SWITCH: "CAPTURE_DEFAULT_SWITCH_VERSION",
    DEVICE_TYPE_GATEWAY: "CAPTURE_DEFAULT_GATEWAY_VERSION",
}

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

# The stored option record nests the three advanced groups, because `asdict`
# walks a nested record. The browser posts every field flat instead. The reader
# merges each nested group back up before it reads one field, so one reading
# path serves both shapes. Every field name inside a group is already the cloud
# field name, so the merge renames nothing.
_OPTION_GROUP_KEYS = ("canary", "rrm", "peer_to_peer")

# A percentage names a share of the run, so the cloud refuses a value outside
# this range (POST_sites_site_id_devices_upgrade.md:67-68).
_PERCENTAGE_LOWEST = 0
_PERCENTAGE_HIGHEST = 100

# A phase list that named no phase would upgrade nothing, and a list longer than
# this reads as a paste mistake. The cloud names no limit, so the portal sets one
# that no real maintenance plan reaches.
_PHASE_COUNT_HIGHEST = 20

# A download group of no access point downloads nothing, and a count above this
# reads as a paste mistake. The cloud default is 10.
_P2P_SIZE_HIGHEST = 1000


class BadOptionError(ValueError):
    """One upgrade option holds a value that the portal refuses.

    Why:
        ``contracts/http-api.md:348`` answers ``POST /api/runs/<id>/options``
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


def _normalized_version(value: object) -> str:
    """Return the exact version form used for compatibility comparisons."""
    return str(value).strip()


def _numeric_version_key(version: str) -> tuple[int, ...]:
    """Return numeric release components so display ordering cannot choose a release."""
    parts = tuple(int(part) for part in re.findall(r"\d+", version))
    return parts or (-1,)


def _eligible_devices(devices: Sequence[Mapping[str, Any]], device_type: str) -> list[Mapping[str, Any]]:
    """Return supported, identified records of one type that can take a target."""
    return [
        device
        for device in devices
        if str(device.get("type", "")).strip().lower() == device_type
        and normalize_device_mac(device.get("mac"))
        and str(device.get("model", "")).strip()
    ]


def _model_version_sets(
    devices: Sequence[Mapping[str, Any]],
    versions_by_model: Mapping[str, Sequence[str]],
) -> list[set[str]]:
    """Return the nonempty version set for each eligible device model."""
    return [
        {
            normalized
            for version in versions_by_model.get(str(device["model"]).strip(), ())
            if (normalized := _normalized_version(version))
        }
        for device in devices
    ]


def _common_candidates(version_sets: Sequence[set[str]]) -> list[str]:
    """Return common versions in descending numeric release order."""
    common = set.intersection(*version_sets) if version_sets else set()
    return sorted(common, key=_numeric_version_key, reverse=True)


def _configured_override(
    device_type: str,
    configured: Mapping[str, str | None],
) -> str:
    """Return the configured type override in its comparison form."""
    value = configured.get(TYPE_OVERRIDE_VARIABLES[device_type])
    return _normalized_version(value) if value else ""


def safe_model_target(
    device_type: str,
    versions: Sequence[str],
    override: str | None,
) -> tuple[str, str]:
    """Return the safe target and the rule that selected it for one model."""
    offered = sorted(
        {_normalized_version(version) for version in versions if _normalized_version(version)},
        key=_numeric_version_key,
        reverse=True,
    )
    configured = _normalized_version(override) if override else ""
    if configured and configured in offered:
        return configured, "override"
    return (offered[0], "model_fallback") if offered else ("", "unavailable")


def selected_device_types(body: Mapping[str, Any]) -> tuple[str, ...]:
    """Validate the selected device types, or use every supported type by default."""
    raw_types = body.get("selected_types")
    if raw_types is None:
        return SUPPORTED_DEVICE_TYPES
    if not isinstance(raw_types, list) or not raw_types:
        raise BadOptionError("selected_types")
    selected = tuple(str(item).strip().lower() for item in raw_types)
    if len(set(selected)) != len(selected) or any(item not in SUPPORTED_DEVICE_TYPES for item in selected):
        raise BadOptionError("selected_types")
    return selected


def _type_warning(device_type: str, eligible: Sequence[Mapping[str, Any]], candidates: Sequence[str]) -> str | None:
    """Return the warning when a type has devices but no shared version."""
    if eligible and not candidates:
        return WARNING_NO_COMMON_CANDIDATE.format(device_type=TYPE_DISPLAY_NAMES[device_type])
    return None


class TypedVersionSelector:
    """Choose one safe default from versions that every device type supports."""

    def select(
        self,
        devices: Sequence[Mapping[str, Any]],
        versions_by_model: Mapping[str, Sequence[str]],
        overrides: Mapping[str, str | None] | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Return candidates, selection, and warning for every supported type."""
        configured = overrides if overrides is not None else os.environ
        selections: dict[str, dict[str, Any]] = {}
        for device_type in SUPPORTED_DEVICE_TYPES:
            eligible = _eligible_devices(devices, device_type)
            candidates = _common_candidates(_model_version_sets(eligible, versions_by_model))
            override = _configured_override(device_type, configured)
            selected = override if override in candidates else (candidates[0] if candidates else None)
            selections[device_type] = {
                "candidates": candidates,
                "selected_version": selected,
                "override_value": override or None,
                "warning": _type_warning(device_type, eligible, candidates),
            }
        logger.debug("Upgrade portal selected typed defaults for %s type(s)", len(selections))
        return selections


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
        logger.warning("Upgrade portal failed the upgrade inventory read: %s", type(error).__name__)
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
    org_id: str | None = None,
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
        org_id: The organization that owns the site and supplies SSR versions.

    Returns:
        The version list of each model.
    """
    models = collect_models(devices)
    logger.info("Upgrade portal reads the available versions of %s model(s) at site %s", len(models), site_id)
    return list_available_versions(session, site_id, devices, org_id)


def build_version_options(
    devices: Sequence[Mapping[str, Any]],
    by_model: Mapping[str, tuple[str, ...]],
    type_selections: Mapping[str, Mapping[str, Any]] | None = None,
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
        type_selections: The selected default for each device type.

    Returns:
        One row for each device, in the order that the inventory returned.
    """
    selections = type_selections or {}
    rows: list[dict[str, Any]] = []
    for device in devices:
        model = str(device.get("model", "")).strip()
        device_type = str(device.get("type", "")).strip().lower()
        versions = sorted(
            {_normalized_version(version) for version in by_model.get(model, ()) if _normalized_version(version)},
            key=_numeric_version_key,
            reverse=True,
        )
        selected = str(selections.get(device_type, {}).get("selected_version") or "")
        safe_target, target_source = safe_model_target(
            device_type,
            versions,
            _configured_override(device_type, os.environ),
        )
        version_target = selected if selected in versions else safe_target
        version_before = str(device.get("version", "")).strip()
        rows.append(
            {
                "mac": normalize_device_mac(device.get("mac")),
                "name": str(device.get("name", "")).strip(),
                "device_type": device_type,
                "model": model,
                "version_before": version_before,
                "version_target": version_target,
                "safe_target": safe_target,
                "target_source": target_source,
                "firmware_mismatch": bool(version_before) and bool(safe_target) and version_before != safe_target,
                "versions": versions,
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


def _now_epoch() -> int:
    """Read the current moment as whole epoch seconds.

    Why:
        The start time window compares the chosen moment against now. A named
        function is the seam that a test replaces, so no test depends on the
        clock of the machine that runs it.

    Returns:
        The current moment in epoch seconds.
    """
    return int(time.time())


def _guard_start_time(moment: int, now: int, field: str = "start_time") -> int:
    """Refuse a chosen moment that sits outside the window a run can use.

    Why:
        The cloud starts the upgrade at once when the moment is already past, so
        a stale value writes firmware immediately while the operator believes
        they scheduled it for later. A moment far ahead never runs at all, and
        the operator waits for work that can never start. Both readings look
        valid to every earlier check, so the window is the only guard.

        The separate reboot window obeys the same rule, so it passes its own
        field name. A refusal that named the start time for a bad reboot window
        would send the operator to the wrong control.

    Args:
        moment: The chosen moment in epoch seconds.
        now: The current moment in epoch seconds.
        field: The control that holds the moment.

    Returns:
        The chosen moment, unchanged.

    Raises:
        BadOptionError: If the moment is already past, or more than one year
            ahead.
    """
    if moment < now - START_TIME_GRACE_SECONDS:
        logger.warning("Upgrade portal refused the field %s because the moment is already past", field)
        raise BadOptionError(field)
    if moment > now + START_TIME_HORIZON_SECONDS:
        logger.warning("Upgrade portal refused the field %s because the moment is more than one year ahead", field)
        raise BadOptionError(field)
    return moment


def _read_start_time(payload: Mapping[str, Any], now: Callable[[], int] | None) -> int | None:
    """Map the start time control onto epoch seconds.

    Why:
        The cloud reads ``start_time`` as epoch seconds. A text value or a
        negative value would reach the cloud and schedule the upgrade at a
        moment that nobody chose.

    Args:
        payload: The request body.
        now: The clock that reads the current moment, or None to keep a stored
            choice exactly as the operator made it.

    Returns:
        The chosen moment in epoch seconds, or None for an immediate start.

    Raises:
        BadOptionError: If the value is not a whole number of seconds, or names
            a moment outside the window that a run can use.
    """
    value = payload.get("start_time")
    if value is None or not str(value).strip():
        return None
    word = str(value).strip()
    if isinstance(value, bool) or not word.isdigit():
        raise BadOptionError("start_time")
    moment = int(word)  # ``isdigit`` already refused a sign, so the value is whole and not negative.
    return moment if now is None else _guard_start_time(moment, now())


def _flat_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Merge every nested advanced group of a stored record back into flat keys.

    Why:
        ``build_options_record`` stores the option record through ``asdict``,
        which writes the three advanced groups as nested mappings. The browser
        posts the same fields flat. One reading path must serve both shapes, or
        a saved run would replay with every advanced choice dropped and the
        cloud would run a plan that nobody picked.

    Args:
        payload: The request body, or the stored option record.

    Returns:
        One flat mapping. A flat key of the payload outranks a nested one,
        because a fresh browser choice must replace a stored one.
    """
    merged = dict(payload)
    for group in _OPTION_GROUP_KEYS:
        nested = payload.get(group)
        if isinstance(nested, Mapping):  # A stored record nests. A browser body does not.
            for name, value in nested.items():
                merged.setdefault(name, value)  # The group field names are already the cloud names.
    return merged


def _read_whole_number(payload: Mapping[str, Any], field: str, highest: int) -> int | None:
    """Read one optional whole number, or refuse a value outside its range.

    Why:
        Every advanced count and every percentage reaches the cloud as a whole
        number. A text value or a negative value would reach the cloud and set a
        limit that nobody chose, and the cloud refusal names no field.

    Args:
        payload: The flat request body.
        field: The cloud field name.
        highest: The largest value the portal accepts.

    Returns:
        The chosen number, or None when the operator left the control alone.

    Raises:
        BadOptionError: If the value is not a whole number inside the range.
    """
    value = payload.get(field)
    if value is None or not str(value).strip():
        return None
    word = str(value).strip()
    if isinstance(value, bool) or not word.isdigit():  # A sign, a decimal point, and a word all fail here.
        raise BadOptionError(field)
    number = int(word)
    if number > highest:
        logger.warning("Upgrade portal refused the field %s above its limit", field)
        raise BadOptionError(field)
    return number


def _number_entries(value: Any) -> list[str]:
    """Split one list control into its entries, whatever shape it arrives in.

    Why:
        A stored record replays a tuple, a JSON store replays a list, and a text
        input posts one comma-separated word. All three must reach the same
        entries, and each empty entry drops so a trailing comma reads as no
        entry at all.

    Args:
        value: The raw value of one list control.

    Returns:
        One text entry for each number that the control names.
    """
    sequence = list(value) if isinstance(value, (list, tuple)) else str(value).split(",")
    return [str(one).strip() for one in sequence if str(one).strip()]


def _read_number_list(payload: Mapping[str, Any], field: str) -> tuple[int, ...] | None:
    """Read one optional list of whole numbers from a text field or a real list.

    Why:
        The phase control and the failure control both carry a list. A text
        input posts ``1,10,50,100`` and a JSON client posts a real list. Both
        must reach the same tuple, and every other shape is a caller fault.

    Args:
        payload: The flat request body.
        field: The cloud field name.

    Returns:
        The chosen numbers, or None when the operator left the control alone.

    Raises:
        BadOptionError: If any entry is not a whole number, or the list is
            empty, or the list is longer than the portal accepts.
    """
    value = payload.get(field)
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    entries = _number_entries(value)
    if not entries or len(entries) > _PHASE_COUNT_HIGHEST:
        logger.warning("Upgrade portal refused the list field %s for its length", field)
        raise BadOptionError(field)
    if not all(word.isdigit() for word in entries):  # A sign and a decimal point both fail here.
        raise BadOptionError(field)
    return tuple(int(word) for word in entries)


def _read_word_choice(payload: Mapping[str, Any], field: str, choices: Sequence[str]) -> str | None:
    """Read one optional word that must come from a fixed list.

    Why:
        The cloud refuses the whole call when a word sits outside its own
        enumeration, and the refusal names no field. The portal checks each word
        before it builds the body.

    Args:
        payload: The flat request body.
        field: The cloud field name.
        choices: Every word that the cloud accepts for this field.

    Returns:
        The chosen word, or None when the operator left the control alone.

    Raises:
        BadOptionError: If the word sits outside the list.
    """
    value = payload.get(field)
    if value is None or not str(value).strip():
        return None
    word = str(value).strip().lower()
    if word not in choices:
        raise BadOptionError(field)
    return word


def _read_optional_boolean(payload: Mapping[str, Any], field: str) -> bool | None:
    """Read one optional boolean that stays absent until the operator sets it.

    Why:
        Every radio resource management flag has a cloud default, and the
        contract asks the portal to omit an optional field unless the operator
        picks it. A ``False`` that the portal invented would replace a cloud
        default that the operator never saw.

    Args:
        payload: The flat request body.
        field: The cloud field name.

    Returns:
        The chosen boolean, or None when the body names no value.

    Raises:
        BadOptionError: If the body holds a value that no rule maps.
    """
    if field not in payload or payload[field] is None or not str(payload[field]).strip():
        return None
    return _read_boolean(payload, field, False)


def _read_canary(payload: Mapping[str, Any]) -> CanaryOptions:
    """Read the three staged-upgrade controls.

    Args:
        payload: The flat request body.

    Returns:
        The staged-upgrade settings.

    Raises:
        BadOptionError: If a phase list, a failure list, or the percentage holds
            a value that no rule maps.
    """
    phases = _read_number_list(payload, "canary_phases")
    failures = _read_number_list(payload, "max_failures")
    if failures is not None and len(failures) != len(phases or ()):
        # The cloud needs one failure limit for each phase. A shorter list would
        # leave a later phase with no limit at all, and the run would continue
        # through a failure that the operator meant to stop.
        logger.warning("Upgrade portal refused a failure list that does not match the phase list")
        raise BadOptionError("max_failures")
    return CanaryOptions(
        canary_phases=phases,
        max_failures=failures,
        max_failure_percentage=_read_whole_number(payload, "max_failure_percentage", _PERCENTAGE_HIGHEST),
    )


def _read_rrm(payload: Mapping[str, Any]) -> RrmOptions:
    """Read the five radio resource management controls.

    Args:
        payload: The flat request body.

    Returns:
        The radio resource management settings.

    Raises:
        BadOptionError: If a percentage or a word holds a value that no rule
            maps.
    """
    return RrmOptions(
        rrm_first_batch_percentage=_read_whole_number(payload, "rrm_first_batch_percentage", _PERCENTAGE_HIGHEST),
        rrm_max_batch_percentage=_read_whole_number(payload, "rrm_max_batch_percentage", _PERCENTAGE_HIGHEST),
        rrm_mesh_upgrade=_read_word_choice(payload, "rrm_mesh_upgrade", MESH_UPGRADE_CHOICES),
        rrm_node_order=_read_word_choice(payload, "rrm_node_order", NODE_ORDER_CHOICES),
        rrm_slow_ramp=_read_optional_boolean(payload, "rrm_slow_ramp"),
    )


def _read_peer_to_peer(payload: Mapping[str, Any]) -> PeerToPeerOptions:
    """Read the three access-point-to-access-point download controls.

    Args:
        payload: The flat request body.

    Returns:
        The peer-to-peer download settings.

    Raises:
        BadOptionError: If a count holds a value that no rule maps.
    """
    return PeerToPeerOptions(
        enable_p2p=_read_boolean(payload, "enable_p2p", DEFAULT_OPTIONS.peer_to_peer.enable_p2p),
        p2p_cluster_size=_read_whole_number(payload, "p2p_cluster_size", _P2P_SIZE_HIGHEST),
        p2p_parallelism=_read_whole_number(payload, "p2p_parallelism", _P2P_SIZE_HIGHEST),
    )


def _read_reboot_at(payload: Mapping[str, Any], now: Callable[[], int] | None) -> int | None:
    """Map the separate reboot window onto epoch seconds.

    Why:
        A switch and a Junos gateway can write the firmware in one window and
        reboot in a later one. The moment obeys the same window rule as the
        start time, because a moment already past reboots the device at once and
        a moment far ahead never reboots it at all.

    Args:
        payload: The flat request body.
        now: The clock that bounds the moment, or None to replay a stored choice.

    Returns:
        The chosen moment in epoch seconds, or None to reboot as soon as the
        write ends.

    Raises:
        BadOptionError: If the value is not a whole number of seconds, or names
            a moment outside the window that a run can use.
    """
    value = payload.get("reboot_at")
    if value is None or not str(value).strip():
        return None
    word = str(value).strip()
    if isinstance(value, bool) or not word.isdigit():
        raise BadOptionError("reboot_at")
    moment = int(word)  # ``isdigit`` already refused a sign, so the value is whole and not negative.
    return moment if now is None else _guard_start_time(moment, now(), "reboot_at")


def _guard_strategy_settings(options: UpgradeOptions) -> None:
    """Refuse an advanced setting that its own strategy never reads.

    Why:
        The cloud reads a phase list for the canary strategy alone, and it reads
        every radio field for the radio strategy alone. A body that carried one
        outside its own strategy would drop the setting without a word, and the
        operator would read a plan that the cloud never runs.

    Args:
        options: The finished option record.

    Raises:
        BadOptionError: If a setting sits outside the strategy that reads it.
    """
    if options.strategy != STRATEGY_CANARY and options.canary.canary_phases is not None:
        logger.warning("Upgrade portal refused a phase list outside the staged strategy")
        raise BadOptionError("canary_phases")
    if options.strategy == STRATEGY_DEFAULT and options.canary.max_failure_percentage is not None:
        logger.warning("Upgrade portal refused a failure limit for a single write of every device")
        raise BadOptionError("max_failure_percentage")


def build_options(payload: Mapping[str, Any], now: Callable[[], int] | None = _now_epoch) -> UpgradeOptions:
    """Map the interface controls onto the seam option record.

    Why:
        ``contracts/http-api.md:356-364`` fixes the body of the options call.
        This function is the only place that joins the controls and the seam, so
        a new control changes one file. It reads a flat body from the browser and
        a nested body from the store, because ``_flat_payload`` merges the two
        shapes into one first.

    Args:
        payload: The request body of ``POST /api/runs/<run_id>/options``, or the
            stored option record of one run.
        now: The clock that bounds the start time. Pass None to replay a stored
            choice, which the operator already made against an earlier clock.

    Returns:
        The finished option record.

    Raises:
        BadOptionError: If any option holds a value that no rule maps.
    """
    logger.info("Upgrade portal maps %s upgrade option field(s)", len(payload))
    flat = _flat_payload(payload)  # One shape, whether the browser or the store sent it.
    options = UpgradeOptions(
        reboot=_read_boolean(flat, "reboot", DEFAULT_OPTIONS.reboot),
        junos_file_action=_read_boolean(flat, "junos_file_action", DEFAULT_OPTIONS.junos_file_action),
        strategy=_read_strategy(flat),
        start_time=_read_start_time(flat, now),
        reboot_at=_read_reboot_at(flat, now),
        force=_read_boolean(flat, "force", DEFAULT_OPTIONS.force),
        stable_version=_read_boolean(flat, "stable_version", DEFAULT_OPTIONS.stable_version),
        canary=_read_canary(flat),
        rrm=_read_rrm(flat),
        peer_to_peer=_read_peer_to_peer(flat),
    )
    _guard_strategy_settings(options)  # A setting outside its own strategy is a caller fault.
    logger.debug("Upgrade portal chose the strategy %s with reboot %s", options.strategy, options.reboot)
    return options


def build_option_record(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return the stored option record of one request body.

    Why:
        Two callers store an option record. ``build_options_record`` stores one
        after it reads the site inventory, and the route stores one when no
        inventory answers. Both must write the same shape, or a run that met a
        failed inventory read would lose every advanced choice and the schedule
        that the operator picked.

    Args:
        payload: The request body of the options call.

    Returns:
        The option record, with the three advanced groups nested.

    Raises:
        BadOptionError: If any option holds a value that no rule maps.
    """
    return asdict(build_options(payload))


def _display_text(value: Any) -> str:
    """Turn one stored advanced value into the text that a control shows.

    Why:
        Every advanced control is a text field or a select, and both read text.
        A list joins with commas, because the phase control and the failure
        control both post that form. A boolean becomes a word, because the
        radio ramp select offers a word. An absent value becomes an empty text,
        which every control reads as "keep the cloud default".

    Args:
        value: The stored value of one advanced option.

    Returns:
        The text that the control shows.
    """
    if value is None:
        return ""
    if isinstance(value, bool):  # This test must come first, because a bool is an int.
        return "yes" if value else "no"
    if isinstance(value, (list, tuple)):
        return ",".join(str(one) for one in value)
    return str(value)


def advanced_option_values(stored: Mapping[str, Any]) -> dict[str, str]:
    """Flatten the stored advanced options into the text of each control.

    Why:
        ``build_options_record`` stores the three advanced groups as nested
        mappings, and the options page draws one flat control for each field. A
        template that walked the groups on its own would repeat the storage
        shape in markup, and a later change of that shape would leave the page
        blank with no error at all.

        A saved run must reopen with every choice still shown. Issue #2156 asks
        for that reload, because an operator who edits one control and loses the
        other eight sends a plan that nobody reviewed.

    Args:
        stored: The ``options`` record of one run, or an empty mapping.

    Returns:
        The text of each advanced control, keyed by its cloud field name.
    """
    flat = _flat_payload(stored)  # One shape, whether the record nests the groups or not.
    names = (
        "max_failure_percentage",
        "canary_phases",
        "max_failures",
        "reboot_at",
        "p2p_cluster_size",
        "p2p_parallelism",
        "rrm_first_batch_percentage",
        "rrm_max_batch_percentage",
        "rrm_node_order",
        "rrm_mesh_upgrade",
        "rrm_slow_ramp",
    )
    return {name: _display_text(flat.get(name)) for name in names}


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


def _selected_target_choices(
    resolved: Sequence[tuple[Mapping[str, Any], str]],
    selected_types: Sequence[str] | None,
) -> list[tuple[Mapping[str, Any], str]]:
    """Return only target choices of the selected supported types."""
    allowed_types = set(selected_types) if selected_types is not None else set(SUPPORTED_DEVICE_TYPES)
    selected = [
        (device, version)
        for device, version in resolved
        if str(device.get("type", "")).strip().lower() in allowed_types
    ]
    if resolved and not selected:
        raise BadOptionError("targets")
    return selected


def _validate_target_versions(
    selected: Sequence[tuple[Mapping[str, Any], str]],
    versions_by_model: Mapping[str, Sequence[str]] | None,
) -> None:
    """Refuse each target version that its device model does not offer."""
    if versions_by_model is None:
        return
    for device, version in selected:
        model = str(device.get("model", "")).strip()
        offered = {_normalized_version(item) for item in versions_by_model.get(model, ())}
        if version not in offered:
            logger.warning("Upgrade portal refused an unavailable target for model %s", model)
            raise BadOptionError("version_target")


def build_targets(
    devices: Sequence[Mapping[str, Any]],
    choices: Sequence[Mapping[str, Any]],
    versions_by_model: Mapping[str, Sequence[str]] | None = None,
    selected_types: Sequence[str] | None = None,
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
        BadOptionError: If a choice names an unknown device, no version, or a
            version that current availability does not offer.
    """
    index = {normalize_device_mac(device.get("mac")): device for device in devices}
    logger.info("Upgrade portal builds %s upgrade target(s)", len(choices))
    resolved = [_resolve_choice(index, choice) for choice in choices]
    selected = _selected_target_choices(resolved, selected_types)
    _validate_target_versions(selected, versions_by_model)
    entries = [build_target_entry(device, version) for device, version in selected]
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


def build_options_view(session: Any, org_id: str, site_id: str) -> dict[str, Any]:
    """Build the device rows and the version map that the options page draws.

    Why:
        The options page drew only the rows that the run record already held,
        and a fresh run holds none. The page therefore stayed empty, the browser
        found no version control to read, and the saved target list stayed
        empty. This function reads the site once and answers both halves that
        the page needs, so the operator sees a device on the first view.

    Args:
        session: The cloud session of the signed-in operator.
        org_id: The organization that holds the site.
        site_id: The site under upgrade.

    Returns:
        A mapping with a ``targets`` list of device rows and a
        ``versions_by_model`` map of the versions of each model.
    """
    inventory = read_upgrade_inventory(session, org_id, site_id)
    if not inventory.records:  # A failed read must never spend a second call for no gain.
        logger.warning("Upgrade portal read no device of site %s for the options page", site_id)
        return {"targets": [], "versions_by_model": {}}
    by_model = read_model_versions(session, site_id, inventory.records, org_id)
    type_selections = TypedVersionSelector().select(inventory.records, by_model)
    rows = build_version_options(inventory.records, by_model, type_selections)
    logger.info("Upgrade portal offers %s device(s) on the options page of site %s", len(rows), site_id)
    return {
        "targets": rows,
        "versions_by_model": {name: list(items) for name, items in by_model.items()},
        "type_selections": type_selections,
    }


def build_options_record(session: Any, org_id: str, site_id: str, body: Mapping[str, Any]) -> dict[str, Any]:
    """Build the stored target list and option record from the browser choices.

    Why:
        The browser sends only a MAC address and a target version for each
        device, but ``to_device_targets`` reads ``device_type`` and the run
        driver reads the family, the scope, and the first uptime. This function
        reads the site inventory once and fills every field, so the record that
        reaches the driver names a real device.

    Args:
        session: The cloud session of the signed-in operator.
        org_id: The organization that holds the site.
        site_id: The site under upgrade.
        body: The request body of the save call.

    Returns:
        A mapping with the ``targets`` entries, the ``options`` record, and the
        ``warnings`` list. An empty mapping when the site read named no device,
        which lets the caller keep the answer that the page already showed.

    Raises:
        BadOptionError: If one choice names an unknown device, an empty version,
            or an option value that no rule maps.
    """
    inventory = read_upgrade_inventory(session, org_id, site_id)
    if not inventory.records:  # A failed read must never look like a bad choice by the operator.
        logger.warning("Upgrade portal read no device of site %s, so the body carries the targets", site_id)
        return {}
    choices = body.get("targets")
    rows = [one for one in choices if isinstance(one, Mapping)] if isinstance(choices, list) else []
    selected_types = selected_device_types(body)
    by_model = read_model_versions(session, site_id, inventory.records, org_id) if rows else {}
    entries = build_targets(inventory.records, rows, by_model if rows else None, selected_types)
    return {
        "targets": entries,
        "options": asdict(build_options(body)),
        "selected_types": list(selected_types),
        "warnings": list(target_warnings(entries)),
    }


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
    "WARNING_NO_COMMON_CANDIDATE",
    "WARNING_SAME_VERSION",
    "BadOptionError",
    "InventoryRead",
    "TypedVersionSelector",
    "advanced_option_values",
    "build_option_record",
    "build_options",
    "build_options_record",
    "build_options_view",
    "build_target_entry",
    "build_targets",
    "safe_model_target",
    "selected_device_types",
    "build_version_options",
    "collect_models",
    "read_model_versions",
    "read_upgrade_inventory",
    "resolve_family_scope",
    "target_warnings",
    "to_device_targets",
]
