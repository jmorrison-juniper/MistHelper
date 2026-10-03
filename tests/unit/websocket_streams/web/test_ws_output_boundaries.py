"""Unit tests for WebSocket command output boundaries."""

from __future__ import annotations  # Keep annotations compatible with the project target.

import json  # Send deterministic message data to the JavaScript harness.
import logging  # Record each offline JavaScript execution.
import shutil  # Find the local Node executable.
import subprocess  # Execute the production JavaScript without a browser.
from pathlib import Path  # Read the production WebSocket page script.

import pytest  # Fail with a clear message when Node is not available.

logger = logging.getLogger(__name__)  # Keep unit test actions visible in test logs.

SCRIPT_PATH = Path(__file__).resolve().parents[4] / "src" / "websocket_streams" / "web" / "static" / "websockets.js"


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
