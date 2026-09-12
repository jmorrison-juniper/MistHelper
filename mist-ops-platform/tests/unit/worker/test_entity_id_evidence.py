"""Tests for the entity identifier fallback paths in the ops platform worker.

Why:
    Issue #2035 records that ``_resolve_entity_uuid`` and ``_extract_entity_id``
    turned an unparsable identifier into a fresh random UUID and recorded
    nothing. The caller prints that value as the identity of the device, so the
    one line that reports a failed push named a device that does not exist.

    Issue #1924 states the rule these tests hold: a failure path may recover,
    but it must leave a record. The tests in
    ``tests/unit/worker/sync/test_events_entity_id.py`` assert the return type
    alone, so they pass against a silent path. These tests assert the record.
"""

from __future__ import annotations

import logging
from uuid import UUID

import pytest

from src.worker.deploy.executor import _resolve_entity_uuid, _synthetic_entity_uuid
from src.worker.sync.events import EventSyncService

# WHY: a Mist MAC style object identifier, which the audit log does return.
MAC_STYLE_ID = "5c5b350e0001"

# WHY: a UUID with one extra character, which is the shape a truncation produces.
MALFORMED_UUID = "00000000-0000-0000-1000-209339051780x"

# WHY: a well formed value, so a test can prove the normal path stays silent.
VALID_UUID = "12345678-1234-5678-1234-567812345678"


class TestResolveEntityUuidLeavesARecord:
    """Cover the deploy executor fallback that named a phantom device."""

    def test_a_malformed_value_warns_and_names_the_value(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A value that is not a UUID must produce a warning that quotes it."""
        # WHY: the operator searches the log for the identifier they submitted.
        with caplog.at_level(logging.WARNING):
            result = _resolve_entity_uuid({"device_id": MALFORMED_UUID})
        assert isinstance(result, UUID)  # WHY: the caller stores this in a UUID field.
        assert MALFORMED_UUID in caplog.text  # WHY: the raw value is the evidence.
        assert "device_id" in caplog.text  # WHY: the key states which field failed.

    def test_a_malformed_value_warns_that_the_identifier_is_synthetic(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """The reader must learn that the returned identifier is not real."""
        # WHY: without this line the reader trusts a fabricated device identity.
        with caplog.at_level(logging.WARNING):
            result = _resolve_entity_uuid({"device_id": MALFORMED_UUID})
        assert "synthetic" in caplog.text  # WHY: the word states the value is invented.
        assert str(result) in caplog.text  # WHY: the log ties the row to the returned value.

    def test_an_empty_dict_warns(self, caplog: pytest.LogCaptureFixture) -> None:
        """No identifier at all must still leave a record."""
        # WHY: an empty dict reached the same silent return before issue #2035.
        with caplog.at_level(logging.WARNING):
            result = _resolve_entity_uuid({})
        assert isinstance(result, UUID)  # WHY: the recovery behavior must not change.
        assert caplog.records  # WHY: the path must not stay silent.

    def test_a_valid_value_stays_silent(self, caplog: pytest.LogCaptureFixture) -> None:
        """The normal path must not add noise to the log."""
        # WHY: issue #1766 records that noise dilutes the signal, so silence matters here.
        with caplog.at_level(logging.WARNING):
            result = _resolve_entity_uuid({"device_id": VALID_UUID})
        assert result == UUID(VALID_UUID)  # WHY: a real identifier must pass through.
        assert not caplog.records  # WHY: a success needs no warning.

    def test_a_later_key_still_supplies_the_identifier(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A malformed first key must not hide a good later key."""
        # WHY: the loop continues, so the real site identifier must still win.
        ids = {"device_id": MALFORMED_UUID, "site_id": VALID_UUID}
        with caplog.at_level(logging.WARNING):
            result = _resolve_entity_uuid(ids)
        assert result == UUID(VALID_UUID)  # WHY: the specific key failed, the general one held.
        assert MALFORMED_UUID in caplog.text  # WHY: the rejected value still needs a record.

    def test_each_synthetic_value_is_new(self) -> None:
        """Two fallback calls must not share one identifier."""
        # WHY: a shared value would collide on a primary key.
        assert _synthetic_entity_uuid([]) != _synthetic_entity_uuid([])


class TestExtractEntityIdLeavesARecord:
    """Cover the audit sync fallback that broke the link to the entity."""

    @pytest.mark.parametrize(
        "raw",
        [MAC_STYLE_ID, MALFORMED_UUID, "not-a-uuid"],
    )
    def test_an_unparsable_identifier_warns_and_names_the_value(
        self,
        raw: str,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """An audit event identifier that is not a UUID must be reported."""
        # WHY: the audit row is the record read after a change causes an outage.
        with caplog.at_level(logging.WARNING):
            result = EventSyncService._extract_entity_id({"obj_id": raw})
        assert isinstance(result, UUID)  # WHY: the column type must not change.
        assert raw in caplog.text  # WHY: the reader needs the value that failed.

    def test_a_missing_identifier_warns(self, caplog: pytest.LogCaptureFixture) -> None:
        """An event with no identifier must leave a record too."""
        # WHY: a row that points at nothing is worse than a missing row.
        with caplog.at_level(logging.WARNING):
            result = EventSyncService._extract_entity_id({})
        assert isinstance(result, UUID)  # WHY: the recovery behavior must not change.
        assert "no identifier" in caplog.text  # WHY: the reason states which path ran.

    def test_the_warning_states_the_link_is_lost(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """The message must name the consequence, not only the cause."""
        # WHY: a junior engineer needs the impact stated, not inferred.
        with caplog.at_level(logging.WARNING):
            EventSyncService._extract_entity_id({"obj_id": MAC_STYLE_ID})
        assert "loses its link" in caplog.text  # WHY: this is the operational impact.

    def test_a_valid_identifier_stays_silent(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """The normal path must not add noise to the log."""
        # WHY: every audit event runs this path, so a warning here would flood the log.
        with caplog.at_level(logging.WARNING):
            result = EventSyncService._extract_entity_id({"obj_id": VALID_UUID})
        assert result == UUID(VALID_UUID)  # WHY: a real identifier must pass through.
        assert not caplog.records  # WHY: a success needs no warning.
