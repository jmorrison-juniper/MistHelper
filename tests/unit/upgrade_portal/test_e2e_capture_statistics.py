"""Prove capture statistics, real builder results, and independent guard failures."""

from __future__ import annotations

import importlib
import importlib.util
import logging
import sys
from collections.abc import Iterator, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar, NoReturn

import pytest

from src.upgrade_portal.capture import assembly, devices
from src.upgrade_portal.compare import diff
from tests.e2e.upgrade_portal.empty_site_seeds import EMPTY_SITE_ID

logger = logging.getLogger(__name__)


class CaptureStatisticsGuard:
    """Reject incomplete statistics without reading or changing a global seed."""

    class Checked:
        """Keep input counts separate from successful running-field checks."""

        @dataclass
        class Counts:
            """Keep measured input counts and completed field checks."""

            inventory: int | None
            statistics: int | None
            index: int | None
            fields: int = 0

            def __str__(self) -> str:
                """Name each measured input and the completed field checks."""
                counts = [
                    value if value is not None else "unreadable"
                    for value in (self.inventory, self.statistics, self.index)
                ]
                return (
                    f"Checked inventory={counts[0]} statistics={counts[1]} " f"index={counts[2]} fields={self.fields}"
                )

        @classmethod
        def measure(cls, inventory: object, statistics: object, index: object) -> CaptureStatisticsGuard.Checked.Counts:
            """Report unreadable inputs instead of treating them as empty records."""
            counts = [
                len(value) if isinstance(value, (Mapping, Sequence)) and not isinstance(value, (str, bytes)) else None
                for value in (inventory, statistics, index)
            ]
            return cls.Counts(counts[0], counts[1], counts[2])

        @staticmethod
        def reject(checked: Counts, reason: str) -> NoReturn:
            """Report the exact defect and stop the guard."""
            logger.error("%s. %s", reason, checked)
            raise AssertionError(f"{reason}. {checked}")

        @staticmethod
        def require(checked: Counts, condition: bool, reason: str) -> None:
            """Reject a failed decision without losing its measurement."""
            if not condition:
                CaptureStatisticsGuard.Checked.reject(checked, reason)

    @staticmethod
    def by_mac(records: object, section: str, checked: Checked.Counts) -> dict[str, Mapping[str, object]]:
        """Require readable, nonempty records with unique normalized addresses."""
        if not isinstance(records, Sequence) or isinstance(records, (str, bytes)):
            CaptureStatisticsGuard.Checked.reject(checked, f"{section} input unreadable")
        CaptureStatisticsGuard.Checked.require(checked, len(records) > 0, f"{section} zero records")
        result: dict[str, Mapping[str, object]] = {}
        for record in records:
            if not isinstance(record, Mapping):
                CaptureStatisticsGuard.Checked.reject(checked, f"{section} record unreadable")
            mac = devices.normalize_device_mac(record.get("mac"))
            CaptureStatisticsGuard.Checked.require(checked, mac != "", f"{section} mac invalid")
            CaptureStatisticsGuard.Checked.require(checked, mac not in result, f"{section} mac duplicate {mac}")
            if section == "inventory":
                address = record.get("ip")
                CaptureStatisticsGuard.Checked.require(
                    checked, isinstance(address, str) and address != "", f"inventory ip missing for {mac}"
                )
            result[mac] = record
        return result

    @staticmethod
    def check_fields(
        record: Mapping[str, object], expected: Mapping[str, object], checked: Checked.Counts, section: str
    ) -> None:
        """Count only successful checks of explicit running fields."""
        for field, value in expected.items():
            reason = f"{section} {field}: expected {value!r}, received {record.get(field)!r}"
            CaptureStatisticsGuard.Checked.require(checked, field in record and record[field] == value, reason)
            checked.fields += 1

    @classmethod
    def check(cls, inventory: object, statistics: object, version: str) -> Checked.Counts:
        """Validate supplied statistics against inventory and an explicit version."""
        checked = cls.Checked.measure(inventory, statistics, {})
        logger.info("Validate capture statistics. %s", checked)
        inventory_rows = cls.by_mac(inventory, "inventory", checked)
        statistics_rows = cls.by_mac(statistics, "statistics", checked)
        missing = sorted(inventory_rows.keys() - statistics_rows.keys())
        extra = sorted(statistics_rows.keys() - inventory_rows.keys())
        CaptureStatisticsGuard.Checked.require(
            checked, not missing and not extra, f"statistics MAC membership missing={missing} extra={extra}"
        )
        for mac, record in statistics_rows.items():
            expected = {"version": version, "status": "connected", "ip": inventory_rows[mac]["ip"], "uptime": 3600}
            cls.check_fields(record, expected, checked, f"statistics {mac}")
            CaptureStatisticsGuard.Checked.require(
                checked,
                set(record) == {"mac", "version", "status", "ip", "uptime"},
                f"statistics fields for {mac} must be mac, version, status, ip, uptime",
            )
        logger.debug("Validated capture statistics. %s", checked)
        return checked

    class SeedContract:
        """Hold the immutable capture expectations and metadata check."""

        VERSIONS: ClassVar[tuple[tuple[str, str], ...]] = (
            ("e2e-capture-pre-0001", "0.14.29216"),
            ("e2e-capture-standalone-0001", "0.14.29216"),
            ("e2e-capture-post-0001", "0.15.1"),
            ("e2e-capture-stored-poll-0001", "0.14.29216"),
            ("e2e-capture-tier3-0001", "0.14.29216"),
        )
        PRESERVED: ClassVar[dict[str, Any]] = {
            "metadata": {
                "org_id": "11111111-1111-1111-1111-111111111111",
                "org_name": "E2E Stand-In Organization",
                "site_id": "22222222-2222-2222-2222-222222222222",
                "site_name": "E2E Stand-In Site",
                "actor_email": "e2e.operator@example.invalid",
                "schema_version": 1,
                "duration_seconds": 1.0,
                "stored_size_bytes": 4096,
            },
            "captures": {
                "e2e-capture-pre-0001": {
                    "run_id": "e2e-run-0001",
                    "role": "pre",
                    "tier": 2,
                    "capture_status": "verified",
                    "started_at": "2026-08-19T10:00:00+00:00",
                },
                "e2e-capture-standalone-0001": {
                    "run_id": "",
                    "role": "pre",
                    "tier": 2,
                    "capture_status": "verified",
                    "started_at": "2026-08-19T10:15:00+00:00",
                },
                "e2e-capture-post-0001": {
                    "run_id": "e2e-run-0001",
                    "role": "post",
                    "tier": 2,
                    "capture_status": "verified",
                    "started_at": "2026-08-19T10:30:00+00:00",
                },
                "e2e-capture-stored-poll-0001": {
                    "run_id": "",
                    "role": "pre",
                    "tier": 2,
                    "capture_status": "complete",
                    "started_at": "2026-08-19T10:45:00+00:00",
                    "state": "verified",
                    "site_id": "e2e-stored-poll-site",
                    "site_name": "E2E Stored Poll Site",
                },
                "e2e-capture-tier3-0001": {
                    "run_id": "e2e-run-0001",
                    "role": "pre",
                    "tier": 3,
                    "capture_status": "verified",
                    "started_at": "2026-08-19T11:00:00+00:00",
                },
            },
            "counts": {
                "devices_total": 3,
                "devices_connected": 3,
                "devices_disconnected": 0,
                "access_points": 1,
                "gateways": 1,
                "switches": 1,
                "clients_wired": 0,
                "clients_wireless": 3,
                "clients_guest": 0,
            },
            "guest": [
                {
                    "mac": "aabbcc000099",
                    "hostname": "e2e-guest-1",
                    "username": "guest@example.invalid",
                    "device_mac": "000000000001",
                    "device_name": "e2e-ap-1",
                    "ssid": "guest-wifi",
                }
            ],
            "extras": {
                "switch_ports": [{"mac": "000000000002", "port_id": "ge-0/0/1", "up": True, "speed": 1000}],
                "poe": [{"mac": "000000000002", "port_id": "ge-0/0/1", "poe_on": True, "power_draw": 4.5}],
                "radios": [{"mac": "000000000001", "band": "5", "channel": 36, "power": 12}],
                "tunnels": [],
                "bgp_peers": [],
                "alarms": [],
            },
        }

        @classmethod
        def require_preserved(cls, capture: Mapping[str, Any]) -> None:
            """Validate stored metadata, clients, extras, and unchanged lifecycle fields."""
            logger.info("Check preserved capture metadata and client groups")
            capture_id = capture["capture_id"]
            preserved = cls.PRESERVED
            expected = {**preserved["metadata"], **preserved["captures"][capture_id], "capture_id": capture_id}
            expected.update(finished_at=expected["started_at"], ordinal=1 if expected["role"] == "pre" else 2)
            excluded = {"devices", "device_index", "counts", "clients", "extras", "partial_reasons"}
            assert {key: value for key, value in capture.items() if key not in excluded} == expected
            cls.require_contents(capture)
            logger.debug("Checked capture metadata fields=%d", len(expected))

        @classmethod
        def require_contents(cls, capture: Mapping[str, Any]) -> None:
            """Check the preserved client groups and Tier 3 sections."""
            logger.info("Check preserved capture client groups and sections")
            preserved = cls.PRESERVED
            tier3 = capture["capture_id"] == "e2e-capture-tier3-0001"
            wireless = [
                {
                    "mac": f"aabbcc00000{number}",
                    "hostname": f"e2e-client-{number}",
                    "device_mac": f"00000000000{number}",
                }
                for number in range(1, 4)
            ]
            assert capture["clients"] == {
                "wired": [],
                "wireless": wireless,
                "guest": preserved["guest"] if tier3 else [],
            }
            assert capture.get("extras") == (preserved["extras"] if tier3 else None)
            assert capture["partial_reasons"] == (
                [{"section": "bgp_peers", "reason": "cloud_call_failed", "http_status": 0}] if tier3 else []
            )
            logger.debug("Checked client groups=3 tier3=%s", tier3)


