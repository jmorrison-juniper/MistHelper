"""One-shot T005 capture harness for smoke_probes_baseline.json (feature 1025).

Why:
    Task T005 in specs/1025-probe-emission-log-fixes/tasks.md requires a pinned
    snapshot of the pre-1025 non-VPN probe-payload output so the INV-1 /
    byte-stability regression test (T010) can compare current output against
    a static ground truth even after `main` advances past 1024. This script is
    invoked once from pytest (which supplies the correct sys.path so
    ``from src.org import ...`` resolves the project package, not the shadow
    ``src/dataclasses/`` package that collides with the stdlib module name).

The harness is deliberately gated behind an environment flag so it does not
run during ordinary ``pytest tests/`` invocations — regenerating a baseline
mid-CI would silently mask drift. Set ``CAPTURE_1025_BASELINE=1`` to run it
and write the fixture, e.g.::

    CAPTURE_1025_BASELINE=1 pytest tests/unit/org/_capture_smoke_baseline.py -s

After the fixture exists on disk, delete the flag and this file becomes a
no-op (pytest still skips it via the module-level guard).
"""

from __future__ import annotations  # future annotations so type hints stay lazy

import json  # stdlib JSON writer used to serialize the captured baseline
import os  # environment lookup for the capture flag
from pathlib import Path  # absolute-path resolution rooted at this test file

import pytest  # test framework — used for skip guard, not for assertions

from src.org import org_synthetic_probes_manager as ospm  # target module under 1025 edit surface

# Path to the smoke_org fixture that _build_probe_set consumes.
# Why: this fixture already ships from 1024 (verified during T002 inventory) and
# defines every emit shape the byte-stability test T010 must pin.
FIXTURES_DIR = Path(__file__).parent / "fixtures"  # sibling directory to this capture harness
SMOKE_ORG_PATH = FIXTURES_DIR / "smoke_org.json"  # (probes, cenr) tuple input
BASELINE_PATH = FIXTURES_DIR / "smoke_probes_baseline.json"  # T005 output target


@pytest.mark.skipif(
    os.environ.get("CAPTURE_1025_BASELINE") != "1",  # only run when explicitly requested
    reason="Set CAPTURE_1025_BASELINE=1 to (re)generate the T005 baseline fixture.",
)
def test_capture_smoke_probes_baseline() -> None:
    """Emit smoke_probes_baseline.json from _build_probe_set on smoke_org.json.

    Why:
        T005 pins the non-VPN probe-payload output on the pre-1025 tip so
        subsequent CENR-warning-move work (T014) cannot silently mutate
        emitted bytes. We call the pure ``_build_probe_set`` helper directly
        (no Mist API, no side effects) and serialize the resulting mapping
        with ``sort_keys=True`` so the baseline is deterministic across
        Python dict-order changes.
    """
    raw = json.loads(SMOKE_ORG_PATH.read_text(encoding="utf-8"))  # deserialize the fixture tuple
    probes_source = raw["probes"]  # role list expected by _build_probe_set
    cenr_source = raw["cenr"]  # CENR observation cache expected by _build_probe_set
    result = ospm._build_probe_set((probes_source, cenr_source), [10])  # smoke fixture uses a single vlan id
    payload = json.dumps(result, sort_keys=True, indent=2, ensure_ascii=True)  # deterministic serialization
    BASELINE_PATH.write_text(payload + "\n", encoding="utf-8", newline="\n")  # LF-terminated for git cleanliness
    # Sanity assertion so the captured file is never empty (silent-write guard).
    assert BASELINE_PATH.stat().st_size > 0, "baseline capture produced an empty file"
