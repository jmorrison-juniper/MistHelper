"""Unit tests for the tier 3 extra reads of one upgrade capture.

Why:
    Tier 3 is optional and tier 2 is the default, so a tier 3 failure must
    never fail a capture. These tests prove that one refused call, one raised
    call, and one absent source each cost their own section and nothing more.

    They also prove the two efficiency claims of the plan. The radio section
    owns no cloud call at all, and the power over Ethernet section rides on the
    same read as the switch port section.

    Every test asserts on a ``REASON_`` constant, never on the message text. A
    message may change for Simplified Technical English at any time, and the
    reason code stays stable.

    No test opens a socket and no test reaches the Mist cloud. Every test
    replaces the four cloud calls with a fake that answers from memory.
"""

from __future__ import annotations

import logging
from types import SimpleNamespace
from typing import Any

import pytest

from src.upgrade_portal.capture import extras

_SCOPE = extras.SiteScope("org-0001", "site-0001")  # WHY: One scope serves every test in this module.
_FAULT_MESSAGE = "The page walk failed."  # WHY: No log record may repeat this, so one test asserts its absence.

_SWITCH_MAC = "5c5b350e0001"
_AP_MAC = "5c5b350e0002"
_GATEWAY_MAC = "5c5b350e0003"

# One port row. It holds no ``port_usage``, no ``neighbor_port_desc``, and no
# ``poe_priority``, so the tests prove that an absent field becomes None.
_PORT_STATE = {"mac": _SWITCH_MAC, "port_id": "ge-0/0/1", "up": True, "speed": 1000, "full_duplex": True}
_PORT_NEIGHBOR = {"mac_count": 2, "neighbor_mac": "aabbccddeeff", "neighbor_system_name": "printer-01"}
_PORT_POWER = {"poe_disabled": False, "poe_mode": "802.3at", "poe_on": True, "power_draw": 12.5}
_PORT_ROW = {**_PORT_STATE, **_PORT_NEIGHBOR, **_PORT_POWER}

# One access point with two of the three bands. The absent ``band_6`` proves
# that a band the device does not report costs no record.
_RADIO_24 = {"channel": 6, "power": 11, "bandwidth": 20, "noise_floor": None, "num_wlans": 3}
_RADIO_5 = {"channel": 44, "power": 14, "bandwidth": 80, "noise_floor": -96, "num_clients": 7}
_AP_STAT = {"mac": _AP_MAC, "type": "ap", "radio_stat": {"band_24": _RADIO_24, "band_5": _RADIO_5}}
_SWITCH_STAT = {"mac": _SWITCH_MAC, "type": "switch"}  # WHY: A switch holds no radio_stat field.

_TUNNEL_ROW = {"mac": _GATEWAY_MAC, "state": "up", "peer_host": "203.0.113.10", "protocol": "ipsec"}
_BGP_ROW = {"mac": _GATEWAY_MAC, "neighbor": "10.0.0.1", "state": "Established", "rx_routes": 42}
_ALARM_ROW = {"id": "alarm-0001", "type": "device_down", "severity": "critical", "acked": False}

_ROWS: dict[str, list[dict[str, Any]]] = {
    extras.SOURCE_PORTS: [_PORT_ROW],
    extras.SECTION_TUNNELS: [_TUNNEL_ROW],
    extras.SECTION_BGP_PEERS: [_BGP_ROW],
    extras.SECTION_ALARMS: [_ALARM_ROW],
}


class _FakeCall:
    """One cloud call that a test controls.

    Why:
        Every cloud call of this module arrives through an injectable seam. The
        fake answers from memory, counts each call, and raises on demand, so a
        test proves both the failure path and the claim that a supplied payload
        costs no call. No test opens a socket.
    """

    def __init__(self, response: Any = None, error: Exception | None = None) -> None:
        """Create a fake call that answers with one response, or raises.

        Args:
            response: The value that the call returns.
            error: The error that the call raises instead of answering.
        """
        self.response = response  # WHY: The answer that the fake hands back.
        self.error = error  # WHY: A test sets this value to fail the call.
        self.scopes: list[extras.SiteScope] = []  # WHY: Records each call, so a test counts them.

    def __call__(self, session: Any, scope: extras.SiteScope) -> Any:
        """Answer one cloud call.

        Args:
            session: The session. The fake ignores it.
            scope: The organization and the site of the call.

        Returns:
            The response that the test supplied.

        Raises:
            Exception: The error that the test placed in ``error``.
        """
        self.scopes.append(scope)
        if self.error is not None:
            raise self.error
        return self.response