class CaptureIndexGuard(CaptureStatisticsGuard):
    """Reject incorrect supplied index entries under the shipped address rule."""

    @staticmethod
    def entries(index: object, checked: CaptureStatisticsGuard.Checked.Counts) -> dict[str, Mapping[str, object]]:
        """Reject unreadable entries, invalid addresses, and normalized duplicates."""
        if not isinstance(index, Mapping):
            CaptureStatisticsGuard.Checked.reject(checked, "index input unreadable")
        CaptureStatisticsGuard.Checked.require(checked, len(index) > 0, "index zero records")
        result: dict[str, Mapping[str, object]] = {}
        for key, entry in index.items():
            mac = devices.normalize_device_mac(key)
            CaptureStatisticsGuard.Checked.require(checked, mac != "", "index mac invalid")
            CaptureStatisticsGuard.Checked.require(checked, mac not in result, f"index mac duplicate {mac}")
            if not isinstance(entry, Mapping):
                CaptureStatisticsGuard.Checked.reject(checked, f"index record unreadable for {mac}")
            result[mac] = entry
        return result

    @classmethod
    def check(cls, inventory: object, index: object, version: str) -> CaptureStatisticsGuard.Checked.Counts:
        """Validate index membership and each explicit running field."""
        checked = cls.Checked.measure(inventory, [], index)
        logger.info("Validate the capture index. %s", checked)
        inventory_rows = cls.by_mac(inventory, "inventory", checked)
        index_rows = cls.entries(index, checked)
        missing = sorted(inventory_rows.keys() - index_rows.keys())
        extra = sorted(index_rows.keys() - inventory_rows.keys())
        CaptureStatisticsGuard.Checked.require(
            checked, not missing and not extra, f"index MAC membership missing={missing} extra={extra}"
        )
        for mac, entry in index_rows.items():
            expected = {"version": version, "status": "connected", "ip": inventory_rows[mac]["ip"], "uptime": 3600}
            cls.check_fields(entry, expected, checked, f"index {mac}")
        logger.debug("Validated the capture index. %s", checked)
        return checked


