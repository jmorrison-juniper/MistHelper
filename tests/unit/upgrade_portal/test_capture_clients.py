"""Unit tests for the client readers of one upgrade capture.

Why:
    The comparison of two captures matches a client on ``mac`` alone. A slip in
    the address normalization, or a dropped client in the wireless join, reports
    a healthy client as lost after an upgrade. These tests hold the module to
    the record shape of ``specs/1823-upgrade-capture-portal/data-model.md``
    section 3.4.

    Every read takes an injectable row source, and every test passes its own
    source or patches the endpoint with ``unittest.mock``. No test opens a
    socket, and no test reads a credential file.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.upgrade_portal.capture import clients

# WHY: A site key in the shape of the data model, so a reader sees a realistic
# identifier rather than a bare word.
SITE_ID = "site-0f3a9c2b7d1e4f5a8b6c0d2e4f6a8b0c"

# WHY: One address in three written forms. The cloud writes each form, and each
# form must reach the same join key.
COLON_FORM = "AA:BB:CC:DD:EE:FF"
DASH_FORM = "aa-bb-cc-dd-ee-ff"
BARE_FORM = "AABBCCDDEEFF"
NORMAL_FORM = "aabbccddeeff"

# WHY: The switch that serves the wired client. The row holds the separated
# form, and the record must hold the normalized form.
SWITCH_MAC_WRITTEN = "00:11:22:33:44:55"
SWITCH_MAC = "001122334455"
WIRED_HOSTNAME = "desk-01"
WIRED_IP = "10.10.0.7"
WIRED_PORT = "ge-0/0/7"
WIRED_VLAN = 30
WIRED_MANUFACTURE = "Cisco Systems, Inc"

# WHY: The parallel arrays of the wired row hold different values from the
# paired object. A test then proves which of the two sources the reader read.
ARRAY_SWITCH_MAC = "00aa00aa00aa"
ARRAY_IP = "10.10.0.99"
ARRAY_PORT = "ge-0/0/99"
ARRAY_VLAN = 99

# WHY: One raw wired row. It holds no "hostname" key and no "username" key,
# because the wired search endpoint publishes neither.
WIRED_ROW: dict[str, Any] = {
    "mac": COLON_FORM,
    "hostname": [WIRED_HOSTNAME],
    "last_hostname": "desk-01-previous",
    "dhcp_hostname": WIRED_HOSTNAME,
    "manufacture": WIRED_MANUFACTURE,
    "ip": [ARRAY_IP],
    "vlan": [ARRAY_VLAN],
    "device_mac": [ARRAY_SWITCH_MAC],
    "port_id": [ARRAY_PORT],
    "device_mac_port": [{"device_mac": SWITCH_MAC_WRITTEN, "port_id": WIRED_PORT, "vlan": WIRED_VLAN, "ip": WIRED_IP}],
}

# WHY: Three wireless addresses in address order. One address sits in both
# sources, one sits in the statistics source, and one sits in the search source.
BOTH_MAC = "112233445566"
STATS_ONLY_MAC = "223344556677"
SEARCH_ONLY_MAC = "334455667788"

# WHY: The signal strength lives in the statistics source alone. The randomized
# address flag lives in the search source alone. Only a join holds all three.
RSSI = -55
SNR = 38

STATS_BASE: dict[str, Any] = {
    "hostname": "laptop-1",
    "ip": "10.20.0.4",
    "username": "user@example.com",
    "ap_mac": "00:11:22:33:44:77",
    "vlan_id": 40,
    "ssid": "Corp",
    "band": "5",
    "rssi": RSSI,
    "snr": SNR,
}

# WHY: The search row writes most values as an array beside a "last_" scalar.
# The scalar describes the end of the window and sits closest to the capture.
SEARCH_BASE: dict[str, Any] = {
    "last_hostname": "laptop-1",
    "last_ip": "10.20.0.4",
    "last_ap": ["00:11:22:33:44:77"],
    "last_vlan": [40],
    "last_ssid": ["Corp"],
    "band": "5",
    "random_mac": True,
}

GUEST_MAC_WRITTEN = "aa-bb-cc-11-22-33"
GUEST_MAC = "aabbcc112233"
GUEST_NAME = "Jane Visitor"
GUEST_EMAIL = "jane.visitor@example.com"
GUEST_AP_WRITTEN = "00:11:22:33:44:66"
GUEST_AP_MAC = "001122334466"
GUEST_SSID = "Guest"

# WHY: An obviously fake address that stands for the access code of a guest. A
# capture holds no credential, so this value must never reach a record.
ACCESS_CODE_EMAIL = "access-code@example.com"

GUEST_ROW: dict[str, Any] = {
    "mac": GUEST_MAC_WRITTEN,
    "name": GUEST_NAME,
    "email": GUEST_EMAIL,
    "ap_mac": GUEST_AP_WRITTEN,
    "ssid": GUEST_SSID,
    "random_mac": True,
    "access_code_email": ACCESS_CODE_EMAIL,
}

# WHY: The statistics endpoint is a point-in-time list and takes no duration.
# The three search endpoints aggregate a window and take the short duration.
SEARCH_WINDOW: dict[str, Any] = {"duration": clients.SEARCH_DURATION}
FETCH_CASES = [
    ("wired_client_api", "searchSiteWiredClients", clients.fetch_wired_rows, SEARCH_WINDOW),
    ("stats_api", "listSiteWirelessClientsStats", clients.fetch_wireless_stats_rows, {}),
    ("wireless_client_api", "searchSiteWirelessClients", clients.fetch_wireless_search_rows, SEARCH_WINDOW),
    ("guest_api", "searchSiteGuestAuthorization", clients.fetch_guest_rows, SEARCH_WINDOW),
]


def _session() -> MagicMock:
    """Return a stand-in for the cloud session.

    Why:
        Every read takes a session and never inspects it when a test injects a
        row source. The mock holds the shape without a cloud account.

    Returns:
        A fresh mock session.
    """
    return MagicMock(name="session")


def _row_source(rows: list[dict[str, Any]]) -> MagicMock:
    """Return a row source that answers with fixed rows.

    Why:
        The injectable row source is the seam that holds a unit test offline.
        This fake replaces the cloud call, so the test opens no socket.

    Args:
        rows: The raw rows that the source returns.

    Returns:
        A mock that returns the rows for any session and any site.
    """
    return MagicMock(return_value=rows)


def _stats_row(mac: str) -> dict[str, Any]:
    """Return one raw row of the wireless statistics endpoint.

    Why:
        This endpoint holds the signal strength and holds no randomized address
        flag. The join must fill that gap from the other source.

    Args:
        mac: The address, in any written form.

    Returns:
        The raw row.
    """
    return {"mac": mac, **STATS_BASE}


def _search_row(mac: str) -> dict[str, Any]:
    """Return one raw row of the wireless search endpoint.

    Why:
        This endpoint holds the randomized address flag and holds no signal
        strength. The join must fill that gap from the other source.

    Args:
        mac: The address, in any written form.

    Returns:
        The raw row.
    """
    return {"mac": mac, **SEARCH_BASE}


def _one_wired_record() -> clients.ClientRecord:
    """Read the one wired client of the fixed row.

    Why:
        Six wired tests read the same row. One helper builds the record, so no
        test repeats the read.

    Returns:
        The record that the reader built.
    """
    records = clients.read_wired_clients(_session(), SITE_ID, _row_source([WIRED_ROW]))
    assert len(records) == 1, "The wired read must build one record for one row."
    return records[0]


def _one_guest_record() -> clients.ClientRecord:
    """Read the one guest client of the fixed row.

    Why:
        Three guest tests read the same row. One helper builds the record, so
        no test repeats the read.

    Returns:
        The record that the reader built.
    """
    records = clients.read_guest_clients(_session(), SITE_ID, _row_source([GUEST_ROW]))
    assert len(records) == 1, "The guest read must build one record for one row."
    return records[0]


def _joined(stats_rows: list[dict[str, Any]], search_rows: list[dict[str, Any]]) -> list[clients.ClientRecord]:
    """Read the wireless clients from two fake sources.

    Why:
        The wireless read calls both endpoints and joins the answers. A test
        controls each side, so a test can hold one client out of one source.

    Args:
        stats_rows: The raw rows of the statistics endpoint.
        search_rows: The raw rows of the search endpoint.

    Returns:
        The joined records, in address order.
    """
    return clients.read_wireless_clients(_session(), SITE_ID, _row_source(stats_rows), _row_source(search_rows))


def _signal_of(record: clients.ClientRecord) -> clients.WirelessSignal:
    """Return the radio facts of one record.

    Why:
        The record types the radio facts as optional. A test that reads the
        signal strength must first prove that the facts exist.

    Args:
        record: The record to read.

    Returns:
        The radio facts of the record.
    """
    signal = record.wireless
    assert isinstance(signal, clients.WirelessSignal), "A wireless record must hold the radio facts."
    return signal


@pytest.mark.parametrize("written", [COLON_FORM, DASH_FORM, BARE_FORM])
def test_every_written_form_of_one_address_reaches_one_value(written: str) -> None:
    """The colon form, the dash form, and the bare form give one value.

    Why:
        The comparison matches a client on the address alone. A form that
        escaped the normalizer would miss its own match, and the report would
        name a healthy client as lost.

    Args:
        written: One written form of the same address.
    """
    assert clients.normalize_mac(written) == NORMAL_FORM


@pytest.mark.parametrize("value", ["", "aabbccddeef", "aabbccddeeffaa", "gg:bb:cc:dd:ee:ff", None, 112233445566])
def test_a_value_that_is_not_an_address_gives_an_empty_string(value: object) -> None:
    """A short value, a long value, a bad character, and a number give nothing.

    Why:
        A caller drops a record that gets an empty string. An empty key would
        otherwise match every other malformed record.

    Args:
        value: A raw value that is not a media access control address.
    """
    assert clients.normalize_mac(value) == ""


def test_the_wired_read_carries_the_names_of_the_client() -> None:
    """The wired record holds the match key, the host name, and the address.

    Why:
        A wired row holds no ``hostname`` key. The reader must read
        ``dhcp_hostname``, or every wired client reaches the report unnamed.
    """
    record = _one_wired_record()
    identity = record.identity
    assert record.mac == NORMAL_FORM
    assert (identity.hostname, identity.ip) == (WIRED_HOSTNAME, WIRED_IP)


def test_the_wired_read_uses_the_last_host_name_when_hostname_is_empty() -> None:
    """The last host name identifies a client when the current list is empty."""
    row = dict(WIRED_ROW)
    row["hostname"] = []
    records = clients.read_wired_clients(_session(), SITE_ID, _row_source([row]))
    assert records[0].identity.hostname == "desk-01-previous"


def test_the_wired_read_carries_the_manufacturer() -> None:
    """The wired record preserves the manufacturer for the capture table."""
    assert _one_wired_record().identity.manufacture == WIRED_MANUFACTURE


def test_the_wired_read_carries_the_switch_and_the_port() -> None:
    """The wired record holds the serving switch, the port, and the number.

    Why:
        A moved client is the one client outcome that is not a loss. The
        comparison finds the move in this group, so the group must be complete.
    """
    attachment = _one_wired_record().attachment
    assert isinstance(attachment, clients.ClientAttachment)
    assert (attachment.device_mac, attachment.port_id, attachment.vlan) == (SWITCH_MAC, WIRED_PORT, WIRED_VLAN)


def test_the_wired_read_leaves_the_device_name_and_the_user_name_empty() -> None:
    """The wired record holds an empty device name and an empty user name.

    Why:
        No client endpoint returns the name of the serving device, and the
        published wired schema carries no user name key. The record still
        carries both fields. The assembler fills the device name from the
        device index.
    """
    record = _one_wired_record()
    assert record.attachment.device_name == ""
    assert record.identity.username == ""


def test_the_wired_read_keeps_a_user_name_that_the_cloud_supplies() -> None:
    """A wired row that names a user reaches the record with that name.

    Why:
        The published wired schema names ``auth_state`` and ``auth_method`` and
        no user name, so the field is empty for every documented row. A cloud
        that starts to publish an 802.1X identity must not lose it in silence.
        The read asks for the key, so the identity travels the moment the cloud
        offers it.
    """
    rows = [{"mac": COLON_FORM, "dhcp_hostname": WIRED_HOSTNAME, "username": "host/lab-pc.example.test"}]
    records = clients.read_wired_clients(_session(), SITE_ID, _row_source(rows))
    assert len(records) == 1, "The wired read must build one record for one row."
    assert records[0].identity.username == "host/lab-pc.example.test"
    assert records[0].to_dict()["username"] == "host/lab-pc.example.test"


def test_the_wired_record_flattens_to_the_stored_field_names() -> None:
    """The flat record holds the field names of the stored document.

    Why:
        The nested groups exist for the Five-Item Rule only. The stored
        document holds one flat record, and it drops every empty value.
    """
    assert _one_wired_record().to_dict() == {
        "mac": NORMAL_FORM,
        "hostname": WIRED_HOSTNAME,
        "ip": WIRED_IP,
        "manufacture": WIRED_MANUFACTURE,
        "device_mac": SWITCH_MAC,
        "port_id": WIRED_PORT,
        "vlan": WIRED_VLAN,
    }


def test_the_wired_read_falls_back_to_the_parallel_arrays() -> None:
    """A row with no paired port still gives a switch, a port, and a number.

    Why:
        The paired object is the preferred source, because two parallel arrays
        can hold a different length. A row that holds no pair must still reach
        the record, or the capture loses the whole client.
    """
    row = {key: value for key, value in WIRED_ROW.items() if key != "device_mac_port"}
    records = clients.read_wired_clients(_session(), SITE_ID, _row_source([row]))
    attachment = records[0].attachment
    assert (attachment.device_mac, attachment.port_id) == (ARRAY_SWITCH_MAC, ARRAY_PORT)
    assert (attachment.vlan, records[0].identity.ip) == (ARRAY_VLAN, ARRAY_IP)


def test_a_row_with_no_address_never_enters_the_list() -> None:
    """A row with a bad address and a row with no address reach no record.

    Why:
        The address is the whole match key. An empty key would match every
        other malformed record and would report a false move.
    """
    rows: list[dict[str, Any]] = [{"mac": "not-an-address"}, {"dhcp_hostname": "no-address-at-all"}]
    assert clients.read_wired_clients(_session(), SITE_ID, _row_source(rows)) == []


def test_the_wired_read_returns_the_records_in_address_order() -> None:
    """The read sorts the records by address.

    Why:
        The cloud states no row order. An unstable order changes the section
        digest, and a changed digest hides the digest shortcut of the render.
    """
    rows: list[dict[str, Any]] = [{"mac": "ffffffffffff"}, {"mac": "111111111111"}, {"mac": "888888888888"}]
    records = clients.read_wired_clients(_session(), SITE_ID, _row_source(rows))
    assert [record.mac for record in records] == ["111111111111", "888888888888", "ffffffffffff"]


def test_the_read_passes_the_session_and_the_site_to_its_source() -> None:
    """The read calls the injected source once with the session and the site.

    Why:
        The injection is the seam that holds every unit test offline. A read
        that ignored the source would reach the cloud.
    """
    session = _session()
    source = _row_source([WIRED_ROW])
    clients.read_wired_clients(session, SITE_ID, source)
    source.assert_called_once_with(session, SITE_ID)


def test_a_client_in_both_sources_gets_the_signal_and_the_flag() -> None:
    """A client in both wireless sources holds all three radio facts.

    Why:
        Neither wireless endpoint holds every field. Only the merged value
        holds the signal strength, the signal over noise, and the flag.
    """
    records = _joined([_stats_row(BOTH_MAC)], [_search_row(BOTH_MAC)])
    assert [record.mac for record in records] == [BOTH_MAC]
    signal = _signal_of(records[0])
    assert (signal.rssi, signal.snr, signal.random_mac) == (RSSI, SNR, True)


def test_a_client_in_one_source_only_still_enters_the_list() -> None:
    """A client that one source misses still reaches the list.

    Why:
        A drop would report a client as lost after an upgrade that never
        touched it. The join therefore keeps every address of either source.
    """
    records = _joined([_stats_row(STATS_ONLY_MAC)], [_search_row(SEARCH_ONLY_MAC)])
    assert [record.mac for record in records] == [STATS_ONLY_MAC, SEARCH_ONLY_MAC]


def test_the_statistics_source_alone_gives_the_signal_and_no_flag() -> None:
    """A client of the statistics source holds the signal and an unknown flag.

    Why:
        A missing flag and a false flag mean different things. The comparison
        splits the client counts by the flag, so an unknown flag stays unknown.
    """
    records = _joined([_stats_row(STATS_ONLY_MAC)], [])
    signal = _signal_of(records[0])
    assert (signal.rssi, signal.snr) == (RSSI, SNR)
    assert signal.random_mac is None


def test_the_search_source_alone_gives_the_flag_and_no_signal() -> None:
    """A client of the search source holds the flag and no signal strength.

    Why:
        The search endpoint publishes no signal strength. The record must
        report the gap as unknown rather than as a zero reading.
    """
    records = _joined([], [_search_row(SEARCH_ONLY_MAC)])
    signal = _signal_of(records[0])
    assert (signal.rssi, signal.snr) == (None, None)
    assert signal.random_mac is True


def test_the_join_drops_no_client_from_either_source() -> None:
    """Three clients across two sources reach three records in address order.

    Why:
        This is the whole promise of the join. One client sits in both sources,
        one sits in the statistics source, and one sits in the search source.
    """
    stats_rows = [_stats_row(BOTH_MAC), _stats_row(STATS_ONLY_MAC)]
    search_rows = [_search_row(BOTH_MAC), _search_row(SEARCH_ONLY_MAC)]
    records = _joined(stats_rows, search_rows)
    assert [record.mac for record in records] == [BOTH_MAC, STATS_ONLY_MAC, SEARCH_ONLY_MAC]


def test_the_join_matches_two_written_forms_of_one_address() -> None:
    """One client written in two forms reaches one record with both halves.

    Why:
        Both sides normalize the address before the join, so the match ignores
        the letter case and the separator. A normalization slip here would
        build two records for one client and would lose the join.
    """
    records = _joined([_stats_row(COLON_FORM)], [_search_row(DASH_FORM)])
    assert [record.mac for record in records] == [NORMAL_FORM]
    signal = _signal_of(records[0])
    assert (signal.rssi, signal.random_mac) == (RSSI, True)


def test_the_statistics_record_wins_a_field_that_both_sources_hold() -> None:
    """The join keeps the statistics value when the two sources differ.

    Why:
        The statistics endpoint describes the present moment. The search
        endpoint aggregates a window and can hold an older value.
    """
    now = clients.ClientRecord(mac=BOTH_MAC, identity=clients.ClientIdentity(hostname="laptop-now"))
    before = clients.ClientRecord(mac=BOTH_MAC, identity=clients.ClientIdentity(hostname="laptop-before"))
    joined = clients.join_wireless_clients([now], [before])
    assert [record.identity.hostname for record in joined] == ["laptop-now"]


def test_the_guest_read_names_the_visitor_and_the_serving_access_point() -> None:
    """The guest record holds the address, the visitor, and the access point.

    Why:
        A guest row names the person under ``name`` and the identity under
        ``email``. The capture holds a guest as a client of the site.
    """
    record = _one_guest_record()
    assert record.mac == GUEST_MAC
    assert (record.identity.hostname, record.identity.username) == (GUEST_NAME, GUEST_EMAIL)
    assert record.attachment.device_mac == GUEST_AP_MAC


def test_the_guest_read_carries_the_network_name_and_the_random_flag() -> None:
    """The guest record holds the wireless network name and the flag.

    Why:
        A guest joins one wireless network. The comparison reports the network
        name beside the address, so the reader can find the client again.
    """
    signal = _signal_of(_one_guest_record())
    assert (signal.ssid, signal.random_mac) == (GUEST_SSID, True)


def test_the_guest_read_never_carries_the_access_code() -> None:
    """The guest record holds no access code address.

    Why:
        A capture holds no credential. The guest row publishes an access code
        address beside the identity, and the reader must leave it in the row.
    """
    assert ACCESS_CODE_EMAIL not in str(_one_guest_record().to_dict())


@pytest.mark.parametrize(("attribute", "call_name", "fetch", "extra"), FETCH_CASES)
def test_each_fetch_reads_its_own_endpoint_and_keeps_the_mappings(
    attribute: str, call_name: str, fetch: Any, extra: dict[str, Any]
) -> None:
    """Each fetch calls one read endpoint and keeps the mapping rows only.

    Why:
        A capture reads and never writes. The mock proves which endpoint the
        fetch calls, and it proves that no test reaches the network.

    Args:
        attribute: The module member that holds the endpoint.
        call_name: The name of the endpoint function.
        fetch: The fetch function under test.
        extra: The keyword arguments beside the session, site, and page size.
    """
    session = _session()
    with patch.object(clients, attribute) as api, patch.object(clients, "mistapi") as sdk:
        sdk.get_all.return_value = [WIRED_ROW, "not a mapping"]
        rows = fetch(session, SITE_ID)
    getattr(api, call_name).assert_called_once_with(session, SITE_ID, limit=clients.page_limit(), **extra)
    assert rows == [WIRED_ROW]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", clients.DEFAULT_PAGE_LIMIT),
        ("a word", clients.DEFAULT_PAGE_LIMIT),
        ("0", clients.MIN_PAGE_LIMIT),
        ("250", 250),
        ("5000", clients.MAX_PAGE_LIMIT),
    ],
)
def test_the_page_size_stays_inside_its_range(monkeypatch: pytest.MonkeyPatch, raw: str, expected: int) -> None:
    """An empty value, a word, and a number outside the range give a safe size.

    Why:
        The page size reaches the cloud on every read. A zero would return no
        row, and a huge number would fail the request.

    Args:
        monkeypatch: The pytest patch helper.
        raw: The value of the environment variable.
        expected: The page size that the module must report.
    """
    monkeypatch.setenv(clients.PAGE_LIMIT_VARIABLE, raw)
    assert clients.page_limit() == expected
