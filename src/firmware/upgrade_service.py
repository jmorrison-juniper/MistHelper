"""The upgrade seam between the capture portal and the Mist cloud.

Why:
    The four existing upgrade classes hold about 12000 lines, 1271 ``print``
    calls, and 80 ``input`` calls, so a web request cannot drive them. The
    module ``src/firmware/firmware_manager.py`` also holds four module globals
    at lines 34 to 37. The save-and-restore blocks at lines 1736 and 1797
    are not thread safe, so two web requests for two organizations corrupt each
    other. This module holds no module state and every value it needs arrives
    as a parameter, so several threads may call every function at once. The
    portal calls this module. The portal never calls ``firmware_manager``.

    Rule 4 of ``specs/1823-upgrade-capture-portal/contracts/upgrade-service.md``
    asks for an information log before an action and a debug log after it. Every
    public function obeys that rule. A private helper stays silent, because a
    helper runs inside an action that its public caller already logged, and a
    log line for each helper would bury the useful lines.

    Every module-level name below binds an immutable literal. The test at
    ``tests/unit/upgrade_portal/test_upgrade_service_prohibitions.py`` reads the
    syntax tree of this file and fails on any other module-level assignment.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from importlib import import_module
from typing import Any

SCOPE_SITE = "site"
SCOPE_ORG = "org"

# Decision (tasks.md open decision 4, closed here): ``UpgradePlan.endpoint``
# holds a literal string, not an enumeration member. The value is the name of a
# cloud function, ``_resolve_endpoint`` looks the name up in a fixed tuple, and a
# plain string travels through JSON to the browser with no conversion.
#
# The site scope offers two calls. ``upgradeSiteDevices`` takes a device list and
# the orchestration fields. ``upgradeDevice`` takes one device in the path and
# holds no orchestration field. ``_uses_the_per_device_call`` states when a group
# takes the second call, and issue #2007 holds the run that asked for it.
ENDPOINT_SITE_DEVICES = "upgradeSiteDevices"
ENDPOINT_SITE_DEVICE = "upgradeDevice"
ENDPOINT_ORG_SSRS = "upgradeOrgSsrs"

STRATEGY_DEFAULT = "big_bang"
STRATEGY_SERIAL = "serial"
STRATEGY_CANARY = "canary"
STRATEGY_RRM = "rrm"

# The word that asks the cloud for the vendor stable build instead of a named
# version (documentation/api/utilities/POST_sites_site_id_devices_upgrade.md:197).
VERSION_STABLE = "stable"

# The two enumerations that the radio resource management fields accept, from
# the same request body schema at lines 135 and 139.
MESH_UPGRADE_CHOICES = ("parallel", "sequential")
NODE_ORDER_CHOICES = ("center_to_fringe", "fringe_to_center")

# The strategy words that the batch site call accepts. The radio resource
# management word reaches an access point alone, and `_strategy_word` drops it
# for every other device type.
_AP_ONLY_STRATEGIES = (STRATEGY_RRM,)

# The complete strategy enumeration of the session smart router request body, from
# documentation/api/utilities/POST_orgs_org_id_ssr_upgrade.md:57. That schema
# lists two words and holds no canary strategy, so the body of that family
# carries one of these two words or no strategy field at all.
_SSR_STRATEGIES = (STRATEGY_DEFAULT, STRATEGY_SERIAL)

# The cloud accepts an upgrade with 200 or with 202 (bulk_switch_upgrader.py:967).
ACCEPTED_STATUS = (200, 202)

# A field that only an upgrade job carries. The organization-scope read of a
# session smart router calls ``listOrgDevicesStats`` and answers device
# statistics, which carry none of these names. A payload with none of them is
# not an upgrade job, so the portal cannot tell which device writes firmware.
_UPGRADE_JOB_KEYS = ("status", "current_phase", "targets", "reboot_in_progress", "upgrade_id")

# The cloud reboots an access point on its own, so only a switch and a gateway
# read the reboot field and the Junos file action field.
_JUNOS_DEVICE_TYPES = ("switch", "gateway")

# The two device type words that the reboot warnings read. The cloud spells the
# device type with these words in every device record.
DEVICE_TYPE_AP = "ap"
DEVICE_TYPE_SWITCH = "switch"

# The cloud default list, from the request body schema at
# documentation/api/utilities/POST_sites_site_id_devices_upgrade.md.
_CANARY_PHASES = (1, 10, 50, 100)

# The literal cloud key for the Junos file action. The house term for the record
# that this portal keeps is "capture", so no prose repeats this vendor key.
_JUNOS_FILE_ACTION_KEY = "snapshot"

# The value that disables the reboot of a session smart router
# (documentation/api/utilities/POST_orgs_org_id_ssr_upgrade.md:47).
_REBOOT_DISABLED = -1

# Mist builds the device identifier from the MAC address with this fixed prefix.
_DEVICE_ID_PREFIX = "00000000-0000-0000-1000-"
_MAC_LENGTH = 12

_WARNING_MIXED_FAMILY = "The selection mixes two gateway families, so the portal sends one call for each family."
_WARNING_MIXED_VERSION = "The selection holds more than one version, so the portal sends one call for each version."
_WARNING_SSR_STRATEGY = (
    "A session smart router accepts the strategy big_bang or serial only, "
    "so the portal sends no strategy for that family."
)

# WHY: The request body schema marks `rrm` as an access point word ("For APs
# only and if `strategy`==`rrm`" at every rrm field). An operator who picks the
# radio strategy for a mixed selection reads one control and gets two behaviors,
# so the plan must name the group that drops the word.
_WARNING_RRM_STRATEGY = (
    "The radio strategy reaches an access point only, "
    "so the portal sends no strategy for the switches and the gateways of this run."
)

# WHY: The stable choice replaces every version the operator picked in the
# device table. The table still shows those versions, so the operator would read
# one plan on the page and the cloud would run another.
_WARNING_STABLE_VERSION = (
    "The run asks the cloud for the vendor stable build, " "so the cloud ignores every version that this page shows."
)

# WHY: The cloud reboots an access point whatever this portal sends. The request
# body schema states it twice, at the `reboot` field of `upgrade_site_devices`
# and of `device_upgrade`: "For Switches and Gateways only (APs are
# automatically rebooted)". An operator who reads the reboot control and plans a
# window around it plans one that is too small, and the wireless service drops
# outside it.
#
# The sentence names the count, because a site of one switch and six access
# points reads as one reboot to plan and it is seven. Issue #2003 asks for the
# count for that reason. The caller fills the one field.
_WARNING_AP_ALWAYS_REBOOTS = (
    "The cloud reboots each of the {count} access point(s) of this run on its own. "
    "The reboot control reaches a switch and a gateway only."
)

# WHY: A run on 2026-08-24 sent `reboot: false` for one EX4100-F-12P through
# `upgradeSiteDevices`, and the switch installed the firmware and rebooted four
# seconds later. Six access points lost power over Ethernet with it. Issue #2007
# holds the event record. The gateway of the same site kept the choice, so the
# behavior differs by platform inside the batch path. Warn until a lab switch
# proves otherwise.
_WARNING_SWITCH_MAY_REBOOT = (
    "A switch may reboot even with the reboot control off. " "Plan a window for every switch of this run."
)

_MESSAGE_NO_CANCEL = "This device family offers no cancel call, so every device continues the upgrade."

# Every cloud function that this module may call, with the module that holds it.
# A name outside this tuple raises, so no caller can reach an endpoint that this
# module does not sanction. The tuple never holds getOrgSsrUpgrade, because
# mistapi 0.63.3 builds the cancel path inside that function.
_ENDPOINT_MODULES = (
    (ENDPOINT_SITE_DEVICES, "mistapi.api.v1.sites.devices"),
    (ENDPOINT_SITE_DEVICE, "mistapi.api.v1.sites.devices"),
    ("getSiteDeviceUpgrade", "mistapi.api.v1.sites.devices"),
    ("cancelSiteDeviceUpgrade", "mistapi.api.v1.sites.devices"),
    ("listSiteAvailableDeviceVersions", "mistapi.api.v1.sites.devices"),
    ("listOrgAvailableSsrVersions", "mistapi.api.v1.orgs.ssr"),
    ("searchSiteDeviceEvents", "mistapi.api.v1.sites.devices"),
    ("getSiteSsrUpgrade", "mistapi.api.v1.sites.ssr"),
    (ENDPOINT_ORG_SSRS, "mistapi.api.v1.orgs.ssr"),
    ("cancelOrgSsrUpgrade", "mistapi.api.v1.orgs.ssr"),
    ("getOrgDeviceUpgrade", "mistapi.api.v1.orgs.devices"),
    ("cancelOrgDeviceUpgrade", "mistapi.api.v1.orgs.devices"),
    ("listOrgDevicesStats", "mistapi.api.v1.orgs.stats"),
)


class GatewayFamily(StrEnum):
    """The two gateway families that need different cloud endpoints.

    Why:
        A Junos gateway rides the same site device upgrade call that a switch
        rides. A session smart router rides a separate endpoint family, and the
        installed SDK offers a cancel call for that family at organization scope
        only.

    Attributes:
        JUNOS: The device path, which carries an access point, a switch, and a
            Junos gateway.
        SSR: A session smart router.
    """

    JUNOS = "junos"
    SSR = "ssr"


@dataclass(frozen=True, slots=True)
class DeviceTarget:
    """One device that the operator selected for the upgrade.

    Why:
        The plan, the body, and the report read the same values, so one frozen
        record keeps them together and no thread can change them. The record
        holds seven fields, because the contract names seven fields at
        ``contracts/upgrade-service.md`` lines 42 to 50 and the portal builds the
        record by keyword.

    Attributes:
        mac: The MAC address in lower case with no separator.
        name: The device name.
        device_type: One of ``ap``, ``switch``, or ``gateway``.
        model: The device model string.
        version_before: The firmware version that the device runs now.
        version_target: The firmware version that the operator picked.
        site_id: The site that holds the device.
    """

    mac: str
    name: str
    device_type: str
    model: str
    version_before: str
    version_target: str
    site_id: str


@dataclass(frozen=True, slots=True)
class CanaryOptions:
    """The staged-upgrade settings of one run.

    Why:
        The cloud reads these three fields only when the strategy is not
        ``big_bang``, and ``max_failures`` only when the strategy is ``canary``.
        One record holds them together, so the option record stays readable and
        a caller sees at a glance which settings belong to a staged upgrade.

        Each field name is the literal cloud field name. A reader who compares
        this record against
        ``documentation/api/utilities/POST_sites_site_id_devices_upgrade.md``
        needs no translation table.

    Attributes:
        canary_phases: The percentage of devices of each phase, or ``None`` for
            the cloud default of 1, 10, 50, and 100.
        max_failures: The count of failures allowed inside each phase, or
            ``None`` to use the percentage instead. The cloud needs one entry
            for each phase.
        max_failure_percentage: The percentage of failures allowed across the
            whole upgrade, or ``None`` for the cloud default of 5.
    """

    canary_phases: tuple[int, ...] | None = None
    max_failures: tuple[int, ...] | None = None
    max_failure_percentage: int | None = None


@dataclass(frozen=True, slots=True)
class RrmOptions:
    """The radio resource management settings of an access point upgrade.

    Why:
        The cloud reads these five fields only for an access point and only when
        the strategy is ``rrm``. The strategy walks the radio neighbourhood in
        batches, so it keeps wireless coverage while the firmware moves.

    Attributes:
        rrm_first_batch_percentage: The percentage of access points of the first
            batch, or ``None`` for the cloud default.
        rrm_max_batch_percentage: The largest percentage of access points of any
            later batch, or ``None`` for the cloud default.
        rrm_mesh_upgrade: ``parallel`` or ``sequential`` for the mesh access
            points at the end of the run, or ``None`` for the cloud default.
        rrm_node_order: ``center_to_fringe`` or ``fringe_to_center``, or ``None``
            for the cloud default.
        rrm_slow_ramp: Whether each batch grows slowly, or ``None`` for the cloud
            default.
    """

    rrm_first_batch_percentage: int | None = None
    rrm_max_batch_percentage: int | None = None
    rrm_mesh_upgrade: str | None = None
    rrm_node_order: str | None = None
    rrm_slow_ramp: bool | None = None


@dataclass(frozen=True, slots=True)
class PeerToPeerOptions:
    """The access-point-to-access-point download settings of one run.

    Why:
        An access point can take the firmware from a neighbour instead of from
        the cloud. A site on a slow link finishes far sooner that way. The cloud
        reads these fields for an access point alone.

    Attributes:
        enable_p2p: Whether an access point may take the firmware from a
            neighbour.
        p2p_cluster_size: The count of access points of one download group, or
            ``None`` for the cloud default of 10.
        p2p_parallelism: The count of download groups that run together, or
            ``None`` for the cloud default.
    """

    enable_p2p: bool = False
    p2p_cluster_size: int | None = None
    p2p_parallelism: int | None = None


@dataclass(frozen=True, slots=True)
class UpgradeOptions:
    """The choices that the operator made for one upgrade run.

    Why:
        One frozen record carries every choice into the pure body builder, so no
        function reads a shared setting and no thread sees a half-changed value.

        The three advanced settings sit in their own records, because each one
        reaches the cloud only under its own condition. A flat record of
        eighteen fields would hide that rule and would break the five-item rule
        of the project.

    Attributes:
        reboot: Whether the cloud reboots the device. A switch and a gateway read
            the value. The cloud reboots an access point on its own.
        junos_file_action: Whether the cloud performs the Junos file action after
            the reboot. A Junos device reads the value.
        strategy: The cloud upgrade strategy.
        start_time: Epoch seconds for a delayed start, or ``None`` for now.
        reboot_at: Epoch seconds for a reboot that runs later than the write, or
            ``None`` to reboot as soon as the write ends. A switch and a gateway
            read the value.
        force: Whether the cloud writes the firmware even when the device already
            runs the chosen version.
        stable_version: Whether the cloud picks the vendor stable build instead
            of the version that the operator picked for each device.
        canary: The staged-upgrade settings.
        rrm: The radio resource management settings.
        peer_to_peer: The access-point-to-access-point download settings.
    """

    reboot: bool = True
    junos_file_action: bool = False
    strategy: str = STRATEGY_DEFAULT
    start_time: int | None = None
    reboot_at: int | None = None
    force: bool = False
    stable_version: bool = False
    canary: CanaryOptions = field(default_factory=CanaryOptions)
    rrm: RrmOptions = field(default_factory=RrmOptions)
    peer_to_peer: PeerToPeerOptions = field(default_factory=PeerToPeerOptions)


@dataclass(frozen=True, slots=True)
class PlanRoute:
    """The scope, the endpoint, and the path identifier of one cloud call.

    Why:
        A plan must carry the path identifier of its call, because
        ``upgradeSiteDevices`` takes a site identifier and ``upgradeOrgSsrs``
        takes an organization identifier. The contract table names five plan
        attributes and names no identifier, so this nested record carries the
        identifier and keeps the plan at the five attributes that the contract
        names.

    Attributes:
        scope: ``site`` or ``org``.
        endpoint: The name of the cloud function that the plan calls.
        scope_id: The site identifier or the organization identifier.
    """

    scope: str
    endpoint: str
    scope_id: str


@dataclass(frozen=True, slots=True)
class UpgradePlan:
    """One cloud upgrade call for one group of devices.

    Why:
        The portal shows the plan to the operator before the start, so the plan
        must hold the finished body and the warnings. The record is frozen, so
        the view that the operator confirmed is the record that the cloud call
        reads.

    Attributes:
        route: The scope, the endpoint, and the path identifier.
        targets: The devices of this group.
        body: The finished request body.
        warnings: Plain sentences for the operator.
    """

    route: PlanRoute
    targets: tuple[DeviceTarget, ...]
    body: Mapping[str, object]
    warnings: tuple[str, ...]

    @property
    def scope(self) -> str:
        """Return the scope of the call.

        Returns:
            ``site`` or ``org``.
        """
        return self.route.scope

    @property
    def endpoint(self) -> str:
        """Return the name of the cloud function that this plan calls.

        Returns:
            The cloud function name.
        """
        return self.route.endpoint


@dataclass(frozen=True, slots=True)
class UpgradeSubmission:
    """The result of one cloud upgrade call.

    Why:
        The portal must report the true answer of the cloud, so the record keeps
        the raw status code instead of a success flag. A caller reads the status
        and decides the retry, because this module never retries.

    Attributes:
        upgrade_id: The cloud identifier, or ``None`` when the cloud returned no
            identifier.
        scope: ``site`` or ``org``.
        accepted: The MAC addresses that the cloud accepted.
        rejected: Each rejected MAC address with its reason.
        raw_status: The HTTP status code.
    """

    upgrade_id: str | None
    scope: str
    accepted: tuple[str, ...]
    rejected: tuple[tuple[str, str], ...]
    raw_status: int


@dataclass(frozen=True, slots=True)
class CancelOutcome:
    """The result of one cancel call.

    Why:
        The cloud describes a cancel as best effort, so a single success flag
        would mislead the operator. The record separates the devices that
        stopped from the devices that may still finish the write.

    Attributes:
        cancelled: The MAC addresses that stopped.
        already_writing: The MAC addresses that may still finish the write.
        no_cancel_available: The MAC addresses of a family with no cancel call.
        message: One plain sentence for the operator.
    """

    cancelled: tuple[str, ...]
    already_writing: tuple[str, ...]
    no_cancel_available: tuple[str, ...]
    message: str


def _logger() -> logging.Logger:
    """Return the logger of this module.

    Why:
        A module-level logger object would be module state, and the contract
        forbids a module global at ``contracts/upgrade-service.md:206``. The
        standard library caches a logger by name, so this call is cheap.

    Returns:
        The logger that carries the name of this module.
    """
    return logging.getLogger(__name__)


def _resolve_endpoint(name: str) -> Any:
    """Return the cloud function that carries this name.

    Why:
        The import happens inside the call, so a test replaces this one function
        and reaches no network. The name list is a fixed tuple, so no caller can
        reach an endpoint that this module does not sanction.

    Args:
        name: The name of the cloud function.

    Returns:
        The cloud function.

    Raises:
        ValueError: If the name is not a sanctioned endpoint.
    """
    for candidate, module_name in _ENDPOINT_MODULES:
        if candidate == name:
            return getattr(import_module(module_name), name)
    raise ValueError(f"the endpoint {name} is not a sanctioned upgrade endpoint")


def _device_id(mac: str) -> str:
    """Build the Mist device identifier of one MAC address.

    Why:
        The request body names ``device_ids`` and the schema marks each item as a
        UUID. Mist builds that UUID from the MAC address with a fixed prefix, so
        the portal needs no extra cloud read to map a MAC address.

    Args:
        mac: The MAC address, with or without a separator.

    Returns:
        The device identifier that the cloud expects.

    Raises:
        ValueError: If the MAC address holds no twelve hexadecimal digits.
    """
    clean = "".join(character for character in mac.lower() if character in "0123456789abcdef")
    if len(clean) != _MAC_LENGTH:
        raise ValueError(f"a device MAC address needs {_MAC_LENGTH} hexadecimal digits")
    return f"{_DEVICE_ID_PREFIX}{clean}"


def _family_from_values(device_type: str, model: str) -> GatewayFamily:
    """Return the gateway family of one type value and one model value.

    Why:
        The grouping step reads the family for every target, and an information
        log for every device would bury the useful lines. This helper holds the
        test, and ``classify_gateway`` adds the log around it.

    Args:
        device_type: The device type value.
        model: The device model value.

    Returns:
        The gateway family.
    """
    normal_type = device_type.strip().lower()
    normal_model = model.strip().upper()
    is_ssr = normal_type == "ssr" or "SSR" in normal_model or "128T" in normal_model
    return GatewayFamily.SSR if is_ssr else GatewayFamily.JUNOS


def classify_gateway(device: Mapping[str, object]) -> GatewayFamily:
    """Return the gateway family of one device record.

    Why:
        A Junos gateway and a session smart router need different cloud calls.
        The one existing discriminator is ``_is_ssr_inventory_row`` at
        ``src/firmware/firmware_manager.py:2291``. This function repeats the same
        test with no module state, so a thread may call it at any time.

    Args:
        device: One device record with a ``type`` key and a ``model`` key.

    Returns:
        ``GatewayFamily.SSR`` for a session smart router, or
        ``GatewayFamily.JUNOS`` for every other gateway.
    """
    device_type = str(device.get("type", ""))
    model = str(device.get("model", ""))
    _logger().info("classify the gateway family of type %s and model %s", device_type, model)
    family = _family_from_values(device_type, model)
    _logger().debug("the gateway family is %s", family.value)
    return family


def _strategy_word(strategy: str, family: GatewayFamily, device_type: str = "") -> str | None:
    """Return the strategy word that one family and one device type accept.

    Why:
        The session smart router schema lists ``big_bang`` and ``serial`` alone.
        A body that carried the word ``canary`` to that family would send a value
        that the schema does not hold. The function drops the word instead of a
        change to ``big_bang``, because a silent change would run a strategy that
        the operator never asked for.

        The request body schema marks ``rrm`` as an access point word. The same
        rule applies to it: a switch group drops the word, and ``plan_upgrade``
        puts a warning on the plan.

    Args:
        strategy: The strategy that the operator chose.
        family: The gateway family of the group.
        device_type: The device type of the group. An empty text skips the
            access point check, which keeps every older caller working.

    Returns:
        The strategy word, or ``None`` when the group accepts no such word.
    """
    if family is GatewayFamily.SSR and strategy not in _SSR_STRATEGIES:
        return None
    if strategy in _AP_ONLY_STRATEGIES and device_type and device_type != DEVICE_TYPE_AP:
        return None  # A switch and a gateway hold no radio neighbourhood to walk.
    return strategy


def _uses_the_per_device_call(
    targets: Sequence[DeviceTarget],
    family: GatewayFamily,
    options: UpgradeOptions,
) -> bool:
    """Return whether this group takes the per-device upgrade endpoint.

    Why:
        The cloud offers two site-scope upgrade calls. ``upgradeSiteDevices``
        takes a device list and adds the orchestration fields ``strategy``,
        ``canary_phases``, and the peer-to-peer settings. ``upgradeDevice`` takes
        one device in the path, and its whole schema is ``reboot``,
        ``reboot_at``, ``snapshot``, ``start_time``, and ``version``. It carries
        no orchestration field at all.

        A run on 2026-08-24 sent ``reboot: false`` and ``strategy: big_bang``
        together for one switch through the batch call. The switch wrote the
        firmware and rebooted four seconds later, and six access points lost
        power over Ethernet with it. The gateway of the same call kept the
        choice. Issue #2007 holds the event record.

        That body named a reboot wave and no reboot in one breath, and no
        operator can tell which one the cloud reads. This function removes the
        contradiction for the one case where it can: a single device with the
        reboot control off. A group of one needs no wave, because every strategy
        word describes the order of several devices.

        The rule stays this narrow on purpose. A run that asks for a reboot has
        no contradiction to remove, and the batch call already serves it. A
        session smart router keeps the organization-scope call, because that
        family offers no per-device path and it is the only family with a cancel
        call at organization scope.

    Args:
        targets: The devices of one group.
        family: The gateway family of the group.
        options: The choices of the operator.

    Returns:
        True when the group holds one device, sits outside the session smart
        router family, and carries the reboot control off.
    """
    if options.reboot:  # A wave and a reboot agree, so the batch call stays.
        return False
    return len(targets) == 1 and family is not GatewayFamily.SSR


def _copy_present(body: dict[str, object], values: Mapping[str, object]) -> None:
    """Copy each named value that the operator set into one request body.

    Why:
        The contract asks the portal to omit an optional field unless the
        operator picks it. A body that carried ``None`` would send a null where
        the cloud expects a number, and the cloud refuses the whole call.

    Args:
        body: The body under construction. The function changes it in place.
        values: The cloud field name of each optional setting and its value.
    """
    for name, value in values.items():
        if value is not None:  # ``None`` means the operator left the control alone.
            body[name] = value


def _add_ssr_fields(body: dict[str, object], options: UpgradeOptions) -> None:
    """Add the reboot schedule of one session smart router body.

    Why:
        That schema holds no reboot flag. It disables a reboot with a
        ``reboot_at`` of -1 instead
        (documentation/api/utilities/POST_orgs_org_id_ssr_upgrade.md:47).

    Args:
        body: The body under construction. The function changes it in place.
        options: The choices of the operator.
    """
    if not options.reboot:  # The one way this schema holds a reboot back.
        body["reboot_at"] = _REBOOT_DISABLED
        return
    _copy_present(body, {"reboot_at": options.reboot_at})  # A separate reboot window.


def _add_junos_fields(body: dict[str, object], options: UpgradeOptions) -> None:
    """Add the reboot fields that a switch and a Junos gateway read.

    Why:
        The cloud rejects the reboot field and the Junos file action field on an
        access point, so only these two device types carry them. The schema
        reads ``reboot_at`` only when ``reboot`` is true, so a held reboot sends
        no window at all.

    Args:
        body: The body under construction. The function changes it in place.
        options: The choices of the operator.
    """
    body["reboot"] = options.reboot
    if options.junos_file_action:
        body[_JUNOS_FILE_ACTION_KEY] = True
    if options.reboot:  # A held reboot needs no window, and the cloud ignores one.
        _copy_present(body, {"reboot_at": options.reboot_at})


def _add_canary_fields(body: dict[str, object], options: UpgradeOptions) -> None:
    """Add the staged-upgrade fields of one batch body.

    Why:
        The request body schema reads ``canary_phases`` and ``max_failures``
        only for the canary strategy, and ``max_failure_percentage`` for every
        strategy above ``big_bang``. A field outside its own strategy makes the
        cloud refuse the whole call.

    Args:
        body: The body under construction. The function changes it in place.
        options: The choices of the operator.
    """
    canary = options.canary
    if options.strategy == STRATEGY_CANARY:
        body["canary_phases"] = list(canary.canary_phases or _CANARY_PHASES)  # The cloud default stays the default.
        _copy_present(body, {"max_failures": list(canary.max_failures) if canary.max_failures else None})
    if options.strategy != STRATEGY_DEFAULT:  # One write of every device allows no partial failure.
        _copy_present(body, {"max_failure_percentage": canary.max_failure_percentage})


def _add_access_point_fields(body: dict[str, object], options: UpgradeOptions) -> None:
    """Add the fields that an access point group alone reads.

    Why:
        The request body schema marks the peer-to-peer fields and every radio
        resource management field "For APs only". A switch body that carried one
        would send a field that its own platform never reads.

    Args:
        body: The body under construction. The function changes it in place.
        options: The choices of the operator.
    """
    peer = options.peer_to_peer
    if peer.enable_p2p:  # The two size fields reach the cloud only with the flag.
        body["enable_p2p"] = True
        _copy_present(body, {"p2p_cluster_size": peer.p2p_cluster_size, "p2p_parallelism": peer.p2p_parallelism})
    if options.strategy == STRATEGY_RRM:  # Every field of this record names its own cloud key.
        _copy_present(body, asdict(options.rrm))


def _add_orchestration_fields(body: dict[str, object], device_type: str, options: UpgradeOptions) -> None:
    """Add the batch-only orchestration fields of one body.

    Why:
        The per-device schema holds five fields and no orchestration field at
        all. Only the batch site call reads a phase list, a failure limit, the
        force flag, and the access point settings.

    Args:
        body: The body under construction. The function changes it in place.
        device_type: The device type of the group.
        options: The choices of the operator.
    """
    _add_canary_fields(body, options)
    if options.force:  # The cloud writes the firmware even onto a device that already runs it.
        body["force"] = True
    if device_type == DEVICE_TYPE_AP:
        _add_access_point_fields(body, options)


def _add_family_fields(
    body: dict[str, object],
    device_type: str,
    options: UpgradeOptions,
    family: GatewayFamily,
    one_device: bool = False,
) -> None:
    """Add the body fields that one device family and one endpoint read.

    Why:
        Three cloud schemas carry three different field sets, and a wrong field
        makes the cloud refuse the whole call. This function picks the set that
        matches the family and the endpoint, and each helper owns one set.

    Args:
        body: The body under construction. The function changes it in place.
        device_type: The device type of the group.
        options: The choices of the operator.
        family: The gateway family of the group.
        one_device: Whether the body travels to the per-device endpoint.
    """
    if family is GatewayFamily.SSR:
        _add_ssr_fields(body, options)
        return  # That schema reads no other field of this portal.
    if device_type in _JUNOS_DEVICE_TYPES:
        _add_junos_fields(body, options)
    if one_device:
        return  # The per-device schema holds no orchestration field at all.
    _add_orchestration_fields(body, device_type, options)


def build_body(
    targets: Sequence[DeviceTarget],
    options: UpgradeOptions,
    family: GatewayFamily,
) -> Mapping[str, object]:
    """Build the request body of one cloud upgrade call.

    Why:
        The body rules differ by device type and by family, and a wrong field
        makes the cloud refuse the whole call. This function is pure, so a test
        proves each rule with no cloud call. It sends no field that no body
        builder reads, because the access point upgrader sets a parallelism value
        that the cloud never reads (``src/firmware/bulk_ap_upgrader.py:1025``).
        The strategy field is absent when the family accepts no such word, and
        ``plan_upgrade`` puts a warning on the plan for that case.

    Args:
        targets: The devices of one group. Every device shares one target
            version, because ``plan_upgrade`` groups by version.
        options: The choices of the operator.
        family: The gateway family of the group.

    Returns:
        The finished request body.

    Raises:
        ValueError: If the target list is empty.
    """
    if not targets:
        raise ValueError("an upgrade body needs at least one target")
    one_device = _uses_the_per_device_call(targets, family, options)  # The small schema holds no list.
    _logger().info("build an upgrade body for %s target(s) of family %s", len(targets), family.value)
    device_type = targets[0].device_type  # One group holds one device type, so one row names it.
    version = VERSION_STABLE if options.stable_version else targets[0].version_target
    body: dict[str, object] = {"version": version}
    if not one_device:  # The batch call names every device, and the per-device call names it in the path.
        body["device_ids"] = [_device_id(target.mac) for target in targets]
        word = _strategy_word(options.strategy, family, device_type)
        if word is not None:
            body["strategy"] = word
    if options.start_time is not None:
        body["start_time"] = options.start_time
    _add_family_fields(body, device_type, options, family, one_device)
    _logger().debug("the upgrade body holds the keys %s", sorted(body))
    return body


def _group_targets(
    targets: Sequence[DeviceTarget],
) -> dict[tuple[str, GatewayFamily, str], tuple[DeviceTarget, ...]]:
    """Group the targets by device type, by gateway family, and by version.

    Why:
        The contract asks for a group for each device type and for each gateway
        family. This function adds the target version to the key, because one
        cloud body carries one version field and the portal lets the operator
        pick a version for each device. A group that mixed two versions would
        send the wrong firmware to half of the group.

    Args:
        targets: Every device that the operator selected.

    Returns:
        A map from the group key to the devices of the group.
    """
    groups: dict[tuple[str, GatewayFamily, str], list[DeviceTarget]] = {}
    for target in targets:
        family = _family_from_values(target.device_type, target.model)
        key = (target.device_type, family, target.version_target)
        groups.setdefault(key, []).append(target)
    return {key: tuple(members) for key, members in groups.items()}


def _drops_the_strategy(
    keys: tuple[tuple[str, GatewayFamily, str], ...],
    options: UpgradeOptions,
) -> bool:
    """Return whether one group of this plan sends no strategy field.

    Why:
        The warning must appear once for the whole plan, so the test reads every
        group key instead of one body. A caller that read a body could not tell a
        dropped word from a word that the operator never chose.

    Args:
        keys: The group keys of the plan.
        options: The choices of the operator.

    Returns:
        True when at least one group drops the chosen strategy word.
    """
    families = {key[1] for key in keys}
    return GatewayFamily.SSR in families and _strategy_word(options.strategy, GatewayFamily.SSR) is None


def _reboot_warnings(
    keys: tuple[tuple[str, GatewayFamily, str], ...],
    options: UpgradeOptions,
    access_points: int,
) -> list[str]:
    """Return the sentences that name a reboot the operator did not ask for.

    Why:
        The reboot control is the one promise this feature makes about the
        moment of disruption. Two device families break that promise, and an
        operator who plans a window from the control alone plans the wrong one.

        An access point always reboots, because the cloud drives it. That
        sentence appears whenever the operator plans a window, which is either a
        run with the reboot control off or a run with a start time. Both choices
        say that the operator picked the moment of the disruption, and for an
        access point the cloud picks it instead. A site of one switch and six
        access points reads as one reboot to plan and it is seven, so the
        sentence names the count. Issue #2003 holds that report.

        A switch rebooted once with the control off, and issue #2007 holds the
        event record. That sentence appears only for a run with the control off,
        because a run that reboots on purpose has nothing to learn from it.

    Args:
        keys: The group keys of the plan.
        options: The choices of the operator.
        access_points: The number of access points in the whole selection.

    Returns:
        Zero, one, or two sentences.
    """
    plans_a_window = not options.reboot or options.start_time is not None  # Either choice picks a moment.
    found: list[str] = []
    if access_points and plans_a_window:  # The cloud reboots an access point whatever the body says.
        found.append(_WARNING_AP_ALWAYS_REBOOTS.format(count=access_points))
    if not options.reboot and DEVICE_TYPE_SWITCH in {key[0] for key in keys}:  # Measured on 2026-08-24.
        found.append(_WARNING_SWITCH_MAY_REBOOT)
    return found


def _advanced_warnings(
    keys: tuple[tuple[str, GatewayFamily, str], ...],
    options: UpgradeOptions,
) -> list[str]:
    """Return the sentences that name an advanced choice the cloud changes.

    Why:
        Two advanced controls apply to a narrower set than the page suggests.
        The radio strategy reaches an access point alone, and the stable choice
        replaces every version that the device table shows. An operator who
        reads the control and never reads the limit plans the wrong run.

    Args:
        keys: The group keys of the plan.
        options: The choices of the operator.

    Returns:
        Zero, one, or two sentences.
    """
    found: list[str] = []
    other_types = {key[0] for key in keys} - {DEVICE_TYPE_AP}  # Every group that holds no access point.
    if options.strategy == STRATEGY_RRM and other_types:  # The word never reaches those groups.
        found.append(_WARNING_RRM_STRATEGY)
    if options.stable_version:  # The picked versions of the device table never reach the cloud.
        found.append(_WARNING_STABLE_VERSION)
    return found


def _plan_warnings(
    keys: Iterable[tuple[str, GatewayFamily, str]],
    options: UpgradeOptions,
    access_points: int = 0,
) -> tuple[str, ...]:
    """Return the plain sentences that the operator reads before the start.

    Why:
        The operator picks one list of devices and expects one action. The portal
        may send several calls, so the operator must see the split first. The
        operator also picks one strategy for the whole selection, so the operator
        must learn that a session smart router group drops a word that its schema
        does not hold.

        The operator also picks one reboot choice, and two device families do not
        keep it. `_reboot_warnings` names those, because a window planned from a
        control that does not hold is worse than no plan at all.

    Args:
        keys: The group keys of the plan.
        options: The choices of the operator.
        access_points: The number of access points in the whole selection.

    Returns:
        One sentence for each split, for each dropped strategy, and for each
        family that reboots against the choice of the operator.
    """
    key_list = tuple(keys)
    warnings: list[str] = []
    if len({key[1] for key in key_list}) > 1:
        warnings.append(_WARNING_MIXED_FAMILY)
    if len({key[2] for key in key_list}) > 1:
        warnings.append(_WARNING_MIXED_VERSION)
    if _drops_the_strategy(key_list, options):
        warnings.append(_WARNING_SSR_STRATEGY)
    warnings.extend(_advanced_warnings(key_list, options))
    warnings.extend(_reboot_warnings(key_list, options, access_points))
    return tuple(warnings)


def _build_plan(
    key: tuple[str, GatewayFamily, str],
    members: tuple[DeviceTarget, ...],
    options: UpgradeOptions,
    identifiers: tuple[str, str],
    warnings: tuple[str, ...],
) -> UpgradePlan:
    """Build one plan for one group of targets.

    Why:
        A session smart router always uses the organization scope, because the
        installed SDK offers ``cancelOrgSsrUpgrade`` and offers no site-scope
        cancel for that family. A run that started at site scope would have no
        way to stop, which FR-038 forbids.

        A group of one device outside that family uses the per-device endpoint
        when the operator turned the reboot control off.
        `_uses_the_per_device_call` states why. The cancel call stays the same,
        because `_cancel_endpoint_name` reads the scope and this plan keeps the
        site scope.

    Args:
        key: The device type, the gateway family, and the target version.
        members: The devices of the group.
        options: The choices of the operator.
        identifiers: The organization identifier and the site identifier.
        warnings: The sentences for the operator.

    Returns:
        One finished plan.
    """
    is_ssr = key[1] is GatewayFamily.SSR
    one_device = _uses_the_per_device_call(members, key[1], options)  # Decides between the two site calls.
    site_endpoint = ENDPOINT_SITE_DEVICE if one_device else ENDPOINT_SITE_DEVICES
    route = PlanRoute(
        scope=SCOPE_ORG if is_ssr else SCOPE_SITE,
        endpoint=ENDPOINT_ORG_SSRS if is_ssr else site_endpoint,
        scope_id=identifiers[0] if is_ssr else identifiers[1],
    )
    body = build_body(members, options, key[1])
    return UpgradePlan(route=route, targets=members, body=body, warnings=warnings)


def plan_upgrade(
    targets: Sequence[DeviceTarget],
    options: UpgradeOptions,
    org_id: str,
    site_id: str,
) -> tuple[UpgradePlan, ...]:
    """Group the targets and return one plan for each group.

    Why:
        The cloud offers one call for each family and scope, so a mixed selection
        needs several calls. The function is pure and performs no cloud call, so
        the portal shows the whole plan to the operator before anything starts.

    Args:
        targets: Every device that the operator selected.
        options: The choices of the operator.
        org_id: The organization identifier for a session smart router call.
        site_id: The site identifier for a device call.

    Returns:
        One plan for each group.
    """
    _logger().info("plan an upgrade for %s target(s)", len(targets))
    groups = _group_targets(targets)
    access_points = sum(1 for target in targets if target.device_type == DEVICE_TYPE_AP)  # The count the warning names.
    warnings = _plan_warnings(groups, options, access_points)
    identifiers = (org_id, site_id)
    plans = tuple(_build_plan(key, members, options, identifiers, warnings) for key, members in groups.items())
    _logger().debug("the plan holds %s cloud call(s)", len(plans))
    return plans


def _status_code(response: Any) -> int:
    """Read the HTTP status code of one cloud answer.

    Why:
        A cloud answer may carry no status code, and this module never raises for
        a cloud error, so a missing code must read as zero.

    Args:
        response: The cloud answer.

    Returns:
        The status code, or zero when the answer carries none.
    """
    try:
        return int(getattr(response, "status_code", 0))
    except (TypeError, ValueError):
        return 0


def _upgrade_id(response: Any) -> str | None:
    """Read the upgrade identifier of one cloud answer.

    Why:
        The device upgrade answer names the identifier ``upgrade_id``, and the
        session smart router answer names it ``id``. One reader covers both, so
        the caller never learns the difference.

    Args:
        response: The cloud answer.

    Returns:
        The identifier, or ``None`` when the answer carries none.
    """
    data = getattr(response, "data", None)
    if not isinstance(data, Mapping):
        return None
    value = data.get("upgrade_id") or data.get("id")
    return str(value) if value else None


def _read_submission(response: Any, plan: UpgradePlan) -> UpgradeSubmission:
    """Turn one cloud answer into a submission record.

    Why:
        The cloud answers with one status for the whole call, so every MAC
        address of the plan shares the outcome of that status.

    Args:
        response: The cloud answer.
        plan: The plan that produced the call.

    Returns:
        The submission record.
    """
    status = _status_code(response)
    macs = tuple(target.mac for target in plan.targets)
    accepted = status in ACCEPTED_STATUS
    reason = f"the cloud answered status {status}"
    return UpgradeSubmission(
        upgrade_id=_upgrade_id(response),
        scope=plan.scope,
        accepted=macs if accepted else (),
        rejected=() if accepted else tuple((mac, reason) for mac in macs),
        raw_status=status,
    )


def _validate_plan(plan: UpgradePlan) -> None:
    """Raise when a plan cannot reach the cloud.

    Why:
        The contract lets this function raise for a malformed plan and forbids a
        raise for a cloud error. The check runs before the call, so the two cases
        never mix.

    Args:
        plan: The plan to check.

    Raises:
        ValueError: If the plan holds no target, no identifier, no device
            identifier, or an unknown scope.
    """
    if not plan.targets:
        raise ValueError("an upgrade plan needs at least one target")
    if not plan.route.scope_id:
        raise ValueError("an upgrade plan needs a site or organization identifier")
    if plan.endpoint == ENDPOINT_SITE_DEVICE:  # The path names the device, so the body names none.
        if len(plan.targets) != 1:
            raise ValueError("the per-device upgrade endpoint takes exactly one target")
    elif not plan.body.get("device_ids"):
        raise ValueError("an upgrade plan needs at least one device identifier")
    if plan.scope not in (SCOPE_SITE, SCOPE_ORG):
        raise ValueError("an upgrade plan needs the scope site or the scope org")


def _send_plan(session: Any, plan: UpgradePlan) -> Any:
    """Perform the one cloud call of one plan.

    Why:
        The two site-scope endpoints take a different number of path values.
        ``upgradeSiteDevices`` names the site and reads the device list from the
        body. ``upgradeDevice`` names the site and the device, and its body holds
        no list. One function holds that difference, so `invoke_upgrade` keeps
        one shape for every plan.

    Args:
        session: The Mist API session. The caller owns it.
        plan: The plan to submit.

    Returns:
        The raw cloud answer.
    """
    call = _resolve_endpoint(plan.endpoint)  # Raises for any name outside the sanctioned tuple.
    if plan.endpoint == ENDPOINT_SITE_DEVICE:  # The device identifier travels in the path, not the body.
        return call(session, plan.route.scope_id, _device_id(plan.targets[0].mac), dict(plan.body))
    return call(session, plan.route.scope_id, dict(plan.body))


def invoke_upgrade(session: Any, plan: UpgradePlan) -> UpgradeSubmission:
    """Send one plan to the cloud and return the submission record.

    Why:
        The seam performs exactly one cloud call and never retries, because the
        caller owns the retry policy and a hidden retry would start a second
        upgrade. The function never raises for a cloud error status, so the
        portal can report the true answer to the operator.

        Decision (tasks.md open decision 3, closed here): the seam carries no
        dry-run parameter. ``plan_upgrade`` and ``build_body`` are pure and reach
        no cloud, so a caller that wants a preview builds the plan and shows it.

    Args:
        session: The Mist API session. The caller owns it.
        plan: The plan to submit.

    Returns:
        The submission record with the raw status code.

    Raises:
        ValueError: If the plan is malformed.
    """
    _validate_plan(plan)
    _logger().info("submit %s for %s device(s) at %s scope", plan.endpoint, len(plan.targets), plan.scope)
    response = _send_plan(session, plan)
    submission = _read_submission(response, plan)
    _logger().debug("the cloud answered status %s and upgrade %s", submission.raw_status, submission.upgrade_id)
    return submission


def _cancel_endpoint_name(plan: UpgradePlan) -> str:
    """Return the cancel endpoint that matches the scope and the family.

    Why:
        The three cancel calls sit in three modules, and the right one follows
        from the endpoint that started the run. An unknown plan returns an empty
        name, so the caller reports the case of FR-038f instead of guessing.

    Args:
        plan: The plan that started the run.

    Returns:
        The endpoint name, or an empty string when no cancel call exists.
    """
    if plan.endpoint == ENDPOINT_ORG_SSRS:
        return "cancelOrgSsrUpgrade"
    if plan.scope == SCOPE_SITE:
        return "cancelSiteDeviceUpgrade"
    if plan.scope == SCOPE_ORG:
        return "cancelOrgDeviceUpgrade"
    return ""


def _normalize_mac(value: object) -> str:
    """Return one MAC address in lower case with no separator.

    Why:
        The cloud writes a MAC address with colons, with dashes, or with no
        separator at all, and in either letter case. Two spellings of one
        address must compare equal. Three call sites once held three different
        rules, and a MAC address written with dashes matched none of them.

    Args:
        value: One MAC address in any spelling.

    Returns:
        The address in lower case with no separator.
    """
    return str(value).replace(":", "").replace("-", "").lower()


def _holds_upgrade_job(status: Mapping[str, object] | None) -> bool:
    """Report whether one payload is an upgrade job that the portal can read.

    Why:
        A payload that is not an upgrade job holds no reboot list, and an
        absent list must never read as an empty list. The reader also honors an
        explicit ``status_known`` of false, because a status that already
        passed through ``_normalize_status`` carries the answer in that field
        instead of in the shape of the payload.

    Args:
        status: The payload of a status read, or ``None``.

    Returns:
        True when the payload is an upgrade job.
    """
    if status is None or status.get("status_known") is False:
        return False
    return any(key in status for key in _UPGRADE_JOB_KEYS)


def _reboot_macs(status: Mapping[str, object] | None) -> frozenset[str] | None:
    """Return the MAC addresses that the last status marked as rebooting.

    Why:
        The cloud holds ``reboot_in_progress`` as a list of MAC addresses, not as
        a boolean. A truth test on the value would mark every device as writing
        firmware. The cloud writes the list at the top level or inside
        ``targets``, so the reader looks at both places.

        An answer of ``None`` means that the portal cannot tell. An empty set
        would claim that no device writes firmware, and the caller would then
        report every device as stopped. An operator who reads the word stopped
        can cut power to a switch that is still writing firmware.

    Args:
        status: The last status that the portal read, or ``None``.

    Returns:
        The MAC addresses in lower case with no separator, or ``None`` when the
        portal cannot tell which devices write firmware.
    """
    if not _holds_upgrade_job(status) or status is None:
        return None
    values = status.get("reboot_in_progress")
    if values is None:
        targets = status.get("targets")
        values = targets.get("reboot_in_progress") if isinstance(targets, Mapping) else None
    if values is None:
        return frozenset()  # The job exists and it names no device, so no device writes firmware.
    if isinstance(values, str) or not isinstance(values, Sequence):
        return None  # The field holds a shape the portal does not understand.
    return frozenset(_normalize_mac(value) for value in values)


def _cancel_message(stopped: int, already: int) -> str:
    """Return one plain sentence about the result of a cancel.

    Why:
        The cloud describes a cancel as best effort, so the operator needs a
        sentence that names both counts instead of the word success.

    Args:
        stopped: The number of devices that stopped.
        already: The number of devices that may still finish the write.

    Returns:
        One sentence.
    """
    if already:
        return f"The cloud stopped {stopped} device(s), and {already} device(s) may still finish the write."
    return f"The cloud stopped {stopped} device(s), and no device was writing firmware."


def _unknown_state_message(count: int) -> str:
    """Return the sentence for a cancel that read no device state.

    Why:
        The cloud accepted the cancel, but the portal could not read which
        devices were writing firmware. The operator must not read the word
        stopped here. A switch that loses power in mid-write does not start
        again, so the sentence names the doubt and names the safe action.

    Args:
        count: The number of devices in the plan.

    Returns:
        Three short sentences.
    """
    return (
        f"The cloud accepted the cancel for {count} device(s). "
        "The portal could not read which devices were writing firmware. "
        "Treat every one of them as a device that may still finish the write."
    )


def _sort_cancel(macs: tuple[str, ...], last_status: Mapping[str, object] | None, status: int) -> CancelOutcome:
    """Sort the MAC addresses of one cancel into the three groups.

    Why:
        A refused cancel leaves every device running, so the portal must not
        report a stop that never happened. An unreadable device state is the
        same case. Every device then joins ``already_writing``, which the
        contract defines as the devices that may still finish the write.

    Args:
        macs: The MAC addresses of the plan.
        last_status: The last upgrade status that the portal read.
        status: The HTTP status code of the cancel call.

    Returns:
        The cancel outcome.
    """
    if status not in ACCEPTED_STATUS:
        refused = f"The cloud refused the cancel with status {status}, so every device continues the upgrade."
        return CancelOutcome((), macs, (), refused)
    writing = _reboot_macs(last_status)
    if writing is None:
        return CancelOutcome((), macs, (), _unknown_state_message(len(macs)))
    already = tuple(mac for mac in macs if _normalize_mac(mac) in writing)
    stopped = tuple(mac for mac in macs if _normalize_mac(mac) not in writing)
    return CancelOutcome(stopped, already, (), _cancel_message(len(stopped), len(already)))


def cancel_upgrade(
    session: Any,
    plan: UpgradePlan,
    upgrade_id: str,
    last_status: Mapping[str, object] | None = None,
) -> CancelOutcome:
    """Ask the cloud to cancel one upgrade.

    Why:
        The cloud describes the cancel as best effort. A device that already
        upgraded stays untouched, and a device in mid-flash may still complete.
        The contract signature names three parameters and asks the function to
        sort each MAC address from the status that the portal read last, so the
        fourth parameter carries that status. The parameter has a default, so
        every three-argument call still works.

    Args:
        session: The Mist API session. The caller owns it.
        plan: The plan that started the run.
        upgrade_id: The cloud identifier of the run.
        last_status: The last status that the portal read, or ``None``.

    Returns:
        The cancel outcome with one plain sentence for the operator.
    """
    macs = tuple(target.mac for target in plan.targets)
    name = _cancel_endpoint_name(plan)
    _logger().info("cancel upgrade %s for %s device(s) through %s", upgrade_id, len(macs), name or "no call")
    if not name:
        _logger().debug("the family of this plan offers no cancel call")
        return CancelOutcome((), (), macs, _MESSAGE_NO_CANCEL)
    response = _resolve_endpoint(name)(session, plan.route.scope_id, upgrade_id)
    outcome = _sort_cancel(macs, last_status, _status_code(response))
    _logger().debug("the cancel stopped %s of %s device(s)", len(outcome.cancelled), len(macs))
    return outcome


def _call_status(
    session: Any,
    scope: str,
    identifier: str,
    upgrade_id: str,
    family: GatewayFamily,
) -> Any:
    """Perform the one cloud read that matches the scope and the family.

    Why:
        This module never calls ``getOrgSsrUpgrade``, because mistapi 0.63.3
        builds the cancel path inside that function at
        ``mistapi/api/v1/orgs/ssr.py:167``, so the read would post to the cancel
        path. The organization-scope read of that family reads the device
        statistics instead.

    Args:
        session: The Mist API session.
        scope: ``site`` or ``org``.
        identifier: The site identifier or the organization identifier.
        upgrade_id: The cloud identifier of the run.
        family: The gateway family of the run.

    Returns:
        The cloud answer.
    """
    if family is GatewayFamily.SSR and scope == SCOPE_ORG:
        return _resolve_endpoint("listOrgDevicesStats")(session, identifier, "gateway")
    if family is GatewayFamily.SSR:
        return _resolve_endpoint("getSiteSsrUpgrade")(session, identifier, upgrade_id)
    name = "getOrgDeviceUpgrade" if scope == SCOPE_ORG else "getSiteDeviceUpgrade"
    return _resolve_endpoint(name)(session, identifier, upgrade_id)


def _payload(response: Any) -> Mapping[str, object]:
    """Return the mapping body of one cloud answer.

    Why:
        The upgrade reads answer with a mapping, and the device statistics read
        answers with a list. One reader returns a mapping for both, so the caller
        needs no type test.

    Args:
        response: The cloud answer.

    Returns:
        The mapping body, or a mapping with the key ``devices`` for a list.
    """
    data = getattr(response, "data", None)
    if isinstance(data, Mapping):
        return {str(key): value for key, value in data.items()}
    if isinstance(data, list):
        return {"devices": data}
    return {}


def _normalize_status(payload: Mapping[str, object], upgrade_id: str, raw_status: int) -> Mapping[str, object]:
    """Return the status fields that the portal reads, under their true names.

    Why:
        The cloud names the phase field ``current_phase``, not ``phase``, and it
        holds ``reboot_in_progress`` as a list of MAC addresses. A caller that
        read ``phase``, or that tested ``reboot_in_progress`` for truth, would
        report the wrong state. The whole payload reaches the reboot reader, so a
        list at the top level and a list inside ``targets`` both report a device.
        The ``start_time`` field is the absolute anchor of the run. The vendor
        calls it the epoch moment when the firmware download started.

        The ``status_known`` field states whether the answer was an upgrade job
        at all. The organization-scope read of a session smart router answers
        device statistics, which name no device that writes firmware. Without
        this field a later reader would see an empty list and would report every
        device as stopped.

    Args:
        payload: The mapping body of the cloud answer.
        upgrade_id: The cloud identifier of the run.
        raw_status: The HTTP status code of the read.

    Returns:
        The status fields.
    """
    raw_targets = payload.get("targets")
    targets = raw_targets if isinstance(raw_targets, Mapping) else {}
    reboot = _reboot_macs(payload)
    return {
        "upgrade_id": upgrade_id,
        "raw_status": raw_status,
        "status": str(payload.get("status", "")),
        "current_phase": payload.get("current_phase"),
        "reboot_in_progress": tuple(sorted(reboot or ())),
        "status_known": reboot is not None,
        "start_time": payload.get("start_time"),  # The epoch moment that anchors every later reading.
        "targets": targets,
    }


def read_upgrade_status(
    session: Any,
    scope: str,
    identifier: str,
    upgrade_id: str,
    family: GatewayFamily = GatewayFamily.JUNOS,
) -> Mapping[str, object]:
    """Read the status of one upgrade.

    Why:
        The portal polls this function every 30 seconds, so the reader must name
        every field exactly as the cloud names it. The contract signature names
        four parameters, but the scope alone does not name the cloud function for
        a session smart router, so the fifth parameter carries the family. The
        parameter has a default, so every four-argument call still works.

    Args:
        session: The Mist API session. The caller owns it.
        scope: ``site`` or ``org``.
        identifier: The site identifier or the organization identifier.
        upgrade_id: The cloud identifier of the run.
        family: The gateway family of the run.

    Returns:
        The status fields, with ``current_phase`` and with
        ``reboot_in_progress`` as a tuple of MAC addresses.
    """
    _logger().info("read the status of upgrade %s at %s scope", upgrade_id, scope)
    response = _call_status(session, scope, identifier, upgrade_id, family)
    status = _normalize_status(_payload(response), upgrade_id, _status_code(response))
    _logger().debug("the upgrade reports state %s and phase %s", status["status"], status["current_phase"])
    return status


def _rows(response: Any) -> tuple[Mapping[str, object], ...]:
    """Return the row list of one cloud answer.

    Why:
        The version read answers with a list of rows, and a cloud error answers
        with no list. One reader returns an empty tuple for the error, so the
        caller needs no type test.

    Args:
        response: The cloud answer.

    Returns:
        The rows of the answer.
    """
    data = getattr(response, "data", None)
    if not isinstance(data, list):
        return ()
    return tuple(row for row in data if isinstance(row, Mapping))


def _group_versions(
    rows: tuple[Mapping[str, object], ...],
    wanted: frozenset[str],
) -> Mapping[str, tuple[str, ...]]:
    """Group the version rows by model.

    Why:
        The cloud returns one flat row for each model and version pair, and the
        portal shows one version list for each model.

    Args:
        rows: The rows of the cloud answer.
        wanted: The models that the caller asked for, in upper case. An empty set
            keeps every model.

    Returns:
        The version list of each model.
    """
    grouped: dict[str, list[str]] = {}
    for row in rows:
        model = str(row.get("model", "")).strip()
        version = str(row.get("version", "")).strip()
        if not model or not version or (wanted and model.upper() not in wanted):
            continue
        grouped.setdefault(model, []).append(version)
    return {model: tuple(versions) for model, versions in grouped.items()}


def _version_requests(
    devices: Iterable[Mapping[str, object]],
) -> tuple[tuple[str, str], ...]:
    """Return the unique device type and model pairs for version reads."""
    requests = {
        (
            str(device.get("device_type", device.get("type", ""))).strip().lower(),
            str(device.get("model", "")).strip(),
        )
        for device in devices
    }
    return tuple(sorted((device_type, model) for device_type, model in requests if device_type and model))


def _ssr_models(devices: Iterable[Mapping[str, object]]) -> tuple[str, ...]:
    """Return the unique SSR models that require the organization version endpoint."""
    models = {
        str(device.get("model", "")).strip() for device in devices if classify_gateway(device) is GatewayFamily.SSR
    }
    models.discard("")
    return tuple(sorted(models))


def _version_rows(
    session: Any,
    site_id: str,
    requests: Iterable[tuple[str, str]],
) -> tuple[Mapping[str, object], ...]:
    """Read the device-version endpoint for the supplied non-SSR models."""
    endpoint = _resolve_endpoint("listSiteAvailableDeviceVersions")
    return tuple(
        row
        for device_type, model in requests
        for row in _rows(endpoint(session, site_id, type=device_type, model=model))
    )


def _ssr_versions(session: Any, org_id: str, models: Iterable[str]) -> Mapping[str, tuple[str, ...]]:
    """Map organization-level SSR versions to each SSR model in the selected site."""
    endpoint = _resolve_endpoint("listOrgAvailableSsrVersions")
    versions = tuple(
        dict.fromkeys(
            str(row.get("version", "")).strip() for row in _rows(endpoint(session, org_id)) if row.get("version")
        )
    )
    return {model: versions for model in models if versions}


def list_available_versions(
    session: Any,
    site_id: str,
    devices: Iterable[Mapping[str, object]],
    org_id: str | None = None,
) -> Mapping[str, tuple[str, ...]]:
    """Return the version list of each model at one site.

    Why:
        The cloud defaults the device endpoint to access points when the request
        omits the device type. Each non-SSR request names both the type and the
        model. SSR devices use their dedicated organization endpoint, whose rows
        have a version but no model, so its version list maps to each SSR model.

        The local API contract at
        ``documentation/api/utilities/GET_sites_site_id_devices_versions.md``
        defines ``type`` and ``model`` query parameters. It specifically requires
        their combined use for switch and gateway devices.

    Args:
        session: The Mist API session. The caller owns it.
        site_id: The site identifier.
        devices: The device records that name each device type and model.
        org_id: The organization identifier needed for SSR version discovery.

    Returns:
        The version list of each model.
    """
    device_rows = tuple(devices)
    requests = _version_requests(device for device in device_rows if classify_gateway(device) is not GatewayFamily.SSR)
    ssr_models = _ssr_models(device_rows)
    wanted = frozenset(model.upper() for _, model in requests)
    _logger().info(
        "read the available versions of %s device model(s) at site %s",
        len(requests) + len(ssr_models),
        site_id,
    )
    grouped = dict(_group_versions(_version_rows(session, site_id, requests), wanted))
    if ssr_models and org_id:
        grouped.update(_ssr_versions(session, org_id, ssr_models))
    elif ssr_models:
        _logger().warning("cannot read SSR versions without the organization identifier")
    _logger().debug("the cloud returned versions for %s model(s)", len(grouped))
    return grouped
