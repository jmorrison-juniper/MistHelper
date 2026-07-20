"""Credential/config preflight unit tests (feature 1020, User Story 3).

Verifies ``_preflight_verify_credentials()`` fails closed - before any mistapi/
requests call - when host/token config is missing or a placeholder, with a
redacted, actionable message referencing ``deploy/.env.example`` and the exact
env var names the code reads. Zero network, zero real credentials; the
zero-HTTP guarantee is proven structurally (the helper imports no network lib).
See ``specs/1020-safe-test-clean-run/contracts/preflight_failure_contract.md``.
"""

from __future__ import annotations

import argparse
import inspect
import logging
from unittest.mock import MagicMock

import pytest

import MistHelper

_CREDENTIAL_ENV_VARS = ("MIST_HOST", "MIST_APITOKEN", "MIST_API_TOKEN")


def _clear_credential_env(monkeypatch):
    """Remove all host/token env vars so each test controls the exact configuration."""
    for name in _CREDENTIAL_ENV_VARS:  # WHY: guarantee a clean slate regardless of the ambient environment.
        monkeypatch.delenv(name, raising=False)


class TestCredentialPreflight:
    """Unit tests for the fail-closed host/token preflight."""

    def test_missing_token_fails_closed_with_actionable_message(self, monkeypatch, caplog):
        """No token env var set -> exits non-zero, naming the token vars and deploy/.env.example."""
        _clear_credential_env(monkeypatch)  # WHY: host now defaults to api.mist.com; only the token is missing.
        caplog.set_level(logging.ERROR)  # WHY: preflight failure emits via logging.error since #886 slice 11.
        with pytest.raises(SystemExit) as exc_info:
            MistHelper._preflight_verify_credentials()
        assert exc_info.value.code == 1
        out = caplog.text
        assert "MIST_APITOKEN" in out and "MIST_API_TOKEN" in out, "must name the token env vars"
        assert "deploy/.env.example" in out, "must reference the template file to copy"
        assert "to .env" in out, "must direct operators to the root .env file the runtime loads"

    def test_blank_host_fails_closed(self, monkeypatch, caplog):
        """MIST_HOST explicitly blank -> exits non-zero with a specific host message (token present)."""
        _clear_credential_env(monkeypatch)
        monkeypatch.setenv("MIST_HOST", "")  # WHY: explicit blank host reproduces the malformed-URL defect.
        monkeypatch.setenv("MIST_APITOKEN", "realtoken0123456789")  # WHY: a real token isolates the host failure.
        caplog.set_level(logging.ERROR)  # WHY: preflight failure emits via logging.error since #886 slice 11.
        with pytest.raises(SystemExit) as exc_info:
            MistHelper._preflight_verify_credentials()
        assert exc_info.value.code == 1
        assert "MIST_HOST" in caplog.text

    def test_placeholder_host_fails_closed(self, monkeypatch, caplog):
        """MIST_HOST left at a copy-paste placeholder -> exits non-zero with a host message."""
        _clear_credential_env(monkeypatch)
        monkeypatch.setenv("MIST_HOST", "your_host_here")  # WHY: unedited .env.example-style placeholder.
        monkeypatch.setenv("MIST_APITOKEN", "realtoken0123456789")
        caplog.set_level(logging.ERROR)  # WHY: preflight failure emits via logging.error since #886 slice 11.
        with pytest.raises(SystemExit):
            MistHelper._preflight_verify_credentials()
        assert "MIST_HOST" in caplog.text

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

    def test_no_raw_token_leaks_in_failure_message(self, monkeypatch, caplog):
        """SC-005: only redacted token previews (first4...last4) may appear, never the raw token value."""
        _clear_credential_env(monkeypatch)
        monkeypatch.setenv("MIST_HOST", "api.mist.com")
        raw_token = "your_verylongsecret_here"  # WHY: a placeholder token (>=8 chars) so a preview is emitted.
        monkeypatch.setenv("MIST_APITOKEN", raw_token)
        caplog.set_level(logging.ERROR)  # WHY: preflight failure emits via logging.error since #886 slice 11.
        with pytest.raises(SystemExit):
            MistHelper._preflight_verify_credentials()
        out = caplog.text
        assert raw_token not in out, "raw token must never appear verbatim in output"
        assert "your...here" in out, "only the redacted first4...last4 preview may appear"

    @pytest.mark.parametrize("mode_name", ("test", "testinteractive"))
    def test_systematic_org_preflight_precedes_session_initialization(self, monkeypatch, mode_name):
        """Systematic runs resolve org_id before constructing a session that could issue MSP API calls."""
        _clear_credential_env(
            monkeypatch
        )  # WHY: control every credential value used by the local host/token preflight.
        monkeypatch.setenv("MIST_HOST", "api.mist.com")  # WHY: valid host isolates the org-id preflight ordering.
        monkeypatch.setenv(
            "MIST_APITOKEN", "realtoken0123456789"
        )  # WHY: non-placeholder token passes local validation.
        org_preflight = MagicMock(
            side_effect=SystemExit(1)
        )  # WHY: simulate missing org_id without reaching config or network code.
        session_initializer = (
            MagicMock()
        )  # WHY: prove no session construction occurs after org preflight rejects the run.
        monkeypatch.setattr(
            MistHelper.ConfigUtils, "get_cached_or_prompted_org_id", org_preflight
        )  # WHY: patch exact startup lookup.
        monkeypatch.setattr(
            MistHelper.MistSessionInitializer, "initialize", session_initializer
        )  # WHY: make API-session work observable.
        args = argparse.Namespace(  # WHY: mirror parser flags while exercising both systematic modes.
            login=False,
            test=mode_name == "test",
            testinteractive=mode_name == "testinteractive",
        )

        with pytest.raises(SystemExit) as exc_info:
            MistHelper._establish_mist_session(args)

        assert (
            exc_info.value.code == 1
        )  # WHY: org preflight preserves the established non-zero configuration failure contract.
        org_preflight.assert_called_once()  # WHY: systematic startup resolves org_id before session construction.
        session_initializer.assert_not_called()  # WHY: no session/MSP HTTP path may begin when org_id is unavailable.
