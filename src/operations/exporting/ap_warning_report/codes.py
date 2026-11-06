"""Match AP trouble codes to the live LED dictionary without inferred meanings."""

from __future__ import annotations

import logging
import math
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


class TroubleCode:
    """Normalize documented numeric trouble evidence and its observation time."""

    @staticmethod
    def normalize(value: object) -> str:
        """Keep zero-padded numeric codes and exclude absent or zero evidence."""
        if value is None or value == "":
            return ""
        if isinstance(value, str) and not value.strip():
            return ""
        if isinstance(value, bool) or not isinstance(value, (str, int)):
            raise ValueError("Invalid AP trouble code type")
        text = str(value).strip()
        if not text.isascii() or not text.isdecimal():
            raise ValueError("Invalid AP trouble code value")
        number = int(text)
        return str(number).zfill(2) if number else ""

    @staticmethod
    def timestamp(value: object) -> str:
        """Convert an available epoch time to UTC without inventing missing time."""
        if value is None:
            return ""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("Invalid AP trouble timestamp type")
        try:
            if not math.isfinite(value) or value < 0:
                raise ValueError("Invalid AP trouble timestamp value")
            return datetime.fromtimestamp(value, tz=UTC).isoformat()
        except (OverflowError, OSError, ValueError):
            raise ValueError("Invalid AP trouble timestamp value") from None


class CodeDefinitions:
    """Validate one live dictionary and retain unknown trouble codes explicitly."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        """Index definitions once so every AP uses the same dictionary."""
        logger.info("Indexing AP trouble definitions")
        if not rows:
            raise ValueError("The AP definition dictionary is empty")
        self._definitions: dict[str, dict[str, str]] = {}
        for row in rows:
            self._add(row)
        logger.debug("Indexed AP trouble definitions records=%d", len(self._definitions))

    def _add(self, row: dict[str, Any]) -> None:
        """Refuse duplicate or incomplete definitions rather than inventing text."""
        if row.get("code") is None or not str(row["code"]).strip():
            raise ValueError("The AP definition dictionary contains a definition without a code")
        code = TroubleCode.normalize(row.get("code"))
        if any(
            not isinstance(row.get(field), str) or not row[field].strip() for field in ("key", "name", "description")
        ):
            raise ValueError("The AP definition dictionary contains an incomplete definition")
        if code in self._definitions:
            raise ValueError("The AP definition dictionary contains a duplicate definition")
        if code:
            self._definitions[code] = {
                "code": code,
                "definition_status": "known",
                "code_key": row["key"],
                "code_name": row["name"],
                "code_description": row["description"],
            }

    def describe(self, code: str) -> dict[str, str]:
        """Return live definition text or an explicit unknown-code indication."""
        if code in self._definitions:
            return dict(self._definitions[code])
        logger.warning("AP trouble code %s has no returned definition", code)
        return {
            "code": code,
            "definition_status": "unknown",
            "code_key": "",
            "code_name": "",
            "code_description": "No definition returned by Mist",
        }
