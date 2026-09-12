"""Tests for the MSP organization scope check (issue #2017).

The old ``require_org_access`` returned at once when ``CurrentUser.is_msp`` was
true. The flag is one global boolean. The Mist ``/api/v1/self`` answer sets the
flag when any privilege row carries ``scope == "msp"``. The flag never named
which MSP account the operator administers.

An operator of one MSP therefore reached every organization on the platform.
That set held the organization of a different MSP, and it held an organization
with no MSP owner.

These tests prove the new behavior. An MSP operator reaches only the
organizations that the MSP owns. Every other organization returns 403.
"""

from __future__ import annotations

import sys  # Extend the import path so "src" resolves during a direct run
from pathlib import Path  # Locate the sub-project root on disk
from types import SimpleNamespace  # Build a stub row without a database
from uuid import UUID  # Match the type the real routes declare

import pytest  # Test framework and skip helper

PLATFORM_ROOT = Path(__file__).resolve().parents[3]  # Sub-project root that holds "src"

if str(PLATFORM_ROOT) not in sys.path:  # Only extend the path one time
    sys.path.insert(0, str(PLATFORM_ROOT))  # Make "src.api" importable

MSP_OWNED_ORG = "11111111-1111-1111-1111-111111111111"  # Organization the MSP owns
FOREIGN_ORG = "22222222-2222-2222-2222-222222222222"  # Organization of a different MSP
ORPHAN_ORG = "33333333-3333-3333-3333-333333333333"  # Organization with no MSP owner
MSP_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"  # MSP account that the operator administers
MSP_B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"  # MSP account that the operator never touches

HTTP_OK = 200  # Names the success status, because a bare number is a magic value
HTTP_FORBIDDEN = 403  # Names the status that a scope refusal returns


# -- Probe application --------------------------------------------------


def _build_probe_app(user):
    """Return a small app whose single route uses the scope dependency."""
    fastapi = pytest.importorskip("fastapi")  # Skip when the web framework is absent
    pytest.importorskip("httpx")  # The test client needs httpx
    pytest.importorskip("sqlalchemy")  # deps.py imports sqlalchemy at module load

    from src.api.deps import get_authenticated_user, get_scoped_org_id

    app = fastapi.FastAPI()  # Minimal app, so the test needs no database

    @app.get("/probe")  # One route is enough to exercise the dependency
    async def probe(org_id: UUID = fastapi.Depends(get_scoped_org_id)) -> dict:  # noqa: B008
        """Return the organization the dependency approved."""
        return {"org_id": str(org_id)}  # Echo the value, so a pass is visible

    async def fake_user():
        """Return the caller that the test controls."""
        return user  # Skip the live Mist lookup and hand back a fixed caller

    app.dependency_overrides[get_authenticated_user] = fake_user  # Replace the Mist lookup
    return app


def _get(app, org_id: str):
    """Send one probe request and return the response."""
    from fastapi.testclient import TestClient  # Imported late, so the skip above applies

    with TestClient(app) as client:  # The context manager runs the app lifespan
        return client.get("/probe", params={"org_id": org_id})


def _msp_user(**overrides):
    """Return an MSP caller whose reachable organizations the test controls."""
    pytest.importorskip("fastapi")  # The dataclass lives beside the FastAPI imports

    from src.api.middleware.auth import CurrentUser

    fields = {  # Default shape of an MSP operator who holds no direct org grant
        "token": "test-token",  # The value is a placeholder, and it reaches no network
        "email": "msp-operator@example.com",  # The audit log records this address
        "org_ids": [],  # An MSP row grants no direct organization
        "is_msp": True,  # The Mist answer carried one row with scope "msp"
        "msp_ids": [MSP_A],  # The operator administers this one MSP account
        "msp_org_ids": [MSP_OWNED_ORG],  # The database says the MSP owns this organization
    }
    fields.update(overrides)  # Let each test narrow or widen the reachable set
    return CurrentUser(**fields)  # Build the caller object the dependency reads


# -- The defect that issue #2017 records --------------------------------


def test_msp_caller_cannot_reach_a_foreign_organization() -> None:
    """An MSP operator must not reach the organization of a different MSP."""
    app = _build_probe_app(_msp_user())  # The MSP owns MSP_OWNED_ORG and nothing else
    response = _get(app, FOREIGN_ORG)  # Ask for an organization of a different MSP
    assert response.status_code == HTTP_FORBIDDEN  # The scope check must refuse the request
    assert "Insufficient privileges" in response.text  # The refusal names the cause


def test_msp_caller_cannot_reach_an_organization_without_an_msp_owner() -> None:
    """The check falls closed when the organization has no MSP owner."""
    app = _build_probe_app(_msp_user())  # The MSP owns MSP_OWNED_ORG and nothing else
    response = _get(app, ORPHAN_ORG)  # Ask for an organization whose msp_id is NULL
    assert response.status_code == HTTP_FORBIDDEN  # A NULL owner must never grant access


def test_msp_flag_alone_grants_no_organization() -> None:
    """The ``is_msp`` flag alone must grant nothing."""
    user = _msp_user(msp_ids=[], msp_org_ids=[])  # The flag is true and the scope is empty
    app = _build_probe_app(user)  # Build the probe with that empty scope
    response = _get(app, MSP_OWNED_ORG)  # Ask for any organization at all
    assert response.status_code == HTTP_FORBIDDEN  # The blanket bypass must be gone


