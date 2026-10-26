"""Collect two bounded latest-stat pages through the existing Mist SDK session."""

import logging
import math
import re
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol
from urllib.parse import parse_qs, urlsplit
from uuid import UUID

from mistapi.api.v1.const.insight_metrics import listInsightMetrics
from mistapi.api.v1.orgs.devices import searchOrgDeviceEvents
from mistapi.api.v1.orgs.stats import listOrgDevicesStats, searchOrgPeerPathStats, searchOrgSwOrGwPorts
from mistapi.api.v1.sites.insights import getSiteInsightMetricsForDevice, getSiteInsightMetricsForGateway

from src.interfaces.wan_performance.domain.identity import CircuitIdentity, GatewayIdentity, IdentityValidator
from src.interfaces.wan_performance.domain.measurement import MetricMeasurement

logger = logging.getLogger(__name__)
STATUS_EVENT_TYPES = "GW_PORT_UP,GW_PORT_DOWN,GW_WAN_UP,GW_WAN_DOWN"
EVENT_PAGE_LIMIT = 100
MAX_EVENT_PAGES = 5


class RequestAdmission(Protocol):
    """Require shared ownership before each outgoing API request."""

    def check(self) -> None:
        """Raise when ownership or request admission is unavailable."""


class SnapshotSession:
    """Share the existing portal session and admission contract between collectors."""

    def __init__(self, session: Any, admission: RequestAdmission) -> None:
        """Use the injected portal session rather than another token flow."""
        self.session = session
        self.admission = admission


class SnapshotClient(SnapshotSession):
    """Never run a poll loop, arbitrary pagination, or an implicit retry."""

    def collect(self, org_id: str, target: GatewayIdentity | None = None) -> dict[str, object]:
        """Return at most 100 gateway ports and 100 VPN paths for one organization."""
        IdentityValidator.identifier(org_id, "org_id")
        if target is not None and target.site.org_id != org_id:
            raise ValueError("The selected gateway organization does not match the portal.")
        logger.info("Collect bounded WAN snapshot pages for organization %s.", org_id)
        self.admission.check()
        ports = self._page(
            searchOrgSwOrGwPorts(
                self.session, org_id, device_type="gateway", mac=target.gateway_id if target else None, limit=100
            )
        )
        self.admission.check()
        peers = self._page(
            searchOrgPeerPathStats(
                self.session,
                org_id,
                mac=target.gateway_id if target else None,
                site_id=target.site.site_id if target else None,
                duration="1h",
                limit=100,
            )
        )
        self._scope(ports[0] + peers[0], target)
        insights = (
            GatewayInsights(self.session, self.admission).collect(org_id, target)
            if target is not None
            else {"samples": [], "partial": False}
        )
        snapshot = {
            "org_id": org_id,
            "collected_at_utc": datetime.now(UTC).isoformat(),
            "ports": ports[0],
            "peers": peers[0],
            "insights": insights,
            "partial": ports[1] or peers[1] or insights.get("partial", False),
            "provenance": "live",
        }
        logger.debug("Collected %d ports and %d peer paths.", len(ports[0]), len(peers[0]))
        return snapshot

    @staticmethod
    def _scope(rows: list[dict[str, object]], target: GatewayIdentity | None) -> None:
        """Refuse returned rows outside the explicitly selected gateway and site."""
        if target is not None and any(
            (row.get("site_id"), row.get("mac")) != (target.site.site_id, target.gateway_id) for row in rows
        ):
            raise ValueError("WAN snapshot rows do not match the selected site and gateway.")

    @staticmethod
    def _page(response: Any) -> tuple[list[dict[str, object]], bool]:
        """Validate one result page and retain an explicit truncation indicator."""
        if response.status_code != 200:
            logger.error("WAN snapshot request failed with HTTP %s.", response.status_code)
            raise ConnectionError(f"WAN snapshot request failed with HTTP {response.status_code}.")
        data = response.data
        if not isinstance(data, dict) or not isinstance(data.get("results"), list):
            raise ValueError("WAN snapshot results must be an array.")
        rows = SnapshotClient._rows(data["results"])
        total = data.get("total")
        if total is None:
            return rows, len(rows) == 100 or bool(data.get("next"))
        if isinstance(total, bool) or not isinstance(total, int) or total < 0:
            raise ValueError("WAN snapshot total must be a non-negative integer.")
        return rows, bool(data.get("next")) or total > len(rows)

    @staticmethod
    def _rows(rows: list[object]) -> list[dict[str, object]]:
        """Enforce the fixed page size and dictionary row shape."""
        if len(rows) > 100:
            raise ValueError("WAN snapshot results must contain at most 100 objects.")
        result = []
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("WAN snapshot results must contain objects.")
            result.append(row)
        return result


