"""Test selected WAN dashboard CSV exports and spreadsheet safety."""

from __future__ import annotations

import csv
import io

import pytest
from flask import Flask
from flask.testing import FlaskClient

from src.interfaces.portals.wan_dashboard.routes import wan_dashboard_bp


class ExportService:
    """Return synthetic rows for the two dashboard exports."""

    def export_gateways(self, **_filters: object) -> dict[str, object]:
        """Return values that exercise CSV quoting and formula neutralization."""
        return {
            "status": "ok",
            "data": [{"name": "=1+1", "site_name": "Site, North", "status": "up", "model": "M", "wan_port_count": 1}],
        }  # Include formula and delimiter text.

    def get_hourly_export(self, gateway_id: str, port_id: str, time_range: str) -> dict[str, object]:
        """Return one hourly row with the exact source field names."""
        return {
            "status": "ok",
            "data": {
                "site_name": "=Site",
                "gateway_hostname": gateway_id,
                "hourly": [
                    {
                        "timestamp": 1,
                        "hour_iso": "1970-01-01T00:00:00Z",
                        "rx_bps": None,
                        "max_rx_bps": 2,
                        "tx_bps": 3,
                        "max_tx_bps": 4,
                        "avg_jitter_ms": 5,
                        "avg_latency_ms": 6,
                        "avg_loss_pct": 7,
                    }
                ],
                "range": time_range,
                "port_id": port_id,
            },
        }  # Keep export values synthetic.


def build_client() -> FlaskClient:
    """Return a local client with the production export routes."""
    app = Flask(__name__)  # Build an isolated application.
    app.config.update(TESTING=True, WAN_DASHBOARD_SERVICE=ExportService())  # Inject the synthetic service.
    app.register_blueprint(wan_dashboard_bp)  # Register the production feature routes.
    return app.test_client()  # Use the app without a server or cloud credential.


class TestGatewayExport:
    """Prove that gateway CSV cells remain safe for spreadsheet users."""

    def test_gateway_export_neutralizes_formulas_and_quotes_delimiters(self) -> None:
        """Formula-leading text receives a safe prefix and delimiter text stays quoted."""
        response = build_client().get("/wan-dashboard/api/gateways/export?search=gw")  # Request one filtered export.
        rows = list(csv.reader(io.StringIO(response.get_data(as_text=True))))  # Parse the emitted CSV records.

        assert response.status_code == 200  # The selected rows export successfully.
        assert rows[0] == ["gateway", "site", "model", "status", "wan_ports"]  # Keep the stable header order.
        assert rows[1] == ["'=1+1", "Site, North", "M", "up", "1"]  # Neutralize formulas and preserve cells.


class TestHourlyExport:
    """Prove that hourly export keeps the source's twelve columns."""

    def test_hourly_export_has_twelve_columns_and_blank_missing_values(self) -> None:
        """The selected hourly metrics retain the source header and empty cells."""
        response = build_client().get(
            "/wan-dashboard/api/gateways/gw-a/ports/wan0/hourly/export?range=24h"
        )  # Request one gateway port and range.
        rows = list(csv.reader(io.StringIO(response.get_data(as_text=True))))  # Parse the emitted CSV.

        assert response.status_code == 200  # The requested range is valid.
        assert len(rows[0]) == 12  # Keep the source's canonical export width.
        assert rows[0] == [
            "site_name",
            "gateway_name",
            "port_id",
            "hour_epoch",
            "hour_iso",
            "rx_avg_bps",
            "rx_peak_bps",
            "tx_avg_bps",
            "tx_peak_bps",
            "jitter_avg_ms",
            "latency_avg_ms",
            "loss_avg_pct",
        ]  # Preserve source column order.
        assert len(rows[1]) == 12  # Keep every data record aligned with the header.
        assert rows[1][0] == "'=Site"  # Neutralize formula-leading Mist text.
        assert rows[1][5] == ""  # Render an absent counter as a blank cell.

    def test_partial_insights_are_not_sent_as_a_current_csv(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A failed insight result remains JSON instead of becoming an empty CSV."""
        service = ExportService()  # Reuse the local response provider.
        monkeypatch.setattr(
            service,
            "get_hourly_export",
            lambda *_args: {
                "status": "partial",
                "data": {"hourly": []},
                "notice": "Mist rate limit reached.",
            },
        )  # Model a response that cannot support a complete export.
        app = Flask(__name__)  # Build an isolated application.
        app.config.update(TESTING=True, WAN_DASHBOARD_SERVICE=service)  # Inject synthetic service data.
        app.register_blueprint(wan_dashboard_bp)  # Register only the production feature routes.

        response = app.test_client().get(
            "/wan-dashboard/api/gateways/gw-a/ports/wan0/hourly/export?range=24h"
        )  # Request the selected hourly output.

        assert response.status_code == 200  # The partial-state JSON remains an API response.
        assert response.mimetype == "application/json"  # Keep a failed export as a JSON response.
        assert response.get_json()["status"] == "partial"  # Preserve the service failure state.
