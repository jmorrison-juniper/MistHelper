"""Tests for the single TLS verification control.

These tests prove issue #1914. Certificate verification must be on
unless the operator opts out, and a run that skips the check must say
so in the log.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from src.inventory.csv_comparator import ComparatorFlags
from src.site.address_audit.audit_engine import AddressAuditEngine
from src.utils.tls_policy import SKIP_VERIFY_ENV_VAR, TLSVerificationPolicy

REPO_ROOT = Path(__file__).resolve().parents[3]  # Repository root, for the source sweep test.

# These files must never disable certificate verification again.
GUARDED_SCRIPTS = (
    "scripts/test_ssr.py",
    "scripts/debug_html.py",
    "scripts/mist_ideas_scraper_ssr.py",
)

# A match on any token means a bypass returned to the tree.
BYPASS_TOKENS = re.compile(r"CERT_NONE|check_hostname\s*=\s*False")


@pytest.fixture(autouse=True)
def _clear_policy_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """Give every test an unset variable and a clean warning latch."""
    monkeypatch.delenv(SKIP_VERIFY_ENV_VAR, raising=False)  # Absent is the default operator state.
    TLSVerificationPolicy.reset()  # Clear the latch so each test sees its own warning.


class TestTLSVerificationPolicy:
    """Cover the default, the opt in, and the operator warning."""

    def test_default_verifies(self) -> None:
        """An unset variable keeps certificate verification on."""
        assert TLSVerificationPolicy.skip_verification() is False  # Secure default.
        assert TLSVerificationPolicy.verify_enabled() is True  # Positive form agrees.

    @pytest.mark.parametrize("token", ["true", "TRUE", "1", "yes", "on"])
    def test_opt_in_disables(self, token: str, monkeypatch: pytest.MonkeyPatch) -> None:
        """A recognized token turns the check off."""
        monkeypatch.setenv(SKIP_VERIFY_ENV_VAR, token)  # Operator opts out explicitly.
        assert TLSVerificationPolicy.skip_verification() is True  # Opt in honored.

    @pytest.mark.parametrize("token", ["false", "0", "no", "off", "maybe", ""])
    def test_unrecognized_stays_secure(self, token: str, monkeypatch: pytest.MonkeyPatch) -> None:
        """An unknown or falsey value keeps the check on."""
        monkeypatch.setenv(SKIP_VERIFY_ENV_VAR, token)  # Includes a typo case.
        assert TLSVerificationPolicy.skip_verification() is False  # Fail secure.

    def test_disabled_run_warns(self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
        """A run that skips the check logs one WARNING."""
        monkeypatch.setenv(SKIP_VERIFY_ENV_VAR, "true")  # Turn the check off.
        with caplog.at_level("WARNING"):  # Capture the operator warning.
            TLSVerificationPolicy.skip_verification()  # Trigger the decision and the log.
        assert any("verification is OFF" in r.message for r in caplog.records)  # Warning present.

    def test_warning_is_not_repeated(self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
        """A loop does not flood the log with the same warning."""
        monkeypatch.setenv(SKIP_VERIFY_ENV_VAR, "true")  # Turn the check off.
        with caplog.at_level("WARNING"):  # Capture every warning record.
            for _ in range(5):  # Simulate a caller inside a loop.
                TLSVerificationPolicy.skip_verification()  # Repeated decision.
        warnings = [r for r in caplog.records if "verification is OFF" in r.message]
        assert len(warnings) == 1  # Exactly one warning per run.

    def test_secure_run_does_not_warn(self, caplog: pytest.LogCaptureFixture) -> None:
        """A normal run stays quiet, so the warning keeps its meaning."""
        with caplog.at_level("WARNING"):  # Capture any warning.
            TLSVerificationPolicy.skip_verification()  # Default secure decision.
        assert not [r for r in caplog.records if "verification is OFF" in r.message]  # Silent.


class TestCallSiteDefaults:
    """Prove every call site now defaults to secure."""

    def test_audit_engine_defaults_secure(self) -> None:
        """The address audit verifies certificates when nothing is set."""
        assert AddressAuditEngine._skip_ssl_verify() is False  # Was True before issue #1914.

    def test_comparator_flags_default_secure(self) -> None:
        """The inventory comparator verifies certificates by default."""
        assert ComparatorFlags().skip_ssl_verify is False  # Was True before issue #1914.


class TestNoBypassReturns:
    """Guard the tree so a future edit cannot reintroduce a bypass."""

    @pytest.mark.parametrize("relative_path", GUARDED_SCRIPTS)
    def test_script_holds_no_bypass(self, relative_path: str) -> None:
        """A guarded script must not disable certificate verification."""
        source = (REPO_ROOT / relative_path).read_text(encoding="utf-8")  # Read the tracked file.
        assert not BYPASS_TOKENS.search(source), f"{relative_path} reintroduced a TLS bypass"
