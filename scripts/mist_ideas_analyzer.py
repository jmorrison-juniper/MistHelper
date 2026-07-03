#!/usr/bin/env python3
"""Thin CLI entry point for the Mist Ideas Analyzer.

The full implementation now lives in :mod:`src.mist_ideas_analyzer`. This
script exists only to preserve the historical ``python scripts/mist_ideas_analyzer.py``
invocation path used by operators, CI, and documentation. All classification,
provisioning, and reporting logic has been relocated to the package so the
compliance analyzer can score each module in isolation.
"""

from __future__ import annotations  # WHY: postponed annotations keep the tiny entrypoint import-free

import sys  # WHY: sys.path manipulation lets the script find the src/ package tree
from pathlib import Path  # WHY: Path resolves the sibling src/ directory portably across OSes

# WHY: prepend the repository root so ``import src.*`` works when the script is
# invoked directly (``python scripts/mist_ideas_analyzer.py``) without an
# active editable install; parents[1] climbs from scripts/ up to the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.mist_ideas_analyzer import main  # noqa: E402  # WHY: import after sys.path setup so the package resolves

if __name__ == "__main__":  # WHY: only invoke the CLI when executed directly, not on import
    main()  # WHY: hand control to the package entry point that owns argument parsing and orchestration