def _response(rows: list[dict[str, Any]] | dict[str, Any], status_code: int = 200) -> SimpleNamespace:
    """Return one cloud answer that a test builds in memory.

    Args:
        rows: The rows of the answer, either as a list or under a ``results`` key.
        status_code: The HTTP status of the answer.

    Returns:
        A stand-in with the two fields that the reader looks at.
    """
    return SimpleNamespace(status_code=status_code, data=rows)


def _fake_calls() -> dict[str, _FakeCall]:
    """Return one controllable fake for every cloud call of the module.

    Why:
        A test that leaves one default call in place would reach the cloud.
        This builder covers every name, so a test starts from a state where no
        call can leave the process.

    Returns:
        One fake for each name of ``CLOUD_FETCHERS``, each holding one row.
    """
    return {name: _FakeCall(_response(_ROWS[name])) for name in extras.CLOUD_FETCHERS}


def _collect(calls: dict[str, _FakeCall], sources: extras.SourcePayloads | None = None) -> dict[str, Any]:
    """Run the tier 3 reads against fake cloud calls.

    Args:
        calls: The fake calls, by name.
        sources: The reads that another step already made.

    Returns:
        One section for each tier 3 section name.
    """
    return extras.collect_extras(object(), _SCOPE, sources, calls)


# ---------------------------------------------------------------------------
# The six sections
# ---------------------------------------------------------------------------


def test_collect_extras_returns_every_section_name() -> None:
    """The result holds all six sections, in the order of the data model."""
    sections = _collect(_fake_calls(), extras.SourcePayloads(device_stats=[_AP_STAT]))
    assert tuple(sections) == extras.SECTION_NAMES
    assert all(sections[name].reason == extras.REASON_READ for name in extras.SECTION_NAMES)


def test_collect_extras_reads_the_switch_port_state() -> None:
    """The switch port section holds the port fields of the shared port read."""
    section = _collect(_fake_calls())[extras.SECTION_SWITCH_PORTS]
    assert section.reason == extras.REASON_READ
    assert section.http_status == 200
    assert section.records[0]["port_id"] == "ge-0/0/1"
    assert section.records[0]["up"] is True
    assert section.records[0]["speed"] == 1000
    assert "poe_mode" not in section.records[0]


def test_collect_extras_reads_the_power_state_from_the_same_port_read() -> None:
    """The power section holds the power fields of the same shared port read.

    Why:
        The plan claims that the power section costs no request of its own. One
        call therefore feeds two sections, and the fake counts that one call.
    """
    calls = _fake_calls()
    section = _collect(calls)[extras.SECTION_POE]
    assert len(calls[extras.SOURCE_PORTS].scopes) == 1
    assert section.records[0]["poe_on"] is True
    assert section.records[0]["power_draw"] == 12.5
    assert "speed" not in section.records[0]


def test_collect_extras_reads_one_radio_record_for_each_reported_band() -> None:
    """The radio section holds one flat record for each band the device reports."""
    sources = extras.SourcePayloads(device_stats=[_AP_STAT, _SWITCH_STAT])
    section = _collect(_fake_calls(), sources)[extras.SECTION_RADIOS]
    assert section.reason == extras.REASON_READ
    assert [record["band"] for record in section.records] == ["band_24", "band_5"]
    assert all(record["mac"] == _AP_MAC for record in section.records)
    assert section.records[1]["channel"] == 44
    assert section.records[0]["num_clients"] is None


