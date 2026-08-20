"""Proof that the portal marks a device that returns on the wrong firmware.

Why:
    FR-051 states the rule: a device that returns on a version that is not the
    requested version must read as a version mismatch. Before this check, the
    run recorded the version a device reported after the upgrade and compared
    it against nothing. A device that stayed on its old firmware therefore read
    as a success, and an operator learned about it only from a later capture.

    Three states matter, and the tests keep them apart:

    1. The reported version equals the requested version. The run did what the
       operator asked.
    2. The reported version differs. This is the defect FR-051 names.
    3. The device reports no version yet. It is still settling. A portal that
       called this a mismatch would send an operator to a healthy device.

    The tests also pin the normalization, because the run page repeats the same
    rule with the Jinja filters `trim` and `lower`. A rule that lived in one
    place only would let the page and the code disagree without any warning.
"""

from __future__ import annotations

import pytest

from src.upgrade_portal.runtime.runs import RunStatusView
from src.upgrade_portal.upgrade import gate

# WHY: Two real firmware versions from the same train. They differ only after
# the fourth character, so a loose comparison would call them equal.
VERSION_TARGET = "23.4R2-S3.9"
VERSION_OLD = "23.4R2.13"

# WHY: A MAC address in the stored form, so every row of these tests reads a
# real value.
DEVICE_MAC = "0011220000aa"

# WHY: Every value that means "the device reported nothing". A null arrives from
# the run record, and whitespace arrives from a record the cloud half filled.
ABSENT_VALUES = (None, "", "   ", "\t\n")


def row(version_target: object, version_after: object) -> dict[str, object]:
    """Build one target row of a run record with the two version fields.

    Why:
        Every row test needs the same two keys under their real names. One
        builder keeps the field names in a single place, so a rename breaks one
        line instead of ten.

    Args:
        version_target: The version the operator picked.
        version_after: The version the device reports.

    Returns:
        One target row with a MAC address and the two version fields.
    """
    return {"mac": DEVICE_MAC, "version_target": version_target, "version_after": version_after}


def test_the_three_tokens_hold_the_contract_words() -> None:
    """The outcome tokens read exactly as the page and the contract expect."""
    assert gate.OUTCOME_VERSION_MATCH == "version_match"  # The page maps this token to a badge.
    assert gate.OUTCOME_VERSION_MISMATCH == "version_mismatch"  # FR-051 names this token.
    assert gate.OUTCOME_VERSION_PENDING == "version_pending"  # The third state is its own token.


def test_the_field_names_match_the_run_record() -> None:
    """The gate reads the same field names the run status body publishes.

    Why:
        The gate reads a target row that another module writes. A field name
        that drifted would make every comparison answer "pending" for ever, and
        no test that built its own row would catch it.
    """
    assert gate.FIELD_VERSION_TARGET in RunStatusView.TARGET_FIELDS  # The requested version.
    assert gate.FIELD_VERSION_AFTER in RunStatusView.TARGET_FIELDS  # The reported version.


def test_an_exact_match_is_not_a_mismatch() -> None:
    """A device that returns on the requested version reads as a match."""
    outcome = gate.version_outcome(VERSION_TARGET, VERSION_TARGET)  # Both values are identical.
    assert outcome == gate.OUTCOME_VERSION_MATCH  # The upgrade did what the operator asked.
    assert outcome != gate.OUTCOME_VERSION_MISMATCH  # FR-051 must raise no alarm here.


def test_a_different_version_is_a_mismatch() -> None:
    """A device that returns on its old firmware reads as a version mismatch.

    Why:
        This is the defect FR-051 names. The device answered the upgrade call
        and then stayed where it was.
    """
    outcome = gate.version_outcome(VERSION_TARGET, VERSION_OLD)  # The device kept its old firmware.
    assert outcome == gate.OUTCOME_VERSION_MISMATCH  # The portal must mark this device.


@pytest.mark.parametrize("reported", ABSENT_VALUES)
def test_a_missing_reported_version_is_neither(reported: object) -> None:
    """A device with no reported version is settling, never a mismatch.

    Args:
        reported: One value that means the device reported nothing.
    """
    outcome = gate.version_outcome(VERSION_TARGET, reported)  # The cloud has not filled the reading.
    assert outcome == gate.OUTCOME_VERSION_PENDING  # The third state, kept apart from the other two.
    assert outcome != gate.OUTCOME_VERSION_MISMATCH  # No alarm while the device is still settling.
    assert outcome != gate.OUTCOME_VERSION_MATCH  # An absent reading proves no match either.


@pytest.mark.parametrize("requested", ABSENT_VALUES)
def test_a_missing_requested_version_is_neither(requested: object) -> None:
    """A row with no requested version proves nothing about the device.

    Why:
        The rule follows `uptime_decreased`: an absent value is no evidence.
        A portal that compared a real reading against an empty request would
        report every device as wrong.

    Args:
        requested: One value that means the row holds no requested version.
    """
    outcome = gate.version_outcome(requested, VERSION_TARGET)  # The row lost the choice of the operator.
    assert outcome == gate.OUTCOME_VERSION_PENDING  # No request, so no verdict.


