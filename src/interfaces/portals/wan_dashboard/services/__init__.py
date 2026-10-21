"""Collect, validate, cache, and export MistCircuitStats dashboard data."""

from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
import logging
import math
import re
import threading
import time
from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import mistapi
import redis
import requests

logger = logging.getLogger(__name__)  # Keep feature events under one module name.


class RedisDashboardCache:
    """Store short-lived dashboard values in the existing Redis service."""

    def __init__(self, client: Any | None) -> None:
        """Keep the shared Redis client or record that it is unavailable."""
        self._client = client  # Reuse the portal's Redis handle without opening another service.

    def get(self, key: str) -> Any | None:
        """Return one decoded value, or None when the cache is unavailable."""
        if self._client is None:  # Redis may be down while the read-only page remains useful.
            return None  # Let the caller read Mist through the shared session.
        try:  # A cache fault must not be mistaken for a successful cloud result.
            value = self._client.get(key)  # Read one feature-namespaced key.
            return json.loads(value) if value else None  # Decode only values that exist.
        except (redis.RedisError, OSError, TimeoutError, TypeError, ValueError) as error:
            logger.warning("wan dashboard cache read failed (%s)", type(error).__name__)  # Do not log cached payloads.
            return None  # Continue through the shared Mist session.

    def set(self, key: str, value: Any, ttl: int) -> None:
        """Write one JSON-safe value with a bounded expiry."""
        if self._client is None:  # No local or second Redis server may replace the shared service.
            return  # The in-process last-success record still supports this worker.
        try:  # Cache failures must remain visible without stopping a safe read.
            payload = json.dumps(value, allow_nan=False, separators=(",", ":"))  # Keep only valid JSON numbers.
            self._client.set(key, payload, ex=ttl)  # Let Redis enforce the configured expiry.
        except (redis.RedisError, OSError, TimeoutError, TypeError, ValueError) as error:
            logger.warning("wan dashboard cache write failed (%s)", type(error).__name__)  # Keep payloads private.


class MistSessionRunner:
    """Run each SDK request once per available token with a shared cooldown."""

    COOLDOWN_SECONDS = 60
    COOLDOWN_KEY_PREFIX = "wan-dashboard:v1:cooldown:"

    def __init__(self, session: Any, org_id: str, cache: RedisDashboardCache) -> None:
        """Keep the Mist session, organization, cache, and local cooldown state."""
        self._session = session  # Use the session supplied by MistHelper.
        self._org_id = org_id  # Scope cooldown keys to the selected organization.
        self._cache = cache  # Reuse the same Redis adapter as dashboard records.
        self._cooldowns: dict[str, float] = {}  # Retain cooldowns when shared Redis is unavailable.
        self._guard = threading.Lock()  # Protect cooldown state across portal request threads.

    def call(self, function: Callable[..., Any], *args: Any, **kwargs: Any) -> tuple[Any | None, str | None]:
        """Call one SDK function with one attempt per token."""
        tokens = self._available_tokens()  # Remove tokens that still honor a previous 429.
        if not tokens:  # No credential can issue a request now.
            return None, "rate_limited"  # Preserve a specific operator-visible status.
        for token in tokens:  # Each candidate appears once in this SDK request.
            request_session = self._clone_session(token)  # Keep SDK retries from consuming another token.
            request_args, request_kwargs = self._replace_session(args, kwargs, request_session)
            try:  # The SDK owns transport and API encoding.
                response = function(*request_args, **request_kwargs)  # Send one supported SDK request.
            except (requests.RequestException, OSError, TimeoutError) as error:
                logger.error("wan dashboard SDK request failed (%s)", type(error).__name__)  # Omit secrets and URLs.
                return None, type(error).__name__  # Report a transport failure without response data.
            status = getattr(response, "status_code", None)  # Reject response objects without a usable status.
            if status == 429:  # A rate limit applies to this token only.
                self._mark_cooldown(token)  # Honor the fixed per-token wait before another SDK call.
                continue  # Try the next authorized token once.
            if status != 200:  # Keep every non-success response distinct from empty data.
                return response, f"http_{status or 'unknown'}"  # Preserve the status without the body.
            return response, None  # Return only a successful SDK response.
        return None, "rate_limited"  # Every configured token reached the rate limit.

    def _available_tokens(self) -> list[str | None]:
        """Return unexpired tokens in the session's configured rotation order."""
        raw_tokens = getattr(self._session, "_apitoken", [])  # Mist SDK keeps configured tokens on its session.
        tokens = list(dict.fromkeys(raw_tokens)) if isinstance(raw_tokens, list) else []  # Remove duplicates.
        if not tokens:  # A cookie-authenticated session has no rotating API token.
            return [None]  # Preserve its existing authenticated session.
        index = getattr(self._session, "_apitoken_index", 0)  # Keep the SDK's current token as the first choice.
        start = index if 0 <= index < len(tokens) else 0  # Guard a stale SDK index.
        ordered = tokens[start:] + tokens[:start]  # Try each configured token once.
        return [token for token in ordered if not self._is_limited(token)]  # Respect each 60-second cooldown.

    def _is_limited(self, token: str) -> bool:
        """Return whether a token is inside its cooldown window."""
        fingerprint = self._fingerprint(token)  # Never place the token itself in a key or log.
        with self._guard:  # Keep the local fallback consistent across request threads.
            expiry = self._cooldowns.get(fingerprint, 0.0)  # Read the local monotonic expiry.
            if expiry > time.monotonic():  # The local entry is still active.
                return True  # Skip the token without a Mist request.
            self._cooldowns.pop(fingerprint, None)  # Drop an expired local entry.
        return bool(self._cache.get(self.COOLDOWN_KEY_PREFIX + self._org_id + ":" + fingerprint))

    def _mark_cooldown(self, token: str | None) -> None:
        """Store a 60-second cooldown without storing the credential."""
        if token is None:  # A cookie session has no token to fingerprint.
            return  # The next request still makes only one SDK attempt.
        fingerprint = self._fingerprint(token)  # Hash the credential before it reaches shared storage.
        with self._guard:  # Keep local expiry updates atomic.
            self._cooldowns[fingerprint] = time.monotonic() + self.COOLDOWN_SECONDS  # Bound the fallback.
        key = self.COOLDOWN_KEY_PREFIX + self._org_id + ":" + fingerprint  # Scope the key to this feature and org.
        self._cache.set(key, True, self.COOLDOWN_SECONDS)  # Share the cooldown between portal workers.

    @staticmethod
    def _fingerprint(token: str) -> str:
        """Return a one-way key for a token without exposing its value."""
        return hashlib.sha256(token.encode("utf-8")).hexdigest()[:24]  # Keep only the digest prefix.

    def _clone_session(self, token: str | None) -> Any:
        """Clone SDK request state so one 429 cannot rotate the shared session."""
        cloned = copy.copy(self._session)  # Preserve the configured cloud, cookies, and authentication mode.
        original_http = getattr(self._session, "_session", None)  # The SDK wraps a Requests session.
        if original_http is not None:  # A test double may omit the transport field.
            cloned_http = copy.copy(original_http)  # Keep adapters and transport configuration.
            for name in ("headers", "proxies", "params", "hooks", "cookies"):
                value = getattr(original_http, name, None)  # Read mutable request state.
                if value is not None:  # Some minimal session doubles omit optional attributes.
                    setattr(cloned_http, name, copy.deepcopy(value))  # Isolate request headers and cookies.
            cloned._session = cloned_http  # Keep the isolated transport on the SDK copy.
            if token is not None:  # Set only the selected authorized token.
                cloned._session.headers["Authorization"] = "Token " + token  # Do not mutate the shared session.
        cloned._apitoken = [token] if token is not None else []  # Prevent the SDK from rotating this request.
        cloned._apitoken_index = 0 if token is not None else -1  # Keep token selection explicit.
        cloned._MAX_429_RETRIES = 0  # One response per token prevents SDK-owned hidden retries.
        return cloned  # The caller discards the isolated session after the request.

    @staticmethod
    def _replace_session(
        args: tuple[Any, ...], kwargs: dict[str, Any], request_session: Any
    ) -> tuple[tuple[Any, ...], dict[str, Any]]:
        """Replace only the shared session argument with the isolated copy."""
        request_args = list(args)  # Copy arguments so the caller's tuple remains unchanged.
        request_kwargs = dict(kwargs)  # Copy keywords so later pages can reuse the original call shape.
        if request_args and request_args[0] is not None:  # SDK endpoint methods take the session first.
            request_args[0] = request_session  # Replace only the session argument.
        elif request_kwargs.get("mist_session") is not None:  # Pagination uses a named session argument.
            request_kwargs["mist_session"] = request_session  # Preserve all other SDK parameters.
        return tuple(request_args), request_kwargs  # Return immutable positional arguments and copied keywords.


