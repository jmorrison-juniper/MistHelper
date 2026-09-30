"""Unit tests for RF diagnostics client request bodies."""

from __future__ import annotations  # WHY: keep annotations import-safe.

from dataclasses import dataclass  # WHY: fake SDK responses mimic APIResponse.data.
from pathlib import Path  # WHY: wiring manifest test reads the feature file.
from typing import Any  # WHY: fake SDK accepts dynamic request bodies.

from src.troubleshooting.rf_diagnostics.client import RfDiagnosticsClient  # WHY: test target.


@dataclass
class FakeResponse:
    """Small response object with the SDK data attribute."""

    data: Any  # WHY: client code reads response.data when present.


class FakeRfdiags:
    """Capture RF diagnostic SDK calls."""

    def __init__(self) -> None:
        """Create call capture storage."""
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []  # WHY: tests assert shape after calls.

    def startSiteRecording(self, *args: Any) -> FakeResponse:
        """Capture start recording calls."""
        self.calls.append(("start", args, {}))  # WHY: record exact positional call shape.
        return FakeResponse({"id": "rf1"})  # WHY: return a usable fake id.

    def stopSiteRfdiagRecording(self, *args: Any) -> FakeResponse:
        """Capture stop recording calls."""
        self.calls.append(("stop", args, {}))  # WHY: record stop path parameters.
        return FakeResponse({})  # WHY: stop has no useful body.

    def downloadSiteRfdiagRecording(self, *args: Any) -> FakeResponse:
        """Capture download calls."""
        self.calls.append(("download", args, {}))  # WHY: record download path parameters.
        return FakeResponse(b"abc")  # WHY: return bytes for saving.

    def getSiteRfdiagRecording(self, *args: Any) -> FakeResponse:
        """Capture get recording calls."""
        self.calls.append(("get", args, {}))  # WHY: record get path parameters.
        return FakeResponse({"id": "rf1"})  # WHY: return a minimal recording.

    def getSiteSiteRfdiagRecording(self, *args: Any, **kwargs: Any) -> FakeResponse:
        """Capture list recording calls."""
        self.calls.append(("list", args, kwargs))  # WHY: record generated OpenAPI list name.
        return FakeResponse([])  # WHY: return an empty list.


class FakeAnalyzeSpectrum:
    """Capture spectrum SDK calls."""

    def __init__(self) -> None:
        """Create call capture storage."""
        self.calls: list[tuple[Any, ...]] = []  # WHY: tests assert request body shape.

    def initiateSiteAnalyzeSpectrum(self, *args: Any) -> FakeResponse:
        """Capture start spectrum calls."""
        self.calls.append(args)  # WHY: store full call for assertions.
        return FakeResponse({"session": "s1"})  # WHY: return a minimal start response.


class FakeSdk:
    """Provide the nested SDK attributes used by the client."""

    def __init__(self) -> None:
        """Build the fake SDK tree."""
        self.rfdiags = FakeRfdiags()  # WHY: tests inspect RF diagnostic calls.
        self.analyze_spectrum = FakeAnalyzeSpectrum()  # WHY: tests inspect spectrum calls.
        sites = type("Sites", (), {"rfdiags": self.rfdiags, "analyze_spectrum": self.analyze_spectrum})  # WHY: tree.
        v1 = type("V1", (), {"sites": sites})  # WHY: mimic mistapi.api.v1.
        self.api = type("Api", (), {"v1": v1})  # WHY: mimic mistapi.api.


class FakeSession:
    """Capture fallback Mist API calls."""

    def __init__(self) -> None:
        """Create call capture storage."""
        self.paths: list[str] = []  # WHY: tests assert the fallback path.

    def mist_get(self, path: str) -> FakeResponse:
        """Capture generic GET calls."""
        self.paths.append(path)  # WHY: SDK lacks running spectrum method.
        return FakeResponse({"status": "complete"})  # WHY: return a final spectrum payload.


def test_spectrum_start_body_matches_openapi_shape() -> None:
    """Spectrum start sends only the documented fields."""
    sdk = FakeSdk()  # WHY: isolate the client from the real SDK.
    client = RfDiagnosticsClient(FakeSession(), sdk=sdk)  # WHY: inject fake dependencies.
    client.start_spectrum("site1", "ap1", "5", 300)  # WHY: exercise request body creation.
    body = sdk.analyze_spectrum.calls[0][2]  # WHY: third argument is the JSON body.
    assert body == {"band": "5", "device_id": "ap1", "duration": 300, "format": "json"}  # WHY: exact shape.


def test_running_spectrum_uses_body_free_fallback_path() -> None:
    """Running spectrum uses the documented fallback path with no body."""
    session = FakeSession()  # WHY: capture generic GET paths.
    client = RfDiagnosticsClient(session, sdk=FakeSdk())  # WHY: inject fake SDK and session.
    client.get_running_spectrum("site1")  # WHY: exercise fallback method.
    assert session.paths == ["/api/v1/sites/site1/analyze_spectrum"]  # WHY: exact OpenAPI path.


