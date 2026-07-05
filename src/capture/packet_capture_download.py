"""Download and poll helpers for packet capture workflows."""

from __future__ import annotations  # WHY: Defer annotation evaluation for lightweight forward references.

import logging  # WHY: Emit structured before/after action logs for capture download workflows.
import os  # WHY: Resolve and verify local file paths for downloaded PCAP artifacts.
import time  # WHY: Pace poll loops while waiting for capture files to become available.
from collections.abc import Callable  # WHY: Type poll/list callbacks without runtime-heavy imports.
from dataclasses import dataclass  # WHY: Group multi-parameter context objects immutably.
from pathlib import Path  # WHY: Build output file paths in a cross-platform-safe way.
from typing import Any  # WHY: Support Mist API response payloads with flexible structures.

import requests  # WHY: Download PCAP binaries from Mist-provided URLs.

_STEP_CHECK_BANNER = (
    "\n[Step 1/3] Checking for completed PCAPs in last 24 hours..."  # WHY: Legacy operator banner preserved.
)
_STEP_DOWNLOAD_BANNER = (
    "\n[Step 2/3] Checking for new PCAPs to download..."  # WHY: Legacy download step banner preserved as constant.
)
_STEP_NO_PENDING_BANNER = (
    "\n[Step 2/3] No completed PCAPs available for download"  # WHY: Legacy no-op banner preserved as constant.
)
_NO_NEW_DOWNLOADS_MSG = (
    "\n  No new PCAPs to download (all already exist locally)"  # WHY: Legacy summary preserved as constant.
)
_POLL_INTERVAL_SEC = 5  # WHY: Legacy five-second poll cadence preserved for PCAP availability checks.
_POLL_BUFFER_SEC = 120  # WHY: Historic post-capture processing buffer preserved before timing out.
_HTTP_OK = 200  # WHY: Named constant replaces repeated magic 200 across status checks.
_DEFAULT_TIMEOUT_SEC = 300  # WHY: Historic request timeout for both stream and one-shot PCAP fetches.
_STREAM_CHUNK_BYTES = 8192  # WHY: Legacy chunk size used when streaming large PCAPs to disk.
_BYTES_PER_MB = 1024 * 1024  # WHY: Reused MB conversion constant avoids duplicated arithmetic literals.
_FILENAME_TEMPLATE = "PacketCapture_{capture_id}.pcap"  # WHY: Historic filename pattern used by MistHelper tooling.
_SAVE_FILENAME_TEMPLATE = "PacketCapture_{prefix}{capture_id}.pcap"  # WHY: Save-step filename pattern preserved.
_DEFAULT_OUTPUT_DIR = Path("data")  # WHY: Historic default output directory reused by save flow.


@dataclass(frozen=True, slots=True)  # WHY: Frozen slots keep pending-download context immutable and hashable.
class _PendingItem:  # WHY: Group per-item download attributes into one value.
    """Immutable per-capture download context extracted for the pending scan."""

    capture_id: str  # WHY: Normalized identifier used in filenames, logs, and user output.
    pcap_url: str  # WHY: Normalized download URL passed to the streaming helper.
    filename: str  # WHY: Legacy expected filename derived from the capture identifier.
    local_path: str  # WHY: Absolute local write path derived from filename + folder.


@dataclass(frozen=True, slots=True)  # WHY: Frozen slots keep polling context immutable across helpers.
class _PollContext:  # WHY: Collapse repeated poll parameters into a single value passed by reference.
    """Immutable polling context grouping list callback, identifiers, and pacing values."""

    list_captures_fn: Callable[[], Any]  # WHY: Callback that returns the current list-capture response.
    capture_id: str  # WHY: Target capture identifier scanned inside each poll attempt.
    max_polls: int  # WHY: Bounded poll count so the loop stops when the wait budget expires.
    start_time: float  # WHY: Baseline wall-clock time used for elapsed and timeout math.
    sleep_fn: Callable[[float], None]  # WHY: Injected sleep hook so tests can bypass real pacing.


