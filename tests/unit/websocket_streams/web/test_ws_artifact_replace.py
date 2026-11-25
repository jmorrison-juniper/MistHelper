"""Tests for the file replace of the batch artifact store while another process holds a file (issue #4926)."""

from __future__ import annotations

import json  # Read the manifest that the store wrote.
import logging  # Read the retry events of the structured logger.
import os  # The double stands in for the one call that Windows refuses.
from pathlib import Path  # Test output stays under the pytest temporary folder.
from types import SimpleNamespace  # Targets and the clock double.
from typing import Any  # The doubles have no public type.

import pytest  # Fixtures, parametrization, and error checks.

from src.mist.realtime.websocket_streams.intake.fields.error import StreamRequestError  # The contract error.
from src.mist.realtime.websocket_streams.web.services.operations import artifacts as artifact_module  # The clock.
from src.mist.realtime.websocket_streams.web.services.operations.artifacts import (
    SessionArtifactService,
)  # The unit under test.
from src.mist.realtime.websocket_streams.web.services.operations.hardware_xml import (
    HardwareXmlPreset,
    HardwareXmlSupport,
)  # The preset and the decoder.
from tests.unit.ex_hardware_inventory.support.hardware_replies import HardwareReplies  # Invented replies.

RETRY_EVENT = "web.artifact.replace.retry"  # The event name that each wait writes.
MANIFEST_ERROR = "web.artifact.batch.manifest.error"  # The event name of a manifest that could not be saved.
WAITS = [0.05, 0.1, 0.2, 0.4]  # The waits of the replace, in seconds.
PROMPT = "switch@site>"  # The prompt that the decoder expects after a reply.


class LockedReplace:
    """Stand in for ``os.replace`` and refuse the first calls, like a file that another process holds."""

    def __init__(self, refusals: int, error: OSError | None = None) -> None:
        """Store the plan and keep the real function.

        Args:
            refusals: How many calls fail before one works.
            error: The error to raise. The default is the Windows permission error.
        """
        self.refusals = refusals  # The calls up to this number raise.
        self.error = error if error is not None else PermissionError(13, "Access is denied")  # What the OS raises.
        self.calls = 0  # Each call counts, accepted or not.
        self._real = os.replace  # The real function must run after the refusals.

    def __call__(self, source: Any, destination: Any) -> None:
        """Raise the planned error, or replace the file."""
        self.calls += 1  # Count this call first.
        if self.calls <= self.refusals:  # The planned lock is still there.
            raise self.error
        self._real(source, destination)  # The lock is gone.


