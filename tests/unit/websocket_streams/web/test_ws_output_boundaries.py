"""Unit tests for WebSocket command output boundaries."""

from __future__ import annotations  # Keep annotations compatible with the project target.

import json  # Send deterministic message data to the JavaScript harness.
import logging  # Record each offline JavaScript execution.
import shutil  # Find the local Node executable.
import subprocess  # Execute the production JavaScript without a browser.
from pathlib import Path  # Read the production WebSocket page script.
from types import SimpleNamespace  # Supply offline session and target identities.
from unittest.mock import Mock  # Simulate process ownership without signaling a real process.

import pytest  # Fail with a clear message when Node is not available.

import src.mist.realtime.websocket_streams.web as _ws_web  # The package that owns the browser asset.
from src.mist.realtime.websocket_streams.intake.fields.error import StreamRequestError  # Check storage failures.
from src.mist.realtime.websocket_streams.web.services.operations import artifacts  # Inspect the real storage boundary.
from tests.unit.websocket_streams.live.transport.runtime.test_ws_feature_structure import (
    PythonStructureGuard,
)  # Apply the existing guard without changing its limits.

logger = logging.getLogger(__name__)  # Keep unit test actions visible in test logs.

_WEB_PACKAGE_DIR = Path(_ws_web.__file__).resolve().parent  # A later package move cannot break this path.
SCRIPT_PATH = _WEB_PACKAGE_DIR / "static" / "websockets.js"  # The browser script under test.


class WebSocketOutputScript:
    """Execute the production command output operations in Node."""

    HARNESS = r"""
const fs = require('fs');
const vm = require('vm');
const payload = JSON.parse(fs.readFileSync(0, 'utf8'));
const context = {
    document: { addEventListener: () => {} },
    window: {}
};
vm.runInNewContext(payload.source, context, { filename: 'websockets.js' });
const output = context.window.MistWebSocketOutput;
const messages = payload.parts.map((content, index) => ({
    content,
    seq: index + 1,
    source: 'HQ',
    received_at: '2026-10-03T19:00:00Z'
}));
const joined = output.joinLineText(messages);
process.stdout.write(JSON.stringify({
    joined,
    filtered: output.filterLineText(joined, payload.filter)
}));
"""

    @classmethod
    def run(cls, parts: list[str], filter_text: str) -> dict[str, str]:
        """Run the production join and filter operations."""
        executable = shutil.which("node")  # Use the installed Node runtime for an offline unit test.
        if executable is None:  # The required JavaScript runtime must not produce a false pass.
            pytest.fail("Node is missing, so the required WebSocket output unit test cannot run.")
        logger.info("The unit test will execute 1 WebSocket output script with %d chunks", len(parts))
        source = SCRIPT_PATH.read_text(encoding="utf-8")  # Read the exact browser script that production serves.
        payload = json.dumps({"source": source, "parts": parts, "filter": filter_text})  # Build deterministic input.
        result = subprocess.run(  # Execute the script with no network or browser dependency.
            [executable, "-e", cls.HARNESS],
            input=payload,
            text=True,
            capture_output=True,
            check=True,
            timeout=15,
        )
        decoded = json.loads(result.stdout)  # Parse the production operation results.
        if not isinstance(decoded, dict):  # A missing result object means the JavaScript contract failed.
            raise AssertionError("The WebSocket output script returned no result object.")
        joined = decoded.get("joined")  # Read the joined command text.
        filtered = decoded.get("filtered")  # Read the filtered command text.
        if not isinstance(joined, str) or not isinstance(filtered, str):  # Both operations must return text.
            raise AssertionError("The WebSocket output script returned an invalid text result.")
        observed = {"joined": joined, "filtered": filtered}  # Keep a precise return type for the assertions.
        logger.debug("The unit test joined %d characters", len(observed["joined"]))
        return observed  # Return the observed text for precise assertions.


def test_command_chunks_preserve_line_and_word_boundaries() -> None:
    """Command chunks must join without an inserted header or separator."""
    parts = ["apbr_SL-Only.inet6.0: 1 d", "estinations, 1 routes\nNext ", "line\n"]  # Split one word and one line.
    observed = WebSocketOutputScript.run(parts, "")  # Execute the production operations without a filter.
    assert observed["joined"] == "apbr_SL-Only.inet6.0: 1 destinations, 1 routes\nNext line\n"