class WanDataNormalizer:
    """Validate and shape raw Mist responses for the dashboard."""

    IDENTIFIER = re.compile(r"\A[A-Za-z0-9_-]{1,128}\Z")
    PORT_IDENTIFIER = re.compile(r"\A[A-Za-z0-9._:/-]{1,128}\Z")
    TRAFFIC_SECONDS = {"1h": 3600, "6h": 21600, "24h": 86400, "7d": 604800}
    INSIGHT_SECONDS = {"1h": 3600, "6h": 21600, "24h": 86400, "3d": 259200, "7d": 604800}
    HOURLY_COLUMNS = (
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
    )

    @classmethod
    def rows(cls, payload: object) -> list[dict[str, Any]] | None:
        """Return a validated list from Mist's list or results envelope."""
        if isinstance(payload, list) and all(isinstance(row, dict) for row in payload):
            return payload  # Accept a direct list only when each row is an object.
        if isinstance(payload, dict) and isinstance(payload.get("results"), list):
            values = payload["results"]  # Read the SDK's search response envelope.
            return values if all(isinstance(row, dict) for row in values) else None  # Reject malformed members.
        return None  # Do not convert an unknown payload into an empty result.

    @classmethod
    def identifier(cls, value: str, *, port: bool = False) -> bool:
        """Check a path identifier against the correct route-safe pattern."""
        pattern = cls.PORT_IDENTIFIER if port else cls.IDENTIFIER  # Port names may contain slashes.
        return bool(pattern.fullmatch(value)) and value not in {".", ".."}  # Reject traversal segments.

    @staticmethod
    def numeric(value: object) -> float | None:
        """Return a finite non-negative metric, or None when Mist omits it."""
        if isinstance(value, bool) or not isinstance(value, (int, float)):  # Booleans are not metric values.
            return None  # Preserve unavailable values instead of inventing zero.
        number = float(value)  # Normalize SDK integers and floats.
        return number if math.isfinite(number) and number >= 0 else None  # Reject invalid metric values.

    @classmethod
    def port_rows(
        cls, source: list[dict[str, Any]], config: dict[str, Any], stats: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Merge Mist port search rows, device configuration, and live counters."""
        configs = cls._port_config(config)  # Keep only named configuration rows.
        output: list[dict[str, Any]] = []  # Build the operator-facing port records.
        for port in source:  # Preserve the Mist port order before sorting.
            output.append(cls._port_row(port, configs, stats))  # Keep unavailable values as None.
        return output  # The caller groups ports under the owning gateway.

    @classmethod
    def _port_row(
        cls,
        port: dict[str, Any],
        configs: dict[str, dict[str, Any]],
        stats: dict[str, Any],
    ) -> dict[str, Any]:
        """Merge one source port with its configuration and live counters."""
        port_id = str(port.get("port_id") or port.get("name") or "")  # Use the stable SDK port identifier.
        raw_live = stats.get(port_id, {}) if isinstance(stats, dict) else {}
        live = raw_live if isinstance(raw_live, dict) else {}  # Reject malformed per-port statistics.
        setting = configs.get(port_id, {})  # Use only the matching device configuration.
        configuration = cls._port_configuration(port, setting, port_id)  # Preserve the source interface settings.
        metrics = cls._port_metrics(port, live)  # Keep current link state and counters separate from configuration.
        enabled = configuration["enabled"]  # Prefer an explicit enabled value when Mist supplies one.
        if not isinstance(enabled, bool):  # Derive enablement only when the source omits its boolean.
            enabled = (
                metrics["up"] is True and setting.get("disabled") is not True
            )  # Match source physical-state rules.
        return {
            "port_id": port_id,
            **configuration,
            **metrics,
            "enabled": enabled,
        }  # Keep unavailable values distinct from zero.

    @classmethod
    def _port_configuration(cls, port: dict[str, Any], setting: dict[str, Any], port_id: str) -> dict[str, Any]:
        """Return the static settings for one normalized port."""
        return {
            "name": str(cls._first_value(setting.get("name"), port.get("name"), port_id)),
            "wan_name": str(cls._first_value(setting.get("wan_name"), port.get("wan_name"), "")),
            "description": str(cls._first_value(setting.get("description"), port.get("description"), "")),
            "enabled": cls._first_value(setting.get("enabled"), port.get("enabled")),
            "usage": port.get("port_usage"),
            "gateway": cls._first_value(setting.get("gateway"), port.get("gateway")),
            "ip": cls._first_value(setting.get("ip"), port.get("ip")),
            "configuration_type": cls._first_value(
                setting.get("type"), setting.get("wan_type"), port.get("configuration_type"), port.get("type")
            ),
            "vlan_id": cls._first_value(setting.get("vlan_id"), port.get("vlan_id")),
            "netmask": cls._first_value(setting.get("netmask"), port.get("netmask")),
            "override": cls._first_value(setting.get("override"), port.get("override")),
        }  # Keep optional source configuration visible as missing.

    @staticmethod
    def _first_value(*values: Any) -> Any:
        """Return the first configured value without dropping false booleans or zero."""
        for value in values:
            if value is not None and value != "":
                return value
        return None

    @classmethod
    def _port_metrics(cls, port: dict[str, Any], live: dict[str, Any]) -> dict[str, Any]:
        """Return validated counters for one normalized port."""
        speed = live.get("speed")  # Prefer the live counter when it exists.
        speed = speed if speed is not None else port.get("speed")  # Preserve an explicit zero speed.
        return {
            "up": live.get("up", port.get("up")),
            "mac": live.get("mac") or port.get("port_mac") or port.get("mac"),
            "speed": cls.numeric(speed),
            "uptime": cls.numeric(live.get("uptime")),
            "rx_bytes": cls.numeric(live.get("rx_bytes")),
            "tx_bytes": cls.numeric(live.get("tx_bytes")),
            "rx_bps": cls.numeric(live.get("rx_bps")),
            "tx_bps": cls.numeric(live.get("tx_bps")),
        }  # Reject non-finite counters and keep missing values as None.

    @classmethod
    def _port_config(cls, payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
        """Find named port configurations in the device, profile, or template data."""
        candidate = payload.get("port_config", payload.get("ports", {}))  # Read the documented config container.
        if isinstance(candidate, list):  # Some Mist payloads return an array of named ports.
            return {str(row.get("name") or row.get("port_id")): row for row in candidate if isinstance(row, dict)}
        if isinstance(candidate, dict):  # Common gateway templates use a mapping keyed by interface.
            return {str(name): row for name, row in candidate.items() if isinstance(row, dict)}
        return {}  # Missing optional configuration stays unavailable.

    @classmethod
    def traffic_samples(cls, payload: dict[str, Any], start: int, interval: int) -> list[dict[str, Any]]:
        """Build validated, UTC traffic samples from gateway insight arrays."""
        timestamps = cls._series(payload, "timestamps")  # Use explicit Mist timestamps when available.
        rx = cls._series(payload, "rx_bps")  # Keep missing values absent rather than zero.
        tx = cls._series(payload, "tx_bps")  # Keep missing values absent rather than zero.
        count = max(len(rx), len(tx), len(timestamps))  # Preserve every metric bucket.
        samples: list[dict[str, Any]] = []  # Build one row for each available bucket.
        for index in range(count):  # Preserve the API order across the selected time window.
            timestamp = timestamps[index] if index < len(timestamps) else start + index * interval
            if not isinstance(timestamp, (int, float)) or isinstance(timestamp, bool):
                continue  # Skip a bucket whose time cannot be represented safely.
            if not math.isfinite(float(timestamp)) or not 0 <= timestamp <= 253402300799:
                continue  # Keep untrusted epoch values inside the supported UTC range.
            samples.append(
                {
                    "timestamp": int(timestamp),
                    "timestamp_utc": datetime.fromtimestamp(timestamp, UTC).isoformat(),
                    "rx_bps": cls.numeric(rx[index]) if index < len(rx) else None,
                    "tx_bps": cls.numeric(tx[index]) if index < len(tx) else None,
                }
            )  # Keep every accepted bucket tied to a UTC time.
        return samples  # The page can render each metric as a separate series.

    @classmethod
    def hourly_rows(cls, data: dict[str, Any], start: int, interval: int = 3600) -> list[dict[str, Any]]:
        """Normalize hourly bandwidth and WAN link-health arrays."""
        bandwidth = data.get("bandwidth")  # Read the gateway-scoped metric result.
        health = data.get("link_health")  # Read the device-scoped link result.
        bandwidth = bandwidth if isinstance(bandwidth, dict) else {}  # Reject malformed optional payloads.
        health = health if isinstance(health, dict) else {}  # Reject malformed optional payloads.
        rx, tx = cls._series(bandwidth, "rx_bps"), cls._series(bandwidth, "tx_bps")
        peak_rx, peak_tx = cls._series(bandwidth, "max_rx_bps"), cls._series(bandwidth, "max_tx_bps")
        jitter = cls._series(health, "avg_jitter")
        latency = cls._series(health, "avg_latency")
        loss = cls._series(health, "avg_loss")
        series = {
            "rx_bps": rx,
            "max_rx_bps": peak_rx,
            "tx_bps": tx,
            "max_tx_bps": peak_tx,
            "avg_jitter_ms": jitter,
            "avg_latency_ms": latency,
            "avg_loss_pct": loss,
        }  # Keep each source array paired with its output name.
        count = max(map(len, series.values()), default=0)  # Keep each returned hourly bucket.
        rows: list[dict[str, Any]] = []  # Keep one output row for every returned bucket.
        for index in range(count):  # Align each metric by its source index.
            rows.append(cls._hourly_row(series, start, interval, index))  # Preserve missing metrics as unavailable.
        return rows  # The CSV writer controls column order and escaping.

    @classmethod
    def _hourly_row(cls, series: dict[str, list[Any]], start: int, interval: int, index: int) -> dict[str, Any]:
        """Build one UTC bucket from all available hourly series."""
        timestamp = start + index * interval  # Use UTC epoch seconds from the validated query window.
        row = {
            name: cls._series_value(values, index) for name, values in series.items()
        }  # Keep each metric aligned by source index.
        return {
            "timestamp": timestamp,
            "hour_iso": datetime.fromtimestamp(timestamp, UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            **row,
        }  # None remains a blank export cell, not a false zero.

    @classmethod
    def _series_value(cls, values: list[Any], index: int) -> float | None:
        """Return one finite numeric sample when its source index exists."""
        return cls.numeric(values[index]) if index < len(values) else None  # Keep missing samples unavailable.

    @staticmethod
    def _series(payload: dict[str, Any], key: str) -> list[Any]:
        """Return a metric array only when Mist supplies a list."""
        value = payload.get(key)  # Read one documented array.
        return value if isinstance(value, list) else []  # Treat a malformed optional series as unavailable.


class CsvExporter:
    """Build spreadsheet-safe CSV documents for the dashboard."""

    GATEWAY_COLUMNS = ("gateway", "site", "model", "status", "wan_ports")

    @classmethod
    def gateway_csv(cls, gateways: list[dict[str, Any]]) -> str:
        """Return the selected gateway rows with a stable header."""
        output = io.StringIO(newline="")  # Let csv.writer control newline and quoting.
        writer = csv.writer(output, lineterminator="\n")  # Use portable line endings.
        writer.writerow(cls.GATEWAY_COLUMNS)  # Keep the source overview export fields in a fixed order.
        for gateway in gateways:  # Write only the rows selected by the route filters.
            writer.writerow(
                cls._safe(value)
                for value in (
                    gateway.get("name"),
                    gateway.get("site_name"),
                    gateway.get("model"),
                    gateway.get("status"),
                    gateway.get("wan_port_count"),
                )
            )  # Neutralize user-controlled text before it reaches a spreadsheet.
        return output.getvalue()  # Return UTF-8-ready text for Flask.

    @classmethod
    def hourly_csv(cls, payload: dict[str, Any]) -> str:
        """Return the source's canonical twelve-column hourly export."""
        output = io.StringIO(newline="")  # Keep CSV newline handling consistent.
        writer = csv.writer(output, lineterminator="\n")  # Quote commas and line breaks safely.
        writer.writerow(WanDataNormalizer.HOURLY_COLUMNS)  # Preserve the source column order.
        for row in sorted(payload.get("hourly", []), key=lambda item: item.get("timestamp", 0)):
            writer.writerow(cls._hourly_cells(payload, row))  # Keep each output row at twelve fields.
        return output.getvalue()  # Return the complete selected export.

    @classmethod
    def _hourly_cells(cls, payload: dict[str, Any], row: dict[str, Any]) -> list[Any]:
        """Build one sanitized row for the hourly metrics export."""
        values = (
            payload.get("site_name"),
            payload.get("gateway_hostname"),
            payload.get("port_id"),
            row.get("timestamp"),
            row.get("hour_iso"),
            row.get("rx_bps"),
            row.get("max_rx_bps"),
            row.get("tx_bps"),
            row.get("max_tx_bps"),
            row.get("avg_jitter_ms"),
            row.get("avg_latency_ms"),
            row.get("avg_loss_pct"),
        )  # Keep the twelve values aligned with the fixed header.
        return [cls._safe(value) for value in values]  # Sanitize every cell before writing.

    @staticmethod
    def _safe(value: Any) -> Any:
        """Neutralize spreadsheet formulas while preserving numeric values."""
        if value is None or isinstance(value, (int, float)):  # Numbers and missing values need no text prefix.
            return value  # Keep metrics numeric and unavailable cells blank.
        text = str(value)  # Convert Mist text to one CSV cell.
        if text.lstrip(" \t\r\n").startswith(("=", "+", "-", "@")):
            return "'" + text  # Stop common spreadsheet formula prefixes.
        return text  # csv.writer still quotes delimiters and newlines.


class WanDashboardService:
    """Serve the read-only organization WAN dashboard from Mist SDK data."""

    PAGE_LIMIT = 1000
    SITE_TTL = 300
    ENTITY_TTL = 600
    STALE_TTL = 86400
    CACHE_PREFIX = "wan-dashboard:v1:"

    def __init__(self, session: Any, org_id: str, cache: RedisDashboardCache | Any | None = None) -> None:
        """Bind the shared Mist session and the shared cache adapter."""
        self._session = session  # Never construct a second Mist authentication session.
        self._org_id = org_id  # Keep every SDK request inside the portal's active organization.
        self._cache = cache if cache is not None else RedisDashboardCache(None)  # No local Redis service is started.
        self._runner = MistSessionRunner(session, org_id, self._cache)  # Enforce per-token cooldown policy.
        self._last_success: dict[str, Any] = {}  # Keep a bounded per-worker stale result as a Redis fallback.
        self._last_success_at: dict[str, datetime] = {}  # Bound memory snapshots by their successful collection time.
        self._stale_guard = threading.Lock()  # Protect last-success data across Flask request threads.

    def get_sites(self) -> dict[str, Any]:
        """Return every authorized organization site, using the five-minute cache."""
        key = self.CACHE_PREFIX + "sites:" + self._org_id  # Scope cached sites to this feature and organization.
        cached = self._cache.get(key)  # Reuse only a fresh shared-cache value.
        if isinstance(cached, list):  # Redis adapter returns decoded JSON rows.
            return self._result("ok", cached)  # A cache hit is an explicit successful result.
        rows, failure = self._read_all(
            mistapi.api.v1.orgs.sites.listOrgSites,
            self._org_id,
            limit=self.PAGE_LIMIT,
        )  # Read all SDK pages before reporting success.
        return self._finish_read(key, rows, failure, self.SITE_TTL)  # Cache only complete valid data.

    def get_overview(
        self, site_id: str | None = None, gateway_id: str | None = None, search: str | None = None
    ) -> dict[str, Any]:
        """Return filtered gateway rows from the complete organization result."""
        sites = self.get_sites()  # Resolve site names from the same authorized organization.
        if sites["status"] != "ok":  # Do not hide a site-list error behind an empty table.
            return sites  # Preserve the explicit stale, rate-limit, or failure result.
        gateways, gateway_error = self._read_all(
            mistapi.api.v1.orgs.stats.listOrgDevicesStats,
            self._org_id,
            type="gateway",
            limit=self.PAGE_LIMIT,
        )  # Use the supported organization statistics endpoint.
        if gateway_error:  # A failed page cannot produce a partial gateway table.
            return self._stale_result(self.CACHE_PREFIX + "overview:" + self._org_id, gateway_error)
        ports, port_error = self._read_all(
            mistapi.api.v1.orgs.stats.searchOrgSwOrGwPorts, self._org_id, limit=self.PAGE_LIMIT
        )  # Read every switch and gateway port page before filtering to WAN rows.
        if port_error:  # The overview needs port totals, so report the data failure.
            return self._stale_result(self.CACHE_PREFIX + "overview:" + self._org_id, port_error)
        inventory, inventory_error = self._read_all(
            mistapi.api.v1.orgs.inventory.getOrgInventory,
            self._org_id,
            type="gateway",
            limit=self.PAGE_LIMIT,
        )  # Read gateway profile and template references through Mist SDK.
        if inventory_error:  # Profile IDs and access scope require the inventory result.
            return self._stale_result(self.CACHE_PREFIX + "overview:" + self._org_id, inventory_error)
        result = self._overview_rows(gateways, ports, inventory, sites["data"], site_id, gateway_id, search)
        key = self.CACHE_PREFIX + "overview:" + self._org_id  # Keep the last full successful table.
        self._cache.set(key + ":last-success", result, self.STALE_TTL)  # Share stale rows across portal workers.
        self._remember(key, result)  # Retain a complete result for explicit stale-data responses.
        return self._result("ok" if result else "empty", result)  # Distinguish a valid empty organization.

    def collect_worker_snapshot(
        self,
        progress: Callable[[str, int], None],
        lease_is_valid: Callable[[], bool],
    ) -> tuple[dict[str, Any] | None, str | None]:
        """Read the four approved bulk datasets before shaping one complete snapshot."""
        reads = (
            ("sites", mistapi.api.v1.orgs.sites.listOrgSites, (self._org_id,), {"limit": self.PAGE_LIMIT}),
            (
                "gateways",
                mistapi.api.v1.orgs.stats.listOrgDevicesStats,
                (self._org_id,),
                {"type": "gateway", "limit": self.PAGE_LIMIT},
            ),
            (
                "ports",
                mistapi.api.v1.orgs.stats.searchOrgSwOrGwPorts,
                (self._org_id,),
                {"limit": self.PAGE_LIMIT},
            ),
            (
                "inventory",
                mistapi.api.v1.orgs.inventory.getOrgInventory,
                (self._org_id,),
                {"type": "gateway", "limit": self.PAGE_LIMIT},
            ),
        )  # Keep the worker collection boundary explicit and bulk-only.
        datasets: dict[str, list[dict[str, Any]]] = {}  # Hold results until every API page succeeds.
        for phase, function, args, kwargs in reads:  # Use the existing SDK pagination path for each bulk read.
            progress(phase, 0)  # Report the active phase before its first admitted request.

            def report_page(count: int, current_phase: str = phase) -> None:
                """Report completed pages under the active bulk-read phase."""
                progress(current_phase, count)  # Keep the worker status phase explicit.

            rows, failure = self._read_all(
                function,
                *args,
                on_page=report_page,
                before_page=lease_is_valid,
                **kwargs,
            )  # Keep pagination, request admission, and page validation in the shared service.
            if failure:  # One failed dataset invalidates the full snapshot.
                return None, failure  # Never return or publish data from earlier pages.
            datasets[phase] = rows  # Retain this complete dataset until all four reads pass.
        overview = self._overview_rows(
            datasets["gateways"], datasets["ports"], datasets["inventory"], datasets["sites"], None, None, None
        )  # Shape one organization-wide view only after complete collection.
        snapshot = {
            "schema_version": 1,
            "org_id": self._org_id,
            "data_source": "live",  # Mark SDK collection so a synthetic example cannot appear as live data.
            "collected_at": datetime.now(UTC).isoformat(),
            "data": overview,
        }  # Keep collection metadata beside the complete, atomic dashboard value.
        return snapshot, None  # The worker publishes only after it confirms its lease.

    def remember_worker_snapshot(self, snapshot: dict[str, Any]) -> None:
        """Keep the worker's complete snapshot in process memory for Redis outages."""
        key = self.CACHE_PREFIX + "overview:" + self._org_id  # Reuse the canonical overview key.
        self._remember(key, snapshot)  # Bound the local fallback by the existing stale TTL.

    def get_cached_overview(
        self, site_id: str | None = None, gateway_id: str | None = None, search: str | None = None
    ) -> dict[str, Any]:
        """Return an existing complete overview without making a Mist request."""
        key = self.CACHE_PREFIX + "overview:" + self._org_id  # Keep reads under the established organization key.
        logger.info("wan dashboard cached overview read started")  # Record the cache action without operator data.
        result = self._cached_result(key)  # Read only the existing snapshot and local stale fallback.
        if result["status"] not in {"ok", "stale", "empty"}:  # Missing or malformed data stays unavailable.
            return result  # Do not collect data from a dashboard request.
        rows, collected_at = self._cached_snapshot_rows(result["data"])  # Accept the current snapshot and legacy rows.
        if rows is None:  # Reject malformed envelopes and malformed records as one unavailable snapshot.
            return self._result("unavailable", [], "The cached overview is invalid.")  # Reject the entire snapshot.
        rows = self._filter_cached_overview(rows, site_id, gateway_id, search)
        result["data"] = rows  # Apply validated filters only after a complete snapshot is available.
        result["data_source"] = "live"  # Keep legacy live cache rows distinct from the static synthetic example.
        if collected_at is not None:  # Worker snapshots carry a verified UTC collection timestamp.
            result["collected_at"] = collected_at  # Let the page show snapshot age without changing row shape.
        if result["status"] == "ok":  # A legacy cache entry has no trustworthy collection timestamp.
            result["status"] = "stale"  # Never label a timestamp-free snapshot as current.
            result["stale"] = True  # Keep the state explicit for the dashboard.
            result["notice"] = "Showing cached data without a verified collection time."
        logger.debug("wan dashboard cached overview read completed with %s rows", len(rows))  # Report only a count.
        return result  # Return only cached complete rows.

    def get_cached_gateway_ports(self, gateway_id: str) -> dict[str, Any]:
        """Report unavailable detail because the approved bulk snapshot has no port detail cache."""
        return self._cached_detail_unavailable(gateway_id, "gateway ports")  # Do not request a gateway endpoint.

    def get_cached_traffic(self, gateway_id: str, port_id: str, time_range: str) -> dict[str, Any]:
        """Read existing traffic history without making a per-port Mist request."""
        key = self._traffic_key(gateway_id, port_id, time_range)  # Reuse the existing traffic cache key.
        return self._cached_detail(key, "traffic", list)  # Require a list from the existing traffic cache.

    def get_cached_insights(self, gateway_id: str, port_id: str, time_range: str) -> dict[str, Any]:
        """Read existing insight history without making a per-port Mist request."""
        key = self._insight_key(gateway_id, port_id, time_range)  # Reuse the existing insight cache key.
        return self._cached_detail(key, "Insights", dict)  # Require an object from the existing insight cache.

    def get_cached_hourly_export(self, gateway_id: str, port_id: str, time_range: str) -> dict[str, Any]:
        """Return an hourly export only when its existing complete insight cache is available."""
        overview = self.get_cached_overview()  # Resolve gateway labels from the cached organization snapshot.
        if overview["status"] not in {"ok", "stale", "empty"}:  # Do not export missing or malformed overview data.
            return overview  # Preserve the explicit unavailable state.
        gateway = next((row for row in overview["data"] if row.get("device_id") == gateway_id), None)
        if gateway is None:  # Do not expose a gateway outside the cached organization view.
            return self._result("forbidden", {}, "Gateway is not in the active organization.")
        insights = self.get_cached_insights(gateway_id, port_id, time_range)  # Read the existing cache only.
        if insights["status"] not in {"ok", "stale", "empty"}:  # Do not export unavailable insight data.
            return insights  # Preserve the missing data state.
        payload = {  # Keep the existing source-compatible export fields.
            "site_name": gateway.get("site_name", ""),
            "gateway_hostname": gateway.get("name", ""),
            "port_id": port_id,
            "hourly": insights["data"].get("hourly", []),
        }
        return self._result(  # Preserve the cached snapshot's stale state in the export envelope.
            insights["status"], payload, insights.get("notice"), stale=insights["status"] == "stale"
        )

    def export_gateways(
        self, site_id: str | None = None, gateway_id: str | None = None, search: str | None = None
    ) -> dict[str, Any]:
        """Return the same selected overview rows and status used by the browser."""
        return self.get_overview(site_id=site_id, gateway_id=gateway_id, search=search)

    def export_cached_gateways(
        self, site_id: str | None = None, gateway_id: str | None = None, search: str | None = None
    ) -> dict[str, Any]:
        """Return selected overview rows from cache without collecting Mist data."""
        return self.get_cached_overview(site_id=site_id, gateway_id=gateway_id, search=search)

    def get_gateway_ports(self, gateway_id: str) -> dict[str, Any]:
        """Return configuration, counters, and peer paths for one in-scope gateway."""
        gateway, error = self._authorized_gateway(gateway_id)  # Resolve only a valid organization gateway.
        if error is not None:  # Preserve validation, authorization, and Mist failure states.
            return error  # Do not issue site-scoped calls after a failed overview.
        if gateway is None:  # Keep an impossible empty resolution from becoming success-shaped data.
            return self._result("error", [], "Gateway could not be resolved.")
        return self._load_gateway_details(gateway)  # Read configuration and live values for this gateway.

    def _authorized_gateway(self, gateway_id: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """Resolve one validated gateway from the current organization overview."""
        if not WanDataNormalizer.identifier(gateway_id):  # Validate the path before any SDK request.
            return None, self._result("invalid", [], "Gateway identifier is invalid.")
        overview = self.get_overview()  # Resolve the identifier against the active organization.
        if overview["status"] not in {"ok", "empty"}:  # Keep cloud faults and stale states explicit.
            return None, overview  # Do not perform a site-scoped request after an overview failure.
        gateway = next((row for row in overview["data"] if row["device_id"] == gateway_id), None)
        if gateway is None:  # A gateway outside the configured organization is not disclosed.
            return None, self._result("forbidden", [], "Gateway is not in the active organization.")
        return gateway, None  # The gateway belongs to a listed organization site.

    def _load_gateway_details(self, gateway: dict[str, Any]) -> dict[str, Any]:
        """Read all available gateway sources and report partial detail data."""
        site_id = gateway["site_id"]  # Use only the site attached to the authorized overview record.
        device, device_error = self._read_one(
            mistapi.api.v1.sites.devices.getSiteDevice, site_id, gateway["device_id"]
        )  # Read the device configuration through the SDK.
        device = device or {}  # Keep available data even when the device configuration is unavailable.
        profile, template, config_error = self._gateway_configuration(gateway, device)
        stats, stats_error = self._read_one(
            mistapi.api.v1.sites.stats.getSiteDeviceStats, site_id, gateway["device_id"]
        )  # Read current counters and link status for this gateway.
        peers, peer_error = self._read_all(
            mistapi.api.v1.orgs.stats.searchOrgPeerPathStats,
            self._org_id,
            mac=str(gateway.get("mac") or ""),
            site_id=site_id,
            limit=self.PAGE_LIMIT,
        )  # Read VPN peer paths only for the selected site and gateway.
        data = self._gateway_detail(gateway, device, profile, template, stats or {}, peers or [])
        failures = (device_error, config_error, stats_error, peer_error)
        status = "partial" if any(failures) else "ok"
        notice = "Some gateway details are unavailable." if status == "partial" else None
        return self._result(status, data, notice)  # Render available values and the missing-source notice.

    def _gateway_configuration(
        self, gateway: dict[str, Any], device: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any], bool]:
        """Read cached profile and template data for the authorized gateway."""
        profile_id = device.get("deviceprofile_id") or gateway.get("deviceprofile_id")
        profile = self._cached_entity(
            "profiles", profile_id, mistapi.api.v1.orgs.deviceprofiles.getOrgDeviceProfile, self._org_id
        )  # Keep profile records for ten minutes.
        template_id = device.get("gatewaytemplate_id") or gateway.get("gatewaytemplate_id")
        template = self._cached_entity(
            "templates", template_id, mistapi.api.v1.orgs.gatewaytemplates.getOrgGatewayTemplate, self._org_id
        )  # Keep gateway templates for ten minutes.
        missing = bool((profile_id and not profile) or (template_id and not template))
        return profile, template, missing  # Preserve unavailable configuration as an explicit partial state.

    def get_traffic(self, gateway_id: str, port_id: str, time_range: str) -> dict[str, Any]:
        """Return one port's traffic samples for an allow-listed range."""
        gateway, error = self._resolve_gateway(gateway_id, port_id, time_range, WanDataNormalizer.TRAFFIC_SECONDS)
        if error:  # Identifier, range, or organization checks stop the request.
            return error  # Keep the validation or authorization result.
        site_id, duration = gateway["site_id"], WanDataNormalizer.TRAFFIC_SECONDS[time_range]
        end = int(datetime.now(UTC).timestamp())  # Use a UTC epoch as the exclusive range end.
        start = end - duration  # Apply the requested bounded range.
        interval = 600 if time_range == "1h" else 3600  # Keep the source's ten-minute one-hour buckets.
        response, failure = self._request(
            mistapi.api.v1.sites.insights.getSiteInsightMetricsForGateway,
            site_id,
            gateway_id,
            "rx_bps,tx_bps",
            port_id=port_id,
            start=str(start),
            end=str(end),
            interval="10m" if interval == 600 else "1h",
        )  # Request only the two required port metrics.
        if failure:  # A rate limit or failed API read is not an empty chart.
            return self._stale_result(self._traffic_key(gateway_id, port_id, time_range), failure)
        payload = self._payload(response)  # Confirm that the response holds an object.
        if payload is None:  # Malformed success data remains a failure.
            return self._result("error", [], "Mist returned an invalid traffic response.")
        samples = WanDataNormalizer.traffic_samples(payload, start, interval)  # Validate metrics and UTC stamps.
        return self._remember_result(self._traffic_key(gateway_id, port_id, time_range), samples)

    def get_insights(self, gateway_id: str, port_id: str, time_range: str) -> dict[str, Any]:
        """Return bandwidth, link health, and native Application Health SLE data."""
        gateway, error = self._resolve_gateway(gateway_id, port_id, time_range, WanDataNormalizer.INSIGHT_SECONDS)
        if error:  # Validate identifiers and the insight range before cloud access.
            return error  # Preserve the explicit input or authorization result.
        duration = WanDataNormalizer.INSIGHT_SECONDS[time_range]  # Use only a supported bounded period.
        end = int(datetime.now(UTC).timestamp())  # Keep all query times in UTC.
        start = end - duration  # Bound the requested insight window.
        bandwidth, bandwidth_error = self._gateway_insights(gateway, port_id, start, end)
        link, link_error = self._link_insights(gateway, port_id, start, end)
        sle, sle_error = self._sle_insights(gateway["site_id"], start, end)
        failures = [failure for failure in (bandwidth_error, link_error, sle_error) if failure]
        key = self._insight_key(gateway_id, port_id, time_range)
        if failures:  # Keep failed insight sources explicit and prefer a complete prior result.
            failure = "rate_limited" if "rate_limited" in failures else failures[0]
            stale = self._stale_result(key, failure)  # Reuse a complete result when Redis or this worker has one.
            if stale["status"] == "stale" or len(failures) == 3:
                return stale  # Do not replace a complete view with partial or failed data.
        data = self._insight_payload(bandwidth, link, sle, start)  # Keep missing metrics as unavailable.
        if failures:  # Some source values exist but one or more insight sources failed.
            return self._result("partial", data, self._notice(failure))
        return self._remember_result(key, data)

    def get_hourly_export(self, gateway_id: str, port_id: str, time_range: str) -> dict[str, Any]:
        """Return the selected port's hourly metrics and source-compatible labels."""
        overview = self.get_overview()  # Resolve gateway labels within the active organization.
        if overview["status"] not in {"ok", "empty"}:  # Do not export failed overview data.
            return overview  # Preserve the explicit failure state.
        gateway = next((row for row in overview["data"] if row["device_id"] == gateway_id), None)
        if gateway is None:  # Do not export a gateway outside the authorized organization.
            return self._result("forbidden", {}, "Gateway is not in the active organization.")
        insights = self.get_insights(gateway_id, port_id, time_range)  # Reuse the same validated insight read.
        if insights["status"] not in {"ok", "empty"}:  # Never label stale or partial data as a current export.
            return insights  # Keep the failure or stale-data notice.
        payload = {
            "site_name": gateway["site_name"],
            "gateway_hostname": gateway["name"],
            "port_id": port_id,
            "hourly": insights["data"]["hourly"],
        }  # Use the source dashboard's twelve-column export fields.
        return self._result(insights["status"], payload)  # Preserve the successful range result.

    def _read_all(
        self,
        function: Callable[..., Any],
        *args: Any,
        on_page: Callable[[int], None] | None = None,
        before_page: Callable[[], bool] | None = None,
        **kwargs: Any,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Read all SDK pages and reject malformed or failed later pages."""
        if before_page is not None and not before_page():  # A lease loss stops before the next Mist request.
            return [], "worker_lease_lost"  # Never collect without the distributed worker lease.
        response, failure = self._request(function, *args, **kwargs)  # Start with the explicit SDK endpoint.
        if failure:  # Do not call pagination on an invalid first response.
            return [], failure  # The caller receives no partial rows.
        return self._read_pages(response, on_page, before_page)  # Keep pagination checks below the complexity limit.

    def _read_pages(
        self,
        response: Any,
        on_page: Callable[[int], None] | None,
        before_page: Callable[[], bool] | None,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Collect complete SDK pages while the worker keeps its lease."""
        rows: list[dict[str, Any]] = []  # Collect rows only until every page succeeds.
        seen_next_pages: set[str] = set()  # A repeated SDK page link cannot spin or duplicate a dataset.
        while response is not None:  # Continue while the SDK provides a next URL.
            page = WanDataNormalizer.rows(getattr(response, "data", None))  # Validate the response shape.
            if page is None:  # Reject malformed data instead of treating it as no rows.
                return [], "malformed_response"  # Do not return earlier pages as success.
            rows.extend(page)  # Add one validated page.
            if on_page is not None:  # The worker reports only fully validated pages.
                on_page(len(seen_next_pages) + 1)  # Keep progress local to the active bulk read.
            if not getattr(response, "next", None):  # Stop only when the response has no next URL.
                return rows, None  # Return the complete set.
            next_page = str(response.next)  # Keep the page marker only in process memory.
            if next_page in seen_next_pages:  # Reject a repeated URL before it creates an unbounded loop.
                return [], "repeated_page"  # Discard every page from this incomplete dataset.
            seen_next_pages.add(next_page)  # Track the URL without logging or persisting it.
            if before_page is not None and not before_page():  # Renew and verify the lease before pagination.
                return [], "worker_lease_lost"  # Stop before the next SDK request.
            response, failure = self._request(
                mistapi.get_next, response=response, mist_session=self._session
            )  # Each page uses the same one-pass token policy.
            if failure:  # A later error invalidates the whole paginated answer.
                return [], failure  # Never present a partial result as complete.
        return rows, "malformed_response"  # A missing page object is an explicit failure.

    def _cached_snapshot_rows(self, payload: Any) -> tuple[list[dict[str, Any]] | None, str | None]:
        """Validate a worker envelope or the legacy list stored by the original dashboard."""
        collected_at: str | None = None  # Legacy values do not carry a verified collection time.
        rows = payload  # Preserve the original list shape for existing cached snapshots.
        if isinstance(payload, dict):  # Worker snapshots include organization and UTC metadata.
            if any(
                (  # Validate all envelope identity fields in one branch.
                    payload.get("schema_version") != 1,  # Reject unknown schema versions.
                    payload.get("org_id") != self._org_id,  # Reject snapshots from another organization.
                    payload.get("data_source", "live") != "live",  # Reject explicit synthetic or unknown sources.
                )
            ):
                return None, None  # Reject invalid or non-live snapshot envelopes.
            collected_at = payload.get("collected_at")  # Read the worker's collection timestamp.
            rows = payload.get("data")  # Read the complete overview records.
            if not isinstance(collected_at, str) or not self._valid_utc_timestamp(collected_at):
                return None, None  # Do not accept an absent, invalid, or timezone-naive timestamp.
        if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
            return None, None  # Reject malformed rows rather than skipping records silently.
        return rows, collected_at  # Return only complete, validated records.

    @staticmethod
    def _valid_utc_timestamp(value: str) -> bool:
        """Check that the worker timestamp parses and includes a UTC offset."""
        try:  # An invalid timestamp must not make the cached snapshot appear current.
            parsed = datetime.fromisoformat(value)  # Parse the standard ISO 8601 value.
        except ValueError:  # Reject text that is not a timestamp.
            return False  # Keep the cache state unavailable.
        return parsed.tzinfo is not None and parsed.utcoffset() == UTC.utcoffset(parsed)  # Require UTC.

    def _request(self, function: Callable[..., Any], *args: Any, **kwargs: Any) -> tuple[Any | None, str | None]:
        """Run one SDK operation and map its status to a safe internal result."""
        if function is mistapi.get_next:  # The pagination helper takes the session by keyword.
            response, failure = self._runner.call(function, *args, **kwargs)
        else:  # Every endpoint method takes the shared session as its first argument.
            response, failure = self._runner.call(function, self._session, *args, **kwargs)
        if failure == "rate_limited":  # Preserve the rate-limit state for stale-data handling.
            return None, failure  # No SDK response exists when every token is unavailable.
        if failure:  # Transport and HTTP failures have no successful payload.
            logger.warning("wan dashboard Mist operation failed (%s)", failure)  # Operation callers log no token.
            return None, failure  # Keep the body out of the operator response.
        return response, None  # The runner returns only HTTP 200 responses.

    def _read_one(
        self, function: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> tuple[dict[str, Any] | None, str | None]:
        """Read and validate one SDK object response."""
        response, failure = self._request(function, *args, **kwargs)  # Reuse SDK session and cooldown rules.
        if failure:  # Keep the precise internal failure code.
            return None, failure  # Do not fabricate an object.
        payload = self._payload(response)  # Validate object shape before the caller reads fields.
        return (payload, None) if payload is not None else (None, "malformed_response")

    @staticmethod
    def _payload(response: Any) -> dict[str, Any] | None:
        """Return one object payload only when the SDK response has the right shape."""
        payload = getattr(response, "data", None)  # Read only the decoded SDK body.
        return payload if isinstance(payload, dict) else None  # Reject lists and missing bodies.

    def _finish_read(self, key: str, rows: list[dict[str, Any]], failure: str | None, ttl: int) -> dict[str, Any]:
        """Cache a complete page set or return a prior successful result."""
        if failure:  # A failed first or later page must not look like a valid empty list.
            return self._stale_result(key, failure)  # Retain the prior successful result when available.
        self._cache.set(key, rows, ttl)  # Use the caller's bounded freshness period.
        self._cache.set(key + ":last-success", rows, self.STALE_TTL)  # Keep a bounded stale fallback.
        self._remember(key, rows)  # Keep a per-worker fallback when Redis is unavailable.
        return self._result("ok" if rows else "empty", rows)  # Empty HTTP 200 is a valid empty result.

    def _stale_result(self, key: str, failure: str) -> dict[str, Any]:
        """Return a stale successful value with an explicit failure state."""
        cached = self._cache.get(key + ":last-success")  # Prefer the shared prior result across workers.
        if cached is None:  # The cache may be absent or unreachable.
            with self._stale_guard:  # Protect local last-success values across requests.
                cached = self._local_snapshot(key)  # Read only this worker's unexpired saved value.
        if cached is not None:  # A previous complete value remains useful.
            return self._result("stale", cached, self._notice(failure), stale=True)
        status = "rate_limited" if failure == "rate_limited" else "error"  # Keep failure classes distinct.
        return self._result(status, [], self._notice(failure))  # No prior data exists to retain.

    def _cached_entity(
        self, kind: str, identifier: str | None, function: Callable[..., Any], org_id: str
    ) -> dict[str, Any]:
        """Read one profile or gateway template through the ten-minute cache."""
        if not identifier:  # Device profiles and templates are optional.
            return {}  # Missing configuration remains unavailable, not an error.
        key = self.CACHE_PREFIX + kind + ":" + org_id + ":" + identifier  # Scope values by type and organization.
        cached = self._cache.get(key)  # Reuse a complete cached object when available.
        if isinstance(cached, dict):  # Reject unexpected cache shapes.
            return cached  # Return the already-decoded profile or template.
        payload, failure = self._read_one(function, org_id, identifier)  # Use the explicit SDK signature.
        if failure or payload is None:  # Optional configuration must not hide other live details.
            return {}  # The partial result notice describes missing profile data at the route.
        self._cache.set(key, payload, self.ENTITY_TTL)  # Keep profiles and templates for ten minutes.
        return payload  # Return the freshly validated configuration.

    def _overview_rows(
        self,
        gateways: list[dict[str, Any]],
        port_rows: list[dict[str, Any]],
        inventory: list[dict[str, Any]],
        sites: list[dict[str, Any]],
        site_filter: str | None,
        gateway_filter: str | None,
        search: str | None,
    ) -> list[dict[str, Any]]:
        """Join authorized sites, gateways, ports, and inventory into table rows."""
        site_names = self._site_name_map(sites)  # Resolve readable names from validated site identifiers.
        inventory_by_mac = self._inventory_map(inventory)  # Match profile references by valid MAC strings.
        ports_by_mac = self._wan_port_map(port_rows)  # Group only source-declared WAN ports.
        return self._filter_gateways(
            gateways, site_names, inventory_by_mac, ports_by_mac, site_filter, gateway_filter, search
        )  # Apply filters after all source pages have been read.

    @staticmethod
    def _site_name_map(sites: list[dict[str, Any]]) -> dict[str, str]:
        """Map valid site identifiers to readable names."""
        return {
            row["id"]: str(row.get("name") or "Unavailable")
            for row in sites
            if isinstance(row.get("id"), str) and WanDataNormalizer.identifier(row["id"])
        }  # Ignore malformed site identifiers before dictionary construction.

    @staticmethod
    def _inventory_map(inventory: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Map valid inventory MAC addresses to profile references."""
        return {
            row["mac"]: row for row in inventory if isinstance(row.get("mac"), str) and row["mac"]
        }  # Ignore malformed MAC values before dictionary construction.

    @staticmethod
    def _wan_port_map(port_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        """Group organization port rows that Mist marks as WAN ports."""
        ports_by_mac: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for port in port_rows:
            if port.get("port_usage") == "wan" and isinstance(port.get("mac"), str) and port["mac"]:
                ports_by_mac[port["mac"]].append(port)  # Keep each WAN port under its gateway MAC.
        return ports_by_mac  # The join uses a validated string key.

    def _filter_gateways(
        self,
        gateways: list[dict[str, Any]],
        site_names: dict[Any, Any],
        inventory: dict[Any, Any],
        ports: dict[str, list[dict[str, Any]]],
        site_filter: str | None,
        gateway_filter: str | None,
        search: str | None,
    ) -> list[dict[str, Any]]:
        """Build and filter safe gateway summary records."""
        query = (search or "").casefold()  # Normalize once for case-insensitive search.
        rows: list[dict[str, Any]] = []  # Keep only gateways with a stable device id.
        for gateway in gateways:  # Build one summary per complete gateway source row.
            record = self._gateway_row(gateway, site_names, inventory, ports)
            if record is not None and self._matches_gateway(record, site_filter, gateway_filter, query):
                rows.append(record)  # Keep only records that are authorized and match every filter.
        return sorted(rows, key=lambda row: (row["site_name"].casefold(), row["name"].casefold()))

    @staticmethod
    def _gateway_row(
        gateway: dict[str, Any],
        site_names: dict[str, str],
        inventory: dict[Any, Any],
        ports: dict[str, list[dict[str, Any]]],
    ) -> dict[str, Any] | None:
        """Build one gateway row only when both device and site IDs are valid."""
        identity = WanDashboardService._gateway_identity(gateway, site_names)
        if identity is None:  # Reject malformed and out-of-scope gateway records.
            return None  # Do not disclose a gateway without a valid organization site.
        mac = identity["mac"]  # Reuse the normalized gateway address for both joins.
        inventory_record = inventory.get(mac, {}) if mac else {}
        source_ports = ports.get(mac, []) if mac else []
        return {
            **identity,
            "uptime": WanDataNormalizer.numeric(gateway.get("uptime")),
            "wan_port_count": len(source_ports),
            "ports": source_ports,
            "deviceprofile_id": inventory_record.get("deviceprofile_id"),
            "gatewaytemplate_id": inventory_record.get("gatewaytemplate_id"),
        }  # Keep untrusted Mist text as data for safe DOM text nodes.

    @staticmethod
    def _gateway_identity(gateway: dict[str, Any], site_names: dict[str, str]) -> dict[str, Any] | None:
        """Validate organization scope and normalize gateway labels."""
        device_id, site_id = gateway.get("id"), gateway.get("site_id")
        if not isinstance(device_id, str) or not WanDataNormalizer.identifier(device_id):
            return None  # Do not use a malformed gateway identifier.
        if not isinstance(site_id, str) or site_id not in site_names:
            return None  # Do not disclose or link a malformed or out-of-scope gateway.
        return {
            "device_id": device_id,
            "site_id": site_id,
            "site_name": site_names[site_id],
            **WanDashboardService._gateway_labels(gateway),
        }  # Keep display values as strings for safe DOM text nodes.

    @staticmethod
    def _gateway_labels(gateway: dict[str, Any]) -> dict[str, str]:
        """Convert untrusted gateway labels to explicit display strings."""
        return {
            "name": str(gateway.get("name") or gateway.get("hostname") or "Unknown gateway"),
            "model": str(gateway.get("model") or ""),
            "status": str(gateway.get("status") or "unknown"),
            "version": str(gateway.get("version") or ""),
            "ip": str(gateway.get("ip") or ""),
            "mac": str(gateway.get("mac") or ""),
        }  # Keep untrusted values as data for safe DOM text nodes.

    @staticmethod
    def _matches_gateway(
        gateway: dict[str, Any],
        site_filter: str | None,
        gateway_filter: str | None,
        query: str,
    ) -> bool:
        """Check site, exact-device, and free-text overview filters."""
        if site_filter and gateway["site_id"] != site_filter:
            return False  # Exclude a gateway from another selected site.
        if gateway_filter and gateway["device_id"] != gateway_filter:
            return False  # Exclude a gateway that does not match the exact identifier.
        searchable = " ".join((gateway["name"], gateway["model"], gateway["site_name"])).casefold()
        return not query or query in searchable  # Search the complete paginated gateway set.

    def _gateway_detail(
        self,
        gateway: dict[str, Any],
        device: dict[str, Any],
        profile: dict[str, Any],
        template: dict[str, Any],
        stats: dict[str, Any],
        peers: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Merge gateway port configuration, counters, and peer-path rows."""
        port_stats = stats.get("port_stat") or stats.get("if_stat") or {}  # Use the SDK's live port map.
        configured = {**template, **profile, **device}  # Device configuration takes precedence.
        ports = WanDataNormalizer.port_rows(gateway.get("ports", []), configured, port_stats)
        peers_by_port: dict[str, list[dict[str, Any]]] = defaultdict(list)  # Group paths by their WAN port.
        for peer in peers:  # Keep each validated object under its source port.
            port_id = str(peer.get("port_id") or "")  # The SDK provides the owner port identifier.
            if port_id:  # Ignore a path that has no owning port.
                peers_by_port[port_id].append(peer)  # Keep peer metrics for the selected gateway.
        return {
            "gateway": gateway,
            "ports": ports,
            "peers_by_port": dict(peers_by_port),
            "timestamp": stats.get("last_seen"),
        }  # Keep the portal page independent of the source API envelope.

    def _resolve_gateway(
        self, gateway_id: str, port_id: str, time_range: str, ranges: dict[str, int]
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        """Validate range and identifiers, then resolve the gateway in the active organization."""
        error = self._gateway_request_error(gateway_id, port_id, time_range, ranges)
        if error is not None:  # Stop before requesting organization data for invalid input.
            return {}, error  # Preserve the input error response.
        gateway, error = self._authorized_gateway(gateway_id)  # Resolve the active organization gateway.
        if error is not None:  # Do not query a site when authorization or the overview failed.
            return {}, error  # Preserve the input, access, or cloud state.
        if gateway is None:  # Do not accept an empty result without its required error state.
            return {}, self._result("error", [], "Gateway could not be resolved.")
        gateway_ports = gateway.get("ports")
        gateway_ports = gateway_ports if isinstance(gateway_ports, list) else []
        allowed_ports = {
            str(port.get("port_id") or port.get("name") or "") for port in gateway_ports if isinstance(port, dict)
        }  # Keep later site calls within the selected gateway's known WAN ports.
        if port_id not in allowed_ports:  # Do not allow a caller to query another port by guessing its name.
            return {}, self._result("forbidden", [], "Port is not in the active gateway.")
        return gateway, None  # A matching gateway is safe for a site-scoped request.

    def _gateway_request_error(
        self, gateway_id: str, port_id: str, time_range: str, ranges: dict[str, int]
    ) -> dict[str, Any] | None:
        """Validate the route identifiers and range before organization access."""
        if not WanDataNormalizer.identifier(gateway_id) or not WanDataNormalizer.identifier(port_id, port=True):
            return self._result("invalid", [], "Gateway or port identifier is invalid.")
        if port_id in {".", ".."} or "/" in gateway_id:
            return self._result("invalid", [], "Gateway or port identifier is invalid.")
        if time_range not in ranges:
            return self._result("invalid", [], "Time range is invalid.")
        return None  # All route values match their supported boundaries.

    def _gateway_insights(
        self, gateway: dict[str, Any], port_id: str, start: int, end: int
    ) -> tuple[dict[str, Any], str | None]:
        """Read average and peak bandwidth through the gateway Insights SDK method."""
        response, failure = self._request(
            mistapi.api.v1.sites.insights.getSiteInsightMetricsForGateway,
            gateway["site_id"],
            gateway["device_id"],
            "rx_bps,tx_bps,max_rx_bps,max_tx_bps",
            port_id=port_id,
            start=str(start),
            end=str(end),
            interval="1h",
        )  # Match the source's gateway metric request.
        payload = self._payload(response) if response is not None else None  # Validate the optional payload.
        return (payload or {}, failure or ("malformed_response" if payload is None else None))

    def _link_insights(
        self, gateway: dict[str, Any], port_id: str, start: int, end: int
    ) -> tuple[dict[str, Any], str | None]:
        """Read link health through the device-scoped Insights SDK method."""
        mac = gateway["mac"].replace("-", "")[-12:]  # Mist expects the device MAC in this metric path.
        payload, failure = self._read_one(
            mistapi.api.v1.sites.insights.getSiteInsightMetricsForDevice,
            gateway["site_id"],
            "wan_link_health",
            mac,
            port_id=port_id,
            start=str(start),
            end=str(end),
            interval="1h",
        )  # Preserve the source's device-scoped link-health request.
        return payload or {}, failure

    def _sle_insights(self, site_id: str, start: int, end: int) -> tuple[dict[str, Any], str | None]:
        """Read Application Health trend, impacted interfaces, and threshold."""
        summary, summary_error = self._read_one(
            mistapi.api.v1.sites.sle.getSiteSleSummaryTrend,
            site_id,
            "site",
            site_id,
            "application-health",
            start=str(start),
            end=str(end),
        )  # The supported summary-trend call provides score and time buckets.
        impacted, impacted_error = self._read_all(
            mistapi.api.v1.sites.sle.listSiteSleImpactedInterfaces,
            site_id,
            "site",
            site_id,
            "application-health",
            start=str(start),
            end=str(end),
        )  # Read impacted interfaces using the documented SLE call.
        threshold, threshold_error = self._read_one(
            mistapi.api.v1.sites.sle.getSiteSleThreshold,
            site_id,
            "site",
            site_id,
            "application-health",
        )  # Read the site threshold without a time range.
        error = summary_error or impacted_error or threshold_error  # Preserve any failed SLE source.
        return {"summary": summary or {}, "impacted": impacted or [], "threshold": threshold or {}}, error

    def _insight_payload(
        self, bandwidth: dict[str, Any], link: dict[str, Any], sle: dict[str, Any], start: int
    ) -> dict[str, Any]:
        """Combine validated insight sources into the browser response."""
        hourly = WanDataNormalizer.hourly_rows({"bandwidth": bandwidth, "link_health": link}, start)
        return {"hourly": hourly, "application_health": self._application_health(sle)}

    @staticmethod
    def _application_health(sle: dict[str, Any], start: int = 0) -> dict[str, Any]:
        """Shape Application Health samples, threshold, and impacted interfaces."""
        samples, threshold, impacted = WanDashboardService._sle_sections(sle)
        totals = WanDataNormalizer._series(samples, "total")
        degraded = WanDataNormalizer._series(samples, "degraded")
        total = sum(value for item in totals if (value := WanDataNormalizer.numeric(item)) is not None)
        degraded_total = sum(value for item in degraded if (value := WanDataNormalizer.numeric(item)) is not None)
        app_health = round(max(0.0, min(100.0, 100 * (total - degraded_total) / total)), 2) if total else None
        return {
            "summary_pct": app_health,
            "threshold_pct": WanDataNormalizer.numeric(threshold.get("threshold")),
            "trend": WanDashboardService._application_health_trend(sle, samples, totals, degraded, start),
            "impacted_interfaces": impacted,
        }  # Missing source values remain null or an empty list with a partial status.

    @staticmethod
    def _application_health_trend(
        sle: dict[str, Any], samples: dict[str, Any], totals: list[Any], degraded: list[Any], start: int
    ) -> list[dict[str, Any]]:
        """Build the source-compatible hourly score and UTC timestamp for each SLE bucket."""
        summary = sle.get("summary")  # Read the outer SLE response metadata.
        summary = summary if isinstance(summary, dict) else {}  # Reject malformed outer metadata.
        sle_block = summary.get("sle", {})  # Read the nested response metadata.
        sle_block = sle_block if isinstance(sle_block, dict) else {}  # Reject malformed SLE metadata.
        first, step = WanDashboardService._sle_time_window(sle, summary, sle_block, start)
        count = max(len(totals), len(degraded), len(WanDataNormalizer._series(samples, "value")))
        trend = []  # Keep only buckets that have a measured denominator.
        for index in range(count):
            total = WanDataNormalizer.numeric(totals[index]) if index < len(totals) else None
            loss = WanDataNormalizer.numeric(degraded[index]) if index < len(degraded) else None
            sample = WanDashboardService._application_health_sample(total, loss, int(first + index * step))
            if sample is not None:
                trend.append(sample)
        return trend

    @staticmethod
    def _sle_time_window(
        sle: dict[str, Any], summary: dict[str, Any], sle_block: dict[str, Any], start: int
    ) -> tuple[float, float]:
        """Return a validated SLE bucket start and interval in seconds."""
        interval = WanDataNormalizer.numeric(sle.get("interval"))
        interval = interval or WanDataNormalizer.numeric(summary.get("interval"))
        first = WanDataNormalizer.numeric(sle.get("start"))
        first = first or WanDataNormalizer.numeric(summary.get("start"))
        first = first or WanDataNormalizer.numeric(sle_block.get("start"))
        return first or float(start), interval or 3600.0

    @staticmethod
    def _application_health_sample(
        total: float | None, degraded: float | None, timestamp: int
    ) -> dict[str, Any] | None:
        """Return one valid application health score or skip an empty bucket."""
        if total is None or total == 0:
            return None
        degraded_count = degraded or 0
        score = max(0.0, min(100.0, 100 * (total - degraded_count) / total))
        return {"timestamp": timestamp, "pct": round(score, 2)}

    @staticmethod
    def _sle_sections(sle: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], list[Any]]:
        """Validate nested SLE samples, threshold, and interface records."""
        summary = sle.get("summary")  # Read only the documented SLE summary object.
        summary = summary if isinstance(summary, dict) else {}  # Reject malformed summary data.
        sle_block = summary.get("sle")  # Read the nested SLE section.
        sle_block = sle_block if isinstance(sle_block, dict) else {}  # Reject malformed SLE data.
        samples = sle_block.get("samples")  # Read one validated sample container.
        samples = samples if isinstance(samples, dict) else {}  # Do not trust nested SDK payload shapes.
        threshold = sle.get("threshold")  # Read the optional site threshold.
        threshold = threshold if isinstance(threshold, dict) else {}  # Reject malformed threshold data.
        raw_impacted = sle.get("impacted")  # Read optional impacted-interface records.
        impacted = raw_impacted if isinstance(raw_impacted, list) else []  # Reject malformed interface data.
        return samples, threshold, impacted  # Return only validated nested collections.

    def _remember_result(self, key: str, data: Any, status: str = "ok", notice: str | None = None) -> dict[str, Any]:
        """Keep a successful view for a later explicit stale response."""
        result = self._result(status, data, notice)  # Build the response before saving it.
        if status in {"ok", "empty"}:  # A partial result cannot replace a complete prior value.
            self._cache.set(key + ":last-success", data, self.STALE_TTL)  # Share stale data across workers.
            self._remember(key, data)  # Keep a local copy if Redis is unavailable.
        return result  # Return the same envelope that the browser receives.

    def _remember(self, key: str, value: Any) -> None:
        """Save a deep copy of one complete result for this worker."""
        with self._stale_guard:  # Prevent one request from exposing a changing payload.
            self._last_success[key] = copy.deepcopy(value)  # Store data without a secret or API response object.
            self._last_success_at[key] = datetime.now(UTC)  # Enforce the stale age limit for process memory.

    def _local_snapshot(self, key: str) -> Any | None:
        """Return a process-local snapshot only while its collection age remains valid."""
        collected_at = self._last_success_at.get(key)  # Read the matching collection timestamp under the lock.
        if collected_at is None or (datetime.now(UTC) - collected_at).total_seconds() > self.STALE_TTL:
            self._last_success.pop(key, None)  # Remove an expired value so later reads cannot revive it.
            self._last_success_at.pop(key, None)  # Remove the expired timestamp with its data.
            return None  # Report unavailable after the fixed maximum snapshot age.
        return copy.deepcopy(self._last_success.get(key))  # Return an isolated copy of the complete snapshot.

    def _cached_result(self, key: str) -> dict[str, Any]:
        """Return only a valid cached list or object, with stale state for legacy entries."""
        logger.info("wan dashboard cached value read started")  # Record each data access without key values.
        cached = self._cache.get(key + ":last-success")  # Use the existing complete-snapshot key.
        if cached is None:  # Redis may be absent or may not hold this record.
            with self._stale_guard:  # Protect process-local snapshots during concurrent requests.
                cached = self._local_snapshot(key)  # Use only an unexpired complete value from this process.
        if isinstance(cached, (list, dict)):  # Reject scalars and malformed cache values.
            result = self._result("stale", cached, "Showing the last complete cached data.", stale=True)
        else:  # A scalar or missing value cannot represent a complete snapshot.
            result = self._result("unavailable", [], "No complete cached snapshot is available.")
        logger.debug("wan dashboard cached value read completed with %s", result["status"])  # Report only state.
        return result  # Keep the cache result explicit for every route.

    def _cached_detail(self, key: str, label: str, expected_type: type[Any]) -> dict[str, Any]:
        """Return cached detail when present or a safe unavailable response."""
        result = self._cached_result(key)  # Read the existing cache without invoking the Mist SDK.
        if result["status"] != "unavailable" and isinstance(result["data"], expected_type):
            return result  # Do not replace available history with a new request.
        if result["status"] != "unavailable":  # Reject cached data that cannot form a complete detail view.
            return self._result("unavailable", [], label + " cache data is invalid.")
        return self._result("unavailable", [], label + " data is not in the cached snapshot.")

    def _cached_detail_unavailable(self, gateway_id: str, label: str) -> dict[str, Any]:
        """Report bulk-snapshot detail as unavailable without issuing a device request."""
        if not WanDataNormalizer.identifier(gateway_id):  # Retain identifier validation at the service boundary.
            return self._result("invalid", [], "Gateway identifier is invalid.")
        return self._result("unavailable", [], label + " data is not in the cached snapshot.")

    @classmethod
    def _filter_cached_overview(
        cls, rows: Any, site_id: str | None, gateway_id: str | None, search: str | None
    ) -> list[dict[str, Any]]:
        """Filter validated cached overview rows without changing their organization scope."""
        if not isinstance(rows, list):  # Reject malformed complete-snapshot shapes.
            return []  # The caller reports unavailable data for malformed cache values.
        valid_rows = [row for row in rows if isinstance(row, dict)]  # Ignore malformed records without exposing them.
        return [row for row in valid_rows if cls._cached_overview_matches(row, site_id, gateway_id, search)]

    @staticmethod
    def _cached_overview_matches(
        row: dict[str, Any], site_id: str | None, gateway_id: str | None, search: str | None
    ) -> bool:
        """Match one cached row against the optional site, gateway, and text filters."""
        matches_site = site_id is None or row.get("site_id") == site_id  # Keep optional site selection exact.
        matches_gateway = gateway_id is None or row.get("device_id") == gateway_id  # Keep gateway selection exact.
        if not matches_site or not matches_gateway:  # Stop before building search text for unrelated rows.
            return False  # Exclude rows that fail an exact identity filter.
        if search is None:  # An absent search term matches every row with valid identities.
            return True  # Preserve the row without a text filter.
        searchable = " ".join(str(row.get(field, "")) for field in ("name", "model", "site_name"))
        return search.casefold() in searchable.casefold()  # Match the operator term without case sensitivity.

    def _traffic_key(self, gateway_id: str, port_id: str, time_range: str) -> str:
        """Return a namespaced stale-data key for one traffic view."""
        return f"{self.CACHE_PREFIX}traffic:{self._org_id}:{gateway_id}:{port_id}:{time_range}"

    def _insight_key(self, gateway_id: str, port_id: str, time_range: str) -> str:
        """Return a namespaced stale-data key for one insight view."""
        return f"{self.CACHE_PREFIX}insights:{self._org_id}:{gateway_id}:{port_id}:{time_range}"

    @staticmethod
    def _notice(failure: str) -> str:
        """Return a safe operator message without SDK bodies or credentials."""
        if failure == "rate_limited":  # The operator can retry after the token cooldown.
            return "Mist rate limit reached. Showing the last successful data when available."
        if failure.startswith("http_"):  # Show status only, never the Mist error body.
            return "Mist returned " + failure.replace("_", " ") + ". Showing the last successful data when available."
        return "Mist data is unavailable (" + failure + "). Showing the last successful data when available."

    @staticmethod
    def _result(status: str, data: Any, notice: str | None = None, *, stale: bool = False) -> dict[str, Any]:
        """Build the common response envelope for routes and browser code."""
        return {"status": status, "data": data, "notice": notice, "stale": stale}
