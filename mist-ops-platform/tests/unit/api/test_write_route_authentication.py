"""Tests that every state-changing route demands a credential (issue #1979).

A route that changes state must never answer an anonymous caller. Three routes
took no authentication dependency at all. ``POST /config/install-from-revision``
pushed a stored configuration back to real Juniper Mist devices, so any caller
who reached the port could change a production network.

This module holds two kinds of test. The first kind reads the route source and
asserts that every write route declares an authentication dependency. That test
needs no web framework, so it runs in every environment. The second kind drives
a live request with no credential and asserts the 401 status code.

The static guard is the part that holds the fix in place. It is default-closed.
A new write route fails the test unless the author adds the dependency, or adds
the function to ``PUBLIC_WRITE_ROUTES`` with a stated reason.
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

WRITE_METHODS = {"post", "put", "patch", "delete"}  # HTTP methods that change state

AUTH_DEPENDENCIES = {  # Dependency callables that resolve and check a caller
    "get_authenticated_user",
    "get_scoped_org_id",
    "get_current_user",
}

PUBLIC_WRITE_ROUTES = {  # Write routes that answer an anonymous caller on purpose
    # The Mist cloud posts to this route. It authenticates the body with an
    # HMAC-SHA256 signature, so it needs no operator credential.
    "receive_mist_webhook",
    # The login route creates the session, so no session can exist before it.
    "login",
    # The refresh route reads the session cookie and issues a token from it.
    "refresh_token",
    # The logout route deletes the session cookie. A logout must always work.
    "logout",
}

HTTP_UNAUTHORIZED = 401  # Status code that a request with no credential must get

ORG_IN_SCOPE = "11111111-1111-1111-1111-111111111111"  # Organization the caller owns
ORG_OUT_OF_SCOPE = "22222222-2222-2222-2222-222222222222"  # Organization the caller must not touch


# -- Static guard -------------------------------------------------------


def _decorator_method(node: ast.expr) -> str:
    """Return the lowercase HTTP method that a route decorator names.

    The modules use several router objects, such as ``router``, ``auth_router``,
    and ``policy_router``. The router name does not matter, so this helper reads
    the attribute name only. It returns an empty string for any other decorator.
    """
    call = node.func if isinstance(node, ast.Call) else node  # Unwrap a called decorator
    if not isinstance(call, ast.Attribute):  # A plain name is not a route decorator
        return ""
    return call.attr.lower()  # "post", "get", "put", and so on


def _declares_auth_dependency(node: ast.AsyncFunctionDef | ast.FunctionDef) -> bool:
    """Return True when a parameter default calls ``Depends`` on an auth provider."""
    args = node.args  # Positional and keyword arguments of the handler
    named = args.args + args.kwonlyargs  # Every argument that can carry a default
    defaults = ([None] * (len(args.args) - len(args.defaults))) + list(args.defaults)
    defaults += list(args.kw_defaults)  # Align the defaults with the argument names
    for _arg, default in zip(named, defaults, strict=False):  # Walk the aligned pairs
        if not isinstance(default, ast.Call):  # Only a call can be a Depends value
            continue
        func_name = getattr(default.func, "id", "") or getattr(default.func, "attr", "")
        if func_name != "Depends":  # Any other call is not a dependency
            continue
        for provider in default.args:  # Read the callable that Depends wraps
            provider_name = getattr(provider, "id", "") or getattr(provider, "attr", "")
            if provider_name in AUTH_DEPENDENCIES:  # The provider resolves a caller
                return True
    return False


def _unauthenticated_write_routes(path: pathlib.Path) -> list[str]:
    """Return the name of every write handler in *path* that takes no credential."""
    tree = ast.parse(path.read_text(encoding="utf-8"))  # Parse the module source
    offenders: list[str] = []  # Collect the offending handler names
    for node in ast.walk(tree):  # Visit every node, so a nested handler counts too
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue  # Only a function can carry a route decorator
        methods = {_decorator_method(d) for d in node.decorator_list}  # Read the decorators
        if not methods & WRITE_METHODS:  # The handler changes no state
            continue
        if node.name in PUBLIC_WRITE_ROUTES:  # The route answers anonymous callers on purpose
            continue
        if _declares_auth_dependency(node):  # The handler resolves a caller
            continue
        offenders.append(node.name)  # Record the handler for the failure message
    return offenders


def test_every_write_route_demands_a_credential() -> None:
    """Assert that no POST, PUT, PATCH, or DELETE route answers an anonymous caller.

    This guard is default-closed. A new write route fails this test until the
    author adds an authentication dependency. Issue #1979 records the three
    routes that shipped without one.
    """
    offenders: dict[str, list[str]] = {}  # Map a module name to its offending handlers
    for module in sorted(ROUTES_DIR.glob("*.py")):  # Read every route module
        found = _unauthenticated_write_routes(module)  # Collect the offenders here
        if found:  # Only record a module that holds an offender
            offenders[module.name] = found
    assert offenders == {}, (  # Report every offender at once, so one run shows all the work
        "These routes change state and take no authentication dependency. Add "
        "Depends(get_authenticated_user) or Depends(get_scoped_org_id). If the "
        "route must stay public, add it to PUBLIC_WRITE_ROUTES with a reason: "
        f"{offenders}"
    )


REPAIRED_ROUTES = {  # Map a module file to the handler that issue #1979 repaired
    "config.py": ["compute_diff", "install_from_revision"],
    "health.py": ["create_channel"],
    "sync.py": ["trigger_sync"],
}


def _index_handlers(module_name: str) -> dict[str, ast.AsyncFunctionDef | ast.FunctionDef]:
    """Return every function in *module_name*, indexed by its name."""
    tree = ast.parse((ROUTES_DIR / module_name).read_text(encoding="utf-8"))
    handlers: dict[str, ast.AsyncFunctionDef | ast.FunctionDef] = {}
    for node in ast.walk(tree):  # Visit every node, so a nested handler counts too
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            handlers[node.name] = node  # Index the function for a direct lookup
    return handlers


def _called_names(node: ast.AsyncFunctionDef | ast.FunctionDef) -> set[str]:
    """Return the name of every function that the body of *node* calls."""
    names: set[str] = set()  # Collect the called names
    for child in ast.walk(node):  # Visit every node in the function body
        if not isinstance(child, ast.Call):  # Only a call carries a callee name
            continue
        names.add(getattr(child.func, "id", "") or getattr(child.func, "attr", ""))
    return names


def test_the_repaired_routes_declare_the_dependency() -> None:
    """Assert that the four routes from issue #1979 now resolve a caller.

    The default-closed guard above passes when a handler is added to the
    allowlist. This test names the repaired handlers, so no later edit can hide
    the regression behind an allowlist entry.
    """
    for module_name, handlers in REPAIRED_ROUTES.items():  # Check each repaired module
        found = _index_handlers(module_name)  # Index this module once
        for handler in handlers:  # Check every repaired handler in this module
            assert handler in found, f"{module_name} lost the handler {handler}"
            assert _declares_auth_dependency(found[handler]), (
                f"{module_name}:{handler} lost its authentication dependency. "
                "An anonymous caller can reach it again. See issue #1979."
            )


def test_the_repaired_routes_check_the_body_organization() -> None:
    """Assert that each repaired route checks the organization the body names.

    The routes read ``org_id`` from the request body, so the scope dependency
    that reads a query parameter cannot check them. Each route must call
    ``require_org_access`` itself, or a caller reaches another organization.
    """
    for module_name, handlers in REPAIRED_ROUTES.items():  # Check each repaired module
        found = _index_handlers(module_name)  # Index this module once
        for handler in handlers:  # Check every repaired handler in this module
            assert handler in found, f"{module_name} lost the handler {handler}"
            assert "require_org_access" in _called_names(found[handler]), (
                f"{module_name}:{handler} reads org_id from the body and runs "
                "no membership check. A caller reaches another organization."
            )


# -- Live request behavior ----------------------------------------------


def _build_probe_app():
    """Return an app that mounts the real config router with a stub database."""
    fastapi = pytest.importorskip("fastapi")  # Skip when the web framework is absent
    pytest.importorskip("httpx")  # The test client needs httpx
    pytest.importorskip("sqlalchemy")  # deps.py imports sqlalchemy at module load

    from src.api.deps import get_db_session
    from src.api.routes.config import router as config_router

    app = fastapi.FastAPI()  # Minimal app, so the test needs no database
    app.include_router(config_router)  # Mount the real routes under test

    async def fake_db():
        """Yield a placeholder, so the database dependency never opens a connection."""
        yield None  # The request must fail on authentication before it reads this

    app.dependency_overrides[get_db_session] = fake_db  # Keep the test off the database
    return app


@pytest.mark.parametrize(
    ("path", "body"),
    [
        (
            "/config/diff",  # The read route discloses a stored device configuration
            {
                "org_id": ORG_OUT_OF_SCOPE,
                "old_revision_id": 1,
                "new_revision_id": 2,
            },
        ),
        (
            "/config/install-from-revision",  # The write route changes a real device
            {
                "org_id": ORG_OUT_OF_SCOPE,
                "revision_id": 1,
                "target_entity_ids": [ORG_IN_SCOPE],
                "confirm": True,
                "reason": "test",
            },
        ),
    ],
)
def test_anonymous_caller_gets_401(path: str, body: dict) -> None:
    """A caller who sends no credential must get 401 and must change nothing.

    The body sets ``confirm`` to true on the install route, because the caller
    controls that field. The guard must be the credential, not the field.
    """
    from fastapi.testclient import TestClient  # Imported late, so the skip above applies

    app = _build_probe_app()  # Mount the real routes
    with TestClient(app) as client:  # Context manager runs the app lifespan
        response = client.post(path, json=body)  # Send no Authorization header and no cookie
    assert response.status_code == HTTP_UNAUTHORIZED, (
        f"{path} answered an anonymous caller with {response.status_code}. "
        "An unauthenticated caller must never reach this route. See issue #1979."
    )
