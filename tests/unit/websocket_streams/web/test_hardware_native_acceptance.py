"""Verify native hardware commands, current status, framing, and durable artifacts."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import mistapi
import pytest

from src.mist.realtime.websocket_streams.intake.fields.error import StreamRequestError
from src.mist.realtime.websocket_streams.intake.pickers.service import StreamPickerService
from src.mist.realtime.websocket_streams.intake.start_request.models import BatchExecutionPlan, BatchTargetRequest
from src.mist.realtime.websocket_streams.live.sessions.manager.factory import BatchRunner, SharedTransport
from src.mist.realtime.websocket_streams.live.sessions.settings import StreamSettings
from src.mist.realtime.websocket_streams.live.terminal.byte_history import HistoryRead
from src.mist.realtime.websocket_streams.web.services.operations.artifacts import SessionArtifactService
from src.mist.realtime.websocket_streams.web.services.operations.hardware_xml import (
    HardwareOutputError,
    HardwareXmlPreset,
    HardwareXmlSupport,
)
from tests.unit.websocket_streams.live.sessions.test_ws_session_manager import FakeSink
from tests.unit.websocket_streams.live.sessions.test_ws_session_manager import (
    TestStreamSessionManager as SessionManagerFixture,
)
from tests.unit.websocket_streams.web.test_ws_web_services import (
    FakeBatchChecker,
    FakeBatchPicker,
    FakeManager,
    hardware_shell_definition,
    make_batch_service,
)


class NativeReplies:
    """Provide device-shaped native replies without production credentials."""

    XML = "<rpc-reply><chassis-inventory><chassis><name>EX-ë</name></chassis></chassis-inventory></rpc-reply>"
    JSON = '{\r\n "chassis-inventory" : [{"chassis": [{"name": [{"data": "EX-ë"}]}]}]\r\n}'
    PROMPT = "mist@EX>"

    @classmethod
    def frame(cls, output_format: str, payload: str) -> bytes:
        """Reproduce native output followed by the observed Junos role marker."""
        command = HardwareXmlPreset.COMMANDS[output_format]
        return f"{command}\r\n{payload}\r\n\r\n{{master:0}}\r\n{cls.PROMPT} ".encode()


@pytest.mark.parametrize("output_format", ["xml", "json", "both"])
@pytest.mark.parametrize("invalid", [None, "xml", "json"])
def test_native_commands_have_independent_capture_and_format_outcomes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, output_format: str, invalid: str | None
) -> None:
    """Run only selected commands and retain valid files when the other native response fails."""
    monkeypatch.setattr(BatchRunner, "QUIET_SECONDS", 0)
    formats = ("xml", "json") if output_format == "both" else (output_format,)
    commands = tuple(HardwareXmlPreset.COMMANDS[value] for value in formats)
    request = SessionManagerFixture()._shell_request()
    target = BatchTargetRequest("target", {"device_id": "device", "label": "EX"}, request)
    artifacts = SessionArtifactService(SimpleNamespace(), None, tmp_path)
    writer = artifacts.prepare_batch((target,), {"preset": HardwareXmlPreset.NAME, "format": output_format})
    plan = BatchExecutionPlan(
        (target,),
        1,
        commands=commands,
        output={"preset": HardwareXmlPreset.NAME, "format": output_format},
        hardware_writer=writer.write_hardware,
        hardware_status=lambda _identity: "connected",
    )
    batch = BatchRunner(
        replace(request, batch_plan=plan), FakeSink(), Mock(), StreamSettings.from_environment(), SharedTransport(1)
    )
    terminal = batch._registry.terminal()
    sink = BatchRunner.TargetSink(FakeSink(), plan, target, terminal)
    terminal.history.append(f"Welcome to Junos\r\n{{master:0}}\r\n{NativeReplies.PROMPT} ".encode())
    sent = []

    def send_input(command: str) -> None:
        """Return a separate response for each exact native command."""
        sent.append(command)
        selected = next(name for name, value in HardwareXmlPreset.COMMANDS.items() if command == value + "\n")
        payload = "<rpc-reply>" if selected == invalid else getattr(NativeReplies, selected.upper())
        raw = NativeReplies.frame(selected, payload)
        split = raw.index("ë".encode()) + 1 if "ë".encode() in raw else 10
        sink.add_bytes(raw[:split])
        sink.add_bytes(raw[split:])

    plan.progress.transitions.transition(target.target_key, "running")
    batch._shell.collect(SimpleNamespace(send_input=send_input), sink, target, terminal)
    row = plan.progress.summary.target_page(0, 1)["targets"][0]
    assert sent == [command + "\n" for command in commands]
    assert row["state"] == ("failed" if invalid in formats else "completed")
    assert {name: result["state"] for name, result in row["formats"].items()} == {
        name: "failed" if name == invalid else "completed" for name in formats
    }
    successful = [name for name in formats if name != invalid]
    assert sorted(Path(name).suffix for name in row["files"]) == sorted("." + name for name in successful)
    for name in row["files"]:
        expected = getattr(NativeReplies, Path(name).suffix[1:].upper())
        assert (tmp_path / writer.artifact_id / name).read_bytes() == expected.encode()


@pytest.mark.parametrize("output_format", ["xml", "json"])
def test_native_inventory_namespaces_and_slash_descriptions_remain_byte_faithful(
    tmp_path: Path, output_format: str
) -> None:
    """Preserve native namespace URLs and hardware descriptions rather than treating them as filesystem secrets."""
    namespace = "http://xml.example.invalid/junos/test/chassis"
    description = "Synthetic SFP/SFP+/SFP28 and 1/10/25G ports"
    xml = (
        f'<rpc-reply xmlns="{namespace}"><chassis-inventory><chassis>'
        f"<description>{description}</description></chassis></chassis-inventory></rpc-reply>"
    )
    native_json = (
        json.dumps(
            {
                "chassis-inventory": [
                    {"attributes": {"xmlns": namespace}, "chassis": [{"description": [{"data": description}]}]}
                ]
            },
            indent=4,
        )
        .replace("/", "\\/")
        .replace("\n", "\r\n")
    )
    native = xml if output_format == "xml" else native_json
    document = HardwareXmlSupport.Decoder.decode_output(
        NativeReplies.frame(output_format, native), NativeReplies.PROMPT, HardwareXmlPreset.COMMANDS[output_format]
    )
    target = BatchTargetRequest(
        "target", {"device_id": "synthetic", "label": "EX"}, SessionManagerFixture()._shell_request()
    )
    artifacts = SessionArtifactService(SimpleNamespace(), None, tmp_path)
    writer = artifacts.prepare_batch((target,), {"preset": HardwareXmlPreset.NAME, "format": output_format})
    files = writer.write_hardware(target.target_key, target.identity, document, output_format)
    assert (tmp_path / writer.artifact_id / files[0]).read_bytes() == native.encode()


@pytest.mark.parametrize("output_format", ["xml", "json"])
@pytest.mark.parametrize(
    "credential",
    ["api_token=synthetic-value", "bearer synthetic-value", "wss://shell.example.invalid/path", "OPENSSH PRIVATE KEY"],
)
def test_native_inventory_rejects_credential_values(output_format: str, credential: str) -> None:
    """Keep actual credential patterns prohibited while accepting ordinary inventory text."""
    xml = f"<rpc-reply><chassis-inventory><chassis><note>{credential}</note></chassis></chassis-inventory></rpc-reply>"
    native_json = json.dumps({"chassis-inventory": [{"chassis": [{"note": [{"data": credential}]}]}]})
    native = xml if output_format == "xml" else native_json
    with pytest.raises(HardwareOutputError, match="credential"):
        HardwareXmlSupport.Decoder.decode_output(
            NativeReplies.frame(output_format, native), NativeReplies.PROMPT, HardwareXmlPreset.COMMANDS[output_format]
        )


@pytest.mark.parametrize("output_format", ["xml", "json"])
@pytest.mark.parametrize("field", ["password", "token", "authorization"])
def test_native_inventory_rejects_credential_field_names(output_format: str, field: str) -> None:
    """Inspect XML element names and JSON keys instead of scanning serialized JSON syntax."""
    xml = (
        f"<rpc-reply><chassis-inventory><chassis><{field}>synthetic-value</{field}>"
        "</chassis></chassis-inventory></rpc-reply>"
    )
    native_json = json.dumps({"chassis-inventory": [{"chassis": [{field: [{"data": "synthetic-value"}]}]}]})
    native = xml if output_format == "xml" else native_json
    with pytest.raises(HardwareOutputError, match="credential"):
        HardwareXmlSupport.Decoder.decode_output(
            NativeReplies.frame(output_format, native), NativeReplies.PROMPT, HardwareXmlPreset.COMMANDS[output_format]
        )


@pytest.mark.parametrize("failure", ["collision", "quota"])
def test_one_native_file_failure_does_not_block_the_other_format(tmp_path: Path, failure: str) -> None:
    """Keep independent formats writable after a collision or a format-specific quota failure."""
    artifacts = SessionArtifactService(SimpleNamespace(), None, tmp_path)
    target = BatchTargetRequest(
        "target", {"device_id": "device", "label": "EX"}, SessionManagerFixture()._shell_request()
    )
    writer = artifacts.prepare_batch((target,), {"preset": HardwareXmlPreset.NAME, "format": "both"})
    xml_path = tmp_path / writer.artifact_id / HardwareXmlSupport.ArtifactNames.safe_paths(target.identity, "xml")[0]
    if failure == "collision":
        xml_path.parent.mkdir(parents=True)
        xml_path.write_bytes(b"existing")
    else:
        artifacts.OUTPUT_LIMIT = len(NativeReplies.JSON.encode())
    documents = {
        output_format: HardwareXmlSupport.Decoder.decode_output(
            NativeReplies.frame(output_format, getattr(NativeReplies, output_format.upper())),
            NativeReplies.PROMPT,
            HardwareXmlPreset.COMMANDS[output_format],
        )
        for output_format in ("xml", "json")
    }
    with pytest.raises(StreamRequestError) as refusal:
        writer.write_hardware(target.target_key, target.identity, documents["xml"], "xml")
    assert refusal.value.code == "output_failed"
    files = writer.write_hardware(target.target_key, target.identity, documents["json"], "json")
    assert (tmp_path / writer.artifact_id / files[0]).read_bytes() == NativeReplies.JSON.encode()
    if failure == "collision":
        assert xml_path.read_bytes() == b"existing"
    else:
        assert not xml_path.exists()


@pytest.mark.parametrize("status", ["disconnected", "unknown", None])
def test_dispatch_skips_non_online_devices_before_creating_a_shell(status: str | None) -> None:
    """A status change after preview cannot become a command failure or open a shell."""
    request = SessionManagerFixture()._shell_request()
    target = BatchTargetRequest("target", {"device_id": "device"}, request)
    plan = BatchExecutionPlan(
        (target,),
        1,
        commands=(HardwareXmlPreset.COMMAND,),
        output={"preset": HardwareXmlPreset.NAME},
        hardware_status=lambda _identity: status,
    )
    build = Mock()
    batch = BatchRunner(
        replace(request, batch_plan=plan), FakeSink(), build, StreamSettings.from_environment(), SharedTransport(1)
    )
    batch._targets.run(target)
    build.assert_not_called()
    row = plan.progress.summary.target_page(0, 1)["targets"][0]
    assert row["state"] == "skipped"
    assert row["reason_code"] == ("offline" if status == "disconnected" else "unknown_status")
    assert row["command_index"] is None
    assert plan.progress.summary.summary()["counts"]["failed"] == 0


def test_unproven_first_command_prevents_second_command(monkeypatch: pytest.MonkeyPatch) -> None:
    """Do not send JSON when XML never returns to its verified prompt."""
    monkeypatch.setattr(BatchRunner, "QUIET_SECONDS", 0)
    request = SessionManagerFixture()._shell_request()
    target = BatchTargetRequest("target", {"device_id": "device"}, request)
    plan = BatchExecutionPlan(
        (target,),
        1,
        commands=tuple(HardwareXmlPreset.COMMANDS.values()),
        output={"preset": HardwareXmlPreset.NAME, "format": "both"},
    )
    batch = BatchRunner(
        replace(request, batch_plan=plan), FakeSink(), Mock(), StreamSettings.from_environment(), SharedTransport(1)
    )
    terminal = batch._registry.terminal()
    sink = BatchRunner.TargetSink(FakeSink(), plan, target, terminal)
    terminal.history.append(NativeReplies.PROMPT.encode())
    sender = Mock()
    monkeypatch.setattr(batch._shell, "_command_prompt", lambda *_args: (0, False))
    plan.progress.transitions.transition(target.target_key, "running")
    batch._shell.collect(SimpleNamespace(send_input=sender), sink, target, terminal)
    sender.assert_called_once_with(HardwareXmlPreset.COMMANDS["xml"] + "\n")
    row = plan.progress.summary.target_page(0, 1)["targets"][0]
    assert row["reason_code"] == "completion_unproven"
    assert row["formats"]["xml"]["state"] == "failed"
    assert row["formats"]["json"]["state"] == "not_attempted"


def test_initial_readiness_waits_for_complete_stable_cli_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ignore banners and fragmented prompt candidates until the CLI prompt remains stable."""
    request = SessionManagerFixture()._shell_request()
    target = BatchTargetRequest("target", {"device_id": "device"}, request)
    batch = BatchRunner(
        replace(request, batch_plan=BatchExecutionPlan((target,), 1)),
        FakeSink(),
        Mock(),
        StreamSettings.from_environment(),
        SharedTransport(1),
    )
    terminal = batch._registry.terminal()
    clock = [0.0]
    pages = [(0.1, b"Welcome >"), (0.1, b"\r\nmist@"), (0.1, b"EX>"), (1.0, b"\r\n{master:0}\r\nmist@EX>"), (2.1, b"")]

    def read_page(after: int, wait_seconds: float) -> HistoryRead:
        """Advance deterministic time while preserving ordered terminal bytes."""
        elapsed, data = pages.pop(0)
        clock[0] += elapsed
        return HistoryRead(data, after, after + len(data), 0, False)

    monkeypatch.setattr(terminal.history, "read", read_page)
    monkeypatch.setattr(
        "src.mist.realtime.websocket_streams.live.sessions.manager.factory.time.monotonic", lambda: clock[0]
    )
    cursor, prompt = batch._shell._initial_prompt(terminal)
    assert prompt == NativeReplies.PROMPT
    assert cursor > 0 and not pages
    assert BatchRunner.Prompt._prompt(b"<rpc-reply>") is None


