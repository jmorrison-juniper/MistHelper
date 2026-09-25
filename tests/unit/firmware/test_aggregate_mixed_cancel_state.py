"""Unit tests for the operation state after a cancel that stopped part of the work.

Why:
    Issue #3371. After a cancel, an operation with one completed child job and
    one cancelled child job read completed. The status card then stated that
    the whole operation completed, and the history list showed a success word.
    One cancelled child job now makes a settled operation read cancelled. The
    access point job obeys the same rule for its sites. A failure still decides
    first.
"""

from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace
from typing import Any

import pytest

from src.firmware.aggregate_upgrade_service import AggregateBuildInput, AggregateUpgradeService
from src.firmware.org_upgrade_service import OrgUpgradeResult
from src.firmware.upgrade_service import CancelOutcome, DeviceTarget, UpgradeOptions

ORG_ID = "66666666-6666-6666-6666-666666666666"  # The organization of the operation.
SITE_ONE = "77777777-7777-7777-7777-777777777777"  # The first site of the operation.
SITE_TWO = "88888888-8888-8888-8888-888888888888"  # The second site of the operation.
SITES = (SITE_ONE, SITE_TWO)  # The site order of each access point status answer.
FIRST_AP_MAC = "001122334455"  # The access point of the first site.
SECOND_AP_MAC = "001122334477"  # The access point of the second site.
SWITCH_MAC = "001122334466"  # The switch of the first site.
READ_SESSION = SimpleNamespace(_MAX_429_RETRIES=0, _session=SimpleNamespace(adapters={}))  # A no-retry session.