def test_filter_matches_a_word_that_spans_command_chunks() -> None:
    """The filter must read complete lines after the command chunks join."""
    parts = ["apbr_SL-Only.inet6.0: 1 d", "estinations, 1 routes\nHidden line\n"]  # Split the filter word.
    observed = WebSocketOutputScript.run(parts, "destinations")  # Filter after the production join.
    assert observed["filtered"] == "apbr_SL-Only.inet6.0: 1 destinations, 1 routes"


class TestBatchArtifactComposition:
    """Verify the composed storage boundary without a live Mist request."""

    def test_artifact_module_obeys_the_existing_structure_guard(self) -> None:
        """Check every helper instead of moving a violation to another class."""
        counts = PythonStructureGuard().inspect([Path(artifacts.__file__)])  # Check the production file.
        assert counts.modules == 1  # Prove that the guard inspected the requested module.
        assert counts.classes > 3  # The storage behavior must use real helper classes.

    @pytest.mark.parametrize("mode", ["combined", "grouped", "both"])
    @pytest.mark.parametrize("group", ["site", "device_type", "device", "client"])
    def test_layouts_preserve_snapshot_order_and_retention(self, tmp_path: Path, mode: str, group: str) -> None:
        """Every layout retains redaction, global order, expiry, and download pins."""
        manager = SimpleNamespace(session=lambda _: SimpleNamespace(live=False, ended_at="2026-10-16T20:00:00Z"))
        service = artifacts.SessionArtifactService(manager, None, tmp_path)  # Keep output below the project test root.
        targets = tuple(
            SimpleNamespace(target_key=str(index), identity={"site_id": f"site-{index}", "device_id": str(index)})
            for index in range(2)
        )  # Freeze the target order independently of write order.
        writer = service.prepare_batch(targets, {"mode": mode, "group_by": group})  # Exercise the public admission API.
        service.bind_batch("parent", writer)  # Bind the public session to its private directory.
        for index in (1, 0):
            writer.write_result(str(index), targets[index].identity, "message", "api_token=private-value", None)
        _, lines = service.download("parent")  # Freeze a partial snapshot before another write.
        writer.write_result("0", targets[0].identity, "message", "later", None)  # Exclude this later sequence.
        assert service.cleanup_expired("parent") is False  # Active response pins prevent retention cleanup.
        records = [json.loads(line) for line in lines]  # Exhaustion must release the response pin.
        assert [record["seq"] for record in records] == [1, 2]  # Preserve global order in every layout.
        assert [record["target"]["site_id"] for record in records] == ["site-1", "site-0"]  # Keep target identity.
        assert "private-value" not in str(records)  # Redact before either saved layout receives data.
        writer.finish([{"target": dict(targets[0].identity), "state": "completed", "private": "hidden"}])
        manifest = service.manifest("parent")  # Read only the safe public summary.
        assert manifest["expires_at"] == "2026-10-16T20:10:00Z"  # Preserve the ten-minute retention window.
        assert manifest["targets"] == [{"target": dict(targets[0].identity), "state": "completed"}]
        assert service.cleanup_expired("parent") is True  # Cleanup succeeds after snapshot exhaustion.
        assert not (tmp_path / writer.artifact_id).exists()  # Remove only this bound tree.

    @pytest.mark.parametrize(
        ("process_error", "retained"),
        [(None, True), (ProcessLookupError(), False), (PermissionError(), True)],
    )
    def test_orphan_cleanup_requires_proven_process_absence(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, process_error: OSError | None, retained: bool
    ) -> None:
        """Preserve live owners, unreadable ownership, unrelated folders, and links."""
        process_check = Mock(side_effect=process_error)  # No real process receives an existence check.
        monkeypatch.setattr(artifacts.os, "kill", process_check)  # Isolate the local process boundary.
        candidate = tmp_path / ("a" * 32)  # Only a generated directory name can become an orphan.
        candidate.mkdir()  # Supply one complete ownership record.
        (candidate / "manifest.json").write_text('{"owner_pid":42}', encoding="utf-8")  # Use a synthetic owner.
        unknown = tmp_path / ("b" * 32)  # Malformed ownership must never permit removal.
        unknown.mkdir()  # Preserve a tree with an unreadable manifest.
        (unknown / "manifest.json").write_text("{", encoding="utf-8")  # Simulate interrupted metadata.
        outside = tmp_path / "unrelated"  # An unrelated directory must remain untouched.
        outside.mkdir()  # Give the checked link a real target.
        linked = tmp_path / ("c" * 32)  # A generated label does not make a symlink safe.
        linked.symlink_to(outside, target_is_directory=True)  # Refuse linked cleanup candidates.
        service = artifacts.SessionArtifactService(SimpleNamespace(), None, tmp_path)  # Use offline storage.
        writer = service.prepare_batch((), {"mode": "combined"})  # Admission performs the orphan scan.
        process_check.assert_called_once_with(42, 0)  # Check only the verified ownership record.
        assert candidate.exists() is retained  # Delete only a process proven absent.
        assert unknown.is_dir() and linked.is_symlink() and outside.is_dir()  # Preserve unsafe or unknown owners.
        writer.discard()  # Remove the newly admitted private tree.

    @pytest.mark.parametrize("failure", ["quota", "symlink", "write"])
    def test_manifest_failure_preserves_partial_state_and_external_files(self, tmp_path: Path, failure: str) -> None:
        """A failed final manifest cannot permit archive download or damage another file."""
        service = artifacts.SessionArtifactService(
            SimpleNamespace(session=lambda _: SimpleNamespace(live=False)), None, tmp_path
        )  # Provide an ended public parent without Mist access.
        writer = service.prepare_batch((), {"mode": "combined"})  # Create a valid initial manifest.
        service.bind_batch("parent", writer)  # Exercise failures through the public service.
        directory = tmp_path / writer.artifact_id  # Inspect only the server-generated private tree.
        outside = tmp_path / "preserved.json"  # Keep an unrelated file as a deletion sentinel.
        outside.write_text("preserved", encoding="utf-8")  # A refused link must not change these bytes.
        if failure == "quota":
            service.MANIFEST_LIMIT = 1  # Apply a live limit after admission.
        elif failure == "symlink":
            (directory / "manifest.json").unlink()  # Replace only this test-owned manifest.
            (directory / "manifest.json").symlink_to(outside)  # Refuse a link before replacement.
        else:
            (directory / ".manifest.tmp").mkdir()  # Force the staged metadata write to fail.
        with pytest.raises(StreamRequestError) as error:
            writer.finish([])  # A final metadata failure must remain visible.
        assert error.value.code == "output_failed"  # Preserve the stable storage error contract.
        assert service.manifest("parent")["partial"] is True  # Keep the incomplete result explicit.
        with pytest.raises(StreamRequestError) as archive_error:
            service.zip_download("parent")  # A failed final manifest cannot mark output complete.
        assert archive_error.value.code == "artifact_not_ready"  # Preserve archive readiness semantics.
        writer.discard()  # Remove the private tree without following its manifest link.
        assert outside.read_text(encoding="utf-8") == "preserved"  # Preserve unrelated data.

    @pytest.mark.parametrize("download_kind", ["jsonl", "zip"])
    def test_download_failures_release_retention_pins(self, tmp_path: Path, download_kind: str) -> None:
        """Read failures release pins so retention can remove a failed tree."""
        service = artifacts.SessionArtifactService(
            SimpleNamespace(session=lambda _: SimpleNamespace(live=False)), None, tmp_path
        )  # Keep the session ended and the manager offline.
        target = SimpleNamespace(target_key="target", identity={"site_id": "site"})  # Use one safe target.
        writer = service.prepare_batch((target,), {"mode": "combined"})  # Save one bounded JSON Lines file.
        writer.write_result("target", target.identity, "message", "saved", None)  # Create a downloadable result.
        writer.finish([{"state": "completed"}])  # Make both download types available.
        service.bind_batch("parent", writer)  # Use the public download and cleanup APIs.
        path = tmp_path / writer.artifact_id / "results" / "combined.jsonl"  # Address only the private result.
        if download_kind == "jsonl":
            _, lines = service.download("parent")  # Pin the file before the read failure.
            path.unlink()  # Simulate a failed storage read after the snapshot.
            with pytest.raises(FileNotFoundError):
                list(lines)  # Iterator failure must release its pin.
        else:
            path.unlink()  # Simulate a missing result during archive construction.
            with pytest.raises(FileNotFoundError):
                service.zip_download("parent")  # Archive failure must release its pin.
        assert service.cleanup_expired("parent") is True  # A failed response cannot strand its cleanup pin.
        assert not (tmp_path / writer.artifact_id).exists()  # Confirm exact tree removal.
