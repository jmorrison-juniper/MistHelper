"""Wave 3 top-up tests for VersionPerModelFetcher (initiative 1018).

Targets the uncovered branches in
``src/inventory/inventory_summary/version_per_model_fetcher.py``. All
network calls into ``_parent.OrgDeviceInventorySummaryCore`` are
monkeypatched so the fetcher executes in-process with no live API.

Design notes:

* No source edits, no new suppressions -- test-only wave.
* All parent-module hooks are patched via ``monkeypatch`` so the
  bindings roll back cleanly after each test.
* The tests target orchestration paths (fetch, expand, bulk-append,
  sort key) plus every leaf helper (_ap_rows, _unassigned_rows,
  _switch_rows via _accumulate_switch_versions, _gateway_rows,
  _prefetch_switches, _prefetch_gateways) including their
  exception-swallow branches.
"""

from __future__ import annotations  # WHY: PEP 604 unions across the module.

import pytest  # WHY: monkeypatch fixture + parametrize for exception branches.

# WHY: SUT + parent module used to intercept the internal inventory-fetch calls.
from src.inventory import org_device_inventory_summary as _parent
from src.inventory.inventory_summary.version_per_model_fetcher import (
    VersionPerModelFetcher,
)

_ORG_ID = "org-under-test"  # WHY: literal used across all tests; value is irrelevant.


# ---------------------------------------------------------------------------
# _sort_row_key
# ---------------------------------------------------------------------------
class TestSortRowKey:
    """Cover the tuple assembly and its negative-count ordering."""

    def test_returns_expected_tuple(self) -> None:
        """The three-tuple must be (device_type, model, -count) with count coerced from string."""
        row = {"device_type": "switch", "model": "EX4300", "count": "5"}  # WHY: count string forces int() cast.
        assert VersionPerModelFetcher._sort_row_key(row) == ("switch", "EX4300", -5)  # WHY: exact tuple check.

    def test_defaults_when_keys_missing(self) -> None:
        """Missing keys must default to empty strings and zero count."""
        assert VersionPerModelFetcher._sort_row_key({}) == ("", "", 0)  # WHY: proves .get defaults are honoured.


# ---------------------------------------------------------------------------
# _accumulate_switch_versions
# ---------------------------------------------------------------------------
class TestAccumulateSwitchVersions:
    """Cover the VC-aware version accumulator, including the model filter and num_members default."""

    def test_filters_by_model_and_sums_num_members(self) -> None:
        """Records for the requested model must fold into version->sum(num_members)."""
        records: list[dict[str, object]] = (
            [  # WHY: mix of matching/non-matching records exercises the ``continue`` filter branch.
                {"model": "EX4300", "version": "22.4", "num_members": 4},  # kept + VC stack of 4.
                {"model": "EX4300", "version": "22.4", "num_members": 2},  # kept + folded into same bucket.
                {"model": "EX2300", "version": "22.4", "num_members": 1},  # dropped by model filter.
                {"model": "EX4300"},  # kept, version defaults to "unknown", num_members defaults to 1.
            ]
        )
        result = VersionPerModelFetcher._accumulate_switch_versions("EX4300", records)  # WHY: exercise fold.
        assert result == {"22.4": 6, "unknown": 1}  # WHY: 4+2 folded; missing fields default correctly.


