"""Provide schema-valid complete settings and a settings-only SDK fixture."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from src.operations.execution.firmware_policy.recovery.backup import PolicyBackup
from src.operations.execution.firmware_policy.recovery.bundle import BundleFiles
from src.operations.execution.firmware_policy.recovery.workflow import RestoreWorkflow
from src.operations.execution.firmware_policy.sdk import PolicyApi
from tests.unit.firmware_policy.fakes import ORG_ID, SITE_ID, SettingsSession


class RestoreSession(SettingsSession):
    """Record real SDK calls using schema-valid mock organization and site settings."""

    def __init__(self, directory: Path) -> None:
        """Create isolated current values and an unchanged predecessor backup."""
        super().__init__(directory)
        self.cloud = "api.mist.com"
        self.settings = {
            f"/api/v1/orgs/{ORG_ID}/setting": {
                "org_id": ORG_ID,
                "allow_mist": False,
                "auto_upgrade": {"enabled": True},
                "ssr": {"conductor_token": "private-fixture"},
            },
            f"/api/v1/sites/{SITE_ID}/setting": {
                "org_id": ORG_ID,
                "site_id": SITE_ID,
                "auto_upgrade": {"enabled": True},
                "dns_servers": ["1.1.1.1"],
            },
        }
        self.backup = PolicyBackup(directory)
        self.saved = [
            {
                "scope": "org",
                "id": ORG_ID,
                "settings": {
                    **deepcopy(self.settings[f"/api/v1/orgs/{ORG_ID}/setting"]),
                    "allow_mist": True,
                    "auto_upgrade": {"enabled": False},
                },
            },
            {
                "scope": "site",
                "id": SITE_ID,
                "settings": {"org_id": ORG_ID, "site_id": SITE_ID, "dns_servers": ["8.8.8.8"]},
            },
        ]
        self.path = self.backup.save(self.saved)

    def get_cloud(self) -> str:
        """Expose an explicit mock cloud without a network authentication step."""
        return self.cloud

    def workflow(self) -> RestoreWorkflow:
        """Create the production workflow using the actual SDK and private file store."""
        return RestoreWorkflow(PolicyApi(self), BundleFiles(self.backup))

    def prepare(self) -> Any:
        """Select both saved records and explicitly bind the mock cloud."""
        return self.workflow().prepare(self.path.stem, [f"org:{ORG_ID}", f"site:{SITE_ID}"], self.cloud)
