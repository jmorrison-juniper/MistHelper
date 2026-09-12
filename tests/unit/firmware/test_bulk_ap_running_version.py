"""Test the running-version rule that the bulk access point upgrader applies.

Issue #2253 found the rule in three places. `RunningFirmwareVersionResolver`
holds it, and two upgraders repeated it with their own code. Every copy was
correct at the time, and the risk was drift: a correction would reach the
resolver and miss the copies.

Warning: a firmware decision that reads a stale version can skip a device that
still needs the firmware, or plan a release the device already runs. Issue #2006
records the defect that produced this rule.

These tests lock two things. The upgrader reads the shared resolver, and a device
with no reading from a running-version endpoint never reaches an upgrade verdict
as though its version were known.
"""

from __future__ import annotations

import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.firmware.bulk_ap_upgrader import UNKNOWN_VERSION, BulkAPFirmwareUpgrader, BulkAPUpgraderConfig
from src.firmware.running_version import RunningFirmwareVersionResolver

# The identifiers of one access point. The stats row and the device row do not
# always share a field, so the resolver accepts the id, the device_id, and the MAC.
_DEVICE_ID = "00000000-0000-0000-0000-00000000ab01"
_DEVICE_MAC = "5c5b350000a1"
_RUNNING_VERSION = "0.14.29695"

# The value that a device listing carries. It names the configured version, which
# can be a release the device left long ago.
_STALE_VERSION = "0.10.17000"


@pytest.fixture(name="upgrader")
def fixture_upgrader() -> Any:
    """Build one upgrader with a stand-in session and no network reach."""
    logging.info("Building a bulk access point upgrader for the version rule tests")  # Report the build.
    config = BulkAPUpgraderConfig(org_id="org-0001", apisession=MagicMock())
    built = BulkAPFirmwareUpgrader(config)  # The constructor builds the resolver.
    logging.debug("The upgrader holds a resolver of type %s", type(built._version_resolver).__name__)
    return built


class TestTheUpgraderReadsTheSharedRule:
    """Issue #2253: one reader holds the running-version rule."""

    def test_the_upgrader_holds_the_shared_resolver(self, upgrader: Any) -> None:
        """The upgrader MUST hold the shared resolver, and not a copy of its rule."""
        logging.info("Checking that the upgrader holds the shared resolver")  # Report the plan.

        assert isinstance(upgrader._version_resolver, RunningFirmwareVersionResolver)

    def test_the_index_answers_the_shared_join_map(self, upgrader: Any) -> None:
        """The index MUST answer the same map that the resolver builds."""
        logging.info("Checking the index against the shared reader")  # Report the plan.
        rows = [{"id": _DEVICE_ID, "mac": _DEVICE_MAC, "version": _RUNNING_VERSION}]

        built = upgrader._index_stats_by_device_id(rows)  # The upgrader path.
        shared = RunningFirmwareVersionResolver.index_stats_rows(rows)  # The shared reader.
        logging.debug("The index answered %d keys", len(built))  # Record the size.

        assert built == shared, "the upgrader must answer the map that the shared reader builds"

    @pytest.mark.parametrize("key", ["id", "device_id", "mac"])
    def test_the_index_accepts_every_join_key(self, upgrader: Any, key: str) -> None:
        """A stats row MUST join on any of the three identifier fields."""
        logging.info("Checking the join key %s", key)  # Report the plan before the work.

        built = upgrader._index_stats_by_device_id([{key: _DEVICE_ID, "version": _RUNNING_VERSION}])

        assert built.get(_DEVICE_ID) == _RUNNING_VERSION, f"the index must join on {key}"