def test_msp_caller_reaches_an_organization_the_msp_owns() -> None:
    """An MSP operator keeps access to the organizations that the MSP owns."""
    app = _build_probe_app(_msp_user())  # The MSP owns MSP_OWNED_ORG
    response = _get(app, MSP_OWNED_ORG)  # Ask for that owned organization
    assert response.status_code == HTTP_OK  # A refusal here would break every MSP operator
    assert response.json()["org_id"] == MSP_OWNED_ORG  # The dependency returns the value


def test_direct_org_grant_still_works_for_an_msp_caller() -> None:
    """A direct organization grant still reaches its organization."""
    user = _msp_user(org_ids=[ORPHAN_ORG])  # Mist granted this organization row by row
    app = _build_probe_app(user)  # Build the probe with that direct grant
    response = _get(app, ORPHAN_ORG)  # Ask for the directly granted organization
    assert response.status_code == HTTP_OK  # A direct grant outranks the MSP lookup


# -- The MSP identifier collector ---------------------------------------


def test_collect_msp_ids_reads_only_the_msp_scoped_rows() -> None:
    """The collector keeps the MSP identifier of every MSP scoped row."""
    pytest.importorskip("fastapi")  # The helper lives beside the FastAPI imports

    from src.api.middleware.auth import collect_msp_ids

    rows = [  # One Mist answer holds a row for each grant
        {"scope": "msp", "msp_id": MSP_A},  # An MSP grant names the MSP account
        {"scope": "org", "org_id": FOREIGN_ORG},  # An org grant names no MSP account
        {"scope": "msp", "msp_id": MSP_A},  # Mist repeats a row, so the result must dedupe
        {"scope": "msp"},  # A malformed row carries no identifier, so drop it
    ]
    assert collect_msp_ids(rows) == [MSP_A]  # Only the one valid MSP identifier survives


def test_collect_msp_ids_returns_an_empty_list_for_no_msp_row() -> None:
    """The collector returns nothing when no row carries the MSP scope."""
    pytest.importorskip("fastapi")  # The helper lives beside the FastAPI imports

    from src.api.middleware.auth import collect_msp_ids

    rows = [{"scope": "org", "org_id": FOREIGN_ORG}]  # A plain operator holds org rows only
    assert collect_msp_ids(rows) == []  # No MSP row means no MSP scope


# -- The database lookup ------------------------------------------------


class _FakeResult:
    """Stand-in for the SQLAlchemy result of one select statement."""

    def __init__(self, rows: list[str]) -> None:
        self._rows = rows  # Hold the organization identifiers the fake query returns

    def scalars(self):
        """Return an object whose ``all`` reports the stored rows."""
        return SimpleNamespace(all=lambda: self._rows)  # Match the SQLAlchemy shape


class _FakeSession:
    """Stand-in for an async SQLAlchemy session that answers one select."""

    def __init__(self, rows: list[str]) -> None:
        self.rows = rows  # Rows that the fake query returns to the helper
        self.statements: list[object] = []  # Record each statement, so a test can read it

    async def execute(self, statement):
        """Record *statement* and return the fixed rows."""
        self.statements.append(statement)  # Prove the helper ran exactly one query
        return _FakeResult(self.rows)  # Answer with the organization identifiers


async def test_resolve_msp_org_ids_returns_the_owned_organizations() -> None:
    """The lookup returns the organizations that the named MSP accounts own."""
    pytest.importorskip("sqlalchemy")  # The helper builds a SQLAlchemy select

    from src.api.middleware.auth import resolve_msp_org_ids

    session = _FakeSession([UUID(MSP_OWNED_ORG)])  # The database owns one organization
    result = await resolve_msp_org_ids(session, [MSP_A])  # Ask for the reachable set
    assert result == [MSP_OWNED_ORG]  # The helper returns the identifier as a string
    assert len(session.statements) == 1  # One MSP lookup costs one query


async def test_resolve_msp_org_ids_skips_the_query_for_no_msp() -> None:
    """The lookup makes no query when the caller administers no MSP."""
    pytest.importorskip("sqlalchemy")  # The helper builds a SQLAlchemy select

    from src.api.middleware.auth import resolve_msp_org_ids

    session = _FakeSession([UUID(MSP_OWNED_ORG)])  # The rows must stay unread
    result = await resolve_msp_org_ids(session, [])  # A plain operator holds no MSP account
    assert result == []  # No MSP account means no MSP organization
    assert session.statements == []  # The helper must add no cost for a plain operator


async def test_resolve_msp_org_ids_drops_a_malformed_identifier() -> None:
    """The lookup ignores an MSP identifier that is not a UUID."""
    pytest.importorskip("sqlalchemy")  # The helper builds a SQLAlchemy select

    from src.api.middleware.auth import resolve_msp_org_ids

    session = _FakeSession([])  # The database returns no organization
    result = await resolve_msp_org_ids(session, ["not-a-uuid"])  # Mist sent a bad value
    assert result == []  # A bad identifier must fall closed, not raise
    assert session.statements == []  # No valid identifier means no query at all


async def test_resolve_msp_org_ids_ignores_an_msp_the_caller_lacks() -> None:
    """The lookup asks only for the MSP accounts that the caller administers."""
    pytest.importorskip("sqlalchemy")  # The helper builds a SQLAlchemy select

    from src.api.middleware.auth import resolve_msp_org_ids

    session = _FakeSession([UUID(MSP_OWNED_ORG)])  # The query answers for MSP_A only
    result = await resolve_msp_org_ids(session, [MSP_A])  # The caller never holds MSP_B
    assert MSP_B not in result  # The foreign MSP must never appear in the answer
    assert result == [MSP_OWNED_ORG]  # Only the owned organization comes back
