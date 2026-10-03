"""Prove declared field requests through the actual writer path."""

from copy import deepcopy
from unittest.mock import call

import pytest

from src.refactors.endpoint_primary_key_strategies import ENDPOINT_PRIMARY_KEY_STRATEGIES
from tests.unit.arango_indexes.fakes import ArangoIndexWriterHarness

INDEX_APIS = (
    "listOrgSites",
    "getOrgInventory",
    "searchOrgDeviceEvents",
    "listOrgMarvisActions",
    "getOrgLicensesSummary",
)


class TestDeclaredFields:
    """Check new collections, existing collections, and repeated writes."""

    @pytest.mark.parametrize("api_name", INDEX_APIS)
    @pytest.mark.parametrize("existing_collection", (False, True))
    def test_each_real_strategy_field_before_import(
        self, writer_harness: ArangoIndexWriterHarness, api_name: str, existing_collection: bool
    ) -> None:
        """Create exactly the declared indexes before importing one record."""
        writer = writer_harness.writer()
        strategy = deepcopy(ENDPOINT_PRIMARY_KEY_STRATEGIES[api_name])
        if existing_collection:
            writer_harness.database.create_collection(api_name)
        record = {"id": "record-1", "uuid": "action-1", "device_id": "device-1", "timestamp": 7}
        first = writer.write([record], api_name, strategy)
        collection = writer_harness.database.collections[api_name]
        expected = [{"type": "persistent", "fields": [name]} for name in strategy["indexes"]]
        assert collection.handle.add_index.call_args_list == [call(definition) for definition in expected]
        assert collection.state.actions[: len(expected)] == [("index", definition) for definition in expected]
        second = writer.write([record], api_name, strategy)
        assert collection.handle.add_index.call_args_list == [call(definition) for definition in expected]
        assert (first.success, first.records_written, second.success, second.records_written) == (True, 1, True, 1)
        assert tuple(collection.state.indexes) == tuple(strategy["indexes"])
        assert strategy == ENDPOINT_PRIMARY_KEY_STRATEGIES[api_name]

    def test_existing_equal_index_is_reused(self, writer_harness: ArangoIndexWriterHarness) -> None:
        """Request an equal index without replacing its server identity."""
        api_name = "listOrgMarvisActions"
        writer_harness.database.create_collection(api_name)
        collection = writer_harness.database.collections[api_name]
        definition = {"type": "persistent", "fields": ["org_id"]}
        original = collection.add_index(definition)
        collection.state.actions.clear()
        writer = writer_harness.writer()
        result = writer.write([{"uuid": "action-1"}], api_name, ENDPOINT_PRIMARY_KEY_STRATEGIES[api_name])
        assert (result.success, result.records_written, collection.state.indexes["org_id"]["id"]) == (
            True,
            1,
            original["id"],
        )
        assert collection.handle.add_index.call_args_list == [
            call({"type": "persistent", "fields": [name]})
            for name in ENDPOINT_PRIMARY_KEY_STRATEGIES[api_name]["indexes"]
        ]
        assert len(collection.state.indexes) == len(ENDPOINT_PRIMARY_KEY_STRATEGIES[api_name]["indexes"])

    def test_empty_records_still_ensure_declared_indexes(self, writer_harness: ArangoIndexWriterHarness) -> None:
        """Open an empty collection without skipping its required indexes."""
        api_name = "listOrgMarvisActions"
        writer = writer_harness.writer()
        strategy = ENDPOINT_PRIMARY_KEY_STRATEGIES[api_name]
        result = writer.write([], api_name, strategy)
        collection = writer_harness.database.collections[api_name]
        assert collection.handle.add_index.call_args_list == [
            call({"type": "persistent", "fields": [name]}) for name in strategy["indexes"]
        ]
        assert collection.handle.import_bulk.call_args_list == []
        assert (result.success, result.records_written, result.records_failed) == (True, 0, 0)


