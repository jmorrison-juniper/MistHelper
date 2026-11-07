"""Verify bounded peer insight request and timestamp behavior."""

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from src.interfaces.wan_performance.collection.peer_insights import PeerQualityInsights
from src.interfaces.wan_performance.domain.identity import GatewayIdentity, PeerPathIdentity, SiteIdentity


class FakeAdmission:
    """Count or refuse peer insight requests."""

    def __init__(self, fail: bool = False) -> None:
        """Set the deterministic admission result."""
        self.fail = fail  # Preserve the chosen test outcome.
        self.checks = 0  # Count checks before the SDK call.

    def check(self) -> None:
        """Refuse transport when the refresh owner is unavailable."""
        self.checks += 1  # Record the request attempt.
        if self.fail:  # Model an expired lease.
            raise ConnectionError("lease expired")  # Stop before transport.


class FakeSession:
    """Return one controlled peer insight response."""

    def __init__(self, status: int = 200, rows: list[dict[str, object]] | None = None) -> None:
        """Keep response data and observed request parameters."""
        self.status = status  # Set the mocked HTTP status.
        self.rows = rows  # Keep optional test rows.
        self.calls: list[tuple[str, dict[str, str] | None]] = []  # Capture SDK arguments.

    def mist_get(self, uri: str, query: dict[str, str] | None = None) -> object:
        """Build a bounded response from the exact request window."""
        self.calls.append((uri, query))  # Record the authenticated SDK call.
        data = {
            "start": int(query["start"]),
            "end": int(query["end"]),
            "interval": 3600,
            "next": False,
            "results": self.rows or [],
        }  # Mirror request bounds.
        return SimpleNamespace(status_code=self.status, data=data)  # Return one mocked response.


class TestPeerInsights:
    """Test peer API behavior without production credentials."""

    @staticmethod
    def target() -> PeerPathIdentity:
        """Return one complete local and remote path identity."""
        gateway = GatewayIdentity(SiteIdentity("org-one", "site-one"), "gw-one")  # Select the gateway.
        return PeerPathIdentity(gateway, "ge-0/0/0", "ge-0/0/1", "11:22:33:44:55:66", "tunnel-one")  # Select peer.

    def test_collect_sends_bounded_peer_filter(self) -> None:
        """Use the selected source path and a two-row response cap."""
        session = FakeSession()  # Return a valid empty response.
        admission = FakeAdmission()  # Allow the request.
        records = PeerQualityInsights(session, admission).collect(self.target())  # Collect one hour.
        uri, query = session.calls[0]  # Read the exact request.
        assert uri.endswith("/gw-one/vpn_peer-metrics")  # Keep the gateway scope.
        assert query["limit"] == "2"  # Keep the response bounded.
        assert query["peer_port_id"] == "ge-0/0/1"  # Preserve remote port scope.
        assert records == ()  # Keep empty data distinct from failure.
        assert admission.checks == 1  # Admit the outgoing request.

    @pytest.mark.parametrize("status", [400, 429, 500])  # Cover client, quota, and server errors.
    def test_http_errors_are_rejected(self, status: int) -> None:
        """Do not convert HTTP errors into empty peer data."""
        session = FakeSession(status=status)  # Return a failed response.
        with pytest.raises(ConnectionError, match=str(status)):  # Require explicit failure.
            PeerQualityInsights(session, FakeAdmission()).collect(self.target())  # Refuse the response.

    def test_peer_metrics_keep_missing_values_unknown(self) -> None:
        """Keep absent peer metrics unknown with explicit reasons."""
        start = int(datetime.now(UTC).replace(minute=0, second=0, microsecond=0).timestamp()) - 3600  # Use prior hour.
        session = FakeSession(rows=[{"timestamp": start + 10}])  # Return one timestamp with no metrics.
        records = PeerQualityInsights(session, FakeAdmission()).collect(self.target())  # Normalize one row.
        assert len(records) == 1  # Preserve the source row.
        assert records[0].metrics["loss"].value is None  # Do not infer zero loss.
        assert records[0].metrics["loss"].missing_reason == "The API snapshot has no value."  # Explain missing data.

    def test_out_of_window_timestamp_is_rejected(self) -> None:
        """Reject peer rows outside the requested hour."""
        session = FakeSession(rows=[{"timestamp": 1}])  # Return a stale timestamp.
        with pytest.raises(ValueError, match="outside"):  # Require time-window validation.
            PeerQualityInsights(session, FakeAdmission()).collect(self.target())  # Refuse stale data.

    def test_admission_failure_prevents_sdk_call(self) -> None:
        """Stop before the SDK call when refresh ownership expires."""
        session = FakeSession()  # Keep a visible call list.
        with pytest.raises(ConnectionError, match="lease"):  # Require fail-closed behavior.
            PeerQualityInsights(session, FakeAdmission(fail=True)).collect(self.target())  # Refuse transport.
        assert not session.calls  # Prove no API request started.
