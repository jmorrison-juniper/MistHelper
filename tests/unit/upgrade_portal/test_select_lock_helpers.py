"""Unit tests for the lock helpers and the page readers of the selection routes.

Why:
    Issue #1996 reports that ``app/routes/select.py`` sits at 86 percent, under
    the 90 percent floor that the aggregate hides. The live run of 2026-08-24
    found six defects, and two of them lived in this module on the inventory
    path. The uncovered half of a module is where a defect survives.

    The blocks below are the ones a page render reaches when something else is
    already broken: a lock store that does not answer, a session layer that
    raises, a malformed address in the lock store, and a device module that is
    not built. Each one must let the page render rather than raise, because a
    page that raises here shows an operator nothing at all.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from src.upgrade_portal.app.routes import select

ORG_ID = "8a1ea872-241a-4c8e-a5ca-2d85674c7229"
SITE_ID = "cf36153a-97bb-4974-8f8f-e9cc25d64d83"

HOLDER = "other.operator@example.invalid"
SAME_PERSON = "the.same.operator@example.invalid"

NO_WAIT = 0  # The value the banner reads as "no cooldown to show".


def explode(*args: Any, **kwargs: Any) -> Any:
    """Raise the way a dead store or a broken session layer does.

    Args:
        args: Ignored.
        kwargs: Ignored.

    Raises:
        RuntimeError: Always.
    """
    raise RuntimeError("the store did not answer")


class TestLockCooldownSeconds:
    """Tests for the number that the lock banner counts down."""

    def test_answers_zero_when_the_lock_store_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A page render survives a store that answers nothing.

        Why:
            The lock contract states that a read never needs the lock store. A
            wait the portal cannot measure reads as no wait at all, which hides
            the cooldown line rather than showing a wrong number.

        Args:
            monkeypatch: The pytest patch helper.
        """
        monkeypatch.setattr(select.lock, "read_lock", explode)
        monkeypatch.setattr(select, "lock_client", lambda: None)
        assert select.lock_cooldown_seconds(ORG_ID, SITE_ID) == NO_WAIT

    def test_answers_zero_for_a_free_site(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """No holder means no operator waits for anything.

        Args:
            monkeypatch: The pytest patch helper.
        """
        monkeypatch.setattr(select.lock, "read_lock", lambda org, site, client=None: None)
        monkeypatch.setattr(select, "lock_client", lambda: None)
        assert select.lock_cooldown_seconds(ORG_ID, SITE_ID) == NO_WAIT

    def test_answers_the_seconds_that_remain(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A held site counts the cooldown down from its own age.

        Args:
            monkeypatch: The pytest patch helper.
        """
        held = SimpleNamespace(age_seconds=lambda: 60.0, owner=SimpleNamespace(actor_email=HOLDER))
        monkeypatch.setattr(select.lock, "read_lock", lambda org, site, client=None: held)
        monkeypatch.setattr(select, "lock_client", lambda: None)
        assert select.lock_cooldown_seconds(ORG_ID, SITE_ID) == select.lock.COOLDOWN_SECONDS - 60

    def test_never_answers_below_zero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A lock older than the cooldown reads as no wait, never as a negative.

        Why:
            The banner prints this number into a sentence. A negative would read
            as a wait that runs backwards.

        Args:
            monkeypatch: The pytest patch helper.
        """
        old = select.lock.COOLDOWN_SECONDS + 100
        held = SimpleNamespace(age_seconds=lambda: float(old), owner=SimpleNamespace(actor_email=HOLDER))
        monkeypatch.setattr(select.lock, "read_lock", lambda org, site, client=None: held)
        monkeypatch.setattr(select, "lock_client", lambda: None)
        assert select.lock_cooldown_seconds(ORG_ID, SITE_ID) == NO_WAIT


class TestTakeoverWord:
    """Tests for the word that a takeover of one site needs first."""

    def test_asks_for_the_takeover_word_when_the_session_layer_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A fault of the session layer proves no match, so the stricter word stands.

        Why:
            FR-079 fixes the takeover word for every operator that is not the
            holder. An unknown operator must never get the lighter word, because
            a takeover erases the in-flight data of the operator that left.

        Args:
            monkeypatch: The pytest patch helper.
        """
        monkeypatch.setattr(select.identity, "current_owner", explode)
        assert select.takeover_word(HOLDER) == select.lock.TAKEOVER_CONFIRMATION_TEXT

    def test_asks_for_the_takeover_word_with_no_signed_session(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An empty address matches no holder.

        Args:
            monkeypatch: The pytest patch helper.
        """
        monkeypatch.setattr(select.identity, "current_owner", lambda: None)
        assert select.takeover_word(HOLDER) == select.lock.TAKEOVER_CONFIRMATION_TEXT

    def test_asks_for_the_takeover_word_when_the_site_names_no_holder(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """One empty half cannot prove that the two operators are one person.

        Args:
            monkeypatch: The pytest patch helper.
        """
        owner = SimpleNamespace(actor_email=SAME_PERSON)
        monkeypatch.setattr(select.identity, "current_owner", lambda: owner)
        assert select.takeover_word("") == select.lock.TAKEOVER_CONFIRMATION_TEXT

    def test_asks_for_the_takeover_word_for_a_malformed_holder(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A malformed address in the lock store proves no match.

        Why:
            The lock store may hold an address that the current rules refuse.
            The stricter word stands, because the portal cannot show that the
            two operators are one person.

        Args:
            monkeypatch: The pytest patch helper.
        """
        owner = SimpleNamespace(actor_email=SAME_PERSON)
        monkeypatch.setattr(select.identity, "current_owner", lambda: owner)
        monkeypatch.setattr(select.identity, "normalize_email", _refuse_second(SAME_PERSON))
        assert select.takeover_word("not-an-address") == select.lock.TAKEOVER_CONFIRMATION_TEXT

    def test_asks_for_the_resume_word_for_the_same_operator(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The operator who returns to a quiet session of their own types the lighter word.

        Why:
            FR-080 asks for the resume word in that one case. A takeover erases
            nothing when the operator is the same person.

        Args:
            monkeypatch: The pytest patch helper.
        """
        owner = SimpleNamespace(actor_email=SAME_PERSON.upper())
        monkeypatch.setattr(select.identity, "current_owner", lambda: owner)
        monkeypatch.setattr(select.identity, "normalize_email", lambda value: str(value).casefold())
        assert select.takeover_word(SAME_PERSON) == select.lock.RESUME_CONFIRMATION_TEXT

    def test_asks_for_the_takeover_word_for_a_different_operator(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Two different addresses read as two different people.

        Args:
            monkeypatch: The pytest patch helper.
        """
        owner = SimpleNamespace(actor_email=SAME_PERSON)
        monkeypatch.setattr(select.identity, "current_owner", lambda: owner)
        monkeypatch.setattr(select.identity, "normalize_email", lambda value: str(value).casefold())
        assert select.takeover_word(HOLDER) == select.lock.TAKEOVER_CONFIRMATION_TEXT


def _refuse_second(good: str) -> Any:
    """Return a normalizer that accepts one address and refuses every other.

    Why:
        The malformed case needs the first call to work and the second to raise,
        because the function reads the operator address before the holder.

    Args:
        good: The one address that the normalizer accepts.

    Returns:
        One normalizer callable.
    """

    def normalize(value: str) -> str:
        """Answer the folded address, or refuse.

        Args:
            value: The address to normalize.

        Returns:
            The folded address.

        Raises:
            ValueError: When the address is not the accepted one.
        """
        if str(value).casefold() != good.casefold():
            raise ValueError("the address is malformed")
        return str(value).casefold()

    return normalize


class TestInventoryPageValues:
    """Tests for the reader that fills the inventory page."""

    def test_renders_an_empty_table_while_the_device_module_is_absent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A missing device module still renders the page.

        Why:
            The page shows its own fallback for a missing count. A raise here
            would take the whole inventory page down on a host that is still
            building.

        Args:
            monkeypatch: The pytest patch helper.
        """
        monkeypatch.setattr(select, "read_inventory", lambda org_id, site_id: None)
        assert select.inventory_parts(ORG_ID, SITE_ID) == ([], {})

    def test_answers_the_devices_and_the_counts(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The page reads both halves by name.

        Args:
            monkeypatch: The pytest patch helper.
        """
        answer = {"devices": [{"mac": "abc"}], "counts": {"devices_total": 1}}
        monkeypatch.setattr(select, "read_inventory", lambda org_id, site_id: answer)
        assert select.inventory_parts(ORG_ID, SITE_ID) == ([{"mac": "abc"}], {"devices_total": 1})


class TestCapturePageUrl:
    """Tests for the forward step out of the inventory page."""

    def test_carries_the_site_as_a_query_argument(self) -> None:
        """The capture page names no site of its own until a capture exists."""
        assert select.capture_page_url(SITE_ID).endswith(f"={SITE_ID}")

    def test_escapes_a_site_identifier_that_holds_a_separator(self) -> None:
        """A value from the cloud still passes through the escape.

        Why:
            The address goes into the markup of a link. An unescaped separator
            would end the argument early and send the operator to another site.
        """
        built = select.capture_page_url("a&b=c")
        assert "a&b=c" not in built
        assert "a%26b%3Dc" in built


class TestInventoryFirmwareTargets:
    """Tests for the firmware target state that the inventory page shows."""

    def test_adds_a_model_target_and_mismatch_state(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The table uses the shared model fallback and marks only a mismatch."""
        devices = [
            {"mac": "aa:aa:aa:aa:aa:01", "type": "ap", "model": "AP45", "version": "0.14.8"},
            {"mac": "aa:aa:aa:aa:aa:02", "type": "switch", "model": "EX4400", "version": "24.2R1.17"},
            {"mac": "aa:aa:aa:aa:aa:03", "type": "gateway", "model": "SSR120", "version": ""},
        ]
        session = SimpleNamespace(cloud_session=object())
        calls: list[tuple[Any, str, list[dict[str, Any]], str]] = []

        def read_versions(
            cloud_session: Any, site_id: str, rows: list[dict[str, Any]], org_id: str
        ) -> dict[str, tuple[str, ...]]:
            calls.append((cloud_session, site_id, rows, org_id))
            return {
                "AP45": ("0.14.9", "0.14.8"),
                "EX4400": ("24.2R1.17",),
                "SSR120": (),
            }

        monkeypatch.setattr(select.identity, "current_session", lambda: session)
        monkeypatch.setattr(select, "read_model_versions", read_versions)
        rows = select.inventory_rows_with_targets(ORG_ID, SITE_ID, devices)

        assert calls == [(session.cloud_session, SITE_ID, devices, ORG_ID)]
        assert rows[0]["version_target"] == "0.14.9"
        assert rows[0]["firmware_mismatch"] is True
        assert rows[1]["version_target"] == "24.2R1.17"
        assert rows[1]["firmware_mismatch"] is False
        assert rows[2]["version_target"] == ""
        assert rows[2]["firmware_mismatch"] is False
