"""The tier 3 extra reads of one upgrade capture.

Why:
    Tier 2 is the default capture and tier 3 is an option that an operator
    turns on for one run. A tier 3 section therefore must never fail the whole
    capture. Every read here degrades to an empty section and a reason, so one
    unreachable endpoint still leaves the other five sections whole.

    Two sections cost no extra cloud call, and this module is built around that
    fact. The radio state already rides inside the ``radio_stat`` field of the
    tier 2 device statistics, so this module takes those statistics as an input
    and never calls the cloud for a radio. The power over Ethernet state rides
    inside the same port record as the switch port state, so one port read
    feeds both sections. A caller that already read the ports supplies them,
    and this module then makes no port call at all.

    The module returns plain sections keyed by the section name. It never
    builds the capture document and it never builds the ``partial_reasons``
    list. Each section carries its own name, its reason, and the HTTP status,
    which is everything the assembly step needs to write one partial reason.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import mistapi

logger = logging.getLogger(__name__)

# The six tier 3 sections of data-model.md section 3.5, in the order of that
# table. A reader compares the code against the table without a search.
SECTION_SWITCH_PORTS = "switch_ports"
SECTION_POE = "poe"
SECTION_RADIOS = "radios"
SECTION_TUNNELS = "tunnels"
SECTION_BGP_PEERS = "bgp_peers"
SECTION_ALARMS = "alarms"

SECTION_NAMES: tuple[str, ...] = (
    SECTION_SWITCH_PORTS,
    SECTION_POE,
    SECTION_RADIOS,
    SECTION_TUNNELS,
    SECTION_BGP_PEERS,
    SECTION_ALARMS,
)

# The shared port read. This name is not a capture section. It names the one
# call that feeds both the switch port section and the power section.
SOURCE_PORTS = "ports"

# The three sections that own a cloud call of their own. The port sections
# share one call and the radio section makes none.
_CALLED_SECTIONS: tuple[str, ...] = (SECTION_TUNNELS, SECTION_BGP_PEERS, SECTION_ALARMS)

REASON_READ = ""
REASON_CALL_FAILED = "cloud_call_failed"
REASON_ERROR_STATUS = "cloud_error_status"
REASON_SOURCE_ABSENT = "source_absent"

_OPTIONAL_SENTENCE = "The extra tier is optional, so the capture keeps every other section."

_MESSAGES: dict[str, str] = {
    REASON_READ: "The portal read this section.",
    REASON_CALL_FAILED: "The cloud call for this section failed. " + _OPTIONAL_SENTENCE,
    REASON_ERROR_STATUS: "The cloud refused the call for this section. " + _OPTIONAL_SENTENCE,
    REASON_SOURCE_ABSENT: "The read that carries this section is absent. " + _OPTIONAL_SENTENCE,
}

# The device scope of the port read. The enum holds switch, gateway, and all.
# The value is named here, because a reader must see that one call covers every
# wired device of the site. A call for each device costs one request for each
# switch instead of about three for the whole site.
PORT_DEVICE_TYPE = "all"

# The alarm filter. False restricts the result to an alarm that nobody
# acknowledged, which is what "open alarms at the moment of capture" means.
ALARM_ACKED = False

# The three bands of the radio_stat field. Every measurement inside a band is
# nullable, so a radio record may hold None for any value.
RADIO_BANDS: tuple[str, ...] = ("band_24", "band_5", "band_6")

_PORT_FIELDS: tuple[str, ...] = ("mac", "port_id", "up", "speed", "full_duplex", "port_usage", "mac_count")
_NEIGHBOR_FIELDS: tuple[str, ...] = ("neighbor_mac", "neighbor_port_desc", "neighbor_system_name")
_SWITCH_PORT_FIELDS: tuple[str, ...] = _PORT_FIELDS + _NEIGHBOR_FIELDS
_POE_FIELDS: tuple[str, ...] = ("mac", "port_id", "poe_disabled", "poe_mode", "poe_on", "poe_priority", "power_draw")
_RADIO_FIELDS: tuple[str, ...] = ("channel", "power", "bandwidth", "noise_floor", "num_clients", "num_wlans")

# The page size when MistHelper is out of reach. 1000 is the largest page the
# cloud accepts, so a fallback still reads a whole page.
_FALLBACK_PAGE_LIMIT = 1000

# The HTTP range that counts as a read.
_STATUS_FLOOR = 200
_STATUS_CEILING = 300


@dataclass(frozen=True, slots=True)
class SiteScope:
    """The organization and the site that one tier 3 read targets.

    Why:
        The tunnel read runs at organization scope and filters by site, because
        ``mistapi`` 0.63.3 holds no site scope tunnel call. The other reads run
        at site scope. One scope value carries both identifiers, so every read
        keeps the same short signature.

    Attributes:
        org_id: The Mist organization identifier.
        site_id: The Mist site identifier.
    """

    org_id: str
    site_id: str


@dataclass(frozen=True, slots=True)
class SourcePayloads:
    """The reads that another step already made.

    Why:
        Two tier 3 sections need no cloud call of their own. The radio state
        rides inside the tier 2 device statistics, and the power over Ethernet
        state rides inside the port records. This holder names both inputs, so
        a reader sees which earlier read feeds which section.

    Attributes:
        device_stats: The tier 2 device statistics. An access point entry holds
            a ``radio_stat`` field. None means the tier 2 read failed, and the
            radio section then reports an absent source.
        port_records: The raw port records of one site. None asks this module
            to read the ports one time, which still feeds both port sections.
    """

    device_stats: Sequence[Mapping[str, Any]] | None = None
    port_records: Sequence[Mapping[str, Any]] | None = None


@dataclass(frozen=True, slots=True)
class ExtraSection:
    """One tier 3 section and the outcome of its read.

    Why:
        The assembly step owns the capture document and owns the shape of
        ``partial_reasons``. This record therefore carries the three values
        that one partial reason needs, and nothing more. A failed section still
        arrives, with an empty record list, so a caller never loses a key.

    Attributes:
        name: The section name of data-model.md section 3.5.
        records: The read rows. Empty after a failed read.
        reason: A stable machine name. ``REASON_READ`` after a good read.
        http_status: The status of the cloud call. 0 when no call was made.
    """

    name: str
    records: tuple[dict[str, Any], ...]
    reason: str
    http_status: int

    @property
    def failed(self) -> bool:
        """Report whether this section needs a partial reason.

        Returns:
            True when the read did not finish.
        """
        return self.reason != REASON_READ

    @property
    def message(self) -> str:
        """Return one plain sentence about the outcome of this section.

        Why:
            The stored record holds a machine name and the interface shows a
            sentence. One map holds both, so the two never drift apart.

        Returns:
            The sentence for the reason of this section.
        """
        return _MESSAGES.get(self.reason, _MESSAGES[REASON_CALL_FAILED])


CloudFetch = Callable[[Any, SiteScope], Any]


@dataclass(frozen=True, slots=True)
class _PagedResponse:
    """Every page of one search call, in the shape of a cloud response.

    Why:
        A search call answers with one page, and a read needs every page. The
        page walk returns a plain list and drops the status, so this holder
        carries the status of the first page beside the joined rows. Every read
        then classifies one shape.

    Attributes:
        status_code: The HTTP status of the first page.
        data: The joined rows of every page.
    """

    status_code: int
    data: list[dict[str, Any]]


def _page_limit() -> int:
    """Return the page size for a tier 3 cloud call.

    Why:
        ``MistHelper`` imports from ``src``, so a top-level import here builds
        a cycle and the process fails to start. The late-binding import copies
        the idiom at ``src/upgrade_portal/runtime/pools.py:148``.

    Returns:
        The shared page limit, or the largest page the cloud accepts.
    """
    try:
        import MistHelper  # Late-binding import. MistHelper imports from src, so a top-level import cycles

        return int(MistHelper.DEFAULT_API_PAGE_LIMIT)
    except Exception as error:  # A page size is a tuning value, never a reason to lose a section
        logger.debug("Upgrade portal uses the fallback page limit: %s", type(error).__name__)
        return _FALLBACK_PAGE_LIMIT


def _records_of(payload: Any) -> tuple[dict[str, Any], ...]:
    """Read the rows out of one cloud payload.

    Why:
        A search call answers with ``{"results": [...]}`` and a page walk
        answers with a bare list. One reader covers both shapes, so a change of
        endpoint never reaches a section.

    Args:
        payload: The ``data`` field of a cloud response, or a page list.

    Returns:
        One dictionary for each row. Empty for any other shape.
    """
    rows = payload.get("results", []) if isinstance(payload, Mapping) else payload
    if not isinstance(rows, list):
        return ()
    return tuple(dict(row) for row in rows if isinstance(row, Mapping))


def _paged(session: Any, response: Any, scope: SiteScope) -> _PagedResponse:
    """Walk every page of one search call.

    Why:
        A large site holds more ports than one page. ``mistapi.get_all``
        answers with an empty list, no error, and no log when the payload shape
        surprises it, which would drop a whole section without a word. The
        first page is therefore the floor, so a surprise loses no row. A silent
        floor would show a short section that reads as whole, so the floor
        writes a log record that names the site and both counts.

    Args:
        session: The mistapi session that made the call.
        response: The response of the first page.
        scope: The organization and the site to read. The log record names the site.

    Returns:
        The status of the first page beside the rows of every page.
    """
    first = _records_of(getattr(response, "data", None))
    status = int(getattr(response, "status_code", 0) or 0)
    try:
        rows = _records_of(mistapi.get_all(response=response, mist_session=session))
    except Exception as error:  # A failed page walk must not lose the rows that already arrived
        logger.warning("Upgrade portal could not walk every page of site %s: %s", scope.site_id, type(error).__name__)
        rows = ()
    if len(rows) < len(first):  # The walk gave up, so the first page holds every row that this call can report.
        logger.warning(
            "Upgrade portal kept the first page of %s row(s) for site %s because the page walk returned %s",
            len(first),
            scope.site_id,
            len(rows),
        )
        return _PagedResponse(status, list(first))
    return _PagedResponse(status, list(rows))


def _fetch_ports(session: Any, scope: SiteScope) -> _PagedResponse:
    """Read every wired port of one site.

    Why:
        One call carries the port state and the power over Ethernet state, so
        the power section costs no request of its own.

    Args:
        session: The mistapi session.
        scope: The organization and the site to read.

    Returns:
        Every port record of the site.
    """
    response = mistapi.api.v1.sites.stats.searchSiteSwOrGwPorts(
        session, scope.site_id, device_type=PORT_DEVICE_TYPE, limit=_page_limit()
    )
    return _paged(session, response, scope)


def _fetch_tunnels(session: Any, scope: SiteScope) -> _PagedResponse:
    """Read the gateway tunnel state of one site.

    Why:
        ``mistapi`` 0.63.3 holds no site scope tunnel call, so the read runs at
        organization scope and filters by site.

    Args:
        session: The mistapi session.
        scope: The organization and the site to read.

    Returns:
        Every tunnel record of the site.
    """
    response = mistapi.api.v1.orgs.stats.searchOrgTunnelsStats(
        session, scope.org_id, site_id=scope.site_id, limit=_page_limit()
    )
    return _paged(session, response, scope)


def _fetch_bgp_peers(session: Any, scope: SiteScope) -> _PagedResponse:
    """Read the BGP peer state of one site.

    Args:
        session: The mistapi session.
        scope: The organization and the site to read.

    Returns:
        Every BGP peer record of the site.
    """
    response = mistapi.api.v1.sites.stats.searchSiteBgpStats(session, scope.site_id, limit=_page_limit())
    return _paged(session, response, scope)


def _fetch_alarms(session: Any, scope: SiteScope) -> _PagedResponse:
    """Read the alarms that nobody acknowledged at one site.

    Why:
        A capture records the open alarms of the moment. Without the filter the
        result also holds every alarm that an operator already handled.

    Args:
        session: The mistapi session.
        scope: The organization and the site to read.

    Returns:
        Every open alarm of the site.
    """
    response = mistapi.api.v1.sites.alarms.searchSiteAlarms(
        session, scope.site_id, acked=ALARM_ACKED, limit=_page_limit()
    )
    return _paged(session, response, scope)


# The four cloud calls of tier 3. A test replaces any entry, so no test opens a
# socket. The radio section is absent on purpose, because it makes no call.
CLOUD_FETCHERS: dict[str, CloudFetch] = {
    SOURCE_PORTS: _fetch_ports,
    SECTION_TUNNELS: _fetch_tunnels,
    SECTION_BGP_PEERS: _fetch_bgp_peers,
    SECTION_ALARMS: _fetch_alarms,
}


def _section_from_response(name: str, response: Any) -> ExtraSection:
    """Classify one cloud answer as a read section or a refused section.

    Args:
        name: The section name.
        response: The cloud response, or the joined pages of one.

    Returns:
        The section. A status outside the 200 range holds no record.
    """
    status = int(getattr(response, "status_code", 0) or 0)
    if not _STATUS_FLOOR <= status < _STATUS_CEILING:
        logger.warning("Upgrade portal read no %s. The cloud answered with status %s", name, status)
        return ExtraSection(name, (), REASON_ERROR_STATUS, status)
    return ExtraSection(name, _records_of(getattr(response, "data", None)), REASON_READ, status)


def _read_section(name: str, session: Any, scope: SiteScope, fetch: CloudFetch) -> ExtraSection:
    """Run one cloud call and turn its answer into a section.

    Why:
        A tier 3 section is optional. This function holds the only error
        boundary of the module, so a failure inside one call never reaches the
        other sections.

    Args:
        name: The section name.
        session: The mistapi session.
        scope: The organization and the site to read.
        fetch: The call to run. A test supplies its own.

    Returns:
        The section, empty and with a reason after a failure.
    """
    try:
        response = fetch(session, scope)
    except Exception as error:  # One optional section must never fail the whole capture
        logger.warning("Upgrade portal could not read %s for site %s: %s", name, scope.site_id, type(error).__name__)
        return ExtraSection(name, (), REASON_CALL_FAILED, 0)
    return _section_from_response(name, response)


def _project(row: Mapping[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    """Copy the named fields of one row.

    Why:
        The key set stays the same for every row and for every capture. A
        comparison then reports a real change of value, and never reports a key
        that only one of the two captures holds.

    Args:
        row: The raw record from the cloud.
        fields: The field names to keep, in order.

    Returns:
        One value for each name. An absent field holds None.
    """
    return {name: row.get(name) for name in fields}


def _radio_record(device: Mapping[str, Any], band: str, entry: Mapping[str, Any]) -> dict[str, Any]:
    """Build one flat radio record.

    Args:
        device: The owning device entry, which supplies the fallback address.
        band: The band name, such as ``band_5``.
        entry: The per-band object of ``radio_stat``.

    Returns:
        The radio record, keyed by device, by band, and by measurement.
    """
    record = _project(entry, _RADIO_FIELDS)
    record["mac"] = entry.get("mac") or device.get("mac")
    record["band"] = band
    return record


def _radios_of_device(device: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Read the per-band radio state of one device.

    Why:
        ``radio_stat`` holds one object for each band, named after the band. A
        capture needs one flat record for each radio, so the band name becomes
        a field of the record.

    Args:
        device: One entry of the tier 2 device statistics.

    Returns:
        One record for each band the device reports. Empty for a device that
        holds no radio, such as a switch or a gateway.
    """
    radio_stat = device.get("radio_stat")
    if not isinstance(radio_stat, Mapping):
        return []
    bands = [(band, radio_stat.get(band)) for band in RADIO_BANDS]
    return [_radio_record(device, band, entry) for band, entry in bands if isinstance(entry, Mapping)]