def test_collect_extras_reads_the_tunnel_state() -> None:
    """The tunnel section holds the rows of the organization scope tunnel call."""
    calls = _fake_calls()
    section = _collect(calls)[extras.SECTION_TUNNELS]
    assert section.records == (_TUNNEL_ROW,)
    assert calls[extras.SECTION_TUNNELS].scopes == [_SCOPE]


def test_collect_extras_reads_the_bgp_peer_state() -> None:
    """The BGP section holds the peer rows of the site scope call."""
    section = _collect(_fake_calls())[extras.SECTION_BGP_PEERS]
    assert section.records == (_BGP_ROW,)
    assert section.records[0]["state"] == "Established"


def test_collect_extras_reads_the_open_alarms() -> None:
    """The alarm section holds the alarm rows of the site scope call."""
    section = _collect(_fake_calls())[extras.SECTION_ALARMS]
    assert section.records == (_ALARM_ROW,)
    assert section.reason == extras.REASON_READ


# ---------------------------------------------------------------------------
# The two sections that cost no extra cloud call
# ---------------------------------------------------------------------------


def test_the_radio_section_owns_no_cloud_call() -> None:
    """No cloud call exists for the radio section.

    Why:
        The radio state rides inside the tier 2 device statistics. A call of its
        own would add one request for each access point for the same values.
    """
    assert extras.SECTION_RADIOS not in extras.CLOUD_FETCHERS
    assert set(extras.CLOUD_FETCHERS) == {
        extras.SOURCE_PORTS,
        extras.SECTION_TUNNELS,
        extras.SECTION_BGP_PEERS,
        extras.SECTION_ALARMS,
    }


def test_collect_extras_makes_no_port_call_when_the_caller_supplies_the_ports() -> None:
    """Supplied port records cost no cloud call and still feed both port sections."""
    calls = _fake_calls()
    sources = extras.SourcePayloads(port_records=[_PORT_ROW])
    sections = _collect(calls, sources)
    assert calls[extras.SOURCE_PORTS].scopes == []
    assert sections[extras.SECTION_SWITCH_PORTS].records[0]["port_id"] == "ge-0/0/1"
    assert sections[extras.SECTION_POE].records[0]["poe_mode"] == "802.3at"


def test_collect_extras_asks_the_cloud_for_the_ports_when_the_caller_supplies_none() -> None:
    """One port call runs when the caller supplies no port records."""
    calls = _fake_calls()
    _collect(calls)
    assert calls[extras.SOURCE_PORTS].scopes == [_SCOPE]


# ---------------------------------------------------------------------------
# An absent source
# ---------------------------------------------------------------------------


def test_the_radio_section_reports_an_absent_source_without_the_device_statistics() -> None:
    """The radio section reports an absent source when the tier 2 read failed."""
    sections = _collect(_fake_calls(), extras.SourcePayloads(device_stats=None))
    section = sections[extras.SECTION_RADIOS]
    assert section.reason == extras.REASON_SOURCE_ABSENT
    assert section.records == ()
    assert section.failed is True
    assert sections[extras.SECTION_ALARMS].reason == extras.REASON_READ


def test_the_radio_section_is_empty_when_no_device_holds_a_radio() -> None:
    """A site of switches reports an empty radio section and no failure."""
    section = _collect(_fake_calls(), extras.SourcePayloads(device_stats=[_SWITCH_STAT]))[extras.SECTION_RADIOS]
    assert section.records == ()
    assert section.reason == extras.REASON_READ
    assert section.failed is False


def test_a_port_record_holds_none_for_a_field_the_cloud_left_out() -> None:
    """An absent field arrives as None, so the key set never changes.

    Why:
        A pre-check and a post-check compare field by field. A key that only
        one of the two captures holds would read as a change.
    """
    sections = _collect(_fake_calls())
    assert sections[extras.SECTION_SWITCH_PORTS].records[0]["port_usage"] is None
    assert sections[extras.SECTION_SWITCH_PORTS].records[0]["neighbor_port_desc"] is None
    assert sections[extras.SECTION_POE].records[0]["poe_priority"] is None


