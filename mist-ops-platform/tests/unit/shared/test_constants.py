"""Unit tests for the shared enumerations in `src.shared.config.constants`.

The root `.gitignore` once hid the whole `src/shared/config/` package, so the
module disappeared and nine importers broke. See issue #1900. These tests fail
if the module disappears again, and they fail if a stored value changes.
"""

from __future__ import annotations

import pytest

from src.shared.config.constants import (
    AlertSeverity,
    AlertType,
    DeviceType,
    EntityType,
    GoldenImageStatus,
    JobStatus,
    WaveStatus,
)

# The `scheduled_jobs.status` column is a String(30), so a longer value truncates.
JOB_STATUS_COLUMN_WIDTH = 30
# The `deployment_waves.status` column is a String(20), so a longer value truncates.
WAVE_STATUS_COLUMN_WIDTH = 20
# The documented job lifecycle holds nine states, and a new state needs a migration.
EXPECTED_JOB_STATUS_COUNT = 9


class TestJobStatus:
    """Pin the nine states of a scheduled deploy job."""

    @pytest.mark.parametrize(
        ("member", "expected"),
        [
            (JobStatus.PENDING, "pending"),
            (JobStatus.APPROVED, "approved"),
            (JobStatus.PRE_CHECK, "pre_check"),
            (JobStatus.EXECUTING, "executing"),
            (JobStatus.POST_CHECK, "post_check"),
            (JobStatus.COMPLETED, "completed"),
            (JobStatus.FAILED, "failed"),
            (JobStatus.ROLLED_BACK, "rolled_back"),
            (JobStatus.CANCELLED, "cancelled"),
        ],
    )
    def test_value_matches_the_stored_text(self, member: JobStatus, expected: str) -> None:
        """The database rows hold this text, so a rename orphans those rows."""
        assert member.value == expected  # Compare the member value against the stored text.

    def test_the_set_is_complete(self) -> None:
        """A new state needs a migration, so the count guards an accidental addition."""
        assert len(JobStatus) == EXPECTED_JOB_STATUS_COUNT  # Guard an accidental addition.

    def test_every_value_fits_the_column(self) -> None:
        """The `scheduled_jobs.status` column is a String(30)."""
        for member in JobStatus:  # Walk every member of the enumeration.
            assert len(member.value) <= JOB_STATUS_COLUMN_WIDTH  # Reject a truncated value.


class TestWaveStatus:
    """Pin the four states of one deployment wave."""

    def test_values_match_the_stored_text(self) -> None:
        """The rollout worker writes this text into `deployment_waves.status`."""
        assert WaveStatus.PENDING.value == "pending"  # The wave waits for its turn.
        assert WaveStatus.EXECUTING.value == "executing"  # The worker pushes the change.
        assert WaveStatus.COMPLETED.value == "completed"  # Every device took the change.
        assert WaveStatus.FAILED.value == "failed"  # At least one device rejected it.

    def test_every_value_fits_the_column(self) -> None:
        """The `deployment_waves.status` column is a String(20)."""
        for member in WaveStatus:  # Walk every member of the enumeration.
            assert len(member.value) <= WAVE_STATUS_COLUMN_WIDTH  # Reject a truncated value.


class TestGoldenImageStatus:
    """Pin the three states of a golden firmware image."""

    def test_values_match_the_stored_text(self) -> None:
        """The `golden_images.lifecycle_state` column holds this text."""
        assert GoldenImageStatus.DRAFT.value == "draft"  # The server default is `draft`.
        assert GoldenImageStatus.APPROVED.value == "approved"  # A deployment needs this.
        assert GoldenImageStatus.RETIRED.value == "retired"  # The image is out of service.


class TestEntityType:
    """Pin the entity kinds that a sync job and a config revision use."""

    def test_values_match_the_stored_text(self) -> None:
        """The sync worker writes this text into `sync_jobs.job_type`."""
        assert EntityType.DEVICE.value == "device"  # One access point, switch, or gateway.
        assert EntityType.SITE.value == "site"  # One physical location.
        assert EntityType.ORG.value == "org"  # The whole organization.


class TestDeviceType:
    """Pin the hardware classes that the inventory sync writes."""

    def test_values_match_the_stored_text(self) -> None:
        """The `devices.device_type` column holds this text."""
        assert DeviceType.AP.value == "ap"  # A wireless access point.
        assert DeviceType.SWITCH.value == "switch"  # A wired switch.
        assert DeviceType.GATEWAY.value == "gateway"  # An edge gateway or a router.


class TestAlertEnums:
    """Pin the alert urgency values and the alert subject values."""

    def test_severity_values(self) -> None:
        """A notification route reads the urgency and picks a channel."""
        assert AlertSeverity.CRITICAL.value == "critical"  # An operator must act now.
        assert AlertSeverity.WARNING.value == "warning"  # An operator must act soon.
        assert AlertSeverity.INFO.value == "info"  # The record is for history only.

    def test_type_values(self) -> None:
        """The alert subject tells the operator which subsystem raised the alert."""
        assert AlertType.DRIFT.value == "drift"  # A device left its baseline.
        assert AlertType.DEPLOY.value == "deploy"  # A deploy job changed state.
        assert AlertType.SYNC.value == "sync"  # A sync job could not read the inventory.


class TestStringSubclassContract:
    """Prove that a member passes straight into a column and into a JSON body."""

    def test_a_member_compares_equal_to_a_plain_string(self) -> None:
        """The callers mix a member and a plain string in the same comparison."""
        assert JobStatus.PENDING == "pending"  # A StrEnum member compares by its text.
        assert DeviceType.AP == "ap"  # The same contract holds for every enumeration.

    def test_str_returns_the_stored_text(self) -> None:
        """A format call must not produce the `JobStatus.PENDING` repr text."""
        assert str(JobStatus.PENDING) == "pending"  # StrEnum coerces to the stored text.
        assert f"{DeviceType.AP}" == "ap"  # An f-string must yield the same stored text.

    def test_every_member_is_a_string(self) -> None:
        """A non-string member breaks the SQLAlchemy bind and the JSON encoder."""
        for enumeration in (
            AlertSeverity,
            AlertType,
            DeviceType,
            EntityType,
            GoldenImageStatus,
            JobStatus,
            WaveStatus,
        ):  # Walk each enumeration that this module exports.
            for member in enumeration:  # Walk every member of that enumeration.
                assert isinstance(member.value, str)  # Reject a non-string value.
