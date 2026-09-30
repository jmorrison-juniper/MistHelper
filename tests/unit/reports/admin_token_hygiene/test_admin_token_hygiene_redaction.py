"""Redaction tests for the admin token hygiene report."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from src.reports.admin_token_hygiene.model import AdminTokenHygieneModel


def test_token_key_never_reaches_rows_or_logs(caplog: object) -> None:
    """A token key value must not appear in rows or log lines."""
    sentinel = "MIST_TOKEN_KEY_SHOULD_NOT_LEAK"
    token = {"id": "tok-1", "name": "robot", "created_time": 1_700_000_000, "last_used": 1_700_000_000, "key": sentinel}
    logger = logging.getLogger("src.reports.admin_token_hygiene.model")
    with caplog.at_level(logging.DEBUG):
        rows = AdminTokenHygieneModel.build_token_rows([token], datetime(2026, 9, 29, tzinfo=UTC), 90)
        logger.debug("Rows built count=%d", len(rows))
    assert sentinel not in str(rows[0].as_row())
    assert sentinel not in caplog.text
