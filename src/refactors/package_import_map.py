"""Package name -> import name mapping extracted from MistHelper (SC-025).

Owns the `PACKAGE_IMPORT_MAP` constant originally defined at module
scope in MistHelper.py, and re-lands it on a lightweight
`PackageImportMapManager` seam per FR-005 / FR-015. The sole MistHelper
callsite (`_early_dependency_check` bootstrap wiring) is rewritten in
the same PR to import the extracted constant; no wrapper shim remains
in MistHelper.py after this extraction.

The mapping keys are pip distribution names and values are the
corresponding importable module names -- the pair diverges whenever a
project publishes under one name (e.g. `pillow`) but exposes its API
under another (e.g. `PIL`). The manager class exposes the mapping as a
class-level attribute so consumers can grab it via
`PackageImportMapManager.MAPPING` while keeping the moved surface a
single import symbol.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing


class PackageImportMapManager:  # Class-body seam for the pip-name -> import-name mapping
    """Class-body seam owning the pip-name -> import-name mapping."""

    MAPPING: dict[str, str] = {  # Map pip package names to their importable module names where they differ
        "websocket-client": "websocket",  # pip 'websocket-client' is imported as 'websocket'
        "python-dotenv": "dotenv",  # pip 'python-dotenv' is imported as 'dotenv'
        "usaddress-scourgify": "scourgify",  # pip 'usaddress-scourgify' is imported as 'scourgify'
        "pillow": "PIL",  # pip 'pillow' is imported as 'PIL'
        "beautifulsoup4": "bs4",  # pip 'beautifulsoup4' is imported as 'bs4'
        "pyyaml": "yaml",  # pip 'pyyaml' is imported as 'yaml'
        "python-dateutil": "dateutil",  # pip 'python-dateutil' is imported as 'dateutil'
        "msgpack-python": "msgpack",  # pip 'msgpack-python' is imported as 'msgpack'
        "flask": "flask",  # 'flask' package and import names match (listed for completeness)
        "flask-wtf": "flask_wtf",  # pip 'flask-wtf' is imported as 'flask_wtf' (hyphen becomes underscore)
        "gunicorn": "gunicorn",  # 'gunicorn' package and import names match (listed for completeness)
    }
