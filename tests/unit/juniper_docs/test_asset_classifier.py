"""Unit tests for the marketing asset classifier (FR-020, FR-027)."""

from __future__ import annotations

import pytest

from src.juniper_docs.classify.asset_classifier import MARKETING_FALLBACK, MarketingAssetClassifier


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            "https://www.juniper.net/content/dam/www/assets/datasheets/us/en/access-points/ap33-datasheet.pdf",
            "datasheets",
        ),
        (
            "https://www.juniper.net/content/dam/www/assets/case-studies/us/en/2024/example-case-study.pdf",
            "case-studies",
        ),
        (
            "https://www.juniper.net/content/dam/www/assets/solution-briefs/us/en/2024/example-brief.pdf",
            "solution-briefs",
        ),
        (
            "https://www.juniper.net/content/dam/www/assets/white-papers/us/en/2023/example-white-paper.pdf",
            "white-papers",
        ),
    ],
)
def test_asset_type_becomes_the_category(url: str, expected: str) -> None:
    """A marketing PDF resolves to the asset type after the assets segment."""
    assert MarketingAssetClassifier().classify(url) == expected  # The path segment wins.


def test_datasheet_lands_in_the_datasheet_category() -> None:
    """A datasheet URL resolves to the datasheet category, the user request."""
    url = "https://www.juniper.net/content/dam/www/assets/datasheets/us/en/switches/ex4400-datasheet.pdf"
    assert MarketingAssetClassifier().classify(url) == "datasheets"  # The datasheet category.


def test_leading_locale_segment_is_skipped() -> None:
    """A locale segment right after assets is skipped for the real asset type."""
    url = "https://www.juniper.net/assets/us/en/local/pdf/whitepapers/74001180-en.pdf"
    assert MarketingAssetClassifier().classify(url) == "local"  # The first non-locale segment.


def test_url_without_an_assets_segment_uses_the_fallback() -> None:
    """A URL with no assets segment resolves to the fixed fallback category."""
    url = "https://www.juniper.net/documentation/us/en/software/jvd/jvd-wan-edge-for-srx.pdf"
    assert MarketingAssetClassifier().classify(url) == MARKETING_FALLBACK  # No asset type.


def test_classification_is_case_folded() -> None:
    """An upper-case asset segment resolves to the lower-case category."""
    url = "https://www.juniper.net/content/dam/www/assets/Datasheets/us/en/example.pdf"
    assert MarketingAssetClassifier().classify(url) == "datasheets"  # One lower-case form.
