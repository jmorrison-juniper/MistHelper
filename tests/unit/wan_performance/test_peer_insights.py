"""Verify bounded peer-stat collection against documented scalar fields."""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.interfaces.wan_performance.collection.peer_insights import PeerQualityStats
from src.interfaces.wan_performance.domain.identity import PeerPathIdentity

SOURCE_ROW = {
    "org_id": "org-one",
    "site_id": "site-one",
    "mac": "aabbccddeeff",
    "port_id": "ge-0/0/1",
    "peer_site_id": "site-two",
    "peer_port_id": "ge-0/0/2",
    "peer_mac": "11:22:33:44:55:66",
    "type": "ipsec",
    "latency": 33.3,
    "mos": 4.2,
    "last_seen": 1704112440,
    "up": True,
}
TARGET = PeerPathIdentity.from_stats_row(SOURCE_ROW, "org-one")


def response(rows: list[object], **metadata: object) -> SimpleNamespace:
    """Build one decoded statistics page with optional pagination metadata."""
    return SimpleNamespace(status_code=200, data={"results": rows, **metadata})


def next_page(cursor: str) -> str:
    """Return a server continuation with one opaque search-after cursor."""
    return f"https://api.mist.com/api/v1/orgs/org-one/stats/peers?search_after={cursor}"


def test_collect_uses_only_supported_peer_filters_and_retains_raw_fields() -> None:
    """Search supported gateway filters and store only peer-schema scalar fields."""
    session, admission = MagicMock(), MagicMock()
    row = deepcopy(SOURCE_ROW)
    row.update(loss=0.25, jitter=4.5, rx_bytes=1000)
    with patch(
        "src.interfaces.wan_performance.collection.peer_insights.searchOrgPeerPathStats",
        return_value=response([row], total=1),
    ) as search:
        samples = PeerQualityStats(session, admission).collect(TARGET)

    search.assert_called_once_with(
        session,
        "org-one",
        mac="aabbccddeeff",
        site_id="site-one",
        duration="1h",
        limit=100,
        search_after=None,
    )
    admission.check.assert_called_once_with()
    assert len(samples) == 1
    assert samples[0].identity == TARGET
    assert samples[0].timestamp_source == "poll"
    assert samples[0].raw_fields == {
        "loss": 0.25,
        "latency": 33.3,
        "jitter": 4.5,
        "mos": 4.2,
        "last_seen": 1704112440,
    }
    assert samples[0].metrics["loss"].unit == "%"
    assert samples[0].metrics["loss"].value == 0.25
    assert samples[0].metrics["latency"].unit == "ms"
    assert samples[0].metrics["latency"].value == 33.3
    assert samples[0].metrics["jitter"].unit == "ms"
    assert samples[0].metrics["jitter"].value == 4.5
    assert samples[0].metrics["mos"].unit == "unknown"
    assert samples[0].metrics["mos"].missing_reason == ("The VPN peer stats schema does not define this field's unit.")


def test_collect_filters_multiple_paths_by_complete_identity() -> None:
    """Select the requested local and remote path when one gateway has multiple peers."""
    other_path = deepcopy(SOURCE_ROW)
    other_path["peer_port_id"] = "ge-0/0/3"
    other_path["peer_mac"] = "22:33:44:55:66:77"
    target_path = deepcopy(SOURCE_ROW)
    target_path["latency"] = 0
    with patch(
        "src.interfaces.wan_performance.collection.peer_insights.searchOrgPeerPathStats",
        return_value=response([other_path, target_path], total=2),
    ):
        samples = PeerQualityStats(MagicMock(), MagicMock()).collect(TARGET)

    assert len(samples) == 1
    assert samples[0].identity == TARGET
    assert samples[0].raw_fields["latency"] == 0


def test_collect_pages_before_filtering_and_preserves_partial_state() -> None:
    """Follow a bounded cursor and retain the target found on the final allowed page."""
    pages = [
        response([], total=10, next=next_page("cursor-1")),
        response([], total=10, next=next_page("cursor-2")),
        response([], total=10, next=next_page("cursor-3")),
        response([], total=10, next=next_page("cursor-4")),
        response([deepcopy(SOURCE_ROW)], total=10, next=next_page("cursor-5")),
    ]
    session, admission = MagicMock(), MagicMock()
    with patch(
        "src.interfaces.wan_performance.collection.peer_insights.searchOrgPeerPathStats",
        side_effect=pages,
    ) as search:
        samples = PeerQualityStats(session, admission).collect(TARGET)

    assert len(samples) == 1
    assert samples[0].partial is True
    assert [call.kwargs["search_after"] for call in search.call_args_list] == [
        None,
        "cursor-1",
        "cursor-2",
        "cursor-3",
        "cursor-4",
    ]
    assert admission.check.call_count == 5


def test_collect_rejects_duplicate_full_identity_without_source_timestamp() -> None:
    """Refuse ambiguous rows when the source schema has no sample timestamp."""
    row = deepcopy(SOURCE_ROW)
    with patch(
        "src.interfaces.wan_performance.collection.peer_insights.searchOrgPeerPathStats",
        return_value=response([row, deepcopy(row)], total=2),
    ):
        with pytest.raises(ValueError, match="duplicate full identities"):
            PeerQualityStats(MagicMock(), MagicMock()).collect(TARGET)


def test_collect_rejects_missing_target_path() -> None:
    """Do not report an empty peer query as a successful selected-path refresh."""
    with patch(
        "src.interfaces.wan_performance.collection.peer_insights.searchOrgPeerPathStats",
        return_value=response([], total=0),
    ):
        with pytest.raises(LookupError, match="selected full path identity"):
            PeerQualityStats(MagicMock(), MagicMock()).collect(TARGET)


@pytest.mark.parametrize("status", [400, 401, 403, 429, 500, 503])
def test_collect_surfaces_http_failures(status: int) -> None:
    """Stop when a peer-stat page returns an HTTP failure."""
    with patch(
        "src.interfaces.wan_performance.collection.peer_insights.searchOrgPeerPathStats",
        return_value=SimpleNamespace(status_code=status, data={}),
    ):
        with pytest.raises(ConnectionError, match=f"HTTP {status}"):
            PeerQualityStats(MagicMock(), MagicMock()).collect(TARGET)


def test_collect_rejects_malformed_rows_and_repeated_cursors() -> None:
    """Reject malformed result shapes and pagination loops."""
    with patch(
        "src.interfaces.wan_performance.collection.peer_insights.searchOrgPeerPathStats",
        return_value=response([None]),
    ):
        with pytest.raises(ValueError, match="bounded object page"):
            PeerQualityStats(MagicMock(), MagicMock()).collect(TARGET)

    loop = response([], total=2, next=next_page("same"))
    with patch(
        "src.interfaces.wan_performance.collection.peer_insights.searchOrgPeerPathStats",
        return_value=loop,
    ):
        with pytest.raises(ValueError, match="repeated a search-after cursor"):
            PeerQualityStats(MagicMock(), MagicMock()).collect(TARGET)


def test_collect_stops_before_api_call_when_admission_fails() -> None:
    """Require the shared request owner before every peer-stat page."""
    admission = MagicMock()
    admission.check.side_effect = ConnectionError("admission denied")
    with patch("src.interfaces.wan_performance.collection.peer_insights.searchOrgPeerPathStats") as search:
        with pytest.raises(ConnectionError, match="admission denied"):
            PeerQualityStats(MagicMock(), admission).collect(TARGET)
    search.assert_not_called()