class DeviceIndexRecorder:
    """Observe actual builder calls, validate identity, and retain actual outputs."""

    @dataclass(frozen=True)
    class Call:
        """Keep immutable input snapshots and the actual returned index."""

        inventory: tuple[Mapping[str, object], ...]
        statistics: tuple[Mapping[str, object], ...]
        index: dict[str, dict[str, object]]

    def __init__(self) -> None:
        """Retain the shipped callable before pytest installs this recorder."""
        self.builder = devices.build_device_index
        self.calls: list[DeviceIndexRecorder.Call] = []
        self.captures: dict[str, dict[str, Any]] = {}

    def __call__(
        self, inventory: Sequence[Mapping[str, object]], statistics: Sequence[Mapping[str, object]]
    ) -> dict[str, dict[str, object]]:
        """Validate a real build without replacing or changing its returned index."""
        logger.info("Observe a real device build with inventory=%d statistics=%d", len(inventory), len(statistics))
        inventory_before, statistics_before = deepcopy(tuple(inventory)), deepcopy(tuple(statistics))
        index = self.builder(inventory, statistics)
        expected_keys = {devices.normalize_device_mac(record.get("mac")) for record in inventory}
        assert set(index) == expected_keys, "The real builder must retain every supplied valid MAC."
        assert tuple(inventory) == inventory_before, "The real builder changed its inventory input."
        assert tuple(statistics) == statistics_before, "The real builder changed its statistics input."
        identity_fields = ("name", "type", "model", "serial", "site_id")
        for record in inventory:
            entry = index[devices.normalize_device_mac(record["mac"])]
            assert {field: entry[field] for field in identity_fields} == {
                field: str(record.get(field) or "") for field in identity_fields
            }, "The real builder must preserve inventory identity."
        self.calls.append(self.Call(inventory_before, statistics_before, index))
        logger.debug(
            "Observed real build inventory=%d statistics=%d index=%d", len(inventory), len(statistics), len(index)
        )
        return index

    def call_for(self, capture: Mapping[str, object]) -> Call:
        """Require the capture to retain one actual observed builder output."""
        matches = [call for call in self.calls if call.index is capture["device_index"]]
        assert len(matches) == 1, f"Checked {len(self.calls)} real builder calls, found {len(matches)} capture outputs."
        return matches[0]

    def require_empty(self, capture: Mapping[str, Any]) -> None:
        """Validate the legitimate empty site's actual inputs, output, and counts."""
        logger.info("Check the empty-site seed after five global builder calls")
        call = self.call_for(capture)
        assert len(self.calls) == 6
        assert (call.inventory, call.statistics, call.index) == ((), (), {})
        assert capture["devices"] == []
        assert capture["clients"] == {"wired": [], "wireless": [], "guest": []}
        assert capture["counts"] == dict.fromkeys(CaptureStatisticsGuard.SeedContract.PRESERVED["counts"], 0)
        logger.debug("Checked empty-site inventory=0 statistics=0 index=0 count fields=9")


