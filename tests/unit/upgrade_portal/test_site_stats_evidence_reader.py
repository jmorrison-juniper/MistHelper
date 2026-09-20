"""Test the site statistics evidence reader for run reconciliation."""

from __future__ import annotations  # WHY: keep annotations from importing runtime objects.

from types import SimpleNamespace  # WHY: build a small stand-in for the mistapi response.
from typing import Any  # WHY: the SDK test seam accepts a token-bearing session object.

import pytest  # WHY: patch the SDK boundary without network access.

from src.firmware.running_version import DEFAULT_STATS_PAGE_LIMIT  # WHY: verify the bounded page size.
from src.upgrade_portal.api.run_controls import routes  # WHY: patch the exact module used by production.
from src.upgrade_portal.api.run_controls.routes import SiteStatsFirmwareEvidenceReader  # WHY: exercise the reader.


class TestSiteStatsFirmwareEvidenceReader:
    """Cover the reconciliation read that uses site device statistics."""

    def test_read_uses_mistapi_064_signature_and_preserves_running_version(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The reader omits ``fields`` and keeps the running firmware evidence."""
        seen: dict[str, Any] = {}  # WHY: capture the exact SDK arguments without a live request.
        rows = [self._statistics_row()]  # WHY: one row proves the running-version path.

        def fake_call(
            session: Any,
            site_id: str,
            type: str | None = None,
            status: str | None = None,
            limit: int | None = None,
            page: int | None = None,
        ) -> SimpleNamespace:
            seen.update(self._call_record(session, site_id, type, status, limit, page))  # WHY: prove no fields kwarg.
            return SimpleNamespace(status_code=200, data=rows)  # WHY: mimic the SDK response shape.

        monkeypatch.setattr(routes.mistapi.api.v1.sites.stats, "listSiteDevicesStats", fake_call)  # WHY: no network.
        monkeypatch.setattr(routes.mistapi, "get_all", self._all_rows)  # WHY: keep pagination deterministic.
        reader = SiteStatsFirmwareEvidenceReader("signed-session")  # WHY: pass an opaque cloud session.
        result = reader.read(self._run_record(), "2026-09-16T18:20:21+00:00")  # WHY: run the repaired path.

        assert seen == {  # WHY: the installed mistapi 0.64.0 signature accepts only these fields.
            "session": "signed-session",
            "site_id": "site-one",
            "type": "all",
            "status": None,
            "limit": DEFAULT_STATS_PAGE_LIMIT,
            "page": None,
        }
        assert result[0]["running_version"] == "24.2R2-S3.3"  # WHY: preserve the firmware evidence.
        assert result[0]["fwupdate_status"] == "success"  # WHY: preserve the reconciliation success token.

    @pytest.mark.parametrize("status_code", [404, 503], ids=["site-missing", "cloud-error"])
    def test_read_site_statistics_rejects_http_error_statuses(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
        status_code: int,
    ) -> None:
        """The evidence reader must not reconcile a failed statistics response."""

        def fake_call(*_args: Any, **_kwargs: Any) -> SimpleNamespace:
            return SimpleNamespace(status_code=status_code, data=[])  # WHY: model a real failed SDK response.

        monkeypatch.setattr(routes.mistapi.api.v1.sites.stats, "listSiteDevicesStats", fake_call)  # WHY: no network.
        reader = SiteStatsFirmwareEvidenceReader("signed-session")  # WHY: use the real reader with fake session.
        caplog.set_level("WARNING", logger=routes.logger.name)  # WHY: capture the operator-grade signal.
        result = reader._read_site_statistics("site-one")  # WHY: drive the real HTTP status branch.
        assert result is None  # WHY: failed HTTP statuses cannot supply firmware evidence.
        assert str(status_code) in caplog.text  # WHY: the log must name the exact cloud status.

    @staticmethod
    def _statistics_row() -> dict[str, Any]:
        """Return one site statistics row with extra payload fields."""
        return {  # WHY: include the fields that the evidence reader needs and one field it must drop.
            "mac": "aa:bb:cc:dd:ee:ff",
            "version": "24.2R2-S3.3",
            "uptime": 120,
            "last_seen": 1789582821,
            "fwupdate": {"status": "success"},
            "ports": [{"name": "ge-0/0/0"}],
        }

    @staticmethod
    def _run_record() -> dict[str, Any]:
        """Return one stored run record with one target."""
        return {  # WHY: match the run store shape used by stale run reconciliation.
            "site_id": "site-one",
            "targets": [{"mac": "aabbccddeeff", "version_target": "24.2R2-S3.3"}],
        }

    @staticmethod
    def _call_record(
        session: Any,
        site_id: str,
        device_type: str | None,
        status: str | None,
        limit: int | None,
        page: int | None,
    ) -> dict[str, Any]:
        """Return the recorded SDK call arguments."""
        return {  # WHY: assert the complete supported signature in one stable mapping.
            "session": session,
            "site_id": site_id,
            "type": device_type,
            "status": status,
            "limit": limit,
            "page": page,
        }

    @staticmethod
    def _all_rows(mist_session: Any, response: SimpleNamespace) -> list[dict[str, Any]]:
        """Return paged rows from the fake SDK response."""
        assert mist_session == "signed-session"  # WHY: prove pagination uses the same session object.
        return list(response.data)  # WHY: mimic ``mistapi.get_all`` without a network call.
