"""Provide a settings-only SDK session double for offline CLI and portal journeys."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

ORG_ID = "00000000-0000-0000-0000-000000000001"
SITE_ID = "00000000-0000-0000-0000-000000000002"
OTHER_SITE_ID = "00000000-0000-0000-0000-000000000003"


class SettingsSession:
    """Exercise real SDK request construction without any network transport."""

    def __init__(self, data_directory: Path) -> None:
        """Hold mock full settings, request evidence, and failure controls."""
        self.settings: dict[str, dict[str, Any]] = {
            f"/api/v1/orgs/{ORG_ID}/setting": {
                "auto_upgrade": {"enabled": False, "custom_versions": {"AP41": "old"}},
                "ssr": {"conductor_token": "private-fixture", "disable_stats": True},
                "allow_mist": False,
            },
            f"/api/v1/sites/{SITE_ID}/setting": {
                "auto_upgrade": {"enabled": False},
                "switch": {"auto_upgrade": {"enabled": True}, "networks": {"main": {"vlan_id": 10}}},
                "ssr": {"auto_upgrade": {"enabled": False}, "conductor_token": "private-fixture"},
                "juniper_srx": {"auto_upgrade": {"enabled": False}, "gateways": []},
                "allow_mist": True,
            },
            f"/api/v1/sites/{OTHER_SITE_ID}/setting": {"allow_mist": False},
        }
        self.writes: list[tuple[str, dict[str, Any]]] = []
        self.reads: list[tuple[str, dict[str, str]]] = []
        self.data_directory = data_directory
        self.fail_write: str | None = None
        self.fail_read: str | None = None
        self.ignore_write = False
        self.status = 503

    def get_cloud(self) -> str:
        """Return the SDK cloud identity used by operation ownership checks."""
        return "api.mist.com"

    def mist_get(self, uri: str, query: dict[str, str] | None = None) -> SimpleNamespace:
        """Return deterministic catalog, inventory, site, or local-setting records."""
        self.reads.append((uri, query or {}))
        data: Any
        if uri == self.fail_read:
            return SimpleNamespace(status_code=self.status, data={"error": "private-fixture"}, next=None)
        if uri in self.settings:
            data = deepcopy(self.settings[uri])
        elif uri.endswith("/sites"):
            data = [{"id": SITE_ID, "name": "First"}, {"id": OTHER_SITE_ID, "name": "Inherited"}]
        elif uri.endswith("/ssr/versions"):
            data = [{"package": "SSR", "version": "6.3.0"}]
        elif uri.endswith("/inventory"):
            data = [
                {"model": "AP41", "type": "ap"},
                {"model": "EX4400", "type": "switch"},
                {"model": "SSR120", "type": "gateway"},
                {"model": "SRX320", "type": "gateway"},
            ]
        elif uri == "/api/v1/const/device_models":
            data = [{"model": "SSR120", "type": "gateway"}, {"model": "SSR130", "type": "gateway"}]
        elif uri == f"/api/v1/orgs/{ORG_ID}":
            data = {"id": ORG_ID, "name": "Fixture Organization"}
        elif uri == "/api/v1/self/usage":
            data = {"requests": 0, "request_limit": 5000}
        elif uri.endswith("/devices/versions"):
            model = {"ap": "AP41", "switch": "EX4400", "gateway": "SRX320"}[(query or {}).get("type", "ap")]
            data = [{"model": model, "version": "new"}, {"model": model, "version": "stable"}]
        elif uri.endswith("/self"):
            data = {"privileges": []}
        else:
            raise AssertionError(f"Unpermitted SDK read: {uri}")
        return SimpleNamespace(status_code=200, data=data, next=None)

    def mist_put(self, uri: str, body: dict[str, Any]) -> SimpleNamespace:
        """Require a verified full backup before accepting a settings-only write."""
        assert uri.endswith("/setting"), f"A non-settings write was attempted: {uri}"
        assert list((self.data_directory / ".firmware-policy-backups").glob("*.json")), "No backup precedes the write"
        self.writes.append((uri, deepcopy(body)))
        if uri == self.fail_write:
            return SimpleNamespace(status_code=self.status, data={"error": "private-fixture"})
        if not self.ignore_write:
            for key, value in body.items():
                if key.startswith("-"):
                    self.settings[uri].pop(key[1:], None)
                else:
                    self.settings[uri][key] = deepcopy(value)
        return SimpleNamespace(status_code=200, data=deepcopy(self.settings[uri]))
