"""Fast-mode module-level constants extracted from MistHelper (initiative 1015, T-02).

Home for bare module-level constants that tune the fast-mode concurrent-execution
pipeline in MistHelper. Kept as plain module-level names (not class attributes) per
the T-02 landing-target decision: single co-location file for the remaining
fast-mode env-derived constants (T-02 + T-03 anticipated additions) to avoid
per-constant module proliferation. No wrapper class, no facade, no shim -- all
callers import the bare name directly from this module.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing

import os  # Read the environment override value at import time

# WHAT: Ceiling on simultaneous outbound API connections used by fast-mode workflows.
# WHY: fast-mode concurrent-connection cap -- bounds ThreadPoolExecutor sizing and
#      the connection-aware semaphore so we do not exceed the Mist API rate limits
#      or exhaust the local HTTP connection pool. Sourced from the
#      FAST_MODE_MAX_CONCURRENT_CONNECTIONS env var (default 8) at import time.
FAST_MODE_MAX_CONCURRENT_CONNECTIONS: int = int(  # Cap on simultaneous API connections in fast mode
    os.getenv("FAST_MODE_MAX_CONCURRENT_CONNECTIONS", "8")  # Env override with 8 default
)