class CasStore:
    """Keep one record behind a compare-and-set."""

    def __init__(self, record: dict[str, Any]) -> None:
        """Store one detached record."""
        self.record = deepcopy(record)  # The durable value.

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return one detached record, or None for another key."""
        return deepcopy(self.record) if self.record.get("run_id") == run_id else None  # Match the key.

    def compare_and_set_run(self, run_id: str, expected_version: int, replacement: dict[str, Any]) -> bool:
        """Replace the record only when its version matches."""
        if self.record.get("run_id") != run_id or self.record.get("record_version") != expected_version:
            return False  # A stale caller changes nothing.
        self.record = deepcopy(replacement)  # Store the detached replacement.
        return True  # Report the accepted change.


class CloudEdge:
    """Answer the cancel calls and the status reads of the organization edge and of the site edge."""

    ACCEPTED_STATUS = (200, 202)  # Match the production service contract.
    GatewayFamily = SimpleNamespace(SSR="ssr", JUNOS="junos")  # Supply the family values that the reader uses.

    def __init__(self, switch_word: str = "cancelled", site_words: tuple[str, ...] = ("completed",)) -> None:
        """Keep the words of the next status reads.

        Args:
            switch_word: The word of each status read of the site job.
            site_words: The site words of each status read of the access point job, in site order.
        """
        self.switch_word = switch_word  # The site job answers this word.
        self.site_words = site_words  # The access point job answers one entry for each word.
        self.calls: list[str] = []  # Each entry names one cloud call and its job.

    def status(self, session: Any, org_id: str, upgrade_id: str) -> OrgUpgradeResult:
        """Answer the access point job with one entry for each site and no root state."""
        del session  # The stand-in opens no socket.
        self.calls.append(f"status:{upgrade_id}")  # A test can read the order of the calls.
        entries = [{"site_id": SITES[index], "upgrade": {"status": word}} for index, word in enumerate(self.site_words)]
        return OrgUpgradeResult(org_id, upgrade_id, 200, {"id": upgrade_id, "site_upgrades": entries}, None)

    def cancel(self, session: Any, org_id: str, upgrade_id: str) -> OrgUpgradeResult:
        """Accept one organization cancel."""
        del session  # The stand-in opens no socket.
        self.calls.append(f"cancel:{upgrade_id}")  # A test can read the order of the calls.
        return OrgUpgradeResult(org_id, upgrade_id, 200, {}, None)  # The contract permits an empty body.

    def read_upgrade_status(self, session: Any, scope: str, identifier: str, upgrade_id: str, family: Any) -> dict:
        """Answer the site job with the fixed word."""
        del session, scope, identifier, family  # The fixed answer needs the job identifier only.
        self.calls.append(f"status:{upgrade_id}")  # A test can read the order of the calls.
        return {"raw_status": 200, "status": self.switch_word, "status_known": True, "targets": {}}

    def cancel_upgrade(self, session: Any, plan: Any, upgrade_id: str, status: Any) -> CancelOutcome:
        """Stop each device of one site job."""
        del session, status  # The fixed answer needs the plan targets only.
        self.calls.append(f"cancel:{upgrade_id}")  # A test can read the order of the calls.
        return CancelOutcome(tuple(device.mac for device in plan.targets), (), (), "The cloud stopped the job.")


def running_operation(service: AggregateUpgradeService, states: dict[str, str]) -> dict[str, Any]:
    """Build one running operation whose two child jobs reached the cloud.

    Args:
        service: The production service with the cloud stand-in.
        states: The stored state of the child job of each family, "ap" and "switch".

    Returns:
        The record, as the store holds it after the last status read.
    """
    sites = ({"site_id": SITE_ONE, "name": "One"}, {"site_id": SITE_TWO, "name": "Two"})  # Two approved sites.
    targets = (  # One access point at each site and one switch, so the operation holds two child jobs.
        DeviceTarget(FIRST_AP_MAC, "ap-one", "ap", "AP45", "0.14.1", "0.15.1", SITE_ONE),
        DeviceTarget(SECOND_AP_MAC, "ap-two", "ap", "AP45", "0.14.1", "0.15.1", SITE_TWO),
        DeviceTarget(SWITCH_MAC, "switch-one", "switch", "EX4400", "23.4R1.8", "23.4R1.9", SITE_ONE),
    )
    record = service.build(AggregateBuildInput("owner", ORG_ID, sites, targets, UpgradeOptions(), "nonce"))
    for child in record["children"]:  # Each child job holds a cloud job.
        child["upgrade_id"] = f"job-{child['device_family']}"  # The cloud identity of the child job.
        child["status"] = states[child["device_family"]]  # The state of the last status read.
    record["state"] = "running"  # One child job still runs, so the operation takes a cancel.
    return record


def child_of(store: CasStore, family: str) -> dict[str, Any]:
    """Return the stored child job of one family."""
    return next(child for child in store.record["children"] if child["device_family"] == family)  # One family.


@pytest.mark.parametrize(
    ("states", "word"),
    [
        (("completed", "cancelled"), "cancelled"),
        (("cancelled", "completed"), "cancelled"),
        (("completed", "completed"), "completed"),
        (("cancelled", "cancelled"), "cancelled"),
        (("completed", "cancelled", "failed"), "failed"),
        (("completed", "cancelled", "rejected"), "failed"),
        (("completed", "cancelled", "not_submitted"), "attention_required"),
        (("completed", "running"), "running"),
        (("cancelled", "running", "failed"), "partial"),
    ],
)
def test_each_set_of_child_states_maps_to_one_operation_word(states: tuple[str, ...], word: str) -> None:
    """One cancelled child job makes a settled operation read cancelled, and a failure still decides first."""
    record = {"children": [{"status": state} for state in states]}  # One child job for each state.
    assert AggregateUpgradeService._aggregate_state(record) == word  # The word that the page prints.


@pytest.mark.parametrize(("switch_word", "word"), [("cancelled", "cancelled"), ("completed", "completed")])
def test_the_status_read_after_the_cancel_stores_the_word_of_the_whole_operation(switch_word: str, word: str) -> None:
    """The cancel stops the running switch job, and the next status read stores the operation word."""
    edge = CloudEdge(switch_word=switch_word)  # The cloud edge of both child job families.
    service = AggregateUpgradeService(edge, edge)  # The production cancel and status read.
    store = CasStore(running_operation(service, {"ap": "completed", "switch": "running"}))  # The durable store.
    service.cancel(READ_SESSION, deepcopy(store.record), store)  # The operator sends the typed cancel.
    after_cancel = store.record["state"]  # The switch job reads running until the next status read.
    service.status(READ_SESSION, deepcopy(store.record), store)  # The page poll reads the switch job again.
    assert edge.calls == ["cancel:job-switch", "status:job-switch"]  # The completed job got no call.
    assert (after_cancel, store.record["state"]) == ("running", word)  # A stopped job decides the word.


@pytest.mark.parametrize(
    ("site_words", "word"),
    [
        (("completed", "cancelled"), "cancelled"),
        (("success", "cancelled"), "cancelled"),
        (("cancelled", "cancelled"), "cancelled"),
        (("completed", "success"), "completed"),
        (("completed", "failed"), "failed"),
    ],
)
def test_each_site_mix_of_the_access_point_job_maps_to_one_word(site_words: tuple[str, ...], word: str) -> None:
    """One cancelled site makes the access point job read cancelled, and a failed site still decides first."""
    result = CloudEdge(site_words=site_words).status(READ_SESSION, ORG_ID, "job-ap")  # No root state.
    assert AggregateUpgradeService._org_status(result) == word  # The word of the access point job.


def test_an_access_point_job_that_stopped_at_one_site_makes_the_operation_read_cancelled() -> None:
    """The access point job completed at one site and stopped at the other site."""
    edge = CloudEdge(site_words=("completed", "cancelled"))  # The cancel stopped the second site.
    service = AggregateUpgradeService(edge, edge)  # The production status read.
    store = CasStore(running_operation(service, {"ap": "running", "switch": "completed"}))  # The durable store.
    service.status(READ_SESSION, deepcopy(store.record), store)  # The page poll reads the access point job.
    assert edge.calls == ["status:job-ap"]  # The completed switch job got no read.
    assert (child_of(store, "ap")["status"], store.record["state"]) == ("cancelled", "cancelled")  # One rule.
