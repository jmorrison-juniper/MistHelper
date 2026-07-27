"""Shared suite/unit regex patterns for the address-audit feature (1003-site-address-audit).

Historically three modules each defined their own suite/unit keyword regex
(``address_resolver``, ``audit_engine``, ``ui_geocoder``), which drifted out of
sync -- a real customer file spelled it ``Sute A-103`` and only some detectors
recognized it. This module is the single source of truth: every suite detector
now derives from :data:`SUITE_KEYWORDS`, so adding a spelling here fixes it
everywhere.

State-safety (the guiding constraint): a suite marker must be an explicit keyword
or a ``#NNN`` hash unit, never a bare token that could be a state code (``FL``) or
a ZIP. That is why the keyword form requires one of the known keywords and the
hash form (in the classification patterns) requires a leading digit.
"""

from __future__ import annotations  # WHY: PEP 604 union syntax on Python 3.13

# Single source of truth for suite/unit keywords. ``sute`` is a common misspelling
# of ``suite`` seen in real customer data; a trailing period (``Ste.``) is matched
# by the ``\.?`` in the patterns below, and ``ste`` already covers the abbreviation.
# ``suit`` is deliberately excluded -- it would match ``lawsuit`` / ``pursuit``.
SUITE_KEYWORDS = r"ste|suite|sute|unit|apt|apartment|bldg|building|space|spc|rm|room|lot"  # WHY: suite/unit vocabulary

# Detection form (NO capture groups): a keyword+id, or a bare ``#<digit...>`` hash
# unit. Used for boolean "does this address carry a suite?" checks in the resolver.
SUITE_PATTERN = rf"\b(?:{SUITE_KEYWORDS})\b\.?\s*#?\s*[\w-]+|#\s*\d[\w-]*"  # WHY: boolean detection - no captures

# Capture form: group(1) = keyword unit id, group(2) = hash unit id. Used by the
# engine to extract the bare unit identifier for suite comparison/adjudication.
SUITE_PATTERN_CAPTURE = rf"\b(?:{SUITE_KEYWORDS})\b\.?\s*#?\s*([\w-]+)|#\s*(\d[\w-]*)"  # WHY: extraction - kw/hash ids

# Phrase form (case-insensitive): the FULL matched keyword token (for example ``Unit 200``,
# ``Ste A2``). The id must start alphanumeric and may carry an internal hyphen. Used
# by the UI geocoder to lift the exact phrase the operator typed so it can be
# re-appended verbatim to a Google suggestion that dropped it.
SUITE_PHRASE_PATTERN = rf"(?i)\b(?:{SUITE_KEYWORDS})\b\.?\s*#?\s*[A-Za-z0-9][A-Za-z0-9-]*"  # WHY: case-insens UI form

# Bare hash unit for the UI geocoder's phrase extraction: unlike the classification
# hash form this allows a letter-first id (``#A5``) because it only ever restores a
# unit the operator explicitly typed (never used to infer a state/ZIP).
HASH_UNIT_PATTERN = r"#\s*[A-Za-z0-9][A-Za-z0-9-]*"  # WHY: bare hash unit for phrase extraction only
