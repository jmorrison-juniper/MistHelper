"""Async database engine, session factory, and connection helpers."""

from __future__ import annotations

import logging
import uuid as uuid_mod
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.shared.config.settings import AppSettings, get_settings

logger = logging.getLogger(__name__)

# Tables using LIST partitioning by org_id
PARTITIONED_TABLES = ("config_revisions", "device_status_snapshots", "audit_records")


def build_engine(settings: AppSettings | None = None) -> create_async_engine:
    """Create an async SQLAlchemy engine with sensible pool defaults."""
    settings = settings or get_settings()
    return create_async_engine(
        settings.database_url,
        echo=False,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
    )


def build_session_factory(
    settings: AppSettings | None = None,
) -> async_sessionmaker[AsyncSession]:
    """Build an async session factory bound to the default engine."""
    engine = build_engine(settings)
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@asynccontextmanager
async def get_session(
    factory: async_sessionmaker[AsyncSession] | None = None,
) -> AsyncGenerator[AsyncSession, None]:
    """Yield an async session with automatic commit/rollback."""
    factory = factory or build_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def ensure_tables_exist(engine) -> None:  # noqa: ANN001
    """Create all ORM tables on startup. Idempotent via checkfirst.

    Uses an advisory lock to prevent race conditions when multiple
    uvicorn workers start simultaneously.
    """
    import src.shared.models  # noqa: F401 — register all models
    from src.shared.models.base import Base

    async with engine.begin() as conn:
        await conn.execute(text("SELECT pg_advisory_lock(1)"))
        try:
            await conn.run_sync(Base.metadata.create_all)
        finally:
            await conn.execute(text("SELECT pg_advisory_unlock(1)"))
    logger.info("Database tables ensured")


async def ensure_org_partitions(engine, org_id: str) -> None:  # noqa: ANN001
    """Create LIST partitions for one org across all partitioned tables."""
    validated = uuid_mod.UUID(str(org_id))
    safe_suffix = validated.hex

    async with engine.begin() as conn:
        for table_name in PARTITIONED_TABLES:
            partition_name = f"{table_name}_org_{safe_suffix}"
            await conn.execute(text(
                f"CREATE TABLE IF NOT EXISTS {partition_name} "
                f"PARTITION OF {table_name} "
                f"FOR VALUES IN ('{validated!s}')"
            ))
    logger.info("Org partitions ensured for %s", validated)
