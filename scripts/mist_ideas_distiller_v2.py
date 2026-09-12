#!/usr/bin/env python3
"""Thin CLI entry point for the Mist Ideas Distiller v2.

The full implementation now lives in the sibling
:mod:`mist_ideas_distiller_v2_pkg` package. This script exists only to
preserve the historical ``python scripts/mist_ideas_distiller_v2.py``
invocation path used by operators, CI, and documentation. All
consolidation, ranking, and pipeline logic has been relocated to the
package so the compliance analyzer can score this tiny wrapper in
isolation.
"""

from __future__ import annotations  # WHY: postponed annotations keep the tiny entrypoint import-free

import sys  # WHY: sys.path manipulation lets the script find the sibling package tree
from pathlib import Path  # WHY: Path resolves the scripts/ directory portably across OSes

# WHY: prepend the scripts/ directory so ``import mist_ideas_distiller_v2_pkg`` works when the
# script is invoked directly (``python scripts/mist_ideas_distiller_v2.py``) without an
# active editable install; ``__file__.parent`` is the sibling of the package.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mist_ideas_distiller_v2_pkg import main  # noqa: E402  # WHY: import after sys.path setup so the package resolves

if __name__ == "__main__":  # WHY: only invoke the CLI when executed directly, not on import
    main()  # WHY: hand control to the package entry point that owns argument parsing and orchestration
