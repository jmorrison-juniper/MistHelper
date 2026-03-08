"""FastAPI dependency injection providers (T024).

Provides ``get_db_session``, ``get_current_user``, and ``get_mist_session``
for use in route function signatures.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.middleware.auth import CurrentUser, get_current_user
from sqlalchemy.ext.asyncio import async_sessionmaker


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Yield an async SQLAlchemy session, commit on success."""
    engine = request.app.state.engine
    factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_authenticated_user(
    user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Alias dependency — returns the validated current user."""
    return user