class PacketCaptureDownloadManager:
    """Encapsulate PCAP polling and download responsibilities for packet capture flows."""

    def fetch_completed_pcaps(self, list_captures_fn: Callable[[], Any], iteration: int) -> list[dict[str, Any]]:
        """Fetch completed PCAP records that expose download URLs."""
        print(_STEP_CHECK_BANNER)  # WHY: Preserve the user-facing loop banner before the API call.
        logging.info("Loop iteration %s: Fetching PCAP list from API", iteration)  # WHY: Log list op before API call.
        pcaps_response = self._invoke_list_callback(list_captures_fn, iteration)  # WHY: Isolate API call try/except.
        if pcaps_response is None:  # WHY: Guard failure path so loop mode continues safely.
            return []  # WHY: Return no completed PCAPs so the loop can continue safely.
        if pcaps_response.status_code != _HTTP_OK:  # WHY: Guard non-success API responses before parsing content.
            return self._log_list_failure(pcaps_response.status_code)  # WHY: Preserve warning output and empty return.
        pcap_list = self.parse_captures_response(pcaps_response.data, iteration)  # WHY: Normalize payload variants.
        return self._select_completed_captures(pcap_list, iteration)  # WHY: Filter+log downloadable captures.

    @staticmethod
    def _invoke_list_callback(list_captures_fn: Callable[[], Any], iteration: int) -> Any:
        """Call the list callback and log status, returning None on failure."""
        try:  # WHY: Catch API/listing failures so loop mode can continue safely.
            pcaps_response = list_captures_fn()  # WHY: Invoke caller-provided list callback for current scope.
            logging.debug(
                "Loop iteration %s: PCAP list callback returned status %s",
                iteration,
                getattr(pcaps_response, "status_code", "unknown"),
            )  # WHY: Log the status code returned by the callback.
            return pcaps_response  # WHY: Return the raw response so caller can inspect status and payload.
        except Exception as list_error:  # pylint: disable=broad-exception-caught  # WHY: Preserve legacy safety net.
            print(f"  Error fetching PCAP list: {list_error}")  # WHY: Preserve existing operator-facing error text.
            logging.exception("Exception listing PCAPs: %s", list_error)  # WHY: Log full list failure details.
            return None  # WHY: Sentinel signals caller to short-circuit to no-downloads result.

    @staticmethod
    def _log_list_failure(status_code: int) -> list[dict[str, Any]]:
        """Emit legacy non-success warning and return an empty completed list."""
        print(f"  Warning: Could not fetch PCAP list (HTTP {status_code})")  # WHY: Preserve existing warning text.
        logging.warning("Failed to list PCAPs: %s", status_code)  # WHY: Log non-success status for audit visibility.
        return []  # WHY: Treat failed list calls as no-download rounds to preserve prior behavior.

    @staticmethod
    def _select_completed_captures(pcap_list: list[dict[str, Any]], iteration: int) -> list[dict[str, Any]]:
        """Retain downloadable captures and emit legacy count logs."""
        completed = [
            pcap for pcap in pcap_list if PacketCaptureDownloadManager._is_downloadable(pcap)
        ]  # WHY: Keep only downloadable PCAP entries to match existing loop semantics.
        print(f"  Found {len(completed)} completed PCAP(s) with download URLs")  # WHY: Preserve legacy count output.
        logging.debug(
            "Loop iteration %s: Filtered %s completed PCAP entries", iteration, len(completed)
        )  # WHY: Log the filtered count after parsing and selection.
        return completed  # WHY: Hand the downloadable capture records back to the manager loop.

    @staticmethod
    def _is_downloadable(pcap: dict[str, Any]) -> bool:
        """Return True when the record has a pcap_url and identifies as a pcap format."""
        return bool(pcap.get("pcap_url")) and pcap.get("format") == "pcap"  # WHY: Preserve prior filter predicate.

    def download_pending_pcaps(
        self,
        completed_pcaps: list[dict[str, Any]],
        download_folder: str,
        download_single_fn: Callable[[str, str, str, str], int] | None = None,
    ) -> int:
        """Download PCAPs that are not already present on disk."""
        effective_download = download_single_fn or self.download_single_pcap  # WHY: Default to own downloader.
        if not completed_pcaps:  # WHY: Preserve the early-no-op branch when no completed PCAPs are available.
            print(_STEP_NO_PENDING_BANNER)  # WHY: Keep the same loop-step output for empty rounds.
            logging.debug("No completed PCAPs were available for download")  # WHY: Record empty download phase.
            return 0  # WHY: Return zero downloads to preserve the prior loop contract.
        print(_STEP_DOWNLOAD_BANNER)  # WHY: Preserve the loop-step banner before local file checks begin.
        logging.info(
            "Checking %s completed PCAP(s) for pending downloads", len(completed_pcaps)
        )  # WHY: Log the download scan before processing capture entries.
        downloads = self._process_pending_items(
            completed_pcaps, download_folder, effective_download
        )  # WHY: Delegate per-item scan to bounded helper to keep this function short.
        self._print_download_summary(downloads)  # WHY: Emit legacy summary output based on total writes.
        logging.debug(
            "Pending download scan completed with %s new file(s)", downloads
        )  # WHY: Log final scan outcome after all items are processed.
        return downloads  # WHY: Return the number of new files written this round.

    def _process_pending_items(
        self,
        completed_pcaps: list[dict[str, Any]],
        download_folder: str,
        download_single_fn: Callable[[str, str, str, str], int],
    ) -> int:
        """Iterate pending records, download missing files, and return written count."""
        downloads = 0  # WHY: Track number of files newly written during this iteration.
        for pcap in completed_pcaps:  # WHY: Process each downloadable capture record one time in order.
            item = self._prepare_pending_item(pcap, download_folder)  # WHY: Normalize identifier and paths once.
            if os.path.exists(item.local_path):  # WHY: Avoid re-downloading files that already exist locally.
                logging.debug("Skipping %s - already downloaded", item.capture_id)  # WHY: Log local cache hit.
                continue  # WHY: Preserve existing skip behavior for already-downloaded captures.
            downloads += self._download_pending_item(item, download_single_fn)  # WHY: Delegate one HTTP transfer.
        return downloads  # WHY: Return final count so caller can emit summary + logs.

    @staticmethod
    def _prepare_pending_item(pcap: dict[str, Any], download_folder: str) -> _PendingItem:
        """Build the immutable download context for one capture record."""
        capture_id = str(pcap.get("id", ""))  # WHY: Normalize identifier for filenames and logs.
        pcap_url = str(pcap.get("pcap_url", ""))  # WHY: Normalize download URL for the helper callback.
        filename = _FILENAME_TEMPLATE.format(capture_id=capture_id)  # WHY: Preserve historic filename pattern.
        local_path = os.path.join(download_folder, filename)  # WHY: Build local path in a Windows-safe way.
        return _PendingItem(capture_id=capture_id, pcap_url=pcap_url, filename=filename, local_path=local_path)

    @staticmethod
    def _download_pending_item(item: _PendingItem, download_single_fn: Callable[[str, str, str, str], int]) -> int:
        """Emit progress logs, invoke the downloader, and return write count."""
        print(f"\n  --> Downloading PCAP: {item.capture_id}")  # WHY: Preserve per-capture operator progress output.
        logging.info("Starting PCAP download for %s", item.capture_id)  # WHY: Log file download before callback.
        written = download_single_fn(
            item.pcap_url, item.local_path, item.filename, item.capture_id
        )  # WHY: Delegate the actual file transfer to the injected single-download function.
        logging.debug(
            "Download counter after %s is %s", item.capture_id, written
        )  # WHY: Log running download count after callback returns.
        return written  # WHY: Return per-item written count for aggregation.

    @staticmethod
    def _print_download_summary(downloads: int) -> None:
        """Emit the legacy success/no-op summary based on new-write count."""
        if downloads > 0:  # WHY: Match historic summary message for successful download rounds.
            print(f"\n  Downloaded {downloads} new PCAP file(s) this round")  # WHY: Preserve success summary.
            return  # WHY: Skip the all-cached branch when at least one file was written.
        print(_NO_NEW_DOWNLOADS_MSG)  # WHY: Preserve all-cached summary when no writes occurred.

    def download_single_pcap(
        self,
        url: str,
        local_path: str,
        filename: str,
        capture_id: str,
        requests_module: Any = requests,
    ) -> int:
        """Download one PCAP file from its URL and stream it to disk."""
        logging.info("Downloading PCAP %s from %s", capture_id, url)  # WHY: Log outbound download before HTTP call.
        try:  # WHY: Catch transfer and file-write failures so caller can continue safely.
            response = requests_module.get(url, stream=True, timeout=_DEFAULT_TIMEOUT_SEC)  # WHY: Stream file.
            logging.debug("Download response for %s status %s", capture_id, response.status_code)  # WHY: Log status.
            return self._handle_stream_response(response, local_path, filename, capture_id)  # WHY: Bounded helper.
        except Exception as download_error:  # pylint: disable=broad-exception-caught  # WHY: Legacy safety net.
            return self._handle_download_exception(download_error, capture_id)  # WHY: Preserve failure contract.

    @staticmethod
    def _handle_download_exception(download_error: Exception, capture_id: str) -> int:
        """Emit legacy failure output and log exception details before returning zero."""
        print(f"      Error downloading: {download_error}")  # WHY: Preserve existing operator exception text.
        logging.exception(
            "Download exception for %s: %s", capture_id, download_error
        )  # WHY: Log full transfer exception for debugging.
        return 0  # WHY: Preserve prior failure contract when download exceptions occur.

    def _handle_stream_response(
        self,
        response: Any,
        local_path: str,
        filename: str,
        capture_id: str,
    ) -> int:
        """Return early on HTTP failure, otherwise stream chunks and log success."""
        if response.status_code != _HTTP_OK:  # WHY: Stop early when endpoint does not return file content.
            return self._log_stream_failure(response.status_code, capture_id)  # WHY: Preserve legacy failure output.
        self._stream_chunks_to_disk(response, local_path)  # WHY: Delegate write loop to keep this function short.
        self._log_stream_success(local_path, filename, capture_id)  # WHY: Emit legacy success feedback + logs.
        return 1  # WHY: Preserve prior success contract for callers aggregating download counts.

    @staticmethod
    def _stream_chunks_to_disk(response: Any, local_path: str) -> None:
        """Persist streamed chunks to the local file path."""
        with open(local_path, "wb") as pcap_file:  # WHY: Write PCAP stream directly to expected local file path.
            for chunk in response.iter_content(chunk_size=_STREAM_CHUNK_BYTES):  # WHY: Preserve chunk cadence.
                pcap_file.write(chunk)  # WHY: Persist each chunk as it arrives from the HTTP stream.

    @staticmethod
    def _log_stream_failure(status_code: int, capture_id: str) -> int:
        """Emit legacy HTTP failure output and return zero writes."""
        print(f"      Failed to download: HTTP {status_code}")  # WHY: Preserve existing HTTP failure message.
        logging.error(
            "Download failed for %s: %s", capture_id, status_code
        )  # WHY: Log HTTP failure with capture identifier.
        return 0  # WHY: Preserve prior contract for failed downloads.

    @staticmethod
    def _log_stream_success(local_path: str, filename: str, capture_id: str) -> None:
        """Report streamed-file success with legacy size and location output."""
        file_size_mb = os.path.getsize(local_path) / _BYTES_PER_MB  # WHY: Compute size for user feedback and logging.
        print(f"      Downloaded: {filename} ({file_size_mb:.2f} MB)")  # WHY: Preserve success message with size.
        logging.debug("Downloaded PCAP %s to %s", capture_id, local_path)  # WHY: Log final local file path.
        logging.info(
            "Downloaded PCAP %s: %.2f MB", capture_id, file_size_mb
        )  # WHY: Log final size summary for audit evidence.

    def poll_and_download_pcap(
        self,
        list_captures_fn: Callable[[], Any],
        capture_id: str,
        duration: int,
        prefix: str = "",
        save_pcap_file_fn: Callable[[str, str, str], None] | None = None,
    ) -> None:
        """Poll until a PCAP URL is ready, then download the resulting file."""
        self._print_poll_banner(capture_id, duration)  # WHY: Preserve legacy multi-line banner output.
        logging.info(
            "Polling for PCAP availability for capture %s", capture_id
        )  # WHY: Log poll lifecycle before first list call.
        pcap_url: str | None = None  # WHY: Track discovered URL so cancellation/error messages can reuse it.
        try:  # WHY: Catch cancellation and other errors without changing user-visible behavior.
            pcap_url = self.poll_for_pcap_url(
                list_captures_fn, capture_id, duration
            )  # WHY: Wait until download URL becomes available or times out.
            self._save_when_ready(pcap_url, capture_id, prefix, save_pcap_file_fn)  # WHY: Handoff to save helper.
        except KeyboardInterrupt:  # WHY: Preserve user-cancel path exactly as before.
            self._report_cancel(capture_id, pcap_url)  # WHY: Emit legacy cancellation banner + optional URL hint.
        except Exception as error:  # pylint: disable=broad-exception-caught  # WHY: Legacy safety net for surface.
            self._report_poll_error(capture_id, pcap_url, error)  # WHY: Preserve legacy high-level error output.

    @staticmethod
    def _print_poll_banner(capture_id: str, duration: int) -> None:
        """Emit the legacy multi-line polling banner."""
        print(f"\n* Capture initiated (ID: {capture_id})")  # WHY: Preserve capture-start banner before wait begins.
        print(f"  Duration: {duration} seconds (plus processing time)")  # WHY: Preserve existing duration guidance.
        print("  Polling for PCAP file availability...")  # WHY: Preserve readiness wait status line.
        print("  Press Ctrl+C to cancel wait and check portal manually")  # WHY: Preserve manual cancellation guidance.

    def _save_when_ready(
        self,
        pcap_url: str | None,
        capture_id: str,
        prefix: str,
        save_pcap_file_fn: Callable[[str, str, str], None] | None,
    ) -> None:
        """Invoke the save callback once a URL is ready; short-circuit otherwise."""
        if not pcap_url:  # WHY: Preserve the early exit when the URL never appears.
            logging.debug(
                "Polling finished for %s without a downloadable URL", capture_id
            )  # WHY: Log no-URL outcome after poll loop ends.
            return  # WHY: Preserve current no-download outcome when polling times out.
        save_callback = save_pcap_file_fn or self.save_pcap_file  # WHY: Use injected save callback when provided.
        logging.info(
            "PCAP URL resolved for %s; starting file save", capture_id
        )  # WHY: Log handoff from polling to file download.
        save_callback(pcap_url, capture_id, prefix)  # WHY: Save discovered PCAP using caller-selected callback.
        logging.debug(
            "PCAP save callback completed for %s", capture_id
        )  # WHY: Log completion after file-save callback returns.

    @staticmethod
    def _report_cancel(capture_id: str, pcap_url: str | None) -> None:
        """Emit legacy cancellation banner and optional manual-download hint."""
        print("\n\n! Download cancelled by user")  # WHY: Preserve existing cancellation banner.
        print(f"  Capture ID: {capture_id}")  # WHY: Preserve capture identifier shown during cancellation.
        if pcap_url:  # WHY: Only show manual URL when polling already discovered it.
            print(f"  Download manually from: {pcap_url}")  # WHY: Preserve manual-download guidance.

    @staticmethod
    def _report_poll_error(capture_id: str, pcap_url: str | None, error: Exception) -> None:
        """Emit legacy high-level poll error output and optional manual hint."""
        print(f"\n! Error downloading PCAP file: {error}")  # WHY: Preserve existing high-level download error text.
        logging.exception(
            "Exception in poll_and_download_pcap for %s: %s", capture_id, error
        )  # WHY: Log full polling/download exception context.
        if pcap_url:  # WHY: Preserve manual URL hint when one was already discovered.
            print(f"  Try downloading manually from: {pcap_url}")  # WHY: Preserve existing operator recovery guidance.

    def poll_for_pcap_url(
        self,
        list_captures_fn: Callable[[], Any],
        capture_id: str,
        duration: int,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> str | None:
        """Poll the capture list API until the requested PCAP URL is ready."""
        max_wait = duration + _POLL_BUFFER_SEC  # WHY: Preserve historic post-capture processing buffer.
        ctx = _PollContext(
            list_captures_fn=list_captures_fn,
            capture_id=capture_id,
            max_polls=max_wait // _POLL_INTERVAL_SEC,
            start_time=time.time(),
            sleep_fn=sleep_fn,
        )  # WHY: Group polling parameters immutably so helpers stay within 5-param budget.
        logging.info(
            "Polling capture list for %s up to %s seconds", capture_id, max_wait
        )  # WHY: Log bounded polling plan before loop begins.
        for poll_attempt in range(1, ctx.max_polls + 1):  # WHY: Poll until URL appears or timeout budget is exhausted.
            pcap_url = self._poll_once(ctx, poll_attempt)  # WHY: Delegate single-attempt logic to keep loop tight.
            if pcap_url:  # WHY: Stop polling immediately once a downloadable URL is present.
                return pcap_url  # WHY: Return the URL to the caller so the file can be saved.
        return self._report_poll_timeout(capture_id, ctx.start_time)  # WHY: Emit timeout banner and preserve contract.

    def _poll_once(self, ctx: _PollContext, poll_attempt: int) -> str | None:
        """Execute one poll iteration; return the URL or None to keep waiting."""
        try:  # WHY: Catch transient poll failures and continue retrying within same wait budget.
            elapsed = int(time.time() - ctx.start_time)  # WHY: Calculate elapsed time for progress and ready messages.
            response = ctx.list_captures_fn()  # WHY: Invoke caller-provided list callback for current attempt.
            logging.debug(
                "Poll attempt %s for %s returned status %s",
                poll_attempt,
                ctx.capture_id,
                getattr(response, "status_code", "unknown"),
            )  # WHY: Log poll status after callback returns.
            if response.status_code != _HTTP_OK:  # WHY: Retry after non-success responses without breaking flow.
                return self._handle_non_success_status(
                    response.status_code, poll_attempt, ctx.sleep_fn
                )  # WHY: Preserve retry pacing after failed poll response.
            return self._resolve_pcap_from_response(
                ctx, response, poll_attempt, elapsed
            )  # WHY: Delegate payload parse + retry pacing to bounded helper.
        except Exception as poll_error:  # pylint: disable=broad-exception-caught  # WHY: Legacy safety net.
            logging.exception(
                "Poll attempt %s exception: %s", poll_attempt, poll_error
            )  # WHY: Log transient poll exceptions with full context before retrying.
            ctx.sleep_fn(_POLL_INTERVAL_SEC)  # WHY: Preserve retry pacing after poll exceptions.
            return None  # WHY: Continue polling until timeout budget is exhausted.

    @staticmethod
    def _handle_non_success_status(
        status_code: int,
        poll_attempt: int,
        sleep_fn: Callable[[float], None],
    ) -> None:
        """Log non-success poll response and sleep before the next retry."""
        logging.warning(
            "Poll attempt %s: API returned status %s", poll_attempt, status_code
        )  # WHY: Log non-success response before sleeping.
        sleep_fn(_POLL_INTERVAL_SEC)  # WHY: Preserve current retry pacing after failed poll response.
        return None  # WHY: Continue polling until timeout budget is exhausted.

    def _resolve_pcap_from_response(
        self,
        ctx: _PollContext,
        response: Any,
        poll_attempt: int,
        elapsed: int,
    ) -> str | None:
        """Parse a successful response and return a URL or emit progress + sleep."""
        captures = self.parse_captures_response(
            response.data, poll_attempt
        )  # WHY: Normalize response payload before searching for target capture.
        pcap_url = self.find_capture_url(
            captures, ctx.capture_id, poll_attempt
        )  # WHY: Search normalized payload for a ready PCAP URL.
        if pcap_url:  # WHY: Report ready state and return URL when the target capture is complete.
            return self._report_ready_url(pcap_url, elapsed)  # WHY: Emit legacy ready banner and return the URL.
        self._emit_progress_and_sleep(ctx, poll_attempt, elapsed)  # WHY: Preserve rolling progress + retry pacing.
        return None  # WHY: Signal caller to continue polling.

    @staticmethod
    def _report_ready_url(pcap_url: str, elapsed: int) -> str:
        """Emit legacy ready banner and log the resolved URL."""
        print(
            f"\r* PCAP file ready for download (after {elapsed}s)                    "
        )  # WHY: Preserve ready banner that clears the progress line.
        logging.info(
            "PCAP URL available after %ss: %s", elapsed, pcap_url
        )  # WHY: Log ready URL and elapsed time for auditability.
        return pcap_url  # WHY: Return the URL to the caller so the file can be saved.

    @staticmethod
    def _emit_progress_and_sleep(ctx: _PollContext, poll_attempt: int, elapsed: int) -> None:
        """Emit the rolling progress line and sleep between intermediate attempts."""
        if poll_attempt < ctx.max_polls:  # WHY: Avoid sleeping after final attempt so timeout is immediate.
            print(
                f"  Waiting for PCAP file... {elapsed}s elapsed (checking every {_POLL_INTERVAL_SEC}s)    ",
                end="\r",
            )  # WHY: Preserve rolling progress output on intermediate attempts.
            ctx.sleep_fn(_POLL_INTERVAL_SEC)  # WHY: Preserve historic retry interval between not-ready responses.

    @staticmethod
    def _report_poll_timeout(capture_id: str, start_time: float) -> None:
        """Emit legacy timeout output and return None to preserve contract."""
        elapsed_total = int(time.time() - start_time)  # WHY: Compute total elapsed wait time for timeout message.
        print(
            f"\r! PCAP file URL not available after waiting {elapsed_total} seconds                    "
        )  # WHY: Preserve timeout banner shown when processing takes too long.
        print(
            f"  The capture may still be processing. Check the Mist portal for capture ID: {capture_id}"
        )  # WHY: Preserve manual follow-up guidance after timeout.
        logging.debug(
            "Polling timed out for %s after %s seconds", capture_id, elapsed_total
        )  # WHY: Log timeout outcome after poll budget is exhausted.
        return None  # WHY: Preserve current timeout contract for callers.

    @staticmethod
    def parse_captures_response(raw_data: Any, poll_attempt: int) -> list[dict[str, Any]]:
        """Normalize list-capture API response payloads into a list of capture dicts."""
        if isinstance(raw_data, dict) and "results" in raw_data:  # WHY: Preserve dict-style paginated payloads.
            captures = list(raw_data["results"])  # WHY: Materialize iterable into a mutable list.
            logging.debug(
                "Poll attempt %s: Extracted 'results' with %s items", poll_attempt, len(captures)
            )  # WHY: Log normalized capture count for dict payloads.
            return captures  # WHY: Return normalized capture list for further processing.
        if isinstance(raw_data, list):  # WHY: Preserve raw list payloads returned by some endpoints.
            logging.debug(
                "Poll attempt %s: Data is list with %s items", poll_attempt, len(raw_data)
            )  # WHY: Log list payload size before returning it unchanged.
            return raw_data  # WHY: Return existing list payload without additional wrapping.
        logging.warning(
            "Poll attempt %s: Unexpected data structure: %s", poll_attempt, type(raw_data)
        )  # WHY: Log unexpected payload shapes for troubleshooting.
        return []  # WHY: Preserve existing fallback for malformed or unexpected payloads.

    @staticmethod
    def find_capture_url(captures: list[dict[str, Any]], capture_id: str, poll_attempt: int) -> str | None:
        """Return the PCAP URL for the target capture when it is present and ready."""
        for capture in captures:  # WHY: Inspect each capture record until the requested identifier is found.
            if not isinstance(capture, dict) or capture.get("id") != capture_id:  # WHY: Skip non-matching entries.
                continue  # WHY: Preserve legacy scan behavior for unrelated or malformed entries.
            return PacketCaptureDownloadManager._extract_pcap_url(
                capture, capture_id, poll_attempt
            )  # WHY: Delegate URL extraction + logging to bounded helper.
        logging.debug(
            "Poll attempt %s: Capture %s not found in %s captures", poll_attempt, capture_id, len(captures)
        )  # WHY: Log when target capture has not appeared yet.
        return None  # WHY: Preserve current not-found contract for polling loop.

    @staticmethod
    def _extract_pcap_url(capture: dict[str, Any], capture_id: str, poll_attempt: int) -> str | None:
        """Read the pcap_url field from a matched capture and log the outcome."""
        pcap_url = capture.get("pcap_url")  # WHY: Read PCAP URL field once target capture is found.
        logging.debug(
            "Poll attempt %s: Found capture %s", poll_attempt, capture_id
        )  # WHY: Log that target capture record was located.
        logging.debug(
            "  - pcap_url: %s", pcap_url if pcap_url else "NOT SET YET"
        )  # WHY: Log whether URL is ready without changing operator output.
        return str(pcap_url) if pcap_url else None  # WHY: Return ready URL or preserve waiting state.

    @staticmethod
    def save_pcap_file(
        pcap_url: str,
        capture_id: str,
        prefix: str = "",
        requests_module: Any = requests,
        output_dir: Path | None = None,
    ) -> None:
        """Download the final PCAP payload and save it under the historic filename pattern."""
        print("\n* Downloading PCAP file...")  # WHY: Preserve user-facing banner before file download begins.
        logging.info("Downloading final PCAP artifact for %s", capture_id)  # WHY: Log outbound artifact download.
        download_response = PacketCaptureDownloadManager._fetch_final_pcap(
            pcap_url, capture_id, requests_module
        )  # WHY: Delegate HTTP fetch + status logging to bounded helper.
        if download_response.status_code != _HTTP_OK:  # WHY: Stop early when artifact endpoint does not succeed.
            PacketCaptureDownloadManager._report_save_http_failure(
                download_response.status_code, pcap_url
            )  # WHY: Preserve legacy failure output without raising.
            return  # WHY: Preserve current failure contract without raising.
        output_filename = PacketCaptureDownloadManager._write_final_pcap(
            download_response.content, capture_id, prefix, output_dir
        )  # WHY: Delegate directory setup + write to keep this method short.
        PacketCaptureDownloadManager._report_save_success(
            output_filename, len(download_response.content), capture_id
        )  # WHY: Emit legacy success output and logs.

    @staticmethod
    def _fetch_final_pcap(pcap_url: str, capture_id: str, requests_module: Any) -> Any:
        """Fetch the final PCAP artifact and log the response status."""
        response = requests_module.get(
            pcap_url, timeout=_DEFAULT_TIMEOUT_SEC
        )  # WHY: Fetch final PCAP payload in one request to preserve existing behavior.
        logging.debug(
            "Final PCAP download for %s returned status %s", capture_id, response.status_code
        )  # WHY: Log artifact download status immediately after response arrives.
        return response  # WHY: Return raw response so caller can inspect status and body.

    @staticmethod
    def _report_save_http_failure(status_code: int, pcap_url: str) -> None:
        """Emit legacy HTTP failure output for the final save step."""
        print("\n! Failed to download PCAP file")  # WHY: Preserve existing high-level failure message.
        print(f"  HTTP Status: {status_code}")  # WHY: Preserve HTTP status detail shown to operators.
        print(f"  You can try downloading manually from: {pcap_url}")  # WHY: Preserve manual-recovery guidance.
        logging.error("PCAP download failed: HTTP %s", status_code)  # WHY: Log HTTP failure for audit visibility.

    @staticmethod
    def _write_final_pcap(content: bytes, capture_id: str, prefix: str, output_dir: Path | None) -> Path:
        """Persist the final PCAP payload and return the resolved output path."""
        target_dir = output_dir or _DEFAULT_OUTPUT_DIR  # WHY: Preserve historic default output directory.
        target_dir.mkdir(exist_ok=True)  # WHY: Ensure output directory exists before writing artifact.
        output_filename = target_dir / _SAVE_FILENAME_TEMPLATE.format(
            prefix=prefix, capture_id=capture_id
        )  # WHY: Preserve historic filename pattern for downstream tooling.
        with open(output_filename, "wb") as pcap_file:  # WHY: Write downloaded payload to disk as binary PCAP.
            pcap_file.write(content)  # WHY: Persist full response content exactly as returned by Mist.
        return output_filename  # WHY: Return path so caller can report size + location.

    @staticmethod
    def _report_save_success(output_filename: Path, content_length: int, capture_id: str) -> None:
        """Emit legacy success output and audit log for the final save step."""
        file_size_mb = content_length / _BYTES_PER_MB  # WHY: Compute final file size for user feedback and logging.
        print("\n* PCAP file downloaded successfully")  # WHY: Preserve success banner shown after file write.
        print(f"  Location: {output_filename}")  # WHY: Preserve saved-file path output for operators.
        print(f"  Size: {file_size_mb:.2f} MB")  # WHY: Preserve downloaded size output for operators.
        print("\n  Open with Wireshark or other PCAP analysis tools")  # WHY: Preserve post-download guidance text.
        logging.debug(
            "Saved PCAP %s to %s", capture_id, output_filename
        )  # WHY: Log final file path after write succeeds.
        logging.info(
            "PCAP file downloaded: %s (%.2f MB)", output_filename, file_size_mb
        )  # WHY: Log final saved artifact summary for audit evidence.
