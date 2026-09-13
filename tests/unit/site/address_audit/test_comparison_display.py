"""Unit tests for ComparisonTableRenderer (1003-site-address-audit)."""

from src.site.address_audit import comparison_display as display_mod
from src.site.address_audit.comparison_display import ComparisonTableRenderer
from src.site.address_audit.models import AddressRow, AuditResult, MatchedSite

_ROW = AddressRow(
    serial="2012233588", model="SSR130", address="100 Main St Suite 5", city="Town", state="FL", zip_code="33000"
)
_SITE = MatchedSite(
    site_id="s1",
    site_name="Store 181",
    mist_address={"address": "100 Main St", "city": "Town", "state": "FL", "zip": "33000"},
    snmp_location="08095 - 100 Main St Suite 5",
    match_strategy="serial",
    match_confidence=1.0,
)


def _result(suggested="100 Main St Suite 5, Town, FL", issue="MISSING_SUITE"):
    """Build an AuditResult for rendering tests."""
    return AuditResult(
        address_row=_ROW,
        matched_site=_SITE,
        issue_type=issue,
        suggested_address=suggested,
        source="Nominatim",
    )


class TestRender:
    """ComparisonTableRenderer.render output."""

    def test_render_contains_headers_and_data(self):
        """The rendered table includes all column headers and the site name."""
        rendered = ComparisonTableRenderer().render([_result()])
        for header in ["Site Name", "Current Mist Address", "Suggested Address", "Issue Type"]:
            assert header in rendered
        assert "Store 181" in rendered
        assert "MISSING_SUITE" in rendered

    def test_long_values_truncated(self):
        """A very long suggested address is truncated with an ellipsis."""
        rendered = ComparisonTableRenderer().render([_result(suggested="X" * 100)])
        assert "..." in rendered
        assert "X" * 100 not in rendered


class TestPrompt:
    """ComparisonTableRenderer.prompt_post_table choices."""

    def test_save_choice(self, monkeypatch):
        """Entering 1 returns 'save'."""
        monkeypatch.setattr(display_mod.InputUtils, "safe_input", staticmethod(lambda *a, **k: "1"))
        assert ComparisonTableRenderer().prompt_post_table([_result()]) == "save"

    def test_quit_choice(self, monkeypatch):
        """Entering q returns 'quit'."""
        monkeypatch.setattr(display_mod.InputUtils, "safe_input", staticmethod(lambda *a, **k: "q"))
        assert ComparisonTableRenderer().prompt_post_table([_result()]) == "quit"

    def test_invalid_then_valid(self, monkeypatch):
        """An invalid entry re-prompts until a valid choice is given."""
        answers = iter(["x", "1"])
        monkeypatch.setattr(display_mod.InputUtils, "safe_input", staticmethod(lambda *a, **k: next(answers)))
        assert ComparisonTableRenderer().prompt_post_table([_result()]) == "save"
