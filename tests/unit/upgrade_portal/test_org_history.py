"""Unit tests for the multi-site section of the history page.

Why:
    Issue #3248. A multi-site upgrade had no history entry, so an operator who
    closed the progress page could not find the upgrade again. The shaper holds
    every rule of the new section. These tests call it with a plain reader, so
    no test needs Flask, a session, or a database.

    The owner key decides the link and never reaches the row. The tests prove
    both halves, because a key in the page would let a reader of the page copy
    the ownership proof of another operator.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from src.upgrade_portal.upgrade.org_history import (
    JOB_PAGE_PREFIX,
    NOT_RECORDED,
    OperationHistorySection,
    OrgOperationHistory,
)

_OWNER = "owner-key-of-this-session"  # WHY: The owner key of the browser session under test.
_OTHER = "owner-key-of-another-session"  # WHY: The owner key of a second operator.
_ORG = "org-0001"  # WHY: One organization owns every operation in this module.
_SITE_A = "site-aaaa"  # WHY: The first approved site of the operation.
_SITE_B = "site-bbbb"  # WHY: The second approved site of the operation.


def _moment(value: Any) -> str:
    """Return a short moment that a test can recognize.

    Args:
        value: The stored moment.

    Returns:
        The stored text with a marker, so a test proves that the rule ran.
    """
    return f"short:{value}"


def _record(**changes: Any) -> dict[str, Any]:
    """Return one stored operation row with every field filled.

    Args:
        changes: The fields that a test replaces.

    Returns:
        The row.
    """
    record: dict[str, Any] = {
        "operation_id": "org-run-0001",
        "org_id": _ORG,
        "site_ids": [_SITE_A, _SITE_B],
        "site_names": {_SITE_A: "Alpha Site", _SITE_B: "Beta Site"},
        "state": "running",
        "actor_email": "operator@example.test",
        "cloud_account": "noc@example.test",
        "created_at": "2026-09-24T01:02:03Z",
        "updated_at": "2026-09-24T01:05:00Z",
        "owner": _OWNER,
        "families": ["switch", "ap"],
    }
    record.update(changes)
    return record


@dataclass
class _Page:
    """A store page with the two fields that the shaper reads."""

    operations: tuple[Mapping[str, Any], ...]
    database_available: bool = True


@dataclass
class _Lister:
    """A store reader that records each call and answers one canned value."""

    answer: Any
    calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = field(default_factory=list)

    def __call__(self, *arguments: Any, **options: Any) -> Any:
        """Record the call and return the canned answer.

        Args:
            arguments: The positional arguments of the call.
            options: The keyword arguments of the call.

        Returns:
            The canned answer.
        """
        self.calls.append((arguments, options))
        return self.answer


def _history(owner_key: str = _OWNER) -> OrgOperationHistory:
    """Return the shaper for one browser session.

    Args:
        owner_key: The owner key of the session.

    Returns:
        The shaper.
    """
    return OrgOperationHistory(owner_key, _moment)


def test_the_owner_session_receives_the_progress_link() -> None:
    """The session that started the operation gets the link to its job page."""
    row = _history().row(_record())
    assert row["can_open"] is True
    assert row["progress_path"] == JOB_PAGE_PREFIX + "org-run-0001"


def test_another_session_receives_no_link() -> None:
    """The job page refuses another session, so the row offers no link to it."""
    row = _history(_OTHER).row(_record())
    assert row["can_open"] is False


def test_an_empty_owner_key_owns_no_operation() -> None:
    """An empty key never matches, even a record that holds an empty owner."""
    row = _history("").row(_record(owner=""))
    assert row["can_open"] is False


def test_the_row_holds_no_owner_key() -> None:
    """The owner key decides the link and never reaches the template."""
    row = _history().row(_record())
    assert "owner" not in row
    assert _OWNER not in [str(value) for value in row.values()]


def test_the_sites_follow_the_approved_order_and_fall_back_to_the_identifier() -> None:
    """The row keeps the approved site order and names a site with no stored name by its identifier."""
    record = _record(site_ids=[_SITE_B, _SITE_A], site_names={_SITE_A: "Alpha Site"})
    row = _history().row(record)
    assert row["sites_text"] == f"{_SITE_B}, Alpha Site"


def test_the_families_follow_the_fixed_order_and_keep_an_unknown_word() -> None:
    """The known families come first in the fixed order, then each unknown word."""
    row = _history().row(_record(families=["gateway", "zeta", "ap", "ssr", "switch", "ap"]))
    assert row["families_text"] == "Access points, Switches, Gateways, Session Smart Routers, zeta"


def test_a_missing_value_shows_the_plain_text() -> None:
    """A record of an older release shows "Not recorded" and the state "unknown"."""
    record = {"operation_id": "org-run-0002", "owner": _OWNER}
    row = _history().row(record)
    assert row["sites_text"] == NOT_RECORDED
    assert row["families_text"] == NOT_RECORDED
    assert row["actor_email"] == NOT_RECORDED
    assert row["cloud_account"] == NOT_RECORDED
    assert row["started_text"] == NOT_RECORDED
    assert row["updated_text"] == NOT_RECORDED
    assert row["started_raw"] == ""
    assert row["state"] == "unknown"


def test_the_moments_use_the_short_rule_and_keep_the_raw_value() -> None:
    """The row shows the short moment and keeps the stored moment for the hover text."""
    row = _history().row(_record())
    assert row["started_text"] == "short:2026-09-24T01:02:03Z"
    assert row["started_raw"] == "2026-09-24T01:02:03Z"
    assert row["updated_text"] == "short:2026-09-24T01:05:00Z"
    assert row["updated_raw"] == "2026-09-24T01:05:00Z"


def test_the_identifier_stays_inside_one_path_segment() -> None:
    """A slash inside a stored identifier cannot move the link to another path."""
    row = _history().row(_record(operation_id="a/b"))
    assert row["progress_path"] == JOB_PAGE_PREFIX + "a%2Fb"


def test_no_organization_reads_nothing() -> None:
    """With no organization, the section makes no store read and asks for an organization."""
    lister = _Lister(_Page((_record(),)))
    section = _history().section(lister, "", _SITE_A, 25)
    assert lister.calls == []
    assert section == OperationHistorySection((), False, True)


def test_the_section_forwards_the_organization_the_site_and_the_limit() -> None:
    """The section passes the page values to the store reader in the recorded shape."""
    lister = _Lister(_Page(()))
    _history().section(lister, _ORG, _SITE_A, 25)
    assert lister.calls == [((_ORG,), {"site_id": _SITE_A, "limit": 25})]


def test_the_section_reports_the_database_flag_of_the_page() -> None:
    """A page that states an outage makes the section state the outage too."""
    section = _history().section(_Lister(_Page((), database_available=False)), _ORG, "", 25)
    assert section.org_selected is True
    assert section.database_available is False
    assert section.rows == ()


def test_a_plain_list_answer_counts_as_available() -> None:
    """A stand-in that answers a list states no outage."""
    section = _history().section(_Lister([_record()]), _ORG, "", 25)
    assert section.database_available is True
    assert [row["operation_id"] for row in section.rows] == ["org-run-0001"]


def test_a_row_with_no_identifier_is_dropped() -> None:
    """A damaged row holds no key for its link, so the section drops it."""
    answer = _Page((_record(operation_id=""), _record(operation_id="org-run-0003")))
    section = _history().section(_Lister(answer), _ORG, "", 25)
    assert [row["operation_id"] for row in section.rows] == ["org-run-0003"]