def test_an_empty_result_set_reads_as_a_section_with_no_record() -> None:
    """A site with no tunnel reports an empty section and no failure."""
    calls = _fake_calls()
    calls[extras.SECTION_TUNNELS] = _FakeCall(_response([]))
    section = _collect(calls)[extras.SECTION_TUNNELS]
    assert section.records == ()
    assert section.reason == extras.REASON_READ
    assert section.failed is False


# ---------------------------------------------------------------------------
# A failed cloud call
# ---------------------------------------------------------------------------


def test_a_failed_alarm_call_keeps_every_other_section() -> None:
    """One raised call costs its own section and no other section."""
    calls = _fake_calls()
    calls[extras.SECTION_ALARMS] = _FakeCall(error=RuntimeError("The call failed."))
    sections = _collect(calls, extras.SourcePayloads(device_stats=[_AP_STAT]))
    assert sections[extras.SECTION_ALARMS].reason == extras.REASON_CALL_FAILED
    assert sections[extras.SECTION_ALARMS].records == ()
    assert sections[extras.SECTION_ALARMS].http_status == 0
    kept = [name for name in extras.SECTION_NAMES if name != extras.SECTION_ALARMS]
    assert all(sections[name].records for name in kept)
    assert all(sections[name].reason == extras.REASON_READ for name in kept)


def test_a_refused_call_reports_the_http_status() -> None:
    """A status outside the 200 range holds no record and keeps the status."""
    calls = _fake_calls()
    calls[extras.SECTION_BGP_PEERS] = _FakeCall(_response([_BGP_ROW], status_code=503))
    section = _collect(calls)[extras.SECTION_BGP_PEERS]
    assert section.reason == extras.REASON_ERROR_STATUS
    assert section.http_status == 503
    assert section.records == ()


def test_a_failed_port_call_fails_both_port_sections_and_keeps_the_other_four() -> None:
    """The shared port read carries one failure into both port sections.

    Why:
        The two port sections rest on one call. A reader must see that the
        saving also means one shared failure.
    """
    calls = _fake_calls()
    calls[extras.SOURCE_PORTS] = _FakeCall(error=OSError("The port call failed."))
    sections = _collect(calls, extras.SourcePayloads(device_stats=[_AP_STAT]))
    assert sections[extras.SECTION_SWITCH_PORTS].reason == extras.REASON_CALL_FAILED
    assert sections[extras.SECTION_POE].reason == extras.REASON_CALL_FAILED
    assert sections[extras.SECTION_SWITCH_PORTS].records == ()
    kept = (extras.SECTION_RADIOS, extras.SECTION_TUNNELS, extras.SECTION_BGP_PEERS, extras.SECTION_ALARMS)
    assert all(sections[name].reason == extras.REASON_READ for name in kept)


def test_every_section_name_survives_a_failure_of_every_cloud_call() -> None:
    """The result still holds all six names when every cloud call fails."""
    calls = {name: _FakeCall(error=RuntimeError("down")) for name in extras.CLOUD_FETCHERS}
    sections = _collect(calls)
    assert tuple(sections) == extras.SECTION_NAMES
    assert all(sections[name].records == () for name in extras.SECTION_NAMES)


def test_failed_sections_names_only_the_sections_that_failed() -> None:
    """The failure list holds the name, the reason, and the status of each loss."""
    calls = _fake_calls()
    calls[extras.SECTION_ALARMS] = _FakeCall(_response([], status_code=429))
    failures = extras.failed_sections(_collect(calls))
    assert [section.name for section in failures] == [extras.SECTION_RADIOS, extras.SECTION_ALARMS]
    assert failures[0].reason == extras.REASON_SOURCE_ABSENT
    assert failures[1].reason == extras.REASON_ERROR_STATUS
    assert failures[1].http_status == 429


# ---------------------------------------------------------------------------
# The helpers that the assembly step calls
# ---------------------------------------------------------------------------


