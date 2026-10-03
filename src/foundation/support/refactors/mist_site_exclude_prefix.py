"""Own the ``MIST_SITE_EXCLUDE_PREFIX`` site filter.

This module owns the site-name prefix filter. The bootstrap reads the
``MIST_SITE_EXCLUDE_PREFIX`` environment variable and publishes the value here.
The prefix protects matching sites from destructive operations.

The landing follows E-14 as a bare module constant. No wrapper class exists.
No getter function exists. An absent environment variable excludes no sites.
"""

from __future__ import annotations  # Enable PEP 604 unions in annotations on 3.10+.

MIST_SITE_EXCLUDE_PREFIX: str = ""  # Bootstrap publishes the configured prefix after import.
