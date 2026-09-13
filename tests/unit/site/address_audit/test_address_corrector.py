"""Unit tests for AddressCorrector write-back (1003-site-address-audit).

All Mist calls are mocked -- no live API is touched. Tests cover the correctable
filter, the per-site review/confirm loop, the fetch-modify-PUT update, and the
fail-soft behavior on permission/API errors.
"""

from unittest.mock import MagicMock

from src.site.address_audit import address_corrector as corr_mod
from src.site.address_audit.address_corrector import AddressCorrector
from src.site.address_audit.models import AddressRow, AuditResult, MatchedSite


def _result(issue="MISSING_SUITE", site_id="s1", mist="100 Main St", suggested="100 Main St Suite 5, Town, FL"):
    """Build an AuditResult for write-back tests."""
    row = AddressRow(
        serial="1", model="SSR130", address="100 Main St Suite 5", city="Town", state="FL", zip_code="33000"
    )
    site = MatchedSite(
        site_id=site_id,
        site_name="Store 181",
        mist_address={"address": mist},
        match_strategy="serial",
    )
    return AuditResult(address_row=row, matched_site=site, issue_type=issue, suggested_address=suggested)


class TestCorrectable:
    """The correctable filter selects only pushable corrections."""

    def test_includes_correctable_states(self):
        """MISSING_SUITE/MISSING_NUMBER/WRONG_STREET/CSV_BETTER/AMBIGUOUS with a diff are included."""
        results = [
            _result(issue=s) for s in ("MISSING_SUITE", "MISSING_NUMBER", "WRONG_STREET", "CSV_BETTER", "AMBIGUOUS")
        ]
        assert len(AddressCorrector(MagicMock()).correctable(results)) == 5

    def test_excludes_non_correctable_states(self):
        """ADDRESS_MATCH / MIST_BETTER / NO_RESULT / UNMATCHED are excluded."""
        results = [_result(issue=s) for s in ("ADDRESS_MATCH", "MIST_BETTER", "NO_RESULT", "UNMATCHED")]
        assert AddressCorrector(MagicMock()).correctable(results) == []

    def test_excludes_when_no_site_id(self):
        """A row without a site_id cannot be pushed."""
        assert AddressCorrector(MagicMock()).correctable([_result(site_id="")]) == []

    def test_excludes_when_suggestion_equals_current(self):
        """No push when the suggestion equals the current Mist address (case-insensitive)."""
        same = _result(mist="100 Main St Suite 5, Town, FL", suggested="100 Main St Suite 5, Town, FL")
        assert AddressCorrector(MagicMock()).correctable([same]) == []


class TestUpdateSiteAddress:
    """The fetch-modify-PUT mechanics."""

    def test_fetch_modify_put_preserves_other_fields(self, monkeypatch):
        """Only 'address' changes; everything else in the site record is preserved on PUT."""
        get_resp = MagicMock()
        get_resp.data = {
            "id": "s1",
            "address": "OLD",
            "latlng": {"lat": 1, "lng": 2},
            "timezone": "X",
            "country_code": "US",
        }
        put_resp = MagicMock()
        put_resp.status_code = 200
        sites = MagicMock()
        sites.getSiteInfo.return_value = get_resp
        sites.updateSiteInfo.return_value = put_resp
        monkeypatch.setattr(corr_mod.mistapi.api.v1.sites, "sites", sites)
        api = MagicMock()
        ok = AddressCorrector(api)._update_site_address("s1", "NEW ADDRESS")
        assert ok is True
        body = sites.updateSiteInfo.call_args.args[2]
        assert body["address"] == "NEW ADDRESS"  # changed
        assert body["latlng"] == {"lat": 1, "lng": 2}  # preserved
        assert body["timezone"] == "X" and body["country_code"] == "US"  # preserved

    def test_non_2xx_is_failure(self, monkeypatch):
        """A non-2xx status (e.g. 403 read-only token) is a failed update."""
        get_resp = MagicMock()
        get_resp.data = {"id": "s1", "address": "OLD"}
        put_resp = MagicMock()
        put_resp.status_code = 403
        sites = MagicMock()
        sites.getSiteInfo.return_value = get_resp
        sites.updateSiteInfo.return_value = put_resp
        monkeypatch.setattr(corr_mod.mistapi.api.v1.sites, "sites", sites)
        assert AddressCorrector(MagicMock())._update_site_address("s1", "NEW") is False

    def test_empty_site_record_is_failure(self, monkeypatch):
        """An empty/list site payload cannot be written back."""
        get_resp = MagicMock()
        get_resp.data = []
        sites = MagicMock()
        sites.getSiteInfo.return_value = get_resp
        monkeypatch.setattr(corr_mod.mistapi.api.v1.sites, "sites", sites)
        assert AddressCorrector(MagicMock())._update_site_address("s1", "NEW") is False
        sites.updateSiteInfo.assert_not_called()


class TestReviewAndApply:
    """The per-site review/confirm loop."""

    def test_yes_pushes_no_skips(self, monkeypatch):
        """'y' pushes the correction; 'n' records a skip; both appear in outcomes."""
        corrector = AddressCorrector(MagicMock())
        monkeypatch.setattr(corrector, "_update_site_address", lambda *_: True)
        answers = iter(["y", "n"])
        monkeypatch.setattr(corr_mod.InputUtils, "safe_input", staticmethod(lambda *a, **k: next(answers)))
        outcomes = corrector.review_and_apply([_result(site_id="s1"), _result(site_id="s2")])
        assert [o.action for o in outcomes] == ["pushed", "skipped"]

    def test_push_failure_is_failed_outcome(self, monkeypatch):
        """An exception during the push yields a failed outcome, not a crash."""
        corrector = AddressCorrector(MagicMock())

        def boom(*_):
            raise RuntimeError("403 forbidden")

        monkeypatch.setattr(corrector, "_update_site_address", boom)
        monkeypatch.setattr(corr_mod.InputUtils, "safe_input", staticmethod(lambda *a, **k: "y"))
        outcomes = corrector.review_and_apply([_result()])
        assert outcomes[0].action == "failed"
        assert "403" in outcomes[0].error

    def test_no_targets_returns_empty(self, monkeypatch):
        """With nothing correctable, review_and_apply returns [] and prompts nothing."""
        spy = MagicMock()
        monkeypatch.setattr(corr_mod.InputUtils, "safe_input", spy)
        assert AddressCorrector(MagicMock()).review_and_apply([_result(issue="ADDRESS_MATCH")]) == []
        spy.assert_not_called()
