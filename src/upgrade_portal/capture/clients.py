"""The client readers of one upgrade capture.

Why:
    A comparison of two captures answers one question for an operator. Did
    every client return after the upgrade? The answer needs one stable key,
    so this module normalizes every media access control address to lower case
    with no separator, and the comparison matches on that value alone
    (``specs/1823-upgrade-capture-portal/data-model.md:358``).

    The cloud returns three different row shapes. A wired row holds arrays and
    holds no ``hostname`` key. A wireless statistics row holds scalars and
    signal strength. A wireless search row holds the randomized-address flag
    and holds no signal strength. This module hides all three shapes behind one
    record, so the assembler and the comparison read one shape only.

    Every read takes an injectable row source. A test passes its own source, so
    no test opens a socket.

    Every read returns the records in address order. The cloud states no row
    order. An unstable order changes the section digest of
    ``data-model.md:70``, and a changed digest hides the digest shortcut that
    holds the render inside 3 seconds.

    This module leaves ``device_name`` empty. No client endpoint returns the
    name of the serving device. The assembler fills the name from the device
    index, which holds one name for each device address.

    A failed cloud call raises. This module catches nothing, because the
    assembler owns ``partial_reasons`` and needs the error to record a partial
    capture.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, fields
from typing import Any

import mistapi
from mistapi.api.v1.sites import clients as wireless_client_api
from mistapi.api.v1.sites import guests as guest_api
from mistapi.api.v1.sites import stats as stats_api
from mistapi.api.v1.sites import wired_clients as wired_client_api

logger = logging.getLogger(__name__)

# The search endpoints aggregate a time window and default to one day. A busy
# site then returns far more addresses than it holds now. The research asks for
# a short window here (research/capture-data-sources.md:1175).
SEARCH_DURATION = "1h"

PAGE_LIMIT_VARIABLE = "MIST_PAGE_LIMIT"
DEFAULT_PAGE_LIMIT = 1000
MIN_PAGE_LIMIT = 1
MAX_PAGE_LIMIT = 1000

_ADDRESS_LENGTH = 12
_ADDRESS_SEPARATORS = str.maketrans("", "", ":-. \t")
_HEX_DIGITS = frozenset("0123456789abcdef")

Row = Mapping[str, Any]
RowReader = Callable[[Any, str], list[dict[str, Any]]]


# ---------------------------------------------------------------------------
# The records
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ClientIdentity:
    """The names that a client carries.

    Why:
        Three sources name a client with three different keys. A wired row uses
        ``dhcp_hostname``, a wireless statistics row uses ``hostname``, and a
        guest row uses ``name``. One group holds the resolved names, so a
        reader never asks which source produced the record.

    Attributes:
        hostname: The learned host name. Empty when no source holds one.
        ip: The address of the client on the network. Empty when absent.
        username: The identity from the authentication exchange. Never a
            password and never an access code.
        manufacture: The client manufacturer. Empty when the cloud does not
            identify it.
    """

    hostname: str = ""
    ip: str = ""
    username: str = ""
    manufacture: str = ""


@dataclass(frozen=True, slots=True)
class ClientAttachment:
    """The device that serves one client.

    Why:
        A moved client is the one client outcome that is not a loss
        (``data-model.md:363``). The comparison finds a move when this group
        differs and the address stays the same, so the serving device sits in
        its own group.

    Attributes:
        device_mac: The address of the serving switch or access point. Lower
            case with no separator.
        device_name: The name of the serving device. This module leaves the
            name empty, and the assembler fills it from the device index.
        port_id: The switch port. Wired clients only.
        vlan: The virtual local area network number. None when absent.
    """

    device_mac: str = ""
    device_name: str = ""
    port_id: str = ""
    vlan: int | None = None


@dataclass(frozen=True, slots=True)
class WirelessSignal:
    """The radio facts of one wireless client or one guest client.

    Why:
        Two endpoints hold these facts and neither holds all of them. The
        statistics endpoint holds ``rssi`` and ``snr``. The search endpoint
        holds ``random_mac``. One group holds both halves, so the join fills
        the gaps in one place.

    Attributes:
        ssid: The wireless network name.
        band: The radio band. The cloud reports ``24``, ``5``, or ``6``.
        rssi: The signal strength. None outside the statistics endpoint.
        snr: The signal over noise. None outside the statistics endpoint.
        random_mac: True when the client used a randomized address. None
            outside the search endpoint.
    """

    ssid: str = ""
    band: str = ""
    rssi: int | None = None
    snr: int | None = None
    random_mac: bool | None = None


@dataclass(frozen=True, slots=True)
class ClientRecord:
    """One client of one site at the moment of the capture.

    Why:
        The data model names 13 flat fields for this record
        (``data-model.md:138``). The Five-Item Rule caps a dataclass at 5
        fields, so this record groups the 13 fields by the question each field
        answers. ``ClientIdentity`` answers who the client is.
        ``ClientAttachment`` answers what serves it. ``WirelessSignal`` answers
        how the radio performed. Every group holds 5 fields or fewer, and each
        group also matches one comparison outcome, so the comparison reads one
        group instead of a field list.

        ``to_dict`` returns the flat 13-field shape that the stored document
        needs, so the split costs the document nothing.

    Attributes:
        mac: The match key. Lower case with no separator. Never empty.
        identity: The names that the client carries.
        attachment: The device that serves the client.
        wireless: The radio facts. None for a wired client.
    """

    mac: str
    identity: ClientIdentity = field(default_factory=ClientIdentity)
    attachment: ClientAttachment = field(default_factory=ClientAttachment)
    wireless: WirelessSignal | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return the flat record shape of the stored capture.

        Why:
            The data model stores one flat record for each client. The nested
            groups exist for the Five-Item Rule, and the document must not
            carry them. The result drops every empty value, because the data
            model treats an absent field and an empty field as one state. The
            drop also holds the section digest stable when one source of the
            wireless join holds a field and the other source does not.

        Returns:
            The flat record. It always holds ``mac``. It holds every other
            field that carries a value.
        """
        flat: dict[str, Any] = {"mac": self.mac}
        flat.update(_filled_fields(self.identity))
        flat.update(_filled_fields(self.attachment))
        if self.wireless is not None:
            flat.update(_filled_fields(self.wireless))
        return flat