class TestCaptureStatisticsGuards:
    """Prove each decision with fresh records independent of the global captures."""

    class Inputs:
        """Build and damage independent records while retaining explicit expectations."""

        @dataclass
        class Records:
            """Keep independent inputs and their damage builders."""

            inventory: list[dict[str, object]]
            statistics: list[dict[str, object]]
            index: dict[str, dict[str, object]]

            @staticmethod
            def damaged_records(records: Sequence[Mapping[str, object]], damage: str) -> object:
                """Return fresh damaged records without changing the valid controls."""
                logger.info("Change independent record input with defect %s", damage)
                result = {
                    "empty": [],
                    "unreadable": None,
                    "unreadable-row": [None, records[1]],
                    "missing": records[1:],
                    "extra": [*records, {**records[0], "mac": "001122334455"}],
                    "invalid": [{**records[0], "mac": "not-a-mac"}, records[1]],
                    "duplicate": [records[0], records[0]],
                    "normalized-duplicate": [records[0], {**records[1], "mac": "aabbccddeeff"}],
                    "mismatched": [{**records[0], "mac": "001122334455"}, records[1]],
                    "missing-ip": [{**records[0], "ip": ""}, records[1]],
                    "extra-field": [{**records[0], "configured_version": "inventory-only-version"}, records[1]],
                }[damage]
                logger.debug("Changed record input. Checked records=%d defect=%s", len(records), damage)
                return result

            @staticmethod
            def damaged_index(index: Mapping[str, Mapping[str, object]], damage: str) -> object:
                """Damage an actual shipped builder result, not a replacement index."""
                logger.info("Change the independent index with defect %s", damage)
                result = {
                    "empty": {},
                    "unreadable": None,
                    "unreadable-row": {**index, "aabbccddeeff": None},
                    "missing": {"aabbccddee01": index["aabbccddee01"]},
                    "extra": {**index, "001122334455": index["aabbccddeeff"]},
                    "invalid": {"not-a-mac": index["aabbccddeeff"], "aabbccddee01": index["aabbccddee01"]},
                    "normalized-duplicate": {**index, "AA:BB:CC:DD:EE:FF": index["aabbccddeeff"]},
                    "mismatched": {"001122334455": index["aabbccddeeff"], "aabbccddee01": index["aabbccddee01"]},
                }[damage]
                logger.debug("Changed the index input. Checked entries=%d defect=%s", len(index), damage)
                return result

        @classmethod
        def valid(cls) -> TestCaptureStatisticsGuards.Inputs.Records:
            """Join alternate MAC spellings with an explicit statistics version."""
            logger.info("Build two independent inventory and statistics controls")
            inventory: list[dict[str, object]] = [
                {"mac": "AA:BB:CC:DD:EE:FF", "ip": "198.51.100.10", "version": "inventory-only-version"},
                {"mac": "aa-bb-cc-dd-ee-01", "ip": "198.51.100.11", "version": "inventory-only-version"},
            ]
            statistics = [
                {"mac": mac, "version": "0.15.1", "status": "connected", "ip": address, "uptime": 3600}
                for mac, address in (("aa-bb-cc-dd-ee-ff", "198.51.100.10"), ("AABBCCDDEE01", "198.51.100.11"))
            ]
            index = devices.build_device_index(inventory, statistics)
            logger.debug("Built controls with inventory=2 statistics=2 index=%d", len(index))
            return cls.Records(inventory, statistics, index)

        @classmethod
        def damaged(cls, records: Records, target: str, damage: str) -> tuple[object, object, object]:
            """Select one supplied input defect for an independent guard decision."""
            if target == "all":
                return [], [], {}
            if target == "inventory":
                return cls.Records.damaged_records(records.inventory, damage), records.statistics, records.index
            if target == "statistics":
                return records.inventory, cls.Records.damaged_records(records.statistics, damage), records.index
            if target == "index":
                return records.inventory, records.statistics, cls.Records.damaged_index(records.index, damage)
            raise AssertionError(f"Unknown supplied input target {target!r}.")

        @staticmethod
        def require_missing_playwright(monkeypatch: pytest.MonkeyPatch) -> None:
            """Prove the module dependency guard without removing an installed package."""
            logger.info("Check the browser module with one unavailable dependency")
            importlib.import_module("tests.e2e.upgrade_portal.test_comparison")
            path = Path(__file__).resolve().parents[2] / "e2e" / "upgrade_portal" / "test_capture_version_comparison.py"
            specification = importlib.util.spec_from_file_location("capture_statistics_missing_browser", path)
            assert specification is not None and specification.loader is not None
            module = importlib.util.module_from_spec(specification)
            with monkeypatch.context() as isolated:
                isolated.setitem(sys.modules, "playwright.sync_api", None)
                with pytest.raises(pytest.skip.Exception) as refusal:
                    specification.loader.exec_module(module)
            assert str(refusal.value) == "The Playwright package is not installed."
            logger.debug("Checked browser modules=1 unavailable dependencies=1 explicit refusals=1")

    @pytest.mark.parametrize("guard", ["statistics", "index"])
    def test_positive_controls_use_statistics_and_normalized_macs(self, guard: str) -> None:
        """Both guards accept alternate spellings and reject an inventory version fallback."""
        inputs = self.Inputs.valid()
        assert {record["version"] for record in inputs.inventory} == {"inventory-only-version"}
        assert set(inputs.index) == {"aabbccddeeff", "aabbccddee01"}
        assert {entry["version"] for entry in inputs.index.values()} == {"0.15.1"}
        if guard == "statistics":
            checked = CaptureStatisticsGuard.check(inputs.inventory, inputs.statistics, "0.15.1")
            expected = "Checked inventory=2 statistics=2 index=0 fields=8"
        else:
            alternate_index = {
                "AA:BB:CC:DD:EE:FF": inputs.index["aabbccddeeff"],
                "aa-bb-cc-dd-ee-01": inputs.index["aabbccddee01"],
            }
            checked = CaptureIndexGuard.check(inputs.inventory, alternate_index, "0.15.1")
            expected = "Checked inventory=2 statistics=0 index=2 fields=8"
        assert str(checked) == expected

    @pytest.mark.parametrize("refusal", ["unknown-target", "missing-playwright"])
    def test_fixture_refusals_are_explicit(self, refusal: str, monkeypatch: pytest.MonkeyPatch) -> None:
        """An invalid fixture target or missing browser package must give an explicit refusal."""
        if refusal == "missing-playwright":
            self.Inputs.require_missing_playwright(monkeypatch)
            return
        inputs = self.Inputs.valid()
        with pytest.raises(AssertionError) as failure:
            self.Inputs.damaged(inputs, "unknown", "empty")
        assert str(failure.value) == "Unknown supplied input target 'unknown'."

    @pytest.mark.parametrize(
        "guard,target,damage,expected",
        [
            ("statistics", "all", "empty", ("inventory zero records", "0 statistics=0 index=0 fields=0")),
            ("statistics", "inventory", "empty", ("inventory zero records", "0 statistics=2 index=0 fields=0")),
            (
                "statistics",
                "inventory",
                "unreadable",
                ("inventory input unreadable", "unreadable statistics=2 index=0 fields=0"),
            ),
            (
                "statistics",
                "inventory",
                "unreadable-row",
                ("inventory record unreadable", "2 statistics=2 index=0 fields=0"),
            ),
            ("statistics", "inventory", "invalid", ("inventory mac invalid", "2 statistics=2 index=0 fields=0")),
            (
                "statistics",
                "inventory",
                "duplicate",
                ("inventory mac duplicate aabbccddeeff", "2 statistics=2 index=0 fields=0"),
            ),
            (
                "statistics",
                "inventory",
                "normalized-duplicate",
                ("inventory mac duplicate aabbccddeeff", "2 statistics=2 index=0 fields=0"),
            ),
            (
                "statistics",
                "inventory",
                "missing-ip",
                ("inventory ip missing for aabbccddeeff", "2 statistics=2 index=0 fields=0"),
            ),
            ("statistics", "statistics", "empty", ("statistics zero records", "2 statistics=0 index=0 fields=0")),
            (
                "statistics",
                "statistics",
                "unreadable",
                ("statistics input unreadable", "2 statistics=unreadable index=0 fields=0"),
            ),
            (
                "statistics",
                "statistics",
                "unreadable-row",
                ("statistics record unreadable", "2 statistics=2 index=0 fields=0"),
            ),
            (
                "statistics",
                "statistics",
                "missing",
                ("statistics MAC membership missing=['aabbccddeeff'] extra=[]", "2 statistics=1 index=0 fields=0"),
            ),
            (
                "statistics",
                "statistics",
                "extra",
                ("statistics MAC membership missing=[] extra=['001122334455']", "2 statistics=3 index=0 fields=0"),
            ),
            ("statistics", "statistics", "invalid", ("statistics mac invalid", "2 statistics=2 index=0 fields=0")),
            (
                "statistics",
                "statistics",
                "duplicate",
                ("statistics mac duplicate aabbccddeeff", "2 statistics=2 index=0 fields=0"),
            ),
            (
                "statistics",
                "statistics",
                "normalized-duplicate",
                ("statistics mac duplicate aabbccddeeff", "2 statistics=2 index=0 fields=0"),
            ),
            (
                "statistics",
                "statistics",
                "mismatched",
                (
                    "statistics MAC membership missing=['aabbccddeeff'] extra=['001122334455']",
                    "2 statistics=2 index=0 fields=0",
                ),
            ),
            (
                "statistics",
                "statistics",
                "extra-field",
                (
                    "statistics fields for aabbccddeeff must be mac, version, status, ip, uptime",
                    "2 statistics=2 index=0 fields=4",
                ),
            ),
            ("index", "all", "empty", ("inventory zero records", "0 statistics=0 index=0 fields=0")),
            ("index", "inventory", "empty", ("inventory zero records", "0 statistics=0 index=2 fields=0")),
            (
                "index",
                "inventory",
                "unreadable",
                ("inventory input unreadable", "unreadable statistics=0 index=2 fields=0"),
            ),
            (
                "index",
                "inventory",
                "unreadable-row",
                ("inventory record unreadable", "2 statistics=0 index=2 fields=0"),
            ),
            ("index", "inventory", "invalid", ("inventory mac invalid", "2 statistics=0 index=2 fields=0")),
            (
                "index",
                "inventory",
                "duplicate",
                ("inventory mac duplicate aabbccddeeff", "2 statistics=0 index=2 fields=0"),
            ),
            (
                "index",
                "inventory",
                "normalized-duplicate",
                ("inventory mac duplicate aabbccddeeff", "2 statistics=0 index=2 fields=0"),
            ),
            (
                "index",
                "inventory",
                "missing-ip",
                ("inventory ip missing for aabbccddeeff", "2 statistics=0 index=2 fields=0"),
            ),
            ("index", "index", "empty", ("index zero records", "2 statistics=0 index=0 fields=0")),
            ("index", "index", "unreadable", ("index input unreadable", "2 statistics=0 index=unreadable fields=0")),
            (
                "index",
                "index",
                "unreadable-row",
                ("index record unreadable for aabbccddeeff", "2 statistics=0 index=2 fields=0"),
            ),
            (
                "index",
                "index",
                "missing",
                ("index MAC membership missing=['aabbccddeeff'] extra=[]", "2 statistics=0 index=1 fields=0"),
            ),
            (
                "index",
                "index",
                "extra",
                ("index MAC membership missing=[] extra=['001122334455']", "2 statistics=0 index=3 fields=0"),
            ),
            ("index", "index", "invalid", ("index mac invalid", "2 statistics=0 index=2 fields=0")),
            (
                "index",
                "index",
                "normalized-duplicate",
                ("index mac duplicate aabbccddeeff", "2 statistics=0 index=3 fields=0"),
            ),
            (
                "index",
                "index",
                "mismatched",
                (
                    "index MAC membership missing=['aabbccddeeff'] extra=['001122334455']",
                    "2 statistics=0 index=2 fields=0",
                ),
            ),
        ],
    )
    def test_membership_and_unreadable_inputs_fail(
        self, guard: str, target: str, damage: str, expected: tuple[str, str]
    ) -> None:
        """Every supplied defect raises its exact cause and measured input counts."""
        inputs = self.Inputs.valid()
        inventory, statistics, index = self.Inputs.damaged(inputs, target, damage)
        with pytest.raises(AssertionError) as failure:
            if guard == "statistics":
                CaptureStatisticsGuard.check(inventory, statistics, "0.15.1")
            else:
                CaptureIndexGuard.check(inventory, index, "0.15.1")
        reason, counts = expected
        assert str(failure.value) == f"{reason}. Checked inventory={counts}"

    @pytest.mark.parametrize("guard", ["statistics", "index"])
    @pytest.mark.parametrize(
        "field_case",
        [
            ("version", "", 0),
            ("version", "0.14.29216", 0),
            ("version", None, 0),
            ("version", "missing", 0),
            ("status", "", 1),
            ("status", "disconnected", 1),
            ("status", None, 1),
            ("status", "missing", 1),
            ("ip", "", 2),
            ("ip", "198.51.100.250", 2),
            ("ip", None, 2),
            ("ip", "missing", 2),
            ("uptime", "", 3),
            ("uptime", 0, 3),
            ("uptime", None, 3),
            ("uptime", "missing", 3),
        ],
    )
    def test_each_running_field_fails_with_its_checked_count(
        self, guard: str, field_case: tuple[str, object, int]
    ) -> None:
        """Empty, wrong, null, and missing fields must never pass a guard."""
        inputs = self.Inputs.valid()
        field, value, completed = field_case
        record = inputs.statistics[0] if guard == "statistics" else inputs.index["aabbccddeeff"]
        if value == "missing":
            record.pop(field)
        else:
            record[field] = value
        expected = {"version": "0.15.1", "status": "connected", "ip": "198.51.100.10", "uptime": 3600}
        with pytest.raises(AssertionError) as failure:
            if guard == "statistics":
                CaptureStatisticsGuard.check(inputs.inventory, inputs.statistics, "0.15.1")
            else:
                CaptureIndexGuard.check(inputs.inventory, inputs.index, "0.15.1")
        counts = "inventory=2 statistics=2 index=0" if guard == "statistics" else "inventory=2 statistics=0 index=2"
        assert str(failure.value) == (
            f"{guard} aabbccddeeff {field}: expected {expected[field]!r}, received {record.get(field)!r}. "
            f"Checked {counts} fields={completed}"
        )


