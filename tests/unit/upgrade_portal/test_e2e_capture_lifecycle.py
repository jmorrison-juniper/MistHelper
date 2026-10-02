"""Require native capture fields and exact shipped pre-check eligibility."""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping, Sequence
from copy import deepcopy
from types import ModuleType
from typing import Any

import pytest

from src.upgrade_portal.capture import assembly, store
from src.upgrade_portal.capture.clients import ClientAttachment, ClientIdentity, ClientRecord
from tests.support.upgrade_portal_e2e.capture_fidelity import NativeCaptureFixture
from tests.support.upgrade_portal_e2e.records import PortalRecordStore

logger = logging.getLogger(__name__)


class PrecheckQueryBoundary:
    """Interpret the actual native filters, sort, limit, and projection in memory."""

    def __init__(self, records: Sequence[Mapping[str, Any]]) -> None:
        """Keep isolated input rows and the exact native query calls."""
        self.records = deepcopy(tuple(records))
        self.calls: list[tuple[str, dict[str, Any]]] = []

    @property
    def aql(self) -> PrecheckQueryBoundary:
        """Expose the controlled query boundary used by the shipped reader."""
        return self

    def execute(self, query: str, bind_vars: dict[str, Any]) -> list[dict[str, Any]]:
        """Apply the real query text instead of copying a lifecycle predicate."""
        logger.info("Read the native pre-check query with documents=%d", len(self.records))
        filters = re.findall(r"FILTER doc\.([a-z_]+) == @([a-z_]+)", query)
        projection = re.search(r"RETURN KEEP\(doc, (.+)\)", query)
        if not filters or projection is None or "SORT doc.started_at DESC\n  LIMIT 1\n" not in query:
            raise AssertionError(f"Checked documents={len(self.records)}. The native query shape is unreadable.")
        self.calls.append((query, deepcopy(bind_vars)))
        matches = [
            row for row in reversed(self.records) if all(row.get(field) == bind_vars[name] for field, name in filters)
        ]
        newest = max(matches, key=lambda row: str(row.get("started_at") or ""), default=None)
        fields = re.findall(r'"([a-z_]+)"', projection.group(1))
        result = [{field: deepcopy(newest[field]) for field in fields if field in newest}] if newest is not None else []
        logger.debug(
            "Checked documents=%d filters=%d query calls=%d rows=%d",
            len(self.records),
            len(filters),
            len(self.calls),
            len(result),
        )
        return result


