"""Models and scoring rules for the admin and API token hygiene report."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, fields
from datetime import UTC, datetime
from typing import Any

TOKEN_IDLE_DAYS_ENV = "TOKEN_IDLE_DAYS"
DEFAULT_TOKEN_IDLE_DAYS = 90
ADMIN_COLUMNS = [
    "admin_id",
    "email",
    "name",
    "role_summary",
    "site_scope",
    "two_factor_state",
    "sso_state",
    "password_age_days",
    "invite_expiry",
    "findings",
]
TOKEN_COLUMNS = [
    "id",
    "name",
    "created_by",
    "created_time",
    "last_used",
    "idle_days",
    "privilege_summary",
    "source_ip_restriction_present",
    "findings",
]
WRITE_ROLES = {"superuser", "org_admin", "network_admin"}


@dataclass(frozen=True, slots=True)
class AdminHygieneRow:
    """One administrator row in `AdminHygiene.csv`."""

    admin_id: str
    email: str
    name: str
    role_summary: str
    site_scope: str
    two_factor_state: str
    sso_state: str
    password_age_days: int | str
    invite_expiry: str
    findings: str

    def as_row(self) -> dict[str, Any]:
        """Return the CSV row in dataclass field order."""
        return {field.name: getattr(self, field.name) for field in fields(self)}


@dataclass(frozen=True, slots=True)
class TokenHygieneRow:
    """One token row in `TokenHygiene.csv`."""

    id: str
    name: str
    created_by: str
    created_time: str
    last_used: str
    idle_days: int | str
    privilege_summary: str
    source_ip_restriction_present: str
    findings: str

    def as_row(self) -> dict[str, Any]:
        """Return the CSV row in dataclass field order."""
        return {field.name: getattr(self, field.name) for field in fields(self)}


@dataclass(frozen=True, slots=True)
class HygieneSummary:
    """Console summary counts for the hygiene report."""

    super_users: int
    admins_no_two_factor_no_sso: int
    idle_tokens: int
    unrestricted_write_tokens: int


class AdminTokenHygieneModel:
    """Score Mist administrators and organization API tokens."""

    @staticmethod
    def read_idle_threshold(environ: Mapping[str, str] | None = None) -> int:
        """Return the token idle threshold from the environment."""
        source = environ if environ is not None else os.environ  # WHY: tests can pass an isolated environment.
        raw_value = source.get(TOKEN_IDLE_DAYS_ENV, str(DEFAULT_TOKEN_IDLE_DAYS))  # WHY: default is 90 days.
        try:
            threshold = int(raw_value)  # WHY: the threshold must be numeric for day comparisons.
        except ValueError as error:
            raise ValueError("TOKEN_IDLE_DAYS must be a positive integer") from error
        if threshold <= 0:  # WHY: zero or negative values would mark every token as idle.
            raise ValueError("TOKEN_IDLE_DAYS must be a positive integer")
        return threshold  # WHY: callers use one validated value for all token rows.

    @staticmethod
    def build_admin_rows(admins: list[dict[str, Any]], now: datetime) -> list[AdminHygieneRow]:
        """Return scored admin rows."""
        return [AdminTokenHygieneModel._admin_row(admin, now) for admin in admins]

    @staticmethod
    def build_token_rows(
        tokens: list[dict[str, Any]], now: datetime, idle_threshold_days: int
    ) -> list[TokenHygieneRow]:
        """Return scored token rows."""
        return [AdminTokenHygieneModel._token_row(token, now, idle_threshold_days) for token in tokens]

    @staticmethod
    def summarize(admin_rows: list[AdminHygieneRow], token_rows: list[TokenHygieneRow]) -> HygieneSummary:
        """Return the console summary counts."""
        return HygieneSummary(
            super_users=sum("super_user" in row.findings.split("|") for row in admin_rows),
            admins_no_two_factor_no_sso=sum("no_two_factor_no_sso" in row.findings.split("|") for row in admin_rows),
            idle_tokens=sum("idle_token" in row.findings.split("|") for row in token_rows),
            unrestricted_write_tokens=sum("unrestricted_write_token" in row.findings.split("|") for row in token_rows),
        )

    @staticmethod
    def _admin_row(admin: Mapping[str, Any], now: datetime) -> AdminHygieneRow:
        """Return one scored administrator row."""
        privileges = AdminTokenHygieneModel._privileges(admin)  # WHY: roles and scopes can have multiple entries.
        role_summary = AdminTokenHygieneModel._role_summary(privileges)  # WHY: the report needs stable role text.
        site_scope = AdminTokenHygieneModel._site_scope(privileges)  # WHY: scope explains where access applies.
        two_factor_state = AdminTokenHygieneModel._two_factor_state(admin)  # WHY: local sign-in risk depends on it.
        sso_state = AdminTokenHygieneModel._sso_state(admin)  # WHY: SSO users follow IdP policy.
        findings = AdminTokenHygieneModel._admin_findings(admin, privileges, now, two_factor_state, sso_state)
        return AdminHygieneRow(
            admin_id=AdminTokenHygieneModel._text(admin.get("admin_id")),
            email=AdminTokenHygieneModel._text(admin.get("email")),
            name=AdminTokenHygieneModel._best_name(admin),
            role_summary=role_summary,
            site_scope=site_scope,
            two_factor_state=two_factor_state,
            sso_state=sso_state,
            password_age_days=AdminTokenHygieneModel._age_days(admin.get("password_modified_time"), now),
            invite_expiry=AdminTokenHygieneModel._time_text(admin.get("expire_time"), "unknown"),
            findings="|".join(findings),
        )

    @staticmethod
    def _token_row(token: Mapping[str, Any], now: datetime, idle_threshold_days: int) -> TokenHygieneRow:
        """Return one scored token row without secret key material."""
        safe_token = {key: value for key, value in token.items() if key != "key"}  # WHY: drop secret token material.
        privileges = AdminTokenHygieneModel._privileges(safe_token)  # WHY: token privileges decide write risk.
        idle_days = AdminTokenHygieneModel._token_idle_days(safe_token, now)  # WHY: idle scoring needs one value.
        src_restricted = AdminTokenHygieneModel._has_source_restriction(safe_token)  # WHY: IP limits reduce risk.
        findings = AdminTokenHygieneModel._token_findings(safe_token, privileges, idle_days, idle_threshold_days)
        if AdminTokenHygieneModel._has_org_write(privileges) and not src_restricted:
            findings.append("unrestricted_write_token")  # WHY: broad write access without IP limits is a finding.
        return TokenHygieneRow(
            id=AdminTokenHygieneModel._text(safe_token.get("id")),
            name=AdminTokenHygieneModel._text(safe_token.get("name")),
            created_by=AdminTokenHygieneModel._text(safe_token.get("created_by")),
            created_time=AdminTokenHygieneModel._time_text(safe_token.get("created_time"), "unknown"),
            last_used=AdminTokenHygieneModel._time_text(safe_token.get("last_used"), "never"),
            idle_days=idle_days,
            privilege_summary=AdminTokenHygieneModel._privilege_summary(privileges),
            source_ip_restriction_present=str(src_restricted).lower(),
            findings="|".join(findings),
        )

    @staticmethod
    def _admin_findings(
        admin: Mapping[str, Any],
        privileges: list[Mapping[str, Any]],
        now: datetime,
        two_factor_state: str,
        sso_state: str,
    ) -> list[str]:
        """Return finding labels for one administrator."""
        findings: list[str] = []  # WHY: stable order makes tests and reports predictable.
        if AdminTokenHygieneModel._has_super_user(privileges):  # WHY: Super User access is a headline count.
            findings.append("super_user")
        if two_factor_state in {"disabled", "unknown"} and sso_state == "local":
            findings.append("no_two_factor_no_sso")  # WHY: local sign-in without 2FA is weak access.
        if AdminTokenHygieneModel._is_expired(admin.get("expire_time"), now):
            findings.append("stale_invite")  # WHY: expired invitations need cleanup.
        if AdminTokenHygieneModel._has_unknown_role(privileges):
            findings.append("unknown_role")  # WHY: unknown access must stay visible.
        if two_factor_state == "unknown" and sso_state == "unknown":
            findings.append("unknown_security_state")  # WHY: missing security state needs review.
        return findings  # WHY: the caller joins labels for the CSV.

    @staticmethod
    def _token_findings(
        token: Mapping[str, Any],
        privileges: list[Mapping[str, Any]],
        idle_days: int | str,
        idle_threshold_days: int,
    ) -> list[str]:
        """Return finding labels for one token."""
        findings: list[str] = []  # WHY: stable order makes tests and reports predictable.
        if token.get("last_used") in (None, ""):
            findings.append("never_used")  # WHY: a token with no use history needs operator review.
        if idle_days == "unknown":
            findings.append("age_unknown")  # WHY: missing age prevents idle scoring.
        if isinstance(idle_days, int) and idle_days >= idle_threshold_days:
            findings.append("idle_token")  # WHY: the threshold marks stale access.
        if AdminTokenHygieneModel._has_unknown_role(privileges):
            findings.append("unknown_privilege")  # WHY: unknown token access must stay visible.
        return findings  # WHY: caller can add combined findings before export.

    @staticmethod
    def _privileges(source: Mapping[str, Any]) -> list[Mapping[str, Any]]:
        """Return readable privilege mappings from a source row."""
        privileges = source.get("privileges", [])  # WHY: Mist stores access grants under privileges.
        if not isinstance(privileges, list):  # WHY: malformed data must not break report generation.
            return []  # WHY: no readable privileges yields unknown summaries later.
        return [privilege for privilege in privileges if isinstance(privilege, Mapping)]

    @staticmethod
    def _role_summary(privileges: list[Mapping[str, Any]]) -> str:
        """Return a stable role summary."""
        roles = sorted({AdminTokenHygieneModel._role_key(privilege.get("role")) for privilege in privileges})
        return "|".join(role for role in roles if role) or "unknown"

    @staticmethod
    def _privilege_summary(privileges: list[Mapping[str, Any]]) -> str:
        """Return a stable role and scope summary."""
        summaries = [AdminTokenHygieneModel._privilege_text(privilege) for privilege in privileges]
        return "|".join(sorted(summary for summary in summaries if summary)) or "unknown"

    @staticmethod
    def _privilege_text(privilege: Mapping[str, Any]) -> str:
        """Return one compact privilege summary."""
        role = AdminTokenHygieneModel._role_key(privilege.get("role")) or "unknown"  # WHY: role is mandatory context.
        scope = AdminTokenHygieneModel._scope_key(privilege)  # WHY: scope shows where the role applies.
        return f"{role}:{scope}"  # WHY: compact stable string for CSV and tests.

    @staticmethod
    def _site_scope(privileges: list[Mapping[str, Any]]) -> str:
        """Return the highest visible site scope."""
        scopes = {AdminTokenHygieneModel._scope_key(privilege) for privilege in privileges}
        if "org" in scopes:  # WHY: org scope outranks site-specific grants.
            return "org"
        if "all_sites" in scopes:  # WHY: all-sites scope is broader than selected site grants.
            return "all_sites"
        if "site_groups" in scopes:  # WHY: site groups are a distinct operator scope.
            return "site_groups"
        if "selected_sites" in scopes:  # WHY: site identifiers mean limited site scope.
            return "selected_sites"
        return "unknown"  # WHY: missing privilege scope needs review.

    @staticmethod
    def _scope_key(privilege: Mapping[str, Any]) -> str:
        """Return a normalized scope key."""
        raw_scope = AdminTokenHygieneModel._role_key(privilege.get("scope"))  # WHY: reuse normalization rules.
        if raw_scope in {"org", "organization"}:
            return "org"
        if raw_scope in {"site", "sites"} or privilege.get("site_id"):
            return "selected_sites"
        if raw_scope in {"sitegroup", "sitegroups", "site_group"} or privilege.get("sitegroup_id"):
            return "site_groups"
        if raw_scope in {"all", "all_sites"}:
            return "all_sites"
        if privilege.get("org_id") and not privilege.get("site_id") and not privilege.get("sitegroup_id"):
            return "org"
        if privilege.get("msp_id"):
            return "msp"
        return raw_scope or "unknown"

    @staticmethod
    def _has_super_user(privileges: list[Mapping[str, Any]]) -> bool:
        """Return True when privileges include org-scope Super User access."""
        return any(
            AdminTokenHygieneModel._role_key(privilege.get("role")) == "superuser"
            and AdminTokenHygieneModel._scope_key(privilege) == "org"
            for privilege in privileges
        )

    @staticmethod
    def _has_org_write(privileges: list[Mapping[str, Any]]) -> bool:
        """Return True when privileges include org-scope write access."""
        return any(
            AdminTokenHygieneModel._role_key(privilege.get("role")) in WRITE_ROLES
            and AdminTokenHygieneModel._scope_key(privilege) == "org"
            for privilege in privileges
        )

    @staticmethod
    def _has_unknown_role(privileges: list[Mapping[str, Any]]) -> bool:
        """Return True when any privilege lacks a readable role."""
        return any(not AdminTokenHygieneModel._role_key(privilege.get("role")) for privilege in privileges)

    @staticmethod
    def _two_factor_state(admin: Mapping[str, Any]) -> str:
        """Return the admin two-factor state."""
        if admin.get("two_factor_verified") is True:
            return "verified"
        if admin.get("enable_two_factor") is True:
            return "enabled"
        if admin.get("two_factor_verified") is False or admin.get("enable_two_factor") is False:
            return "disabled"
        return "unknown"

    @staticmethod
    def _sso_state(admin: Mapping[str, Any]) -> str:
        """Return the admin SSO state."""
        if admin.get("via_sso") is True:
            return "sso"
        if admin.get("via_sso") is False:
            return "local"
        return "unknown"

    @staticmethod
    def _token_idle_days(token: Mapping[str, Any], now: datetime) -> int | str:
        """Return idle days from last use or token creation."""
        reference = token.get("last_used") or token.get("created_time")  # WHY: never-used tokens use created time.
        age = AdminTokenHygieneModel._age_days(reference, now)  # WHY: convert epoch to whole days.
        return age if isinstance(age, int) else "unknown"

    @staticmethod
    def _age_days(value: Any, now: datetime) -> int | str:
        """Return whole days between an epoch value and now."""
        parsed = AdminTokenHygieneModel._epoch(value)  # WHY: source uses epoch seconds or milliseconds.
        if parsed is None:
            return "unknown"
        seconds = max(0.0, now.timestamp() - parsed.timestamp())  # WHY: future timestamps should not go negative.
        return int(seconds // 86400)  # WHY: whole days are easier to compare and read.

    @staticmethod
    def _time_text(value: Any, empty_text: str) -> str:
        """Return readable UTC time text for an epoch value."""
        parsed = AdminTokenHygieneModel._epoch(value)  # WHY: source time can be missing or epoch formatted.
        return parsed.isoformat() if parsed is not None else empty_text

    @staticmethod
    def _is_expired(value: Any, now: datetime) -> bool:
        """Return True when an epoch value is before now."""
        parsed = AdminTokenHygieneModel._epoch(value)  # WHY: invite expiry is an epoch value when present.
        return bool(parsed and parsed < now)  # WHY: past expiry means a stale invitation or account.

    @staticmethod
    def _epoch(value: Any) -> datetime | None:
        """Return an epoch value as a UTC datetime."""
        if value in (None, ""):
            return None
        try:
            number = float(value)  # WHY: Mist times can arrive as integer-like strings.
        except (TypeError, ValueError):
            return None
        if number > 1_000_000_000_000:
            number /= 1000  # WHY: values above this bound are epoch milliseconds.
        return datetime.fromtimestamp(number, tz=UTC)

    @staticmethod
    def _has_source_restriction(token: Mapping[str, Any]) -> bool:
        """Return True when the token has one or more source IP limits."""
        src_ips = token.get("src_ips")  # WHY: Mist stores source limits under src_ips.
        return isinstance(src_ips, list) and bool(src_ips)

    @staticmethod
    def _role_key(value: Any) -> str:
        """Return a normalized role or scope key."""
        return str(value or "").strip().lower().replace(" ", "_")

    @staticmethod
    def _text(value: Any) -> str:
        """Return text for optional source values."""
        return "" if value is None else str(value)

    @staticmethod
    def _best_name(admin: Mapping[str, Any]) -> str:
        """Return the best available admin display name."""
        name = AdminTokenHygieneModel._text(admin.get("name"))  # WHY: display name is preferred when present.
        if name:
            return name
        parts = [
            AdminTokenHygieneModel._text(admin.get("first_name")),
            AdminTokenHygieneModel._text(admin.get("last_name")),
        ]
        return " ".join(part for part in parts if part)
