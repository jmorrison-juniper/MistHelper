"""Application settings read from the process environment.

The platform reads every setting from an environment variable. The deployment
supplies those variables through ``deploy/compose.yml`` and an ``.env`` file.

``session_cookie_secure`` controls the ``Secure`` attribute of the
``mist_session`` cookie. The default is ``True``, so the browser sends the
cookie over HTTPS only. Set ``SESSION_COOKIE_SECURE=false`` for local work over
plain HTTP. Warning: a false value lets any network hop read the session
identifier. Never set a false value in production.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from functools import lru_cache

logger = logging.getLogger(__name__)  # Records the settings load, without any secret value.

_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})  # Accepts the common ways to write true.

# WHY: a slots dataclass turns each class attribute into a descriptor, not the default value.
# The builder below must read the default from a module constant, not from AppSettings.
_DEFAULT_APP_NAME = "mist-ops-platform"
_DEFAULT_DATABASE_URL = "postgresql+asyncpg://mistops:changeme@localhost:5432/mistops"
_DEFAULT_REDIS_URL = "redis://localhost:6379/0"
_DEFAULT_MIST_API_HOST = "api.mist.com"
_DEFAULT_SYNC_INTERVAL_SECONDS = 300
_DEFAULT_LOG_LEVEL = "INFO"


def _env_str(name: str, default: str) -> str:
    """Return the environment value for *name*, or *default*."""
    return os.environ.get(name, default)  # A missing variable falls back to the default.


def _env_bool(name: str, default: bool) -> bool:
    """Return the environment value for *name* as a boolean."""
    raw = os.environ.get(name)  # Read the raw text, because an environment value is always text.
    if raw is None:  # An absent variable must keep the safe default.
        return default
    return raw.strip().lower() in _TRUE_VALUES  # Compare in lower case, so "True" also works.


def _env_int(name: str, default: int) -> int:
    """Return the environment value for *name* as an integer."""
    raw = os.environ.get(name)  # Read the raw text before the conversion.
    if raw is None:  # An absent variable must keep the documented default.
        return default
    try:
        return int(raw)  # Convert the text, because the caller needs a number.
    except ValueError:
        # WHY: a bad value must not stop the service. The default keeps the service alive.
        logger.warning("Setting %s is not a number. The default %d applies.", name, default)
        return default


@dataclass(frozen=True, slots=True)
class AppSettings:
    """Holds every setting that the platform reads at start."""

    app_name: str = _DEFAULT_APP_NAME
    database_url: str = _DEFAULT_DATABASE_URL
    redis_url: str = _DEFAULT_REDIS_URL
    mist_api_host: str = _DEFAULT_MIST_API_HOST
    mist_api_token: str = ""
    vault_addr: str = ""
    vault_token: str = ""
    mist_webhook_secret: str = ""
    sync_interval_seconds: int = _DEFAULT_SYNC_INTERVAL_SECONDS
    log_level: str = _DEFAULT_LOG_LEVEL
    session_cookie_secure: bool = True


def build_settings() -> AppSettings:
    """Build one settings object from the process environment."""
    logger.info("Application settings load starts.")  # Announce the load before the work.
    settings = AppSettings(
        app_name=_env_str("APP_NAME", _DEFAULT_APP_NAME),  # Names the service in the logs.
        database_url=_env_str("DATABASE_URL", _DEFAULT_DATABASE_URL),  # Points at Postgres.
        redis_url=_env_str("REDIS_URL", _DEFAULT_REDIS_URL),  # Points at the session store.
        mist_api_host=_env_str("MIST_API_HOST", _DEFAULT_MIST_API_HOST),  # Selects the region.
        mist_api_token=_env_str("MIST_API_TOKEN", ""),  # Supplies the worker fallback credential.
        vault_addr=_env_str("VAULT_ADDR", ""),  # An empty value turns the Vault lookup off.
        vault_token=_env_str("VAULT_TOKEN", ""),  # An empty value turns the Vault lookup off.
        mist_webhook_secret=_env_str("MIST_WEBHOOK_SECRET", ""),  # Verifies each inbound webhook.
        sync_interval_seconds=_env_int(
            "SYNC_INTERVAL_SECONDS",
            _DEFAULT_SYNC_INTERVAL_SECONDS,
        ),  # Paces the inventory sync.
        log_level=_env_str("LOG_LEVEL", _DEFAULT_LOG_LEVEL),  # Sets how much detail the logs hold.
        session_cookie_secure=_env_bool("SESSION_COOKIE_SECURE", True),  # Defaults to HTTPS only.
    )
    # WHY: the operator needs proof of the cookie policy. The value is a flag, not a secret.
    logger.debug(
        "Application settings load done. The secure cookie flag is %s.",
        settings.session_cookie_secure,
    )
    return settings


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Return the one shared settings object."""
    return build_settings()  # The cache keeps one object, so every caller reads the same values.
