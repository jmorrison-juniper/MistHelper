"""Interactive operation for RF diagnostics menu 290."""

from __future__ import annotations  # WHY: keep annotations import-safe.

import logging  # WHY: log each operation action before and after it.
from datetime import UTC, datetime  # WHY: build recording names with a stable timestamp.
from typing import Any  # WHY: dependency resolver returns dynamic helpers.

from src.foundation.runtime.config.source_dependency_resolver import (
    SourceDependencyResolver,
)  # WHY: read shared session and helpers.
from src.mist.intelligence.troubleshooting.rf_diagnostics.audit import (
    RfDiagnosticsAuditWriter,
)  # WHY: persist one audit row per run.
from src.mist.intelligence.troubleshooting.rf_diagnostics.client import RfDiagnosticsClient  # WHY: wrap Mist API calls.
from src.mist.intelligence.troubleshooting.rf_diagnostics.file_naming import (
    RfDiagnosticFileNamer,
)  # WHY: normalize MAC input.
from src.mist.intelligence.troubleshooting.rf_diagnostics.models import (
    STATUS_CANCELLED,
    RfDiagnosticRun,
)  # WHY: audit cancellations.
from src.mist.intelligence.troubleshooting.rf_diagnostics.recording import (
    RfDiagnosticRecordingRunner,
)  # WHY: run recording mode.
from src.mist.intelligence.troubleshooting.rf_diagnostics.spectrum import (
    SpectrumAnalysisRunner,
)  # WHY: run spectrum mode.

logger = logging.getLogger(__name__)  # WHY: make menu 290 logs easy to filter.


