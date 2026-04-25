"""Fixtures for integration tests that call the real Mist API.

These tests require valid credentials in .env (MIST_APITOKEN + org_id).
They are skipped automatically when credentials are absent.

Usage:
    pytest tests/integration/ -m integration -v
"""

import os

import pytest

# ---------------------------------------------------------------------------
# Credential detection -- skip entire module when missing
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


# Auto-skip every test in this directory when credentials are missing
def pytest_collection_modifyitems(config, items):
    """Skip integration tests when API credentials are not available."""
    skip_marker = pytest.mark.skip(reason="No Mist API credentials (.env)")
    for item in items:
        if "integration" in str(item.fspath):
            if not _has_credentials():
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
    session = mistapi.APISession(apitoken=token, host=host)
    return session


@pytest.fixture(scope="session")
def org_id():
    """Return the org_id from environment."""
    _ensure_env()
    return os.getenv("MIST_ORG_ID") or os.getenv("org_id")