def test_normalization_ignores_surrounding_whitespace() -> None:
    """A reading with surrounding whitespace still matches the request."""
    padded = f"  {VERSION_TARGET}\t\n"  # A record the cloud returned with padding.
    assert gate.version_outcome(VERSION_TARGET, padded) == gate.OUTCOME_VERSION_MATCH  # Padding is not a change.


def test_normalization_ignores_case() -> None:
    """A reading in a different case still matches the request."""
    shouted = VERSION_TARGET.upper()  # `23.4R2-S3.9` becomes `23.4R2-S3.9` in full upper case.
    quiet = VERSION_TARGET.lower()  # The same version in full lower case.
    assert gate.version_outcome(shouted, quiet) == gate.OUTCOME_VERSION_MATCH  # Case is not a change.


def test_normalization_keeps_every_inner_character() -> None:
    """The rule removes no inner character, so two close versions stay apart.

    Why:
        A rule that stripped punctuation or inner spaces would call two real
        firmware versions equal and would hide the very defect FR-051 names.
    """
    assert gate.version_outcome(VERSION_TARGET, VERSION_OLD) == gate.OUTCOME_VERSION_MISMATCH  # Same train.
    assert gate.version_outcome("23.4 R2", "23.4R2") == gate.OUTCOME_VERSION_MISMATCH  # An inner space counts.


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, ""),
        ("", ""),
        ("   ", ""),
        ("  23.4R2.13  ", "23.4r2.13"),
        ("23.4R2-S3.9", "23.4r2-s3.9"),
        ("23.4R2-S3.9\r\n", "23.4r2-s3.9"),
    ],
)
def test_normalize_version_returns_the_pinned_form(raw: object, expected: str) -> None:
    """The normalization removes surrounding whitespace and case, and no more.

    Args:
        raw: The value as it arrives from a record or from a browser.
        expected: The one form every comparison in the portal reads.
    """
    assert gate.normalize_version(raw) == expected  # The page repeats this rule with `trim` and `lower`.


def test_version_matches_answers_true_only_on_a_match() -> None:
    """The boolean reader agrees with the token reader on every state."""
    assert gate.version_matches(VERSION_TARGET, VERSION_TARGET) is True  # The one true case.
    assert gate.version_matches(VERSION_TARGET, VERSION_OLD) is False  # A mismatch is not a match.
    assert gate.version_matches(VERSION_TARGET, None) is False  # An absent reading proves no match.


def test_version_matches_refuses_two_absent_values() -> None:
    """Two empty values never match, because no reading proves no match.

    Why:
        A plain string comparison would answer True for two empty values and
        would mark an untouched device as a success.
    """
    assert gate.version_matches("", "") is False  # Nothing equals nothing, but nothing is not a match.
    assert gate.version_matches(None, None) is False  # A null pair carries no evidence either.


def test_target_version_outcome_reads_the_row_fields() -> None:
    """The row reader finds both versions on one target row of the run."""
    assert gate.target_version_outcome(row(VERSION_TARGET, VERSION_OLD)) == gate.OUTCOME_VERSION_MISMATCH
    assert gate.target_version_outcome(row(VERSION_TARGET, VERSION_TARGET)) == gate.OUTCOME_VERSION_MATCH
    assert gate.target_version_outcome(row(VERSION_TARGET, None)) == gate.OUTCOME_VERSION_PENDING


def test_target_version_outcome_treats_an_absent_field_as_pending() -> None:
    """A row that holds neither field reads as pending, and raises nothing.

    Why:
        The run writes a target row before the upgrade starts, so the reported
        version is absent for most of the run. A reader that raised there would
        break the run page at the moment an operator watches it.
    """
    assert gate.target_version_outcome({}) == gate.OUTCOME_VERSION_PENDING  # An empty row proves nothing.
    assert gate.target_version_outcome({"mac": DEVICE_MAC}) == gate.OUTCOME_VERSION_PENDING  # Neither field.


def test_the_module_exports_every_new_name() -> None:
    """Every name FR-051 adds joins the public list of the gate module.

    Why:
        A caller in another module reads the public list. A name that is absent
        from that list reads as private, and a later cleanup could remove it.
    """
    added = {
        "FIELD_VERSION_AFTER",
        "FIELD_VERSION_OUTCOME",
        "FIELD_VERSION_TARGET",
        "OUTCOME_VERSION_MATCH",
        "OUTCOME_VERSION_MISMATCH",
        "OUTCOME_VERSION_PENDING",
        "normalize_version",
        "target_version_outcome",
        "version_matches",
        "version_outcome",
    }
    assert added <= set(gate.__all__)  # Every new name is public.
