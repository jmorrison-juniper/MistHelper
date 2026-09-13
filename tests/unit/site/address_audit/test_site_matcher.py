"""Unit tests for SiteMatchingEngine (1003-site-address-audit)."""

from src.site.address_audit import site_matcher as matcher_mod
from src.site.address_audit.site_matcher import SiteMatchingEngine

_SITES = [
    {"id": "s1", "name": "Store 181", "address": "5550 N Military Trail", "city": "Boca Raton", "state": "FL"},
    {"id": "s2", "name": "Store 182", "address": "6000 Glades Rd", "city": "Boca Raton", "state": "FL"},
]
_INVENTORY = {
    "2012233588": {"serial": "2012233588", "site_id": "s1"},
    "2012234081": {"serial": "2012234081", "site_id": None},  # claimed but unassigned
}
_SITES_BY_ID = {s["id"]: s for s in _SITES}


class TestMatchSerial:
    """SiteMatchingEngine.match_serial golden-key behavior."""

    def test_serial_hit(self):
        """A serial assigned to a site matches with strategy 'serial'."""
        engine = SiteMatchingEngine(_INVENTORY, _SITES_BY_ID)
        result = engine.match_serial("2012233588")
        assert result.match_strategy == "serial"
        assert result.site_id == "s1"
        assert result.match_confidence == 1.0
        assert result.mist_address["address"] == "5550 N Military Trail"

    def test_serial_miss_unmatched(self):
        """An unknown serial returns unmatched (engine then tries fuzzy)."""
        engine = SiteMatchingEngine(_INVENTORY, _SITES_BY_ID)
        assert engine.match_serial("0000000000").match_strategy == "unmatched"

    def test_unassigned_device_unmatched(self):
        """A claimed-but-unassigned device (null site_id) is unmatched."""
        engine = SiteMatchingEngine(_INVENTORY, _SITES_BY_ID)
        assert engine.match_serial("2012234081").match_strategy == "unmatched"


class TestMatchFuzzy:
    """SiteMatchingEngine.match_fuzzy fallback behavior."""

    def test_fuzzy_hit_above_threshold(self):
        """A close address match returns strategy 'fuzzy' with scaled confidence."""
        engine = SiteMatchingEngine(_INVENTORY, _SITES_BY_ID, fuzzy_threshold=80.0)
        result = engine.match_fuzzy("5550 N Military Trail Boca Raton FL", _SITES)
        assert result.match_strategy == "fuzzy"
        assert result.site_id == "s1"
        assert 0.0 < result.match_confidence <= 1.0

    def test_fuzzy_below_threshold_unmatched(self):
        """An unrelated address falls below the cutoff -> unmatched."""
        engine = SiteMatchingEngine(_INVENTORY, _SITES_BY_ID, fuzzy_threshold=95.0)
        assert engine.match_fuzzy("totally different place xyz", _SITES).match_strategy == "unmatched"

    def test_empty_address_unmatched(self):
        """An empty query is unmatched without error."""
        engine = SiteMatchingEngine(_INVENTORY, _SITES_BY_ID)
        assert engine.match_fuzzy("", _SITES).match_strategy == "unmatched"

    def test_rapidfuzz_absent_unmatched(self, monkeypatch):
        """When rapidfuzz is unavailable, fuzzy matching degrades to unmatched."""
        monkeypatch.setattr(matcher_mod, "process", None)
        monkeypatch.setattr(matcher_mod, "fuzz", None)
        engine = SiteMatchingEngine(_INVENTORY, _SITES_BY_ID)
        assert engine.match_fuzzy("5550 N Military Trail", _SITES).match_strategy == "unmatched"