class GatewayInsights(SnapshotSession):
    """Read one gateway UUID and its bounded gateway and device insight pages."""

    def collect(self, org_id: str, target: GatewayIdentity) -> dict[str, Any]:
        """Resolve one selected gateway and never infer device UUIDs from MACs."""
        return self._collect(org_id, target, None, None, None)

    def collect_for_port(
        self, org_id: str, target: CircuitIdentity, speed_mbps: object, current_status: object
    ) -> dict[str, Any]:
        """Collect raw utilization and source link events for one cached port."""
        return self._collect(org_id, target.gateway, target.port_name, speed_mbps, current_status)

    def _collect(
        self,
        org_id: str,
        target: GatewayIdentity,
        port_name: str | None,
        speed_mbps: object,
        current_status: object,
    ) -> dict[str, Any]:
        """Share discovery and catalog checks without widening either collection scope."""
        IdentityValidator.identifier(org_id, "org_id")
        if target.site.org_id != org_id:
            raise ValueError("The selected gateway organization does not match the portal.")
        self.admission.check()
        response = listOrgDevicesStats(
            self.session,
            org_id,
            type="gateway",
            site_id=target.site.site_id,
            mac=target.gateway_id,
            limit=2,
            page=1,
        )
        device = self._device(response, org_id, target)
        self.admission.check()
        catalog = listInsightMetrics(self.session)
        end = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
        start = end - timedelta(hours=1)
        interval = "10m" if port_name is not None else "1h"
        units = {name: self._metadata(catalog, name, interval) for name in ("rx_bps", "tx_bps")}
        selected = {**device, "selected_port": port_name}
        samples = self._metrics(selected, units, start, end, interval)
        status_events = None
        if port_name is not None:
            samples.extend(PortQualityInsights(self.session, self.admission).collect(device, port_name, end))
            utilization = self._utilization(samples, speed_mbps)
            samples.append(utilization)
            status_events = self._status_events(device, port_name, start, end, current_status)
            samples.extend(
                {**metric, "hour_start_utc": start.isoformat()}
                for metric in utilization["congestion_metrics"] + status_events["metrics"]
            )
        return {
            "gateway": device,
            "port_id": port_name,
            "samples": samples,
            "status_events": status_events,
            "partial": bool(status_events and not status_events["complete"]),
        }

    @staticmethod
    def _device(response: Any, org_id: str, target: GatewayIdentity) -> dict[str, Any]:
        """Reject non-array discovery, wrong tenant, and non-UUID endpoint identifiers."""
        if response.status_code != 200:
            raise ConnectionError(f"Gateway discovery failed with HTTP {response.status_code}.")
        if not isinstance(response.data, list) or len(response.data) > 1:
            raise ValueError("Gateway discovery requires an array with at most one gateway.")
        if not response.data:
            raise ValueError("The selected gateway is absent from organization discovery.")
        device = response.data[0]
        if not isinstance(device, dict) or device.get("org_id") != org_id:
            raise ValueError("Gateway discovery organization does not match the selected organization.")
        UUID(device["id"])
        IdentityValidator.identifier(device["site_id"], "site_id")
        IdentityValidator.identifier(device["mac"], "gateway MAC")
        if (device["site_id"], device["mac"]) != (target.site.site_id, target.gateway_id):
            raise ValueError("Gateway discovery does not match the selected site and MAC.")
        return device

    @staticmethod
    def _metadata(response: Any, name: str, interval_name: str) -> str:
        """Use catalog scope, unit, type, interval, and max-age rather than assumed metadata."""
        if response.status_code != 200:
            raise ConnectionError(f"Insight catalog failed with HTTP {response.status_code}.")
        if not isinstance(response.data, dict) or not isinstance(response.data.get(name), dict):
            raise ValueError("The insight catalog has no supported gateway metric.")
        metadata = response.data[name]
        scopes, unit = metadata.get("scopes"), metadata.get("unit")
        if not isinstance(scopes, list) or not {"gateway", "device"}.intersection(scopes):
            raise ValueError("The insight metric does not support gateway scope.")
        if metadata.get("type") != "timeseries":
            raise ValueError("The insight catalog must supply a timeseries unit.")
        unit = MetricMeasurement(None, unit, missing_reason="Catalog metadata validation.").unit
        interval_seconds = {"10m": 600, "1h": 3600}.get(interval_name)
        interval = metadata.get("intervals", {}).get(interval_name, {})
        if (
            interval_seconds is None
            or interval.get("interval") != interval_seconds
            or interval.get("max_age", 0) < 3600
        ):
            raise ValueError("The insight catalog does not support the requested bounded window.")
        return unit

    def _metrics(
        self, device: dict[str, Any], units: dict[str, str], start: datetime, end: datetime, interval: str
    ) -> list[dict[str, Any]]:
        """Read explicitly named rate arrays from one bounded insight response."""
        self.admission.check()
        response = getSiteInsightMetricsForGateway(
            self.session,
            device["site_id"],
            device["id"],
            "rx_bps,tx_bps",
            port_id=device.get("selected_port"),
            start=str(int(start.timestamp())),
            end=str(int(end.timestamp())),
            interval=interval,
            limit=6 if interval == "10m" else 1,
            page=1,
        )
        if response.status_code != 200:
            raise ConnectionError(f"Gateway insight request failed with HTTP {response.status_code}.")
        return [self._sample(response.data, name, unit, start, end, interval) for name, unit in units.items()]

    @staticmethod
    def _timestamps(value: object) -> list[str]:
        """Require string timestamps before date parsing."""
        if not isinstance(value, list) or not all(isinstance(timestamp, str) for timestamp in value):
            raise ValueError("Gateway insight timestamps must be a string array.")
        return [timestamp for timestamp in value if isinstance(timestamp, str)]

    @staticmethod
    def _sample_arrays(data: dict[str, Any], name: str, maximum_samples: int) -> tuple[list[str], list[object]]:
        """Select one unambiguous result array and validate its paired timestamps."""
        if name not in data or "results" in data:
            raise ValueError("Gateway insight response must name each requested metric array.")
        values = data[name]
        timestamps = GatewayInsights._timestamps(data.get("rt"))
        if not isinstance(values, list) or len(timestamps) != len(values) or len(timestamps) > maximum_samples:
            raise ValueError("Gateway insight values and timestamps must be aligned and bounded.")
        return timestamps, values

    @classmethod
    def _sample(cls, data: Any, name: str, unit: str, start: datetime, end: datetime, interval: str) -> dict[str, Any]:
        """Validate timestamps and retain every sample returned for the hour."""
        interval_seconds, maximum_samples = cls._sample_contract(interval)
        cls._validate_sample_window(data, start, end, interval_seconds)
        timestamps, values = cls._sample_arrays(data, name, maximum_samples)
        points = cls._sample_points(timestamps, values, unit, start, interval_seconds, maximum_samples)
        raw_values = tuple(point["value"] for point in points if point["value"] is not None)
        return {
            "metric": name,
            "unit": "bit/s",
            "hour_start_utc": start.isoformat(),
            "value": raw_values[-1] if raw_values else None,
            "raw_values": raw_values,
            "sample_count": len(raw_values),
            "coverage_fraction": len(raw_values) / maximum_samples,
            "missing_reason": None if raw_values else "The API snapshot has no value.",
            "points": points,
        }

    @staticmethod
    def _sample_contract(interval: str) -> tuple[int, int]:
        """Return the fixed sample interval and maximum count for one supported window."""
        contracts = {"10m": (600, 6), "1h": (3600, 1)}
        if interval not in contracts:
            raise ValueError("Gateway insight interval is not supported.")
        return contracts[interval]

    @staticmethod
    def _validate_sample_window(data: Any, start: datetime, end: datetime, interval_seconds: int) -> None:
        """Reject response metadata that does not match the bounded request."""
        if not isinstance(data, dict) or (
            data.get("start"),
            data.get("end"),
            data.get("interval"),
            bool(data.get("next")),
        ) != (int(start.timestamp()), int(end.timestamp()), interval_seconds, False):
            raise ValueError("Gateway insight response does not match the requested bounded window.")

    @classmethod
    def _sample_points(
        cls,
        timestamps: list[str],
        values: list[object],
        unit: str,
        start: datetime,
        interval_seconds: int,
        maximum_samples: int,
    ) -> list[dict[str, Any]]:
        """Pair validated timestamps with normalized rates inside the requested hour."""
        expected = {start + timedelta(seconds=interval_seconds * index) for index in range(maximum_samples)}
        parsed = [datetime.fromisoformat(timestamp.replace("Z", "+00:00")) for timestamp in timestamps]
        if any(timestamp not in expected for timestamp in parsed):
            raise ValueError("Gateway insight timestamp does not match the requested interval.")
        factor = cls._rate_factor(unit)
        return [
            {"timestamp": timestamp.isoformat(), "value": cls._rate_value(value, factor)}
            for timestamp, value in zip(parsed, values, strict=True)
        ]

    @staticmethod
    def _rate_factor(unit: str) -> int:
        """Normalize catalog byte rates to bit rates before utilization math."""
        factors = {"Bps": 8, "bit/s": 1}
        if unit not in factors:
            raise ValueError("Gateway rate insights must use Bps or bit/s catalog units.")
        return factors[unit]

    @staticmethod
    def _rate_value(value: object, factor: int) -> float | None:
        """Preserve missing samples and reject invalid or negative rate values."""
        if value is None:
            return None
        if isinstance(value, str):
            value = float(value)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0 or not math.isfinite(value):
            raise ValueError("Gateway insight rates must be non-negative finite numbers.")
        return float(value) * factor

    @classmethod
    def _utilization(cls, samples: list[dict[str, Any]], speed_mbps: object) -> dict[str, Any]:
        """Calculate each 10-minute utilization sample from aligned rates and capacity."""
        receive, transmit = cls._rate_samples(samples)
        receive_points, transmit_points = receive["points"], transmit["points"]
        cls._validate_rate_alignment(receive_points, transmit_points)
        points = cls._utilization_points(receive_points, transmit_points, speed_mbps)
        raw_values = tuple(point["value"] for point in points if point["value"] is not None)
        sample_count = len(raw_values)
        return {
            "metric": "utilization_pct",
            "unit": "%",
            "hour_start_utc": receive["hour_start_utc"],
            "value": cls._percentile(raw_values) if raw_values else None,
            "raw_values": raw_values,
            "sample_count": sample_count,
            "coverage_fraction": sample_count / 6,
            "missing_reason": (
                None if raw_values else "Utilization requires aligned rates and a positive integer port speed in Mbps."
            ),
            "congestion_metrics": cls._congestion_metrics(raw_values, sample_count),
        }

    @staticmethod
    def _rate_samples(samples: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
        """Select the receive and transmit arrays needed for port utilization."""
        by_name = {sample["metric"]: sample for sample in samples}
        try:
            return by_name["rx_bps"], by_name["tx_bps"]
        except KeyError as error:
            raise ValueError("Gateway insight response must include both rate directions.") from error

    @staticmethod
    def _validate_rate_alignment(receive_points: list[dict[str, Any]], transmit_points: list[dict[str, Any]]) -> None:
        """Require receive and transmit values to describe identical intervals."""
        receive_times = [point["timestamp"] for point in receive_points]
        transmit_times = [point["timestamp"] for point in transmit_points]
        if receive_times != transmit_times:
            raise ValueError("Receive and transmit insight timestamps must align.")

    @staticmethod
    def _utilization_points(
        receive_points: list[dict[str, Any]], transmit_points: list[dict[str, Any]], speed_mbps: object
    ) -> list[dict[str, Any]]:
        """Calculate one utilization value per aligned pair when capacity is valid."""
        return [
            {
                "timestamp": receive_point["timestamp"],
                "value": GatewayInsights._utilization_value(
                    receive_point["value"], transmit_point["value"], speed_mbps
                ),
            }
            for receive_point, transmit_point in zip(receive_points, transmit_points, strict=True)
        ]

    @staticmethod
    def _utilization_value(receive: float | None, transmit: float | None, speed_mbps: object) -> float | None:
        """Keep utilization unknown when either rate or the port capacity is absent."""
        if (
            not isinstance(speed_mbps, int)
            or isinstance(speed_mbps, bool)
            or speed_mbps <= 0
            or receive is None
            or transmit is None
        ):
            return None
        return max(receive, transmit) / speed_mbps / 1_000_000 * 100

    @staticmethod
    def _congestion_metrics(raw_values: tuple[float, ...], sample_count: int) -> list[dict[str, Any]]:
        """Summarize complete sample occupancy at the supported congestion thresholds."""
        return [GatewayInsights._congestion_metric(raw_values, threshold, sample_count) for threshold in (70, 80, 90)]

    @staticmethod
    def _percentile(values: tuple[float, ...]) -> float:
        """Apply the source short-hour maximum fallback to raw utilization samples."""
        ordered = sorted(values)
        return ordered[-1] if len(ordered) < 20 else ordered[min(int(len(ordered) * 0.95), len(ordered) - 1)]

    @staticmethod
    def _congestion_metric(values: tuple[float, ...], threshold: int, sample_count: int) -> dict[str, Any]:
        """Report congestion occupancy only when all six 10-minute samples are known."""
        metric = {
            "metric": f"congestion_minutes_over_{threshold}_pct",
            "unit": "min",
            "hour_start_utc": None,
            "value": sum(value > threshold for value in values) * 10 if sample_count == 6 else None,
            "sample_count": sample_count,
            "coverage_fraction": sample_count / 6,
            "missing_reason": None if sample_count == 6 else "Congestion duration requires six aligned samples.",
        }
        return metric

    def _status_events(
        self,
        device: dict[str, Any],
        port_name: str,
        start: datetime,
        end: datetime,
        current_status: object,
    ) -> dict[str, Any]:
        """Read a fixed number of event pages and expose incomplete history as unknown."""
        logger.info("Collect bounded link events for the selected WAN port.")
        events, cursor, pages, complete = [], None, 0, False
        for _ in range(MAX_EVENT_PAGES):
            data = self._event_page(device, start, end, cursor)
            pages += 1
            events.extend(self._matching_events(data["results"], port_name, start, end))
            cursor = self._event_cursor(data.get("next"))
            if cursor is None:
                complete = True
                break
        metrics = self._status_metrics(events, end, current_status, complete)
        logger.debug("Read %d link event pages and %d matching events.", pages, len(events))
        return {"complete": complete, "page_count": pages, "event_count": len(events), "metrics": metrics}

    def _event_page(self, device: dict[str, Any], start: datetime, end: datetime, cursor: str | None) -> dict[str, Any]:
        """Request one organization event page for one gateway and time window."""
        self.admission.check()
        response = searchOrgDeviceEvents(
            self.session,
            device["org_id"],
            mac=device["mac"],
            device_type="gateway",
            type=STATUS_EVENT_TYPES,
            limit=EVENT_PAGE_LIMIT,
            start=str(int(start.timestamp())),
            end=str(int(end.timestamp())),
            search_after=cursor,
        )
        if response.status_code != 200:
            raise ConnectionError(f"Gateway event search failed with HTTP {response.status_code}.")
        data = response.data
        if not isinstance(data, dict) or not isinstance(data.get("results"), list):
            raise ValueError("Gateway event results must be an array.")
        if len(data["results"]) > EVENT_PAGE_LIMIT:
            raise ValueError("Gateway event results exceeded the fixed page limit.")
        return data

    @classmethod
    def _matching_events(
        cls, rows: list[object], port_name: str, start: datetime, end: datetime
    ) -> list[tuple[datetime, bool]]:
        """Keep only valid link transitions that name the selected port."""
        events = []
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("Gateway event results must contain objects.")
            event_type = row.get("type")
            if event_type not in {"GW_PORT_UP", "GW_WAN_UP", "GW_PORT_DOWN", "GW_WAN_DOWN"}:
                continue
            if not cls._event_matches_port(row, port_name):
                continue
            instant = cls._event_time(row.get("timestamp"))
            if not start <= instant <= end:
                raise ValueError("Gateway event timestamp is outside the requested window.")
            events.append((instant, event_type in {"GW_PORT_UP", "GW_WAN_UP"}))
        return sorted(events, key=lambda event: event[0])

    @staticmethod
    def _event_matches_port(row: dict[str, Any], port_name: str) -> bool:
        """Match the exact port field or source event text without matching another port."""
        if any(row.get(field) == port_name for field in ("port_id", "port")):
            return True
        text = row.get("text")
        if not isinstance(text, str):
            return False
        pattern = rf"(?<![\w/.-]){re.escape(port_name)}(?![\w/.-])"
        return re.search(pattern, text, flags=re.IGNORECASE) is not None

    @staticmethod
    def _event_time(value: object) -> datetime:
        """Parse event timestamps as aware UTC instants."""
        try:
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return datetime.fromtimestamp(value, UTC)
            if isinstance(value, str):
                if value.isdecimal():
                    return datetime.fromtimestamp(float(value), UTC)
                instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
                if instant.tzinfo is not None:
                    return instant.astimezone(UTC)
        except (ValueError, OverflowError, OSError):
            pass
        raise ValueError("Gateway event timestamp must be a valid UTC instant.")

    @staticmethod
    def _event_cursor(value: object) -> str | None:
        """Extract the documented search-after token from the next-page URL."""
        if value is None or value == "":
            return None
        if not isinstance(value, str):
            raise ValueError("Gateway event pagination cursor must be a URL string.")
        cursor = parse_qs(urlsplit(value).query).get("search_after")
        if cursor and cursor[0]:
            return cursor[0]
        raise ValueError("Gateway event next-page URL has no search-after cursor.")

    @classmethod
    def _status_metrics(
        cls,
        events: list[tuple[datetime, bool]],
        end: datetime,
        current_status: object,
        complete: bool,
    ) -> list[dict[str, Any]]:
        """Calculate source-style minutes and event transitions for one hour."""
        if not complete:
            return [
                cls._missing_status_metric(name, "Event history reached the five-page limit.")
                for name in ("up_minutes", "down_minutes", "flap_count")
            ]
        return cls._complete_status_metrics(events, end, current_status)

    @classmethod
    def _complete_status_metrics(
        cls, events: list[tuple[datetime, bool]], end: datetime, current_status: object
    ) -> list[dict[str, Any]]:
        """Leave pre-event time unknown and use current state only when no events exist."""
        if not events:
            state = cls._current_state(current_status)
            up_minutes = 60.0 if state is True else 0.0 if state is False else None
            down_minutes = 60.0 if state is False else 0.0 if state is True else None
            return [
                cls._status_metric("up_minutes", up_minutes, state is not None),
                cls._status_metric("down_minutes", down_minutes, state is not None),
                cls._status_metric("flap_count", 0.0, True),
            ]
        up_seconds, down_seconds = cls._event_durations(events, end)
        return [
            cls._status_metric("up_minutes", up_seconds / 60, True, (up_seconds + down_seconds) / 3600),
            cls._status_metric("down_minutes", down_seconds / 60, True, (up_seconds + down_seconds) / 3600),
            cls._status_metric("flap_count", float(len(events)), True),
        ]

    @staticmethod
    def _current_state(value: object) -> bool | None:
        """Accept only explicit boolean or source up/down status values."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return {"up": True, "down": False}.get(value.casefold())
        return None

    @staticmethod
    def _event_durations(events: list[tuple[datetime, bool]], end: datetime) -> tuple[float, float]:
        """Accumulate known state only after the first observed event."""
        up_seconds = down_seconds = 0.0
        previous_time, state = events[0]
        for instant, next_state in events[1:]:
            elapsed = (instant - previous_time).total_seconds()
            if state:
                up_seconds += elapsed
            else:
                down_seconds += elapsed
            previous_time, state = instant, next_state
        elapsed = (end - previous_time).total_seconds()
        if state:
            up_seconds += elapsed
        else:
            down_seconds += elapsed
        return up_seconds, down_seconds

    @staticmethod
    def _status_metric(name: str, value: float | None, known: bool, coverage_fraction: float = 1.0) -> dict[str, Any]:
        """Keep status values and their evidence coverage explicit."""
        return {
            "metric": name,
            "unit": "count" if name == "flap_count" else "min",
            "hour_start_utc": None,
            "value": value,
            "sample_count": 1 if known else 0,
            "coverage_fraction": coverage_fraction if known else 0.0,
            "missing_reason": None if known else "No link events or current state are available.",
        }

    @staticmethod
    def _missing_status_metric(name: str, reason: str) -> dict[str, Any]:
        """Represent a truncated event window as unknown rather than healthy."""
        return {
            "metric": name,
            "unit": "count" if name == "flap_count" else "min",
            "hour_start_utc": None,
            "value": None,
            "sample_count": 0,
            "coverage_fraction": 0.0,
            "missing_reason": reason,
        }


class PortQualityInsights(SnapshotSession):
    """Read bounded hourly loss, jitter, and latency for one selected gateway port."""

    _FIELDS = {
        "avg_loss": ("avg_loss_pct", "%"),
        "avg_jitter": ("avg_jitter_ms", "ms"),
        "avg_latency": ("avg_latency_ms", "ms"),
    }

    def collect(self, device: dict[str, Any], port_name: str, end: datetime) -> list[dict[str, Any]]:
        """Use the existing device-scoped Mist insight endpoint and shared admission."""
        start = end - timedelta(hours=1)
        mac = device["mac"].replace("-", "")[-12:]
        self.admission.check()
        response = getSiteInsightMetricsForDevice(
            self.session,
            device["site_id"],
            "wan_link_health",
            mac,
            port_id=port_name,
            start=str(int(start.timestamp())),
            end=str(int(end.timestamp())),
            interval="1h",
            limit=1,
            page=1,
        )
        if response.status_code != 200:
            raise ConnectionError(f"Port link-health request failed with HTTP {response.status_code}.")
        return self._samples(response.data, start, end)

    @classmethod
    def _samples(cls, data: Any, start: datetime, end: datetime) -> list[dict[str, Any]]:
        """Validate the requested hour and preserve absent fields as unknown values."""
        if not isinstance(data, dict) or (
            data.get("start"),
            data.get("end"),
            data.get("interval"),
            bool(data.get("next")),
        ) != (int(start.timestamp()), int(end.timestamp()), 3600, False):
            raise ValueError("Port link-health response does not match the requested hourly window.")
        timestamps = cls._timestamps(data.get("rt", []))
        return [
            cls._sample(data, field, metric, unit, timestamps, start) for field, (metric, unit) in cls._FIELDS.items()
        ]

    @staticmethod
    def _timestamps(value: object) -> list[datetime]:
        """Parse at most one UTC timestamp from the response."""
        if not isinstance(value, list) or len(value) > 1:
            raise ValueError("Port link-health timestamps must contain at most one value.")
        if not value:
            return []
        timestamp = value[0]
        if isinstance(timestamp, (int, float)) and not isinstance(timestamp, bool):
            return [datetime.fromtimestamp(timestamp, UTC)]
        if not isinstance(timestamp, str):
            raise ValueError("Port link-health timestamp must be text or epoch seconds.")
        return [datetime.fromisoformat(timestamp.replace("Z", "+00:00"))]

    @staticmethod
    def _sample(
        data: dict[str, Any],
        field: str,
        metric: str,
        unit: str,
        timestamps: list[datetime],
        start: datetime,
    ) -> dict[str, Any]:
        """Map one optional hourly series to its source-compatible name and unit."""
        values = data.get(field, [])
        if values is None:
            values = []
        if not isinstance(values, list) or len(values) > 1:
            raise ValueError(f"Port link-health field {field} must contain at most one value.")
        if values and timestamps and timestamps[0] != start:
            raise ValueError("Port link-health timestamp does not match the requested hour.")
        return {
            "metric": metric,
            "unit": unit,
            "hour_start_utc": start.isoformat(),
            "value": values[0] if values else None,
        }
