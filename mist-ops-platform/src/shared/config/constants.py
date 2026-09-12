"""Shared enumerations for the ops platform.

Nine modules import a name from this module. The module holds the string
constants that the API routes, the worker tasks, and the database rows share.

Every class derives from `StrEnum`. A `StrEnum` member compares equal to a
plain string, so a member passes straight into a SQLAlchemy column and into a
JSON body. Each member also keeps a `.value` attribute, and the callers in
this repository read that attribute.

Warning: A value in this module is a stored database value. Do not rename a
value. A rename orphans every row that already holds the old text.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = [
    "AlertSeverity",
    "AlertType",
    "DeviceType",
    "EntityType",
    "GoldenImageStatus",
    "JobStatus",
    "WaveStatus",
]


class JobStatus(StrEnum):
    """The lifecycle state of a scheduled deploy job.

    The `scheduled_jobs.status` column stores the value. The column is a
    `String(30)`, so every value here stays below 30 characters.

    The happy path runs PENDING, APPROVED, PRE_CHECK, EXECUTING, POST_CHECK,
    and then COMPLETED. A failure moves the job to FAILED, and a rollback then
    moves the job to ROLLED_BACK. CANCELLED is a terminal state.
    """

    PENDING = "pending"  # The operator created the job, and nobody approved it yet.
    APPROVED = "approved"  # An approver released the job, so the worker can claim it.
    PRE_CHECK = "pre_check"  # The worker runs the pre-checks against the target devices.
    EXECUTING = "executing"  # The worker pushes the change to the target devices.
    POST_CHECK = "post_check"  # The worker verifies the change on the target devices.
    COMPLETED = "completed"  # Every wave finished, and every post-check passed.
    FAILED = "failed"  # A check failed or a push failed, so the job stopped.
    ROLLED_BACK = "rolled_back"  # The worker restored the previous configuration.
    CANCELLED = "cancelled"  # An operator stopped the job before the worker claimed it.


class WaveStatus(StrEnum):
    """The lifecycle state of one deployment wave inside a rollout plan.

    The `deployment_waves.status` column stores the value. The column is a
    `String(20)`, so every value here stays below 20 characters.
    """

    PENDING = "pending"  # The wave waits for the previous wave to complete.
    EXECUTING = "executing"  # The worker pushes the change to the devices of this wave.
    COMPLETED = "completed"  # Every device of this wave took the change.
    FAILED = "failed"  # At least one device of this wave rejected the change.


class GoldenImageStatus(StrEnum):
    """The lifecycle state of a golden firmware image.

    The `golden_images.lifecycle_state` column stores the value, and that
    column carries the server default `draft`. A firmware deployment accepts
    the APPROVED state only.
    """

    DRAFT = "draft"  # An operator registered the image, and nobody approved it yet.
    APPROVED = "approved"  # An approver cleared the image for a firmware deployment.
    RETIRED = "retired"  # The image is out of service, so no deployment may use it.


class EntityType(StrEnum):
    """The kind of Mist entity that a sync job or a config revision targets.

    The `config_revisions.entity_type` column and the `sync_jobs.job_type`
    column store the value. Both columns are a `String(30)`.
    """

    DEVICE = "device"  # One access point, switch, or gateway inside an organization.
    SITE = "site"  # One physical location that holds a group of devices.
    ORG = "org"  # The whole organization, which owns every site and every device.


class DeviceType(StrEnum):
    """The hardware class of one Mist device.

    The `devices.device_type` column stores the value. The column is a
    `String(20)`.
    """

    AP = "ap"  # A wireless access point.
    SWITCH = "switch"  # A wired switch.
    GATEWAY = "gateway"  # An edge gateway or a router.


class AlertSeverity(StrEnum):
    """The urgency of a drift alert or a notification.

    A notification route reads the value and picks the delivery channel.
    """

    CRITICAL = "critical"  # The condition breaks service, so an operator must act now.
    WARNING = "warning"  # The condition risks service, so an operator must act soon.
    INFO = "info"  # The condition needs no action, and the record is for history only.


class AlertType(StrEnum):
    """The subject of an alert that the platform raises."""

    DRIFT = "drift"  # A device configuration no longer matches its baseline.
    DEPLOY = "deploy"  # A deploy job changed state, or a deploy job failed.
    SYNC = "sync"  # A sync job could not read the Mist inventory.