class CaptureLifecycleGuard:
    """Measure native documents and compare both real eligibility readers."""

    @staticmethod
    def document(record: object, expected_content: str) -> tuple[int, int]:
        """Reject unreadable or obsolete fields without a success-shaped fallback."""
        logger.info("Check one native capture document")
        if not isinstance(record, Mapping):
            raise AssertionError("Checked documents=0. The capture document is unreadable.")
        if record.get(store.CAPTURE_STATE_FIELD) != store.CaptureState.VERIFIED.value:
            raise AssertionError("Checked documents=1 lifecycle fields=1. The lifecycle is not verified.")
        if record.get("capture_status") != expected_content:
            raise AssertionError("Checked documents=1 lifecycle fields=1 content fields=1. The content status differs.")
        if expected_content not in {assembly.STATUS_COMPLETE, assembly.STATUS_PARTIAL, assembly.STATUS_FAILED}:
            raise AssertionError(
                "Checked documents=1 lifecycle fields=1 content fields=1. The content status is obsolete."
            )
        logger.debug("Checked documents=1 lifecycle fields=1 content fields=1")
        return 1, 2

    @staticmethod
    def eligibility(records: Sequence[dict[str, Any]], site_id: str, expected_id: str) -> tuple[int, int]:
        """Require both actual readers to return the explicit expected capture."""
        logger.info("Compare native pre-check eligibility with documents=%d", len(records))
        owned = PortalRecordStore("e2e-3375-unit-owner")
        for record in records:
            assert owned.write_capture(record) is True
        boundary = PrecheckQueryBoundary(records)
        native = store.latest_standalone_precheck(site_id, database=boundary)
        native_id = str(native["capture_id"]) if native is not None else ""
        actual_id = owned.newest_precheck(site_id)
        measure = f"Checked documents={len(records)} query calls={len(boundary.calls)} readers=2"
        assert len(boundary.calls) == 1, measure
        assert (
            native_id == expected_id
        ), f"{measure}. The native reader returned {native_id!r}, expected {expected_id!r}."
        assert actual_id == expected_id, f"{measure}. The stand-in returned {actual_id!r}, expected {expected_id!r}."
        assert boundary.calls[0][1]["verified"] == store.CaptureState.VERIFIED.value
        logger.debug("%s selected capture=%s", measure, expected_id)
        return len(records), len(boundary.calls)

    @staticmethod
    def seed(configuration: pytest.Config) -> dict[str, Any]:
        """Obtain a fresh genuine native standalone document without global mutation."""
        native = NativeCaptureFixture.read(configuration)
        return native.stand_in_capture_index()["e2e-capture-standalone-0001"]

    @staticmethod
    def obsolete_predicate(record: dict[str, Any], site_id: str) -> bool:
        """Represent the original defective content-field decision for a negative control."""
        return (
            record.get("site_id") == site_id
            and record.get("role") == "pre"
            and record.get("run_id") == ""
            and record.get("capture_status") == "verified"
        )

    @classmethod
    def damage_decision(cls, monkeypatch: pytest.MonkeyPatch, damage: str) -> None:
        """Apply one explicit eligibility regression without changing production bytes."""
        if damage == "old-stand-in":
            monkeypatch.setattr(PortalRecordStore, "_is_precheck", staticmethod(cls.obsolete_predicate))
            return
        original = store._PRECHECK_QUERY
        changed = (
            original.replace("  FILTER doc.state == @verified\n", "")
            if damage == "remove-filter"
            else original.replace("doc.state == @verified", "doc.capture_status == @verified")
        )
        assert changed != original
        monkeypatch.setattr(store, "_PRECHECK_QUERY", changed)