# ---------------------------------------------------------------------------
# The address normalizer
# ---------------------------------------------------------------------------


def normalize_mac(value: object) -> str:
    """Return one media access control address in lower case with no separator.

    Why:
        The comparison matches a client on ``mac`` alone and matches a device
        on the same form (``data-model.md:95``). The cloud writes an address in
        several forms, so one address would otherwise miss its own match. This
        function is the single form for the whole capture path, and the device
        reader calls it too.

    Args:
        value: The raw value from a cloud row. Any type is safe here, because a
            row may hold a number, a null, or a missing key.

    Returns:
        The 12 hexadecimal characters of the address in lower case. An empty
        string when the value is not a media access control address. A caller
        drops a record that gets an empty string, because an empty key would
        match every other malformed record.
    """
    if not isinstance(value, str):
        return ""
    cleaned = value.translate(_ADDRESS_SEPARATORS).lower()
    if len(cleaned) != _ADDRESS_LENGTH:
        return ""
    if not _HEX_DIGITS.issuperset(cleaned):
        return ""
    return cleaned


# ---------------------------------------------------------------------------
# The cloud row sources
# ---------------------------------------------------------------------------


def fetch_wired_rows(session: Any, site_id: str) -> list[dict[str, Any]]:
    """Read every wired client row of one site.

    Why:
        No point-in-time wired call exists. The search call is the only full
        wired list (``research/capture-data-sources.md:278``).

    Args:
        session: The mistapi session.
        site_id: The site to read.

    Returns:
        Every row of every page.
    """
    response = wired_client_api.searchSiteWiredClients(session, site_id, limit=page_limit(), duration=SEARCH_DURATION)
    return _collect(session, response)


def fetch_wireless_stats_rows(session: Any, site_id: str) -> list[dict[str, Any]]:
    """Read the connected wireless clients of one site.

    Why:
        This call returns the connected clients only, and it is the one source
        of signal strength (``research/capture-data-sources.md:176``).

    Args:
        session: The mistapi session.
        site_id: The site to read.

    Returns:
        Every row of every page.
    """
    response = stats_api.listSiteWirelessClientsStats(session, site_id, limit=page_limit())
    return _collect(session, response)


def fetch_wireless_search_rows(session: Any, site_id: str) -> list[dict[str, Any]]:
    """Read the wireless clients of one site over a short window.

    Why:
        This call is the one source of the randomized-address flag. The
        statistics call holds no such flag
        (``research/capture-data-sources.md:1002``).

    Args:
        session: The mistapi session.
        site_id: The site to read.

    Returns:
        Every row of every page.
    """
    response = wireless_client_api.searchSiteWirelessClients(
        session, site_id, limit=page_limit(), duration=SEARCH_DURATION
    )
    return _collect(session, response)


