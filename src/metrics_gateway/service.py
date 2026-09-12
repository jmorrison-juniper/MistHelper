"""Settings and wiring for the metrics gateway.

Why:
    The gateway has two output paths and one cache. This module builds the
    settings and the cache from the process environment, so a menu entry, a
    command line flag, and a WSGI server all start the same gateway with the
    same settings.

    The Flask layer lives in `web.py` and not here. A `pass_persist` helper
    reads these settings and builds this cache, and it has no use for a web
    framework, so it must not pay to load one.
"""

from __future__ import annotations

import logging
import os
import threading
from dataclasses import dataclass, replace
from typing import Any

from src.metrics_gateway.cache import DEFAULT_REFRESH_SECONDS, MetricsCache
from src.metrics_gateway.collector import MistMetricsCollector, MistStatsReader
from src.metrics_gateway.snmp import DEFAULT_BASE_OID

logger = logging.getLogger(__name__)

PORT_VARIABLE = "METRICS_PORT"  # The listen port of the Prometheus endpoint.
HOST_VARIABLE = "METRICS_HOST"  # The bind address of that endpoint.
REFRESH_VARIABLE = "METRICS_REFRESH_SECONDS"  # The age at which a cached reading becomes stale.
SITE_IDS_VARIABLE = "METRICS_SITE_IDS"  # A comma list of sites. Unset means every site.
BASE_OID_VARIABLE = "METRICS_SNMP_BASE_OID"  # The base OID that `snmpd.conf` names.
ORG_ID_VARIABLES = ("METRICS_ORG_ID", "MIST_ORG_ID")  # The organization to report, in order of preference.

DEFAULT_PORT = 8057  # Port 8055 serves the data browsing portal and port 8056 serves the upgrade capture portal.
DEFAULT_HOST = "127.0.0.1"  # Loopback only, which is the rule the upgrade capture portal already applies.

# WHY: A container reaches its endpoint through a published port, and a bind to
# loopback inside a container answers no client at all. A workstation must never
# take this address, so only `resolve_host` may return it.
ALL_INTERFACES_HOST = "0.0.0.0"  # nosec B104  # Container only, because a published port needs it.


def _read_int(name: str, default: int) -> int:
    """Read a whole number from the environment, or keep the default.

    Why:
        A typo in one setting must not stop an operations tool. The gateway logs
        the fault and keeps the documented default instead.

    Args:
        name: The environment variable name.
        default: The value to use when the variable is unset or unreadable.

    Returns:
        The number.
    """
    raw = (os.environ.get(name) or "").strip()  # An unset value and a blank value mean the same thing.
    if not raw:  # No value was set, so the default applies without a warning.
        return default
    try:  # A wrong value must warn and then fall back, because a stopped gateway raises no alarm at all.
        return int(raw)
    except ValueError:
        logger.warning("The setting %s holds %r, which is not a whole number. Use %d instead.", name, raw, default)
        return default


def resolve_host(requested: str | None, *, in_container: bool) -> str:
    """Choose the address that the Prometheus endpoint binds.

    Why:
        The endpoint asks for no password, because a Prometheus scraper carries
        none. A bind to every address therefore offers the readings to every
        computer that can reach the host, and a workstation on a customer
        network reaches many. Loopback is the safe default for a workstation.

        A container is the opposite case, because it reaches its endpoint
        through a published port and the container boundary already holds that
        port. An operator who names an address always wins, because a reverse
        proxy needs a bind that neither default describes.

    Args:
        requested: The address from `METRICS_HOST`, or None when it is unset.
        in_container: True when the gateway runs inside a container.

    Returns:
        The address that the server binds.
    """
    named = (requested or "").strip()  # An unset value and a blank value are the same.
    if named:  # The operator named an address, so no default applies.
        logger.info("The setting %s names the bind address %s", HOST_VARIABLE, named)
        return named
    if in_container:  # A published port cannot reach a loopback bind.
        return ALL_INTERFACES_HOST
    logger.info("No %s value is set, so the gateway binds loopback only", HOST_VARIABLE)
    return DEFAULT_HOST


