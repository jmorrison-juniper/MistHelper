"""The reconnect event catalogue and the organization event poll of the settle gate.

Why:
    The settle gate needs one of its three signals from the device event stream.
    Two rules make that read easy to get wrong, and both are silent when broken.

    First, the connected event key list is not vendor confirmed. Only
    ``AP_RESTARTED`` and ``AP_CONNECTED`` appear in a read source of this
    repository (``research/settle-gate-apis.md`` section 4.2). ``SW_CONNECTED``,
    ``GW_CONNECTED``, and ``GW_RESTARTED`` are inferences from the naming
    pattern. This module therefore hard-codes no key. It loads the catalogue from
    the cloud and keeps every key that ends in ``_CONNECTED`` or ``_RESTARTED``,
    so a vendor rename costs nothing.

    Second, ``searchOrgDeviceEvents`` defaults ``device_type`` to ``ap``. A
    switch gate or a gateway gate that omits the parameter reads access point
    events, finds no reconnect, and waits for ever with no error. Every call in
    this module passes the value.

    Third, the cursor is ``search_after``. Both vendored event search documents
    advise ``limit`` and ``page`` under their pagination heading, and no ``page``
    parameter exists in either parameter table or in the installed SDK. This
    module narrows the window with ``start`` and ``end`` and raises ``limit``, so
    one poll usually fits one page.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, urlsplit

import mistapi

from src.upgrade_portal.capture.devices import normalize_device_mac

logger = logging.getLogger(__name__)

# T138 fixes the cadence. One family polls at a time, because the cascade runs
# one phase at a time. That is 180 calls each hour, and the settle gate spends
# another 180 on the device statistics. The pair stays under the 360 call budget
# of T142, which is under 8 percent of the 5000 call quota at
# ``src/utils/rate_limiting.py:56``.
POLL_INTERVAL_SECONDS = 20

DEFAULT_WINDOW_SECONDS = 300
DEFAULT_EVENT_LIMIT = 1000
MIN_EVENT_LIMIT = 1
MAX_EVENT_LIMIT = 1000
DEFAULT_MAX_PAGES = 10

SUFFIX_CONNECTED = "_CONNECTED"
SUFFIX_RESTARTED = "_RESTARTED"

DEVICE_TYPE_AP = "ap"
DEVICE_TYPE_SWITCH = "switch"
DEVICE_TYPE_GATEWAY = "gateway"
DEVICE_TYPES = (DEVICE_TYPE_GATEWAY, DEVICE_TYPE_SWITCH, DEVICE_TYPE_AP)

CURSOR_PARAMETER = "search_after"


@dataclass(frozen=True, slots=True)
class EventKeys:
    """The reconnect event keys that the cloud catalogue reports.

    Why:
        The gate matches an event by key, and the key list differs by cloud
        release. The record holds the two groups apart, because a restart and a
        reconnect are two different signals. The record is frozen, so two gate
        threads may read one instance with no lock.

    Attributes:
        connected: Every key that ends in ``_CONNECTED``.
        restarted: Every key that ends in ``_RESTARTED``.
    """

    connected: frozenset[str]
    restarted: frozenset[str]

    @property
    def is_empty(self) -> bool:
        """Report whether the catalogue gave no reconnect key at all.

        Why:
            An empty result means the read failed or the cloud changed the
            naming pattern. The gate must then say so plainly instead of waiting
            for an event that can never match.

        Returns:
            True when neither group holds a key.
        """
        return not self.connected and not self.restarted

    def matches(self, event_type: str) -> bool:
        """Report whether one event key is a reconnect signal.

        Args:
            event_type: The ``type`` field of one event record.

        Returns:
            True when the key sits in either group.
        """
        key = str(event_type).strip().upper()
        return key in self.connected or key in self.restarted


@dataclass(frozen=True, slots=True)
class EventWindow:
    """The time window and the page size of one event poll.

    Why:
        A narrow window with a high page size lets one poll fit one page, which
        keeps the cursor work rare. The record carries the three values together
        so that no caller sends a start without an end.

    Attributes:
        start: The first moment of the window, in epoch seconds.
        end: The last moment of the window, in epoch seconds.
        limit: The page size that the poll asks for.
    """

    start: int
    end: int
    limit: int = DEFAULT_EVENT_LIMIT


@dataclass(frozen=True, slots=True)
class EventPage:
    """One page of the organization event search.

    Attributes:
        events: The event records of the page.
        cursor: The ``search_after`` value of the next page, or None at the end.
        truncated: True when the page filled and the cloud gave no cursor. The
            caller must then narrow the window, because the rest is lost.
    """

    events: tuple[Mapping[str, Any], ...]
    cursor: str | None
    truncated: bool


def _payload(response: Any) -> Any:
    """Return the parsed body of one cloud answer.

    Args:
        response: The answer that the SDK built.

    Returns:
        The parsed body, or None when the answer holds no body.
    """
    return getattr(response, "data", None)


def _rows(response: Any) -> tuple[Mapping[str, Any], ...]:
    """Return the record list of one cloud answer.

    Why:
        The constants endpoint answers with a plain list and the event search
        answers with an object that holds ``results``. One reader covers both,
        and it names an answer that it cannot read instead of returning an empty
        list in silence.

    Args:
        response: The answer that the SDK built.

    Returns:
        The records of the answer. Empty when the shape is unknown.
    """
    payload = _payload(response)
    if isinstance(payload, dict):
        payload = payload.get("results")
    if not isinstance(payload, list):
        logger.warning("Upgrade portal read an event answer shape that it does not know")
        return ()
    return tuple(row for row in payload if isinstance(row, Mapping))


def filter_event_keys(rows: Iterable[Mapping[str, Any]]) -> EventKeys:
    """Keep the reconnect keys of the device event catalogue.

    Why:
        T137 forbids a hard-coded key list, because only the access point keys
        are vendor confirmed. The suffix test survives a vendor rename of the
        family prefix, and the poll already splits the families with the
        ``device_type`` parameter, so this function needs no prefix map.

    Args:
        rows: The catalogue records. Each record holds a ``key`` field.

    Returns:
        The two reconnect key groups.
    """
    connected: set[str] = set()
    restarted: set[str] = set()
    for row in rows:
        key = str(row.get("key", "")).strip().upper()
        if key.endswith(SUFFIX_CONNECTED):
            connected.add(key)
        elif key.endswith(SUFFIX_RESTARTED):
            restarted.add(key)
    logger.debug("Upgrade portal kept %s connected key(s) and %s restart key(s)", len(connected), len(restarted))
    return EventKeys(frozenset(connected), frozenset(restarted))


def read_event_definitions(session: Any) -> tuple[Mapping[str, Any], ...]:
    """Read the whole device event catalogue from the cloud.

    Why:
        ``listDeviceEventsDefinitions`` takes the session alone. It carries no
        organization parameter and no page parameter, so one call returns the
        whole catalogue. ``research/settle-gate-apis.md:259`` names the SDK path
        ``mistapi.api.v1.constants.events``. That module does not exist. The real
        path is ``mistapi.api.v1.const.device_events``.

    Args:
        session: The cloud session. The caller owns it.

    Returns:
        The catalogue records. Empty when the read failed.
    """
    logger.info("Upgrade portal reads the device event catalogue")
    try:
        response = mistapi.api.v1.const.device_events.listDeviceEventsDefinitions(session)
    except Exception as error:  # A failed catalogue read must not stop the run.
        logger.warning("Upgrade portal failed the device event catalogue read: %s", error)
        return ()
    return _rows(response)


class EventCatalogue:
    """Holds the reconnect key list that one portal process discovered.

    Why:
        The catalogue changes only with a cloud release, so one read serves the
        whole process life. A module level cache would be process state that no
        test can clear, so the cache lives on an instance that the application
        owns and a test builds fresh.
    """

    def __init__(self) -> None:
        """Build an empty catalogue holder."""
        self._lock = threading.Lock()
        self._keys: EventKeys | None = None

    @property
    def cached(self) -> EventKeys | None:
        """Return the cached keys with no cloud read.

        Returns:
            The cached keys, or None before the first load.
        """
        return self._keys

    def load(self, session: Any) -> EventKeys:
        """Return the reconnect keys, and read the catalogue once.

        Why:
            Several gate threads start together, and each one needs the keys.
            The lock spans the cloud read on purpose, so the process makes one
            call instead of one call for each thread. The read happens once, so
            the wait costs nothing after the start.

        Args:
            session: The cloud session. The caller owns it.

        Returns:
            The reconnect keys. The record is empty when the read failed.
        """
        with self._lock:
            if self._keys is not None:
                return self._keys
            keys = filter_event_keys(read_event_definitions(session))
            if keys.is_empty:
                logger.warning("Upgrade portal found no reconnect event key in the catalogue")
            self._keys = keys
        logger.info("Upgrade portal cached %s reconnect event key(s)", len(keys.connected) + len(keys.restarted))
        return keys

    def reset(self) -> None:
        """Drop the cached keys so that the next load reads the cloud again."""
        with self._lock:
            self._keys = None


def build_window(
    now: float,
    lookback_seconds: int = DEFAULT_WINDOW_SECONDS,
    limit: int = DEFAULT_EVENT_LIMIT,
) -> EventWindow:
    """Build the time window of one event poll.

    Why:
        A wide window returns more events than one page holds, and the cloud
        gives no warning when a page fills. A narrow window with a high page size
        keeps one poll inside one page, which is the rule of T139.

    Args:
        now: The current moment in epoch seconds.
        lookback_seconds: How far back the window reaches.
        limit: The page size to ask for. The function clamps it.

    Returns:
        The finished window.

    Raises:
        ValueError: If the look-back is not a positive number of seconds.
    """
    if lookback_seconds <= 0:
        raise ValueError("an event window needs a positive look-back")
    end = int(now)
    page_size = max(MIN_EVENT_LIMIT, min(int(limit), MAX_EVENT_LIMIT))
    return EventWindow(start=end - int(lookback_seconds), end=end, limit=page_size)


def _validate_device_type(device_type: str) -> str:
    """Check the device type of one poll.

    Why:
        ``searchOrgDeviceEvents`` defaults ``device_type`` to ``ap``. A typing
        mistake would read access point events for a switch phase and the gate
        would wait for ever with no error. The check turns that silence into a
        fault at the first call.

    Args:
        device_type: The family to read.

    Returns:
        The device type in lower case.

    Raises:
        ValueError: If the value names no known family.
    """
    value = str(device_type).strip().lower()
    if value not in DEVICE_TYPES:
        raise ValueError(f"an event poll needs one of {DEVICE_TYPES}")
    return value


def read_cursor(response: Any) -> str | None:
    """Return the ``search_after`` value of the next page.

    Why:
        The cloud reports the cursor in the ``next`` URL and names it
        ``search_after``. The vendor text states plainly that a caller must never
        build the value. This reader therefore copies the value and never
        computes one.

    Args:
        response: The answer that the SDK built.

    Returns:
        The cursor of the next page, or None at the end of the result set.
    """
    payload = _payload(response)
    if not isinstance(payload, dict):
        return None
    direct = payload.get(CURSOR_PARAMETER)
    if direct not in (None, ""):
        return str(direct)
    return _cursor_from_url(payload.get("next"))


def _cursor_from_url(next_url: Any) -> str | None:
    """Read the cursor out of the ``next`` URL of one answer.

    Args:
        next_url: The ``next`` field of the answer.

    Returns:
        The cursor, or None when the URL carries none.
    """
    if not isinstance(next_url, str) or not next_url:
        return None
    values = parse_qs(urlsplit(next_url).query).get(CURSOR_PARAMETER, [])
    return values[0] if values else None


def poll_device_events(
    session: Any,
    org_id: str,
    device_type: str,
    window: EventWindow,
    cursor: str | None = None,
) -> EventPage:
    """Read one page of device events at the organization scope.

    Why:
        The gate reads the organization scope, because one call then covers every
        site of a multiple-site run. The call passes ``device_type`` on every
        poll, because the parameter defaults to ``ap``.

        The call passes ``start`` and ``end`` as text. The installed SDK types
        both as ``str | None`` even though the values are epoch seconds.

    Args:
        session: The cloud session. The caller owns it.
        org_id: The organization to read.
        device_type: The family to read. One of ``gateway``, ``switch``, ``ap``.
        window: The time window and the page size.
        cursor: The ``search_after`` value of the previous page, or None for the
            first page.

    Returns:
        One page of events, with the cursor of the next page.

    Raises:
        ValueError: If the device type names no known family.
    """
    family = _validate_device_type(device_type)
    logger.info("Upgrade portal reads %s events of organization %s", family, org_id)
    response = mistapi.api.v1.orgs.devices.searchOrgDeviceEvents(
        session,
        org_id,
        device_type=family,
        start=str(window.start),
        end=str(window.end),
        limit=window.limit,
        search_after=cursor,
    )
    return _read_page(response, family, window.limit)


def _read_page(response: Any, device_type: str, limit: int) -> EventPage:
    """Turn one cloud answer into a page record.

    Why:
        The cloud reports no error when a page fills and the caller misses the
        rest. This reader names that case, so the gate can narrow the window
        instead of missing a reconnect.

    Args:
        response: The answer that the SDK built.
        device_type: The family that the poll asked for.
        limit: The page size that the poll asked for.

    Returns:
        The finished page record.
    """
    rows = _rows(response)
    cursor = read_cursor(response)
    truncated = cursor is None and len(rows) >= limit
    if truncated:
        logger.warning("Upgrade portal filled one %s event page with no cursor. Narrow the window", device_type)
    logger.debug("Upgrade portal read %s %s event(s)", len(rows), device_type)
    return EventPage(rows, cursor, truncated)


def drain_device_events(
    session: Any,
    org_id: str,
    device_type: str,
    window: EventWindow,
    max_pages: int = DEFAULT_MAX_PAGES,
) -> tuple[Mapping[str, Any], ...]:
    """Read every page of one event window.

    Why:
        One poll usually fits one page, because the window is narrow and the page
        size is high. The loop covers the busy site that does not fit. The page
        count has a ceiling, so a cloud that always returns a cursor cannot hold
        the gate thread for ever.

    Args:
        session: The cloud session. The caller owns it.
        org_id: The organization to read.
        device_type: The family to read.
        window: The time window and the page size.
        max_pages: The largest number of pages to read in one poll.

    Returns:
        Every event of the window, in the order that the cloud returned.

    Raises:
        ValueError: If the device type names no known family.
    """
    collected: list[Mapping[str, Any]] = []
    cursor: str | None = None
    for _ in range(max(1, max_pages)):
        page = poll_device_events(session, org_id, device_type, window, cursor)
        collected.extend(page.events)
        cursor = page.cursor
        if cursor is None:
            break
    else:
        logger.warning("Upgrade portal stopped the %s event read at the page ceiling", device_type)
    return tuple(collected)


def select_reconnect_events(
    events: Sequence[Mapping[str, Any]],
    keys: EventKeys,
) -> tuple[Mapping[str, Any], ...]:
    """Keep the events whose key is a reconnect signal.

    Args:
        events: The event records of one poll.
        keys: The reconnect keys that the catalogue reported.

    Returns:
        The matching events, in the order that the cloud returned.
    """
    if keys.is_empty:
        logger.warning("Upgrade portal holds no reconnect event key, so it matched no event")
        return ()
    return tuple(event for event in events if keys.matches(str(event.get("type", ""))))


def reconnect_macs(events: Sequence[Mapping[str, Any]], keys: EventKeys) -> frozenset[str]:
    """Return the MAC address of each device that reported a reconnect.

    Why:
        The gate compares this set against the target list, so both sides must
        write a MAC address the same way. The set uses the shared normalizer,
        which gives lower case and no separator.

    Args:
        events: The event records of one poll.
        keys: The reconnect keys that the catalogue reported.

    Returns:
        The MAC address of each device that reported a reconnect.
    """
    macs = {normalize_device_mac(event.get("mac")) for event in select_reconnect_events(events, keys)}
    macs.discard("")
    logger.debug("Upgrade portal saw a reconnect from %s device(s)", len(macs))
    return frozenset(macs)


def seconds_until_next_poll(last_poll_at: float, now: float) -> float:
    """Return the wait before the next event poll.

    Why:
        T138 fixes the cadence at 20 seconds. The driver owns the sleep, because
        a sleep inside this module would block a test. The function reports zero
        when the moment already passed, so a slow poll never builds a backlog.

    Args:
        last_poll_at: The moment of the previous poll, in epoch seconds.
        now: The current moment, in epoch seconds.

    Returns:
        The seconds to wait. Zero when the next poll is due.
    """
    remaining = POLL_INTERVAL_SECONDS - (now - last_poll_at)
    return max(0.0, remaining)


__all__ = [
    "CURSOR_PARAMETER",
    "DEFAULT_EVENT_LIMIT",
    "DEFAULT_MAX_PAGES",
    "DEFAULT_WINDOW_SECONDS",
    "DEVICE_TYPES",
    "DEVICE_TYPE_AP",
    "DEVICE_TYPE_GATEWAY",
    "DEVICE_TYPE_SWITCH",
    "MAX_EVENT_LIMIT",
    "MIN_EVENT_LIMIT",
    "POLL_INTERVAL_SECONDS",
    "SUFFIX_CONNECTED",
    "SUFFIX_RESTARTED",
    "EventCatalogue",
    "EventKeys",
    "EventPage",
    "EventWindow",
    "build_window",
    "drain_device_events",
    "filter_event_keys",
    "poll_device_events",
    "read_cursor",
    "read_event_definitions",
    "reconnect_macs",
    "seconds_until_next_poll",
    "select_reconnect_events",
]
