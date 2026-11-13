"""Shared fixtures for alert digest tests."""

from __future__ import annotations  # Enable modern annotations without runtime imports.

from dataclasses import dataclass  # Create compact fake response objects.
from typing import Any  # Accept raw fake response payloads.

ORG_ID = "00000000-0000-4000-8000-000000003561"  # Synthetic organization identifier.


@dataclass
class FakeResponse:
    """A stand-in for a mistapi response."""

    status_code: int | None  # Preserve the fake HTTP status.
    data: Any = None  # Preserve the fake response body.


def definition(key: str = "device_down", group: str = "infrastructure", severity: str = "warn") -> dict[str, Any]:
    """Return one synthetic alarm definition."""
    return {"key": key, "group": group, "severity": severity, "display": key.replace("_", " "), "fields": []}


def alarm(number: int = 1, **overrides: Any) -> dict[str, Any]:
    """Return one synthetic alarm row."""
    row: dict[str, Any] = {
        "id": f"alarm-{number}",
        "type": "device_down",
        "site_id": "site-1",
        "site_name": "Lab Site",
        "severity": "warn",
        "count": 1,
        "timestamp": 1_700_000_000 + number,
        "last_seen": 1_700_000_100 + number,
        "hostname": f"switch-{number}",
        "acked": False,
    }
    row.update(overrides)
    return row


def alarm_page(rows: list[Any], next_link: str | None = None) -> FakeResponse:
    """Return one fake alarm search page."""
    data: dict[str, Any] = {"results": list(rows), "total": len(rows), "limit": 1000}
    if next_link is not None:
        data["next"] = next_link
    return FakeResponse(200, data)
