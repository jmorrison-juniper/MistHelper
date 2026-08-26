"""Fixtures for integration tests that call the real Mist API.

A test that calls the real cloud asks for the `mist_api_session` fixture or the
`org_id` fixture. Both read credentials from .env (MIST_APITOKEN + org_id), and
both are skipped automatically when those credentials are absent. A test in this
directory that asks for neither fixture builds its own stand-ins, so it runs
either way.

Usage:
    pytest tests/integration/ -m integration -v
"""

import inspect
import os

import pytest

# ---------------------------------------------------------------------------
# Credential detection -- skip the credentialed tests when .env holds nothing
# ---------------------------------------------------------------------------

_env_loaded = False


def _ensure_env():
    """Load .env once (idempotent) and return True if credentials exist."""
    global _env_loaded
    if not _env_loaded:
        try:
            from dotenv import load_dotenv

            load_dotenv(override=False)
        except ImportError:
            pass
        _env_loaded = True
    token = os.getenv("MIST_APITOKEN") or os.getenv("MIST_API_TOKEN")
    org = os.getenv("MIST_ORG_ID") or os.getenv("org_id")
    return bool(token and org)


def _has_credentials() -> bool:
    return _ensure_env()


# Fixtures that read .env. A test that asks for one of these needs credentials.
_CREDENTIAL_FIXTURES = frozenset({"mist_api_session", "org_id"})


# Auto-skip the credentialed tests in this directory when credentials are missing
def pytest_collection_modifyitems(config, items):
    """Skip integration tests that need API credentials when none are present.

    Why:
        An earlier version of this hook skipped every test under
        `tests/integration/`. That rule is too wide. Some integration tests
        build their own stand-ins, open no socket, and reach no cloud, so they
        passed locally and then skipped silently in continuous integration,
        where they proved nothing. The hook now asks each test which fixtures
        it wants. `item.fixturenames` holds the whole resolved closure, so a
        test that reaches a credentialed fixture through another fixture is
        still caught.

    Args:
        config: The pytest configuration. The hook does not read it.
        items: The collected tests. The hook marks a subset of them.
    """
    if _has_credentials():
        return
    skip_marker = pytest.mark.skip(reason="No Mist API credentials (.env)")
    for item in items:
        if "integration" not in str(item.fspath):
            continue
        if _CREDENTIAL_FIXTURES.isdisjoint(item.fixturenames):
            continue  # This test supplies its own stand-ins and needs no cloud.
        item.add_marker(skip_marker)


# ---------------------------------------------------------------------------
# Session-scoped fixtures (one API session per test run)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def mist_api_session():
    """Create a real mistapi.APISession from .env credentials.

    Session-scoped so we authenticate once per pytest invocation.
    """
    _ensure_env()
    import mistapi

    host = os.getenv("MIST_HOST", "api.mist.com")
    token = os.getenv("MIST_APITOKEN") or os.getenv("MIST_API_TOKEN")

    apisession_class = mistapi.APISession
    apisession_module = inspect.getmodule(apisession_class)
    apisession_module_name = getattr(apisession_module, "__name__", "")
    if not apisession_module_name.startswith("mistapi"):
        pytest.skip("Skipping integration tests: mistapi.APISession is mocked or monkeypatched")

    session = apisession_class(apitoken=token, host=host)
    if type(session).__module__.startswith("unittest.mock"):
        pytest.skip("Skipping integration tests: APISession constructor returned mock object")
    return session


@pytest.fixture(scope="session")
def org_id():
    """Return the org_id from environment."""
    _ensure_env()
    return os.getenv("MIST_ORG_ID") or os.getenv("org_id")
