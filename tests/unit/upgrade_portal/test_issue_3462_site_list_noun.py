"""Unit tests for the noun of the multi-site site refusals.

Why:
    Issue #3462. Each save refusal put the plural noun "these sites" before
    the list of site names, also for a list of one name. The operator then
    read "at these sites: Site A". These tests read the whole text of each
    refusal for one, two, and twelve sites. They call the class directly, so
    they need no route, no cloud, and no browser.
"""

from __future__ import annotations

import pytest

from src.upgrade_portal.upgrade.org_site_records import (
    NAME_LIMIT,
    SHORT_MESSAGE,
    UNPLANNED_MESSAGE,
    UNREAD_MESSAGE,
    OrgSiteRefusal,
)

ONE_LABEL = ["Site A"]  # A refusal that names one site.
TWO_LABELS = ["Site A", "Site B"]  # A refusal that names two sites.
TWELVE_LABELS = [f"Site {number}" for number in range(1, NAME_LIMIT + 3)]  # Two names more than the limit.
UNREAD_ADVICE = (  # The advice of the refusal for a site with no device.
    "Save the options again. If a site holds no device, clear that site on the Sites page."
)
UNPLANNED_ADVICE = (  # The advice of the refusal for a site with no planned device.
    "Check the device types and the target versions. "
    "If a site holds no device of the checked types, clear that site on the Sites page."
)
SHORT_ADVICE = "Reload this page. Then save the options again."  # The advice of the refusal for a short site.
TEMPLATE_IDS = ["unread", "unplanned", "short"]  # One test identifier for each refusal.


@pytest.mark.parametrize(
    ("count", "place"),
    [(1, "this site"), (2, "these sites"), (12, "these sites"), (0, "these sites")],
    ids=["one-site", "two-sites", "twelve-sites", "no-site"],
)
def test_the_place_words_follow_the_count(count: int, place: str) -> None:
    """FR-006: one site takes the singular noun, and each other count takes the plural noun."""
    assert OrgSiteRefusal.place_text(count) == place  # The words before the list of names.


@pytest.mark.parametrize(
    ("template", "text"),
    [
        (UNREAD_MESSAGE, f"The portal read no device at this site: Site A. {UNREAD_ADVICE}"),
        (UNPLANNED_MESSAGE, f"The plan holds no device at this site: Site A. {UNPLANNED_ADVICE}"),
        (SHORT_MESSAGE, f"The portal did not read the complete device list at this site: Site A. {SHORT_ADVICE}"),
    ],
    ids=TEMPLATE_IDS,
)
def test_a_refusal_of_one_site_names_this_site(template: str, text: str) -> None:
    """FR-003: the old text said "at these sites: Site A" for one site."""
    assert str(OrgSiteRefusal(template, ONE_LABEL)) == text  # The whole text that the flash region shows.


@pytest.mark.parametrize(
    ("template", "text"),
    [
        (UNREAD_MESSAGE, f"The portal read no device at these sites: Site A, Site B. {UNREAD_ADVICE}"),
        (UNPLANNED_MESSAGE, f"The plan holds no device at these sites: Site A, Site B. {UNPLANNED_ADVICE}"),
        (
            SHORT_MESSAGE,
            f"The portal did not read the complete device list at these sites: Site A, Site B. {SHORT_ADVICE}",
        ),
    ],
    ids=TEMPLATE_IDS,
)
def test_a_refusal_of_two_sites_names_these_sites(template: str, text: str) -> None:
    """FR-003: two or more sites keep the plural noun."""
    assert str(OrgSiteRefusal(template, TWO_LABELS)) == text  # The whole text that the flash region shows.


def test_a_long_refusal_keeps_the_plural_noun() -> None:
    """FR-005: a list above the limit names ten sites and the count of the rest, with the plural noun."""
    shown = ", ".join(TWELVE_LABELS[:NAME_LIMIT])  # The ten names that the refusal shows.
    expected = f"The portal read no device at these sites: {shown}, and 2 more. {UNREAD_ADVICE}"  # The whole text.
    assert str(OrgSiteRefusal(UNREAD_MESSAGE, TWELVE_LABELS)) == expected  # Twelve sites, and ten names show.


def test_a_refusal_of_one_identifier_names_this_site() -> None:
    """A site with no name shows its identifier, and the noun rule counts that site too."""
    identifier = "00000000-0000-0000-0000-0000000000ee"  # The label of a site whose name read failed.
    expected = f"The portal read no device at this site: {identifier}. {UNREAD_ADVICE}"  # The whole text.
    assert str(OrgSiteRefusal(UNREAD_MESSAGE, [identifier])) == expected  # One identifier is one site.
