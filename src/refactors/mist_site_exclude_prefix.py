"""``MIST_SITE_EXCLUDE_PREFIX`` constant extracted from MistHelper (initiative 1015 T-15).

Owns the site-name-prefix filter originally defined at
``MistHelper.py`` lines 2138-2143 as a module-level assignment reading
the ``MIST_SITE_EXCLUDE_PREFIX`` environment variable. The prefix
shields sites whose name starts with the configured value from
destructive operations (for example Menu #149 WAN2 migration, Menu #166 WAN
probe configuration, Menu #167 WAN probe device overrides).

Landing per E-14 as a **bare module-level constant**. No wrapper
class exists, and no getter function exists. The bootstrap publishes the
configured value after import. A missing env var means "no sites excluded".

``MistHelper.py`` re-exports the constant so historical
``MistHelper.MIST_SITE_EXCLUDE_PREFIX`` and ``mh.MIST_SITE_EXCLUDE_PREFIX``
callers keep working. The bootstrap updates the copied values together.
"""

from __future__ import annotations  # Enable PEP 604 unions in annotations on 3.10+.

MIST_SITE_EXCLUDE_PREFIX: str = ""  # Bootstrap publishes the configured prefix after import.