class TestNativeCaptureLifecycle:
    """Require every actual seed and counted independent negative controls."""

    def test_all_five_native_documents_and_parent_names(self, request: pytest.FixtureRequest) -> None:
        """Measure actual lifecycle, content, native names, and accepted count keys."""
        native = NativeCaptureFixture.read(request.config)
        captures = native.stand_in_capture_index()
        before = deepcopy(captures)
        measured = [0, 0, 0]
        for capture_id, capture in captures.items():
            expected = assembly.STATUS_PARTIAL if capture_id == "e2e-capture-tier3-0001" else assembly.STATUS_COMPLETE
            checked = CaptureLifecycleGuard.document(capture, expected)
            measured[0] += checked[0]
            measured[1] += checked[1]
            assert len(capture["counts"]) == 9 and set(capture["counts"]) == set(assembly.COUNT_KEYS)
            for rows in capture["clients"].values():
                for row in rows:
                    assert row["device_name"] == capture["device_index"][row["device_mac"]]["name"]
                    measured[2] += 1
        assert measured == [5, 10, 16]
        assert captures == before
        print("Checked native documents=5 lifecycle/content fields=10 count fields=45 matched client parents=16.")

    @pytest.mark.parametrize(
        ("damage", "message"),
        [
            ("unreadable", "documents=0"),
            ("missing-state", "lifecycle fields=1"),
            ("pending", "lifecycle fields=1"),
            ("obsolete-content", "content fields=1"),
            ("swapped-fields", "lifecycle fields=1"),
        ],
    )
    def test_document_guard_rejects_independent_damage(
        self, request: pytest.FixtureRequest, damage: str, message: str
    ) -> None:
        """A guard must fail when its real input is absent, damaged, or obsolete."""
        seed = CaptureLifecycleGuard.seed(request.config)
        damaged: object = {
            "unreadable": None,
            "missing-state": {key: value for key, value in seed.items() if key != store.CAPTURE_STATE_FIELD},
            "pending": {**seed, store.CAPTURE_STATE_FIELD: store.CaptureState.PENDING.value},
            "obsolete-content": {**seed, "capture_status": "verified"},
            "swapped-fields": {**seed, "state": "complete", "capture_status": "verified"},
        }[damage]
        with pytest.raises(AssertionError, match=message):
            CaptureLifecycleGuard.document(damaged, assembly.STATUS_COMPLETE)
        assert seed["state"] == store.CaptureState.VERIFIED.value
        assert seed["capture_status"] == assembly.STATUS_COMPLETE

    def test_matched_and_unmatched_names_use_the_native_index(self, request: pytest.FixtureRequest) -> None:
        """Normalize a matched address and retain no guessed name for an unmatched address."""
        seed = CaptureLifecycleGuard.seed(request.config)
        clients = [
            ClientRecord(
                "aabbcc337501", ClientIdentity(hostname="Matched"), ClientAttachment(device_mac="00:00:00:00:00:01")
            ),
            ClientRecord(
                "aabbcc337502", ClientIdentity(hostname="Unmatched"), ClientAttachment(device_mac="001122334455")
            ),
        ]
        logger.info("Join two controlled clients through the shipped parent-name builder")
        rows = assembly.fill_device_names(clients, seed["device_index"])
        assert len(rows) == 2 and rows[0]["device_name"] == "E2E ap 1"
        assert "device_name" not in rows[1]
        logger.debug("Checked native parent rows=2 matched=1 unmatched=1 guessed labels=0")

    @pytest.mark.parametrize("content", [assembly.STATUS_COMPLETE, assembly.STATUS_PARTIAL, assembly.STATUS_FAILED])
    def test_native_content_builder_keeps_all_three_values(self, request: pytest.FixtureRequest, content: str) -> None:
        """Resolve genuine content conditions without adding a content eligibility policy."""
        seed = CaptureLifecycleGuard.seed(request.config)
        sections = assembly.CaptureSections(
            device_index=seed["device_index"] if content != assembly.STATUS_FAILED else {},
            devices=seed["devices"] if content != assembly.STATUS_FAILED else [],
            clients=seed["clients"] if content != assembly.STATUS_FAILED else {},
        )
        reasons = (
            []
            if content == assembly.STATUS_COMPLETE
            else [{"section": "devices", "reason": assembly.REASON_READ_FAILED, "http_status": 503}]
        )
        resolved = assembly.resolve_status(sections, reasons)
        assert resolved == content
        seed.update(
            capture_status=resolved, devices=sections.devices, clients=sections.clients, partial_reasons=reasons
        )
        seed.update(device_index=sections.device_index, counts=assembly.build_counts(sections))
        assert CaptureLifecycleGuard.document(seed, content) == (1, 2)
        assert CaptureLifecycleGuard.eligibility([seed], str(seed["site_id"]), str(seed["capture_id"])) == (1, 1)

    @pytest.mark.parametrize("damage", ["duplicate", "unreadable-contract"])
    def test_native_identity_guard_fails_explicitly(
        self, request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch, damage: str
    ) -> None:
        """Do not allocate a second fixture identity or accept an unreadable native contract."""
        path = request.config.rootpath / "tests/e2e/upgrade_portal/conftest.py"
        modules = [ModuleType(f"damaged_native_{number}") for number in range(2 if damage == "duplicate" else 1)]
        for module in modules:
            module.__file__ = str(path)
        monkeypatch.setattr(NativeCaptureFixture, "candidates", lambda _configuration: modules)
        expected = "modules=2" if damage == "duplicate" else "contract is unreadable"
        with pytest.raises(AssertionError, match=expected):
            NativeCaptureFixture.read(request.config)
        assert len(modules) == (2 if damage == "duplicate" else 1)