# ---------------------------------------------------------------------------
# _switch_rows + _gateway_rows
# ---------------------------------------------------------------------------
class TestSwitchAndGatewayRows:
    """Cover the two per-type row builders."""

    def test_switch_rows_emits_one_row_per_version_bucket(self) -> None:
        """The switch row builder returns one dict per accumulated version bucket."""
        records = [  # WHY: three records, two distinct version buckets.
            {"model": "EX4300", "version": "22.4", "num_members": 2},
            {"model": "EX4300", "version": "22.4", "num_members": 1},
            {"model": "EX4300", "version": "23.2", "num_members": 1},
        ]
        rows = VersionPerModelFetcher._switch_rows("EX4300", records)  # WHY: exercise materialize path.
        by_version = {row["version"]: row["count"] for row in rows}  # WHY: order-agnostic assertion.
        assert by_version == {"22.4": 3, "23.2": 1}  # WHY: verifies num_members-aware fold shape.
        assert all(row["device_type"] == "switch" and row["model"] == "EX4300" for row in rows)  # WHY: shape.

    def test_gateway_rows_counts_one_per_record(self) -> None:
        """Gateway rows count exactly one per matching record (no num_members multiplier)."""
        records = [  # WHY: proves num_members is NOT applied on gateway branch.
            {"model": "SRX300", "version": "23.2"},
            {"model": "SRX300", "version": "23.2"},
            {"model": "SRX345", "version": "23.2"},  # dropped by model filter.
            {"model": "SRX300"},  # version defaults to "unknown".
        ]
        rows = VersionPerModelFetcher._gateway_rows("SRX300", records)  # WHY: exercise gateway materialize.
        by_version = {row["version"]: row["count"] for row in rows}  # WHY: order-agnostic assertion.
        assert by_version == {"23.2": 2, "unknown": 1}  # WHY: one-per-record fold, model filter honoured.
        assert all(row["device_type"] == "gateway" for row in rows)  # WHY: device_type must be gateway.

    def test_switch_rows_empty_when_no_matching_model(self) -> None:
        """A model with no records yields an empty list, not an error."""
        assert VersionPerModelFetcher._switch_rows("EX4300", [{"model": "SRX"}]) == []  # WHY: filter-out.

    def test_gateway_rows_empty_when_no_matching_model(self) -> None:
        """Same guarantee on the gateway builder."""
        assert VersionPerModelFetcher._gateway_rows("SRX300", [{"model": "EX"}]) == []  # WHY: filter-out.


# ---------------------------------------------------------------------------
# _rows_for_model
# ---------------------------------------------------------------------------
class TestRowsForModel:
    """Cover the per-row dispatcher including the blank-model and unknown-type branches."""

    def test_blank_model_returns_empty_list(self) -> None:
        """Rows with an empty model name are skipped before any dispatch."""
        result = VersionPerModelFetcher._rows_for_model({"device_type": "switch"}, [], [])  # WHY: blank.
        assert result == []  # WHY: no output emitted for blank-model rows.

    def test_ap_device_type_returns_empty_list(self) -> None:
        """AP device type falls through to the trailing return."""
        row = {"device_type": "ap", "model": "AP45"}  # WHY: AP dispatch is handled in bulk elsewhere.
        assert VersionPerModelFetcher._rows_for_model(row, [], []) == []  # WHY: dispatcher skips.

    def test_switch_dispatch_returns_switch_rows(self) -> None:
        """The switch branch produces per-model rows via the switch helper."""
        row = {"device_type": "switch", "model": "EX4300"}  # WHY: minimal model row.
        switch_records = [{"model": "EX4300", "version": "22.4", "num_members": 1}]  # WHY: one matching record.
        rows = VersionPerModelFetcher._rows_for_model(row, switch_records, [])  # WHY: dispatch.
        assert len(rows) == 1 and rows[0]["device_type"] == "switch"  # WHY: dispatch reached _switch_rows.

    def test_gateway_dispatch_returns_gateway_rows(self) -> None:
        """The gateway branch produces per-model rows via the gateway helper."""
        row = {"device_type": "gateway", "model": "SRX300"}  # WHY: minimal model row.
        gateway_records = [{"model": "SRX300", "version": "23.2"}]  # WHY: one matching record.
        rows = VersionPerModelFetcher._rows_for_model(row, [], gateway_records)  # WHY: dispatch.
        assert len(rows) == 1 and rows[0]["device_type"] == "gateway"  # WHY: dispatch reached _gateway_rows.

    def test_unknown_device_type_returns_empty_list(self) -> None:
        """An unrecognized device_type hits the trailing return."""
        row = {"device_type": "mystery", "model": "X"}  # WHY: forces final ``return []`` line.
        assert VersionPerModelFetcher._rows_for_model(row, [], []) == []  # WHY: no dispatch match.


