"""Shared data objects for RF diagnostics runs."""

from __future__ import annotations  # WHY: allow compact type hints on Python 3.13.

from dataclasses import dataclass  # WHY: store run records with explicit fields.
from pathlib import Path  # WHY: represent download paths without platform-specific separators.
from typing import Any  # WHY: Mist API payloads can contain mixed JSON values.

STATUS_CANCELLED = "cancelled"  # WHY: one value marks an operator refusal or interruption.
STATUS_FAILED = "failed"  # WHY: one value marks an API, wait, or file write failure.
STATUS_SUCCESS = "success"  # WHY: one value marks a completed diagnostic run.
STATUS_TIMEOUT = "timeout"  # WHY: one value marks a bounded poll that reached its limit.
MODE_RECORDING = "recording"  # WHY: audit rows need one stable value for RF recordings.
MODE_SPECTRUM = "spectrum"  # WHY: audit rows need one stable value for spectrum analysis.


@dataclass(frozen=True)
class SpectrumAnalysisSession:
    """Store the result of one spectrum analysis start or poll."""

    site_id: str  # WHY: the site identifies the API scope.
    device_id: str  # WHY: the AP identifies the RF source.
    status: str  # WHY: the runner needs one state value to decide whether polling continues.
    payload: dict[str, Any]  # WHY: keep the raw Mist result for the operator summary.


@dataclass(frozen=True)
class RfDiagnosticRecording:
    """Store the state of one RF diagnostic recording."""

    site_id: str  # WHY: the site identifies the API scope.
    client_mac: str  # WHY: the client MAC identifies the target.
    rfdiag_id: str  # WHY: stop, get, and download calls need this identifier.
    status: str  # WHY: the runner needs one state value for audit output.
    payload: dict[str, Any]  # WHY: keep the raw Mist result for troubleshooting.


@dataclass(frozen=True)
class RfDiagnosticFile:
    """Describe a downloaded RF diagnostic file."""

    path: Path  # WHY: callers print and audit the saved path.
    byte_count: int  # WHY: zero bytes means the download failed.


@dataclass(frozen=True)
class RfDiagnosticRun:
    """Describe one row in the RF diagnostics audit file."""

    mode: str  # WHY: operators must distinguish spectrum and recording rows.
    site_id: str  # WHY: the site names the Mist scope.
    target: str  # WHY: the target is an AP identifier or a client MAC.
    started_at: str  # WHY: the run start time orders rows.
    status: str  # WHY: status states the final outcome.
    result_reference: str  # WHY: this is the session id, file path, or failure reason.

    @staticmethod
    def column_names() -> list[str]:
        """Return the stable CSV column order."""
        return [  # WHY: keep the CSV header stable across runs.
            "mode",  # WHY: first column groups the two diagnostic modes.
            "site_id",  # WHY: second column names the API scope.
            "target",  # WHY: third column names the AP or client.
            "started_at",  # WHY: fourth column sorts the audit trail.
            "status",  # WHY: fifth column gives the final result.
            "result_reference",  # WHY: final column points to details or a file.
        ]

    def as_row(self) -> dict[str, str]:
        """Return this run as a CSV-ready dictionary."""
        return {  # WHY: csv.DictWriter expects a mapping of column names to values.
            "mode": self.mode,  # WHY: include the diagnostic mode in every row.
            "site_id": self.site_id,  # WHY: include the Mist site in every row.
            "target": self.target,  # WHY: include the AP or client target in every row.
            "started_at": self.started_at,  # WHY: include the operator run time in every row.
            "status": self.status,  # WHY: include the final outcome in every row.
            "result_reference": self.result_reference,  # WHY: include the detail pointer in every row.
        }