def fetch_guest_rows(session: Any, site_id: str) -> list[dict[str, Any]]:
    """Read the guest authorizations of one site.

    Why:
        The search call takes ``limit`` and pages, and the plain list call does
        not. This call also reads only. The update call and the delete call of
        the same module write, and a capture never writes to the cloud.

    Args:
        session: The mistapi session.
        site_id: The site to read.

    Returns:
        Every row of every page.
    """
    response = guest_api.searchSiteGuestAuthorization(session, site_id, limit=page_limit(), duration=SEARCH_DURATION)
    return _collect(session, response)


def page_limit() -> int:
    """Return the page size for one paged read.

    Why:
        A large page holds the request count down. The repository already
        offers this control through one environment variable, and the capture
        path follows the same control instead of adding a second one.

    Returns:
        The page size, held between ``MIN_PAGE_LIMIT`` and ``MAX_PAGE_LIMIT``.
    """
    raw = os.environ.get(PAGE_LIMIT_VARIABLE, "").strip()
    if not raw.isdigit():
        return DEFAULT_PAGE_LIMIT
    return max(MIN_PAGE_LIMIT, min(MAX_PAGE_LIMIT, int(raw)))


def _collect(session: Any, response: Any) -> list[dict[str, Any]]:
    """Return every row of a paged response.

    Why:
        The pagination helper returns an empty list for a shape it does not
        know, and it raises nothing and logs nothing
        (``research/capture-data-sources.md:6.2``). A silent empty list would
        read as a site with no clients, so this function reports the count.

    Args:
        session: The mistapi session.
        response: The first response of the read.

    Returns:
        Every row that is a mapping.
    """
    rows = mistapi.get_all(session, response)
    kept = [row for row in rows if isinstance(row, dict)]
    logger.debug("Upgrade capture read %s client rows.", len(kept))
    return kept


# ---------------------------------------------------------------------------
# The public reads
# ---------------------------------------------------------------------------


def read_wired_clients(session: Any, site_id: str, source: RowReader | None = None) -> list[ClientRecord]:
    """Read the wired clients of one site.

    Args:
        session: The mistapi session.
        site_id: The site to read.
        source: The row source. None reads the cloud. A test passes its own
            source, so the test opens no socket.

    Returns:
        One record for each row that holds an address, in address order.
    """
    rows = (source or fetch_wired_rows)(session, site_id)
    return _build_records(rows, _wired_record)


def read_wireless_clients(
    session: Any,
    site_id: str,
    stats_source: RowReader | None = None,
    search_source: RowReader | None = None,
) -> list[ClientRecord]:
    """Read the wireless clients of one site from both sources.

    Why:
        Neither wireless endpoint holds every field. The statistics endpoint
        holds the signal strength and the search endpoint holds the
        randomized-address flag, so the read calls both and joins the results
        (``research/capture-data-sources.md:1016``).

    Args:
        session: The mistapi session.
        site_id: The site to read.
        stats_source: The row source for the statistics endpoint. None reads
            the cloud.
        search_source: The row source for the search endpoint. None reads the
            cloud.

    Returns:
        One record for each address in either source, in address order.
    """
    stats_rows = (stats_source or fetch_wireless_stats_rows)(session, site_id)
    search_rows = (search_source or fetch_wireless_search_rows)(session, site_id)
    stats_records = _build_records(stats_rows, _wireless_stats_record)
    search_records = _build_records(search_rows, _wireless_search_record)
    return join_wireless_clients(stats_records, search_records)


def read_guest_clients(session: Any, site_id: str, source: RowReader | None = None) -> list[ClientRecord]:
    """Read the guest clients of one site.

    Why:
        A guest row is an authorization record. It carries a serving access
        point and a wireless network name, so the capture holds a guest as a
        client and keeps the guest list apart from the wireless list.

    Args:
        session: The mistapi session.
        site_id: The site to read.
        source: The row source. None reads the cloud.

    Returns:
        One record for each row that holds an address, in address order.
    """
    rows = (source or fetch_guest_rows)(session, site_id)
    return _build_records(rows, _guest_record)


