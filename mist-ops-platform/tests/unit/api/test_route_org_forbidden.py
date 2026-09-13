"""Table driven proof that a caller outside the organization gets 403 (issue #2015).

Pull request #2012 put an organization membership check on every mutating route
in ``config.py`` and ``deploy.py``. No test proved the refusal for any single
route, so a future route could drop the check with no failure to report it.

This module walks a table of the mutating routes. Each entry names one method,
one path, and one request body. The body carries the organization identifier, so
the route runs its check before it reads the database.

Two tests read the same table. The first signs in as an operator of another
organization and asserts 403. The second signs in as the correct operator and
asserts that the answer is not 403. A check that refused every caller would pass
a 403 only test, so the second test is the guard against that mistake.

A new route joins the table with one line. The route then fails at once when it
carries no check.
"""

from __future__ import annotations

import sys  # Extend the import path so "src" resolves during a direct run
from datetime import UTC, datetime  # Build the scheduled time that a job body needs
from pathlib import Path  # Locate the sub-project root on disk
from typing import Any  # Name the shape of a request body

import pytest  # Test framework and skip helper

PLATFORM_ROOT = Path(__file__).resolve().parents[3]  # Sub-project root that holds "src"

if str(PLATFORM_ROOT) not in sys.path:  # Only extend the path one time
    sys.path.insert(0, str(PLATFORM_ROOT))  # Make "src.api" importable

CALLER_ORG = "11111111-1111-1111-1111-111111111111"  # Organization that the caller belongs to
TARGET_ORG = "22222222-2222-2222-2222-222222222222"  # Organization named in every request body
ENTITY_ID = "33333333-3333-3333-3333-333333333333"  # Placeholder device or site identifier
RECORD_ID = "44444444-4444-4444-4444-444444444444"  # Placeholder identifier in a route path

HTTP_FORBIDDEN = 403  # Names the status that a scope refusal returns
_FUTURE = datetime(2030, 1, 1, tzinfo=UTC)  # A fixed future time, so the clock never drifts
SCHEDULED_AT = _FUTURE.isoformat()  # The job schema demands an ISO 8601 timestamp

_TARGET_ENTITY = {  # One target entity, reused by the job and the dry run bodies
    "entity_type": "device",  # The schema demands a string entity type
    "entity_id": ENTITY_ID,  # The schema demands a UUID entity identifier
}

MUTATING_ROUTES: list[tuple[str, str, dict[str, Any]]] = [
    (  # POST /config/diff reads two revisions of one organization
        "post",
        "/config/diff",
        {"org_id": TARGET_ORG, "old_revision_id": 1, "new_revision_id": 2},
    ),
    (  # POST /config/install-from-revision pushes a stored revision back to devices
        "post",
        "/config/install-from-revision",
        {"org_id": TARGET_ORG, "revision_id": 1, "target_entity_ids": [ENTITY_ID]},
    ),
    (  # POST /config/baselines stores the intended state of one entity
        "post",
        "/config/baselines",
        {
            "org_id": TARGET_ORG,
            "entity_type": "device",
            "entity_scope": ENTITY_ID,
            "config_payload": {},
        },
    ),
    (  # POST /deploy/jobs schedules a change against the devices of one organization
        "post",
        "/deploy/jobs",
        {
            "org_id": TARGET_ORG,
            "target_entities": [_TARGET_ENTITY],
            "change_payload": {},
            "scheduled_at": SCHEDULED_AT,
        },
    ),
    (  # POST /deploy/dry-run validates a change without applying it
        "post",
        "/deploy/dry-run",
        {
            "org_id": TARGET_ORG,
            "target_entities": [_TARGET_ENTITY],
            "change_payload": {},
        },
    ),
    (  # POST /deploy/rollouts creates a multi-wave rollout plan
        "post",
        "/deploy/rollouts",
        {
            "org_id": TARGET_ORG,
            "name": "probe rollout",
            "waves": [{"wave_number": 1, "target_entities": [_TARGET_ENTITY]}],
        },
    ),
    (  # POST /deploy/golden-images registers a firmware image for one organization
        "post",
        "/deploy/golden-images",
        {
            "org_id": TARGET_ORG,
            "image_type": "firmware",
            "device_model": "EX4400",
            "version": "23.4R2.13",
            "content_hash": "0" * 64,
        },
    ),
    (  # POST /deploy/templates stores a reusable change template
        "post",
        "/deploy/templates",
        {
            "org_id": TARGET_ORG,
            "name": "probe template",
            "category": "config",
            "target_entity_type": "device",
        },
    ),
]

ROUTE_IDS = [f"{method.upper()} {path}" for method, path, _ in MUTATING_ROUTES]  # Readable names


