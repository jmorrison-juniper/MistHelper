"""Shared test setup for the mist-ops-platform suite.

The package `src.shared.config` is absent from the repository. The root
`.gitignore` holds the pattern `config/`, so git never tracked the directory.
Every clean checkout and every worktree therefore fails to import the worker
modules. This file supplies a minimal stand-in so the suite can run.

The stand-in loads only when the real package is absent. If a developer holds
the real `src.shared.config` package, the real package wins.
"""

from __future__ import annotations

import sys
import types
from enum import StrEnum
from importlib.util import find_spec


def _real_config_package_exists() -> bool:
    """Report whether the real `src.shared.config` package is importable."""
    try:
        return find_spec("src.shared.config.constants") is not None
    except (ImportError, ValueError):
        return False


class _JobStatus(StrEnum):
    """Stand-in for the shared job lifecycle status enum."""

    PENDING = "pending"
    APPROVED = "approved"
    PRE_CHECK = "pre_check"
    EXECUTING = "executing"
    POST_CHECK = "post_check"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    ROLLBACK_FAILED = "rollback_failed"
    CANCELLED = "cancelled"


class _EntityType(StrEnum):
    """Stand-in for the shared Mist entity type enum."""

    DEVICE = "device"
    SITE = "site"
    SITE_SETTING = "site_setting"
    SITE_INFO = "site_info"
    WLAN = "wlan"
    ORG = "org"


class _DeviceType(StrEnum):
    """Stand-in for the shared Mist device type enum."""

    AP = "ap"
    SWITCH = "switch"
    GATEWAY = "gateway"


class _AlertSeverity(StrEnum):
    """Stand-in for the shared alert severity enum."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class _AlertType(StrEnum):
    """Stand-in for the shared alert type enum."""

    DRIFT = "drift"
    JOB_FAILURE = "job_failure"
    ROLLBACK = "rollback"


class _WaveStatus(StrEnum):
    """Stand-in for the shared rollout wave status enum."""

    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class _GoldenImageStatus(StrEnum):
    """Stand-in for the shared golden image status enum."""

    CANDIDATE = "candidate"
    APPROVED = "approved"
    RETIRED = "retired"


class _AppSettings:
    """Stand-in for the application settings object."""

    app_name = "mist-ops-platform"
    app_version = "0.1.0"
    environment = "test"
    log_level = "INFO"
    database_url = "postgresql+asyncpg://localhost/misthelper_test"
    redis_url = "redis://localhost:6379/0"
    redis_socket_timeout_seconds = 5.0
    redis_connect_timeout_seconds = 5.0
    worker_count = 1
    sync_interval_seconds = 300
    mist_api_host = "api.mist.com"
    mist_api_token = ""
    mist_webhook_secret = ""
    vault_addr = ""
    vault_token = ""


def _build_constants_module() -> types.ModuleType:
    """Build the stand-in `src.shared.config.constants` module."""
    constants = types.ModuleType("src.shared.config.constants")
    constants.JobStatus = _JobStatus  # type: ignore[attr-defined]
    constants.EntityType = _EntityType  # type: ignore[attr-defined]
    constants.DeviceType = _DeviceType  # type: ignore[attr-defined]
    constants.AlertSeverity = _AlertSeverity  # type: ignore[attr-defined]
    constants.AlertType = _AlertType  # type: ignore[attr-defined]
    constants.WaveStatus = _WaveStatus  # type: ignore[attr-defined]
    constants.GoldenImageStatus = _GoldenImageStatus  # type: ignore[attr-defined]
    return constants


def _build_settings_module() -> types.ModuleType:
    """Build the stand-in `src.shared.config.settings` module."""
    settings = types.ModuleType("src.shared.config.settings")
    settings.AppSettings = _AppSettings  # type: ignore[attr-defined]
    settings.get_settings = _AppSettings  # type: ignore[attr-defined]
    return settings


def _install_config_stand_in() -> None:
    """Register the stand-in `src.shared.config` package in `sys.modules`."""
    package = types.ModuleType("src.shared.config")
    package.__path__ = []  # Mark the module as a package so the submodules resolve.

    sys.modules["src.shared.config"] = package
    sys.modules["src.shared.config.constants"] = _build_constants_module()
    sys.modules["src.shared.config.settings"] = _build_settings_module()


if not _real_config_package_exists():
    _install_config_stand_in()
