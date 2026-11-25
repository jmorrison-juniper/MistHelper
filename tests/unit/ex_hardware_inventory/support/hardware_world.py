"""The shared world of the integration tests of the CLI flow.

Why:
    Several integration test files need the same fake organization, the same fake shells, and the same
    patched seams of the menu. This module holds that world once, so each test file states only its scenario.
"""

from __future__ import annotations

import csv
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.mist.realtime.websocket_streams.live.sessions.manager.factory import BatchRunner
from src.operations.exporting.ex_hardware_inventory import console as console_module
from src.operations.exporting.ex_hardware_inventory import operation as operation_module
from src.operations.exporting.ex_hardware_inventory.operation import ExHardwareInventoryReport
from src.operations.exporting.ex_hardware_inventory.run import batch as batch_module
from src.operations.exporting.ex_hardware_inventory.run.watch import BatchWatcher
from tests.unit.ex_hardware_inventory.support.hardware_fakes import FakeMist, Payloads, ledger_session
from tests.unit.ex_hardware_inventory.support.hardware_shells import FakeOrganization, FakeShells, uuid

ORG_A, ORG_B = uuid(1), uuid(2)  # Invented organizations.
SITE_1, SITE_2, SITE_3 = uuid(11), uuid(12), uuid(13)  # Invented sites.
TOKEN = "SYNTHETIC-TOKEN-VALUE"  # A fake credential that must never appear in any output.
COMMAND = "show chassis hardware detail | display xml | no-more"  # The one fixed command.


class World:
    """One fake organization with its shells, its session, and the typed answer."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Patch every outside seam and build the default world."""
        monkeypatch.chdir(tmp_path)  # The report and the run folders go under the temporary folder.
        monkeypatch.setenv("MISTHELPER_STANDALONE", "true")  # No database backend.
        monkeypatch.delenv("PORTAL_WS_HARDWARE_CONCURRENCY", raising=False)  # The default of three.
        monkeypatch.setattr(BatchRunner, "QUIET_SECONDS", 0)  # No quiet wait in a fake shell.
        monkeypatch.setattr(BatchRunner, "COMMAND_SECONDS", 0.6)  # A silent shell times out quickly.
        monkeypatch.setattr(BatchWatcher, "POLL_SECONDS", 0.02)  # Poll fast.
        self.tmp_path = tmp_path
        self.ledger = SimpleNamespace(org_id=None)  # The shared request ledger.
        self.session = ledger_session(self.ledger)  # A session whose adapter holds the ledger.
        self.session._apitoken = [TOKEN]  # The credential that must never leak.
        self.shells = FakeShells()
        self.mist = FakeOrganization(monkeypatch, self.ledger)
        self.answer = ""  # What the operator types.
        self.prompts: list[str] = []
        monkeypatch.setattr(batch_module, "RunnerFactory", self.shells.factory())
        resolver = SimpleNamespace(
            apisession=self.session,
            ConfigUtils=SimpleNamespace(get_cached_org_id=lambda: None),
            InputUtils=SimpleNamespace(safe_input=self._ask),
        )
        monkeypatch.setattr(operation_module, "SourceDependencyResolver", resolver)
        monkeypatch.setattr(console_module, "SourceDependencyResolver", resolver)
        self.monkeypatch = monkeypatch

    def _ask(self, prompt: str, **_kwargs: object) -> str:
        """Record the prompt and answer like the operator."""
        self.prompts.append(prompt)
        return self.answer

    def org_token(self, org_id: str = ORG_A, name: str = "Alpha Org") -> FakeMist:
        """Make the credential an organization token for one organization."""
        return FakeMist(self.monkeypatch, Payloads.profile([Payloads.org_grant(org_id, name)]))

    def mixed_site_one(self) -> None:
        """Add a site with two connected EX switches, a disconnected one, and an access point."""
        self.mist.add(
            ORG_A,
            (SITE_1, "Site One"),
            [
                (uuid(101), "ex-01", "switch", "EX4100-48P"),
                (uuid(102), "ex-02", "switch", "EX4100-24P"),
                (uuid(103), "ex-03", "switch", "EX4100-48P"),
                (uuid(104), "ap-01", "ap", "AP45"),
            ],
        )
        self.mist.statuses[uuid(103)] = ["disconnected"]  # Offline at the preview.

    def rows(self) -> list[dict[str, str]]:
        """Read the one report file under data/."""
        files = sorted((self.tmp_path / "data").glob("ExHardwareInventory_*.csv"))
        assert len(files) == 1, f"expected one report file, found {files}"
        with files[0].open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))


def run_menu(capsys: pytest.CaptureFixture[str]) -> tuple[int, list[str]]:
    """Run the menu and return its result and its console lines."""
    result = ExHardwareInventoryReport.run()
    return result, capsys.readouterr().out.splitlines()