class _FakeResult:
    """Stand-in for the SQLAlchemy result of one select statement."""

    @staticmethod
    def scalar_one_or_none() -> None:
        """Report that the database holds no matching row."""
        return None  # A missing row makes the route answer 404, and never 403

    @staticmethod
    def scalars():
        """Return an object whose ``all`` reports no row."""
        from types import SimpleNamespace  # Build the shape that SQLAlchemy returns

        return SimpleNamespace(all=list)  # An empty list keeps every route off the 403 path

    @staticmethod
    def scalar() -> None:
        """Report that the aggregate query found nothing."""
        return None  # A route that counts rows then sees an empty organization


class _FakeSession:
    """Stand-in for an async SQLAlchemy session that holds no row."""

    async def execute(self, statement):
        """Answer every select with an empty result."""
        del statement  # The stub runs no query, so the statement never matters
        return _FakeResult()  # The routes must reach 404, so the 403 case stays unambiguous

    async def flush(self) -> None:
        """Accept a flush without writing anything."""
        return None  # No database means no write, and the test needs none

    async def commit(self) -> None:
        """Accept a commit without writing anything."""
        return None  # The dependency commits on success, so this call must not fail

    async def rollback(self) -> None:
        """Accept a rollback without writing anything."""
        return None  # The dependency rolls back on failure, so this call must not fail

    def add(self, instance) -> None:
        """Accept a new row without storing it."""
        del instance  # The stub stores nothing, so a staged row is discarded here


def _fake_user_factory(caller_org: str):
    """Return a dependency that answers with a caller inside *caller_org*."""
    from src.api.middleware.auth import CurrentUser

    async def fake_user() -> CurrentUser:
        """Return a caller that belongs to *caller_org* and to nothing else."""
        return CurrentUser(  # A plain operator holds one organization and no MSP grant
            token="test-token",  # The value is a placeholder, and it reaches no network
            email="operator@example.com",  # The audit log records this address
            org_ids=[caller_org],  # The scope check compares the request against this list
        )

    return fake_user  # The caller registers this function as a dependency override


async def _fake_db():
    """Yield the stub session, so no route opens a real connection."""
    yield _FakeSession()  # The routes must refuse before they ever read a row


def _build_app(caller_org: str):
    """Return an app that mounts the real config and deploy routers."""
    fastapi = pytest.importorskip("fastapi")  # Skip when the web framework is absent
    pytest.importorskip("httpx")  # The test client needs httpx
    pytest.importorskip("sqlalchemy")  # The route modules import sqlalchemy at module load

    from src.api.deps import get_authenticated_user, get_db_session
    from src.api.routes.config import router as config_router
    from src.api.routes.deploy import router as deploy_router

    app = fastapi.FastAPI()  # Minimal app, so the test needs no live database
    app.include_router(config_router)  # Mount the real config routes, not a copy
    app.include_router(deploy_router)  # Mount the real deploy routes, not a copy
    app.dependency_overrides[get_authenticated_user] = _fake_user_factory(caller_org)
    app.dependency_overrides[get_db_session] = _fake_db  # Replace the database session
    return app


def _send(app, method: str, path: str, body: dict[str, Any]):
    """Send one request and return the response."""
    from fastapi.testclient import TestClient  # Imported late, so the skip above applies

    # WHY: a stub session makes some routes fail late. A 500 must become a response,
    # because the test reads the status code and never the traceback.
    with TestClient(app, raise_server_exceptions=False) as client:
        return client.request(method.upper(), path, json=body)


@pytest.mark.parametrize(("method", "path", "body"), MUTATING_ROUTES, ids=ROUTE_IDS)
def test_caller_outside_the_organization_is_refused(
    method: str,
    path: str,
    body: dict[str, Any],
) -> None:
    """Every mutating route refuses a caller outside the named organization."""
    app = _build_app(CALLER_ORG)  # The caller belongs to CALLER_ORG only
    response = _send(app, method, path, body)  # Every body names TARGET_ORG instead
    assert response.status_code == HTTP_FORBIDDEN, (  # Report the route on a failure
        f"{method.upper()} {path} answered {response.status_code}. "
        "A caller outside the organization must receive 403."
    )


@pytest.mark.parametrize(("method", "path", "body"), MUTATING_ROUTES, ids=ROUTE_IDS)
def test_caller_inside_the_organization_is_not_refused(
    method: str,
    path: str,
    body: dict[str, Any],
) -> None:
    """The correct caller passes the check, so the guard refuses nobody by mistake."""
    app = _build_app(TARGET_ORG)  # The caller now belongs to the organization in the body
    response = _send(app, method, path, body)  # Send the same request as the test above
    assert response.status_code != HTTP_FORBIDDEN, (  # Report the route on a failure
        f"{method.upper()} {path} answered 403 for a caller inside the organization. "
        "The check must refuse only an outside caller."
    )
