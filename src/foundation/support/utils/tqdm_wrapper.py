"""tqdm wrapper extracted from MistHelper (initiative 1015 T-14).

Owns the ``tqdm`` progress-bar wrapper originally defined at
MistHelper.py:774-780 as a no-op fallback that was later overridden
with the real ``tqdm`` package during import initialization.

This module resolves the progress wrapper without logging during import.
It tries to import the real ``tqdm`` package and re-exports it under the
name ``tqdm``. When the package is not installed, it falls back to an
iterable pass-through that preserves caller code unchanged.

MistHelper.py re-exports ``tqdm`` at the top of the file so historical
``MistHelper.tqdm`` and ``mh.tqdm`` callers keep working. The re-exported
symbol is the same callable, not a delegator.
"""

from __future__ import annotations  # Enable PEP 604 unions in annotations on 3.10+.

from collections.abc import Iterable  # Type hint for the fallback iterable pass-through.
from typing import Any  # Broad typing for optional kwargs the real tqdm accepts.

try:  # Prefer the real progress-bar package when installed.
    from tqdm import tqdm as _real_tqdm  # Real progress bar.

    tqdm: Any = _real_tqdm  # Re-export the real callable under the canonical name.
except ImportError:  # tqdm not installed -- fall back to a no-op pass-through.

    def tqdm(iterable: Iterable[Any], *_args: Any, **_kwargs: Any) -> Iterable[Any]:  # No-op fallback.
        """Return the iterable unchanged. Used when the real tqdm is unavailable.

        This preserves the caller signature so code that expects a
        progress-bar wrapper keeps working -- there is simply no visible
        progress bar until the real package is installed.
        """
        return iterable  # Iterable pass-through: caller iterates as if tqdm had wrapped it.
