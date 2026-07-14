"""Wave 3 top-up tests for SiteMatchingEngine (initiative 1018).

Targets the last uncovered branch in
``src/site/address_audit/site_matcher.py`` -- the ``continue`` on
line 86 of ``_build_choice_map`` when a site record lacks an ``id``.
Existing test module ``test_site_matcher.py`` already covers every
other branch; this file only adds the malformed-site-record path.
"""

from __future__ import annotations  # WHY: PEP 604 unions retained across whole test module.

from src.site.address_audit.site_matcher import SiteMatchingEngine  # WHY: SUT under test.

# WHY: Minimal inventory + sites_by_id keep the engine construction cheap; not exercised here.
_INVENTORY: dict[str, dict[str, object]] = {}  # WHY: no serial lookups in these tests.
_SITES_BY_ID: dict[str, dict[str, object]] = {}  # WHY: no site_id lookups in these tests.


class TestBuildChoiceMapMalformedSite:
    """Cover the ``continue`` branch when a site record is missing its ``id``."""

    def test_site_without_id_is_skipped(self) -> None:
        """A site record with no ``id`` key must be silently skipped, not raise."""
        engine = SiteMatchingEngine(_INVENTORY, _SITES_BY_ID)  # WHY: default threshold is fine.
        sites = [  # WHY: mix one valid and one malformed record to prove filtering, not aborting.
            {"id": "good-1", "address": "1 Main", "city": "Boca", "state": "FL"},  # kept.
            {"address": "999 Nowhere"},  # WHY: no id -> must trigger the line-86 continue branch.
        ]
        result = engine._build_choice_map(sites)  # WHY: exercise the private helper directly.
        assert "good-1" in result  # WHY: the valid record survives the filter.
        assert len(result) == 1  # WHY: proves the malformed record was dropped rather than keyed on "".

    def test_all_sites_missing_id_returns_empty(self) -> None:
        """When every site is malformed, the resulting map is empty (not raising)."""
        engine = SiteMatchingEngine(_INVENTORY, _SITES_BY_ID)  # WHY: fresh engine per test.
        sites = [{"address": "no id here"}, {"city": "still no id"}]  # WHY: all rows hit line 86.
        assert engine._build_choice_map(sites) == {}  # WHY: empty map means the continue fired for every row.
