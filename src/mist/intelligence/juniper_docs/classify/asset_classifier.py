"""Classify a marketing asset by its asset-type path segment.

A marketing PDF lives at ``/content/dam/www/assets/<type>/us/en/...``. The
segment after ``assets`` names the asset type, such as ``datasheets`` or
``case-studies``. That segment is a reliable category signal, so a marketing
asset needs no content analysis. The classifier reads the path segment and
returns the type as the category (FR-020, FR-027).
"""

from __future__ import annotations  # Enable modern union syntax on every annotation.

import logging  # Trace each marketing classification for observability.
from urllib.parse import urlsplit  # Read the path segments of one asset URL.

_LOGGER = logging.getLogger(__name__)  # Module logger for the asset classification.

MARKETING_FALLBACK = "marketing-asset"  # The category when a URL names no asset type.
_LOCALE_TOKENS = frozenset({"us", "en", "en_us"})  # Locale segments that are not a type.
_ASSET_MARKER = "assets"  # The path segment before the asset-type segment.


class MarketingAssetClassifier:
    """Derive a marketing category from the ``/assets/<type>/`` path segment."""

    def classify(self, url: str) -> str:
        """Return the asset-type category for one marketing PDF URL."""
        _LOGGER.debug("Classifying marketing asset %s", url)  # Trace the classification.
        segments = urlsplit(url).path.strip("/").split("/")  # The path segments only.
        category = self._asset_type(segments)  # The first type after the assets segment.
        _LOGGER.debug("Marketing asset %s mapped to %s", url, category)  # Result category.
        return category  # The category names the marketing output folder.

    @staticmethod
    def _asset_type(segments: list[str]) -> str:
        """Return the first non-locale segment after ``assets``, or the fallback."""
        if _ASSET_MARKER not in segments:  # A URL with no assets segment names no type.
            return MARKETING_FALLBACK  # Use the fixed fallback category name.
        after = segments[segments.index(_ASSET_MARKER) + 1 :]  # Segments past the marker.
        for segment in after:  # Skip a leading locale token such as us or en.
            if segment.lower() not in _LOCALE_TOKENS:  # The first real type segment wins.
                return segment.lower()  # The asset type names the category.
        return MARKETING_FALLBACK  # Only locale tokens followed the assets segment.