def _radio_section(device_stats: Sequence[Mapping[str, Any]] | None) -> ExtraSection:
    """Build the radio section out of the tier 2 device statistics.

    Why:
        The radio state already arrived with tier 2. A second call would add
        one request for each access point and return the same values.

    Args:
        device_stats: The tier 2 device statistics. None means that read
            failed, so the section reports an absent source.

    Returns:
        The radio section.
    """
    if device_stats is None:
        logger.warning("Upgrade portal read no radios. The device statistics are absent")
        return ExtraSection(SECTION_RADIOS, (), REASON_SOURCE_ABSENT, 0)
    records: list[dict[str, Any]] = []
    for device in device_stats:
        records.extend(_radios_of_device(device))
    return ExtraSection(SECTION_RADIOS, tuple(records), REASON_READ, 0)


def _read_ports(
    session: Any, scope: SiteScope, sources: SourcePayloads, fetchers: Mapping[str, CloudFetch]
) -> ExtraSection:
    """Return the raw port records that feed the port section and the power section.

    Why:
        Supplied records cost nothing. A caller that already ran the port call
        group hands the rows over and this module makes no call. A caller that
        supplies nothing gets one call, which still feeds both sections.

    Args:
        session: The mistapi session.
        scope: The organization and the site to read.
        sources: The reads that another step already made.
        fetchers: The cloud calls, by name.

    Returns:
        A section named after the shared port read. It is not a capture
        section, so each port section copies its own fields out of it.
    """
    if sources.port_records is not None:
        return ExtraSection(SOURCE_PORTS, tuple(dict(row) for row in sources.port_records), REASON_READ, 0)
    return _read_section(SOURCE_PORTS, session, scope, fetchers[SOURCE_PORTS])


