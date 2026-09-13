"""Reads Mist Cloud once and turns the answer into metric samples.

Why:
    The upstream `mist_snmp_gateway` reads one site at a time. It calls
    `getSiteStats` for each site, then `listSiteDevicesStats` for each site, and
    it waits 100 milliseconds between two sites so that the Mist rate limit
    holds. A 200 site organization therefore costs 400 calls and at least 20
    seconds of deliberate delay on every refresh.

    Mist publishes the same readings for a whole organization from three
    endpoints. This collector calls `getOrgStats` once, `listOrgSiteStats`
    once, and `listOrgDevicesStats` once. The cost of a refresh no longer grows
    with the site count, so a large organization refreshes as fast as a small
    one.

    Issue #2006 warns that `listSiteDevices` reports the configured firmware
    version and not the running one. This collector reads `listOrgDevicesStats`,
    which is a statistics endpoint and therefore reports the running version.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from src.metrics_gateway.catalog import MetricCatalog, MetricDefinition, MetricKind, MetricScope
from src.metrics_gateway.samples import LabelPairs, MetricSnapshot, SampleBuilder

logger = logging.getLogger(__name__)

ENDPOINT_ORG_STATS = "getOrgStats"  # One record for the organization, including the service level expectations.
ENDPOINT_SITE_STATS = "listOrgSiteStats"  # One record for each site of the organization.
ENDPOINT_DEVICE_STATS = "listOrgDevicesStats"  # One record for each device of the organization.

PAGE_LIMIT = 1000  # The page size the rest of MistHelper uses, set by `DEFAULT_API_PAGE_LIMIT`.
CONNECTED_STATUS = "connected"  # The one `status` value that means the device answers Mist Cloud.
BYTES_PER_KILOBYTE = 1024  # Mist reports device memory in kilobytes, and Prometheus wants bytes.
PERCENT_FULL_SCALE = 100.0  # Mist reports a share as a percent, and a Prometheus ratio runs from 0 to 1.


def _dig(payload: Mapping[str, Any], dotted: str) -> Any:
    """Read a value from a nested mapping through a dotted path.

    Args:
        payload: The Mist record.
        dotted: The path, such as `user_minutes.total`.

    Returns:
        The value, or None when any step of the path is missing.
    """
    current: Any = payload  # Start at the whole record and walk one step at a time.
    for step in dotted.split("."):  # Each step names one key of the next mapping.
        if not isinstance(current, Mapping):  # A non-mapping cannot hold the next key, so the path ends here.
            return None
        current = current.get(step)  # Take the next level, which may itself be None.
    return current


def _as_float(value: Any) -> float | None:
    """Turn a Mist value into a number, or report that it is not one.

    Why:
        Mist omits a field when a device does not report it, and it sends a
        boolean for a few fields. A missing reading must not become 0, because 0
        is a real value that would silence an alarm.

    Args:
        value: The raw value from the Mist record.

    Returns:
        The number, or None when the value is absent or is not a number.
    """
    if isinstance(value, bool):  # A boolean is an int in Python, so it must be tested first.
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):  # A plain number needs no conversion beyond the float cast.
        return float(value)
    return None  # Text, None, and every container are not readings.


def _ratio_from_percent(row: Mapping[str, Any], *paths: str) -> float | None:
    """Turn the first percent that a record holds into a ratio.

    Args:
        row: The Mist record.
        *paths: The dotted paths to try, in order of preference.

    Returns:
        The share from 0 to 1, or None when the record holds no percent.
    """
    for path in paths:  # An access point and a switch report the same fact under different names.
        number = _as_float(_dig(row, path))  # Read one candidate path.
        if number is not None:  # The first path that answers wins, so the order of the paths matters.
            return number / PERCENT_FULL_SCALE
    return None


def _kilobytes_to_bytes(row: Mapping[str, Any], path: str) -> float | None:
    """Turn a kilobyte reading into bytes.

    Args:
        row: The Mist record.
        path: The dotted path of the kilobyte field.

    Returns:
        The byte count, or None when the record holds no such field.
    """
    number = _as_float(_dig(row, path))  # Read the kilobyte field the caller named.
    return None if number is None else number * BYTES_PER_KILOBYTE


# WHY: These readings need arithmetic or a choice between two field names, so a
# dotted source path cannot describe them. The catalog leaves `source` empty for
# each one, and this table supplies the rule instead.
_DEVICE_DERIVED: Mapping[str, Callable[[Mapping[str, Any]], float | None]] = {
    "mist_device_up": lambda row: 1.0 if row.get("status") == CONNECTED_STATUS else 0.0,
    "mist_device_cpu_utilization_ratio": lambda row: _ratio_from_percent(row, "cpu_util", "cpu_stat.util"),
    "mist_device_memory_used_bytes": lambda row: _kilobytes_to_bytes(row, "mem_used_kb"),
    "mist_device_memory_total_bytes": lambda row: _kilobytes_to_bytes(row, "mem_total_kb"),
    "mist_device_cpu_temperature_celsius": lambda row: _as_float(_dig(row, "environment.cpu_temp")),
}


class MistStatsReader:
    """Calls the three Mist endpoints that the gateway reads.

    Why:
        A test must run without a Mist tenant and without a network. The reader
        holds the three endpoint callables in one place, so a test can supply a
        stand-in for any of them. `RunningFirmwareVersionResolver` uses the same
        pattern for the same reason.
    """

    def __init__(self, session: Any, overrides: Mapping[str, Callable[..., Any]] | None = None) -> None:
        """Store the Mist session and any stand-in endpoint the caller supplies.

        Args:
            session: The `mistapi` session, or a stand-in during a test.
            overrides: Endpoint callables by endpoint name. A test passes one
                here so that no call reaches the network.
        """
        self._session = session  # Every endpoint takes the session as its first argument.
        self._overrides = dict(overrides or {})  # A copy keeps a later caller edit out of this reader.

    def _endpoint(self, name: str) -> Callable[..., Any]:
        """Return the callable for one endpoint name.

        Args:
            name: The Mist endpoint name, such as `getOrgStats`.

        Returns:
            The stand-in when the caller supplied one, and the real endpoint otherwise.
        """
        if name in self._overrides:  # A stand-in wins, so a test needs no network.
            return self._overrides[name]
        import mistapi.api.v1.orgs.stats as _org_stats  # A lazy import keeps the module load cheap.

        endpoint: Callable[..., Any] = getattr(_org_stats, name)  # Narrow the untyped module attribute.
        return endpoint

    @staticmethod
    def _payload(response: Any, endpoint: str) -> Any:
        """Return the body of a Mist response, or None when the call failed.

        Args:
            response: The object the endpoint returned.
            endpoint: The endpoint name, used only for the log line.

        Returns:
            The response body, or None.
        """
        status = getattr(response, "status_code", 200)  # A stand-in response may omit the status.
        if status != 200:  # A failed call carries no reading the gateway can serve.
            logger.error("The %s call returned status %s", endpoint, status)  # Record the failure for an operator.
            return None
        return getattr(response, "data", None)  # A good call carries its body in `data`.

    def org_stats(self, org_id: str) -> Mapping[str, Any]:
        """Read the organization statistics.

        Args:
            org_id: The Mist organization identifier.

        Returns:
            The organization record, or an empty mapping when the call failed.
        """
        logger.info("Read the organization statistics for %s", org_id)  # Log before the call.
        payload = self._payload(self._endpoint(ENDPOINT_ORG_STATS)(self._session, org_id), ENDPOINT_ORG_STATS)
        logger.debug("The %s call returned %s", ENDPOINT_ORG_STATS, type(payload).__name__)  # Log the result shape.
        return payload if isinstance(payload, Mapping) else {}

    def _rows(self, endpoint: str, org_id: str, **kwargs: Any) -> list[dict[str, Any]]:
        """Read a list endpoint and keep the records the gateway can read.

        Args:
            endpoint: The Mist endpoint name.
            org_id: The Mist organization identifier.
            **kwargs: The extra query arguments for the endpoint.

        Returns:
            The records, without any entry that is not a mapping.
        """
        logger.info("Read %s for organization %s", endpoint, org_id)  # Log before the call.
        payload = self._payload(self._endpoint(endpoint)(self._session, org_id, limit=PAGE_LIMIT, **kwargs), endpoint)
        rows = [row for row in payload or [] if isinstance(row, dict)]  # Drop any shape the collector cannot read.
        logger.debug("The %s call returned %d records", endpoint, len(rows))  # Log the result count.
        return rows

    def site_stats(self, org_id: str) -> list[dict[str, Any]]:
        """Read the statistics of every site in the organization.

        Args:
            org_id: The Mist organization identifier.

        Returns:
            One record for each site.
        """
        return self._rows(ENDPOINT_SITE_STATS, org_id)

    def device_stats(self, org_id: str) -> list[dict[str, Any]]:
        """Read the statistics of every device in the organization.

        Why:
            The type `all` is needed. Without it Mist returns the access points
            alone, which is the mistake the project instructions record.

        Args:
            org_id: The Mist organization identifier.

        Returns:
            One record for each access point, switch, and gateway.
        """
        return self._rows(ENDPOINT_DEVICE_STATS, org_id, type="all")


class MistMetricsCollector:
    """Turns one pass over Mist Cloud into a frozen set of metric samples."""

    def __init__(self, reader: MistStatsReader, org_id: str, site_ids: Sequence[str] = ()) -> None:
        """Store the reader, the organization, and the optional site filter.

        Args:
            reader: The object that calls the Mist endpoints.
            org_id: The Mist organization identifier.
            site_ids: The sites to report. An empty sequence reports every site.
        """
        self._reader = reader  # The one object that touches the network.
        self._org_id = org_id  # Every endpoint call needs this identifier.
        self._site_ids = frozenset(site_ids)  # A frozen set makes the membership test cheap and stops a later edit.
        self._catalog = MetricCatalog()  # The definitions that both output paths share.

    def collect(self) -> MetricSnapshot:
        """Read Mist Cloud once and return every reading it answered.

        Why:
            A failed call must not raise into the refresh thread, because the
            cache has to keep serving the last good reading. The failure becomes
            a snapshot with `ok` set to False instead.

        Returns:
            The frozen snapshot of this pass.
        """
        started = time.time()  # Record the start so the snapshot can report the pass duration.
        builder = SampleBuilder()  # Collect the samples of this pass in one place.
        logger.info("Start a metrics pass over organization %s", self._org_id)  # Log before the first call.
        try:  # A Mist fault must become a failed snapshot and never an exception in the refresh thread.
            self._collect_all(builder)
        except Exception as failure:  # The cache must survive every fault a Mist call can raise.
            logger.exception("The metrics pass over organization %s failed", self._org_id)  # Record the fault.
            return builder.freeze(time.time(), time.time() - started, ok=False, error=str(failure))
        duration = time.time() - started  # Measure the whole pass, including every page of every endpoint.
        logger.debug("The metrics pass produced %d samples in %.2f seconds", len(builder.samples), duration)
        return builder.freeze(time.time(), duration, ok=True)

    def _collect_all(self, builder: SampleBuilder) -> None:
        """Read the three endpoints and record every reading they answer.

        Args:
            builder: The collector of this pass.
        """
        org = self._reader.org_stats(self._org_id)  # One record for the whole organization.
        self._collect_org(builder, org)
        self._collect_sle(builder, org)
        site_names = self._collect_sites(builder, self._reader.site_stats(self._org_id))
        self._collect_devices(builder, self._reader.device_stats(self._org_id), site_names)

    def _wanted(self, site_id: str) -> bool:
        """Report whether the site filter admits this site.

        Args:
            site_id: The Mist site identifier.

        Returns:
            True when the caller named no filter, or when the filter holds this site.
        """
        return not self._site_ids or site_id in self._site_ids

    def _collect_org(self, builder: SampleBuilder, org: Mapping[str, Any]) -> None:
        """Record the organization scalars.

        Args:
            builder: The collector of this pass.
            org: The record that `getOrgStats` returned.
        """
        labels: LabelPairs = (("org_id", self._org_id), ("org_name", str(org.get("name", ""))))
        # WHY: an organization reading is an SNMP scalar and not a table row, so it carries no
        # row identity. `MetricSnapshot.row_keys` therefore reports no row for this scope.
        for definition in self._catalog.for_scope(MetricScope.ORG):  # Walk the scalars in column order.
            if definition.kind is MetricKind.INFO:  # The informational reading carries its facts in the labels.
                builder.add_info(definition, labels, "", str(org.get("name", "")))
                continue
            number = _as_float(_dig(org, definition.source)) if definition.source else None
            if number is not None:  # A missing reading stays absent, because 0 would silence an alarm.
                builder.add(definition, number, (("org_id", self._org_id),))

    def _collect_sle(self, builder: SampleBuilder, org: Mapping[str, Any]) -> None:
        """Record one row for each service level expectation of the organization.

        Args:
            builder: The collector of this pass.
            org: The record that `getOrgStats` returned.
        """
        entries = org.get("sle") or []  # Mist omits the list when the organization has no wireless service.
        for entry in entries:  # One row for each expectation, such as coverage or capacity.
            if not isinstance(entry, Mapping):  # Drop any shape this collector cannot read.
                continue
            path = str(entry.get("path", ""))  # The `path` field names the expectation.
            if path:  # An unnamed expectation has no stable row identity, so it cannot become a row.
                self._add_sle_row(builder, entry, path)

    def _add_sle_row(self, builder: SampleBuilder, entry: Mapping[str, Any], path: str) -> None:
        """Record the three readings of one service level expectation.

        Args:
            builder: The collector of this pass.
            entry: One element of the `sle` list.
            path: The name of the expectation.
        """
        labels: LabelPairs = (("org_id", self._org_id), ("sle", path))
        total = _as_float(_dig(entry, "user_minutes.total"))  # The denominator of the ratio.
        for definition in self._catalog.for_scope(MetricScope.SLE):  # Walk the three columns in order.
            if definition.source:  # The two measured columns copy a value straight out of the record.
                number = _as_float(_dig(entry, definition.source))
            else:  # The ratio column is derived, so the gateway divides once here for every poller.
                ok_minutes = _as_float(_dig(entry, "user_minutes.ok"))
                number = None if not total or ok_minutes is None else ok_minutes / total
            if number is not None:  # A missing reading stays absent rather than becoming a false 0.
                builder.add(definition, number, labels, path)

    def _collect_sites(self, builder: SampleBuilder, rows: Sequence[Mapping[str, Any]]) -> dict[str, str]:
        """Record one row for each site, and return the site names by identifier.

        Args:
            builder: The collector of this pass.
            rows: The records that `listOrgSiteStats` returned.

        Returns:
            The site name of each reported site, keyed by site identifier.
        """
        names: dict[str, str] = {}  # The device rows need the site name, which the device record omits.
        for row in sorted(rows, key=lambda item: str(item.get("id", ""))):  # A sorted walk fixes the SNMP row order.
            site_id = str(row.get("id", ""))  # The site identifier is the row identity of the site table.
            if not site_id or not self._wanted(site_id):  # Skip an unnamed site and every site the filter excludes.
                continue
            names[site_id] = str(row.get("name", ""))  # Remember the name for the device rows.
            self._add_site_row(builder, row, site_id)
        logger.debug("The metrics pass recorded %d sites", len(names))  # Log the count the filter admitted.
        return names

    def _add_site_row(self, builder: SampleBuilder, row: Mapping[str, Any], site_id: str) -> None:
        """Record every reading of one site.

        Args:
            builder: The collector of this pass.
            row: One record from `listOrgSiteStats`.
            site_id: The site identifier.
        """
        name = str(row.get("name", ""))  # The name a NOC engineer recognizes.
        labels: LabelPairs = (("site_id", site_id), ("site_name", name))
        for definition in self._catalog.for_scope(MetricScope.SITE):  # Walk the columns in order.
            if definition.kind is MetricKind.INFO:  # The informational reading carries the text of the row.
                info_labels = labels + (("country_code", str(row.get("country_code", ""))),)
                builder.add_info(definition, info_labels, site_id, name)
                continue
            number = _as_float(_dig(row, definition.source)) if definition.source else None
            if number is not None:  # A missing count stays absent, because 0 devices reads as an outage.
                builder.add(definition, number, labels, site_id)

    def _collect_devices(
        self, builder: SampleBuilder, rows: Sequence[Mapping[str, Any]], site_names: Mapping[str, str]
    ) -> None:
        """Record one row for each device that the site filter admits.

        Args:
            builder: The collector of this pass.
            rows: The records that `listOrgDevicesStats` returned.
            site_names: The site name of each reported site, keyed by identifier.
        """
        counted = 0  # Count the admitted devices so the log can report the pass size.
        for row in sorted(rows, key=lambda item: str(item.get("mac", ""))):  # A sorted walk fixes the SNMP row order.
            mac = str(row.get("mac", ""))  # The MAC address is the row identity of the device table.
            site_id = str(row.get("site_id", ""))  # The device record names its site by identifier only.
            if not mac or not self._wanted(site_id):  # Skip an unnamed device and every excluded site.
                continue
            self._add_device_row(builder, row, mac, site_names.get(site_id, ""))
            counted += 1
        logger.debug("The metrics pass recorded %d devices", counted)  # Log the count the filter admitted.

    @staticmethod
    def _device_labels(row: Mapping[str, Any], mac: str, site_name: str) -> LabelPairs:
        """Build the labels that identify one device.

        Args:
            row: One record from `listOrgDevicesStats`.
            mac: The device MAC address.
            site_name: The name of the site that holds the device.

        Returns:
            The label pairs, in the order the renderer prints them.
        """
        return (
            ("mac", mac),
            ("device_name", str(row.get("name", ""))),
            ("site_id", str(row.get("site_id", ""))),
            ("site_name", site_name),
            ("device_type", str(row.get("type", ""))),
        )

    def _add_device_row(self, builder: SampleBuilder, row: Mapping[str, Any], mac: str, site_name: str) -> None:
        """Record every reading of one device.

        Args:
            builder: The collector of this pass.
            row: One record from `listOrgDevicesStats`.
            mac: The device MAC address.
            site_name: The name of the site that holds the device.
        """
        labels = self._device_labels(row, mac, site_name)
        for definition in self._catalog.for_scope(MetricScope.DEVICE):  # Walk the columns in order.
            if definition.kind is MetricKind.INFO:  # The informational reading carries the model and the version.
                builder.add_info(definition, labels + self._device_facts(row), mac, str(row.get("name", "")))
                continue
            number = self._device_value(definition, row)
            if number is not None:  # A missing reading stays absent rather than becoming a false 0.
                builder.add(definition, number, labels, mac)

    @staticmethod
    def _device_facts(row: Mapping[str, Any]) -> LabelPairs:
        """Build the extra labels that describe the hardware and the firmware.

        Why:
            `listOrgDevicesStats` is a statistics endpoint, so its `version`
            field reports the running firmware. Issue #2006 records that the
            device listing reports the configured version instead, which can
            name a release the device left long ago.

        Args:
            row: One record from `listOrgDevicesStats`.

        Returns:
            The model, the serial number, and the running firmware version.
        """
        return (
            ("model", str(row.get("model", ""))),
            ("serial", str(row.get("serial", ""))),
            ("version", str(row.get("version", ""))),
        )

    @staticmethod
    def _device_value(definition: MetricDefinition, row: Mapping[str, Any]) -> float | None:
        """Read one device reading, by dotted path or by derivation rule.

        Args:
            definition: The catalog entry for the reading.
            row: One record from `listOrgDevicesStats`.

        Returns:
            The number, or None when the device does not report it.
        """
        if definition.source:  # Most readings copy a field straight out of the record.
            return _as_float(_dig(row, definition.source))
        rule = _DEVICE_DERIVED.get(definition.name)  # The rest need arithmetic or a choice between two field names.
        return rule(row) if rule else None