def test_recording_start_body_matches_openapi_shape() -> None:
    """Recording start sends only the documented fields."""
    sdk = FakeSdk()  # WHY: isolate the client from the real SDK.
    client = RfDiagnosticsClient(FakeSession(), sdk=sdk)  # WHY: inject fake dependencies.
    client.start_recording("site1", "name1", "aabbccddeeff", 30)  # WHY: exercise request body creation.
    body = sdk.rfdiags.calls[0][1][2]  # WHY: third positional argument is the JSON body.
    assert body == {"name": "name1", "type": "client", "mac": "aabbccddeeff", "duration": 30}  # WHY: exact.


def test_recording_body_clamps_duration_to_openapi_range() -> None:
    """Recording body clamps duration to the OpenAPI range."""
    high = RfDiagnosticsClient.recording_body("name1", "aabbccddeeff", 999)  # WHY: operator input can exceed schema.
    low = RfDiagnosticsClient.recording_body("name1", "aabbccddeeff", 0)  # WHY: operator Ctrl+C mode sends zero.
    assert high["duration"] == 180  # WHY: OpenAPI maximum is 180 seconds.
    assert low["duration"] == 180  # WHY: zero uses operator-stop mode bounded by cloud maximum.


def test_recording_stop_download_and_list_use_expected_operations() -> None:
    """Stop, download, and list use the OpenAPI operation names."""
    sdk = FakeSdk()  # WHY: isolate the client from the real SDK.
    client = RfDiagnosticsClient(FakeSession(), sdk=sdk)  # WHY: inject fake dependencies.
    client.stop_recording("site1", "rf1")  # WHY: exercise stop call.
    client.download_recording("site1", "rf1")  # WHY: exercise download call.
    client.list_recordings("site1", limit=10)  # WHY: exercise generated list call.
    assert [call[0] for call in sdk.rfdiags.calls] == ["stop", "download", "list"]  # WHY: operations match.
    assert sdk.rfdiags.calls[2][2] == {"limit": 10}  # WHY: list call sends query parameters as kwargs.


def test_confirmation_accepts_only_y() -> None:
    """The operation confirmation starts a run only for y."""
    from src.troubleshooting.rf_diagnostics.operation import (
        RfDiagnosticsOperation,
    )  # WHY: import here avoids setup cost.

    operation = RfDiagnosticsOperation.__new__(RfDiagnosticsOperation)  # WHY: bypass resolver-backed constructor.
    operation._input = lambda *args, **kwargs: ""  # WHY: Enter must default to N.
    assert operation._confirm("Start? [y/N]: ") is False  # WHY: Enter cannot start a remote diagnostic.
    operation._input = lambda *args, **kwargs: "Y"  # WHY: uppercase y should be accepted.
    assert operation._confirm("Start? [y/N]: ") is True  # WHY: explicit y starts the diagnostic.
    operation._input = lambda *args, **kwargs: "yes"  # WHY: any value other than y must be rejected.
    assert operation._confirm("Start? [y/N]: ") is False  # WHY: only y is accepted by the safety rule.


def test_wiring_manifest_lists_deferred_integration_files() -> None:
    """The wiring manifest carries the exact deferred integration files."""
    repo_root = Path(__file__).resolve().parents[4]  # WHY: pytest can run from a changed working directory.
    text = (repo_root / "specs" / "3570-spectrum-rfdiag" / "wiring.md").read_text(
        encoding="utf-8"
    )  # WHY: read manifest.
    required = [  # WHY: every file here is forbidden to this package pull request.
        "MistHelper.py",
        "src/utils/operation_registry.py",
        "src/refactors/endpoint_primary_key_strategies.py",
        "README.md",
        "documentation/menu_reference.md",
        ".github/copilot-instructions.md",
    ]
    for item in required:  # WHY: check each deferred file explicitly.
        assert item in text  # WHY: integration agent must find the deferred file name.


class FakeAuditFailure:
    """Fake audit writer that reports a failed write."""

    def __init__(self) -> None:
        """Create call capture storage."""
        self.rows: list[Any] = []  # WHY: test verifies that one write was attempted.

    def append(self, run: Any) -> bool:
        """Record the attempted row and report failure."""
        self.rows.append(run)  # WHY: the operation must attempt one audit write.
        return False  # WHY: simulate disk failure without touching the file system.


def test_operation_reports_audit_write_failure(caplog) -> None:
    """Operation audit helper logs when persistence fails."""
    from src.troubleshooting.rf_diagnostics.models import RfDiagnosticRun  # WHY: build one audit row.
    from src.troubleshooting.rf_diagnostics.operation import RfDiagnosticsOperation  # WHY: test helper method.

    operation = RfDiagnosticsOperation.__new__(RfDiagnosticsOperation)  # WHY: bypass resolver-backed constructor.
    operation._audit = FakeAuditFailure()  # WHY: inject failing audit writer.
    row = RfDiagnosticRun("spectrum", "site1", "ap1", "t1", "success", "ok")  # WHY: one audit attempt.
    operation._write_audit(row)  # WHY: exercise visible failure path.
    assert len(operation._audit.rows) == 1  # WHY: exactly one write attempt was made.
    assert "was not written" in caplog.text  # WHY: failed persistence is visible.
