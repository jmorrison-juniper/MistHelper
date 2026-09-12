"""FastAPI dependency injection providers (T024).

Provides ``get_db_session``, ``get_current_user``, ``get_scoped_org_id``, and
``get_mist_session`` for use in route function signatures.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.middleware.auth import (
    CurrentUser,
    get_current_user,
    require_org_access,
)
from sqlalchemy.ext.asyncio import async_sessionmaker

logger = logging.getLogger(__name__)


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


async def get_scoped_org_id(
    org_id: UUID = Query(...),
    user: CurrentUser = Depends(get_authenticated_user),
) -> UUID:
    """Return the requested ``org_id`` only after the membership check passes.

    Every route that accepts an ``org_id`` query parameter must read the value
    through this dependency. The dependency authenticates the caller and then
    confirms the caller belongs to the requested organization. A route that
    reads ``org_id`` directly from ``Query`` exposes the data of every other
    organization, so no route may do that.
    """
    logger.debug("Checking organization membership for %s", org_id)  # Record the check before it runs
    try:
        require_org_access(str(org_id), user)  # Raise 403 when the caller is outside the organization
    except HTTPException:
        logger.warning(  # Record the denial, because a denial is a security event
            "Denied cross-organization access to %s for %s",
            org_id,
            user.email or "unknown caller",
        )
        raise  # Preserve the 403 status and the original detail text
    logger.debug("Granted access to organization %s", org_id)  # Record the allow decision
    return org_id  # Hand the checked value to the route
