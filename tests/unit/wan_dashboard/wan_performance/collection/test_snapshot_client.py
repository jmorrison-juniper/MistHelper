"""Verify bounded WAN snapshot requests and tenant scope."""

from types import SimpleNamespace

import pytest

from src.interfaces.wan_performance.collection import snapshot_client
from src.interfaces.wan_performance.collection.snapshot_client import SnapshotClient, SnapshotPageValidator


class FakeAdmission:
    """Count or refuse request admission."""

    def __init__(self, fail: bool = False) -> None:
        """Set the deterministic admission result."""
        self.fail = fail  # Keep the test outcome explicit.
        self.checks = 0  # Count checks before transport.

    def check(self) -> None:
        """Count each check and optionally refuse the request."""
        self.checks += 1  # Record the attempted admission.
        if self.fail:  # Model a lost refresh lease.
            raise ConnectionError("lease expired")  # Stop before transport.


class TestSnapshotClient:
    """Test one-page collection without live Mist access."""

    def test_collection_uses_two_bounded_sdk_calls(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Use one page per source and keep the result marked live."""
        calls: list[tuple[str, dict[str, object]]] = []  # Record exact SDK arguments.

        def ports(session: object, org_id: str, *, device_type: str, mac: str | None, limit: int) -> object:
            calls.append(
                (
                    "ports",
                    {"session": session, "org_id": org_id, "device_type": device_type, "mac": mac, "limit": limit},
                )
            )  # Record port request.
            return SimpleNamespace(
                status_code=200,
                data={"results": [{"org_id": org_id, "site_id": "site-one", "mac": "gw-one"}], "total": 1},
            )  # Return one row.

        def peers(
            session: object, org_id: str, *, mac: str | None, site_id: str | None, duration: str, limit: int
        ) -> object:
            calls.append(
                (
                    "peers",
                    {
                        "session": session,
                        "org_id": org_id,
                        "mac": mac,
                        "site_id": site_id,
                        "duration": duration,
                        "limit": limit,
                    },
                )
            )  # Record peer request.
            return SimpleNamespace(status_code=200, data={"results": [], "total": 0})  # Return no peer rows.

        monkeypatch.setattr(snapshot_client, "searchOrgSwOrGwPorts", ports)  # Replace the Mist transport.
        monkeypatch.setattr(snapshot_client, "searchOrgPeerPathStats", peers)  # Replace the Mist transport.
        admission = FakeAdmission()  # Use an open refresh lease.
        result = SnapshotClient(object(), admission).collect("org-one")  # Collect without live credentials.
        assert len(calls) == 2  # Bound collection to two source pages.
        assert calls[0][1]["limit"] == 100  # Keep the port page bounded.
        assert calls[1][1]["limit"] == 100  # Keep the peer page bounded.
        assert admission.checks == 2  # Admit each outgoing request.
        assert result["partial"] is False  # Preserve complete source counts.
        assert result["provenance"] == "live"  # Mark the actual source type.

    @pytest.mark.parametrize("status", [400, 429, 500])  # Cover client, quota, and server failures.
    def test_http_errors_do_not_become_empty_success(self, status: int, monkeypatch: pytest.MonkeyPatch) -> None:
        """Report HTTP failures instead of returning empty rows."""
        monkeypatch.setattr(
            snapshot_client,
            "searchOrgSwOrGwPorts",
            lambda *args, **kwargs: SimpleNamespace(status_code=status, data={}),
        )  # Mock the SDK response.
        client = SnapshotClient(object(), FakeAdmission())  # Use an admitted request.
        with pytest.raises(ConnectionError, match=str(status)):  # Require explicit failure.
            client._ports("org-one", None)  # Refuse the failed response.

    def test_full_page_without_count_is_partial(self) -> None:
        """Mark a full page as incomplete when the source gives no count."""
        response = SimpleNamespace(
            status_code=200, data={"results": [{"id": number} for number in range(100)]}
        )  # Model a full page.
        rows, partial = SnapshotPageValidator.parse(response)  # Validate the page.
        assert len(rows) == 100  # Preserve the bounded page.
        assert partial is True  # Require completeness evidence.

    def test_wrong_tenant_row_is_rejected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Reject a row that escapes the requested organization."""
        bad = SimpleNamespace(
            status_code=200, data={"results": [{"org_id": "other-org"}], "total": 1}
        )  # Model tenant leak.
        monkeypatch.setattr(
            snapshot_client, "searchOrgSwOrGwPorts", lambda *args, **kwargs: bad
        )  # Mock the SDK response.
        monkeypatch.setattr(
            snapshot_client,
            "searchOrgPeerPathStats",
            lambda *args, **kwargs: SimpleNamespace(status_code=200, data={"results": [], "total": 0}),
        )  # Mock empty peers.
        with pytest.raises(ValueError, match="organization"):  # Require tenant isolation.
            SnapshotClient(object(), FakeAdmission()).collect("org-one")  # Refuse mixed-tenant data.

    def test_admission_failure_prevents_transport(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Stop before the Mist SDK call when refresh ownership is lost."""
        calls: list[bool] = []  # Record whether transport started.
        monkeypatch.setattr(
            snapshot_client, "searchOrgSwOrGwPorts", lambda *args, **kwargs: calls.append(True)
        )  # Track ports.
        client = SnapshotClient(object(), FakeAdmission(fail=True))  # Use a refused lease.
        with pytest.raises(ConnectionError, match="lease"):  # Require fail-closed admission.
            client._ports("org-one", None)  # Refuse before transport.
        assert not calls  # Prove the SDK was not called.
