"""Test the seed module that holds the two stale runs of the bulk tests.

Why:
    Issue #3507. The two stale seed runs sat on the first site of the picker,
    so the create call of each later journey met them. The seed module now
    writes both runs on a site of their own. These tests prove the site, the
    live state, the fields that the bulk tests read, and the result of the
    write.
"""

from __future__ import annotations  # Keep the annotations independent from the import order.

import logging  # Read the log lines of the write, and record each step of the tests.
from typing import Any  # The records hold JSON values of mixed types.

import pytest  # The parameters of the write tests and the log capture.

from src.interfaces.portals.upgrade_portal.app.routes.upgrade import run_is_live  # The shipped rule of the site scan.
from tests.e2e.upgrade_portal.stale_run_seeds import (  # Issue #3507: the module under test.
    STALE_PRE_CLOUD_RUN_ID,
    STALE_SITE_ID,
    STALE_SITE_NAME,
    STALE_STOPPING_RUN_ID,
    StaleRunSeeds,
)

logger = logging.getLogger(__name__)  # Keep the records of this module under one name.

SEED_LOGGER = "tests.e2e.upgrade_portal.stale_run_seeds"  # The logger name of the module under test.
ORG_ID = "11111111-1111-1111-1111-111111111111"  # The stand-in organization of the browser server.
FIRST_SITE_ID = "22222222-2222-2222-2222-222222222222"  # The first site of the picker.
OLD_UPDATE_TIME = "2026-09-01T10:00:00+00:00"  # The old update time that makes both runs stale.


class ScriptedUpgrade:
    """Stand in for the upgrade route module, and answer each save from a script."""

    def __init__(self, answers: list[bool]) -> None:
        """Keep the answers in call order, and start with no saved key."""
        self.answers = list(answers)  # A copy, so the parameter list stays whole for the next case.
        self.saved: list[str] = []  # The key of each record that the write sent, in call order.

    def save_run(self, record: dict[str, Any]) -> bool:
        """Keep the key of one record, and return the next scripted answer."""
        self.saved.append(str(record["run_id"]))  # The test reads which records the write sent.
        return self.answers.pop(0)  # The store accepts or refuses this record.


class TestTheStaleRecords:
    """Both records hold the stale site, a live state, and the fields that the bulk tests read."""

    def test_both_records_hold_the_stale_site(self) -> None:
        """Each record MUST name the stale site, its name, and the organization of the caller."""
        logger.info("Read the site of each stale record")  # Log the plan.
        records = StaleRunSeeds.records(ORG_ID)  # Both records, in write order.
        assert [record["run_id"] for record in records] == [STALE_PRE_CLOUD_RUN_ID, STALE_STOPPING_RUN_ID]
        assert {record["site_id"] for record in records} == {STALE_SITE_ID}  # One site for both runs.
        assert {record["site_name"] for record in records} == {STALE_SITE_NAME}  # The history page shows it.
        assert {record["org_id"] for record in records} == {ORG_ID}  # The lock key needs the organization.

    def test_the_stale_site_is_not_the_first_site(self) -> None:
        """The stale site MUST differ from the first site, which each create journey reads."""
        logger.info("Compare the stale site with the first site of the picker")  # Log the plan.
        assert STALE_SITE_ID != FIRST_SITE_ID  # A shared site blocks each create call on the first site.

    def test_both_records_are_live(self) -> None:
        """Both records MUST be live, because the bulk cancel and the reconcile act on a live run only."""
        logger.info("Read the live state of each stale record")  # Log the plan.
        assert [run_is_live(record) for record in StaleRunSeeds.records(ORG_ID)] == [True, True]

    def test_an_empty_record_is_not_live(self) -> None:
        """An empty record MUST read as not live, so the live check of both records can fail."""
        logger.info("Read the live state of an empty record")  # Log the plan.
        assert run_is_live({}) is False  # A record with no state blocks no create call.

    def test_the_pre_cloud_record_keeps_its_fields(self) -> None:
        """The pre-cloud record MUST keep the state and the old update time of the bulk cancel."""
        logger.info("Read the fields of the pre-cloud record")  # Log the plan.
        record = StaleRunSeeds.pre_cloud_record(ORG_ID)  # The run that the bulk cancel ends.
        assert record["state"] == "awaiting_confirmation"  # A state before the cloud, so a cancel applies.
        assert record["updated_at"] == OLD_UPDATE_TIME  # The old time makes the run stale.
        assert (record["targets"], record["options"]) == ([], {})  # The cancel reads no target.

    def test_the_stopping_record_names_the_scripted_task(self) -> None:
        """The stopping record MUST name the target and the task of the scripted reconcile evidence."""
        logger.info("Read the fields of the stopping record")  # Log the plan.
        record = StaleRunSeeds.stopping_record(ORG_ID)  # The run that the reconcile test settles.
        assert record["state"] == "stopping"  # The one state that offers the reconcile control.
        assert record["updated_at"] == OLD_UPDATE_TIME  # The old time makes the run stale.
        assert record["targets"] == [{"device_id": "e2e-target-one", "cloud_task_id": "e2e-task-one"}]


class TestTheWrite:
    """The write sends both records and reports each answer of the store."""

    @pytest.mark.parametrize(
        ("answers", "expected"),
        [([True, True], True), ([True, False], False), ([False, True], False), ([False, False], False)],
        ids=["both-accepted", "stopping-refused", "pre-cloud-refused", "both-refused"],
    )
    def test_the_write_reports_each_store_answer(self, answers: list[bool], expected: bool) -> None:
        """The write MUST send both records, and it MUST report False when the store refuses one."""
        logger.info("Write both stale records against the answers %s", answers)  # Log the plan.
        upgrade = ScriptedUpgrade(answers)  # The store that answers from the script.
        assert StaleRunSeeds.write(upgrade, ORG_ID) is expected  # One result for both saves.
        assert upgrade.saved == [STALE_PRE_CLOUD_RUN_ID, STALE_STOPPING_RUN_ID]  # A refusal stops no later save.

    def test_the_write_logs_one_line_before_and_one_line_after(self, caplog: pytest.LogCaptureFixture) -> None:
        """The write MUST log one info line before the saves and one debug line after them."""
        logger.info("Write both stale records, and read the log lines of the write")  # Log the plan.
        caplog.set_level(logging.DEBUG, logger=SEED_LOGGER)  # Keep each level of the module under test.
        StaleRunSeeds.write(ScriptedUpgrade([True, True]), ORG_ID)  # One write that the store accepts.
        levels = [record.levelno for record in caplog.records if record.name == SEED_LOGGER]  # Each line.
        assert levels == [logging.INFO, logging.DEBUG]  # One line before the saves and one line after them.
