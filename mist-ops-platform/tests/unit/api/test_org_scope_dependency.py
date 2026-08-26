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
HTTP_OK = 200  # Names the success status, because a bare number is a magic value
HTTP_FORBIDDEN = 403  # Names the status that a scope refusal returns


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


def _has_auth_dependency(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Return True when the function declares an authentication dependency.

    A route without this dependency is fully anonymous. The platform accepts
    both get_authenticated_user and get_scoped_org_id as valid auth dependencies.
    get_scoped_org_id calls get_authenticated_user internally, so either form
    satisfies the authentication requirement.
    """
    auth_deps = {"get_authenticated_user", "get_scoped_org_id"}  # Both forms satisfy auth
    all_args = node.args.args + node.args.kwonlyargs  # Every named parameter
    all_defaults = (
        ([None] * (len(node.args.args) - len(node.args.defaults)))
        + list(node.args.defaults)
        + list(node.args.kw_defaults)
    )  # Align defaults with arguments
    for arg, default in zip(all_args, all_defaults):  # Walk each arg-default pair
        if default is None:  # No default means no Depends
            continue
        if not (isinstance(default, ast.Call) and getattr(default.func, "id", "") == "Depends"):
            continue  # Not a Depends() call
        dep_args = default.args  # The argument passed to Depends(...)
        if not dep_args:  # Depends called with no positional arg
            continue
        dep_name = getattr(dep_args[0], "id", "")  # Simple name, e.g. get_authenticated_user
        if dep_name in auth_deps:  # Found an accepted authentication dependency
            return True
    return False


def _is_route_handler(node: ast.FunctionDef | ast.AsyncFunctionDef, tree: ast.Module) -> bool:
    """Return True when the function is decorated with a router method decorator."""
    router_methods = {"get", "post", "put", "patch", "delete"}  # HTTP method decorator names
    for decorator in node.decorator_list:  # Walk all decorators on this function
        if not isinstance(decorator, ast.Call):  # Only decorated calls count
            continue
        func = decorator.func  # The decorator itself
        method = getattr(func, "attr", None)  # e.g. router.get -> "get"
        if method in router_methods:  # Matches an HTTP method
            return True
    return False


def _get_route_handlers_without_auth(path: pathlib.Path) -> list[str]:
    """Return function names that are route handlers with no auth dependency."""
    tree = ast.parse(path.read_text(encoding="utf-8"))  # Parse the source without importing it
    offenders: list[str] = []  # Collect handlers that lack authentication
    for node in ast.walk(tree):  # Visit every AST node
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue  # Only functions can be route handlers
        if not _is_route_handler(node, tree):  # Skip non-route functions
            continue
        if not _has_auth_dependency(node):  # Route has no authentication dependency
            offenders.append(node.name)  # Record the offender
    return offenders


def _default_is_depends(default: ast.expr | None) -> bool:
    """Return True when the default value is a Depends() call.

    FastAPI dependency parameters use Depends(func) as their default value.
    Body parameters have no default or use a Body() literal. Only body
    parameters need the require_org_access check.
    """
    if default is None:  # No default value
        return False
    if not isinstance(default, ast.Call):  # Not a function call
        return False
    func_name = getattr(default.func, "id", None)  # Simple function name
    return func_name == "Depends"  # True only for Depends(...)


def _body_org_id_without_scope_check(path: pathlib.Path) -> list[str]:
    """Return handler names that accept a body model with org_id but skip the scope check.

    A handler that reads org_id from a body parameter passes the guard only
    when its body calls require_org_access or _resolve_org_ids. Without that
    call, any authenticated caller supplies any org_id and writes into that org.

    Parameters with a Depends(...) default are FastAPI dependencies, not body
    parameters. Those are excluded because the dependency performs its own
    scope check through get_scoped_org_id or require_org_access.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))  # Parse without importing
    body_org_id_models: set[str] = set()  # Names of models that carry org_id
    for node in ast.walk(tree):  # Collect class definitions first
        if not isinstance(node, ast.ClassDef):
            continue  # Only classes can be models
        ann_names = {
            stmt.target.id
            for stmt in node.body
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)
        }  # Collect annotated assignments (e.g. org_id: UUID)
        assign_names = {
            stmt.targets[0].id
            for stmt in node.body
            if isinstance(stmt, ast.Assign) and isinstance(stmt.targets[0], ast.Name)
        }  # Collect plain assignments too
        if "org_id" in (ann_names | assign_names):  # This model carries org_id
            body_org_id_models.add(node.name)
    offenders: list[str] = []  # Handlers that accept a body org_id without the check
    for node in ast.walk(tree):  # Walk only route handlers
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue  # Only handlers matter
        if not _is_route_handler(node, tree):  # Skip helper functions
            continue
        if _calls_a_scope_check(node):  # Handler already performs its own check
            continue
        all_args = node.args.args + node.args.kwonlyargs  # Every named parameter
        all_defaults = (
            ([None] * (len(node.args.args) - len(node.args.defaults)))
            + list(node.args.defaults)
            + list(node.args.kw_defaults)
        )  # Align defaults with argument positions
        for arg, default in zip(all_args, all_defaults):  # Walk arg-default pairs
            if _default_is_depends(default):  # Depends() params are FastAPI dependencies
                continue
            annotation = arg.annotation  # The type annotation of this parameter
            if annotation is None:  # No type annotation
                continue
            ann_name = getattr(annotation, "id", None)  # Simple name, e.g. ExportRequest
            if ann_name in body_org_id_models:  # Parameter type carries org_id
                offenders.append(node.name)
                break  # One match per handler is enough
    return offenders


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


