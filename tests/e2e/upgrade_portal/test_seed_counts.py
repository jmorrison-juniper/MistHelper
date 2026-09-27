"""Direct test of issue #3492: each browser seed capture holds the count map of a real capture.

Why:
    Issue #3492. The seed captures of the browser tests wrote a count map of
    three keys by hand. A real capture holds the nine keys of the shipped
    function `build_counts`, and three of those keys count the devices of each
    type. The history page found no type count in a seed, so each seed row
    read "No device type". The Tier 3 seed also counted no guest client.

    This module reads the five seeds with no browser. It builds each count map
    again with the shipped builder. It also replaces the builder with a marker,
    which proves that the seed file calls the builder and writes no count by
    hand. The session fixture of the folder still starts the browser test
    server, so the CI job "E2E smoke tests" runs this module.
"""

from __future__ import annotations

import logging
from typing import Any

import pytest

# WHY: Issue #2241. Each module of this folder carries its own skip, and the
# unit test `test_e2e_strict_guard.py` proves that rule. The session fixture of
# the folder starts the browser test server, so a workstation with no browser
# package skips this module together with the rest of the folder.
pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")

from src.upgrade_portal.capture import assembly  # WHY: The skip above runs first.
from tests.e2e.upgrade_portal.conftest import (  # WHY: The skip above runs first.
    POST_CAPTURE_ID,
    PRE_CAPTURE_ID,
    STANDALONE_PRE_CAPTURE_ID,
    STORED_POLL_CAPTURE_ID,
    TIER3_CAPTURE_ID,
    stand_in_capture_index,
)

logger = logging.getLogger(__name__)

SEED_CAPTURE_IDS = (  # The five seed captures, in the order of the seed stamps.
    PRE_CAPTURE_ID,
    STANDALONE_PRE_CAPTURE_ID,
    POST_CAPTURE_ID,
    STORED_POLL_CAPTURE_ID,
    TIER3_CAPTURE_ID,
)
TYPE_COUNTS = {"gateways": 1, "switches": 1, "access_points": 1}  # One device of each type in each seed.
TIER3_CLIENT_COUNTS = {"clients_wired": 0, "clients_wireless": 3, "clients_guest": 1}  # Three radios, one guest.
MARKER_COUNTS = {"marker_count": 7}  # A map that no real builder writes, so a hand-written map cannot match it.


def builder_counts(seed: dict[str, Any]) -> dict[str, int]:
    """Build the count map of one seed again with the shipped builder.

    Args:
        seed: One seed capture document.

    Returns:
        The nine counts that a real capture of the same lists holds.
    """
    logger.info("Build the count map of %s with the shipped builder", seed["capture_id"])  # Log before the build.
    sections = assembly.CaptureSections(  # The three parts of a capture that the builder reads.
        device_index=seed["device_index"],  # The joined type and state of each device.
        devices=seed["devices"],  # The device records of the site.
        clients=seed["clients"],  # The wired, the wireless, and the guest client lists.
    )
    counts = assembly.build_counts(sections)  # The writer of the count map of a real capture.
    logger.debug("The builder gives %s for %s", counts, seed["capture_id"])  # Log after the build.
    return counts  # The caller compares this map with the stored map of the seed.


@pytest.mark.parametrize("capture_id", SEED_CAPTURE_IDS)
def test_each_seed_holds_the_count_map_of_the_builder(capture_id: str) -> None:
    """FR-001 and SC-002: the count map of each seed equals the builder output, key for key."""
    seed = stand_in_capture_index()[capture_id]  # The seed that the browser test server stores.
    stored = seed["counts"]  # The count map that the history page and the capture page read.
    assert list(stored) == list(assembly.COUNT_KEYS), f"{capture_id}: the count keys are {list(stored)}"  # Nine keys.
    assert stored == builder_counts(seed), f"{capture_id}: the count map is {stored}"  # The shape of a real capture.
    logger.debug("The seed %s holds the count map of the builder", capture_id)  # Log after the compare.


@pytest.mark.parametrize("capture_id", SEED_CAPTURE_IDS)
def test_each_seed_counts_one_device_of_each_type(capture_id: str) -> None:
    """FR-004: each seed counts one gateway, one switch, and one access point."""
    stored = stand_in_capture_index()[capture_id]["counts"]  # The count map of the seed.
    types = {name: stored.get(name) for name in TYPE_COUNTS}  # The three counts that the Device types cell reads.
    assert types == TYPE_COUNTS, f"{capture_id}: the type counts are {types}"  # One device of each type.
    logger.debug("The seed %s counts one device of each type", capture_id)  # Log after the compare.


def test_the_tier3_seed_counts_its_guest_client() -> None:
    """FR-003: the Tier 3 seed builds its count map after it adds the guest client."""
    seed = stand_in_capture_index()[TIER3_CAPTURE_ID]  # The one seed with a guest client.
    assert len(seed["clients"]["guest"]) == 1, "The Tier 3 seed holds no guest client."  # The stored list.
    clients = {name: seed["counts"].get(name) for name in TIER3_CLIENT_COUNTS}  # The three client counts.
    assert clients == TIER3_CLIENT_COUNTS, f"The Tier 3 client counts are {clients}"  # The guest client counts too.
    logger.debug("The Tier 3 seed counts %s clients", sum(TIER3_CLIENT_COUNTS.values()))  # Log after the compare.


def test_the_seed_file_writes_no_count_by_hand(monkeypatch: pytest.MonkeyPatch) -> None:
    """FR-002: a replaced builder reaches each seed, so no seed holds a map that the file wrote by hand."""
    calls: list[assembly.CaptureSections] = []  # Each call that the seed file makes to the builder.

    def marker_builder(sections: assembly.CaptureSections) -> dict[str, int]:
        """Record one call, and return the marker map."""
        calls.append(sections)  # The test counts the calls after the build.
        return dict(MARKER_COUNTS)  # A fresh copy, so no seed shares one map object.

    logger.info("Replace the shipped builder with the marker builder")  # Log before the build of the seeds.
    monkeypatch.setattr(assembly, "build_counts", marker_builder)  # The seed file reads the module name late.
    seeds = stand_in_capture_index()  # Each seed builds its count map with the marker builder.
    held = {capture_id: seeds[capture_id]["counts"] for capture_id in SEED_CAPTURE_IDS}  # The five maps.
    assert all(counts == MARKER_COUNTS for counts in held.values()), f"A seed wrote a map by hand: {held}"
    assert len(calls) >= len(SEED_CAPTURE_IDS), f"The builder ran {len(calls)} times."  # One call or more per seed.
    logger.debug("The seed file called the builder %s times", len(calls))  # Log after the compare.
