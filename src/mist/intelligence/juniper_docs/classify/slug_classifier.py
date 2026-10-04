"""Classify each document into a top-level category from its slug.

The classifier matches the slug against a keyword map for the category set and
returns the uncategorized bucket when no keyword matches. When a slug matches
more than one category, a fixed precedence order gives a reproducible result
(FR-020, FR-021).
"""

from __future__ import annotations  # Enable modern union syntax on every annotation.

import logging  # Trace each classification for observability.
import re  # Match a keyword at a token boundary in the slug.

_LOGGER = logging.getLogger(__name__)  # Module logger for the slug classification.

UNCATEGORIZED = "uncategorized"  # The bucket for a slug that matches no keyword.

# The category rules run in this fixed precedence order, so a slug that matches
# more than one keyword resolves the same way on every run (FR-021). A letter of
# volatility ranks above security so a compliance token never hides it, and the
# generic guide rule ranks last so a specific guide keeps its exact category.
_CATEGORY_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("release-notes", ("release-note", "relnote")),
    ("letters-of-volatility", ("letter-of-volatility",)),
    ("security-and-compliance", ("security", "compliance", "hardening")),
    ("migration", ("migration", "migrate")),
    ("installation-guides", ("install", "quick-start", "hardware-guide")),
    ("configuration-guides", ("config",)),
    ("administration-guides", ("admin",)),
    ("cli-reference", ("cli", "command-reference")),
    ("api", ("api", "openconfig")),
    ("design", ("design", "reference-architecture", "jvd", "validated-design")),
    ("datasheets", ("datasheet",)),
    ("guides", ("user-guide", "guide")),
)


class SlugClassifier:
    """Match one document slug to a top-level category with a fixed precedence."""

    def classify(self, slug: str) -> str:
        """Return the first category whose keyword matches, or uncategorized."""
        _LOGGER.debug("Classifying slug %s", slug)  # Trace the classification.
        lowered = slug.lower()  # Compare in one case only.
        for category, keywords in _CATEGORY_RULES:  # Walk the rules in precedence order.
            if any(self._matches(keyword, lowered) for keyword in keywords):  # A keyword hit.
                _LOGGER.debug("Slug %s matched category %s", slug, category)  # Result.
                return category  # The first matching category wins by precedence.
        return UNCATEGORIZED  # No keyword matched, so the document is uncategorized.

    @staticmethod
    def _matches(keyword: str, slug: str) -> bool:
        """Return True when a keyword starts at a token boundary in the slug."""
        return re.search(r"(?<![a-z])" + re.escape(keyword), slug) is not None  # Prefix hit.
