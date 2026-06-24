"""Download and poll helpers for packet capture workflows."""

from __future__ import annotations

import logging  # Emit before-and-after action logs for capture download workflows.
import os  # Resolve and verify local file paths for downloaded PCAP artifacts.
import time  # Pace poll loops while waiting for capture files to become available.
from collections.abc import Callable  # Type poll/list callbacks without importing runtime-heavy helpers.
from pathlib import Path  # Build output file paths in a cross-platform-safe way.
from typing import Any  # Support Mist API response payloads with flexible structures.

import requests  # Download PCAP binaries from Mist-provided URLs.


class PacketCaptureDownloadManager:
    """Encapsulate PCAP polling and download responsibilities for packet capture flows."""

    def fetch_completed_pcaps(self, list_captures_fn: Callable[[], Any], iteration: int) -> list[dict[str, Any]]:
        """Fetch completed PCAP records that expose download URLs."""
        print(
            "\n[Step 1/3] Checking for completed PCAPs in last 24 hours..."
        )  # Preserve the user-facing loop banner before the API call.
        logging.info(
            "Loop iteration %s: Fetching PCAP list from API", iteration
        )  # Log the list operation before calling the Mist API.
        try:  # Catch API/listing failures so loop mode can continue safely.
            pcaps_response = list_captures_fn()  # Invoke the caller-provided list callback for the current scope.
            logging.debug(
                "Loop iteration %s: PCAP list callback returned status %s",
                iteration,
                getattr(pcaps_response, "status_code", "unknown"),
            )  # Log the status code returned by the callback.
        except Exception as list_error:  # pylint: disable=broad-exception-caught
            print(
                f"  Error fetching PCAP list: {list_error}"
            )  # Preserve the existing operator-facing error text for list failures.
            logging.exception(
                "Exception listing PCAPs: %s", list_error
            )  # Log the full list failure details for troubleshooting.
            return []  # Return no completed PCAPs so the loop can continue safely.
        if pcaps_response.status_code != 200:  # Guard non-success API responses before parsing payload content.
            print(
                f"  Warning: Could not fetch PCAP list (HTTP {pcaps_response.status_code})"
            )  # Preserve the existing warning text for operators.
            logging.warning(
                "Failed to list PCAPs: %s", pcaps_response.status_code
            )  # Log the non-success status for audit visibility.
            return []  # Treat failed list calls as no-download rounds to preserve prior behavior.
        pcap_list = self.parse_captures_response(
            pcaps_response.data, iteration
        )  # Normalize dict/list payload variants into one capture list.
        completed = [
            pcap for pcap in pcap_list if pcap.get("pcap_url") and pcap.get("format") == "pcap"
        ]  # Keep only downloadable PCAP entries to match existing loop semantics.
        print(
            f"  Found {len(completed)} completed PCAP(s) with download URLs"
        )  # Preserve the completed-capture count shown to operators.
        logging.debug(
            "Loop iteration %s: Filtered %s completed PCAP entries", iteration, len(completed)
        )  # Log the filtered count after parsing and selection.
        return completed  # Hand the downloadable capture records back to the manager loop.

    def download_pending_pcaps(
        self,
        completed_pcaps: list[dict[str, Any]],
        download_folder: str,
        download_single_fn: Callable[[str, str, str, str], int],
    ) -> int:
        """Download PCAPs that are not already present on disk."""
        if not completed_pcaps:  # Preserve the early-no-op branch when no completed PCAPs are available.
            print(
                "\n[Step 2/3] No completed PCAPs available for download"
            )  # Keep the same loop-step output for empty rounds.
            logging.debug(
                "No completed PCAPs were available for download"
            )  # Record that the download phase had nothing to do.
            return 0  # Return zero downloads to preserve the prior loop contract.
        print(
            "\n[Step 2/3] Checking for new PCAPs to download..."
        )  # Preserve the loop-step banner before local file checks begin.
        logging.info(
            "Checking %s completed PCAP(s) for pending downloads", len(completed_pcaps)
        )  # Log the download scan before processing capture entries.
        downloads = 0  # Track the number of files newly written during this iteration.
        for pcap in completed_pcaps:  # Process each downloadable capture record one time in order.
            capture_id = str(pcap.get("id", ""))  # Normalize the capture identifier for filenames and logs.
            pcap_url = str(pcap.get("pcap_url", ""))  # Normalize the download URL for the helper callback.
            expected_filename = (
                f"PacketCapture_{capture_id}.pcap"  # Preserve the historic filename pattern used by MistHelper.
            )
            local_path = os.path.join(download_folder, expected_filename)  # Build the local path in a Windows-safe way.
            if os.path.exists(local_path):  # Avoid re-downloading files that already exist locally.
                logging.debug(
                    "Skipping %s - already downloaded", capture_id
                )  # Log the local cache hit before continuing to the next file.
                continue  # Preserve the existing skip behavior for already-downloaded captures.
            print(f"\n  --> Downloading PCAP: {capture_id}")  # Preserve the per-capture operator progress output.
            logging.info(
                "Starting PCAP download for %s", capture_id
            )  # Log the file download before invoking the streaming callback.
            downloads += download_single_fn(
                pcap_url, local_path, expected_filename, capture_id
            )  # Delegate the actual file transfer to the injected single-download function.
            logging.debug(
                "Download counter after %s is %s", capture_id, downloads
            )  # Log the running download count after the callback returns.
        if downloads > 0:  # Match the historic summary message for successful download rounds.
            print(
                f"\n  Downloaded {downloads} new PCAP file(s) this round"
            )  # Preserve the success summary shown after download passes.
        else:  # Preserve the all-cached summary when no writes occurred.
            print(
                "\n  No new PCAPs to download (all already exist locally)"
            )  # Keep the no-op summary text unchanged for operators.
        logging.debug(
            "Pending download scan completed with %s new file(s)", downloads
        )  # Log the final scan outcome after all items are processed.
        return downloads  # Return the number of new files written this round.

    def download_single_pcap(
        self,
        url: str,
        local_path: str,
        filename: str,
        capture_id: str,
        requests_module: Any = requests,
    ) -> int:
        """Download one PCAP file from its URL and stream it to disk."""
        logging.info(
            "Downloading PCAP %s from %s", capture_id, url
        )  # Log the outbound download request before the HTTP call.
        try:  # Catch transfer and file-write failures so the caller can continue safely.
            response = requests_module.get(
                url, stream=True, timeout=300
            )  # Stream the file to avoid unnecessary in-memory buffering for large PCAPs.
            logging.debug(
                "Download response for %s returned status %s", capture_id, response.status_code
            )  # Log the HTTP status returned by the download endpoint.
            if response.status_code != 200:  # Stop early when the endpoint does not return file content.
                print(
                    f"      Failed to download: HTTP {response.status_code}"
                )  # Preserve the existing operator-facing HTTP failure message.
                logging.error(
                    "Download failed for %s: %s", capture_id, response.status_code
                )  # Log the HTTP failure with the capture identifier.
                return 0  # Preserve the prior contract for failed downloads.
            with open(local_path, "wb") as pcap_file:  # Write the PCAP stream directly to the expected local file path.
                for chunk in response.iter_content(
                    chunk_size=8192
                ):  # Preserve the existing chunk size used for streaming downloads.
                    pcap_file.write(chunk)  # Persist each chunk as it arrives from the HTTP stream.
            file_size_mb = os.path.getsize(local_path) / (
                1024 * 1024
            )  # Compute the downloaded file size for user feedback and logging.
            print(
                f"      Downloaded: {filename} ({file_size_mb:.2f} MB)"
            )  # Preserve the existing success message including file size.
            logging.debug(
                "Downloaded PCAP %s to %s", capture_id, local_path
            )  # Log the completed local file path after the write succeeds.
            logging.info(
                "Downloaded PCAP %s: %.2f MB", capture_id, file_size_mb
            )  # Log the final size summary for audit evidence.
            return 1  # Preserve the prior success contract for callers aggregating download counts.
        except Exception as download_error:  # pylint: disable=broad-exception-caught
            print(f"      Error downloading: {download_error}")  # Preserve the existing operator-facing exception text.
            logging.exception(
                "Download exception for %s: %s", capture_id, download_error
            )  # Log the full transfer exception for debugging.
            return 0  # Preserve the prior failure contract when download exceptions occur.

    def poll_and_download_pcap(
        self,
        list_captures_fn: Callable[[], Any],
        capture_id: str,
        duration: int,
        prefix: str = "",
        save_pcap_file_fn: Callable[[str, str, str], None] | None = None,
    ) -> None:
        """Poll until a PCAP URL is ready, then download the resulting file."""
        print(
            f"\n* Capture initiated (ID: {capture_id})"
        )  # Preserve the capture-start banner shown before the wait begins.
        print(
            f"  Duration: {duration} seconds (plus processing time)"
        )  # Preserve the existing duration guidance for operators.
        print("  Polling for PCAP file availability...")  # Preserve the readiness wait status line.
        print(
            "  Press Ctrl+C to cancel wait and check portal manually"
        )  # Preserve the operator guidance for manual cancellation.
        logging.info(
            "Polling for PCAP availability for capture %s", capture_id
        )  # Log the poll lifecycle before the first list call.
        pcap_url: str | None = None  # Track the discovered PCAP URL so cancellation/error messages can reuse it.
        try:  # Catch cancellation and other errors without changing user-visible behavior.
            pcap_url = self.poll_for_pcap_url(
                list_captures_fn, capture_id, duration
            )  # Wait until the download URL becomes available or times out.
            if not pcap_url:  # Preserve the early exit when the URL never appears.
                logging.debug(
                    "Polling finished for %s without a downloadable URL", capture_id
                )  # Log the no-URL outcome after the poll loop ends.
                return  # Preserve the current no-download outcome when polling times out.
            save_callback = (
                save_pcap_file_fn or self.save_pcap_file
            )  # Use the provided save callback when compatibility layers inject one.
            logging.info(
                "PCAP URL resolved for %s; starting file save", capture_id
            )  # Log the handoff from polling to file download.
            save_callback(
                pcap_url, capture_id, prefix
            )  # Save the discovered PCAP file using the caller-selected callback.
            logging.debug(
                "PCAP save callback completed for %s", capture_id
            )  # Log completion after the file-save callback returns.
        except KeyboardInterrupt:  # Preserve the user-cancel path exactly as before.
            print("\n\n! Download cancelled by user")  # Preserve the existing cancellation banner for operator control.
            print(f"  Capture ID: {capture_id}")  # Preserve the capture identifier shown during cancellation.
            if pcap_url:  # Only show the manual URL when polling already discovered it.
                print(
                    f"  Download manually from: {pcap_url}"
                )  # Preserve the manual-download guidance for cancelled waits.
        except Exception as error:  # pylint: disable=broad-exception-caught
            print(f"\n! Error downloading PCAP file: {error}")  # Preserve the existing high-level download error text.
            logging.exception(
                "Exception in poll_and_download_pcap for %s: %s", capture_id, error
            )  # Log the full polling/download exception context.
            if pcap_url:  # Preserve the manual URL hint when one was already discovered.
                print(
                    f"  Try downloading manually from: {pcap_url}"
                )  # Preserve the existing operator recovery guidance.

    def poll_for_pcap_url(
        self,
        list_captures_fn: Callable[[], Any],
        capture_id: str,
        duration: int,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> str | None:
        """Poll the capture list API until the requested PCAP URL is ready."""
        max_wait = duration + 120  # Preserve the historic post-capture processing buffer before timing out.
        poll_interval = 5  # Preserve the existing five-second poll cadence for PCAP availability checks.
        max_polls = max_wait // poll_interval  # Convert the total wait budget into a bounded number of poll attempts.
        start_time = time.time()  # Track elapsed time for operator progress output and timeout messaging.
        logging.info(
            "Polling capture list for %s up to %s seconds", capture_id, max_wait
        )  # Log the bounded polling plan before the loop begins.
        for poll_attempt in range(1, max_polls + 1):  # Poll until the URL appears or the timeout budget is exhausted.
            try:  # Catch transient poll failures and continue to retry within the same wait budget.
                elapsed = int(time.time() - start_time)  # Calculate elapsed time for progress and ready messages.
                response = list_captures_fn()  # Invoke the caller-provided list callback for the current poll attempt.
                logging.debug(
                    "Poll attempt %s for %s returned status %s",
                    poll_attempt,
                    capture_id,
                    getattr(response, "status_code", "unknown"),
                )  # Log the poll status after the callback returns.
                if response.status_code != 200:  # Retry after non-success responses without breaking operator flow.
                    logging.warning(
                        "Poll attempt %s: API returned status %s", poll_attempt, response.status_code
                    )  # Log the non-success response before sleeping.
                    sleep_fn(poll_interval)  # Preserve the current retry pacing after a failed poll response.
                    continue  # Continue polling until the timeout budget is exhausted.
                captures = self.parse_captures_response(
                    response.data, poll_attempt
                )  # Normalize the response payload before searching for the target capture.
                pcap_url = self.find_capture_url(
                    captures, capture_id, poll_attempt
                )  # Search the normalized payload for a ready PCAP URL.
                if pcap_url:  # Stop polling immediately once a downloadable URL is present.
                    print(
                        f"\r* PCAP file ready for download (after {elapsed}s)                    "
                    )  # Preserve the ready banner that clears the progress line.
                    logging.info(
                        "PCAP URL available after %ss: %s", elapsed, pcap_url
                    )  # Log the ready URL and elapsed time for auditability.
                    return pcap_url  # Return the URL to the caller so the file can be saved.
                if (
                    poll_attempt < max_polls
                ):  # Avoid sleeping after the final attempt so timeout reporting is immediate.
                    print(
                        f"  Waiting for PCAP file... {elapsed}s elapsed (checking every {poll_interval}s)    ", end="\r"
                    )  # Preserve the rolling progress output on intermediate attempts.
                    sleep_fn(
                        poll_interval
                    )  # Preserve the historic retry interval between successful-but-not-ready responses.
            except Exception as poll_error:  # pylint: disable=broad-exception-caught
                logging.exception(
                    "Poll attempt %s exception: %s", poll_attempt, poll_error
                )  # Log transient poll exceptions with full context before retrying.
                sleep_fn(poll_interval)  # Preserve the retry pacing after poll exceptions.
        elapsed_total = int(time.time() - start_time)  # Compute the total elapsed wait time for the timeout message.
        print(
            f"\r! PCAP file URL not available after waiting {elapsed_total} seconds                    "
        )  # Preserve the timeout banner shown when processing takes too long.
        print(
            f"  The capture may still be processing. Check the Mist portal for capture ID: {capture_id}"
        )  # Preserve the manual follow-up guidance after timeout.
        logging.debug(
            "Polling timed out for %s after %s seconds", capture_id, elapsed_total
        )  # Log the timeout outcome after the poll budget is exhausted.
        return None  # Preserve the current timeout contract for callers.

    @staticmethod
    def parse_captures_response(raw_data: Any, poll_attempt: int) -> list[dict[str, Any]]:
        """Normalize list-capture API response payloads into a list of capture dicts."""
        if (
            isinstance(raw_data, dict) and "results" in raw_data
        ):  # Preserve support for paginated dict-style API payloads.
            captures = list(
                raw_data["results"]
            )  # Materialize the results iterable into a mutable list for downstream scanning.
            logging.debug(
                "Poll attempt %s: Extracted 'results' with %s items", poll_attempt, len(captures)
            )  # Log the normalized capture count for dict payloads.
            return captures  # Return the normalized capture list for further processing.
        if isinstance(raw_data, list):  # Preserve support for raw list payloads returned by some endpoints.
            logging.debug(
                "Poll attempt %s: Data is list with %s items", poll_attempt, len(raw_data)
            )  # Log the list payload size before returning it unchanged.
            return raw_data  # Return the existing list payload without additional wrapping.
        logging.warning(
            "Poll attempt %s: Unexpected data structure: %s", poll_attempt, type(raw_data)
        )  # Log unexpected payload shapes for troubleshooting.
        return []  # Preserve the existing fallback for malformed or unexpected payloads.

    @staticmethod
    def find_capture_url(captures: list[dict[str, Any]], capture_id: str, poll_attempt: int) -> str | None:
        """Return the PCAP URL for the target capture when it is present and ready."""
        for capture in captures:  # Inspect each capture record until the requested identifier is found.
            if not isinstance(
                capture, dict
            ):  # Skip malformed entries to preserve robustness against unexpected payload members.
                continue  # Ignore non-dict entries exactly as the prior implementation did.
            if capture.get("id") != capture_id:  # Ignore unrelated capture records while scanning the current payload.
                continue  # Continue scanning until the target capture appears.
            pcap_url = capture.get("pcap_url")  # Read the PCAP URL field once the target capture is found.
            logging.debug(
                "Poll attempt %s: Found capture %s", poll_attempt, capture_id
            )  # Log that the target capture record was located.
            logging.debug(
                "  - pcap_url: %s", pcap_url if pcap_url else "NOT SET YET"
            )  # Log whether the URL is ready without changing the operator output.
            return (
                str(pcap_url) if pcap_url else None
            )  # Return the ready URL or preserve the waiting state when it is still absent.
        logging.debug(
            "Poll attempt %s: Capture %s not found in %s captures", poll_attempt, capture_id, len(captures)
        )  # Log when the target capture has not appeared yet.
        return None  # Preserve the current not-found contract for the polling loop.

    @staticmethod
    def save_pcap_file(
        pcap_url: str,
        capture_id: str,
        prefix: str = "",
        requests_module: Any = requests,
        output_dir: Path | None = None,
    ) -> None:
        """Download the final PCAP payload and save it under the historic filename pattern."""
        print("\n* Downloading PCAP file...")  # Preserve the user-facing banner before the file download begins.
        logging.info(
            "Downloading final PCAP artifact for %s", capture_id
        )  # Log the outbound artifact download before the HTTP call.
        download_response = requests_module.get(
            pcap_url, timeout=300
        )  # Fetch the final PCAP payload in one request to preserve the existing behavior.
        logging.debug(
            "Final PCAP download for %s returned status %s", capture_id, download_response.status_code
        )  # Log the artifact download status immediately after the response arrives.
        if download_response.status_code != 200:  # Stop early when the artifact endpoint does not succeed.
            print("\n! Failed to download PCAP file")  # Preserve the existing high-level failure message for operators.
            print(
                f"  HTTP Status: {download_response.status_code}"
            )  # Preserve the HTTP status detail shown to operators.
            print(
                f"  You can try downloading manually from: {pcap_url}"
            )  # Preserve the manual-recovery guidance on HTTP failures.
            logging.error(
                "PCAP download failed: HTTP %s", download_response.status_code
            )  # Log the HTTP failure for audit visibility.
            return  # Preserve the current failure contract without raising.
        target_dir = output_dir or Path(
            "data"
        )  # Preserve the historic default output directory while allowing test injection.
        target_dir.mkdir(exist_ok=True)  # Ensure the output directory exists before writing the artifact.
        output_filename = (
            target_dir / f"PacketCapture_{prefix}{capture_id}.pcap"
        )  # Preserve the historic filename pattern for downstream tooling.
        with open(output_filename, "wb") as pcap_file:  # Write the downloaded payload to disk as a binary PCAP file.
            pcap_file.write(download_response.content)  # Persist the full response content exactly as returned by Mist.
        file_size_mb = len(download_response.content) / (
            1024 * 1024
        )  # Compute the final file size for user feedback and logging.
        print(
            "\n* PCAP file downloaded successfully"
        )  # Preserve the success banner shown after the file write completes.
        print(f"  Location: {output_filename}")  # Preserve the saved-file path output for operators.
        print(f"  Size: {file_size_mb:.2f} MB")  # Preserve the downloaded size output for operators.
        print("\n  Open with Wireshark or other PCAP analysis tools")  # Preserve the post-download guidance text.
        logging.debug(
            "Saved PCAP %s to %s", capture_id, output_filename
        )  # Log the final file path after the write succeeds.
        logging.info(
            "PCAP file downloaded: %s (%.2f MB)", output_filename, file_size_mb
        )  # Log the final saved artifact summary for audit evidence.