def _derive(source: ExtraSection, name: str, fields: tuple[str, ...]) -> ExtraSection:
    """Copy one field set out of the shared port read.

    Why:
        The switch port state and the power over Ethernet state arrive in the
        same record. Two sections therefore share one read, and a failure of
        that read carries the same reason and the same status into both.

    Args:
        source: The shared port read.
        name: The section name to build.
        fields: The fields that belong to the section.

    Returns:
        The section, with the reason and the status of the shared read.
    """
    records = tuple(_project(row, fields) for row in source.records)
    return ExtraSection(name, records, source.reason, source.http_status)


def collect_extras(
    session: Any,
    scope: SiteScope,
    sources: SourcePayloads | None = None,
    fetchers: Mapping[str, CloudFetch] | None = None,
) -> dict[str, ExtraSection]:
    """Read every tier 3 section of one site.

    Why:
        The result always holds all six names. A caller therefore reads a
        section without a membership test, and a failure in one section never
        removes another. The caller assembles the capture document.

    Args:
        session: The mistapi session. A test never needs a real one.
        scope: The organization and the site to read.
        sources: The reads that another step already made. None asks this
            module to read the ports one time, and reports the radio section as
            an absent source.
        fetchers: Cloud calls that replace the defaults, by name. A test passes
            its own, so no test opens a socket.

    Returns:
        One section for each name of ``SECTION_NAMES``, in that order.
    """
    payloads = sources if sources is not None else SourcePayloads()
    calls: dict[str, CloudFetch] = dict(CLOUD_FETCHERS)
    if fetchers is not None:
        calls.update(fetchers)
    ports = _read_ports(session, scope, payloads, calls)
    sections = {
        SECTION_SWITCH_PORTS: _derive(ports, SECTION_SWITCH_PORTS, _SWITCH_PORT_FIELDS),
        SECTION_POE: _derive(ports, SECTION_POE, _POE_FIELDS),
        SECTION_RADIOS: _radio_section(payloads.device_stats),
    }
    for name in _CALLED_SECTIONS:
        sections[name] = _read_section(name, session, scope, calls[name])
    return sections


