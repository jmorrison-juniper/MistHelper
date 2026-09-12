"""FastAPI application factory with router mounting and lifespan (T019)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.shared.config.settings import get_settings
from src.shared.db import build_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage startup/shutdown resources."""
    settings = get_settings()
    engine = build_engine(settings)
    app.state.engine = engine

    # WHY: Alembic owns the schema. See issue #1883. A `create_all` call on
    # startup used `checkfirst`, so it skipped every table the migration built
    # and it added the missing ORM tables. The result matched neither owner.
    # Run `alembic upgrade head` before you start the API. See docs/operations.md.

    yield
    await engine.dispose()


def create_app() -> FastAPI:
    """Build and return the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Mist Ops Platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    _mount_middleware(app, settings)
    _mount_routers(app)
    return app


def _mount_middleware(app: FastAPI, settings) -> None:  # noqa: ANN001
    """Register middleware layers in order (outermost first)."""
    from src.api.middleware.logging import StructuredLoggingMiddleware
    from src.api.middleware.rate_limit import RateLimitMiddleware

    app.add_middleware(StructuredLoggingMiddleware)
    app.add_middleware(
        RateLimitMiddleware,
        redis_url=settings.redis_url,
    )


def _mount_routers(app: FastAPI) -> None:
    """Include all API routers under /api/v1."""
    from src.api.routes.audit import router as audit_router
    from src.api.routes.config import router as config_router
    from src.api.routes.deploy import router as deploy_router
    from src.api.routes.health import auth_router, router as health_router
    from src.api.routes.sync import (
        drift_router,
        inv_router,
        policy_router,
        router as sync_router,
    )
    from src.api.routes.webhooks import router as webhook_router

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(sync_router, prefix="/api/v1")
    app.include_router(inv_router, prefix="/api/v1")
    app.include_router(webhook_router, prefix="/api/v1")
    app.include_router(config_router, prefix="/api/v1")
    app.include_router(deploy_router, prefix="/api/v1")
    app.include_router(audit_router, prefix="/api/v1")
    app.include_router(drift_router, prefix="/api/v1")
    app.include_router(policy_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