def join_wireless_clients(
    stats_records: Sequence[ClientRecord],
    search_records: Sequence[ClientRecord],
) -> list[ClientRecord]:
    """Join the two wireless sources on the address.

    Why:
        A client that one source holds and the other source misses still
        belongs in the capture (``data-model.md:154``). A drop would report a
        client as lost after an upgrade that never touched it.

    Args:
        stats_records: The records of the statistics endpoint. These records
            win a difference, because they describe the present moment.
        search_records: The records of the search endpoint.

    Returns:
        One record for each address in either source, in address order. A
        record from one source keeps the fields of that source only.
    """
    joined: dict[str, ClientRecord] = {record.mac: record for record in stats_records}
    for record in search_records:
        held = joined.get(record.mac)
        joined[record.mac] = _merge_records(held, record) if held is not None else record
    return sorted(joined.values(), key=_address_of)


# ---------------------------------------------------------------------------
# The row mappers
# ---------------------------------------------------------------------------


def _wired_record(row: Row) -> ClientRecord | None:
    """Return one wired client record.

    Why:
        A wired row holds arrays for ``ip``, ``vlan``, ``device_mac``, and
        ``port_id``, and it holds no ``hostname`` key
        (``research/capture-data-sources.md:286``). The row also holds
        ``device_mac_port``, which pairs a device with its port. The pair beats
        the parallel arrays, because two arrays can hold a different length.

        The published wired schema carries no ``username`` key. Both
        ``documentation/api/sites/GET_sites_site_id_wired_clients_search.md``
        and the organization variant name ``auth_state`` and ``auth_method``
        and no user name. The read still asks for the key. A cloud that starts
        to publish an 802.1X identity then reaches the record on its own, and a
        cloud that publishes none leaves the field empty, which
        ``data-model.md:154`` allows.

    Args:
        row: One raw row of the wired search.

    Returns:
        The record, or None when the row holds no address.
    """
    mac = normalize_mac(row.get("mac"))
    if not mac:
        return None
    paired = _first(row.get("device_mac_port"))
    pair: Row = paired if isinstance(paired, Mapping) else {}
    identity = ClientIdentity(
        hostname=_wired_hostname(row),
        ip=_text(pair.get("ip") or row.get("ip")),
        username=_text(row.get("username")),
        manufacture=_text(row.get("manufacture")),
    )
    return ClientRecord(mac=mac, identity=identity, attachment=_wired_attachment(row, pair))


def _wired_hostname(row: Row) -> str:
    """Return the usable host name from one wired-client response.

    Why:
        Mist has returned a host name under three keys. A current response can
        hold `hostname` as a list and `last_hostname` as a scalar. The capture
        keeps one value so the table does not display a list.

    Args:
        row: One raw wired-client response.

    Returns:
        The first usable host name from the current and older response keys.
    """
    return _text(row.get("hostname")) or _text(row.get("last_hostname")) or _text(row.get("dhcp_hostname"))


def _wired_attachment(row: Row, pair: Row) -> ClientAttachment:
    """Return the switch and the port that serve one wired client.

    Args:
        row: One raw row of the wired search.
        pair: The first ``device_mac_port`` member of the row. Empty when the
            row holds none.

    Returns:
        The attachment. ``device_name`` stays empty for the assembler.
    """
    return ClientAttachment(
        device_mac=normalize_mac(pair.get("device_mac") or _first(row.get("device_mac"))),
        port_id=_text(pair.get("port_id") or row.get("port_id")),
        vlan=_number(_present(pair.get("vlan"), row.get("vlan"))),
    )


def _wireless_stats_record(row: Row) -> ClientRecord | None:
    """Return one wireless client record from the statistics endpoint.

    Why:
        This row holds scalars and holds the signal strength. It holds no
        randomized-address flag, so ``random_mac`` stays None until the join.

    Args:
        row: One raw row of the statistics endpoint.

    Returns:
        The record, or None when the row holds no address.
    """
    mac = normalize_mac(row.get("mac"))
    if not mac:
        return None
    identity = ClientIdentity(
        hostname=_text(row.get("hostname")),
        ip=_text(row.get("ip")),
        username=_text(row.get("username")),
    )
    attachment = ClientAttachment(device_mac=normalize_mac(row.get("ap_mac")), vlan=_number(row.get("vlan_id")))
    signal = WirelessSignal(
        ssid=_text(row.get("ssid")),
        band=_text(row.get("band")),
        rssi=_number(row.get("rssi")),
        snr=_number(row.get("snr")),
    )
    return ClientRecord(mac=mac, identity=identity, attachment=attachment, wireless=signal)