class TestGlobalCaptureStatistics:
    """Require all five real global seeds, exact counts, and unchanged stored fields."""

    @pytest.fixture
    def capture_seeds(self, monkeypatch: pytest.MonkeyPatch) -> Iterator[DeviceIndexRecorder]:
        """Observe five genuine global builds without starting a browser or server."""
        from tests.e2e.upgrade_portal import conftest as seeds

        recorder = DeviceIndexRecorder()
        monkeypatch.setattr(devices, "build_device_index", recorder)
        logger.info("Read all five global capture seeds through the real device builder")
        recorder.captures = seeds.stand_in_capture_index()
        assert set(recorder.captures) == {
            capture_id for capture_id, _version in CaptureStatisticsGuard.SeedContract.VERSIONS
        }
        assert len(recorder.calls) == 5, f"Checked {len(recorder.calls)} real builder calls, expected five."
        logger.debug(
            "Read captures=%d real builder calls=%d inventory records=%d",
            len(recorder.captures),
            len(recorder.calls),
            sum(len(call.inventory) for call in recorder.calls),
        )
        yield recorder

    @pytest.mark.parametrize("capture_id,version", CaptureStatisticsGuard.SeedContract.VERSIONS)
    def test_global_statistics_and_inventory(
        self, capture_seeds: DeviceIndexRecorder, capture_id: str, version: str
    ) -> None:
        """Each unchanged inventory must supply three complete statistics records."""
        capture = capture_seeds.captures[capture_id]
        call = capture_seeds.call_for(capture)
        expected_inventory = [
            {
                "id": f"e2e-device-000{number}",
                "name": f"E2E {kind} {number}",
                "type": kind,
                "mac": f"00000000000{number}",
                "model": f"E2E-{kind.upper()}",
                "serial": f"E2ESERIAL000{number}",
                "ip": f"192.0.2.{number}",
                "version": version,
                "status": "connected",
                "site_id": "22222222-2222-2222-2222-222222222222",
            }
            for number, kind in enumerate(("ap", "gateway", "switch"), start=1)
        ]
        assert capture["devices"] == expected_inventory
        assert call.inventory == tuple(expected_inventory)
        checked = CaptureStatisticsGuard.check(call.inventory, call.statistics, version)
        assert str(checked) == "Checked inventory=3 statistics=3 index=0 fields=12"

    @pytest.mark.parametrize("capture_id,version", CaptureStatisticsGuard.SeedContract.VERSIONS)
    def test_global_index_fields(self, capture_seeds: DeviceIndexRecorder, capture_id: str, version: str) -> None:
        """All three real index entries must retain identity and explicit running fields."""
        capture = capture_seeds.captures[capture_id]
        call = capture_seeds.call_for(capture)
        assert set(call.index) == {"000000000001", "000000000002", "000000000003"}
        checked = CaptureIndexGuard.check(call.inventory, call.index, version)
        assert str(checked) == "Checked inventory=3 statistics=0 index=3 fields=12"
        for entry in call.index.values():
            assert {field: entry[field] for field in ("vc_role", "vc_mac", "num_members")} == {
                "vc_role": "standalone",
                "vc_mac": "",
                "num_members": 1,
            }

    @pytest.mark.parametrize("capture_id,version", CaptureStatisticsGuard.SeedContract.VERSIONS)
    def test_global_counts_and_preserved_metadata(
        self, capture_seeds: DeviceIndexRecorder, capture_id: str, version: str
    ) -> None:
        """The complete count map and all stored metadata must retain their contracts."""
        capture = capture_seeds.captures[capture_id]
        preserved = CaptureStatisticsGuard.SeedContract.PRESERVED
        CaptureStatisticsGuard.SeedContract.require_preserved(capture)
        tier3 = capture_id == "e2e-capture-tier3-0001"
        sections = assembly.CaptureSections(
            device_index=capture["device_index"], devices=capture["devices"], clients=capture["clients"]
        )
        counts = assembly.build_counts(sections)
        assert capture["counts"] == counts
        assert counts == {**preserved["counts"], "clients_guest": 1 if tier3 else 0}, (
            f"Checked capture={capture_id} inventory=3 index=3 count fields=9. "
            f"Expected total=3 connected=3 disconnected=0, received {counts}."
        )
        assert {record["version"] for record in capture["devices"]} == {version}

    def test_existing_pair_changes_three_versions_and_empty_site_stays_empty(
        self, capture_seeds: DeviceIndexRecorder
    ) -> None:
        """Preserve the empty site and require three actual version deltas."""
        from tests.e2e.upgrade_portal import conftest as seeds

        empty = seeds.stand_in_capture(
            "e2e-empty-statistics-proof", "pre", "0.14.29216", seeds.PRE_CAPTURE_STAMP, EMPTY_SITE_ID
        )
        capture_seeds.require_empty(empty)
        before, after = capture_seeds.captures["e2e-capture-pre-0001"], capture_seeds.captures["e2e-capture-post-0001"]
        comparison = diff.compare_devices(before, after)
        changed = diff.count_version_changes(comparison.deltas)
        assert (
            changed == 3
        ), f"Checked captures=2 device rows={len(comparison.deltas)}. Expected version changes=3, received {changed}."
        assert {delta.mac for delta in comparison.deltas} == {"000000000001", "000000000002", "000000000003"}
        assert {delta.outcome for delta in comparison.deltas} == {"changed"}
        for delta in comparison.deltas:
            assert [(change.field, change.before, change.after) for change in delta.changes] == [
                ("version", "0.14.29216", "0.15.1")
            ]
