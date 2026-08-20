"""Unit tests for the client comparison of two upgrade captures.

Why:
    Two faults in this module would each raise a false alarm on every busy
    site, and neither raises an error. A comparison that counts a roam as a
    loss reports a healthy upgrade as a failure. A comparison that matches on
    a composite registry key sees a new timestamp in every capture and reports
    the whole client list as new.

    The registry joins the endpoint, the address, and a timestamp with a colon
    (``src/db/redis_writer.py:627``), so the tests below drive that exact key
    form. Every test feeds plain dictionaries. No test opens a socket, reads
    the ``.env`` file, or names a real credential.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.upgrade_portal.compare import clients

# WHY: Obviously fake addresses. A reader sees at once that no test reaches a
#      real site.
CLIENT_MAC = "aabbccddeeff"
OTHER_CLIENT_MAC = "aabbccddee00"
ACCESS_POINT_ONE = "0011220000aa"
ACCESS_POINT_TWO = "0011220000bb"

# WHY: The registry key form of ``_build_key``. The timestamp differs in every
#      capture, which is the whole reason for the stripping rule.
BEFORE_KEY = f"searchclient:{CLIENT_MAC}:1723200000"
AFTER_KEY = f"searchclient:{CLIENT_MAC}:1723203600"

DIGEST_ONE = "b1946ac92492d2347c6235b4d2611184"
DIGEST_TWO = "591785b794601e212b260e25925636fd"


def _client_row(**overrides: Any) -> dict[str, Any]:
    """Return one client row with the fields a comparison reads.

    Why:
        Each test changes one field of a whole row. Building the row here keeps
        the difference under test on the single line that names it.

    Args:
        **overrides: The fields to replace.

    Returns:
        One client row.
    """
    row: dict[str, Any] = {
        "mac": CLIENT_MAC,
        "hostname": "laptop-01",
        "device_mac": ACCESS_POINT_ONE,
        "device_name": "ap-lobby",
        "timestamp": 1723200000,
    }
    row.update(overrides)
    return row


def _capture(rows: Any, kind: str = clients.KIND_WIRELESS, digests: dict[str, str] | None = None) -> dict[str, Any]:
    """Return one capture document around a client section.

    Why:
        The comparison reads two keys of a large document. A small builder
        keeps every test to the two keys that matter.

    Args:
        rows: The client section, as a list or as a registry map.
        kind: The client kind that holds the rows.
        digests: The digest map, when the test needs one.

    Returns:
        One capture document.
    """
    capture: dict[str, Any] = {"clients": {kind: rows}}
    if digests is not None:
        capture["digests"] = digests
    return capture


# ---------------------------------------------------------------------------
# The match key
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        (CLIENT_MAC, CLIENT_MAC),
        ("AA:BB:CC:DD:EE:FF", CLIENT_MAC),
        ("aa-bb-cc-dd-ee-ff", CLIENT_MAC),
        (BEFORE_KEY, CLIENT_MAC),
        (AFTER_KEY, CLIENT_MAC),
        ("searchclient:AA:BB:CC:DD:EE:FF:1723200000", CLIENT_MAC),
        (f"{CLIENT_MAC}1723200000", CLIENT_MAC),
        ("", ""),
        ("no address here", ""),
        (None, ""),
        (12345, ""),
    ],
)
def test_the_key_reader_returns_the_address_alone(key: Any, expected: str) -> None:
    """The key reader drops the endpoint and the timestamp and keeps the address.

    Args:
        key: The raw registry key.
        expected: The address the reader must return.
    """
    assert clients.strip_timestamp_key(key) == expected


def test_two_keys_with_different_timestamps_match_one_client() -> None:
    """A new timestamp in the key never makes a second client."""
    before = _capture({BEFORE_KEY: _client_row()})
    after = _capture({AFTER_KEY: _client_row(timestamp=1723203600)})

    result = clients.compare_clients(before, after)

    assert len(result.deltas) == 1
    assert result.deltas[0].mac == CLIENT_MAC
    assert result.deltas[0].outcome == clients.OUTCOME_PRESENT


def test_the_match_reads_the_address_of_the_row_first() -> None:
    """A row with its own address wins over a key that holds another one."""
    before = _capture({"searchclient:000000000000:1": _client_row(mac=CLIENT_MAC)})
    after = _capture([_client_row()])

    result = clients.compare_clients(before, after)

    assert [delta.mac for delta in result.deltas] == [CLIENT_MAC]


def test_a_row_without_an_address_never_reaches_the_report() -> None:
    """A row with no usable address is dropped rather than matched."""
    before = _capture([_client_row(mac=""), _client_row()])
    after = _capture([_client_row()])

    result = clients.compare_clients(before, after)

    assert [delta.mac for delta in result.deltas] == [CLIENT_MAC]


# ---------------------------------------------------------------------------
# The four outcomes
# ---------------------------------------------------------------------------


def test_the_outcome_names_match_the_data_model() -> None:
    """The four client outcomes carry the names of the data model."""
    assert clients.CLIENT_OUTCOMES == ("present", "moved", "added", "missing")


def test_the_same_serving_device_reports_present() -> None:
    """A client on the same access point in both captures is ``present``."""
    before = _capture([_client_row(device_mac=ACCESS_POINT_ONE)])
    after = _capture([_client_row(device_mac=ACCESS_POINT_ONE)])

    assert clients.compare_clients(before, after).deltas[0].outcome == clients.OUTCOME_PRESENT


def test_a_new_serving_device_reports_moved() -> None:
    """A client that roamed to another access point is ``moved``."""
    before = _capture([_client_row(device_mac=ACCESS_POINT_ONE, device_name="ap-lobby")])
    after = _capture([_client_row(device_mac=ACCESS_POINT_TWO, device_name="ap-stair")])

    delta = clients.compare_clients(before, after).deltas[0]

    assert delta.outcome == clients.OUTCOME_MOVED
    assert delta.move.before_device == ACCESS_POINT_ONE
    assert delta.move.after_device == ACCESS_POINT_TWO
    assert delta.move.before_name == "ap-lobby"
    assert delta.move.after_name == "ap-stair"


def test_a_move_is_never_a_loss() -> None:
    """The loss list never holds ``moved``."""
    assert clients.OUTCOME_MOVED not in clients.LOSS_OUTCOMES
    assert clients.LOSS_OUTCOMES == (clients.OUTCOME_MISSING,)


def test_a_client_of_the_post_check_capture_alone_is_added() -> None:
    """A client that only the post-check capture holds is ``added``."""
    result = clients.compare_clients(_capture([]), _capture([_client_row()]))

    delta = result.deltas[0]

    assert delta.outcome == clients.OUTCOME_ADDED
    assert delta.move.after_device == ACCESS_POINT_ONE
    assert delta.move.before_device == ""


def test_a_client_of_the_pre_check_capture_alone_is_missing() -> None:
    """A client that only the pre-check capture holds is ``missing``."""
    result = clients.compare_clients(_capture([_client_row()]), _capture([]))

    delta = result.deltas[0]

    assert delta.outcome == clients.OUTCOME_MISSING
    assert delta.move.before_device == ACCESS_POINT_ONE
    assert delta.move.after_device == ""


def test_a_serving_device_with_separators_still_matches() -> None:
    """The same access point in two spellings never reads as a move."""
    before = _capture([_client_row(device_mac="00:11:22:00:00:AA")])
    after = _capture([_client_row(device_mac=ACCESS_POINT_ONE)])

    assert clients.compare_clients(before, after).deltas[0].outcome == clients.OUTCOME_PRESENT


def test_an_absent_serving_device_never_reads_as_a_move() -> None:
    """An unknown access point on one side leaves the client ``present``."""
    before = _capture([_client_row(device_mac="")])
    after = _capture([_client_row(device_mac=ACCESS_POINT_TWO)])

    assert clients.compare_clients(before, after).deltas[0].outcome == clients.OUTCOME_PRESENT


def test_a_new_signal_reading_never_reads_as_a_move() -> None:
    """A field outside the serving device never changes the outcome."""
    before = _capture([_client_row(rssi=-50, uptime=10)])
    after = _capture([_client_row(rssi=-72, uptime=900)])

    assert clients.compare_clients(before, after).deltas[0].outcome == clients.OUTCOME_PRESENT


# ---------------------------------------------------------------------------
# The section readers
# ---------------------------------------------------------------------------


def test_the_comparison_reads_all_three_client_kinds() -> None:
    """A wired client, a wireless client, and a guest client all report."""
    before: dict[str, Any] = {
        "clients": {
            clients.KIND_WIRED: [_client_row(mac="000000000001")],
            clients.KIND_WIRELESS: [_client_row(mac="000000000002")],
            clients.KIND_GUEST: [_client_row(mac="000000000003")],
        }
    }

    result = clients.compare_clients(before, before)

    assert [delta.kind for delta in result.deltas] == ["wired", "wireless", "guest"]


def test_the_comparison_sorts_the_clients_by_address() -> None:
    """The client rows arrive in address order."""
    before = _capture([_client_row(mac=OTHER_CLIENT_MAC), _client_row(mac=CLIENT_MAC)])
    after = _capture([])

    result = clients.compare_clients(before, after)

    assert [delta.mac for delta in result.deltas] == [OTHER_CLIENT_MAC, CLIENT_MAC]


def test_a_capture_without_a_client_map_reports_no_client() -> None:
    """A capture with no client map reports no client and raises nothing."""
    assert clients.compare_clients({}, {}).deltas == ()


def test_a_row_of_the_wrong_type_never_stops_the_comparison() -> None:
    """A partial capture with a broken row still reports the good rows."""
    before = _capture(["not a row", _client_row()])
    after = _capture([_client_row()])

    assert [delta.mac for delta in clients.compare_clients(before, after).deltas] == [CLIENT_MAC]


# ---------------------------------------------------------------------------
# The digest short circuit
# ---------------------------------------------------------------------------


def test_a_matching_digest_skips_one_client_section() -> None:
    """A wireless section with the same digest compares no wireless client."""
    digests = {clients.SECTION_CLIENTS_WIRELESS: DIGEST_ONE}
    before = _capture([_client_row(device_mac=ACCESS_POINT_ONE)], digests=digests)
    after = _capture([_client_row(device_mac=ACCESS_POINT_TWO)], digests=digests)

    result = clients.compare_clients(before, after)

    assert result.deltas == ()
    assert result.skipped_sections == (clients.SECTION_CLIENTS_WIRELESS,)


def test_a_skipped_section_never_hides_another_section() -> None:
    """A matching wired digest still compares the wireless clients."""
    digests = {clients.SECTION_CLIENTS_WIRED: DIGEST_ONE}
    before: dict[str, Any] = {
        "digests": digests,
        "clients": {
            clients.KIND_WIRED: [_client_row(mac="000000000001")],
            clients.KIND_WIRELESS: [_client_row(mac=CLIENT_MAC, device_mac=ACCESS_POINT_ONE)],
        },
    }
    after: dict[str, Any] = {
        "digests": digests,
        "clients": {
            clients.KIND_WIRED: [_client_row(mac="000000000001")],
            clients.KIND_WIRELESS: [_client_row(mac=CLIENT_MAC, device_mac=ACCESS_POINT_TWO)],
        },
    }

    result = clients.compare_clients(before, after)

    assert [delta.mac for delta in result.deltas] == [CLIENT_MAC]
    assert result.deltas[0].outcome == clients.OUTCOME_MOVED
    assert result.skipped_sections == (clients.SECTION_CLIENTS_WIRED,)


def test_a_differing_digest_compares_the_section() -> None:
    """Two different wireless digests compare every wireless client."""
    before = _capture([_client_row()], digests={clients.SECTION_CLIENTS_WIRELESS: DIGEST_ONE})
    after = _capture([_client_row()], digests={clients.SECTION_CLIENTS_WIRELESS: DIGEST_TWO})

    result = clients.compare_clients(before, after)

    assert result.skipped_sections == ()
    assert len(result.deltas) == 1


# ---------------------------------------------------------------------------
# The counters and the dictionary form
# ---------------------------------------------------------------------------


def test_the_counter_reads_the_outcome_of_each_record() -> None:
    """The counter reports one number for each outcome."""
    deltas = (
        clients.ClientDelta(mac=CLIENT_MAC, outcome=clients.OUTCOME_MOVED),
        clients.ClientDelta(mac=OTHER_CLIENT_MAC, outcome=clients.OUTCOME_MOVED),
        clients.ClientDelta(mac="000000000001", outcome=clients.OUTCOME_MISSING),
    )

    assert clients.count_outcome(deltas, clients.OUTCOME_MOVED) == 2
    assert clients.count_outcome(deltas, clients.OUTCOME_MISSING) == 1
    assert clients.count_outcome(deltas, clients.OUTCOME_PRESENT) == 0


def test_the_client_result_carries_the_two_contract_keys() -> None:
    """The dictionary form names ``client_deltas`` and ``skipped_sections``."""
    result = clients.ClientComparison(
        deltas=(clients.ClientDelta(mac=CLIENT_MAC, outcome=clients.OUTCOME_MISSING, hostname="laptop-01"),),
        skipped_sections=(clients.SECTION_CLIENTS_GUEST,),
    )

    body = result.to_dict()

    assert set(body) == {"client_deltas", "skipped_sections"}
    assert body["skipped_sections"] == ["clients_guest"]
    assert body["client_deltas"][0]["mac"] == CLIENT_MAC
    assert body["client_deltas"][0]["outcome"] == "missing"


def test_the_client_row_flattens_the_two_serving_devices() -> None:
    """A table column reads a flat serving device value."""
    move = clients.ClientMove(
        before_device=ACCESS_POINT_ONE,
        after_device=ACCESS_POINT_TWO,
        before_name="ap-lobby",
        after_name="ap-stair",
    )
    delta = clients.ClientDelta(mac=CLIENT_MAC, outcome=clients.OUTCOME_MOVED, move=move)

    row = delta.to_dict()

    assert row["before_device"] == ACCESS_POINT_ONE
    assert row["after_device"] == ACCESS_POINT_TWO
    assert row["before_device_name"] == "ap-lobby"
    assert row["after_device_name"] == "ap-stair"
