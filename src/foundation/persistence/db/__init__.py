"""MistHelper polyglot database package.

Routes API data to ArangoDB (documents), Redis JSON (events),
or Redis TimeSeries (metrics) based on ENDPOINT_PRIMARY_KEY_STRATEGIES
configuration.
"""

from __future__ import annotations

import os
import socket
import time
from dataclasses import dataclass
from urllib.parse import urlparse

import structlog

from src.foundation.persistence.db.support import host_resolver as _host_resolver

ARANGO_DEFAULT_URL = "http://misthelper-arangodb:9529"  # Compose service URL used when ARANGO_HOST is unset.
ARANGO_DEFAULT_HOSTNAME = "misthelper-arangodb"  # Host applied when a URL carries no host of its own.
ARANGO_DEFAULT_PORT = 9529  # Port applied when ARANGO_HOST carries no explicit port.
REDIS_DEFAULT_HOST = "misthelper-redis"  # Compose service name used when REDIS_HOST is unset.
REDIS_DEFAULT_PORT = 9379  # Port applied when REDIS_PORT is unset or unreadable.
PROBE_TIMEOUT_SECONDS = 0.5  # Bound the TCP phase separately from the shared DNS caller budget.
ARANGO_USERNAME_FIELD = "ARANGO_USERNAME"  # Name the ArangoDB account environment variable.
ARANGO_PASSWORD_FIELD = "ARANGO_ROOT_PASSWORD"  # nosec B105  # Name the ArangoDB password variable.
REDIS_PASSWORD_FIELD = "REDIS_PASSWORD"  # nosec B105  # Name the Redis password variable.
WEBHOOK_SECRET_FIELD = "WEBHOOK_SECRET"  # nosec B105  # Name the Mist webhook secret variable.


