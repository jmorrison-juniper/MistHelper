"""The stand-in cloud of a rehearsal run.

Why:
    ``src/upgrade_portal/app/seam_shapes.py`` records the rule of issue #1991.
    A stand-in must answer the call that the caller really makes, and not a
    simpler shape that the author imagined. This module copies the signature of
    each shipped call from ``contracts/rehearsal-cloud.md``.

    The stand-in also refuses every firmware write. FR-005 and SC-005 both need
    that refusal, because a silent stand-in cannot prove that the run wrote no
    firmware.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from tests.support.rehearsal.clock import RehearsalClock
from tests.support.rehearsal.errors import RehearsalFirmwareError
from tests.support.rehearsal.script import DeviceScript, FleetScript

logger = logging.getLogger(__name__)  # The module logger, so each answer carries this name.

# WHY: The event key of a reconnect. ``events.filter_event_keys`` keeps a key
# that ends with one of these two suffixes, and the catalogue answer must hold
# a key of that shape for each device family.
CATALOGUE_KEYS: tuple[str, ...] = ("GW_CONNECTED", "SW_CONNECTED", "AP_CONNECTED", "AP_RESTARTED")

# WHY: One reconnect key for each family. ``events.reconnect_macs`` matches the
# ``type`` field of an event against the catalogue, so the two must agree.
RECONNECT_TYPES: Mapping[str, str] = {"gateway": "GW_CONNECTED", "switch": "SW_CONNECTED", "ap": "AP_CONNECTED"}

# WHY: The three write endpoints of ``src/firmware/upgrade_service.py``. The
# resolver refuses each one, so a rehearsal can never reach real firmware.
FIRMWARE_WRITE_NAMES: tuple[str, ...] = ("upgradeSiteDevices", "upgradeDevice", "upgradeOrgSsrs")

# WHY: The cancel endpoints of the three scopes. ``stop.cancel_target`` reaches
# one of them for each device that the operator stopped.
CANCEL_NAMES: tuple[str, ...] = ("cancelSiteDeviceUpgrade", "cancelOrgDeviceUpgrade", "cancelOrgSsrUpgrade")

# WHY: The status reads of the three scopes, and the organization statistics
# read that ``_call_status`` uses for a session smart router.
STATUS_NAMES: tuple[str, ...] = ("getSiteDeviceUpgrade", "getOrgDeviceUpgrade", "getSiteSsrUpgrade")
STATISTICS_NAME: str = "listOrgDevicesStats"

# WHY: The upgrade identifier of the rehearsal. One value serves the whole run,
# because the stand-in holds one upgrade job.
UPGRADE_ID: str = "rehearsal-upgrade-0001"


@dataclass(frozen=True, slots=True)
class StandInResponse:
    """One cloud answer, in the shape that every shipped reader takes.

    Attributes:
        data: The body, as the shipped readers expect it.
        status_code: The HTTP status that the page guard reads.
        headers: The answer headers. Every shipped reader ignores them.
    """

    data: Any
    status_code: int = 200
    headers: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CallRecord:
    """One call that a shipped reader made through the stand-in.

    Attributes:
        name: The attachment point that the caller reached.
        positional: The arguments that the caller passed by position.
        keywords: The keyword names that the caller passed.
        at: The clock reading of the call.
    """

    name: str
    positional: tuple[Any, ...]
    keywords: frozenset[str]
    at: float


def _statistics_record(script: DeviceScript, elapsed: float, now: float) -> dict[str, Any]:
    """Build one device statistics record of one poll round.

    Why:
        ``gate.reading_from_record`` reads five fields, and it drops a record
        that carries no usable address. The builder writes all five.

    Args:
        script: The plan of the device.
        elapsed: The seconds since the run started.
        now: The present clock reading, which dates the record.

    Returns:
        One record in the shape that the cloud answers.
    """
    return {
        "mac": script.mac,  # The address that the gate joins against the run target.
        "type": script.device_type,  # The family, which the caller filters on.
        "version": script.version_of(elapsed),  # One half of the reboot proof.
        "uptime": script.uptime_of(elapsed),  # The other half, which falls at the reboot.
        "last_seen": int(now),  # FR-046 dates every record on the cloud clock and never the local one.
    }


class StandInCloud:
    """The answers of the cloud and the counters of every call.

    Why:
        One object holds the five attachment points, so a test attaches once
        and reads one call record. The object holds no settle rule and no phase
        rule. The shipped code owns every rule that the rehearsal proves.
    """

    def __init__(self, fleet: FleetScript, clock: RehearsalClock) -> None:
        """Build one stand-in cloud.

        Args:
            fleet: The scripts of the run.
            clock: The one time source of the run.
        """
        self.fleet = fleet  # The stand-in answers from this script and holds no rule of its own.
        self.clock = clock  # One time source, so an answer and a gate reading never disagree.
        self._calls: list[CallRecord] = []  # Every call, in order, for the call shape test.
        self._counts: dict[str, int] = {}  # The count of each call name, which ``calls_of`` reports.
        self._pause: Callable[[], None] | None = None  # The hook that holds one poll round.
        self.writing: set[str] = set()  # The devices that already write firmware and must not be cancelled.
        self.cancelled: list[str] = []  # Each identifier that a cancel call named, in call order.
        self.total_bonus: int = 0  # A test raises this to make the page guard report a short read.
        self.frozen_last_seen: float | None = None  # A test sets this to hold every record at one cloud moment.

    def set_pause(self, hook: Callable[[], None] | None) -> None:
        """Install the hook that holds one poll round.

        Why:
            Q8 of ``research.md`` asks the suite to read the run record while a
            poll round is in flight. The hook blocks that round, so the read
            meets a run that is truly busy.

        Args:
            hook: The callable to run inside the next statistics answer, or
                None to remove an installed hook.
        """
        logger.info("Install a stand-in pause hook: %s", hook is not None)  # The action, before it happens.
        self._pause = hook  # The next statistics answer runs it one time.
        logger.debug("The stand-in pause hook is now %s", self._pause is not None)  # The result.

    def calls_of(self, name: str) -> int:
        """Return how many times a caller reached one attachment point.

        Args:
            name: The attachment point name.

        Returns:
            The count. Zero when no caller reached that point.
        """
        return self._counts.get(name, 0)  # A missing name counts as zero, which SC-005 reads.

    def calls(self) -> tuple[CallRecord, ...]:
        """Return every recorded call in call order.

        Returns:
            The call records.
        """
        return tuple(self._calls)  # A tuple copy leaves the record safe from the caller.

    def calls_named(self, name: str) -> tuple[CallRecord, ...]:
        """Return every recorded call of one attachment point.

        Args:
            name: The attachment point name.

        Returns:
            The matching call records in call order.
        """
        return tuple(call for call in self._calls if call.name == name)  # The shape test reads one point at a time.

    def _record(self, name: str, positional: tuple[Any, ...], keywords: Mapping[str, Any]) -> None:
        """Record one call of one attachment point.

        Args:
            name: The attachment point name.
            positional: The arguments that the caller passed by position.
            keywords: The keyword arguments that the caller passed.
        """
        self._counts[name] = self._counts.get(name, 0) + 1  # The counter that ``calls_of`` reports.
        self._calls.append(CallRecord(name, positional, frozenset(keywords), self.clock.now()))  # The shape record.

    def list_org_devices_stats(
        self,
        session: Any,
        org_id: str,
        *,
        type: str = "all",  # The shipped caller names this keyword, so the stand-in must answer the same name.
        site_id: str | None = None,
        fields: str | None = None,
        limit: int = 100,
        **extra: Any,
    ) -> StandInResponse:
        """Answer the device statistics read of one poll round.

        Args:
            session: The cloud session.
            org_id: The organization that owns the devices.
            type: The device family filter that the caller sent.
            site_id: The site to read, or None for the whole organization.
            fields: The field list that the caller asked for.
            limit: The page size that the caller asked for.
            **extra: Any further keyword that a later caller adds.

        Returns:
            One page of device statistics records.
        """
        keywords = {"type": type, "site_id": site_id, "fields": fields, "limit": limit, **extra}  # The real call.
        self._record(STATISTICS_NAME, (session, org_id), keywords)  # The shape test reads this record.
        if self._pause is not None:  # Q8 of the research holds one round here.
            self._pause()  # The hook runs inside the round, so a reader meets a busy run.
        now = self.clock.now()  # One reading dates every record of this answer.
        stamp = self.frozen_last_seen if self.frozen_last_seen is not None else now  # A stale cloud repeats one stamp.
        elapsed = now - self.fleet.started_at  # The offset that each script reads.
        results = [_statistics_record(script, elapsed, stamp) for script in self.fleet.scripts]  # The whole fleet.
        body = {"results": results, "total": len(results) + self.total_bonus, "next": None}  # FR-009 page shape.
        logger.debug("The stand-in answered %s device statistics records", len(results))  # The result.
        return StandInResponse(body)  # Status 200, because this read answered.

    def get_all(self, mist_session: Any = None, response: Any = None, **extra: Any) -> list[dict[str, Any]]:
        """Walk every page of one cloud answer.

        Why:
            ``gate.read_fleet_statistics`` calls this helper with the keywords
            ``mist_session`` and ``response``. The stand-in answers one page,
            so the walk returns the records of that page.

        Args:
            mist_session: The cloud session that the caller passed.
            response: The first page that the caller already read.
            **extra: Any further keyword that a later caller adds.

        Returns:
            The records of the answer.
        """
        keywords = {"mist_session": mist_session, "response": response, **extra}  # The real call of line 856.
        self._record("get_all", (), keywords)  # The shape test proves both keyword names.
        body = getattr(response, "data", None)  # Every shipped reader takes the body with ``getattr``.
        records = body.get("results", []) if isinstance(body, dict) else []  # An unknown shape reads as empty.
        logger.debug("The stand-in page walk returned %s records", len(records))  # The result of the walk.
        return [dict(record) for record in records]  # A copy leaves the stand-in body unchanged.

    def search_org_device_events(
        self,
        session: Any,
        org_id: str,
        *,
        device_type: str = "ap",
        start: str | None = None,
        end: str | None = None,
        limit: int = 100,
        search_after: str | None = None,
        **extra: Any,
    ) -> StandInResponse:
        """Answer the device event search of one poll round.

        Why:
            Rule 1 of section 3 of the contract states that the default of
            ``device_type`` is ``ap``. A caller that sends no family therefore
            reads access points alone, and the real cloud shares that rule.

        Args:
            session: The cloud session.
            org_id: The organization to read.
            device_type: The family to read.
            start: The start of the window, as text holding epoch seconds.
            end: The end of the window, as text holding epoch seconds.
            limit: The page size that the caller asked for.
            search_after: The cursor of the previous page.
            **extra: Any further keyword that a later caller adds.

        Returns:
            One page of device events.
        """
        keywords = {"device_type": device_type, "start": start, "end": end, "limit": limit, **extra}  # The real call.
        keywords["search_after"] = search_after  # The fifth keyword of the shipped call at events.py line 437.
        self._record("searchOrgDeviceEvents", (session, org_id), keywords)  # The shape test reads this record.
        results = self._events_in_window(device_type, start, end)  # Rule 3 keeps the window honest.
        logger.debug("The stand-in answered %s %s events", len(results), device_type)  # The result of the read.
        return StandInResponse({"results": results, "total": len(results), "next": None})  # The paged event shape.

    def _events_in_window(self, device_type: str, start: str | None, end: str | None) -> list[dict[str, Any]]:
        """Return every reconnect event of one family inside one window.

        Args:
            device_type: The family that the caller asked for.
            start: The start of the window, as text holding epoch seconds.
            end: The end of the window, as text holding epoch seconds.

        Returns:
            The matching event records.
        """
        first = float(start) if start is not None else float("-inf")  # The window arrives as text, never as a number.
        last = float(end) if end is not None else float("inf")  # The same rule holds for the end of the window.
        key = RECONNECT_TYPES.get(device_type, "AP_CONNECTED")  # One reconnect key for each family.
        rows: list[dict[str, Any]] = []  # The answer of this one search.
        for script in self.fleet.scripts_of_type(device_type):  # Rule 1 answers one family and no other.
            moment = self.fleet.started_at + script.reconnect_at  # The moment that the device reported the reconnect.
            if first <= moment <= last:  # Rule 3 answers an event only inside the window.
                rows.append({"mac": script.mac, "type": key, "timestamp": moment, "device_type": device_type})
        return rows  # The caller matches each type against the catalogue.

    def list_device_events_definitions(self, session: Any) -> StandInResponse:
        """Answer the device event catalogue read.

        Args:
            session: The cloud session.

        Returns:
            The catalogue records that hold the reconnect keys.
        """
        self._record("listDeviceEventsDefinitions", (session,), {})  # One positional argument, as section 4 states.
        rows = [{"key": key} for key in CATALOGUE_KEYS]  # ``filter_event_keys`` reads the ``key`` field alone.
        logger.debug("The stand-in answered %s catalogue keys", len(rows))  # The result of the read.
        return StandInResponse(rows)  # The constants endpoint answers a plain list.

    def resolve_endpoint(self, name: str) -> Callable[..., StandInResponse]:
        """Return the stand-in callable of one upgrade endpoint.

        Why:
            Section 5 of the contract names nine endpoints. Three of them write
            firmware, and the resolver refuses each one at this seam. The
            refusal happens before any call, so no test can reach a write.

        Args:
            name: The endpoint name that the shipped caller asked for.

        Returns:
            The stand-in callable of that endpoint.

        Raises:
            RehearsalFirmwareError: When the name writes firmware.
            ValueError: When the name is not an upgrade endpoint.
        """
        logger.info("The stand-in resolves the upgrade endpoint %s", name)  # The action, before it happens.
        self._record("_resolve_endpoint", (name,), {})  # SC-005 counts the three write names in this record.
        if name in FIRMWARE_WRITE_NAMES:  # FR-005 forbids a firmware write in a rehearsal.
            raise RehearsalFirmwareError(f"The rehearsal refused the firmware write endpoint {name}.")
        answer = self._endpoint_answer(name)  # The read endpoints and the cancel endpoints both land here.
        logger.debug("The stand-in resolved the endpoint %s", name)  # The result of the action.
        return answer  # The shipped caller now calls this callable with the session and the identifiers.

    def _endpoint_answer(self, name: str) -> Callable[..., StandInResponse]:
        """Return the callable of one read endpoint or one cancel endpoint.

        Args:
            name: The endpoint name.

        Returns:
            The stand-in callable.

        Raises:
            ValueError: When the name is not an upgrade endpoint.
        """
        if name in CANCEL_NAMES:  # A cancel records the identifier and answers the outcome.
            return lambda *args, **kwargs: self._cancel(name, args, kwargs)
        if name in STATUS_NAMES:  # A status read answers the upgrade job of one scope.
            return lambda *args, **kwargs: self._status(name, args, kwargs)
        if name == STATISTICS_NAME:  # The organization scope read of a session smart router.
            return lambda *args, **kwargs: self._router_statistics(args, kwargs)
        raise ValueError(f"the endpoint {name} is not a sanctioned upgrade endpoint")

    def _cancel(self, name: str, args: tuple[Any, ...], kwargs: Mapping[str, Any]) -> StandInResponse:
        """Record one cancel call and answer the outcome.

        Args:
            name: The cancel endpoint name.
            args: The arguments that the caller passed by position.
            kwargs: The keyword arguments that the caller passed.

        Returns:
            The cancel answer, with status 200.
        """
        logger.info("The stand-in records a cancel through %s", name)  # The action, before it happens.
        self._record(name, args, kwargs)  # The stop test reads the scope from this record.
        self.cancelled.append(str(args[1]) if len(args) > 1 else "")  # The scope identifier of the cancel call.
        logger.debug("The stand-in holds %s cancel calls", len(self.cancelled))  # The result of the action.
        return StandInResponse({"result": "ok"})  # ``_sort_cancel`` accepts status 200 and status 202.

    def _status(self, name: str, args: tuple[Any, ...], kwargs: Mapping[str, Any]) -> StandInResponse:
        """Answer one upgrade status read.

        Args:
            name: The status endpoint name.
            args: The arguments that the caller passed by position.
            kwargs: The keyword arguments that the caller passed.

        Returns:
            The upgrade job of that scope.
        """
        self._record(name, args, kwargs)  # The shape test reads the three positional arguments.
        writing = sorted(self.writing)  # The devices that already write firmware and must not be interrupted.
        body = {
            "status": "upgrading",  # The state of the upgrade job.
            "current_phase": "downloading",  # The phase that the cloud reports for this job.
            "targets": {"reboot_in_progress": writing},  # ``_sort_cancel`` reads this list.
            "upgrade_id": UPGRADE_ID,  # The identifier that the submission returned.
            "status_known": True,  # ``stop.status_is_known`` needs this field.
        }
        logger.debug("The stand-in answered the upgrade status of %s", name)  # The result of the read.
        return StandInResponse(body)  # Status 200, because the read answered.

    def _router_statistics(self, args: tuple[Any, ...], kwargs: Mapping[str, Any]) -> StandInResponse:
        """Answer the organization scope read of a session smart router.

        Why:
            The rule of section 5 states that this read answers device
            statistics and no upgrade job. ``stop.status_is_known`` then reads
            the status of that device as unknown, which is the honest answer.

        Args:
            args: The arguments that the caller passed by position.
            kwargs: The keyword arguments that the caller passed.

        Returns:
            The device statistics of the organization scope.
        """
        self._record(STATISTICS_NAME, args, kwargs)  # The same name that the settle gate reaches.
        logger.debug("The stand-in answered the router statistics read")  # The result of the read.
        return StandInResponse([])  # A list, so ``_payload`` reports devices and names no upgrade job.
