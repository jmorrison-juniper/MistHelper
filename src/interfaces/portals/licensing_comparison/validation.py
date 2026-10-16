"""Validate operator-entered organization and license data before use."""

from __future__ import annotations

import re
from typing import Any


class ManualRowValidator:
    """Validate session-only organization rows and purchased license counts."""

    _number_pattern = re.compile(r"[A-Z0-9_-]{1,32}")

    @classmethod
    def _valid_count_map(cls, value: Any) -> bool:
        """Accept maps with supported names and non-negative whole counts."""
        return isinstance(value, dict) and all(
            isinstance(key, str) and cls._number_pattern.fullmatch(key) and type(count) is int and count >= 0
            for key, count in value.items()
        )

    @classmethod
    def validate_manual_rows(
        cls,
        rows: Any,
        choices: list[dict[str, str]],
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Validate manual organization rows without making Mist requests."""
        if not isinstance(rows, list):
            return [], "Manual rows must be a list."
        names = {choice["name"].casefold() for choice in choices}
        row_ids: set[str] = set()
        clean_rows: list[dict[str, Any]] = []
        for row in rows:
            clean_row, error = cls._validate_manual_row(row, names, row_ids)
            if error:
                return [], error
            clean_rows.append(clean_row)
        return clean_rows, None

    @classmethod
    def _validate_manual_row(
        cls,
        row: Any,
        names: set[str],
        row_ids: set[str],
    ) -> tuple[dict[str, Any], str | None]:
        """Validate one manual organization and update duplicate trackers."""
        row_id, name, identity_error = cls._manual_identity(row, names, row_ids)
        if identity_error:
            return {}, identity_error
        if row_id is None or name is None:
            return {}, "Each manual row needs a valid identifier and name."
        licenses, inventory = row.get("licenses", {}), row.get("inventory", {})
        if not cls._valid_count_map(licenses) or not cls._valid_count_map(inventory):
            return {}, "Manual license and inventory counts must be non-negative whole numbers."
        row_ids.add(row_id)
        names.add(name.casefold())
        return {
            "org_id": row_id,
            "name": name,
            "source": "manual",
            "licenses": licenses,
            "inventory": inventory,
        }, None

    @staticmethod
    def _manual_identity(
        row: Any,
        names: set[str],
        row_ids: set[str],
    ) -> tuple[str | None, str | None, str | None]:
        """Validate a manual row identifier and a unique organization name."""
        if not isinstance(row, dict):
            return None, None, "Each manual row must be an object."
        row_id, name = row.get("row_id"), row.get("name")
        if not isinstance(row_id, str) or not re.fullmatch(r"manual-[A-Za-z0-9_-]{1,64}", row_id):
            return None, None, "Each manual row needs a valid row_id."
        if row_id in row_ids:
            return None, None, "Manual row identifiers must be unique."
        if not isinstance(name, str) or not name.strip() or len(name) > 120:
            return None, None, "Each manual row needs a name of 1 to 120 characters."
        normalized_name = name.strip()
        if normalized_name.casefold() in names:
            return None, None, "Manual organization names must be unique."
        return row_id, normalized_name, None

    @classmethod
    def validate_purchases(
        cls,
        purchases: Any,
        row_ids: set[str],
    ) -> tuple[dict[str, dict[str, int]], str | None]:
        """Validate purchased counts and their organization keys."""
        if not isinstance(purchases, dict):
            return {}, "Purchased amounts must be an object."
        # Never accept purchase rows for organizations outside this comparison.
        if any(not isinstance(row_id, str) or row_id not in row_ids for row_id in purchases):
            return {}, "Purchased amounts name an organization that is not in this comparison."
        clean_purchases: dict[str, dict[str, int]] = {}
        for row_id, values in purchases.items():
            if not cls._valid_count_map(values):
                return {}, "Purchased amounts must use supported license names and non-negative whole numbers."
            clean_purchases[row_id] = values
        return clean_purchases, None


class OrganizationIdValidator:
    """Validate organization ID arrays before the service reads Mist data."""

    @staticmethod
    def validate(value: Any) -> tuple[list[str] | None, str | None]:
        """Return valid unique organization IDs or an input error."""
        if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
            return None, "Organization IDs must be a list of non-empty strings."
        if len(set(value)) != len(value):
            return None, "The organization list contains duplicate IDs."
        return value, None
