"""Prove that secondary indexes do not change stored documents or import behavior."""

from copy import deepcopy
from typing import Any
from unittest.mock import patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as hypothesis_strategies

from src.foundation.persistence.db.arango_writer import IMPORT_BATCH_SIZE
from src.foundation.support.refactors.endpoint_primary_key_strategies import ENDPOINT_PRIMARY_KEY_STRATEGIES
from tests.unit.arango_indexes.fakes import ArangoIndexWriterHarness


class TestDocumentPreservation:
    """Retain existing primary keys, metadata, replacement imports, and values."""

    @pytest.mark.parametrize("api_name", ("listOrgSites", "searchOrgDeviceEvents", "getOrgLicensesSummary"))
    def test_primary_key_and_values_match_the_unchanged_write_contract(
        self, writer_harness: ArangoIndexWriterHarness, api_name: str
    ) -> None:
        """Compare the complete prepared document rather than only its field presence."""
        writer = writer_harness.writer()
        strategy = deepcopy(ENDPOINT_PRIMARY_KEY_STRATEGIES[api_name])
        record = {"id": "record-1", "device_id": "device-1", "timestamp": 7, "nested": {"enabled": True, "value": None}}
        original = deepcopy(record)
        with (
            patch("src.foundation.persistence.db.arango_writer.time.time", return_value=1770000000),
            patch("src.foundation.persistence.db.arango_writer.uuid.uuid4", return_value="summary-key"),
        ):
            result = writer.write([record], api_name, strategy)
        key = "summary-key" if strategy["type"] == "auto_increment_with_unique" else "record-1"
        expected = {**record, "_key": key, "_misthelper_updated_at": 1770000000, "_misthelper_deleted_at": None}
        collection = writer_harness.database.collections[api_name]
        assert collection.state.documents == {key: expected}
        assert collection.handle.import_bulk.call_args.kwargs == {"on_duplicate": "replace"}
        assert (result.success, result.records_written, result.records_failed, record) == (True, 1, 0, original)
        assert strategy == ENDPOINT_PRIMARY_KEY_STRATEGIES[api_name]

    def test_repeated_natural_key_updates_one_document(self, writer_harness: ArangoIndexWriterHarness) -> None:
        """Keep natural-key replacement and input isolation after index confirmation."""
        api_name = "listOrgMarvisActions"
        writer = writer_harness.writer()
        strategy = ENDPOINT_PRIMARY_KEY_STRATEGIES[api_name]
        first_record = {"uuid": "action-1", "status": "old", "details": {"value": 1}}
        second_record = {"uuid": "action-1", "status": "new", "details": {"value": 2}}
        original = deepcopy(second_record)
        first = writer.write([first_record], api_name, strategy)
        second = writer.write([second_record], api_name, strategy)
        documents = writer_harness.database.collections[api_name].state.documents
        assert (first.records_written, second.records_written, second.records_failed, tuple(documents)) == (
            1,
            1,
            0,
            ("action-1",),
        )
        assert (documents["action-1"]["status"], documents["action-1"]["details"], second_record) == (
            "new",
            {"value": 2},
            original,
        )

    def test_oversized_input_keeps_batch_boundaries_and_row_counts(
        self, writer_harness: ArangoIndexWriterHarness
    ) -> None:
        """Retain the existing batch size when an export spans two imports."""
        api_name = "listOrgMarvisActions"
        writer = writer_harness.writer()
        rows = [{"uuid": f"action-{number}", "status": "open"} for number in range(IMPORT_BATCH_SIZE + 1)]
        result = writer.write(rows, api_name, ENDPOINT_PRIMARY_KEY_STRATEGIES[api_name])
        collection = writer_harness.database.collections[api_name]
        assert [len(entry.args[0]) for entry in collection.handle.import_bulk.call_args_list] == [IMPORT_BATCH_SIZE, 1]
        assert [entry.kwargs for entry in collection.handle.import_bulk.call_args_list] == [
            {"on_duplicate": "replace"},
            {"on_duplicate": "replace"},
        ]
        assert (result.success, result.records_written, result.records_failed, len(collection.state.documents)) == (
            True,
            IMPORT_BATCH_SIZE + 1,
            0,
            IMPORT_BATCH_SIZE + 1,
        )
        assert collection.handle.add_index.call_count == len(ENDPOINT_PRIMARY_KEY_STRATEGIES[api_name]["indexes"])


class TestPayloadValues:
    """Retain arbitrary JSON values without normalizing them in the index path."""

    @settings(max_examples=30, deadline=None)
    @given(
        payload=hypothesis_strategies.recursive(
            hypothesis_strategies.one_of(
                hypothesis_strategies.none(),
                hypothesis_strategies.booleans(),
                hypothesis_strategies.integers(),
                hypothesis_strategies.floats(allow_nan=False, allow_infinity=False),
                hypothesis_strategies.text(max_size=80),
            ),
            lambda values: hypothesis_strategies.one_of(
                hypothesis_strategies.lists(values, max_size=5),
                hypothesis_strategies.dictionaries(hypothesis_strategies.text(max_size=12), values, max_size=5),
            ),
            max_leaves=10,
        )
    )
    def test_json_values_and_unicode_remain_unchanged(self, payload: Any) -> None:
        """Compare complete stored values and the original caller record."""
        harness = ArangoIndexWriterHarness()
        record = {"uuid": "action-1", "details": payload, "name": "\u00e9\u6771\U0001f680"}
        original = deepcopy(record)
        try:
            writer = harness.writer()
            result = writer.write(
                [record], "listOrgMarvisActions", ENDPOINT_PRIMARY_KEY_STRATEGIES["listOrgMarvisActions"]
            )
            stored = harness.database.collections["listOrgMarvisActions"].state.documents["action-1"]
            assert (stored["details"], stored["name"], record) == (payload, original["name"], original)
            assert (result.success, result.records_written, result.records_failed) == (True, 1, 0)
        finally:
            harness.close()