@pytest.fixture
def waits(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Record each wait of the store, and wait for nothing."""
    recorded: list[float] = []  # The seconds of each wait, in order.
    monkeypatch.setattr(artifact_module, "time", SimpleNamespace(sleep=recorded.append))  # Only the store's clock.
    return recorded


def make_run(tmp_path: Path) -> tuple[SessionArtifactService, Any, Any]:
    """Admit one hardware run with one switch. Return the service, the writer, and the target."""
    target = SimpleNamespace(target_key="target", identity={"device_id": "device-1", "label": "EX-1"})
    service = SessionArtifactService(SimpleNamespace(), None, tmp_path)
    writer = service.prepare_batch((target,), {"preset": HardwareXmlPreset.NAME, "format": "xml", "mode": "combined"})
    return service, writer, target


def make_document() -> Any:
    """Decode one framed reply the way the batch runner does."""
    framed = (HardwareReplies.single_switch("SW1") + "\n" + PROMPT).encode()
    return HardwareXmlSupport.Decoder.decode_output(framed, PROMPT, HardwareXmlPreset.COMMAND)


class TestReplace:
    """The replace waits out a short lock, and it gives up on a lock that stays."""

    @staticmethod
    def staged(tmp_path: Path) -> tuple[Path, Path]:
        """Write one staged file. Return it with the path of its destination."""
        temporary = tmp_path / ".staged.tmp"
        temporary.write_text("new", encoding="utf-8")
        return temporary, tmp_path / "final.txt"

    def test_a_lock_that_clears_is_waited_out(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, waits: list[float]
    ) -> None:
        """Two refusals give two waits, and the third try replaces the file."""
        service, _, _ = make_run(tmp_path)
        temporary, destination = self.staged(tmp_path)
        locked = LockedReplace(refusals=2)
        monkeypatch.setattr(os, "replace", locked)
        service._storage.metadata.replace(temporary, destination)
        assert locked.calls == 3 and waits == WAITS[:2]  # The waits grow with each refusal.
        assert destination.read_text(encoding="utf-8") == "new" and not temporary.exists()

    def test_a_lock_that_stays_raises_after_the_last_try(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, waits: list[float]
    ) -> None:
        """Five tries and four waits cost at most 0.75 seconds, and then the permission error reaches the caller."""
        service, _, _ = make_run(tmp_path)
        temporary, destination = self.staged(tmp_path)
        locked = LockedReplace(refusals=99)
        monkeypatch.setattr(os, "replace", locked)
        with pytest.raises(PermissionError):
            service._storage.metadata.replace(temporary, destination)
        assert locked.calls == 5 and waits == WAITS and sum(waits) == pytest.approx(0.75)
        assert not destination.exists() and temporary.exists()  # The staged file stays for the caller to remove.

    @pytest.mark.parametrize(
        "error",
        [FileNotFoundError(2, "gone"), OSError(28, "disk full"), IsADirectoryError(21, "is a directory")],
    )
    def test_another_error_is_not_retried(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, waits: list[float], error: OSError
    ) -> None:
        """Only a lock clears with time, so any other error fails at the first try."""
        service, _, _ = make_run(tmp_path)
        temporary, destination = self.staged(tmp_path)
        locked = LockedReplace(refusals=99, error=error)
        monkeypatch.setattr(os, "replace", locked)
        with pytest.raises(OSError) as raised:
            service._storage.metadata.replace(temporary, destination)
        assert raised.value is error and locked.calls == 1 and waits == []

    def test_an_empty_list_of_waits_means_one_try(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, waits: list[float]
    ) -> None:
        """A caller that passes no waits gets the plain replace and its error."""
        service, _, _ = make_run(tmp_path)
        temporary, destination = self.staged(tmp_path)
        locked = LockedReplace(refusals=1)
        monkeypatch.setattr(os, "replace", locked)
        with pytest.raises(PermissionError):
            service._storage.metadata.replace(temporary, destination, waits=())
        assert locked.calls == 1 and waits == []


class TestBatchRecord:
    """A short lock does not fail the batch record, and a lock that stays fails it once."""

    def test_a_short_lock_does_not_fail_the_manifest_write(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, waits: list[float]
    ) -> None:
        """The record stays writable, and the manifest on disk holds the new state."""
        service, writer, _ = make_run(tmp_path)
        locked = LockedReplace(refusals=1)
        monkeypatch.setattr(os, "replace", locked)
        service._storage.metadata.write(writer._record)
        manifest = json.loads((tmp_path / writer.artifact_id / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["status"] == "writing" and writer._record.status == "writing"
        assert locked.calls == 2 and waits == WAITS[:1]  # One refusal, one wait, one accepted try.

    def test_a_lock_that_stays_fails_the_record_once_and_logs_each_wait(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        waits: list[float],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """The record fails after the last try, and the log names the type of the error, never a path."""
        service, writer, _ = make_run(tmp_path)
        caplog.set_level(logging.DEBUG)
        monkeypatch.setattr(os, "replace", LockedReplace(refusals=99))
        with pytest.raises(StreamRequestError) as refusal:
            service._storage.metadata.write(writer._record)
        assert refusal.value.code == "output_failed"
        assert writer._record.status == "failed" and writer._record.partial is True
        assert caplog.text.count(RETRY_EVENT) == len(WAITS) and caplog.text.count(MANIFEST_ERROR) == 1
        assert "PermissionError" in caplog.text and str(tmp_path) not in caplog.text
        assert waits == WAITS

    def test_a_short_lock_does_not_fail_the_saved_reply(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, waits: list[float]
    ) -> None:
        """The reply is published after one wait, and the record keeps writing for the next switch."""
        _, writer, target = make_run(tmp_path)
        document = make_document()
        locked = LockedReplace(refusals=1)
        monkeypatch.setattr(os, "replace", locked)
        names = writer.write_hardware(target.target_key, target.identity, document, "xml")
        saved = tmp_path / writer.artifact_id / names[0]
        assert saved.read_bytes() == document.xml.encode("utf-8")
        assert writer._record.status == "writing" and writer._record.files == set(names)
        assert locked.calls == 3 and waits == WAITS[:1]  # The publish took two tries. The snapshot took one.

    def test_a_lock_that_stays_on_the_reply_removes_it_and_keeps_the_record_writable(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, waits: list[float]
    ) -> None:
        """One refused reply fails its own target only. No partial file stays, and the record can still save."""
        _, writer, target = make_run(tmp_path)
        monkeypatch.setattr(os, "replace", LockedReplace(refusals=99))
        with pytest.raises(StreamRequestError) as refusal:
            writer.write_hardware(target.target_key, target.identity, make_document(), "xml")
        assert refusal.value.code == "output_failed"
        left = sorted(path.name for path in (tmp_path / writer.artifact_id).rglob("*") if path.is_file())
        assert left == ["manifest.json"]  # The staged file and the published file are gone.
        assert writer._record.status == "writing" and writer._record.partial is True
        assert waits == WAITS
