"""Credential/config preflight unit tests (feature 1020, User Story 3).

Verifies ``_preflight_verify_credentials()`` fails closed - before any mistapi/
requests call - when host/token config is missing or a placeholder, with a
redacted, actionable message referencing ``deploy/.env.example`` and the exact
env var names the code reads. Zero network, zero real credentials; the
zero-HTTP guarantee is proven structurally (the helper imports no network lib).
See ``specs/1020-safe-test-clean-run/contracts/preflight_failure_contract.md``.
"""

from __future__ import annotations

import inspect

import pytest

import MistHelper

_CREDENTIAL_ENV_VARS = ("MIST_HOST", "MIST_APITOKEN", "MIST_API_TOKEN")


def _clear_credential_env(monkeypatch):
    """Remove all host/token env vars so each test controls the exact configuration."""
    for name in _CREDENTIAL_ENV_VARS:  # WHY: guarantee a clean slate regardless of the ambient environment.
        monkeypatch.delenv(name, raising=False)


class TestCredentialPreflight:
    """Unit tests for the fail-closed host/token preflight."""

    def test_missing_token_fails_closed_with_actionable_message(self, monkeypatch, capsys):
        """No token env var set -> exits non-zero, naming the token vars and deploy/.env.example."""
        _clear_credential_env(monkeypatch)  # WHY: host now defaults to api.mist.com; only the token is missing.
        with pytest.raises(SystemExit) as exc_info:
            MistHelper._preflight_verify_credentials()
        assert exc_info.value.code == 1
        out = capsys.readouterr().out
        assert "MIST_APITOKEN" in out and "MIST_API_TOKEN" in out, "must name the token env vars"
        assert "deploy/.env.example" in out, "must reference the template file to copy"

    def test_blank_host_fails_closed(self, monkeypatch, capsys):
        """MIST_HOST explicitly blank -> exits non-zero with a specific host message (token present)."""
        _clear_credential_env(monkeypatch)
        monkeypatch.setenv("MIST_HOST", "")  # WHY: explicit blank host reproduces the malformed-URL defect.
        monkeypatch.setenv("MIST_APITOKEN", "realtoken0123456789")  # WHY: a real token isolates the host failure.
        with pytest.raises(SystemExit) as exc_info:
            MistHelper._preflight_verify_credentials()
        assert exc_info.value.code == 1
        assert "MIST_HOST" in capsys.readouterr().out

    def test_placeholder_host_fails_closed(self, monkeypatch, capsys):
        """MIST_HOST left at a copy-paste placeholder -> exits non-zero with a host message."""
        _clear_credential_env(monkeypatch)
        monkeypatch.setenv("MIST_HOST", "your_host_here")  # WHY: unedited .env.example-style placeholder.
        monkeypatch.setenv("MIST_APITOKEN", "realtoken0123456789")
        with pytest.raises(SystemExit):
            MistHelper._preflight_verify_credentials()
        assert "MIST_HOST" in capsys.readouterr().out

    def test_valid_host_and_token_passes(self, monkeypatch):
        """Real non-placeholder host + present token -> returns without exiting."""
        _clear_credential_env(monkeypatch)
        monkeypatch.setenv("MIST_HOST", "api.mist.com")
        monkeypatch.setenv("MIST_APITOKEN", "realtoken0123456789")
        # No SystemExit expected: the call should return None and continue.
        assert MistHelper._preflight_verify_credentials() is None

    def test_login_mode_does_not_require_token(self, monkeypatch):
        """require_token=False (interactive --login) -> a valid host alone passes with no token set."""
        _clear_credential_env(monkeypatch)
        monkeypatch.setenv("MIST_HOST", "api.mist.com")  # WHY: --login authenticates via email/password, no token.
        assert MistHelper._preflight_verify_credentials(require_token=False) is None

    def test_preflight_never_imports_network_libraries(self):
        """SC-004: the preflight helper's source imports neither requests nor mistapi (structural zero-HTTP)."""
        source = inspect.getsource(MistHelper._preflight_verify_credentials)
        assert "import requests" not in source, "preflight must not import requests"
        assert "import mistapi" not in source, "preflight must not import mistapi"

    def test_no_raw_token_leaks_in_failure_message(self, monkeypatch, capsys):
        """SC-005: only redacted token previews (first4...last4) may appear, never the raw token value."""
        _clear_credential_env(monkeypatch)
        monkeypatch.setenv("MIST_HOST", "api.mist.com")
        raw_token = "your_verylongsecret_here"  # WHY: a placeholder token (>=8 chars) so a preview is emitted.
        monkeypatch.setenv("MIST_APITOKEN", raw_token)
        with pytest.raises(SystemExit):
            MistHelper._preflight_verify_credentials()
        out = capsys.readouterr().out
        assert raw_token not in out, "raw token must never appear verbatim in output"
        assert "your...here" in out, "only the redacted first4...last4 preview may appear"
