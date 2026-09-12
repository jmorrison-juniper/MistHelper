"""Shared socket timeout values for every Redis client of the platform.

A Redis client that carries no socket timeout waits without a limit. A host
that drops packets stays silent instead of refusing the connection, so the
caller never returns. The token cache, the session store, and the rate limiter
are optimizations. A slow cache must never hold a worker forever.

Two environment variables tune the limits.

``REDIS_SOCKET_TIMEOUT_SECONDS`` limits one read or one write.
``REDIS_CONNECT_TIMEOUT_SECONDS`` limits the connect.

Both default to ``REDIS_SOCKET_TIMEOUT_SECONDS`` below, which is 5 seconds.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)  # Reports the resolved limits, which hold no secret.

# WHY: one shared constant keeps every call site on the same safe default.
REDIS_SOCKET_TIMEOUT_SECONDS = 5.0


def redis_timeout_kwargs() -> dict[str, float]:
    """Return the socket timeout keyword arguments for a Redis client."""
    from src.shared.config.settings import get_settings

    logger.info("Redis socket timeout lookup starts.")  # Announce the lookup before the read.
    settings = get_settings()  # Read the one shared settings object, so every client agrees.
    # WHY: read the fields directly. AppSettings declares both, and the test stand-in in
    # tests/conftest.py declares both. A getattr default would hide a rename, so a typo
    # would silently restore the unlimited wait that this module exists to prevent.
    read_limit = float(settings.redis_socket_timeout_seconds)
    connect_limit = float(settings.redis_connect_timeout_seconds)
    kwargs = {"socket_timeout": read_limit, "socket_connect_timeout": connect_limit}
    logger.debug(
        "Redis socket timeout lookup done. The read limit is %s and the connect limit is %s.",
        read_limit,
        connect_limit,
    )
    return kwargs