def _wireless_search_record(row: Row) -> ClientRecord | None:
    """Return one wireless client record from the search endpoint.

    Why:
        This row holds an array for most concepts and a ``last_`` scalar beside
        it. The scalar describes the end of the window, which is the closest
        value to the moment of the capture. The row holds no signal strength,
        so ``rssi`` and ``snr`` stay None until the join.

    Args:
        row: One raw row of the search endpoint.

    Returns:
        The record, or None when the row holds no address.
    """
    mac = normalize_mac(row.get("mac"))
    if not mac:
        return None
    identity = ClientIdentity(
        hostname=_text(_present(row.get("last_hostname"), row.get("hostname"))),
        ip=_text(_present(row.get("last_ip"), row.get("ip"))),
        username=_text(row.get("username")),
    )
    attachment = ClientAttachment(
        device_mac=normalize_mac(_first(_present(row.get("last_ap"), row.get("ap")))),
        vlan=_number(_present(row.get("last_vlan"), row.get("vlan"))),
    )
    signal = WirelessSignal(
        ssid=_text(_present(row.get("last_ssid"), row.get("ssid"))),
        band=_text(row.get("band")),
        random_mac=_flag(row.get("random_mac")),
    )
    return ClientRecord(mac=mac, identity=identity, attachment=attachment, wireless=signal)


def _guest_record(row: Row) -> ClientRecord | None:
    """Return one guest client record.

    Why:
        A guest row names the person and never the credential. ``name`` is the
        text the guest typed, so it fills ``hostname``. ``email`` is the guest
        identity, so it fills ``username``. The row also holds
        ``access_code_email``, and this function never reads it.

    Args:
        row: One raw row of the guest search.

    Returns:
        The record, or None when the row holds no address.
    """
    mac = normalize_mac(row.get("mac"))
    if not mac:
        return None
    identity = ClientIdentity(hostname=_text(row.get("name")), username=_text(row.get("email")))
    attachment = ClientAttachment(device_mac=normalize_mac(row.get("ap_mac")))
    signal = WirelessSignal(ssid=_text(row.get("ssid")), random_mac=_flag(row.get("random_mac")))
    return ClientRecord(mac=mac, identity=identity, attachment=attachment, wireless=signal)


# ---------------------------------------------------------------------------
# The merge of two sources
# ---------------------------------------------------------------------------


def _merge_records(primary: ClientRecord, secondary: ClientRecord) -> ClientRecord:
    """Return one record built from two records with the same address.

    Args:
        primary: The record that wins a difference.
        secondary: The record that fills a gap.

    Returns:
        The merged record.
    """
    return ClientRecord(
        mac=primary.mac,
        identity=_merge_identity(primary.identity, secondary.identity),
        attachment=_merge_attachment(primary.attachment, secondary.attachment),
        wireless=_merge_signal(primary.wireless, secondary.wireless),
    )


def _merge_identity(primary: ClientIdentity, secondary: ClientIdentity) -> ClientIdentity:
    """Return the names of two records with the same address.

    Args:
        primary: The names that win a difference.
        secondary: The names that fill a gap.

    Returns:
        The merged names.
    """
    return ClientIdentity(
        hostname=_present(primary.hostname, secondary.hostname) or "",
        ip=_present(primary.ip, secondary.ip) or "",
        username=_present(primary.username, secondary.username) or "",
        manufacture=_present(primary.manufacture, secondary.manufacture) or "",
    )


def _merge_attachment(primary: ClientAttachment, secondary: ClientAttachment) -> ClientAttachment:
    """Return the serving device of two records with the same address.

    Args:
        primary: The attachment that wins a difference.
        secondary: The attachment that fills a gap.

    Returns:
        The merged attachment.
    """
    return ClientAttachment(
        device_mac=_present(primary.device_mac, secondary.device_mac) or "",
        device_name=_present(primary.device_name, secondary.device_name) or "",
        port_id=_present(primary.port_id, secondary.port_id) or "",
        vlan=_number(_present(primary.vlan, secondary.vlan)),
    )


def _merge_signal(primary: WirelessSignal | None, secondary: WirelessSignal | None) -> WirelessSignal | None:
    """Return the radio facts of two records with the same address.

    Why:
        This merge carries the whole value of the join. The statistics source
        holds ``rssi`` and ``snr``. The search source holds ``random_mac``.
        Only the merged value holds all three.

    Args:
        primary: The radio facts that win a difference.
        secondary: The radio facts that fill a gap.

    Returns:
        The merged radio facts, or None when neither record holds any.
    """
    if primary is None:
        return secondary
    if secondary is None:
        return primary
    return WirelessSignal(
        ssid=_present(primary.ssid, secondary.ssid) or "",
        band=_present(primary.band, secondary.band) or "",
        rssi=_number(_present(primary.rssi, secondary.rssi)),
        snr=_number(_present(primary.snr, secondary.snr)),
        random_mac=_flag(_present(primary.random_mac, secondary.random_mac)),
    )


