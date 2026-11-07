"""Collect one bounded VPN peer-quality window through the Mist SDK session."""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from src.interfaces.wan_performance.collection.snapshot_records import PeerSnapshotMetrics
from src.interfaces.wan_performance.domain.identity import PeerPathIdentity
from src.interfaces.wan_performance.domain.measurement import HourlyMeasurement

logger = logging.getLogger(__name__)
PEER_ROW_LIMIT = 2  # Bound source response size.
PEER_INTERVAL_SECONDS = 3600  # Match one completed hour.


class RequestAdmission(Protocol):
    """Require shared ownership before each outgoing request."""

    def check(self) -> None:
        """Raise when request admission or refresh ownership is unavailable."""


class MistSession(Protocol):
    """Expose the authenticated Mist SDK request method."""

    def mist_get(self, uri: str, query: dict[str, str] | None = None) -> Any:
        """Return one SDK response for an authenticated read."""


class PeerResponseValidator:
    """Validate bounded peer response metadata and rows."""

    @classmethod
    def measurements(
        cls, response: Any, target: PeerPathIdentity, start: datetime, end: datetime
    ) -> tuple[HourlyMeasurement, ...]:
        """Convert valid response rows into immutable hourly measurements."""
        if response.status_code != 200:  # HTTP failures must not look like empty data.
            raise ConnectionError(
                f"VPN peer insight request failed with HTTP {response.status_code}."
            )  # Report status.
        data = response.data  # Read the SDK response body.
        if not isinstance(data, dict):  # Require the documented response object.
            raise ValueError("VPN peer insight response must be an object.")  # Reject malformed bodies.
        cls._window(data, start, end)  # Match source metadata to the request.
        rows = data.get("results")  # Read the bounded result list.
        if not isinstance(rows, list) or len(rows) > PEER_ROW_LIMIT or data.get("next"):  # Enforce fixed bounds.
            raise ValueError("VPN peer insight response exceeds the fixed two-row page.")  # Reject extra pages.
        records = tuple(cls._record(row, target, start, end) for row in rows)  # Validate each source row.
        hours = [record.hour_start_utc for record in records]  # Collect natural hour keys.
        if len(set(hours)) != len(hours):  # Duplicate timestamps would overwrite observations.
            raise ValueError("VPN peer insight results contain duplicate hourly timestamps.")  # Reject collisions.
        return records  # Return only validated measurements.

    @staticmethod
    def _window(data: dict[str, Any], start: datetime, end: datetime) -> None:
        """Require one completed-hour response with no continuation page."""
        expected = (int(start.timestamp()), int(end.timestamp()), PEER_INTERVAL_SECONDS, False)  # Define request scope.
        actual = (data.get("start"), data.get("end"), data.get("interval"), bool(data.get("next")))  # Read metadata.
        if actual != expected:  # Reject a response for another interval.
            raise ValueError("VPN peer insight response does not match the requested bounded window.")  # Fail closed.

    @classmethod
    def _record(cls, row: object, target: PeerPathIdentity, start: datetime, end: datetime) -> HourlyMeasurement:
        """Validate one timestamp and preserve only documented peer metrics."""
        if not isinstance(row, dict):  # Each result must be one source object.
            raise ValueError("VPN peer insight results must contain objects.")  # Reject malformed rows.
        instant = cls._timestamp(row.get("timestamp"))  # Validate the source time.
        if not start <= instant < end:  # Keep samples inside the requested hour.
            raise ValueError("VPN peer insight timestamp is outside the requested hour.")  # Reject out-of-range data.
        hour = instant.replace(minute=0, second=0, microsecond=0)  # Assign the observation hour only.
        metrics = PeerSnapshotMetrics.parse(row)  # Validate the documented metric fields.
        return HourlyMeasurement(target, hour, datetime.now(UTC), metrics, "live")  # Preserve live source provenance.

    @staticmethod
    def _timestamp(value: object) -> datetime:
        """Parse epoch seconds or timezone-aware ISO text as UTC."""
        if isinstance(value, bool):  # Booleans can behave like integers in Python.
            raise ValueError("VPN peer timestamp must use epoch seconds or ISO text.")  # Reject ambiguous input.
        if isinstance(value, (int, float)):  # Accept numeric epoch seconds.
            try:  # Guard platform timestamp limits.
                return datetime.fromtimestamp(value, UTC)  # Normalize the source instant to UTC.
            except (OSError, OverflowError, ValueError) as error:  # Reject unsupported epoch values.
                raise ValueError("VPN peer timestamp is outside the supported range.") from error  # Preserve cause.
        if not isinstance(value, str):  # Require supported source formats.
            raise ValueError("VPN peer timestamp must use epoch seconds or ISO text.")  # Reject invalid types.
        instant = datetime.fromisoformat(value.replace("Z", "+00:00"))  # Parse an ISO UTC suffix.
        if instant.tzinfo is None:  # Naive times cannot identify a global instant.
            raise ValueError("VPN peer timestamp must include a UTC offset.")  # Reject local time.
        return instant.astimezone(UTC)  # Normalize explicit offsets to UTC.


class PeerQualityInsights:
    """Read and validate one bounded VPN peer time-series request."""

    def __init__(self, session: MistSession, admission: RequestAdmission) -> None:
        """Use the selected portal session and its shared admission lease."""
        self.session = session  # Reuse the authenticated SDK session.
        self.admission = admission  # Reuse the current refresh owner.

    def collect(self, target: PeerPathIdentity) -> tuple[HourlyMeasurement, ...]:
        """Fetch at most two peer samples for the previous completed hour."""
        end = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)  # End at the current UTC hour.
        start = end - timedelta(hours=1)  # Request the previous complete interval.
        response = self._request(target, start, end)  # Send one admitted SDK request.
        records = PeerResponseValidator.measurements(response, target, start, end)  # Validate every returned row.
        logger.debug("Collected %d bounded VPN peer samples.", len(records))  # Record the result count.
        return records  # Keep an empty result distinct from request failure.

    def _request(self, target: PeerPathIdentity, start: datetime, end: datetime) -> Any:
        """Send a scoped peer query through the authenticated SDK session."""
        site_id = target.gateway.site.site_id  # Preserve the selected site.
        device_mac = target.gateway.gateway_id  # Use the source gateway identifier.
        uri = f"/api/v1/sites/{site_id}/insights/device/{device_mac}/vpn_peer-metrics"  # Use the documented SDK path.
        query = {  # Keep each query boundary explicit.
            "start": str(int(start.timestamp())),  # Bound the request start.
            "end": str(int(end.timestamp())),  # Bound the request end.
            "interval": "1h",  # Request one hourly interval.
            "limit": str(PEER_ROW_LIMIT),  # Keep the response bounded.
            "peer_mac": target.peer_mac,  # Select the remote peer.
            "port_id": target.port_name,  # Select the local port.
            "peer_port_id": target.peer_port_id,  # Select the remote port.
        }
        logger.info("Request bounded VPN peer insight for site %s.", site_id)  # Log scope without credentials.
        self.admission.check()  # Refuse before transport if ownership expired.
        return self.session.mist_get(uri=uri, query=query)  # Use the Mist SDK session transport.
