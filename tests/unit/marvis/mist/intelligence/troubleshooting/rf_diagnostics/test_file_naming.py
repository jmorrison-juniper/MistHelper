"""Unit tests for RF diagnostic file-name helpers."""

from __future__ import annotations  # WHY: keep annotations import-safe.

from datetime import datetime  # WHY: build deterministic file names.
from pathlib import Path  # WHY: assert path suffixes safely.

import pytest  # WHY: assert validation failures.

from src.mist.intelligence.troubleshooting.rf_diagnostics.file_naming import RfDiagnosticFileNamer  # WHY: test target.


def test_recording_path_contains_site_mac_and_time() -> None:
    """The recording path includes the site, client MAC, and timestamp."""
    namer = RfDiagnosticFileNamer(Path("data") / "rfdiags")  # WHY: use the production default shape.
    moment = datetime(2026, 9, 29, 16, 10, 13)  # WHY: deterministic timestamp token.
    path = namer.build_recording_path("site/one", "aa:bb:cc:dd:ee:ff", moment)  # WHY: exercise sanitizing.
    assert path.parts[-2] == "rfdiags"  # WHY: downloads must stay under data/rfdiags.
    assert path.name == "rfdiag_site-one_aabbccddeeff_20260929T161013.pcap"  # WHY: acceptance file shape.


def test_normalize_mac_rejects_bad_value() -> None:
    """MAC validation fails before an API call can start."""
    with pytest.raises(ValueError):  # WHY: invalid MACs must fail closed.
        RfDiagnosticFileNamer.normalize_mac("not-a-mac")  # WHY: non-hex input is unsafe for request bodies.