def configure_db_logging() -> None:
    """Configure structlog for the db package: JSON, ASCII-only, stdlib."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(ensure_ascii=True),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


@dataclass
class DatabaseConfig:
    """Connection settings for polyglot database backends."""

    arango_host: str = "http://misthelper-arangodb:9529"
    arango_database: str = "misthelper"
    arango_username: str = "root"
    arango_password: str = "misthelper"
    redis_host: str = "misthelper-redis"
    redis_port: int = 9379
    redis_password: str = "misthelper"
    standalone_mode: bool = False
    webhook_enabled: bool = True
    webhook_secret: str = ""

    @classmethod
    def from_env(cls) -> DatabaseConfig:
        """Build config from environment variables.

        Both unresolved names select standalone mode. One resolved name keeps
        the existing partial-backend and required-credential behavior.
        Central DNS callers use a one-second budget and a 30-second result cache.
        DNS success does not prove that a database service is ready.
        """
        explicit_standalone = os.environ.get("MISTHELPER_STANDALONE", "").lower() == "true"  # Read CSV-only override.
        arango_host = os.environ.get("ARANGO_HOST", ARANGO_DEFAULT_URL)  # Use the compose host unless overridden.
        redis_host = os.environ.get("REDIS_HOST", REDIS_DEFAULT_HOST)  # Use the compose Redis host unless overridden.
        redis_port = _env_int("REDIS_PORT", REDIS_DEFAULT_PORT)  # Parse the Redis port with the existing guard.
        standalone = explicit_standalone or _hosts_unreachable(
            arango_host, redis_host
        )  # Skip secrets when no DB exists.
        webhook_enabled = os.environ.get("WEBHOOK_ENABLED", "true").lower() == "true"  # Preserve the existing default.
        arango_username = _optional_env(ARANGO_USERNAME_FIELD) if standalone else _required_env(ARANGO_USERNAME_FIELD)
        arango_password = _optional_env(ARANGO_PASSWORD_FIELD) if standalone else _required_env(ARANGO_PASSWORD_FIELD)
        redis_password = _optional_env(REDIS_PASSWORD_FIELD) if standalone else _required_env(REDIS_PASSWORD_FIELD)
        webhook_secret = _optional_env(WEBHOOK_SECRET_FIELD)  # The webhook route rejects an empty secret before use.

        return cls(
            arango_host=arango_host,
            arango_database=os.environ.get("ARANGO_DATABASE", "misthelper"),
            arango_username=arango_username,
            arango_password=arango_password,
            redis_host=redis_host,
            redis_port=redis_port,
            redis_password=redis_password,
            standalone_mode=standalone,
            webhook_enabled=webhook_enabled,
            webhook_secret=webhook_secret,
        )


def _hosts_unreachable(arango_url: str, redis_host: str) -> bool:
    """Return True when both database names lack a recent resolved address.

    Each DNS caller waits at most one second. Positive and negative results
    expire after 30 monotonic seconds. No TCP connection occurs here.
    A timed-out operating system lookup retains its finite worker slot.
    """
    log = structlog.get_logger(__name__)
    arango_hostname = urlparse(arango_url).hostname or ARANGO_DEFAULT_HOSTNAME
    log.info("database_host_discovery_started")
    arango_ok = bool(_host_resolver.DEFAULT_RESOLVER.resolve(arango_hostname).addresses)
    redis_ok = bool(_host_resolver.DEFAULT_RESOLVER.resolve(redis_host).addresses)
    log.debug("database_host_discovery_finished", arango_resolved=arango_ok, redis_resolved=redis_ok)
    if not arango_ok and not redis_ok:
        log.info(
            "standalone_auto_detected",
            msg="Database hosts unreachable, using CSV/SQLite only",
            arango_host=arango_hostname,
            redis_host=redis_host,
            checked_hosts=2,
        )
        return True
    return False


def _required_env(name: str) -> str:
    """Return a required environment value, or raise a field-named error."""
    raw = os.environ.get(name)  # Read without a default so absence stays visible.
    value = str(raw or "").strip()  # Treat whitespace as missing for credential fields.
    if value:  # A non-empty value can authenticate the configured backend.
        return value  # Return only the value, never log it.
    log = structlog.get_logger(__name__)  # Build a package logger for the validation event.
    log.error("missing_required_database_config", field=name)  # Log only the field name.
    raise ValueError(f"Missing required environment variable: {name}")  # Stop before a default credential is used.


def _optional_env(name: str) -> str:
    """Return an optional environment value with whitespace trimmed."""
    raw = os.environ.get(name)  # Read without a default so no placeholder credential appears.
    return str(raw or "").strip()  # Empty means not configured, and no authenticated call uses it.


def _env_int(name: str, default: int) -> int:
    """Return an integer environment variable, or the default when the value is absent or unreadable."""
    raw = os.environ.get(name, "")  # Read the raw value so an empty string keeps the default.
    try:
        return int(raw)  # Convert the operator supplied value.
    except ValueError:
        return default  # An unreadable port must not stop an export.


def _can_connect(hostname: str, port: int) -> bool:
    """Probe resolved numeric addresses within one aggregate TCP budget."""
    log = structlog.get_logger(__name__)
    log.info("database_tcp_probe_started", hostname=hostname, port=port)
    resolved = _host_resolver.DEFAULT_RESOLVER.resolve(hostname)
    deadline = time.monotonic() + PROBE_TIMEOUT_SECONDS
    checked_count = 0
    for family, socket_type, protocol, _canonical_name, address in resolved.addresses:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        endpoint = (address[0], port, address[2], address[3]) if len(address) == 4 else (address[0], port)
        checked_count += 1
        try:
            with socket.socket(family, socket_type, protocol) as connection:
                connection.settimeout(remaining)
                connection.connect(endpoint)
            log.debug("database_tcp_probe_finished", hostname=hostname, reachable=True, checked_addresses=checked_count)
            return True
        except (OSError, OverflowError) as error:
            log.debug("database_tcp_address_failed", hostname=hostname, error_type=type(error).__name__)
    log.debug("database_tcp_probe_finished", hostname=hostname, reachable=False, checked_addresses=checked_count)
    return False


def polyglot_hosts_unreachable() -> bool:
    """Return True when neither ArangoDB nor Redis answers a TCP connect.

    The probe reads the same environment variables as ``DatabaseConfig.from_env``.
    It opens a TCP connection because a hostname can resolve while no service listens.
    DNS uses the shared one-second caller budget and 30-second result cache.
    Each service then has one separate 0.5-second aggregate TCP budget.
    The function does not cache service readiness.
    """
    log = structlog.get_logger(__name__)  # Bind the package logger for the probe record.
    arango_url = os.environ.get("ARANGO_HOST", ARANGO_DEFAULT_URL)  # Read the configured ArangoDB URL.
    redis_host = os.environ.get("REDIS_HOST", REDIS_DEFAULT_HOST)  # Read the configured Redis host.
    parsed = urlparse(arango_url)  # Split the URL so the probe gets a host and a port.
    arango_ok = _can_connect(parsed.hostname or ARANGO_DEFAULT_HOSTNAME, parsed.port or ARANGO_DEFAULT_PORT)
    redis_ok = _can_connect(redis_host, _env_int("REDIS_PORT", REDIS_DEFAULT_PORT))  # Probe Redis.
    log.info(
        "polyglot_host_probe",
        arango_host=parsed.hostname,
        arango_reachable=arango_ok,
        redis_host=redis_host,
        redis_reachable=redis_ok,
        checked_hosts=2,
    )  # Record both verdicts so a dropped write is traceable.
    return not arango_ok and not redis_ok  # Only total silence makes the polyglot backend unusable.


@dataclass
class WriteResult:
    """Outcome of a database write operation."""

    success: bool
    backend: str  # "arangodb", "redis", "redis_json", "dual", "csv_only"
    records_written: int
    records_failed: int
    error_message: str = ""


@dataclass
class DualWriteResult:
    """Captures independent success/failure of both backends for dual-write."""

    arango_result: WriteResult
    redis_result: WriteResult

    @property
    def combined(self) -> WriteResult:
        """Merge both results into a single WriteResult for logging."""
        total_written = self.arango_result.records_written + self.redis_result.records_written
        total_failed = self.arango_result.records_failed + self.redis_result.records_failed
        both_ok = self.arango_result.success and self.redis_result.success
        errors = []
        if self.arango_result.error_message:
            errors.append(f"arango: {self.arango_result.error_message}")
        if self.redis_result.error_message:
            errors.append(f"redis: {self.redis_result.error_message}")
        return WriteResult(
            success=both_ok,
            backend="dual",
            records_written=total_written,
            records_failed=total_failed,
            error_message="; ".join(errors),
        )


__all__ = [
    "DatabaseConfig",
    "DualWriteResult",
    "WriteResult",
    "configure_db_logging",
]