class TestAStaleReadingNeverBecomesAVersion:
    """A value that no running-version endpoint reported must not look like one."""

    def test_the_running_version_reaches_the_caller(self, upgrader: Any) -> None:
        """A stats row MUST give its version to the caller."""
        logging.info("Checking the running version path")  # Report the plan before the work.
        lookup = {_DEVICE_ID: _RUNNING_VERSION}  # The stats endpoint named this device.

        answer = upgrader._get_ap_version({"id": _DEVICE_ID, "mac": _DEVICE_MAC}, lookup)

        assert answer == _RUNNING_VERSION, "a running reading must reach the caller"

    def test_the_mac_address_also_reaches_the_running_version(self, upgrader: Any) -> None:
        """A stats row keyed by MAC MUST still reach the device row."""
        logging.info("Checking the MAC join of the version read")  # Report the plan.
        lookup = {_DEVICE_MAC: _RUNNING_VERSION}  # The stats row carried a MAC and no id.

        answer = upgrader._get_ap_version({"id": _DEVICE_ID, "mac": _DEVICE_MAC}, lookup)

        assert answer == _RUNNING_VERSION, "the MAC address must join the two rows"

    def test_a_device_with_no_stats_row_reads_as_unknown(self, upgrader: Any) -> None:
        """A device that no stats row names MUST read as unknown.

        Why:
            No running-version endpoint reported this device, so the portal
            cannot state the version it runs.
        """
        logging.info("Checking a device that no stats row names")  # Report the plan.

        answer = upgrader._get_ap_version({"id": _DEVICE_ID, "mac": _DEVICE_MAC}, {})

        assert answer == UNKNOWN_VERSION, "a device with no stats row cannot name a version"

    def test_the_listing_version_never_reaches_the_caller(self, upgrader: Any) -> None:
        """The configured version of a device row MUST NOT reach the caller.

        Why:
            Issue #2006. `listSiteDevices` reports the configured version, which
            can name a release the device left long ago. The resolver marks such
            a reading stale, and the upgrader must refuse it.
        """
        logging.info("Checking that the listing version stays out of the verdict")  # Report the plan.
        row = {"id": _DEVICE_ID, "mac": _DEVICE_MAC, "version": _STALE_VERSION}  # A listing row.

        answer = upgrader._get_ap_version(row, {})  # No stats row exists for this device.

        assert answer != _STALE_VERSION, "a configured version must never reach a firmware verdict"
        assert answer == UNKNOWN_VERSION, "a stale reading must read as unknown"


class TestAnUnknownVersionStaysInTheUpgradeBucket:
    """A device the portal cannot read must never look like a finished one."""

    def test_an_unknown_device_needs_the_upgrade(self, upgrader: Any) -> None:
        """A device with no readable version MUST land in the upgrade bucket.

        Why:
            The already-at-target bucket skips the device. A skip on a value that
            no endpoint confirmed leaves production hardware on old firmware, and
            the operator reads the run as complete.
        """
        logging.info("Checking the partition of a device with no readable version")  # Report the plan.
        devices = [{"id": _DEVICE_ID, "mac": _DEVICE_MAC}]  # One device with no entry in ap_versions.

        needing, at_target = upgrader._partition_devices_by_version(devices, _RUNNING_VERSION)
        logging.debug("The partition put %d in upgrade and %d at target", len(needing), len(at_target))

        assert needing == devices, "an unreadable device must stay in the upgrade bucket"
        assert at_target == [], "an unreadable device must never read as already at target"

    def test_a_device_at_the_target_is_skipped(self, upgrader: Any) -> None:
        """A device whose running version matches the target MUST be skipped."""
        logging.info("Checking the partition of a device already at the target")  # Report the plan.
        upgrader.ap_versions[_DEVICE_ID] = _RUNNING_VERSION  # A running reading placed this value.
        devices = [{"id": _DEVICE_ID, "mac": _DEVICE_MAC}]

        needing, at_target = upgrader._partition_devices_by_version(devices, _RUNNING_VERSION)

        assert needing == [], "a device at the target needs no upgrade"
        assert at_target == devices, "a device at the target belongs in the skip bucket"

    def test_the_whole_read_path_keeps_an_unread_device_in_the_upgrade_bucket(self, upgrader: Any) -> None:
        """The read and the partition together MUST protect an unread device.

        Why:
            The two steps run one after the other in the real flow. This test
            drives both, so no future change can pass one and break the pair.
        """
        logging.info("Checking the read and the partition together")  # Report the plan.
        access_point = {"id": _DEVICE_ID, "mac": _DEVICE_MAC, "version": _STALE_VERSION}
        upgrader.all_aps = [access_point]  # The listing named one device.

        upgrader._process_aps_with_stats({})  # No stats row exists, so nothing confirms a version.
        needing, at_target = upgrader._partition_devices_by_version([access_point], _STALE_VERSION)
        logging.debug("The recorded version is %r", upgrader.ap_versions.get(_DEVICE_ID))

        assert upgrader.ap_versions[_DEVICE_ID] == UNKNOWN_VERSION, "the stale value must not be recorded"
        assert needing == [access_point], "the device must stay in the upgrade bucket"
        assert at_target == [], "the stale value must not skip the device"