@pytest.mark.parametrize(
    "native_json",
    [
        '{"chassis-inventory":',
        "{}",
        '{"chassis-inventory":[]}',
        '{"chassis-inventory":[1]}',
        '{"chassis-inventory":[{}],"bad":NaN}',
    ],
)
def test_invalid_native_json_never_becomes_a_success_file(native_json: str) -> None:
    """Reject malformed, empty, incorrect, or nonstandard native JSON."""
    with pytest.raises(HardwareOutputError):
        HardwareXmlSupport.Decoder.decode_output(
            NativeReplies.frame("json", native_json), NativeReplies.PROMPT, HardwareXmlPreset.COMMANDS["json"]
        )


def test_preview_explains_offline_and_unknown_exclusions(tmp_path: Path) -> None:
    """Only explicit current connected status makes an EX target eligible."""
    picker = FakeBatchPicker(device_target=True)
    picker.site_rows = picker.site_rows[:1]
    picker.target_rows = [
        {
            "id": f"44444444-4444-4444-8444-{index:012d}",
            "device_id": f"44444444-4444-4444-8444-{index:012d}",
            "label": status,
            "family": "ex",
            "target_type": "device",
            "status": status,
        }
        for index, status in enumerate(("connected", "disconnected", "unknown"))
    ]
    service = make_batch_service(FakeBatchChecker(hardware_shell_definition()), picker, FakeManager(), tmp_path)
    preview = service.preview({"preset": HardwareXmlPreset.NAME, "format": "both", "scope_revision": 1})
    assert preview["target_count"] == 1
    assert preview["excluded"]["offline"] == 1
    assert preview["excluded"]["unknown_status"] == 1
    assert preview["confirmation"]["phrase"] == "RUN 1 TARGETS"


