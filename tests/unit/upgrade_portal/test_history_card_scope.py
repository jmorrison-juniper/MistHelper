"""Verify the nine card descriptions for each authorized history scope."""

from __future__ import annotations

from dataclasses import asdict, fields
from typing import Any
from unittest.mock import create_autospec

import pytest

from src.upgrade_portal.app.history_descriptions import HistoryCardDescription, HistoryCardScope
from src.upgrade_portal.app.routes import review


class TestHistoryCardScope:
    """Keep the description rules inside the dedicated semantic view model."""

    @pytest.mark.parametrize(
        "site_id,rows,expected",
        [
            (
                "site-with-no-records",
                [],
                {
                    "runs": {
                        "note": "The single-site upgrade runs of the selected site, newest first.",
                        "caption": "The single-site upgrade runs of the selected site.",
                        "empty": "This page shows no single-site upgrade run for the selected site.",
                    },
                    "operations": {
                        "note": "The multi-site upgrades that include the selected site, newest first.",
                        "caption": "The multi-site upgrades that include the selected site.",
                        "empty": "This page shows no multi-site upgrade that includes the selected site.",
                    },
                    "audit": {
                        "note": "The site lock actions of the selected site, newest first.",
                        "caption": "The site lock actions of the selected site.",
                        "empty": "This page shows no site lock action for the selected site.",
                    },
                },
            ),
            (
                "site-a",
                [{"site_name": 'Site <A> & "North"'}],
                {
                    "runs": {
                        "note": 'The single-site upgrade runs of Site <A> & "North", newest first.',
                        "caption": 'The single-site upgrade runs of Site <A> & "North".',
                        "empty": 'This page shows no single-site upgrade run for Site <A> & "North".',
                    },
                    "operations": {
                        "note": 'The multi-site upgrades that include Site <A> & "North", newest first.',
                        "caption": 'The multi-site upgrades that include Site <A> & "North".',
                        "empty": 'This page shows no multi-site upgrade that includes Site <A> & "North".',
                    },
                    "audit": {
                        "note": 'The site lock actions of Site <A> & "North", newest first.',
                        "caption": 'The site lock actions of Site <A> & "North".',
                        "empty": 'This page shows no site lock action for Site <A> & "North".',
                    },
                },
            ),
            (
                "",
                [{"site_name": "Selected Alpha"}, {"site_name": "Selected Beta"}],
                {
                    "runs": {
                        "note": "The single-site upgrade runs of the selected organization, newest first.",
                        "caption": "The single-site upgrade runs of the selected organization.",
                        "empty": "This page shows no single-site upgrade run for the selected organization.",
                    },
                    "operations": {
                        "note": "The multi-site upgrades of the selected organization, newest first.",
                        "caption": "The multi-site upgrades of the selected organization.",
                        "empty": "This page shows no multi-site upgrade for the selected organization.",
                    },
                    "audit": {
                        "note": "The site lock actions of the selected organization, newest first.",
                        "caption": "The site lock actions of the selected organization.",
                        "empty": "This page shows no site lock action for the selected organization.",
                    },
                },
            ),
        ],
    )
    def test_all_nine_descriptions(
        self, site_id: str, rows: list[dict[str, Any]], expected: dict[str, dict[str, str]]
    ) -> None:
        """Require exact complete strings for unnamed, named, and organization scopes."""
        validated = review.HistoryScope.for_page(site_id, rows)
        scope = HistoryCardScope(validated.site_id, validated.site_name)
        actual = {attribute: asdict(getattr(scope, attribute)) for attribute in expected}
        assert actual == expected
        assert [field.name for field in fields(scope)] == ["site_id", "site_name"]
        assert [field.name for field in fields(HistoryCardDescription)] == ["note", "empty", "caption"]

    @pytest.mark.parametrize("rows", [[{}], [{"site_name": None}], [{"site_name": ""}]])
    def test_missing_name_never_prints_the_requested_identifier(self, rows: list[dict[str, Any]]) -> None:
        """An empty display name must not become a query identifier or a fabricated site name."""
        validated = review.HistoryScope.for_page("UNTRUSTED-site-identifier", rows)
        scope = HistoryCardScope(validated.site_id, validated.site_name)
        groups = [asdict(card) for card in (scope.runs, scope.operations, scope.audit)]
        assert all("the selected site" in text for group in groups for text in group.values())
        assert all("UNTRUSTED" not in text for group in groups for text in group.values())
        assert HistoryCardDescription.scope_subject(scope.site_id, scope.site_name) == "the selected site"

    def test_organization_scope_reads_no_site_name(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A first row cannot change the subject of organization-wide descriptions."""
        reader = create_autospec(review.read_site_name, side_effect=AssertionError("Do not read one site's name."))
        monkeypatch.setattr(review, "read_site_name", reader)
        validated = review.HistoryScope.for_page("", [{"site_name": "Unrelated first row"}])
        scope = HistoryCardScope(validated.site_id, validated.site_name)
        assert scope.runs.caption == "The single-site upgrade runs of the selected organization."
        reader.assert_not_called()

    def test_name_text_is_not_marked_as_safe_markup(self) -> None:
        """The real template must retain responsibility for escaping every stored name."""
        validated = review.HistoryScope.for_page("site-a", [{"site_name": "<script>name</script>"}])
        scope = HistoryCardScope(validated.site_id, validated.site_name)
        groups = [asdict(card) for card in (scope.runs, scope.operations, scope.audit)]
        assert {type(text) for group in groups for text in group.values()} == {str}

    def test_later_named_capture_supplies_the_existing_display_name(self) -> None:
        """Keep the existing first-available-name policy instead of adding a lookup."""
        validated = review.HistoryScope.for_page("site-a", [{}, {"site_name": "Selected Alpha"}])
        scope = HistoryCardScope(validated.site_id, validated.site_name)
        assert scope.site_name == "Selected Alpha"
        assert scope.runs.caption == "The single-site upgrade runs of Selected Alpha."