@dataclass(frozen=True, slots=True)
class GatewaySettings:
    """Every setting the gateway reads from the environment.

    Attributes:
        org_id: The Mist organization to report.
        host: The bind address of the Prometheus endpoint.
        port: The listen port of that endpoint.
        refresh_seconds: The age at which a cached reading becomes stale.
        site_ids: The sites to report. An empty tuple reports every site.
        base_oid: The base OID that `snmpd.conf` names.
    """

    org_id: str
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    refresh_seconds: float = DEFAULT_REFRESH_SECONDS
    site_ids: tuple[str, ...] = ()
    base_oid: str = DEFAULT_BASE_OID

    @classmethod
    def from_environment(cls, in_container: bool = False) -> GatewaySettings:
        """Build the settings from the process environment.

        Args:
            in_container: True when the gateway runs inside a container.

        Returns:
            The frozen settings record.
        """
        org_id = next((os.environ[name] for name in ORG_ID_VARIABLES if os.environ.get(name)), "")
        raw_sites = (os.environ.get(SITE_IDS_VARIABLE) or "").strip()  # A comma list, or an empty string.
        sites = tuple(part.strip() for part in raw_sites.split(",") if part.strip())  # Drop a blank list entry.
        settings = cls(
            org_id=org_id,
            host=resolve_host(os.environ.get(HOST_VARIABLE), in_container=in_container),
            port=_read_int(PORT_VARIABLE, DEFAULT_PORT),
            refresh_seconds=float(_read_int(REFRESH_VARIABLE, int(DEFAULT_REFRESH_SECONDS))),
            site_ids=sites,
            base_oid=(os.environ.get(BASE_OID_VARIABLE) or DEFAULT_BASE_OID).strip(),
        )
        logger.info(
            "The metrics gateway reports organization %s on %s port %d, refreshing every %.0f seconds",
            settings.org_id or "(unset)",
            settings.host,
            settings.port,
            settings.refresh_seconds,
        )
        return settings

    def with_org_id(self, org_id: str) -> GatewaySettings:
        """Return a copy of these settings that names another organization.

        Why:
            A container reads the organization from the environment and never
            prompts. A menu start has an operator, so it can pick an
            organization after the settings are already built. The record is
            frozen, so the choice arrives as a copy and never as an edit.

        Args:
            org_id: The organization the operator chose.

        Returns:
            The new settings record.
        """
        return replace(self, org_id=org_id)


def build_cache(session: Any, settings: GatewaySettings) -> MetricsCache:
    """Build the cache that both output paths read.

    Args:
        session: The `mistapi` session.
        settings: The settings that name the organization and the interval.

    Returns:
        The cache, which is empty until the first poll or the first refresh.
    """
    logger.info("Build the metrics cache for organization %s", settings.org_id)  # Log before the build.
    reader = MistStatsReader(session)  # The one object that touches the network.
    collector = MistMetricsCollector(reader, settings.org_id, settings.site_ids)
    return MetricsCache(collector, settings.refresh_seconds)


def start_refresh_thread(cache: MetricsCache, stop: threading.Event) -> threading.Thread:
    """Refresh the cache on a timer, so no poll ever waits for Mist Cloud.

    Why:
        A poll refreshes the cache when it finds a stale reading, and that poll
        then waits for the whole Mist pass. A background thread does the work
        ahead of the poll instead, so a Prometheus scrape always answers fast.

    Args:
        cache: The cache to refresh.
        stop: The event that ends the thread.

    Returns:
        The started thread, which is a daemon so it cannot hold the process open.
    """

    def _loop() -> None:
        """Refresh until the caller sets the stop event."""
        while not stop.is_set():  # The event ends the loop at the next wait, or sooner.
            cache.refresh_now()  # The cache never raises, so this loop needs no guard.
            stop.wait(cache.refresh_seconds)  # `wait` returns early when the caller stops the gateway.

    thread = threading.Thread(target=_loop, name="metrics-gateway-refresh", daemon=True)
    logger.info("Start the metrics refresh thread on a %.0f second interval", cache.refresh_seconds)
    thread.start()
    return thread