def test_section_records_returns_one_list_for_each_section() -> None:
    """The flat map holds one list for each of the six section names."""
    records = extras.section_records(_collect(_fake_calls(), extras.SourcePayloads(device_stats=[_AP_STAT])))
    assert tuple(records) == extras.SECTION_NAMES
    assert all(isinstance(rows, list) for rows in records.values())
    assert len(records[extras.SECTION_RADIOS]) == 2


def test_a_section_reports_a_message_for_its_reason() -> None:
    """Each reason carries one plain sentence, so the interface never invents one."""
    calls = _fake_calls()
    calls[extras.SECTION_TUNNELS] = _FakeCall(error=RuntimeError("down"))
    sections = _collect(calls)
    assert sections[extras.SECTION_TUNNELS].message != sections[extras.SECTION_RADIOS].message
    assert sections[extras.SECTION_ALARMS].message == extras._MESSAGES[extras.REASON_READ]


# ---------------------------------------------------------------------------
# The payload reader and the page walk
# ---------------------------------------------------------------------------


def test_the_payload_reader_covers_the_search_shape_and_the_list_shape() -> None:
    """One reader covers the wrapped answer of a search and a bare page list."""
    assert extras._records_of({"results": [_ALARM_ROW]}) == (_ALARM_ROW,)
    assert extras._records_of([_ALARM_ROW]) == (_ALARM_ROW,)
    assert extras._records_of(None) == ()
    assert extras._records_of({"error": "no results key"}) == ()


def test_the_page_walk_keeps_the_first_page_when_the_walk_returns_nothing(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """A silent empty answer from the page walk never drops the first page.

    Why:
        ``mistapi.get_all`` returns an empty list with no error and no log when
        the payload shape surprises it. Without this floor a whole section
        would vanish and nobody would know. The floor writes a warning that
        names the site, because a short section with no warning reads as whole.
    """
    monkeypatch.setattr(extras, "mistapi", SimpleNamespace(get_all=lambda response, mist_session: []))
    with caplog.at_level(logging.WARNING, logger=extras.logger.name):
        walked = extras._paged(object(), _response({"results": [_PORT_ROW]}), _SCOPE)
    assert walked.data == [_PORT_ROW]
    assert walked.status_code == 200
    assert [record for record in caplog.records if record.levelno == logging.WARNING]
    assert _SCOPE.site_id in caplog.text  # The logging rule wants a site identifier on every record.


def test_the_page_walk_keeps_every_row_of_every_page(monkeypatch: pytest.MonkeyPatch) -> None:
    """The page walk replaces the first page when it returns more rows."""
    pages = [_PORT_ROW, dict(_PORT_ROW, port_id="ge-0/0/2")]
    monkeypatch.setattr(extras, "mistapi", SimpleNamespace(get_all=lambda response, mist_session: pages))
    walked = extras._paged(object(), _response({"results": [_PORT_ROW]}), _SCOPE)
    assert walked.data == pages


def test_the_page_walk_keeps_the_first_page_when_the_walk_raises(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """A failed page walk keeps the rows that already arrived.

    Why:
        The log record of the fault must carry the class name alone. A driver
        message can hold a connection string, and a connection string can hold
        a credential, so no log record may repeat one.
    """

    def _raise(response: Any, mist_session: Any) -> list[dict[str, Any]]:
        """Fail the page walk.

        Args:
            response: The first page. The stand-in ignores it.
            mist_session: The session. The stand-in ignores it.

        Returns:
            Nothing. The stand-in always raises.

        Raises:
            RuntimeError: Always, because the walk must fail.
        """
        raise RuntimeError(_FAULT_MESSAGE)

    monkeypatch.setattr(extras, "mistapi", SimpleNamespace(get_all=_raise))
    with caplog.at_level(logging.WARNING, logger=extras.logger.name):
        walked = extras._paged(object(), _response({"results": [_PORT_ROW]}), _SCOPE)
    assert walked.data == [_PORT_ROW]
    assert "RuntimeError" in caplog.text
    assert _FAULT_MESSAGE not in caplog.text
