"""The plan of each device and of the whole fleet through a rehearsal.

Why:
    The stand-in cloud answers from a script and holds no rule of its own. A
    script states when one device reconnects and when its version changes. The
    shipped settle gate then decides whether that story proves a reboot.

    Section 2 and section 3 of ``data-model.md`` state every field and every
    rule of this module.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)  # The module logger, so each build carries this name.

# WHY: The three device families that the cascade drives. The gateway family
# also carries the session smart router, because the shipped driver sorts a
# router into the gateway phase.
TYPE_GATEWAY: str = "gateway"
TYPE_SWITCH: str = "switch"
TYPE_ACCESS_POINT: str = "ap"

# WHY: The two firmware versions of the rehearsal. A changed version is one of
# the two facts that ``gate._note_reboot`` needs, so the pair must differ.
VERSION_BEFORE: str = "0.14.29562"
VERSION_AFTER: str = "0.14.30606"

# WHY: An uptime that falls proves a reboot on its own. The value is about
# eleven days, which is a plausible reading for a site device.
UPTIME_BEFORE_SECONDS: int = 950000


@dataclass(frozen=True, slots=True)
class DeviceScript:
    """The plan of one device through the rehearsal.

    Attributes:
        mac: The address in lower case with no separator.
        device_type: One of ``gateway``, ``switch``, or ``ap``.
        version_before: The firmware version before the upgrade.
        version_after: The firmware version after the upgrade.
        uptime_before: The uptime in seconds before the reboot.
        reconnect_at: The offset of the reconnect event from the run start.
        version_at: The offset of the version change from the run start.
        uptime_reset_at: The offset of the uptime fall, or None to follow
            ``version_at``. A later value scripts the cloud that publishes the
            target version before the device reboots.
    """

    mac: str
    device_type: str
    version_before: str = VERSION_BEFORE
    version_after: str = VERSION_AFTER
    uptime_before: int = UPTIME_BEFORE_SECONDS
    reconnect_at: float = 40.0
    version_at: float = 40.0
    uptime_reset_at: float | None = None

    @property
    def reboot_moment(self) -> float:
        """Return the offset at which the uptime counter restarts.

        Returns:
            The scripted reset offset, or the version offset when none is set.
        """
        return self.version_at if self.uptime_reset_at is None else self.uptime_reset_at  # One rule, one line.

    def version_of(self, elapsed: float) -> str:
        """Return the version that the cloud reports at one offset.

        Args:
            elapsed: The seconds since the run started.

        Returns:
            The version before the change, or the version after it.
        """
        return self.version_after if elapsed >= self.version_at else self.version_before  # One rule, one line.

    def uptime_of(self, elapsed: float) -> int:
        """Return the uptime that the cloud reports at one offset.

        Why:
            ``gate.uptime_decreased`` proves a reboot from a fall in this
            reading, so the value must fall at the moment of the version change.

        Args:
            elapsed: The seconds since the run started.

        Returns:
            The uptime in seconds.
        """
        if elapsed < self.reboot_moment:  # Before the reboot the device keeps counting up.
            return self.uptime_before + int(elapsed)  # A rising reading proves no reboot.
        return int(elapsed - self.reboot_moment) + 1  # After the reboot the counter restarts near zero.


@dataclass(frozen=True, slots=True)
class FleetScript:
    """The scripts of every device of one rehearsal run.

    Attributes:
        scripts: One script for each device of the fleet.
        started_at: The clock reading at the start of the run.
    """

    scripts: tuple[DeviceScript, ...] = field(default_factory=tuple)
    started_at: float = 0.0

    def script_for(self, mac: str) -> DeviceScript | None:
        """Return the script of one address.

        Args:
            mac: The address in lower case with no separator.

        Returns:
            The matching script, or None when the fleet holds no such address.
        """
        for script in self.scripts:  # The fleet holds seven scripts at most, so a walk is cheap.
            if script.mac == mac:  # Rule 1 makes each address unique, so the first match is the only match.
                return script  # The caller reads the plan of that one device.
        return None  # An unknown address answers nothing, and the caller then reports it.

    def scripts_of_type(self, device_type: str) -> tuple[DeviceScript, ...]:
        """Return every script of one device family.

        Why:
            One event search names one device family. The stand-in answers that
            family and no other, because the real cloud shares that rule.

        Args:
            device_type: One of ``gateway``, ``switch``, or ``ap``.

        Returns:
            The matching scripts in fleet order.
        """
        return tuple(script for script in self.scripts if script.device_type == device_type)  # One family only.

    def macs(self) -> tuple[str, ...]:
        """Return the address of every device of the fleet.

        Returns:
            The addresses in fleet order.
        """
        return tuple(script.mac for script in self.scripts)  # The guard tests read this list.


def cascade_fleet(started_at: float) -> FleetScript:
    """Return the fleet of the cascade rehearsal.

    Why:
        Rule 2 of section 3 of ``data-model.md`` asks for 2 gateways, 2
        switches, and 2 access points. That fleet exercises all four phases and
        still keeps one poll round small.

    Args:
        started_at: The clock reading at the start of the run.

    Returns:
        The fleet script of the cascade tests.
    """
    logger.info("Build the cascade fleet at reading %s", started_at)  # The action, before it happens.
    scripts = (
        DeviceScript("aa0000000001", TYPE_GATEWAY),  # The first gateway of the first phase.
        DeviceScript("aa0000000002", TYPE_GATEWAY),  # The second gateway of the first phase.
        DeviceScript("bb0000000001", TYPE_SWITCH),  # The first switch of the second phase.
        DeviceScript("bb0000000002", TYPE_SWITCH),  # The second switch of the second phase.
        DeviceScript("cc0000000001", TYPE_ACCESS_POINT),  # The first access point of the third phase.
        DeviceScript("cc0000000002", TYPE_ACCESS_POINT),  # The second access point of the third phase.
    )
    fleet = FleetScript(scripts=scripts, started_at=float(started_at))  # One record for the whole run.
    logger.debug("Built the cascade fleet of %s devices", len(scripts))  # The result of the action.
    return fleet  # The stand-in cloud answers from this record.


def stop_fleet(started_at: float) -> FleetScript:
    """Return the fleet of the stop rehearsal.

    Why:
        The stop tests need one session smart router, because the router rides
        a separate cancel endpoint of the organization scope. Rule 2 of section
        3 of ``data-model.md`` asks for that extra device.

    Args:
        started_at: The clock reading at the start of the run.

    Returns:
        The cascade fleet and one session smart router.
    """
    logger.info("Build the stop fleet at reading %s", started_at)  # The action, before it happens.
    router = DeviceScript("dd0000000001", TYPE_GATEWAY)  # The router rides the gateway phase of the cascade.
    base = cascade_fleet(started_at)  # The stop fleet holds every device of the cascade fleet.
    fleet = FleetScript(scripts=(*base.scripts, router), started_at=float(started_at))  # Seven devices in all.
    logger.debug("Built the stop fleet of %s devices", len(fleet.scripts))  # The result of the action.
    return fleet  # The stop tests answer from this record.
