"""Stop one upgrade run after the operator types the word STOP.

Why:
    A stop is a protected action. FR-038b accepts the exact text `STOP` and
    no other word, so a stray click never ends an upgrade that a site needs.

    A cancel is best effort. The cloud may accept the call while a device is
    already writing firmware, and that device completes the upgrade. FR-038c
    and FR-038d forbid an interrupt of a write, because an interrupted write
    can leave a device unusable. The operator must read that truth in plain
    words, so the message names each group and says that a device in mid-write
    finishes the upgrade.

    The stop request record and the confirmation check already live in
    `src/upgrade_portal/runtime/signals.py`. This module executes the cancel
    calls and reports the result. It never duplicates the request record.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

from src.firmware.upgrade_service import (
    CancelOutcome,
    GatewayFamily,
    UpgradePlan,
    cancel_upgrade,
    read_upgrade_status,
)
from src.upgrade_portal.runtime.signals import (
    STOP_CONFIRMATION_TEXT,
    ConfirmationRequiredError,
    RunRecordStore,
    StopOutcome,
    StopRequestStore,
)

__all__ = [
    "STOP_CONFIRMATION_TEXT",
    "StopCounts",
    "StopTarget",
    "TargetResult",
    "cancel_target",
    "merge_results",
    "plan_macs",
    "read_last_status",
    "require_confirmation",
    "status_is_known",
    "stop_message",
    "stop_run",
    "stop_run_and_record",
]

logger = logging.getLogger(__name__)

# WHY: The one sentence the operator must read when a device is writing
# firmware. FR-038d forbids an interrupt, so the device finishes the upgrade.
_WRITE_RULE: Final[str] = "The portal never interrupts a write, so the"

# WHY: A cancel call that never answered leaves every device of that plan
# running. The house rule of the upgrade seam reports the same result for a
# refused cancel, so the portal never claims a stop that did not happen.
_MESSAGE_CALL_FAILED: Final[str] = "The cloud did not answer the cancel call, so every device continues the upgrade."


@dataclass(frozen=True, slots=True)
class StopTarget:
    """One upgrade plan of a run and the cloud identifier of that upgrade.

    Why:
        The cancel call needs the plan and the identifier that the submission
        returned. A run holds one plan for each scope and family, so a stop
        walks a list of these records.

    Attributes:
        plan: The plan the run submitted.
        upgrade_id: The identifier the cloud returned for that plan.
        family: The gateway family, which selects the status call.
    """

    plan: UpgradePlan
    upgrade_id: str
    family: GatewayFamily = GatewayFamily.JUNOS


@dataclass(frozen=True, slots=True)
class TargetResult:
    """What one cancel call achieved for one plan.

    Why:
        The portal must never claim a stop it cannot prove. The second field
        records whether the portal read the device state before the cancel,
        so the message can qualify the claim.

    Attributes:
        outcome: The three device groups and the message of the seam.
        status_known: True when the portal read the upgrade status first.
    """

    outcome: CancelOutcome
    status_known: bool = True


@dataclass(frozen=True, slots=True)
class StopCounts:
    """How many devices reached each group of one stop.

    Why:
        The message builder needs four numbers and no device name. A record
        keeps the builder free of the lists and keeps each helper short.

    Attributes:
        cancelled: Devices the cloud stopped.
        already_writing: Devices that write firmware now.
        no_cancel_available: Devices with no cancel call in the cloud.
        status_unknown: Plans whose device state the portal could not read.
    """

    cancelled: int = 0
    already_writing: int = 0
    no_cancel_available: int = 0
    status_unknown: int = 0


def require_confirmation(text: str) -> None:
    """Refuse a stop that the operator did not confirm with the word STOP.

    Why:
        FR-038b names the exact text and the exact letter case. The check
        reuses the stop store, so one rule serves the route and this module.

    Args:
        text: The text the operator typed.

    Raises:
        ConfirmationRequiredError: When the text is not the word STOP.
    """
    if not StopRequestStore.confirmation_matches(text):
        raise ConfirmationRequiredError(f"The stop control needs the exact text {STOP_CONFIRMATION_TEXT}.")


def plan_macs(plan: UpgradePlan) -> tuple[str, ...]:
    """Return the MAC address of each device the plan holds.

    Args:
        plan: The upgrade plan.

    Returns:
        One MAC address for each target of the plan.
    """
    return tuple(target.mac for target in plan.targets)


def read_last_status(session: Any, target: StopTarget) -> Mapping[str, object] | None:
    """Read the upgrade status so the cancel call can sort the devices.

    Why:
        The status names each device that is writing firmware now. The seam
        takes the same mapping as `last_status`, so one read serves both
        calls. A failed read must not stop the cancel.

    Args:
        session: The Mist session.
        target: The plan and the upgrade identifier.

    Returns:
        The status mapping, or None when the read failed.
    """
    try:
        return read_upgrade_status(
            session,
            target.plan.scope,
            target.plan.route.scope_id,
            target.upgrade_id,
            target.family,
        )
    except Exception as error:  # noqa: BLE001  # WHY: A failed read must never block the cancel call.
        logger.warning("The portal could not read the status of upgrade %s: %s", target.upgrade_id, error)
        return None


def status_is_known(status: Mapping[str, object] | None) -> bool:
    """Report whether one status read told the portal which devices write firmware.

    Why:
        A read can answer and still tell the portal nothing. The
        organization-scope read of a session smart router answers device
        statistics, not an upgrade job. The seam marks that answer with
        `status_known` set to false. A test for `None` alone would call that
        answer a good read, and the operator would then see the word stopped
        for a device that is still writing firmware.

    Args:
        status: The status mapping that the seam returned, or None.

    Returns:
        True only when the seam stated that the answer was an upgrade job.
    """
    if status is None:
        return False
    return status.get("status_known") is True


def cancel_target(session: Any, target: StopTarget) -> TargetResult:
    """Cancel one plan and report which devices stopped.

    Why:
        A cancel that raises must not end the whole stop. The other plans of
        the run still need their call.

    Args:
        session: The Mist session.
        target: The plan and the upgrade identifier.

    Returns:
        The groups of that plan and whether the portal read the state first.
    """
    last_status = read_last_status(session, target)
    try:
        outcome = cancel_upgrade(session, target.plan, target.upgrade_id, last_status)
    except Exception as error:  # noqa: BLE001  # WHY: One failed plan must not end the stop of the other plans.
        logger.warning("The cancel call for upgrade %s failed: %s", target.upgrade_id, error)
        return TargetResult(CancelOutcome((), plan_macs(target.plan), (), _MESSAGE_CALL_FAILED), status_known=False)
    return TargetResult(outcome, status_known=status_is_known(last_status))


def _device_count(count: int) -> str:
    """Return the count and the word device in the right number.

    Args:
        count: How many devices.

    Returns:
        Text such as `1 device` or `4 devices`.
    """
    return "1 device" if count == 1 else f"{count} devices"


def _cancelled_sentence(count: int) -> str:
    """Return the sentence about the devices the cloud stopped.

    Args:
        count: How many devices the cloud stopped.

    Returns:
        One sentence.
    """
    if count == 0:
        return "The portal cancelled no device."
    return f"The portal cancelled the upgrade for {_device_count(count)}."


def _writing_sentence(count: int) -> str:
    """Return the sentence about the devices that write firmware now.

    Why:
        FR-038d forbids an interrupt of a write. The operator must read in
        plain words that each of these devices finishes the upgrade.

    Args:
        count: How many devices write firmware now.

    Returns:
        One sentence, or empty text when no device is writing.
    """
    if count == 0:
        return ""
    if count == 1:
        return f"{_WRITE_RULE} 1 device that writes firmware now finishes the upgrade."
    return f"{_WRITE_RULE} {count} devices that write firmware now finish the upgrade."


def _no_cancel_sentence(count: int) -> str:
    """Return the sentence about the devices with no cancel call.

    Args:
        count: How many devices have no cancel call in the cloud.

    Returns:
        One sentence, or empty text when every device has a cancel call.
    """
    if count == 0:
        return ""
    if count == 1:
        return "The cloud offers no cancel call for 1 device, so that device continues the upgrade."
    return f"The cloud offers no cancel call for {count} devices, so those devices continue the upgrade."


def _unknown_sentence(count: int) -> str:
    """Return the sentence about a plan whose device state the portal missed.

    Why:
        FR-038f forbids a claim that the portal cannot prove. A missing read
        leaves the mid-write state unknown, so the message says so.

    Args:
        count: How many plans the portal could not read first.

    Returns:
        One sentence, or empty text when the portal read every plan.
    """
    if count == 0:
        return ""
    return "The portal could not read the device state first, so a device in mid-write may still finish the upgrade."


def stop_message(counts: StopCounts) -> str:
    """Return the plain message the operator reads after a stop.

    Why:
        The message holds one short sentence for each condition that applies.
        A single long sentence would break the sentence-length rule of the
        writing guide and would hide the mid-write truth in a clause.

    Args:
        counts: How many devices reached each group.

    Returns:
        The message. Always at least one sentence.
    """
    tail = (
        _writing_sentence(counts.already_writing),
        _no_cancel_sentence(counts.no_cancel_available),
        _unknown_sentence(counts.status_unknown),
    )
    parts = [_cancelled_sentence(counts.cancelled)]
    parts.extend(sentence for sentence in tail if sentence)
    return " ".join(parts)


def merge_results(results: Sequence[TargetResult]) -> StopOutcome:
    """Join the result of every plan into one outcome for the run.

    Why:
        A run may hold one plan for each scope and family. The operator reads
        one answer, so the three lists join and the message counts the whole
        run. A device that is writing never appears in the cancelled list.

    Args:
        results: One entry for each plan of the run.

    Returns:
        The three device lists and one plain message.
    """
    writing = {mac for item in results for mac in item.outcome.already_writing}
    blocked = {mac for item in results for mac in item.outcome.no_cancel_available}
    stopped = {mac for item in results for mac in item.outcome.cancelled} - writing - blocked
    unknown = sum(1 for item in results if not item.status_known)
    counts = StopCounts(len(stopped), len(writing), len(blocked), unknown)
    return StopOutcome(
        cancelled=tuple(sorted(stopped)),
        already_writing=tuple(sorted(writing)),
        no_cancel_available=tuple(sorted(blocked)),
        message=stop_message(counts),
    )


def stop_run(session: Any, targets: Sequence[StopTarget], confirmation: str) -> StopOutcome:
    """Cancel every plan of one run after the operator types STOP.

    Why:
        This is the whole stop control. The caller supplies the plans, and
        the module answers with the three lists and one plain message.

    Args:
        session: The Mist session.
        targets: One entry for each plan of the run.
        confirmation: The text the operator typed.

    Returns:
        The three device lists and one plain message.

    Raises:
        ConfirmationRequiredError: When the text is not the word STOP.
    """
    require_confirmation(confirmation)
    logger.info("The portal stops %s upgrade plans at the request of an operator", len(targets))
    results = [cancel_target(session, target) for target in targets]
    outcome = merge_results(results)
    logger.info("The stop cancelled %s devices", len(outcome.cancelled))
    logger.info("The stop left %s devices in mid-write", len(outcome.already_writing))
    return outcome


def stop_run_and_record(
    store: RunRecordStore,
    run_id: str,
    session: Any,
    targets: Sequence[StopTarget],
    confirmation: str,
) -> StopOutcome:
    """Stop one run and write the outcome into the stop request of the record.

    Why:
        The route needs one call. The run record then holds the answer, so a
        page reload and a poll both show the same three lists and the same
        message.

    Args:
        store: The run record store.
        run_id: The run key.
        session: The Mist session.
        targets: One entry for each plan of the run.
        confirmation: The text the operator typed.

    Returns:
        The three device lists and one plain message.

    Raises:
        ConfirmationRequiredError: When the text is not the word STOP.
    """
    outcome = stop_run(session, targets, confirmation)
    # This layer owns the outcome write for every stop that reaches the cloud.
    # `app/routes/upgrade.record_stop_outcome` reads the record and skips its own
    # write once this write lands, so one stop writes the outcome one time.
    StopRequestStore(store).record_outcome(run_id, outcome)
    return outcome