def section_records(sections: Mapping[str, ExtraSection]) -> dict[str, list[dict[str, Any]]]:
    """Flatten the sections into the plain map of data-model.md section 3.5.

    Why:
        The capture document holds a list for each section name. The assembly
        step owns that document, so this helper only flattens the sections and
        writes nothing else.

    Args:
        sections: The result of ``collect_extras``.

    Returns:
        One list for each section name, in the order of ``SECTION_NAMES``.
    """
    return {name: list(sections[name].records) for name in SECTION_NAMES if name in sections}


def failed_sections(sections: Mapping[str, ExtraSection]) -> tuple[ExtraSection, ...]:
    """Name the sections that need a partial reason.

    Why:
        The assembly step owns the shape of ``partial_reasons``. This helper
        only selects the failed sections, so the caller reads the name, the
        reason, and the HTTP status straight off each record.

    Args:
        sections: The result of ``collect_extras``.

    Returns:
        Every failed section, in the order of ``SECTION_NAMES``.
    """
    return tuple(sections[name] for name in SECTION_NAMES if name in sections and sections[name].failed)


__all__ = [
    "ALARM_ACKED",
    "CLOUD_FETCHERS",
    "PORT_DEVICE_TYPE",
    "RADIO_BANDS",
    "REASON_CALL_FAILED",
    "REASON_ERROR_STATUS",
    "REASON_READ",
    "REASON_SOURCE_ABSENT",
    "SECTION_ALARMS",
    "SECTION_BGP_PEERS",
    "SECTION_NAMES",
    "SECTION_POE",
    "SECTION_RADIOS",
    "SECTION_SWITCH_PORTS",
    "SECTION_TUNNELS",
    "SOURCE_PORTS",
    "CloudFetch",
    "ExtraSection",
    "SiteScope",
    "SourcePayloads",
    "collect_extras",
    "failed_sections",
    "section_records",
]