class TestNativePrecheckEligibility:
    """Keep content status independent from every native lifecycle eligibility decision."""

    @pytest.mark.parametrize("content", [assembly.STATUS_COMPLETE, assembly.STATUS_PARTIAL, assembly.STATUS_FAILED])
    @pytest.mark.parametrize(
        "state",
        [store.CaptureState.VERIFIED.value, store.CaptureState.PENDING.value, store.CaptureState.FAILED.value, None],
    )
    def test_lifecycle_alone_decides_verification(
        self, request: pytest.FixtureRequest, content: str, state: str | None
    ) -> None:
        """Verified complete, partial, and failed content all follow the native state query."""
        seed = CaptureLifecycleGuard.seed(request.config)
        seed.update(capture_status=content, state=state)
        expected = seed["capture_id"] if state == store.CaptureState.VERIFIED.value else ""
        assert CaptureLifecycleGuard.eligibility([seed], str(seed["site_id"]), expected) == (1, 1)

    @pytest.mark.parametrize(
        "change",
        [
            {"run_id": "e2e-3375-owned-run"},
            {"run_id": None},
            {"site_id": "e2e-3375-wrong-site"},
            {"role": "post"},
            {"state": "complete", "capture_status": "verified"},
            {"state": None, "capture_status": "verified"},
        ],
    )
    def test_other_native_filters_remain_required(self, request: pytest.FixtureRequest, change: dict[str, Any]) -> None:
        """Content cannot bypass native origin, run, site, role, or lifecycle rules."""
        seed = CaptureLifecycleGuard.seed(request.config)
        site_id = str(seed["site_id"])
        seed.update(change)
        assert CaptureLifecycleGuard.eligibility([seed], site_id, "") == (1, 1)

    @pytest.mark.parametrize("equal_time", [False, True])
    def test_native_time_and_tie_order_are_preserved(self, request: pytest.FixtureRequest, equal_time: bool) -> None:
        """The same ordering winner retains its own tier without a new content policy."""
        seed = CaptureLifecycleGuard.seed(request.config)
        newer = {**seed, "capture_id": "e2e-3375-newer", "tier": 3, "capture_status": "partial"}
        older = {**seed, "capture_id": "e2e-3375-older", "tier": 2}
        newer["started_at"] = older["started_at"] if equal_time else "2026-09-02T10:00:00+00:00"
        expected = older["capture_id"] if equal_time else newer["capture_id"]
        assert CaptureLifecycleGuard.eligibility([newer, older], str(seed["site_id"]), expected) == (2, 1)
        owned = PortalRecordStore("e2e-3375-order-owner")
        for record in (newer, older):
            assert owned.write_capture(record) is True
        assert owned.newest_precheck_tier(str(seed["site_id"])) == (expected, 2 if equal_time else 3)

    @pytest.mark.parametrize("damage", ["remove-filter", "swap-field", "old-stand-in"])
    def test_native_guard_detects_lifecycle_regressions(
        self, request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch, damage: str
    ) -> None:
        """The guard fails if either real decision removes or swaps lifecycle eligibility."""
        seed = CaptureLifecycleGuard.seed(request.config)
        seed["capture_status"] = assembly.STATUS_PARTIAL
        pending = {
            **seed,
            "capture_id": "e2e-3375-pending",
            "state": "pending",
            "started_at": "2026-09-03T10:00:00+00:00",
        }
        CaptureLifecycleGuard.damage_decision(monkeypatch, damage)
        with pytest.raises(AssertionError, match="Checked documents=2 query calls=1 readers=2"):
            CaptureLifecycleGuard.eligibility([seed, pending], str(seed["site_id"]), str(seed["capture_id"]))
