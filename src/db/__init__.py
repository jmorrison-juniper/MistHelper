"""MistHelper polyglot database package.

Routes API data to ArangoDB (documents), Redis JSON (events),
or Redis TimeSeries (metrics) based on ENDPOINT_PRIMARY_KEY_STRATEGIES
configuration.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import structlog


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


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger for the given module name."""
    return structlog.get_logger(name)


@dataclass
class DatabaseConfig:
    """Connection settings for polyglot database backends."""

    arango_host: str = "http://arangodb:8529"
    arango_database: str = "misthelper"
    arango_username: str = "root"
    arango_password: str = ""
    redis_host: str = "redis-stack"
    redis_port: int = 6379
    redis_password: str = ""
    standalone_mode: bool = False
    webhook_enabled: bool = True
    webhook_secret: str = ""

    @classmethod
    def from_env(cls) -> DatabaseConfig:
        """Build config from environment variables."""
        return cls(
            arango_host=os.environ.get("ARANGO_HOST", "http://arangodb:8529"),
            arango_database=os.environ.get("ARANGO_DATABASE", "misthelper"),
            arango_username=os.environ.get("ARANGO_USERNAME", "root"),
            arango_password=os.environ.get("ARANGO_ROOT_PASSWORD", ""),
            redis_host=os.environ.get("REDIS_HOST", "redis-stack"),
            redis_port=int(os.environ.get("REDIS_PORT", "6379")),
            redis_password=os.environ.get("REDIS_PASSWORD", ""),
            standalone_mode=os.environ.get("MISTHELPER_STANDALONE", "false").lower() == "true",
            webhook_enabled=os.environ.get("WEBHOOK_ENABLED", "true").lower() == "true",
            webhook_secret=os.environ.get("WEBHOOK_SECRET", ""),
        )


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
    "get_logger",
]
