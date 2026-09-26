"""Map each MistHelper menu option to the Mist API endpoints that it can reach.

The tool reads ``MistHelper.py`` and the ``src/`` tree with static analysis only.
It imports no project module, and it calls no API. It writes one index page and
one page for each registry category under ``documentation/menu-api/``, and the
same pages for the wiki under ``documentation/wiki/``. The ``--check`` mode fails
when a page on disk differs from the generated text. See
``specs/3411-docs-audit/`` for the full specification.
"""

# Package-level semantic version. Bump this when the page format changes.
__version__ = "1.0.0"  # Read by the --version flag and by the page footer.
