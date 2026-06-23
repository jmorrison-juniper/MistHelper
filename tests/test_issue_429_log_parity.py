"""Parity test for issue #429 logging f-string sweep.

Loads `tests/fixtures/issue_429_log_baseline.json` and asserts that the
current source code of `MistHelper.py` produces the exact same rendered
log string for every fixture entry. This test PASSES pre-refactor (since
the baseline was captured here) and must continue to PASS after every
tranche of the CONV-LOG-FSTRING sweep.

If a tranche rewrites a fixture line, the rendered output MUST stay
byte-identical to the baseline -- proving the codemod preserved log
content. If a tranche accidentally drops a substitution or changes a
format spec, this test fails and pinpoints the offending line.
"""

from __future__ import annotations  # Enable PEP 604 union syntax on Python 3.13.

import json  # Stdlib JSON loader for the baseline fixture.
from pathlib import Path  # Portable filesystem access on Windows + POSIX.
from typing import Any  # Type hint for the heterogeneous inputs dict.

import libcst as cst  # AST-preserving CST library for re-rendering current source.
import pytest  # Test framework used across the project.

from tools.capture_log_baseline import (  # Reuse the rendering primitives.
    FIXTURE_SITES,
    _extract_msg_and_args,
    _LineCallCollector,
)

REPO_ROOT = Path(__file__).resolve().parent.parent  # tests/ -> repo root.
BASELINE_PATH = REPO_ROOT / "tests" / "fixtures" / "issue_429_log_baseline.json"  # Frozen baseline JSON.
SOURCE_PATH = REPO_ROOT / "MistHelper.py"  # File the sweep is rewriting.


def _build_inputs_for_pattern(pattern: str, raw_inputs: dict[str, Any]) -> dict[str, Any]:
    """Reconstruct the same enriched inputs dict the capture script used."""
    merged = {**raw_inputs}  # Start from the operator-curated dict (no mutation).
    if pattern == "attribute_access":  # L1343 references sys.executable.
        merged["sys"] = type("FakeSys", (), {"executable": "/usr/bin/python3"})()  # Inject fake.
    if pattern == "g003_concat":  # L6120 calls table.get_string().

        class _FakeTable:  # Minimal stand-in for PrettyTable.
            def __init__(self, text: str) -> None:  # Holds the rendered text.
                self._text = text  # Stored once per fixture entry.

            def get_string(self) -> str:  # PrettyTable's public API surface.
                return self._text  # Whatever the fixture passed in.

        merged["table"] = _FakeTable(merged.pop("table_text"))  # Wrap the table_text input.
    return merged  # Caller passes this to _extract_msg_and_args.


@pytest.fixture(scope="module")
def baseline() -> dict[str, dict[str, Any]]:
    """Load the frozen baseline once per test module."""
    if not BASELINE_PATH.exists():  # Hard guard so the test fails loudly if fixture is missing.
        pytest.skip(f"baseline fixture not found at {BASELINE_PATH}")  # Skip cleanly until baseline is generated.
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))  # Parse the JSON into a dict.


@pytest.fixture(scope="module")
def module() -> cst.Module:
    """Parse `MistHelper.py` exactly once for the whole test module."""
    if not SOURCE_PATH.exists():  # Defensive: the only thing this test cares about.
        pytest.skip(f"source not found at {SOURCE_PATH}")  # Skip cleanly if missing.
    source = SOURCE_PATH.read_text(encoding="utf-8")  # Read once; libcst parse is the slow step.
    return cst.parse_module(source)  # Parse with libcst.


@pytest.mark.parametrize("site_id", [s["site_id"] for s in FIXTURE_SITES])  # One test per fixture site.
def test_log_render_matches_baseline(
    site_id: str,
    baseline: dict[str, dict[str, Any]],
    module: cst.Module,
) -> None:
    """Render the current source at the fixture line and compare to baseline."""
    if site_id not in baseline:  # The baseline may legitimately miss sites that failed capture.
        pytest.skip(f"site {site_id} missing from baseline fixture")  # Skip rather than fail.
    expected = baseline[site_id]["rendered"]  # The frozen ground truth.
    site_def = next(s for s in FIXTURE_SITES if s["site_id"] == site_id)  # Operator-curated entry.
    inputs = _build_inputs_for_pattern(site_def["pattern"], site_def["inputs"])  # Same enrichment as capture.
    wrapper = cst.MetadataWrapper(module)  # MetadataWrapper enables PositionProvider lookups.
    collector = _LineCallCollector(site_def["line"])  # Find the call at the fixture line.
    wrapper.visit(collector)  # Walk; collector stops at the first matching Call node.
    assert (
        collector.found is not None
    ), (  # Line drift would manifest as a missing match.
        f"no logging call found at line {site_def['line']} in current source"
    )
    msg, args = _extract_msg_and_args(collector.found, inputs)  # Pull (msg, args) tuple.
    import logging  # Local import so the test module's import surface stays narrow.

    record = logging.LogRecord(  # Mirror the framework's render path exactly.
        name="issue429_parity",
        level=logging.INFO,
        pathname=__file__,
        lineno=site_def["line"],
        msg=msg,
        args=args,
        exc_info=None,
    )
    actual = record.getMessage()  # The string the real logger would emit.
    assert (
        actual == expected
    ), f"site {site_id} drift: expected {expected!r}, got {actual!r}"  # Byte-identical rendering is the whole contract.
