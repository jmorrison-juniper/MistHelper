"""Unit tests for the RMA device replacement operation and persistence."""

from __future__ import annotations  # WHY: keep annotations consistent with source modules.

import shutil  # WHY: clean the project-relative test data directory.
from pathlib import Path  # WHY: verify backup and CSV paths.
from typing import Any  # WHY: fake clients store arbitrary requests.

from src.inventory.device_replace import operation as operation_module  # WHY: patch the resolver used by the module.
from src.inventory.device_replace.models import InventoryDevice, ReplaceRequest  # WHY: build fake devices.
from src.inventory.device_replace.operation import DeviceReplaceOperation  # WHY: test the workflow.
from src.inventory.device_replace.persistence import DeviceReplacePersistence  # WHY: test evidence files.

TEST_DATA_DIR = Path("data") / "test-rma-device-replace"  # WHY: avoid forbidden temporary directories.


class FakeInputUtils:
    """FIFO input helper for operation tests."""

    answers: list[str] = []  # WHY: tests load prompt answers in order.

    @classmethod
    def safe_input(cls, prompt: str, context: str = "unknown") -> str:
        """Return the next test answer."""
        _ = prompt  # WHY: keep the prompt parameter visible for the shared signature.
        _ = context  # WHY: keep the context parameter visible for the shared signature.
        return cls.answers.pop(0)  # WHY: each prompt consumes one planned answer.


class FakeClient:
    """Fake replacement client for operation tests."""

    def __init__(self, devices: list[InventoryDevice]) -> None:
        """Store fake inventory devices."""
        self.devices = devices  # WHY: list_inventory returns this controlled set.
        self.replacements: list[ReplaceRequest] = []  # WHY: tests assert request gating.
        self.backup_read = False  # WHY: tests assert backup read happened before request.

    def list_inventory(self) -> list[InventoryDevice]:
        """Return fake inventory devices."""
        return self.devices  # WHY: no network in unit tests.

    def get_old_configuration(self, old_device: InventoryDevice) -> dict[str, str]:
        """Return fake old device configuration."""
        self.backup_read = True  # WHY: record that the backup source was read.
        return {"id": old_device.device_id, "name": old_device.name}  # WHY: backup payload content.

    def replace_device(self, request: ReplaceRequest) -> dict[str, str]:
        """Record the replacement request."""
        self.replacements.append(request)  # WHY: tests assert exactly one sent request.
        return {"message": "sent"}  # WHY: operation writes this result message.


class FakeResolver:
    """Resolver replacement that supplies deterministic test input."""

    InputUtils = FakeInputUtils  # WHY: operation code reads this class attribute for prompts.


def _device(**overrides: str) -> InventoryDevice:
    """Return one inventory device for operation tests."""
    row = {
        "id": "old-id",
        "mac": "aabbcc000001",
        "serial": "old-serial",
        "model": "AP45",
        "type": "ap",
        "site_id": "site-1",
        "name": "Old AP",
    }
    row.update(overrides)  # WHY: each test changes only the relevant fields.
    return InventoryDevice.from_row(row)  # WHY: exercise source normalization.


def _clean_data_dir() -> None:
    """Remove the project-relative test data directory."""
    if TEST_DATA_DIR.exists():  # WHY: a prior failed test can leave evidence files behind.
        shutil.rmtree(TEST_DATA_DIR)  # WHY: start each test with a clean controlled directory.


def test_operation_sends_no_request_until_replace(monkeypatch: Any) -> None:
    """The operation sends one request only after typed confirmation."""
    _clean_data_dir()  # WHY: isolate file evidence for this test.
    old_device = _device()  # WHY: source device.
    new_device = _device(id="new-id", mac="aabbcc000002", site_id="", name="New AP")  # WHY: target device.
    client = FakeClient([old_device, new_device])  # WHY: fake inventory and replacement send.
    FakeInputUtils.answers = ["Old AP", "1", "REPLACE"]  # WHY: old selector, new choice, confirmation.
    monkeypatch.setattr(operation_module, "SourceDependencyResolver", FakeResolver)  # WHY: no interactive input.
    persistence = DeviceReplacePersistence(TEST_DATA_DIR)  # WHY: controlled project-relative outputs.
    DeviceReplaceOperation.run_with_dependencies("org-1", client, persistence, dry_run=False)  # WHY: exercise flow.
    assert client.backup_read is True  # WHY: backup source was read before request.
    assert len(client.replacements) == 1  # WHY: confirmation allowed one request.
    assert (TEST_DATA_DIR / "DeviceReplaceLog.csv").read_text(encoding="utf-8").count("sent") == 2
    _clean_data_dir()  # WHY: leave no project-relative test artifact.


