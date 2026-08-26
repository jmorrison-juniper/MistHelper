"""MistHelper polyglot database package.

Routes API data to ArangoDB (documents), Redis JSON (events),
or Redis TimeSeries (metrics) based on ENDPOINT_PRIMARY_KEY_STRATEGIES
configuration.
"""

from __future__ import annotations

import os
import socket
from dataclasses import dataclass
from urllib.parse import urlparse

import structlog

ARANGO_DEFAULT_URL = "http://misthelper-arangodb:9529"  # Compose service URL used when ARANGO_HOST is unset.
ARANGO_DEFAULT_PORT = 9529  # Port applied when ARANGO_HOST carries no explicit port.
REDIS_DEFAULT_HOST = "misthelper-redis"  # Compose service name used when REDIS_HOST is unset.
REDIS_DEFAULT_PORT = 9379  # Port applied when REDIS_PORT is unset or unreadable.
PROBE_TIMEOUT_SECONDS = 0.5  # Short TCP budget so a dead host never stalls an export.


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

        Auto-detects standalone mode when database hosts are unreachable,
        preventing noisy retry loops when running outside a container.
        """
        explicit_standalone = os.environ.get("MISTHELPER_STANDALONE", "").lower() == "true"
        arango_host = os.environ.get("ARANGO_HOST", ARANGO_DEFAULT_URL)
        redis_host = os.environ.get("REDIS_HOST", REDIS_DEFAULT_HOST)
        redis_port = _env_int("REDIS_PORT", REDIS_DEFAULT_PORT)

        standalone = explicit_standalone or _hosts_unreachable(arango_host, redis_host)

        return cls(
            arango_host=arango_host,
            arango_database=os.environ.get("ARANGO_DATABASE", "misthelper"),
            arango_username=os.environ.get("ARANGO_USERNAME", "root"),
            arango_password=os.environ.get("ARANGO_ROOT_PASSWORD", "misthelper"),
            redis_host=redis_host,
            redis_port=redis_port,
            redis_password=os.environ.get("REDIS_PASSWORD", "misthelper"),
            standalone_mode=standalone,
            webhook_enabled=os.environ.get("WEBHOOK_ENABLED", "true").lower() == "true",
            webhook_secret=os.environ.get("WEBHOOK_SECRET", ""),
        )


def _hosts_unreachable(arango_url: str, redis_host: str) -> bool:
    """Return True if both ArangoDB and Redis hostnames fail DNS resolution.

    Uses a fast DNS-only check (no TCP connection) with a short timeout
    so the caller never blocks on retries.
    """
    arango_hostname = urlparse(arango_url).hostname or "arangodb"
    arango_ok = _can_resolve(arango_hostname)
    redis_ok = _can_resolve(redis_host)
    if not arango_ok and not redis_ok:
        log = structlog.get_logger(__name__)
        log.info(
            "standalone_auto_detected",
            msg="Database hosts unreachable, using CSV/SQLite only",
            arango_host=arango_hostname,
            redis_host=redis_host,
        )
        return True
    return False


def _can_resolve(hostname: str) -> bool:
    """Check whether a hostname resolves via DNS (no connection attempt)."""
    try:
        socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        return True
    except socket.gaierror:
        return False


def _env_int(name: str, default: int) -> int:
    """Return an integer environment variable, or the default when the value is absent or unreadable."""
    raw = os.environ.get(name, "")  # Read the raw value so an empty string keeps the default.
    try:
        return int(raw)  # Convert the operator supplied value.
    except ValueError:
        return default  # An unreadable port must not stop an export.


def _can_connect(hostname: str, port: int) -> bool:
    """Return True when a TCP connect to the host and port succeeds inside the probe timeout."""
    try:
        with socket.create_connection((hostname, port), timeout=PROBE_TIMEOUT_SECONDS):  # Open and close one socket.
            return True  # A service listens on that address.
    except OSError:
        return False  # A refused, filtered, or unresolvable address counts as silent.


def polyglot_hosts_unreachable() -> bool:
    """Return True when neither ArangoDB nor Redis answers a TCP connect.

    The probe reads the same environment variables as ``DatabaseConfig.from_env``.
    It opens a TCP connection because a hostname can resolve while no service listens.
    A caller must cache the answer, because each call costs up to two timeouts.
    """
    log = structlog.get_logger(__name__)  # Bind the package logger for the probe record.
    arango_url = os.environ.get("ARANGO_HOST", ARANGO_DEFAULT_URL)  # Read the configured ArangoDB URL.
    redis_host = os.environ.get("REDIS_HOST", REDIS_DEFAULT_HOST)  # Read the configured Redis host.
    parsed = urlparse(arango_url)  # Split the URL so the probe gets a host and a port.
    arango_ok = _can_connect(parsed.hostname or "arangodb", parsed.port or ARANGO_DEFAULT_PORT)  # Probe ArangoDB.
    redis_ok = _can_connect(redis_host, _env_int("REDIS_PORT", REDIS_DEFAULT_PORT))  # Probe Redis.
    log.info(
        "polyglot_host_probe",
        arango_host=parsed.hostname,
        arango_reachable=arango_ok,
        redis_host=redis_host,
        redis_reachable=redis_ok,
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
