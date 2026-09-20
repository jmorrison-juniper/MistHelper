"""Unit tests for the slug classifier (T022, FR-020, FR-021)."""

from __future__ import annotations

import pytest

from src.juniper_docs.classify.slug_classifier import SlugClassifier


@pytest.mark.parametrize(
    ("slug", "expected"),
    [
        ("software/junos/release-notes/junos-release-notes-23.4r1", "release-notes"),
        ("software/junos-configuration-guide", "configuration-guides"),
        ("software/junos-administration-guide", "administration-guides"),
        ("hardware/srx340-installation-guide", "installation-guides"),
        ("software/junos-cli-reference", "cli-reference"),
        ("software/junos-rest-api-guide", "api"),
        ("software/junos-security-hardening", "security-and-compliance"),
        ("software/junos-migration-guide", "migration"),
        ("software/jvd/data-center-design", "design"),
    ],
)
def test_each_category_matches_its_keyword(slug: str, expected: str) -> None:
    """Each category slug resolves to the matching category."""
    assert SlugClassifier().classify(slug) == expected  # The keyword drives the category.


def test_no_keyword_returns_uncategorized() -> None:
    """A slug with no category keyword resolves to the uncategorized bucket."""
    assert SlugClassifier().classify("software/srx-overview-topic") == "uncategorized"


def test_precedence_prefers_installation_over_configuration() -> None:
    """A slug that matches install and config returns installation guides."""
    slug = "software/srx-installation-and-configuration-guide"  # Two keywords match.
    assert SlugClassifier().classify(slug) == "installation-guides"  # Install ranks higher.


def test_short_keyword_does_not_match_inside_a_word() -> None:
    """The short api keyword does not match inside an unrelated word."""
    assert SlugClassifier().classify("software/capital-planning") == "uncategorized"
