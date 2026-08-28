"""The client present count reports every client of a skipped section.

Why:
    The comparison proves an upgrade returned every client. A matching client
    digest proves the section equal, so the comparison reads no row. The
    present count must then report the whole section, because a bare zero there
    reads as a site that lost every client. Issue #2109 records that defect.

    A measured zero must still read as zero. A fix that fills every zero would
    hide a real empty client section, which is the opposite fault. FR-113,
    FR-114, FR-116, and FR-117 pin these rules, and these tests hold them.

No network:
    Every test feeds plain dictionaries. No test opens a socket, reads the
    ``.env`` file, or names a real credential.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

from typing import Any  # A capture document maps a key to a free-form value.

from src.upgrade_portal.compare import clients as client_compare  # The client half under test.
from src.upgrade_portal.compare import statistics  # The roll-up that the operator reads.

# --------------------------------------------------------------------------
# The fixed values. Each one repeats a rule of the specification.
# --------------------------------------------------------------------------

MAC_PREFIX = "00112200"  # Obviously fake addresses, so no test reaches a real site.

# WHY: A distinct address block for each kind, so no client falls in two
#      sections and no test can double count one client by accident.
KIND_OFFSET = {
    client_compare.KIND_WIRED: 0x0000,  # The wired block starts at zero.
    client_compare.KIND_WIRELESS: 0x1000,  # The wireless block starts well above wired.
    client_compare.KIND_GUEST: 0x2000,  # The guest block starts well above wireless.
}

WIRED_COUNT = 3  # The wired section of the live report.
WIRELESS_COUNT = 4  # The wireless section of the live report.
GUEST_COUNT = 2  # The guest section of the live report.
SITE_CLIENT_COUNT = WIRED_COUNT + WIRELESS_COUNT + GUEST_COUNT  # The whole client count.

FULL_SIZES = {
    client_compare.KIND_WIRED: WIRED_COUNT,  # Every wired client of the site.
    client_compare.KIND_WIRELESS: WIRELESS_COUNT,  # Every wireless client of the site.
    client_compare.KIND_GUEST: GUEST_COUNT,  # Every guest client of the site.
}

EMPTY_SIZES = {kind: 0 for kind in client_compare.CLIENT_KINDS}  # A site with no client at all.

MATCHING_DIGEST = "b1946ac92492d2347c6235b4d2611184"  # A shared digest lets a section skip.
OTHER_DIGEST = "591785b794601e212b260e25925636fd"  # A different digest forces a section compare.

RETURN_RATE_WHOLE = 1.0  # Every client returned, so the rate reads one.


def _client_rows(kind: str, total: int) -> list[dict[str, Any]]:
    """Return one client list that holds ``total`` rows of one kind.

    Args:
        kind: ``wired``, ``wireless``, or ``guest``.
        total: How many client rows to build.

    Returns:
        One list of flat client rows, each with a distinct address.
    """
    base = KIND_OFFSET[kind]  # The block keeps each kind on its own addresses.
    return [
        {
            "mac": f"{MAC_PREFIX}{base + index:04x}",  # A distinct address for each client.
            "hostname": f"{kind}-host-{index:02d}",  # A readable name proves the row is whole.
            "device_mac": "aabbccddeeff",  # One serving device keeps every client present.
        }
        for index in range(total)  # One row for each client of the kind.
    ]


def _capture(sizes: dict[str, int], digests: dict[str, str] | None = None) -> dict[str, Any]:
    """Return one capture document around the three client sections.

    Args:
        sizes: How many rows each kind holds.
        digests: The digest of each kind, or None for a matching digest on all.

    Returns:
        One capture document with a client map and a digest map.
    """
    clients = {kind: _client_rows(kind, sizes.get(kind, 0)) for kind in client_compare.CLIENT_KINDS}  # The three lists.
    chosen = digests or {kind: MATCHING_DIGEST for kind in client_compare.CLIENT_KINDS}  # A matching digest by default.
    section_digests = {
        client_compare.SECTION_FOR_KIND[kind]: chosen[kind] for kind in client_compare.CLIENT_KINDS
    }  # Map each kind digest onto its section name, so the reader finds it.
    return {"clients": clients, "digests": section_digests}  # The two keys the comparison reads.


def _present(before: dict[str, Any], after: dict[str, Any]) -> int:
    """Return the present count of one comparison of two captures.

    Args:
        before: The pre-check capture.
        after: The post-check capture.

    Returns:
        The corrected present count that the operator reads.
    """
    clients = client_compare.compare_clients(before, after)  # The client half of the comparison.
    return statistics.count_clients(clients).present  # The present count the page shows.


# ---------------------------------------------------------------------------
# The true count after a digest skip
# ---------------------------------------------------------------------------


def test_two_identical_captures_prove_every_client_present() -> None:
    """A matching digest on every section reports every client present."""
    before = _capture(FULL_SIZES)  # The pre-check capture holds the whole site.
    after = _capture(FULL_SIZES)  # The post-check capture holds the same site.

    present = _present(before, after)  # The three digests match, so the comparison skips every row.

    assert present == SITE_CLIENT_COUNT  # The present count equals the whole client count.


def test_a_skipped_client_section_carries_the_present_count() -> None:
    """The client comparison reports the count the three digests proved."""
    result = client_compare.compare_clients(_capture(FULL_SIZES), _capture(FULL_SIZES))  # Two equal captures.

    assert result.proved_present == SITE_CLIENT_COUNT  # The comparison carries the whole proved count.


def test_the_present_count_reads_the_larger_client_index() -> None:
    """A digest match proves the two sections equal, so the larger size wins."""
    before = _capture(FULL_SIZES)  # The pre-check capture holds every client.
    after = _capture(EMPTY_SIZES)  # The post-check capture lost its rows but keeps the matching digest.

    result = client_compare.compare_clients(before, after)  # The digests still match, so the section skips.

    assert result.proved_present == SITE_CLIENT_COUNT  # The larger of the two sizes proves the count.


def test_the_return_rate_reads_the_corrected_present_count() -> None:
    """Every client returned, so the corrected present count makes the rate one."""
    comparison = client_compare.compare_clients(_capture(FULL_SIZES), _capture(FULL_SIZES))  # Two equal captures.

    counts = statistics.count_clients(comparison)  # The roll-up adds the proved count to present.

    assert counts.return_rate == RETURN_RATE_WHOLE  # The rate reads the corrected present count.


# ---------------------------------------------------------------------------
# The double count guard
# ---------------------------------------------------------------------------


def test_a_compared_section_never_adds_a_proved_present_count() -> None:
    """A section the comparison read carries no proved count, so none doubles."""
    before = _capture(FULL_SIZES)  # The pre-check capture holds every client.
    after = _capture(FULL_SIZES, {kind: OTHER_DIGEST for kind in client_compare.CLIENT_KINDS})  # Every digest differs.

    result = client_compare.compare_clients(before, after)  # No digest matches, so the comparison reads every row.

    assert result.proved_present == 0  # A read section adds no proved count.
    assert statistics.count_clients(result).present == SITE_CLIENT_COUNT  # The read rows count once, not twice.


def test_a_mix_counts_the_skip_and_the_read_rows_once() -> None:
    """One skipped section adds its size, and the read sections add their rows."""
    before = _capture(FULL_SIZES)  # The pre-check capture holds every client.
    after = _capture(
        FULL_SIZES,
        {
            client_compare.KIND_WIRED: MATCHING_DIGEST,  # The wired digest matches, so wired skips.
            client_compare.KIND_WIRELESS: OTHER_DIGEST,  # The wireless digest differs, so wireless reads.
            client_compare.KIND_GUEST: OTHER_DIGEST,  # The guest digest differs, so guest reads.
        },
    )  # The post-check capture skips wired alone.

    result = client_compare.compare_clients(before, after)  # One section skips, and two sections read.

    assert result.proved_present == WIRED_COUNT  # Only the skipped wired section proves a count.
    assert statistics.count_clients(result).present == SITE_CLIENT_COUNT  # Each client counts exactly once.


# ---------------------------------------------------------------------------
# The measured zero
# ---------------------------------------------------------------------------


def test_a_measured_empty_client_section_still_reports_zero() -> None:
    """A site with no client reports zero, because the zero is measured."""
    present = _present(_capture(EMPTY_SIZES), _capture(EMPTY_SIZES))  # Both captures hold no client.

    assert present == 0  # A measured empty site still reads zero.


def test_the_client_result_dict_still_names_two_keys_only() -> None:
    """The proved count travels in the statistics, not in the client dict."""
    result = client_compare.compare_clients(_capture(FULL_SIZES), _capture(FULL_SIZES))  # Two equal captures.

    assert set(result.to_dict()) == {"client_deltas", "skipped_sections"}  # The dict names the two contract keys only.