class TestDeclarationChanges:
    """Keep confirmed fields separate from the current declaration order."""

    def test_duplicates_and_reordering_do_not_repeat_requests(self, writer_harness: ArangoIndexWriterHarness) -> None:
        """Preserve the first field order without requesting duplicates."""
        writer = writer_harness.writer()
        strategy = deepcopy(ENDPOINT_PRIMARY_KEY_STRATEGIES["listOrgSites"])
        strategy["indexes"] = ["name", "org_id", "name", "org_id"]
        writer.write([], "listOrgSites", strategy)
        strategy["indexes"] = ["org_id", "name"]
        writer.write([], "listOrgSites", strategy)
        collection = writer_harness.database.collections["listOrgSites"]
        assert collection.handle.add_index.call_args_list == [
            call({"type": "persistent", "fields": ["name"]}),
            call({"type": "persistent", "fields": ["org_id"]}),
        ]
        assert tuple(collection.state.indexes) == ("name", "org_id")

    def test_strategy_extension_checks_only_new_fields(self, writer_harness: ArangoIndexWriterHarness) -> None:
        """Check added fields without removing previously confirmed indexes."""
        writer = writer_harness.writer()
        strategy = deepcopy(ENDPOINT_PRIMARY_KEY_STRATEGIES["listOrgSites"])
        complete_fields = list(strategy["indexes"])
        strategy["indexes"] = complete_fields[:2]
        writer.write([], "listOrgSites", strategy)
        strategy["indexes"] = complete_fields
        writer.write([], "listOrgSites", strategy)
        strategy["indexes"] = complete_fields[:1]
        writer.write([], "listOrgSites", strategy)
        collection = writer_harness.database.collections["listOrgSites"]
        assert collection.handle.add_index.call_args_list == [
            call({"type": "persistent", "fields": [name]}) for name in complete_fields
        ]
        assert tuple(collection.state.indexes) == tuple(complete_fields)

    def test_same_field_in_another_collection_is_checked(self, writer_harness: ArangoIndexWriterHarness) -> None:
        """Do not let one collection confirm another collection's fields."""
        writer = writer_harness.writer()
        for api_name in ("listOrgSites", "getOrgInventory"):
            writer.write([], api_name, ENDPOINT_PRIMARY_KEY_STRATEGIES[api_name])
        requests = {
            name: collection.handle.add_index.call_args_list
            for name, collection in writer_harness.database.collections.items()
        }
        assert requests == {
            name: [
                call({"type": "persistent", "fields": [field]})
                for field in ENDPOINT_PRIMARY_KEY_STRATEGIES[name]["indexes"]
            ]
            for name in ("listOrgSites", "getOrgInventory")
        }


class TestEmptyAndInvalidDeclarations:
    """Distinguish an absent declaration from invalid configured fields."""

    @pytest.mark.parametrize("declared_indexes", ([], ()))
    def test_empty_index_list_keeps_existing_write_result(
        self, writer_harness: ArangoIndexWriterHarness, declared_indexes: object
    ) -> None:
        """Import normally when the declaration contains no field."""
        writer = writer_harness.writer()
        strategy = deepcopy(ENDPOINT_PRIMARY_KEY_STRATEGIES["listOrgMarvisActions"])
        strategy["indexes"] = declared_indexes
        result = writer.write([{"uuid": "action-1"}], "listOrgMarvisActions", strategy)
        collection = writer_harness.database.collections["listOrgMarvisActions"]
        assert collection.handle.add_index.call_args_list == []
        assert (result.success, result.records_written, result.records_failed) == (True, 1, 0)

    def test_missing_index_list_creates_no_secondary_index(self, writer_harness: ArangoIndexWriterHarness) -> None:
        """Keep the established behavior for a strategy without indexes."""
        writer = writer_harness.writer()
        strategy = deepcopy(ENDPOINT_PRIMARY_KEY_STRATEGIES["listOrgMarvisActions"])
        strategy.pop("indexes")
        result = writer.write([{"uuid": "action-1"}], "listOrgMarvisActions", strategy)
        collection = writer_harness.database.collections["listOrgMarvisActions"]
        assert collection.handle.add_index.call_args_list == []
        assert (result.success, result.records_written, result.records_failed) == (True, 1, 0)

    @pytest.mark.parametrize(
        "invalid_indexes", (None, "org_id", {"field": "org_id"}, [""], [" "], [1], [None], [["org_id"]])
    )
    def test_invalid_declaration_fails_before_database_mutations(
        self, writer_harness: ArangoIndexWriterHarness, invalid_indexes: object
    ) -> None:
        """Reject invalid fields without creating a collection or importing data."""
        writer = writer_harness.writer()
        strategy = deepcopy(ENDPOINT_PRIMARY_KEY_STRATEGIES["listOrgMarvisActions"])
        strategy["indexes"] = invalid_indexes
        with pytest.raises(ValueError, match="ArangoDB index"):
            writer.write([{"uuid": "action-1"}], "listOrgMarvisActions", strategy)
        assert writer_harness.database.handle.create_collection.call_args_list == []
        assert writer_harness.database.collections == {}
