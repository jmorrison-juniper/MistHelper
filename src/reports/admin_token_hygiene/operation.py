"""Operation entry point for menu 273 admin and API token hygiene."""

from __future__ import annotations

import csv
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.config.source_dependency_resolver import SourceDependencyResolver
from src.reports.admin_token_hygiene.client import AdminTokenHygieneClient
from src.reports.admin_token_hygiene.model import (
    ADMIN_COLUMNS,
    TOKEN_COLUMNS,
    AdminHygieneRow,
    AdminTokenHygieneModel,
    HygieneSummary,
    TokenHygieneRow,
)

logger = logging.getLogger(__name__)

ADMIN_FILENAME = "AdminHygiene.csv"
API_CREDENTIAL_FILENAME = "TokenHygiene.csv"
ADMIN_ENDPOINT_NAME = "adminTokenHygieneAdmins"
API_CREDENTIAL_ENDPOINT_NAME = "adminTokenHygieneTokens"


class AdminTokenHygieneReport:
    """Run the admin and API token hygiene report."""

    resolver: Any = SourceDependencyResolver
    client_class = AdminTokenHygieneClient
    model = AdminTokenHygieneModel

    @classmethod
    def _resolve_org_id(cls) -> str:
        """Return the active organization identifier."""
        logger.info("Admin token hygiene resolves the organization")  # WHY: action log before resolver call.
        org_id = cls.resolver.ConfigUtils.get_cached_or_prompted_org_id()  # WHY: use the shared org resolver.
        logger.debug("Admin token hygiene resolved org=%s", org_id)  # WHY: identifier is not a secret.
        return str(org_id)  # WHY: client paths need text values.

    @classmethod
    def _resolve_session(cls) -> Any:
        """Return the active Mist API session."""
        logger.info("Admin token hygiene resolves the Mist API session")  # WHY: action log before session read.
        session = cls.resolver.apisession  # WHY: use the shared session held by MistHelper.
        logger.debug("Admin token hygiene session present=%s", session is not None)  # WHY: no token data in logs.
        return session  # WHY: the client uses this object for SDK calls.

    @staticmethod
    def _rows(values: list[AdminHygieneRow] | list[TokenHygieneRow]) -> list[dict[str, Any]]:
        """Return export rows from dataclass records."""
        return [value.as_row() for value in values]  # WHY: DataExporter writes dictionaries.

    @classmethod
    def _write_empty_csv(cls, filename: str, fieldnames: list[str]) -> None:
        """Write only the CSV header when the exporter rejects empty input."""
        path = Path("data") / filename  # WHY: bare report files belong under data/.
        logger.info("Writing empty hygiene CSV header to %s", path)  # WHY: action log before file write.
        path.parent.mkdir(parents=True, exist_ok=True)  # WHY: a new worktree can have no data directory.
        with path.open("w", newline="", encoding="utf-8") as csv_file:  # WHY: newline keeps CSV portable.
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)  # WHY: fieldnames define the header order.
            writer.writeheader()  # WHY: empty source data still needs a readable report contract.
        logger.debug("Wrote empty hygiene CSV header to %s", path)  # WHY: result summary after file write.

    @classmethod
    def _export_rows(cls, rows: list[dict[str, Any]], filename: str, endpoint: str, fieldnames: list[str]) -> bool:
        """Write report rows through the shared exporter."""
        if not rows:  # WHY: the shared exporter intentionally skips empty input.
            cls._write_empty_csv(filename, fieldnames)  # WHY: acceptance requires a header-only CSV.
            return True  # WHY: the header file is the expected empty report.
        logger.info("Writing %d hygiene rows to %s", len(rows), filename)  # WHY: action log before export.
        written = cls.resolver.DataExporter.write_with_format_selection(  # WHY: use shared output backends.
            rows,
            filename,
            api_function_name=endpoint,
            fieldnames=fieldnames,
        )
        logger.debug("Hygiene export finished file=%s written=%s", filename, written)  # WHY: result summary.
        return bool(written)  # WHY: caller reports export failures.

    @staticmethod
    def _log_summary(summary: HygieneSummary) -> None:
        """Log the operator summary."""
        logger.info("Admin hygiene Super Users: %d", summary.super_users)  # WHY: required summary count.
        logger.info(  # WHY: required summary count for local weak sign-in.
            "Admin hygiene admins with no two-factor authentication and no SSO: %d",
            summary.admins_no_two_factor_no_sso,
        )
        logger.info("Token hygiene idle tokens: %d", summary.idle_tokens)  # WHY: required token stale count.
        logger.info(  # WHY: required token broad-access count.
            "Token hygiene unrestricted write tokens: %d",
            summary.unrestricted_write_tokens,
        )

    @classmethod
    def run(cls) -> None:
        """Fetch, score, summarize, and export admin and token hygiene."""
        logger.info("Menu #273: Starting admin and API token hygiene report")  # WHY: name the menu row.
        org_id = cls._resolve_org_id()  # WHY: every client call needs the organization identifier.
        client = cls.client_class(cls._resolve_session(), org_id)  # WHY: one client owns the SDK call surface.
        threshold = cls.model.read_idle_threshold()  # WHY: one validated threshold applies to all token rows.
        now = datetime.now(tz=UTC)  # WHY: one timestamp makes report ages consistent.
        admins = client.list_admins()  # WHY: read administrators before scoring admin risk.
        tokens = client.list_tokens()  # WHY: read tokens before scoring token risk.
        settings = client.get_settings()  # WHY: password policy context is read for future report extension.
        logger.debug("Admin token hygiene settings present=%s", bool(settings))  # WHY: count context only.
        admin_rows = cls.model.build_admin_rows(admins, now)  # WHY: convert source admins into safe rows.
        token_rows = cls.model.build_token_rows(tokens, now, threshold)  # WHY: remove token keys before export.
        summary = cls.model.summarize(admin_rows, token_rows)  # WHY: console output needs aggregate counts.
        cls._log_summary(summary)  # WHY: operator reads the outcome before opening files.
        admin_written = cls._export_rows(cls._rows(admin_rows), ADMIN_FILENAME, ADMIN_ENDPOINT_NAME, ADMIN_COLUMNS)
        token_written = cls._export_rows(
            cls._rows(token_rows),
            API_CREDENTIAL_FILENAME,
            API_CREDENTIAL_ENDPOINT_NAME,
            TOKEN_COLUMNS,
        )
        if not admin_written or not token_written:  # WHY: a failed write must not look successful.
            raise RuntimeError("Admin token hygiene report could not write one or more output files")
        logger.info("Menu #273: Admin and API token hygiene report complete")  # WHY: completion log.