# Health and webhook routes do not expose tenant data, so they are exempt from authentication.
_AUTH_EXEMPT_MODULES = {"health.py", "webhooks.py", "__init__.py"}  # Modules that may omit auth


def test_no_route_handler_is_anonymous() -> None:
    """Assert that every data route handler declares get_authenticated_user.

    A handler without an authentication dependency is fully anonymous. Any
    caller who reaches the port can read or write data without a token. This
    test catches the pattern before it reaches the branch.
    """
    offenders: dict[str, list[str]] = {}  # Map a module name to its offending handlers
    for module in sorted(ROUTES_DIR.glob("*.py")):  # Read every route module
        if module.name in _AUTH_EXEMPT_MODULES:  # Skip exempt modules
            continue
        found = _get_route_handlers_without_auth(module)  # Collect handlers with no auth
        if found:  # Only record a module that holds an offender
            offenders[module.name] = found
    assert offenders == {}, (
        "These route handlers have no authentication dependency and are fully anonymous. "
        f"Add user: CurrentUser = Depends(get_authenticated_user): {offenders}"
    )


def test_no_handler_accepts_body_org_id_without_scope_check() -> None:
    """Assert that every handler that accepts a body org_id calls require_org_access.

    A handler that reads org_id from a request body and never calls
    require_org_access lets any authenticated caller write data into any
    organization. This test catches the pattern before it reaches the branch.
    """
    offenders: dict[str, list[str]] = {}  # Map a module name to its offending handlers
    for module in sorted(ROUTES_DIR.glob("*.py")):  # Read every route module
        found = _body_org_id_without_scope_check(module)  # Collect the offenders
        if found:  # Only record a module that holds an offender
            offenders[module.name] = found
    assert offenders == {}, (
        "These handlers accept a body with org_id but never call require_org_access. "
        f"Add require_org_access(str(body.org_id), user) before writing data: {offenders}"
    )


# -- Live request behavior ----------------------------------------------


def _build_probe_app(
    org_ids: list[str],
    *,
    is_msp: bool = False,
    msp_org_ids: list[str] | None = None,
):
    """Return a small app whose single route uses the scope dependency."""
    fastapi = pytest.importorskip("fastapi")  # Skip when the web framework is absent
    pytest.importorskip("httpx")  # The test client needs httpx
    pytest.importorskip("sqlalchemy")  # deps.py imports sqlalchemy at module load
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
        return CurrentUser(
            token="test-token",
            email="tester@example.com",
            org_ids=org_ids,
            is_msp=is_msp,
            msp_org_ids=msp_org_ids or [],  # Organizations that the MSP of the caller owns
        )

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


def test_msp_caller_reads_only_the_organizations_the_msp_owns() -> None:
    """An MSP caller reaches an owned organization and no other one.

    The old check returned at once for any MSP caller. That granted every
    organization on the platform to one MSP operator. Issue #2017 records the
    defect. Module ``test_msp_org_scope`` holds the full set of cases.
    """
    app = _build_probe_app([], is_msp=True, msp_org_ids=[ORG_IN_SCOPE])  # The MSP owns one org
    assert _get(app, ORG_IN_SCOPE).status_code == HTTP_OK  # The owned organization stays reachable
    assert _get(app, ORG_OUT_OF_SCOPE).status_code == HTTP_FORBIDDEN  # Every other org is refused


def test_caller_without_a_token_is_refused() -> None:
    """An unauthenticated caller never reaches the data."""
    fastapi = pytest.importorskip("fastapi")  # Skip when the web framework is absent
    pytest.importorskip("httpx")  # The test client needs httpx
    pytest.importorskip("sqlalchemy")  # deps.py imports sqlalchemy at module load
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
