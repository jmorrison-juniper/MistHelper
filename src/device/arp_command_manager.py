"""ARPCommandManager -- ARP command execution + WebSocket output streaming.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 42).
Consolidates ARP command triggering, WebSocket subscription, incoming
message parsing, and output export (raw text + two-dataset CSVs).

Direct imports cover stdlib (csv, importlib, json, logging, os, threading,
time) plus third-party (requests, websocket, prettytable) and the
``WebSocketStreamTarget`` dataclass. Every live-global read
(``apisession``, ``PromptClientUtils``, ``FilePathUtils``) is resolved via
lazy ``mh = importlib.import_module("MistHelper")`` inside the methods
that need them. Callers continue to reach the class through the
``MistHelper.ARPCommandManager`` re-export alias.
"""

from __future__ import annotations  # WHY: PEP 604 unions for future annotations.

import csv  # WHY: _write_dataset_csv writes CSV rows to disk.
import importlib  # WHY: lazy MistHelper import avoids circular load at module init.
import json  # WHY: parse WebSocket JSON envelope + subscribe payload serialization.
import logging  # WHY: structured trace for WS lifecycle + parse errors.
import os  # WHY: environment fallback for MIST_HOST / MIST_APITOKEN.
import threading  # WHY: run websocket-client event loop in a background thread.
import time  # WHY: idle-timeout polling.

import requests  # WHY: HTTP POST to trigger the ARP command.
from prettytable import PrettyTable  # WHY: render parsed ARP rows as a table.

import websocket  # WHY: websocket-client stream subscription.
from src.dataclasses.websocket_stream_target import WebSocketStreamTarget  # Bundle for WS connection identity.


