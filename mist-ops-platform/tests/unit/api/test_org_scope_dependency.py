"""Tests for the organization scope dependency (issue #1879).

The platform is multi-tenant. Every route that accepts an ``org_id`` query
parameter must confirm that the caller belongs to that organization. Without
the check, any caller with a valid token reads the data of any organization.

This module holds two kinds of test. The first kind drives the dependency
through a live request and asserts the status code. The second kind reads the
route source and asserts that no route takes ``org_id`` straight from
``Query``. The source test needs no web framework, so it runs in every
environment.
"""

from __future__ import annotations

import ast  # Parse the route modules without an import, so the test needs no dependency
import pathlib  # Locate the route modules on disk
import sys  # Extend the import path so "src" resolves during a direct run

import pytest  # Test framework and skip helper

ROUTES_DIR = (  # Directory that holds every API route module
    pathlib.Path(__file__).resolve().parents[3] / "src" / "api" / "routes"
)
PLATFORM_ROOT = pathlib.Path(__file__).resolve().parents[3]  # Sub-project root

if str(PLATFORM_ROOT) not in sys.path:  # Only extend the path once
    sys.path.insert(0, str(PLATFORM_ROOT))  # Make "src.api" importable

ORG_IN_SCOPE = "11111111-1111-1111-1111-111111111111"  # Organization the caller owns
ORG_OUT_OF_SCOPE = "22222222-2222-2222-2222-222222222222"  # Organization the caller must not read


# -- Static guard -------------------------------------------------------


def _bare_query_org_params(path: pathlib.Path) -> list[str]:
    """Return the name of every function that reads ``org_id`` from ``Query``."""
    tree = ast.parse(path.read_text(encoding="utf-8"))  # Parse the module source
    offenders: list[str] = []  # Collect the offending function names
    for node in ast.walk(tree):  # Visit every node, so nested routes count too
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue  # Only a function can declare a route parameter
        if _reads_org_id_from_query(node):  # Check this function's defaults
            offenders.append(node.name)  # Record the function for the failure message
    return offenders


def _reads_org_id_from_query(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Return True when ``org_id`` takes its default from a ``Query`` call.

    A function that calls ``_resolve_org_ids`` or ``require_org_access`` runs
    the membership check itself, so that shape passes.
    """
    if _calls_a_scope_check(node):  # The function checks the membership by hand
        return False
    args = node.args  # Positional and keyword arguments of the function
    named = args.args + args.kwonlyargs  # Every argument that can carry a default
    defaults = ([None] * (len(args.args) - len(args.defaults))) + list(args.defaults)
    defaults += list(args.kw_defaults)  # Align the defaults with the argument names
    for arg, default in zip(named, defaults):  # Walk the aligned pairs
        if arg.arg != "org_id" or default is None:  # Only the org_id argument matters
            continue
        if isinstance(default, ast.Call) and getattr(default.func, "id", "") == "Query":
            return True  # A bare Query default skips the membership check
    return False


def _calls_a_scope_check(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Return True when the function body calls a known scope check helper."""
    checks = {"_resolve_org_ids", "require_org_access"}  # Helpers that raise 403 on a bad scope
    for child in ast.walk(node):  # Visit every node in the function body
        if isinstance(child, ast.Call) and getattr(child.func, "id", "") in checks:
            return True  # The function performs its own membership check
    return False


def test_no_route_reads_org_id_from_query() -> None:
    """Assert that every route reads ``org_id`` through the scope dependency.

    A route that keeps ``org_id: UUID = Query(...)`` exposes the data of every
    other organization. This test fails the build when a new route reintroduces
    that shape.
    """
    offenders: dict[str, list[str]] = {}  # Map a module name to its offending functions
    for module in sorted(ROUTES_DIR.glob("*.py")):  # Read every route module
        found = _bare_query_org_params(module)  # Collect the offenders in this module
        if found:  # Only record a module that holds an offender
            offenders[module.name] = found
    assert offenders == {}, (  # Report every offender at once, so one run shows all the work
        "These routes read org_id straight from Query and skip the membership "
        f"check. Use Depends(get_scoped_org_id) instead: {offenders}"
    )


# -- Live request behavior ----------------------------------------------


def _build_probe_app(org_ids: list[str], *, is_msp: bool = False):
    """Return a small app whose single route uses the scope dependency."""
    fastapi = pytest.importorskip("fastapi")  # Skip when the web framework is absent
    pytest.importorskip("httpx")  # The test client needs httpx
    from uuid import UUID  # Match the type the real routes declare

    from src.api.deps import get_authenticated_user, get_scoped_org_id
    from src.api.middleware.auth import CurrentUser

    app = fastapi.FastAPI()  # Minimal app, so the test needs no database

    @app.get("/probe")  # One route is enough to exercise the dependency
    async def probe(org_id: UUID = fastapi.Depends(get_scoped_org_id)) -> dict:
        """Return the organization the dependency approved."""
        return {"org_id": str(org_id)}  # Echo the value, so a pass is visible

    async def fake_user() -> CurrentUser:
        """Return a caller whose scope the test controls."""
        return CurrentUser(token="test-token", email="tester@example.com", org_ids=org_ids, is_msp=is_msp)

    app.dependency_overrides[get_authenticated_user] = fake_user  # Skip the live Mist lookup
    return app


def _get(app, org_id: str):
    """Send one probe request and return the response."""
    from fastapi.testclient import TestClient  # Imported late, so the skip above applies

    with TestClient(app) as client:  # Context manager runs the app lifespan
        return client.get("/probe", params={"org_id": org_id})


def test_caller_reads_its_own_organization() -> None:
    """A caller inside the organization gets the data."""
    app = _build_probe_app([ORG_IN_SCOPE])  # Caller owns one organization
    response = _get(app, ORG_IN_SCOPE)  # Request that same organization
    assert response.status_code == 200  # The membership check passes
    assert response.json()["org_id"] == ORG_IN_SCOPE  # The dependency returns the value


def test_caller_cannot_read_another_organization() -> None:
    """A caller outside the organization gets 403, not the data."""
    app = _build_probe_app([ORG_IN_SCOPE])  # Caller owns one organization
    response = _get(app, ORG_OUT_OF_SCOPE)  # Request a different organization
    assert response.status_code == 403  # The membership check refuses the request
    assert "Insufficient privileges" in response.text  # The refusal names the cause


def test_msp_caller_reads_any_organization() -> None:
    """An MSP caller keeps cross-organization access."""
    app = _build_probe_app([], is_msp=True)  # MSP caller holds no explicit org list
    response = _get(app, ORG_OUT_OF_SCOPE)  # Request any organization
    assert response.status_code == 200  # The MSP branch allows the request


def test_caller_without_a_token_is_refused() -> None:
    """An unauthenticated caller never reaches the data."""
    fastapi = pytest.importorskip("fastapi")  # Skip when the web framework is absent
    pytest.importorskip("httpx")  # The test client needs httpx
    from uuid import UUID  # Match the type the real routes declare

    from fastapi.testclient import TestClient
    from src.api.deps import get_scoped_org_id

    app = fastapi.FastAPI()  # No dependency override, so the real auth path runs

    @app.get("/probe")  # One route is enough to exercise the dependency
    async def probe(org_id: UUID = fastapi.Depends(get_scoped_org_id)) -> dict:
        """Return the organization the dependency approved."""
        return {"org_id": str(org_id)}  # Never reached without a token

    with TestClient(app) as client:  # Context manager runs the app lifespan
        response = client.get("/probe", params={"org_id": ORG_IN_SCOPE})
    assert response.status_code == 401  # The dependency refuses a missing token