# ---------------------------------------------------------------------------
# The small readers of one raw value
# ---------------------------------------------------------------------------


def _build_records(rows: Sequence[Row], mapper: Callable[[Row], ClientRecord | None]) -> list[ClientRecord]:
    """Return one record for each row that holds an address.

    Why:
        A row with no address cannot take part in the comparison, because the
        address is the whole match key. The count of the dropped rows reaches
        the log, so an operator sees a source that returns malformed rows.

    Args:
        rows: The raw rows of one read.
        mapper: The function that turns one row into one record.

    Returns:
        The records in address order.
    """
    records = [record for record in (mapper(row) for row in rows) if record is not None]
    dropped = len(rows) - len(records)
    if dropped > 0:
        logger.warning("Upgrade capture dropped %s client rows that hold no valid address.", dropped)
    return sorted(records, key=_address_of)


def _address_of(record: ClientRecord) -> str:
    """Return the sort key of one client record.

    Args:
        record: The record to sort.

    Returns:
        The address of the client.
    """
    return record.mac


def _filled_fields(record: Any) -> dict[str, Any]:
    """Return the named fields of one record group that hold a value.

    Args:
        record: One frozen record group.

    Returns:
        Each field name with its value. A None value and an empty string stay
        out of the result.
    """
    named = ((item.name, getattr(record, item.name)) for item in fields(record))
    return {name: value for name, value in named if value is not None and value != ""}


def _present(primary: Any, secondary: Any) -> Any:
    """Return the first value of two that holds content.

    Why:
        The same concept arrives under two keys and from two sources. One rule
        picks between them, so no mapper repeats the rule.

    Args:
        primary: The preferred value.
        secondary: The value that fills a gap.

    Returns:
        The primary value when it holds content. The secondary value in every
        other case.
    """
    if primary is None or primary == "":
        return secondary
    return primary


def _first(value: object) -> object:
    """Return the first member of a list, or the value itself.

    Why:
        A search row holds an array where a statistics row holds a scalar. One
        function reads both, so no mapper tests the type again.

    Args:
        value: The raw value from a row.

    Returns:
        The first member of a list, None for an empty list, or the value.
    """
    if isinstance(value, list):
        return value[0] if value else None
    return value


def _text(value: object) -> str:
    """Return one text field of a row.

    Args:
        value: The raw value from a row.

    Returns:
        The text with no leading space and no trailing space. An empty string
        when the value is not text.
    """
    picked = _first(value)
    return picked.strip() if isinstance(picked, str) else ""


def _number(value: object) -> int | None:
    """Return one whole number field of a row.

    Why:
        The cloud writes a virtual local area network number as a number in one
        endpoint and as text in another endpoint. The stored document holds an
        integer in both cases (``data-model.md:146``).

    Args:
        value: The raw value from a row.

    Returns:
        The whole number, or None when the value is not a number.
    """
    picked = _first(value)
    if isinstance(picked, bool):
        return None
    if isinstance(picked, int | float):
        return int(picked)
    if isinstance(picked, str) and picked.strip().lstrip("-").isdigit():
        return int(picked)
    return None


def _flag(value: object) -> bool | None:
    """Return one true or false field of a row.

    Why:
        A missing flag and a false flag mean different things. The comparison
        splits the client statistics by ``random_mac``, so an unknown flag must
        stay unknown (``research/capture-data-sources.md:1019``).

    Args:
        value: The raw value from a row.

    Returns:
        The flag, or None when the row holds no flag.
    """
    picked = _first(value)
    return picked if isinstance(picked, bool) else None


__all__ = [
    "DEFAULT_PAGE_LIMIT",
    "MAX_PAGE_LIMIT",
    "MIN_PAGE_LIMIT",
    "PAGE_LIMIT_VARIABLE",
    "SEARCH_DURATION",
    "ClientAttachment",
    "ClientIdentity",
    "ClientRecord",
    "WirelessSignal",
    "fetch_guest_rows",
    "fetch_wired_rows",
    "fetch_wireless_search_rows",
    "fetch_wireless_stats_rows",
    "join_wireless_clients",
    "normalize_mac",
    "page_limit",
    "read_guest_clients",
    "read_wired_clients",
    "read_wireless_clients",
]