def test_operation_dry_run_writes_backup_and_sends_no_request(monkeypatch: Any) -> None:
    """Dry-run mode writes evidence and skips the replace request."""
    _clean_data_dir()  # WHY: isolate file evidence for this test.
    old_device = _device()  # WHY: source device.
    new_device = _device(id="new-id", mac="aabbcc000002", site_id="", name="New AP")  # WHY: target device.
    client = FakeClient([old_device, new_device])  # WHY: fake inventory and replacement send.
    FakeInputUtils.answers = ["aabbcc000001", "aabbcc000002", "REPLACE"]  # WHY: MAC selectors and confirm.
    monkeypatch.setattr(operation_module, "SourceDependencyResolver", FakeResolver)  # WHY: no interactive input.
    persistence = DeviceReplacePersistence(TEST_DATA_DIR)  # WHY: controlled project-relative outputs.
    DeviceReplaceOperation.run_with_dependencies("org-1", client, persistence, dry_run=True)  # WHY: exercise dry run.
    backups = list((TEST_DATA_DIR / "rma_backups").glob("*.json"))  # WHY: prove backup exists.
    assert backups and client.replacements == []  # WHY: dry-run stops before request.
    assert "dry_run" in (TEST_DATA_DIR / "DeviceReplaceLog.csv").read_text(encoding="utf-8")
    _clean_data_dir()  # WHY: leave no project-relative test artifact.


def test_operation_cancel_sends_no_request(monkeypatch: Any) -> None:
    """Wrong confirmation cancels the replacement request."""
    _clean_data_dir()  # WHY: isolate file evidence for this test.
    old_device = _device()  # WHY: source device.
    new_device = _device(id="new-id", mac="aabbcc000002", site_id="", name="New AP")  # WHY: target device.
    client = FakeClient([old_device, new_device])  # WHY: fake inventory and replacement send.
    FakeInputUtils.answers = ["Old AP", "1", "no"]  # WHY: wrong confirmation.
    monkeypatch.setattr(operation_module, "SourceDependencyResolver", FakeResolver)  # WHY: no interactive input.
    persistence = DeviceReplacePersistence(TEST_DATA_DIR)  # WHY: controlled project-relative outputs.
    DeviceReplaceOperation.run_with_dependencies("org-1", client, persistence, dry_run=False)  # WHY: exercise cancel.
    assert client.replacements == []  # WHY: request must not send without exact confirmation.
    assert "cancelled" in (TEST_DATA_DIR / "DeviceReplaceLog.csv").read_text(encoding="utf-8")
    _clean_data_dir()  # WHY: leave no project-relative test artifact.


def test_backup_and_log_files_hold_required_fields() -> None:
    """Persistence writes the backup and DeviceReplaceLog.csv fields."""
    _clean_data_dir()  # WHY: isolate file evidence for this test.
    old_device = _device()  # WHY: source device for backup metadata.
    persistence = DeviceReplacePersistence(TEST_DATA_DIR)  # WHY: controlled project-relative outputs.
    backup_path = persistence.write_backup("org-1", old_device, {"hostname": "old"})  # WHY: write backup.
    DeviceReplaceOperation._write_result("org-1", persistence, old_device, old_device, backup_path, "dry_run", "ok")
    assert backup_path.exists()  # WHY: acceptance requires a backup file.
    csv_text = (TEST_DATA_DIR / "DeviceReplaceLog.csv").read_text(encoding="utf-8")  # WHY: inspect log file.
    assert "old_mac,new_mac" in csv_text and "aabbcc000001" in csv_text and "dry_run" in csv_text
    _clean_data_dir()  # WHY: leave no project-relative test artifact.