@pytest.mark.parametrize("http_status", [200, 403, 503])
def test_status_read_uses_fresh_running_stats_and_fails_closed(
    monkeypatch: pytest.MonkeyPatch, http_status: int
) -> None:
    """Read live status on every check and reject failed SDK pages."""
    response = SimpleNamespace(status_code=http_status, data=[{"id": "device", "status": "connected"}], next=None)
    read_stats = Mock(return_value=response)
    monkeypatch.setattr(mistapi.api.v1.sites.stats, "listSiteDevicesStats", read_stats)
    picker = StreamPickerService(object(), "organization")
    if http_status != 200:
        with pytest.raises(StreamRequestError):
            picker.device_statuses("site")
        return
    assert picker.device_statuses("site") == {"device": "connected"}
    response.data = [{"id": "device", "status": "disconnected"}]
    assert picker.device_statuses("site") == {"device": "disconnected"}
    assert read_stats.call_count == 2
    assert read_stats.call_args.kwargs["type"] == "all"


def test_hardware_run_survives_session_expiry_restart_and_new_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Preserve successful native files and partial outcomes without automatic cleanup or overwrites."""
    manager = SimpleNamespace(session=lambda _session: SimpleNamespace(live=False))
    artifacts = SessionArtifactService(manager, None, tmp_path)
    request = SessionManagerFixture()._shell_request()
    target = BatchTargetRequest("target", {"device_id": "device", "label": "EX"}, request)
    output = {"preset": HardwareXmlPreset.NAME, "format": "both"}
    writer = artifacts.prepare_batch((target,), output)
    document = HardwareXmlSupport.Decoder.decode_output(
        NativeReplies.frame("xml", NativeReplies.XML), NativeReplies.PROMPT, HardwareXmlPreset.COMMAND
    )
    files = writer.write_hardware(target.target_key, target.identity, document, "xml")
    pending = json.loads((tmp_path / writer.artifact_id / "manifest.json").read_text())
    assert pending["partial"] is True
    assert pending["files"] == list(files)
    assert pending["targets"][0]["formats"]["xml"]["state"] == "completed"
    writer.finish(
        [
            {
                "target": dict(target.identity),
                "state": "failed",
                "files": list(files),
                "formats": {"xml": {"state": "completed"}, "json": {"state": "failed"}},
            }
        ]
    )
    artifacts.bind_batch("session", writer)
    assert artifacts.cleanup_expired("session") is True
    restarted = SessionArtifactService(manager, None, tmp_path)
    monkeypatch.setattr(restarted._storage.retention, "process_is_alive", lambda _pid: False)
    second = restarted.prepare_batch((target,), output)
    assert second.artifact_id != writer.artifact_id
    path = tmp_path / writer.artifact_id
    assert (path / files[0]).read_bytes() == NativeReplies.XML.encode()
    manifest = json.loads((path / "manifest.json").read_text())
    assert manifest["durable"] is True and manifest["partial"] is True
    assert manifest["targets"][0]["formats"]["json"]["state"] == "failed"
    with pytest.raises(StreamRequestError):
        writer.write_hardware(target.target_key, target.identity, document, "xml")
    assert (path / files[0]).read_bytes() == NativeReplies.XML.encode()