# ---------------------------------------------------------------------------
# _prefetch_switches / _prefetch_gateways
# ---------------------------------------------------------------------------
class TestPrefetchSwitches:
    """Cover the switch prefetch: skip, success, and exception-swallow branches."""

    def test_skips_when_no_switch_models(self) -> None:
        """When model_rows has no switches, no API call is issued and result is empty."""
        result = VersionPerModelFetcher._prefetch_switches(  # WHY: exercise the ``if not any`` short-circuit.
            _ORG_ID, [{"device_type": "gateway", "model": "SRX"}]
        )
        assert result == []  # WHY: proves no fetch attempted.

    def test_returns_fetched_records(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Success path returns the parent fetcher's records verbatim."""
        expected = [{"model": "EX4300", "version": "22.4"}]  # WHY: sentinel list identity checked below.
        monkeypatch.setattr(  # WHY: patch the parent fetcher on the shared parent module.
            _parent.OrgDeviceInventorySummaryCore,
            "_fetch_switch_physical_inventory",
            staticmethod(lambda org_id: expected),
        )
        result = VersionPerModelFetcher._prefetch_switches(_ORG_ID, [{"device_type": "switch", "model": "EX"}])
        assert result is expected  # WHY: identity check proves no wrapping/copying by the SUT.

    def test_swallows_exception_and_returns_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Fetch errors are logged + swallowed; the fetcher returns an empty list."""

        def boom(_org_id: str) -> list[dict]:
            """Raise to exercise the ``except Exception`` branch of _prefetch_switches."""
            raise RuntimeError("boom-switch")  # WHY: any exception must trigger the swallow.

        monkeypatch.setattr(  # WHY: patch parent fetcher to raise.
            _parent.OrgDeviceInventorySummaryCore,
            "_fetch_switch_physical_inventory",
            staticmethod(boom),
        )
        result = VersionPerModelFetcher._prefetch_switches(_ORG_ID, [{"device_type": "switch", "model": "EX"}])
        assert result == []  # WHY: swallow returns an empty list for graceful degradation.


class TestPrefetchGateways:
    """Cover the gateway prefetch: skip, success, and exception-swallow branches."""

    def test_skips_when_no_gateway_models(self) -> None:
        """No gateway rows -> no API call, empty return."""
        result = VersionPerModelFetcher._prefetch_gateways(_ORG_ID, [{"device_type": "switch", "model": "EX"}])
        assert result == []  # WHY: proves the ``if not any`` short-circuit fires.

    def test_returns_fetched_records(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Success path returns the parent fetcher's records verbatim."""
        expected = [{"model": "SRX300", "version": "23.2"}]  # WHY: sentinel list identity checked below.
        monkeypatch.setattr(
            _parent.OrgDeviceInventorySummaryCore,
            "_fetch_gateway_physical_inventory",
            staticmethod(lambda org_id: expected),
        )
        result = VersionPerModelFetcher._prefetch_gateways(_ORG_ID, [{"device_type": "gateway", "model": "SRX"}])
        assert result is expected  # WHY: identity check proves no wrapping/copying by the SUT.

    def test_swallows_exception_and_returns_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Fetch errors are logged + swallowed; the fetcher returns an empty list."""

        def boom(_org_id: str) -> list[dict]:
            """Raise to exercise the ``except Exception`` branch of _prefetch_gateways."""
            raise RuntimeError("boom-gw")  # WHY: any exception must trigger the swallow.

        monkeypatch.setattr(
            _parent.OrgDeviceInventorySummaryCore,
            "_fetch_gateway_physical_inventory",
            staticmethod(boom),
        )
        result = VersionPerModelFetcher._prefetch_gateways(_ORG_ID, [{"device_type": "gateway", "model": "SRX"}])
        assert result == []  # WHY: swallow returns an empty list for graceful degradation.


# ---------------------------------------------------------------------------
# _ap_rows (with and without ap_records fallback)
# ---------------------------------------------------------------------------
class TestApRows:
    """Cover the AP bulk row builder: with provided records + the fallback fetch path."""

    def test_uses_provided_records_with_stub_bucket(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """With ap_records supplied, no fallback fetch happens; only bucket helper is invoked."""

        def bucket(record: dict, _distinct: str) -> str:
            """Return the record's version verbatim (bucketing logic is out of scope for this test)."""
            return str(record.get("version") or "unknown")  # WHY: mirror parent semantics for the 3-way rule.

        monkeypatch.setattr(  # WHY: pin the bucketing helper so the assertion is deterministic.
            _parent.OrgDeviceInventorySummaryCore,
            "_ap_inventory_bucket",
            staticmethod(bucket),
        )
        records = [  # WHY: three records over two model+version keys to prove aggregation.
            {"model": "AP45", "version": "0.14"},
            {"model": "AP45", "version": "0.14"},
            {"model": "AP32", "version": "0.14"},
            {"model": "AP45"},  # WHY: version defaults to "unknown" via the bucket helper.
        ]
        rows = VersionPerModelFetcher._ap_rows(_ORG_ID, records)  # WHY: exercise the with-records path.
        summary = {(row["model"], row["version"]): row["count"] for row in rows}  # WHY: order-agnostic.
        assert summary == {("AP45", "0.14"): 2, ("AP32", "0.14"): 1, ("AP45", "unknown"): 1}  # WHY: fold.
        assert all(row["device_type"] == "ap" for row in rows)  # WHY: device_type must be constant "ap".

    def test_falls_back_to_parent_fetch_when_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Passing ap_records=None must trigger the parent _fetch_ap_inventory fallback."""
        monkeypatch.setattr(  # WHY: fallback fetcher returns a single AP record.
            _parent.OrgDeviceInventorySummaryCore,
            "_fetch_ap_inventory",
            staticmethod(lambda _org_id: [{"model": "AP41", "version": "0.14"}]),
        )
        monkeypatch.setattr(  # WHY: bucket helper returns version verbatim so assertion is stable.
            _parent.OrgDeviceInventorySummaryCore,
            "_ap_inventory_bucket",
            staticmethod(lambda record, _d: str(record.get("version") or "unknown")),
        )
        rows = VersionPerModelFetcher._ap_rows(_ORG_ID, None)  # WHY: ap_records is None -> fallback.
        assert rows == [{"device_type": "ap", "model": "AP41", "version": "0.14", "count": 1}]  # WHY: exact.

    def test_model_defaults_to_unknown(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Records without a model must group under the literal "unknown" bucket."""
        monkeypatch.setattr(  # WHY: bucket helper returns version verbatim so assertion is stable.
            _parent.OrgDeviceInventorySummaryCore,
            "_ap_inventory_bucket",
            staticmethod(lambda record, _d: "0.14"),
        )
        rows = VersionPerModelFetcher._ap_rows(_ORG_ID, [{}, {"model": None}])  # WHY: both records lack model.
        assert rows == [{"device_type": "ap", "model": "unknown", "version": "0.14", "count": 2}]  # WHY: fold.


# ---------------------------------------------------------------------------
# _accumulate_unassigned + _unassigned_rows
# ---------------------------------------------------------------------------
class TestUnassignedRows:
    """Cover the unassigned-inventory row builder, including the fallback fetch."""

    def test_accumulate_unassigned_defaults(self) -> None:
        """Missing type/model default to "unknown"."""
        result = VersionPerModelFetcher._accumulate_unassigned([{}, {"type": "switch"}, {"model": "EX4300"}])
        assert result == {("unknown", "unknown"): 1, ("switch", "unknown"): 1, ("unknown", "EX4300"): 1}  # WHY.

    def test_unassigned_rows_uses_provided_records(self) -> None:
        """Records supplied directly must skip the parent fetch fallback."""
        records = [{"type": "switch", "model": "EX4300"}, {"type": "switch", "model": "EX4300"}]  # WHY: fold.
        rows = VersionPerModelFetcher._unassigned_rows(_ORG_ID, records)  # WHY: with-records path.
        assert rows == [  # WHY: single (switch, EX4300) fold with unassigned version bucket.
            {"device_type": "switch", "model": "EX4300", "version": "unassigned", "count": 2}
        ]

    def test_unassigned_rows_falls_back_when_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Passing None triggers the parent _fetch_unassigned_inventory fallback."""
        monkeypatch.setattr(  # WHY: fallback fetcher returns a single record.
            _parent.OrgDeviceInventorySummaryCore,
            "_fetch_unassigned_inventory",
            staticmethod(lambda _org_id: [{"type": "ap", "model": "AP45"}]),
        )
        rows = VersionPerModelFetcher._unassigned_rows(_ORG_ID, None)  # WHY: None -> fallback.
        assert rows == [{"device_type": "ap", "model": "AP45", "version": "unassigned", "count": 1}]  # WHY.


# ---------------------------------------------------------------------------
# _expand_model_rows
# ---------------------------------------------------------------------------
class TestExpandModelRows:
    """Cover the expander's iteration + AP-skip branch."""

    def test_skips_ap_rows_and_dispatches_others(self) -> None:
        """AP rows are skipped (handled in bulk); non-AP rows dispatch through _rows_for_model."""
        model_rows = [  # WHY: mix of AP + switch + gateway rows.
            {"device_type": "ap", "model": "AP45"},  # skipped in expand loop.
            {"device_type": "switch", "model": "EX4300"},  # produces one switch row.
            {"device_type": "gateway", "model": "SRX300"},  # produces one gateway row.
        ]
        switch_records = [{"model": "EX4300", "version": "22.4", "num_members": 1}]  # WHY: one match.
        gateway_records = [{"model": "SRX300", "version": "23.2"}]  # WHY: one match.
        rows = VersionPerModelFetcher._expand_model_rows(  # WHY: exercise iteration + AP skip.
            model_rows, switch_records, gateway_records  # WHY: the org id left both signatures in issue #887.
        )
        by_type = sorted(row["device_type"] for row in rows)  # WHY: order-agnostic assertion.
        assert by_type == ["gateway", "switch"]  # WHY: proves AP row was skipped; other two dispatched.


# ---------------------------------------------------------------------------
# _append_bulk_rows
# ---------------------------------------------------------------------------
class TestAppendBulkRows:
    """Cover the bulk-append helper (delegates to _ap_rows + _unassigned_rows)."""

    def test_appends_ap_and_unassigned_rows(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Both helper outputs are extended onto ``all_rows`` in-place."""
        monkeypatch.setattr(  # WHY: bucket helper returns version verbatim for a deterministic assertion.
            _parent.OrgDeviceInventorySummaryCore,
            "_ap_inventory_bucket",
            staticmethod(lambda record, _d: str(record.get("version") or "unknown")),
        )
        all_rows: list[dict] = []  # WHY: fresh accumulator; must be mutated by the helper.
        VersionPerModelFetcher._append_bulk_rows(
            _ORG_ID,
            all_rows,
            [{"model": "AP45", "version": "0.14"}],  # WHY: one AP record -> one AP row.
            [{"type": "switch", "model": "EX4300"}],  # WHY: one unassigned record -> one unassigned row.
        )
        device_types = sorted(row["device_type"] for row in all_rows)  # WHY: order-agnostic.
        assert device_types == ["ap", "switch"]  # WHY: proves both helpers ran and their outputs appended.


# ---------------------------------------------------------------------------
# fetch (orchestrator)
# ---------------------------------------------------------------------------
class TestFetchOrchestrator:
    """Cover the public orchestrator end-to-end with all parent hooks patched."""

    def test_full_orchestration_sorted_output(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A single AP + switch + gateway row set is orchestrated, folded, and returned sorted."""
        monkeypatch.setattr(  # WHY: switch inventory returns one matching record for EX4300.
            _parent.OrgDeviceInventorySummaryCore,
            "_fetch_switch_physical_inventory",
            staticmethod(lambda _org_id: [{"model": "EX4300", "version": "22.4", "num_members": 3}]),
        )
        monkeypatch.setattr(  # WHY: gateway inventory returns one matching record for SRX300.
            _parent.OrgDeviceInventorySummaryCore,
            "_fetch_gateway_physical_inventory",
            staticmethod(lambda _org_id: [{"model": "SRX300", "version": "23.2"}]),
        )
        monkeypatch.setattr(  # WHY: bucket helper returns version verbatim so assertion is deterministic.
            _parent.OrgDeviceInventorySummaryCore,
            "_ap_inventory_bucket",
            staticmethod(lambda record, _d: str(record.get("version") or "unknown")),
        )
        model_rows = [  # WHY: three device types drive the expander + bulk-append paths.
            {"device_type": "ap", "model": "AP45"},
            {"device_type": "switch", "model": "EX4300"},
            {"device_type": "gateway", "model": "SRX300"},
        ]
        rows = VersionPerModelFetcher.fetch(  # WHY: full orchestration exercised here.
            _ORG_ID,
            model_rows,
            unassigned_records=[{"type": "switch", "model": "EX4300"}],
            ap_records=[{"model": "AP45", "version": "0.14"}],
        )
        # WHY: verify sort by (device_type, model, -count) is applied.
        assert [(row["device_type"], row["model"]) for row in rows] == [
            ("ap", "AP45"),  # WHY: ap sorts first alphabetically.
            ("gateway", "SRX300"),  # WHY: gateway sorts second.
            ("switch", "EX4300"),  # WHY: switch third; two entries below.
            ("switch", "EX4300"),  # WHY: unassigned bucket also switch/EX4300.
        ]
