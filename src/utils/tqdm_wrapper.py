"""tqdm wrapper extracted from MistHelper (initiative 1015 T-14).

Owns the ``tqdm`` progress-bar wrapper originally defined at
MistHelper.py:774-780 as a no-op fallback that was later overridden
with the real ``tqdm`` package during import initialization.

This module resolves the tension at import time: it tries to import the
real ``tqdm`` package and re-exports it under the name ``tqdm``; when
the package is not installed, it falls back to an iterable pass-through
that preserves caller code unchanged. Callers therefore always get a
callable named ``tqdm`` that accepts the same signature regardless of
package availability -- no runtime rebinding of a module-global is
required, which removes the fragile ordering dependency between the
fallback definition and its later overrider.

MistHelper.py re-exports ``tqdm`` at the top of the file so historical
``MistHelper.tqdm`` / ``mh.tqdm`` callers keep working transparently --
the re-exported symbol is the same callable, not a delegator.
"""

from __future__ import annotations  # Enable PEP 604 unions in annotations on 3.10+.

import logging  # Structured action logging per Constitution VII (remediates missing_action_logging).
from collections.abc import Iterable  # Type hint for the fallback iterable pass-through.
from typing import Any  # Broad typing for optional kwargs the real tqdm accepts.

try:  # Prefer the real progress-bar package when installed.
    from tqdm import tqdm as _real_tqdm  # Real progress bar.

    tqdm: Any = _real_tqdm  # Re-export the real callable under the canonical name.
    logging.debug("tqdm_wrapper: real tqdm resolved from installed package.")  # Debug envelope: real path.
except ImportError:  # tqdm not installed -- fall back to a no-op pass-through.
    logging.info("tqdm_wrapper: real tqdm not installed; using no-op fallback.")  # Info envelope: fallback path.

    def tqdm(iterable: Iterable[Any], *_args: Any, **_kwargs: Any) -> Iterable[Any]:  # No-op fallback.
        """Return the iterable unchanged; used when the real tqdm is unavailable.

        This preserves the caller signature so code that expects a
        progress-bar wrapper keeps working -- there is simply no visible
        progress bar until the real package is installed.
        """
        logging.debug("tqdm_wrapper: no-op tqdm invoked (real package missing).")  # Trace fallback invocation.
        return iterable  # Iterable pass-through: caller iterates as if tqdm had wrapped it.
