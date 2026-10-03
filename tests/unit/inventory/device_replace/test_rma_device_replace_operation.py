"""Unit tests for the RMA device replacement operation and persistence."""

from __future__ import annotations  # WHY: keep annotations consistent with source modules.

from pathlib import Path  # WHY: verify backup and CSV paths.
from typing import Any  # WHY: fake clients store arbitrary requests.

from src.mist.resources.inventory.device_replace import (
    operation as operation_module,
)  # WHY: patch the resolver used by the module.
from src.mist.resources.inventory.device_replace.models import (
    InventoryDevice,
    ReplaceRequest,
)  # WHY: build fake devices.
from src.mist.resources.inventory.device_replace.operation import DeviceReplaceOperation  # WHY: test the workflow.
from src.mist.resources.inventory.device_replace.persistence import (
    DeviceReplacePersistence,
)  # WHY: test evidence files.


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
        self.fail_replace = False  # WHY: one test verifies durable logging when Mist refuses the request.

    def list_inventory(self) -> list[InventoryDevice]:
        """Return fake inventory devices."""
        return self.devices  # WHY: no network in unit tests.

    def get_old_configuration(self, old_device: InventoryDevice) -> dict[str, str]:
        """Return fake old device configuration."""
        self.backup_read = True  # WHY: record that the backup source was read.
        return {"id": old_device.device_id, "name": old_device.name}  # WHY: backup payload content.

    def replace_device(self, request: ReplaceRequest) -> dict[str, str]:
        """Record the replacement request."""
        if self.fail_replace:  # WHY: simulate a Mist request failure without network access.
            raise RuntimeError("Mist refused replacement")  # WHY: operation must write an error row.
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


def test_operation_sends_no_request_until_replace(monkeypatch: Any, tmp_path: Path) -> None:
    """The operation sends one request only after typed confirmation."""
    old_device = _device()  # WHY: source device.
    new_device = _device(id="new-id", mac="aabbcc000002", site_id="", name="New AP")  # WHY: target device.
    client = FakeClient([old_device, new_device])  # WHY: fake inventory and replacement send.
    FakeInputUtils.answers = ["Old AP", "1", "REPLACE"]  # WHY: old selector, new choice, confirmation.
    monkeypatch.setattr(operation_module, "SourceDependencyResolver", FakeResolver)  # WHY: no interactive input.
    persistence = DeviceReplacePersistence(tmp_path)  # WHY: keep test output outside the repository data tree.
    DeviceReplaceOperation.run_with_dependencies("org-1", client, persistence, dry_run=False)  # WHY: exercise flow.
    assert client.backup_read is True  # WHY: backup source was read before request.
    assert len(client.replacements) == 1  # WHY: confirmation allowed one request.
    assert (tmp_path / "DeviceReplaceLog.csv").read_text(encoding="utf-8").count("sent") == 2


def test_operation_dry_run_writes_backup_and_sends_no_request(monkeypatch: Any, tmp_path: Path) -> None:
    """Dry-run mode writes evidence and skips the replace request."""
    old_device = _device()  # WHY: source device.
    new_device = _device(id="new-id", mac="aabbcc000002", site_id="", name="New AP")  # WHY: target device.
    client = FakeClient([old_device, new_device])  # WHY: fake inventory and replacement send.
    FakeInputUtils.answers = ["aabbcc000001", "aabbcc000002", "REPLACE"]  # WHY: MAC selectors and confirm.
    monkeypatch.setattr(operation_module, "SourceDependencyResolver", FakeResolver)  # WHY: no interactive input.
    persistence = DeviceReplacePersistence(tmp_path)  # WHY: keep test output outside the repository data tree.
    DeviceReplaceOperation.run_with_dependencies("org-1", client, persistence, dry_run=True)  # WHY: exercise dry run.
    backups = list((tmp_path / "rma_backups").glob("*.json"))  # WHY: prove backup exists.
    assert backups and client.replacements == []  # WHY: dry-run stops before request.
    assert "dry_run" in (tmp_path / "DeviceReplaceLog.csv").read_text(encoding="utf-8")


def test_operation_cancel_sends_no_request(monkeypatch: Any, tmp_path: Path) -> None:
    """Wrong confirmation cancels the replacement request."""
    old_device = _device()  # WHY: source device.
    new_device = _device(id="new-id", mac="aabbcc000002", site_id="", name="New AP")  # WHY: target device.
    client = FakeClient([old_device, new_device])  # WHY: fake inventory and replacement send.
    FakeInputUtils.answers = ["Old AP", "1", "no"]  # WHY: wrong confirmation.
    monkeypatch.setattr(operation_module, "SourceDependencyResolver", FakeResolver)  # WHY: no interactive input.
    persistence = DeviceReplacePersistence(tmp_path)  # WHY: keep test output outside the repository data tree.
    DeviceReplaceOperation.run_with_dependencies("org-1", client, persistence, dry_run=False)  # WHY: exercise cancel.
    assert client.replacements == []  # WHY: request must not send without exact confirmation.
    assert "cancelled" in (tmp_path / "DeviceReplaceLog.csv").read_text(encoding="utf-8")


def test_operation_logs_error_when_replace_request_fails(monkeypatch: Any, tmp_path: Path) -> None:
    """Mist request failures create an error log row."""
    old_device = _device()  # WHY: source device.
    new_device = _device(id="new-id", mac="aabbcc000002", site_id="", name="New AP")  # WHY: target device.
    client = FakeClient([old_device, new_device])  # WHY: fake inventory and replacement send.
    client.fail_replace = True  # WHY: force the replace request to fail.
    FakeInputUtils.answers = ["Old AP", "1", "REPLACE"]  # WHY: reach the failing replace call.
    monkeypatch.setattr(operation_module, "SourceDependencyResolver", FakeResolver)  # WHY: no interactive input.
    persistence = DeviceReplacePersistence(tmp_path)  # WHY: keep test output outside the repository data tree.
    DeviceReplaceOperation.run_with_dependencies("org-1", client, persistence, dry_run=False)  # WHY: exercise error.
    assert "error" in (tmp_path / "DeviceReplaceLog.csv").read_text(encoding="utf-8")


def test_backup_and_log_files_hold_required_fields(tmp_path: Path) -> None:
    """Persistence writes the backup and DeviceReplaceLog.csv fields."""
    old_device = _device()  # WHY: source device for backup metadata.
    persistence = DeviceReplacePersistence(tmp_path)  # WHY: keep test output outside the repository data tree.
    backup_path = persistence.write_backup("org-1", old_device, {"hostname": "old"})  # WHY: write backup.
    DeviceReplaceOperation._write_result("org-1", persistence, old_device, old_device, backup_path, "dry_run", "ok")
    assert backup_path.exists()  # WHY: acceptance requires a backup file.
    csv_text = (tmp_path / "DeviceReplaceLog.csv").read_text(encoding="utf-8")  # WHY: inspect log file.
    assert "old_mac,new_mac" in csv_text and "aabbcc000001" in csv_text and "dry_run" in csv_text
