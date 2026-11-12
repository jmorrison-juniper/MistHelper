"""Verify orphan retention with synthetic process checks."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.mist.realtime.websocket_streams.web.services.operations import artifacts


@pytest.mark.parametrize(
    ("process_error", "retained"),
    [(None, True), (PermissionError(), True), (ProcessLookupError(), False), ("windows_missing", False)],
)
def test_orphan_admission_checks_process_ownership(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, process_error: OSError | str | None, retained: bool
) -> None:
    """Keep live owners and remove only owners proven absent during admission."""
    if process_error == "windows_missing":
        process_error = OSError("Synthetic Windows process error")
        process_error.winerror = 87
    process_check = Mock(side_effect=process_error)
    monkeypatch.setattr(artifacts.os, "kill", process_check)
    candidate = tmp_path / ("a" * 32)
    candidate.mkdir()
    (candidate / "manifest.json").write_text('{"owner_pid":42}', encoding="utf-8")
    service = artifacts.SessionArtifactService(SimpleNamespace(), None, tmp_path)
    writer = service.prepare_batch((), {"mode": "combined"})
    process_check.assert_called_once_with(42, 0)
    assert candidate.exists() is retained
    assert (tmp_path / writer.artifact_id / "manifest.json").is_file()
    writer.discard()


@pytest.mark.parametrize("winerror", [None, 5, 88])
def test_unrelated_process_errors_propagate(monkeypatch: pytest.MonkeyPatch, winerror: int | None) -> None:
    """Keep unexpected process errors visible to the caller."""
    error = OSError("Synthetic process error")
    if winerror is not None:
        error.winerror = winerror
    process_check = Mock(side_effect=error)
    monkeypatch.setattr(artifacts.os, "kill", process_check)
    with pytest.raises(OSError) as caught:
        artifacts.BatchArtifactStorage.Retention.process_is_alive(42)
    assert caught.value is error
    process_check.assert_called_once_with(42, 0)


def test_orphan_removal_failure_propagates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep filesystem failures visible after a Windows owner is absent."""
    error = OSError("Synthetic Windows process error")
    error.winerror = 87
    monkeypatch.setattr(artifacts.os, "kill", Mock(side_effect=error))
    candidate = tmp_path / ("a" * 32)
    candidate.mkdir()
    (candidate / "manifest.json").write_text('{"owner_pid":42}', encoding="utf-8")
    service = artifacts.SessionArtifactService(SimpleNamespace(), None, tmp_path)
    failure = OSError("Synthetic removal failure")
    monkeypatch.setattr(service._storage.files, "remove_tree", Mock(side_effect=failure))
    with pytest.raises(OSError) as caught:
        service.prepare_batch((), {"mode": "combined"})
    assert caught.value is failure
    assert candidate.is_dir()
