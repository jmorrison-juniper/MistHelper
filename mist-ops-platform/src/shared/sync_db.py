"""A guarded synchronous engine scope for the Celery tasks and the sync routes.

A SQLAlchemy engine owns a connection pool. The pool holds open PostgreSQL
sockets until some code calls ``dispose``. A caller that places the
``dispose`` call after a ``with Session(engine)`` block skips the call
whenever the block raises, because the exception leaves the function first.

Both process types that run this code live for a long time. A Celery worker
stays up for days, and a FastAPI worker serves many requests. So one leaked
pool per failure adds up until PostgreSQL reaches ``max_connections``. After
that limit, every service on the database fails to connect.

The scope below closes that gap. The ``finally`` clause runs after a return
and after an exception, so no exit path can skip the release.

This module fixes issue #1942. It also holds the pattern that pull request
#1920 first applied to one task in ``src.worker.tasks.sync_tasks``.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING

from sqlalchemy import create_engine

from src.shared.config.settings import get_settings

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy import Engine

logger = logging.getLogger(__name__)

# The async driver cannot run inside a Celery task or a sync route, so the
# caller swaps it for the blocking driver before it opens the engine.
_ASYNC_DRIVER = "+asyncpg"
_SYNC_DRIVER = "+psycopg2"


def build_sync_url() -> str:
    """Return the database URL with the blocking driver in place.

    Returns:
        The configured database URL that names the ``psycopg2`` driver.
    """
    settings = get_settings()  # Read the one settings object the app shares.
    # Swap the driver name, because asyncpg cannot serve a blocking Session.
    return str(settings.database_url).replace(_ASYNC_DRIVER, _SYNC_DRIVER)


@contextmanager
def sync_engine() -> Iterator[Engine]:
    """Yield a scoped engine and dispose it on every exit path.

    Yields:
        An engine bound to the blocking database driver.
    """
    sync_url = build_sync_url()  # Build the URL before the engine opens.
    logger.info("Opening a scoped engine for the sync database")
    engine = create_engine(sync_url)  # Open the pool this scope owns.
    try:
        yield engine  # Run the whole caller body inside this scope.
    finally:
        # This line runs after a return and after an exception, so the pool
        # goes back to the operating system on every path.
        engine.dispose()
        logger.debug("Disposed the scoped engine and closed its connection pool")
