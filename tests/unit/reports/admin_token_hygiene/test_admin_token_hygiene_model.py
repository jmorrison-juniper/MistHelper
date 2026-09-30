"""Unit tests for admin and token hygiene scoring."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.reports.admin_token_hygiene.model import AdminTokenHygieneModel

NOW = datetime(2026, 9, 29, tzinfo=UTC)
TEN_DAYS_AGO = int(NOW.timestamp()) - 864000
ONE_HUNDRED_DAYS_AGO = int(NOW.timestamp()) - 8_640_000


def test_admin_superuser_counts_from_org_scope_privilege() -> None:
    """A Super User privilege at org scope must count in the summary."""
    admins = [{"email": "admin@example.net", "privileges": [{"role": "superuser", "scope": "org"}]}]
    rows = AdminTokenHygieneModel.build_admin_rows(admins, NOW)
    summary = AdminTokenHygieneModel.summarize(rows, [])
    assert rows[0].findings == "super_user|unknown_security_state"
    assert summary.super_users == 1


def test_admin_without_two_factor_and_sso_counts() -> None:
    """A local admin without two-factor authentication must count in the summary."""
    admins = [{"email": "local@example.net", "enable_two_factor": False, "via_sso": False, "privileges": []}]
    rows = AdminTokenHygieneModel.build_admin_rows(admins, NOW)
    summary = AdminTokenHygieneModel.summarize(rows, [])
    assert "no_two_factor_no_sso" in rows[0].findings
    assert summary.admins_no_two_factor_no_sso == 1


def test_admin_expired_invite_adds_stale_invite() -> None:
    """An expired invite must add the stale_invite finding."""
    admins = [{"email": "invite@example.net", "expire_time": TEN_DAYS_AGO, "privileges": []}]
    rows = AdminTokenHygieneModel.build_admin_rows(admins, NOW)
    assert "stale_invite" in rows[0].findings
    assert rows[0].invite_expiry.startswith("2026-09-19")


def test_never_used_token_uses_age_for_idle_days() -> None:
    """A never-used token must use token age as idle days and mark never_used."""
    tokens = [{"id": "tok-1", "name": "robot", "created_time": ONE_HUNDRED_DAYS_AGO, "privileges": []}]
    rows = AdminTokenHygieneModel.build_token_rows(tokens, NOW, 90)
    assert rows[0].idle_days == 100
    assert "never_used" in rows[0].findings
    assert "idle_token" in rows[0].findings


def test_unrestricted_write_token_requires_org_write_and_no_source_limit() -> None:
    """Only org-wide write tokens without source IP limits are unrestricted write tokens."""
    tokens = [
        {"id": "tok-1", "name": "wide", "privileges": [{"role": "org_admin", "scope": "org"}]},
        {
            "id": "tok-2",
            "name": "limited",
            "privileges": [{"role": "org_admin", "scope": "org"}],
            "src_ips": ["192.0.2.1"],
        },
        {"id": "tok-3", "name": "read", "privileges": [{"role": "observer", "scope": "org"}]},
    ]
    rows = AdminTokenHygieneModel.build_token_rows(tokens, NOW, 90)
    assert "unrestricted_write_token" in rows[0].findings
    assert "unrestricted_write_token" not in rows[1].findings
    assert "unrestricted_write_token" not in rows[2].findings


def test_token_idle_threshold_reads_environment() -> None:
    """TOKEN_IDLE_DAYS must override the default threshold when set."""
    assert AdminTokenHygieneModel.read_idle_threshold({}) == 90
    assert AdminTokenHygieneModel.read_idle_threshold({"TOKEN_IDLE_DAYS": "30"}) == 30


def test_token_idle_threshold_rejects_invalid_environment() -> None:
    """TOKEN_IDLE_DAYS must fail clearly when it is invalid."""
    with pytest.raises(ValueError, match="TOKEN_IDLE_DAYS"):
        AdminTokenHygieneModel.read_idle_threshold({"TOKEN_IDLE_DAYS": "bad"})