class ARPCommandManager:  # ARP WebSocket command manager.
    """Manages ARP command execution via WebSocket for network devices.

    Consolidates all ARP-related functionality including command triggering,
    WebSocket message handling, and output processing/export.
    """

    @staticmethod
    def _resolve_arp_target_ids(site_id, device_id):
        """Resolve (site_id, device_id), prompting if either is missing. Returns tuple or (None, None) on abort."""
        if site_id and device_id:  # Already supplied — pass through
            return site_id, device_id
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of PromptClientUtils live-global.
        site_id, device_id = mh.PromptClientUtils.select_site_and_device_ids(site_id, device_id)  # type: ignore[no-untyped-call]
        return site_id, device_id  # Caller validates emptiness

    @staticmethod
    def _resolve_mist_ws_credentials():
        """Resolve (host, token) from session or environment. Returns (None, None) when either is missing."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession live-global.
        mist_host = getattr(mh.apisession, "host", None) or os.getenv("MIST_HOST")  # Session host > env
        mist_apitoken = getattr(mh.apisession, "apitoken", None) or os.getenv("MIST_APITOKEN")  # Session token > env
        if not mist_host or not mist_apitoken:  # Either missing — caller bails
            return None, None
        return mist_host, mist_apitoken  # Caller streams using these

    @staticmethod
    def execute(site_id=None, device_id=None):  # Run the ARP command.
        """Execute ARP command on a device and stream output via WebSocket (prompts for IDs when missing)."""
        site_id, device_id = ARPCommandManager._resolve_arp_target_ids(site_id, device_id)  # Resolve or prompt
        if not site_id or not device_id:  # Still missing — abort
            return
        mist_host, mist_apitoken = ARPCommandManager._resolve_mist_ws_credentials()  # Resolve creds
        if not mist_host or not mist_apitoken:  # Missing creds — abort
            print(" Mist host or API token not found in session or environment.")  # User-facing notice
            return
        print(" Subscribing to WebSocket stream...")  # User progress
        session_id = ARPCommandManager._trigger_command(mist_host, mist_apitoken, site_id, device_id)  # type: ignore[no-untyped-call]
        if not session_id:  # Trigger failed — nothing to listen for
            return
        ARPCommandManager._listen_for_output(  # type: ignore[no-untyped-call]
            WebSocketStreamTarget(  # Issue #470: bundle WS connection identity into one target.
                mist_host.replace("api.", "api-ws."), mist_apitoken, site_id, device_id, session_id
            )
        )

    @staticmethod
    def _trigger_command(mist_host, mist_apitoken, site_id, device_id):  # Trigger the ARP command.
        """Trigger ARP command on device via REST API."""
        url = f"https://{mist_host}/api/v1/sites/{site_id}/devices/{device_id}/arp"  # Build the URL.
        headers = {"Authorization": f"Token {mist_apitoken}"}  # Auth header.
        response = requests.post(url, headers=headers, json={}, timeout=30)  # POST the command.

        if response.status_code == 200:  # Success.
            session_id = response.json().get("session")  # Read the session id.
            print(f"! ARP command triggered. Session ID: {session_id}")  # Tell the user.
            return session_id  # Return the session.
        else:
            print(f"! Failed to trigger ARP command: {response.status_code}")  # Tell the user fail.
            print(response.text)  # Show the body.
            return None  # Return None.

    @staticmethod
    def _build_ws_subscribe(target: WebSocketStreamTarget) -> tuple[str, list[str], dict]:
        """Return (ws_url, auth headers, subscribe payload) for the bundled stream target."""
        ws_url = f"wss://{target.mist_host}/api-ws/v1/stream"  # Stream URL.
        headers = [f"Authorization: Token {target.mist_apitoken}"]  # Auth header.
        subscribe_msg = {  # Subscribe payload routed by site+device.
            "subscribe": f"/sites/{target.site_id}/devices/{target.device_id}/cmd"
        }
        return ws_url, headers, subscribe_msg  # Bundle for the caller.

    @staticmethod
    def _make_ws_callbacks(
        target: WebSocketStreamTarget,
        state: dict,
        output_lines: list[str],
        debug: bool,
        subscribe_msg: dict,
    ) -> dict:
        """Return on_message/on_close/on_error/on_open callbacks closed over a mutable state dict."""

        def on_message(ws, message):  # WebSocket message handler.
            del ws  # The websocket client passes itself; unused here but required by the callback signature.
            state["last_message_time"], state["buffer"] = ARPCommandManager._handle_message(  # type: ignore[no-untyped-call]
                message, target.session_id, state["buffer"], output_lines, debug
            )

        def on_close(ws, *args):  # WebSocket close handler.
            del ws, args  # Signature required by websocket-client; parameters unused here.
            ARPCommandManager._handle_close(output_lines, debug)  # type: ignore[no-untyped-call]

        def on_error(ws, error):  # WebSocket error handler.
            del ws  # Signature required by websocket-client; ws unused here.
            logging.error("! WebSocket error: %s", error)  # Log the error.

        def on_open(ws):  # WebSocket open handler.
            logging.info(" WebSocket opened. Subscribing...")  # Log the open.
            ws.send(json.dumps(subscribe_msg))  # Send the subscribe.

        return {"on_message": on_message, "on_close": on_close, "on_error": on_error, "on_open": on_open}

    @staticmethod
    def _poll_ws_idle(ws, state: dict, output_lines: list[str], timeout: int, idle_timeout: int) -> None:
        """Poll the running WebSocket until idle-timeout-after-output or hard timeout."""
        start_time = time.time()  # Start the timer.
        while time.time() - start_time < timeout:  # Poll until timeout.
            time.sleep(1)  # Pace the poll.
            if time.time() - state["last_message_time"] > idle_timeout and output_lines:  # Idle with output.
                logging.info(" Idle timeout reached. Closing WebSocket.")  # Log the idle close.
                ws.close()  # Close the socket.
                break  # Stop polling.
        if ws.keep_running:  # Still running -- hard timeout fired.
            logging.warning(" Timeout waiting for ARP output.")  # Warn the timeout.
            ws.close()  # Close the socket.

    @staticmethod
    def _listen_for_output(target: WebSocketStreamTarget, timeout=30, idle_timeout=3, debug=False):
        """Listen for WebSocket command output from a device (issue #470: connection identity in target)."""
        if debug:  # Debug mode.
            websocket.enableTrace(True)  # Trace the WebSocket.
        ws_url, headers, subscribe_msg = ARPCommandManager._build_ws_subscribe(target)  # Build endpoint.
        state: dict = {"last_message_time": time.time(), "buffer": ""}  # Shared callback state.
        output_lines: list[str] = []  # Collect output lines.
        callbacks = ARPCommandManager._make_ws_callbacks(target, state, output_lines, debug, subscribe_msg)
        ws = websocket.WebSocketApp(ws_url, header=headers, **callbacks)  # Build the WebSocket app.
        ws_thread = threading.Thread(target=ws.run_forever)  # Run it in a thread.
        ws_thread.start()  # Start the thread.
        ARPCommandManager._poll_ws_idle(ws, state, output_lines, timeout, idle_timeout)  # Wait for completion.

    @staticmethod
    def _drain_buffer_to_lines(buffer: str, output_lines: list[str]) -> str:
        """Split complete newline-terminated lines out of buffer, append them, and return the remainder."""
        while "\n" in buffer:  # Split on newlines.
            line, buffer = buffer.split("\n", 1)  # Pop one line.
            output_lines.append(line)  # Collect it.
        return buffer  # Return the remaining tail.

    @staticmethod
    @staticmethod
    def _parse_ws_arp_payload(message: str):
        """Parse a WebSocket frame into the inner ARP data dict (returns None when frame can't be unwrapped)."""
        msg = json.loads(message)  # Outer envelope
        data_str = msg.get("data", "{}")  # Outer data string
        data_obj = json.loads(data_str) if isinstance(data_str, str) else data_str  # Inner JSON or already-parsed
        inner_data = data_obj.get("data", {})  # Inner payload
        if isinstance(inner_data, str):  # Stringified inner — decode once more
            inner_data = json.loads(inner_data)
        return inner_data  # Caller checks session id

    @staticmethod
    def _safe_parse_ws_arp_payload(message):  # type: ignore[no-untyped-def]
        """Parse the nested ARP payload and log+swallow JSON/key errors; return inner dict or ``None`` on failure."""
        try:
            return ARPCommandManager._parse_ws_arp_payload(message)  # Nested JSON unwrap
        except json.JSONDecodeError as exception:  # Malformed JSON anywhere in the chain
            logging.error("WebSocket message JSON decode error: %s", exception)
            return None
        except KeyError as exception:  # Missing expected key in inner payload
            logging.warning("WebSocket message missing expected key: %s", exception)
            return None
        except Exception as exception:  # Defensive catch
            logging.error("Unexpected error parsing WebSocket message: %s", exception)
            return None

    @staticmethod
    def _handle_message(message, session_id, buffer, output_lines, debug=False):  # Parse one ARP message.
        """Handle incoming WebSocket message."""
        last_message_time = time.time()  # Arrival timestamp
        if debug:  # Optional raw-frame trace
            logging.debug("WebSocket raw message received: %s", message)
        inner_data = ARPCommandManager._safe_parse_ws_arp_payload(message)  # Parse + log-on-fail
        if inner_data is None:  # Parse failed -> caller continues
            return last_message_time, buffer
        if inner_data.get("session") != session_id:  # Not our session -> ignore
            return last_message_time, buffer
        raw_output = inner_data.get("raw", "")  # Append fragment
        buffer = ARPCommandManager._drain_buffer_to_lines(buffer + raw_output, output_lines)  # Flush full lines
        if debug:  # Size-trace after processing
            logging.debug("Processed WebSocket data: %s chars", len(raw_output))
        return last_message_time, buffer

    @staticmethod
    def _handle_close(output_lines, debug=False):  # Handle the close.
        """Handle WebSocket close and process output."""
        logging.info(" WebSocket closed.")  # Log the close.
        if not output_lines:  # No output captured during this session.
            print(" No ARP output received for this session.")  # Tell the user none.
            logging.warning(" No ARP output received for this session.")  # Warn none.
            return  # Nothing further to process.
        compiled_output = "\n".join(output_lines)  # Join the captured lines into one block.
        ARPCommandManager._save_output(compiled_output)  # type: ignore[no-untyped-call]
        ARPCommandManager._export_to_csv("arp_output_raw.txt")  # type: ignore[no-untyped-call]
        print("\n  ARP Output Received:\n")  # Tell the user output arrived.
        ARPCommandManager._render_arp_table(compiled_output, debug)  # type: ignore[no-untyped-call]

    @staticmethod
    def _render_arp_table(compiled_output, debug):  # Render the parsed ARP output.
        """Parse compiled ARP output and display it as a padded table."""
        logging.debug("Rendering ARP table from compiled output")  # Trace the render step.
        parsed_rows, max_cols = ARPCommandManager._parse_arp_rows(compiled_output)  # type: ignore[no-untyped-call]
        if not parsed_rows:  # No rows parsed -- nothing to tabulate.
            return  # Skip table construction entirely.
        table = PrettyTable()  # Build the table.
        table.field_names = [f"Col {col_num + 1}" for col_num in range(max_cols)]  # Number the columns.
        for row in parsed_rows:  # Add each parsed row.
            table.add_row(row)  # Add the row to the table.
        ARPCommandManager._emit_arp_table(table, len(parsed_rows), debug)  # type: ignore[no-untyped-call]

    @staticmethod
    def _parse_arp_rows(compiled_output):  # Parse compiled output into padded rows.
        """Split compiled output into tab-delimited rows padded to a uniform width."""
        logging.debug("Parsing ARP rows from compiled output")  # Trace the parse step.
        rows = compiled_output.split("\n")  # Split the block into individual rows.
        parsed_rows = [row.split("\t") for row in rows if row.strip()]  # Split each non-empty row on tabs.
        max_cols = max((len(row) for row in parsed_rows), default=0)  # Widest row determines column count.
        ARPCommandManager._pad_rows(parsed_rows, max_cols)  # type: ignore[no-untyped-call]
        return parsed_rows, max_cols  # Return the padded rows and the column width.

    @staticmethod
    def _pad_rows(parsed_rows, max_cols):  # Pad rows to a uniform width.
        """Pad each row with empty cells until it reaches max_cols columns."""
        logging.debug("Padding %d ARP rows to %d columns", len(parsed_rows), max_cols)  # Trace the pad step.
        for row in parsed_rows:  # Pad each row in place.
            while len(row) < max_cols:  # Keep padding until the row is full width.
                row.append("")  # Append an empty cell.

    @staticmethod
    def _emit_arp_table(table, row_count, debug):  # Print or log the rendered table.
        """Print the table in debug mode or report the row count otherwise."""
        if debug:  # Debug mode shows the full table.
            print(table)  # Print the table for the user.
            logging.debug("\n%s", table.get_string())  # Log the table contents.
        else:  # Non-debug mode reports only the row count.
            print(f"! ARP output received with {row_count} rows.")  # Tell the user the row count.

    @staticmethod
    def _save_output(compiled_output, filename="arp_output_raw.txt"):  # Save raw output.
        """Save compiled output to file."""
        try:
            mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of FilePathUtils live-global.
            file_path = mh.FilePathUtils.get_csv_path(filename)  # Build the path.
            with open(file_path, "w", encoding="utf-8") as f:  # Open the file.
                f.write(compiled_output)  # Write the output.
            logging.info("! ARP output saved to %s", file_path)  # Log the save.
        except Exception as e:  # Save failed.
            logging.error("! Failed to save ARP output to file: %s", e)  # Log the error.

    @staticmethod
    def _extract_arp_columns(line: str) -> list[str]:
        """Tab-split a line and return non-empty stripped columns."""
        return [col.strip() for col in line.split("\t") if col.strip()]  # Split + strip + drop empties

    @staticmethod
    def _split_arp_text_into_datasets(raw_text: str) -> tuple[list[list[str]], list[list[str]]]:
        """Split raw ARP text into two tab-delimited datasets separated by a 'Total' marker line."""
        lines = raw_text.splitlines()  # Split into lines.
        dataset1: list[list[str]] = []  # First dataset.
        dataset2: list[list[str]] = []  # Second dataset.
        current_dataset = dataset1  # Start with the first.
        for line in lines:  # Walk lines.
            if "Total" in line:  # Total marker.
                current_dataset = dataset2  # Switch datasets.
                continue  # Marker isn't a row.
            columns = ARPCommandManager._extract_arp_columns(line)  # Delegate tab-split + strip
            if columns:  # Have columns.
                current_dataset.append(columns)  # Collect the row.
        return dataset1, dataset2  # Return both datasets.

    @staticmethod
    def _write_dataset_csv(path: str, rows: list[list[str]]) -> None:
        """Write a single dataset to a CSV file and announce the row count."""
        with open(path, "w", newline="", encoding="utf-8") as fout:  # Open the CSV.
            writer = csv.writer(fout)  # CSV writer.
            writer.writerows(rows)  # Write the rows.
        print(f"! Saved {len(rows)} rows to {path}")  # Tell the user.

    @staticmethod
    def _export_to_csv(txt_filename="arp_output_raw.txt", csv1="arp_dataset1.csv", csv2="arp_dataset2.csv"):
        """Export ARP output to CSV files."""
        try:
            mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of FilePathUtils live-global.
            txt_file_path = mh.FilePathUtils.get_csv_path(txt_filename)  # Source path.
            csv1_path = mh.FilePathUtils.get_csv_path(csv1)  # First CSV path.
            csv2_path = mh.FilePathUtils.get_csv_path(csv2)  # Second CSV path.
            with open(txt_file_path, encoding="utf-8") as f:  # Open the source.
                raw_text = f.read()  # Read the text.
            dataset1, dataset2 = ARPCommandManager._split_arp_text_into_datasets(raw_text)  # Split.
            ARPCommandManager._write_dataset_csv(csv1_path, dataset1)  # Write first CSV.
            ARPCommandManager._write_dataset_csv(csv2_path, dataset2)  # Write second CSV.
        except Exception as e:  # Export failed.
            print(f"! Failed to export ARP output to CSV: {e}")  # Tell the user.
