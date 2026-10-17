"""Collect one bounded VPN peer quality hour through the admitted Mist session."""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from mistapi.__api_response import APIResponse

from src.interfaces.portals.wan_performance.collection.peer_metrics import PeerSnapshotMetrics
from src.interfaces.portals.wan_performance.domain.identity import PeerPathIdentity
from src.interfaces.portals.wan_performance.domain.measurement import HourlyMeasurement

logger = logging.getLogger(__name__)
PEER_METRIC = "vpn_peer-metrics"
PEER_QUERY_LIMIT = 2
PEER_INTERVAL_SECONDS = 3600


class RequestAdmission(Protocol):
    """Require shared ownership before each outgoing API request."""

    def check(self) -> None:
        """Raise when ownership or request admission is unavailable."""


class MistSession(Protocol):
    """Expose only the admitted HTTP GET used by the peer insight request."""

    def mist_get(self, uri: str, query: dict[str, str] | None = None) -> APIResponse:
        """Return the Mist SDK response for one authenticated request."""


class PeerQualityInsights:
    """Read and validate the source VPN peer time-series contract."""

    def __init__(self, session: MistSession, admission: RequestAdmission) -> None:
        """Use the selected portal session and its shared admission lease."""
        self.session = session
        self.admission = admission

    def collect(self, target: PeerPathIdentity) -> tuple[HourlyMeasurement, ...]:
        """Fetch at most two source peer samples for the previous completed hour."""
        end = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
        start = end - timedelta(hours=1)
        response = self._request(target, start, end)
        measurements = self._measurements(response, target, start, end)
        logger.debug("Collected %d bounded VPN peer quality samples.", len(measurements))
        return measurements

    def _request(self, target: PeerPathIdentity, start: datetime, end: datetime) -> APIResponse:
        """Send the source peer filters through Mist's admitted session transport."""
        site_id = target.gateway.site.site_id
        device_mac = target.gateway.gateway_id
        uri = f"/api/v1/sites/{site_id}/insights/device/{device_mac}/{PEER_METRIC}"
        query = self._query(target, start, end)
        logger.info("Request bounded VPN peer insight for site %s.", site_id)
        self.admission.check()
        return self.session.mist_get(uri=uri, query=query)

    @staticmethod
    def _query(target: PeerPathIdentity, start: datetime, end: datetime) -> dict[str, str]:
        """Return the exact path filters and one completed hourly time window."""
        return {
            "start": str(int(start.timestamp())),
            "end": str(int(end.timestamp())),
            "interval": "1h",
            "limit": str(PEER_QUERY_LIMIT),
            "peer_mac": target.peer_mac,
            "port_id": target.port_name,
            "peer_port_id": target.peer_port_id,
        }

    @classmethod
    def _measurements(
        cls, response: APIResponse, target: PeerPathIdentity, start: datetime, end: datetime
    ) -> tuple[HourlyMeasurement, ...]:
        """Convert only bounded, timestamped response rows into hourly records."""
        if response.status_code != 200:
            logger.error("VPN peer insight request failed with HTTP %s.", response.status_code)
            raise ConnectionError(f"VPN peer insight request failed with HTTP {response.status_code}.")
        cls._validate_window(response.data, start, end)
        rows = cls._rows(response.data)
        records = tuple(cls._measurement(row, target, start, end) for row in rows)
        if len({record.hour_start_utc for record in records}) != len(records):
            raise ValueError("VPN peer insight results contain duplicate hourly timestamps.")
        return records

    @staticmethod
    def _validate_window(data: object, start: datetime, end: datetime) -> None:
        """Require the documented response envelope to match the bounded request."""
        if not isinstance(data, dict):
            raise ValueError("VPN peer insight response must be an object.")
        expected = (int(start.timestamp()), int(end.timestamp()), PEER_INTERVAL_SECONDS, False)
        actual = (data.get("start"), data.get("end"), data.get("interval"), bool(data.get("next")))
        if actual != expected:
            raise ValueError("VPN peer insight response does not match the requested bounded window.")

    @staticmethod
    def _rows(data: Any) -> list[dict[str, Any]]:
        """Require the documented result objects and enforce the fixed response cap."""
        if not isinstance(data, dict) or not isinstance(data.get("results"), list):
            raise ValueError("VPN peer insight results must be an array.")
        raw_rows = data["results"]
        if len(raw_rows) > PEER_QUERY_LIMIT or data.get("next"):
            raise ValueError("VPN peer insight response exceeds the fixed two-row page.")
        rows: list[dict[str, Any]] = []
        for row in raw_rows:
            if not isinstance(row, dict):
                raise ValueError("VPN peer insight results must contain objects.")
            rows.append(row)
        return rows

    @classmethod
    def _measurement(
        cls, row: dict[str, Any], target: PeerPathIdentity, start: datetime, end: datetime
    ) -> HourlyMeasurement:
        """Keep each source timestamp and its peer metrics in one UTC hour."""
        instant = cls._timestamp(row.get("timestamp"))
        if not start <= instant < end:
            raise ValueError("VPN peer insight timestamp is outside the requested hour.")
        metrics = PeerSnapshotMetrics.parse(row)
        return HourlyMeasurement(
            target,
            instant.replace(minute=0, second=0, microsecond=0),
            datetime.now(UTC),
            metrics,
            "live",
        )

    @staticmethod
    def _timestamp(value: object) -> datetime:
        """Parse source epoch seconds or an ISO 8601 timestamp as UTC."""
        if isinstance(value, bool):
            raise ValueError("VPN peer insight timestamp must be epoch seconds or ISO text.")
        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(value, UTC)
            except (OSError, OverflowError, ValueError) as error:
                raise ValueError("VPN peer insight timestamp is outside the supported range.") from error
        if not isinstance(value, str):
            raise ValueError("VPN peer insight timestamp must be epoch seconds or ISO text.")
        instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if instant.tzinfo is None:
            raise ValueError("VPN peer insight timestamp must include a UTC offset.")
        return instant.astimezone(UTC)