class RfDiagnosticsOperation:
    """Run spectrum analysis or RF diagnostic recording from menu 290."""

    @staticmethod
    def run() -> None:
        """Ask for a mode, run it, and write one audit row."""
        logger.info("Menu #290: Starting RF diagnostics")  # WHY: name the menu row at start.
        operation = RfDiagnosticsOperation()  # WHY: one instance keeps helper methods short.
        operation._run()  # WHY: static handler delegates to instance collaborators.

    def __init__(self) -> None:
        """Create default collaborators from the shared application context."""
        self._client = RfDiagnosticsClient(SourceDependencyResolver.apisession)  # WHY: use the active Mist session.
        self._audit = RfDiagnosticsAuditWriter()  # WHY: default audit target is data/RfDiagnostics.csv.
        self._input = SourceDependencyResolver.InputUtils.safe_input  # WHY: use the EOF-safe prompt wrapper.

    def _run(self) -> None:
        """Dispatch the selected RF diagnostic mode."""
        mode = self._ask_mode()  # WHY: operator chooses one of two safe flows.
        if mode == "1":  # WHY: mode 1 is spectrum analysis.
            self._run_spectrum()  # WHY: keep spectrum prompts and execution together.
            return  # WHY: do not fall through to recording.
        if mode == "2":  # WHY: mode 2 is RF diagnostic recording.
            self._run_recording()  # WHY: keep recording prompts and execution together.
            return  # WHY: operation is complete.
        logger.info(
            "RF diagnostics cancelled before a mode was selected"
        )  # WHY: empty or unknown input is safe cancel.

    def _ask_mode(self) -> str:
        """Ask which RF diagnostic mode to run."""
        logger.info("Prompting for RF diagnostics mode")  # WHY: action log before prompt.
        answer = self._input(  # WHY: safe input handles EOF and Ctrl+C.
            "Select RF diagnostic mode: 1=spectrum analysis, 2=RF diagnostic recording, Enter=cancel: ",
            default_value="",
            allow_empty=True,
            context="rf_diagnostics.mode",
        )
        logger.debug("RF diagnostics mode answer_present=%s", bool(answer))  # WHY: do not log full free text.
        return str(answer).strip()  # WHY: downstream comparisons use trimmed text.

    def _run_spectrum(self) -> None:
        """Prompt and run AP spectrum analysis."""
        site_id = self._select_site()  # WHY: every Mist call needs a site.
        device_id = self._ask_required("Enter AP device ID: ", "rf_diagnostics.ap")  # WHY: API requires AP id.
        band = self._ask_default("Enter band (24, 5, or 6) [5]: ", "5", "rf_diagnostics.band")  # WHY: band required.
        duration = self._ask_int("Enter duration seconds [300]: ", 300, "rf_diagnostics.spectrum_duration")
        if not self._confirm("Start spectrum analysis now? [y/N]: "):  # WHY: acceptance requires y or N before start.
            self._write_cancel("spectrum", site_id, device_id)  # WHY: cancelled attempt still gets one audit row.
            return  # WHY: no remote call after decline.
        session, run = SpectrumAnalysisRunner(self._client).run(site_id, device_id, band, duration)  # WHY: run mode.
        self._write_audit(run)  # WHY: one audit row per attempt, with visible failure handling.
        logger.info("Spectrum analysis result: %s", session.payload)  # WHY: operator sees the final result.

    def _run_recording(self) -> None:
        """Prompt and run client RF diagnostic recording."""
        site_id = self._select_site()  # WHY: every Mist call needs a site.
        client_mac = self._ask_mac()  # WHY: request body requires a client MAC for type client.
        duration = self._ask_int(
            "Enter duration seconds, 0 for Ctrl+C stop within 180 seconds [30]: ", 30, "rf_diagnostics.duration"
        )
        if not self._confirm("Start RF diagnostic recording now? [y/N]: "):  # WHY: acceptance requires confirmation.
            self._write_cancel("recording", site_id, client_mac)  # WHY: cancelled attempt still gets one audit row.
            return  # WHY: no remote call after decline.
        name = self._recording_name(client_mac)  # WHY: Mist requires a recording name.
        recording, diagnostic_file, run = RfDiagnosticRecordingRunner(self._client).run(
            site_id, client_mac, duration, name
        )
        self._write_audit(run)  # WHY: one audit row per attempt, with visible failure handling.
        self._report_recording(recording.rfdiag_id, diagnostic_file)  # WHY: operator gets the file path or failure.

    @staticmethod
    def _select_site() -> str:
        """Ask for a site with the shared prompt helper."""
        logger.info("Prompting for RF diagnostics site")  # WHY: action log before site prompt.
        site_id = SourceDependencyResolver.PromptUtils.select_site_with_logging()  # WHY: reuse existing chooser.
        logger.debug("RF diagnostics selected site_id=%s", site_id)  # WHY: result summary after site prompt.
        return str(site_id)  # WHY: Mist SDK expects a string path parameter.

    def _ask_required(self, prompt: str, context: str) -> str:
        """Ask for a required text value."""
        value = self._input(prompt, default_value="", allow_empty=False, context=context).strip()  # WHY: safe prompt.
        if not value:  # WHY: empty value cannot build a safe request body.
            raise ValueError("A required RF diagnostics value was not supplied.")  # WHY: fail before API calls.
        return value  # WHY: caller uses validated text.

    def _ask_default(self, prompt: str, default: str, context: str) -> str:
        """Ask for text and return a default when blank."""
        value = self._input(
            prompt, default_value=default, allow_empty=True, context=context
        ).strip()  # WHY: safe prompt.
        return value or default  # WHY: keep caller defaults explicit.

    def _ask_int(self, prompt: str, default: int, context: str) -> int:
        """Ask for an integer and return a default on invalid input."""
        value = self._input(
            prompt, default_value=str(default), allow_empty=True, context=context
        ).strip()  # WHY: safe prompt.
        try:  # WHY: operator text can be invalid.
            return int(value)  # WHY: duration APIs require an integer.
        except ValueError:  # WHY: invalid duration should not crash the menu.
            logger.warning("Invalid integer for %s. Using default %s", context, default)  # WHY: visible repair.
            return default  # WHY: safe bounded default.

    def _ask_mac(self) -> str:
        """Ask for and normalize a client MAC address."""
        value = self._ask_required("Enter client MAC address: ", "rf_diagnostics.client_mac")  # WHY: target required.
        return RfDiagnosticFileNamer.normalize_mac(value)  # WHY: request body and file name use one normalized MAC.

    def _confirm(self, prompt: str) -> bool:
        """Return True only for a lowercase or uppercase y answer."""
        logger.info("Prompting for RF diagnostics confirmation")  # WHY: action log before confirmation.
        answer = self._input(prompt, default_value="N", allow_empty=True, context="rf_diagnostics.confirm")
        confirmed = str(answer).strip().lower() == "y"  # WHY: only y starts a remote diagnostic.
        logger.debug("RF diagnostics confirmation accepted=%s", confirmed)  # WHY: result summary after prompt.
        return confirmed  # WHY: caller gates side effects with this value.

    def _write_cancel(self, mode: str, site_id: str, target: str) -> None:
        """Write one cancellation audit row."""
        started_at = datetime.now(UTC).isoformat(timespec="seconds")  # WHY: cancellation rows need an order time.
        run = RfDiagnosticRun(mode, site_id, target, started_at, STATUS_CANCELLED, "operator declined")
        self._write_audit(run)  # WHY: acceptance requires one row per run attempt.
        logger.info("RF diagnostics %s cancelled before start", mode)  # WHY: operator-visible cancellation.

    def _write_audit(self, run: RfDiagnosticRun) -> None:
        """Write one audit row or report the failed persistence."""
        if self._audit.append(run):  # WHY: normal path confirms persistence.
            logger.debug("RF diagnostics audit row persisted status=%s", run.status)  # WHY: result summary.
            return  # WHY: no error to report.
        logger.error("RF diagnostics audit row was not written for mode %s", run.mode)  # WHY: visible failure path.

    @staticmethod
    def _recording_name(client_mac: str) -> str:
        """Return a Mist-visible recording name."""
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")  # WHY: names must be unique enough for operators.
        return f"misthelper-rfdiag-{client_mac}-{timestamp}"  # WHY: name states source tool and target client.

    @staticmethod
    def _report_recording(rfdiag_id: str, diagnostic_file: Any) -> None:
        """Report recording completion or failure to the operator."""
        if diagnostic_file is None:  # WHY: failed downloads produce no file object.
            logger.error("RF diagnostic recording %s did not produce a file", rfdiag_id)  # WHY: clear failure line.
            return  # WHY: no path to print.
        logger.info("RF diagnostic recording %s saved to %s", rfdiag_id, diagnostic_file.path)  # WHY: success line.
