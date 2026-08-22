"""Build, advance, and present the upgrade run record.

Why:
    One upgrade run ties one site, one operator, one pre-check capture, one
    firmware upgrade, and one post-check capture together. An operator reads
    that record months after the work, so the record must hold every field
    from the first release and must never reach an impossible state.

    This module owns the shape of the record, the legal moves between the
    states, and the status body the browser polls. It owns no storage. Every
    method here returns a plain dictionary, and
    ``src/upgrade_portal/capture/store.py`` writes that dictionary to the
    database and reads the key back. The two concerns stay apart, so a change
    of database touches one module only.
"""

from __future__ import annotations

import logging
import re
import uuid
from collections.abc import Mapping, MutableMapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, ClassVar, Final

__all__ = [
    "PHASE_ORDER",
    "RUN_KEY_PREFIX",
    "SCHEMA_VERSION",
    "PhaseState",
    "RunRecordBuilder",
    "RunSpec",
    "RunState",
    "RunStateMachine",
    "RunStatusView",
    "RunTransitionError",
]

logger = logging.getLogger(__name__)

# WHY: The first release writes the integer 1. A reader that finds a higher
# number refuses to render and says so, so a record written today stays
# readable years from now. The feature never deletes a record.
SCHEMA_VERSION: Final[int] = 1

# WHY: The key holds no slash and no colon, so the key sanitizer of the writer
# leaves the value alone.
RUN_KEY_PREFIX: Final[str] = "run-"

# WHY: The physical dependency of a site fixes this order. Everything sits
# downstream of the gateways. The access points and the wired clients sit
# downstream of the switches. Only the wireless clients sit downstream of the
# access points. Every artifact of this feature agrees on this order.
PHASE_ORDER: Final[tuple[str, ...]] = ("gateways", "switches", "aps", "clients")


def _utc_now_text() -> str:
    """Return the present time in UTC as ISO 8601 text.

    Why:
        Every stored time in this feature is text in UTC. A local time would
        read wrong in another time zone, and a naive value would give no clue
        which zone the writer used.

    Returns:
        The present time, for example 2026-08-19T14:03:11.482913+00:00.
    """
    return datetime.now(tz=UTC).isoformat()


class RunTransitionError(ValueError):
    """Raised when a caller asks for a run state move that the model forbids.

    Why:
        A silent illegal move leaves a stored record that no reader can
        explain months later. The message names the state before and the
        state after, so the caller sees the exact refusal. The class extends
        ValueError, so a caller that catches ValueError still works.
    """


class RunState(StrEnum):
    """Every state one upgrade run may hold.

    Why:
        A closed set of names keeps a stored record readable years after the
        work. The names come from the run state list of the data model and
        from no other source.
    """

    CREATED = "created"
    PRE_CAPTURE_RUNNING = "pre_capture_running"
    PRE_CAPTURE_DONE = "pre_capture_done"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    UPGRADE_SUBMITTING = "upgrade_submitting"
    UPGRADE_RUNNING = "upgrade_running"
    SETTLING_GATEWAYS = "settling_gateways"
    SETTLING_SWITCHES = "settling_switches"
    SETTLING_APS = "settling_aps"
    SETTLING_CLIENTS = "settling_clients"
    POST_CAPTURE_RUNNING = "post_capture_running"
    POST_CAPTURE_DONE = "post_capture_done"
    COMPLETE = "complete"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


class PhaseState(StrEnum):
    """Every state one cascade phase may hold.

    Why:
        The status contract shows the values ``waiting`` and ``settled``. The
        other three values fill the gaps the contract leaves. ``skipped``
        answers FR-058, which asks the portal to pass over a gate when the
        site holds no device of that family.
    """

    PENDING = "pending"
    WAITING = "waiting"
    SETTLED = "settled"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class RunSpec:
    """The values the operator supplies when one run starts.

    Why:
        The run record holds twenty fields. A builder that took them as
        parameters would break the five-parameter limit and would invite a
        wrong positional order. This group travels as one argument.

    Attributes:
        org_id: The Mist organization identifier.
        org_name: The organization name shown in the interface.
        site_id: The Mist site identifier.
        site_name: The site name shown in the interface.
        actor_email: The signed-in operator who owns the run.
        browser_id: The browser that holds the site lock.
        tier: The capture tier for both captures. 2 or 3.
        targets: One entry for each device the run upgrades. Empty at
            creation, because the operator picks the versions later.
        options: The upgrade options the operator chose. Empty at creation.
    """

    org_id: str
    org_name: str
    site_id: str
    site_name: str
    actor_email: str
    browser_id: str
    tier: int = 2
    targets: Sequence[Mapping[str, Any]] = ()
    options: Mapping[str, Any] = field(default_factory=dict)


class RunRecordBuilder:
    """Build one upgrade run document from the operator choices.

    Why:
        Every stage of the run reads the same record. The builder writes each
        field at creation, so no stage meets a missing key. The class returns
        a plain dictionary and writes nothing to the database.
    """

    # WHY: A key of any other shape breaks the read-back check of the store.
    KEY_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"run-[0-9a-f]{32}")

    # WHY: The data model marks every one of these fields as required.
    REQUIRED_FIELDS: ClassVar[tuple[str, ...]] = (
        "_key",
        "run_id",
        "schema_version",
        "org_id",
        "org_name",
        "site_id",
        "site_name",
        "actor_email",
        "browser_id",
        "created_at",
        "updated_at",
        "state",
        "tier",
        "targets",
        "options",
        "phases",
        "stop_request",
        "pre_capture_id",
        "post_capture_id",
        "error",
    )

    def build(self, spec: RunSpec) -> dict[str, Any]:
        """Return one new run record for the operator choices.

        Why:
            The builder writes every field at creation. A field added at a
            later stage would leave an older record without it.

        Args:
            spec: The organization, the site, the operator, and the options.

        Returns:
            A plain dictionary that the store writes without further edits.

        Raises:
            ValueError: When the new record fails its own validation.
        """
        key = self.new_key()
        record: dict[str, Any] = {"_key": key, "run_id": key, "schema_version": SCHEMA_VERSION}
        record.update(self._site_fields(spec))
        record.update(self._time_fields(_utc_now_text()))
        record.update(self._progress_fields(spec))
        self.validate(record)
        logger.info("Built run record %s for site %s", key, spec.site_id)
        return record

    @staticmethod
    def new_key() -> str:
        """Return one fresh run key.

        Why:
            A random value needs no counter and no round trip to the
            database, so two workers never mint the same key.

        Returns:
            A key of the shape run- and 32 lowercase hexadecimal characters.
        """
        return f"{RUN_KEY_PREFIX}{uuid.uuid4().hex}"

    @classmethod
    def validate(cls, record: Mapping[str, Any]) -> None:
        """Raise when one run record misses a field or holds a wrong value.

        Why:
            A record that reaches the store with a missing field stays wrong
            forever, because this feature deletes no record.

        Args:
            record: The run record to check.

        Raises:
            ValueError: When a field is missing or holds a wrong value.
        """
        missing = [name for name in cls.REQUIRED_FIELDS if name not in record]
        if missing:
            raise ValueError(f"The run record misses these fields: {', '.join(missing)}.")
        if not cls.KEY_PATTERN.fullmatch(str(record["_key"])) or record["run_id"] != record["_key"]:
            raise ValueError("The key must read run- and 32 hexadecimal characters, and run_id must match it.")
        if not cls._is_plain_int(record["schema_version"]) or record["schema_version"] != SCHEMA_VERSION:
            raise ValueError(f"The schema_version must be the integer {SCHEMA_VERSION}.")
        if not cls._is_plain_int(record["tier"]) or record["tier"] not in (2, 3):
            raise ValueError("The tier must be the integer 2 or the integer 3.")

    @staticmethod
    def _is_plain_int(value: Any) -> bool:
        """Return true when one value is an integer and is not a boolean.

        Why:
            Python holds bool as a subclass of int, so `True == 1` reads as
            true. A stored `True` would pass an equality check against the
            schema version 1, and the store would then hold a record that no
            later reader can trust. A float carries the same risk, because
            `2.0 == 2` also reads as true. This check names the exact type and
            closes both holes.

        Args:
            value: The value to check.

        Returns:
            True when the value is an int and is not a bool.
        """
        return isinstance(value, int) and not isinstance(value, bool)  # Bool is an int subclass.

    @staticmethod
    def _site_fields(spec: RunSpec) -> dict[str, Any]:
        """Return the organization, site, operator, and tier fields.

        Args:
            spec: The operator choices for this run.

        Returns:
            The seven fields that name who ran the work and where.
        """
        return {
            "org_id": spec.org_id,
            "org_name": spec.org_name,
            "site_id": spec.site_id,
            "site_name": spec.site_name,
            "actor_email": spec.actor_email,
            "browser_id": spec.browser_id,
            "tier": int(spec.tier),
        }

    @staticmethod
    def _time_fields(now: str) -> dict[str, Any]:
        """Return the creation time, the update time, and the first state.

        Args:
            now: The present time as ISO 8601 text in UTC.

        Returns:
            The three fields that open the life of the record.
        """
        return {"created_at": now, "updated_at": now, "state": RunState.CREATED.value}

    @classmethod
    def _progress_fields(cls, spec: RunSpec) -> dict[str, Any]:
        """Return the target list, the options, and the empty progress fields.

        Why:
            Each identifier field starts as null rather than absent, so a
            reader never has to tell a missing key from an empty value.

        Args:
            spec: The operator choices for this run.

        Returns:
            The seven fields that carry the progress of the run.
        """
        return {
            "targets": [dict(target) for target in spec.targets],
            "options": dict(spec.options),
            "phases": cls.initial_phases(),
            "stop_request": None,
            "pre_capture_id": None,
            "post_capture_id": None,
            "error": None,
        }

    @staticmethod
    def initial_phases() -> list[dict[str, Any]]:
        """Return one pending entry for each cascade phase.

        Why:
            The record holds the four phases from the first moment, in the
            fixed cascade order, so the status body never has to invent one.

        Returns:
            Four phase entries in the order gateways, switches, aps, clients.
        """
        return [
            {"name": name, "state": PhaseState.PENDING.value, "settled": 0, "total": 0, "settled_at": None, "note": ""}
            for name in PHASE_ORDER
        ]


class RunStateMachine:
    """Move one run record between the states the data model allows.

    Why:
        An illegal move corrupts a record that an operator reads months
        later. This class refuses the move and names both states, rather
        than write a state that no reader can explain.

        FR-058 needs no extra move. A site with no device of one family runs
        that phase with the phase state ``skipped``, so the run still passes
        through each settling state in the fixed order.
    """

    # WHY: The one linear path of the data model. Each member may move only to
    # the member that follows it.
    CHAIN: ClassVar[tuple[RunState, ...]] = (
        RunState.CREATED,
        RunState.PRE_CAPTURE_RUNNING,
        RunState.PRE_CAPTURE_DONE,
        RunState.AWAITING_CONFIRMATION,
        RunState.UPGRADE_SUBMITTING,
        RunState.UPGRADE_RUNNING,
        RunState.SETTLING_GATEWAYS,
        RunState.SETTLING_SWITCHES,
        RunState.SETTLING_APS,
        RunState.SETTLING_CLIENTS,
        RunState.POST_CAPTURE_RUNNING,
        RunState.POST_CAPTURE_DONE,
        RunState.COMPLETE,
    )

    # WHY: A finished run moves nowhere. The stop route answers
    # run_not_stoppable for each of these three states.
    TERMINAL: ClassVar[frozenset[RunState]] = frozenset(
        {RunState.COMPLETE, RunState.STOPPED, RunState.FAILED},
    )

    def advance(self, record: MutableMapping[str, Any], target: RunState | str) -> MutableMapping[str, Any]:
        """Move one run record to a new state and stamp the update time.

        Args:
            record: The run record. The method edits it in place.
            target: The wanted state, as a RunState or as its plain name.

        Returns:
            The same record, with the new state and a fresh update time.

        Raises:
            RunTransitionError: When the model forbids the move.
        """
        current = self.read_state(record)
        wanted = self.coerce(target)
        if wanted not in self.allowed_next(current):
            raise RunTransitionError(f"A run cannot move from {current.value} to {wanted.value}.")
        record["state"] = wanted.value
        record["updated_at"] = _utc_now_text()
        logger.info("Run %s moved from %s to %s", record.get("run_id", ""), current.value, wanted.value)
        return record

    def fail(self, record: MutableMapping[str, Any], stage: str, message: str) -> MutableMapping[str, Any]:
        """Move one run record to the failed state and record the reason.

        Why:
            A failed run with no reason gives the operator nothing to act on.
            The error time repeats the update time, so the two agree.

        Args:
            record: The run record. The method edits it in place.
            stage: The step that failed, for example post_capture.
            message: One plain sentence for the operator. Never a credential.

        Returns:
            The same record, in the failed state, with the error field set.

        Raises:
            RunTransitionError: When the run already reached a final state.
        """
        self.advance(record, RunState.FAILED)
        record["error"] = {"stage": stage, "message": message, "at": record["updated_at"]}
        logger.warning("Run %s failed at stage %s", record.get("run_id", ""), stage)
        return record

    @classmethod
    def allowed_next(cls, state: RunState) -> frozenset[RunState]:
        """Return every state one run may enter from one state.

        Why:
            The model allows one step along the chain, a stop from any live
            state, and a failure from any live state. A final state allows
            nothing.

        Args:
            state: The current state of the run.

        Returns:
            The legal next states. An empty set for a final state.
        """
        if state in cls.TERMINAL:
            return frozenset()
        if state is RunState.STOPPING:
            return frozenset({RunState.STOPPED, RunState.FAILED})
        following = cls.CHAIN[cls.CHAIN.index(state) + 1]
        return frozenset({following, RunState.STOPPING, RunState.FAILED})

    @classmethod
    def read_state(cls, record: Mapping[str, Any]) -> RunState:
        """Return the state one run record holds.

        Args:
            record: The run record to read.

        Returns:
            The state of the record.

        Raises:
            RunTransitionError: When the record holds no known state name.
        """
        return cls.coerce(str(record.get("state", "")))

    @staticmethod
    def coerce(value: RunState | str) -> RunState:
        """Return the run state that one name stands for.

        Why:
            The routes and the driver pass plain text. A name outside the
            model must fail here, at the edge, and never reach the store.

        Args:
            value: A RunState or the plain name of one state.

        Returns:
            The matching RunState.

        Raises:
            RunTransitionError: When no state carries that name.
        """
        try:
            return RunState(value)
        except ValueError as error:
            raise RunTransitionError(f"{value!r} is not a run state of this model.") from error


class RunStatusView:
    """Build the status body that the run page polls.

    Why:
        The browser polls this body every 30 seconds and uses no server-sent
        events. Every key the contract names is present on every call, so the
        page never has to guess whether a value is missing or empty.
    """

    # WHY: The contract shows these seven keys on a target row. The view fills
    # any key the driver has not written yet with null.
    TARGET_FIELDS: ClassVar[tuple[str, ...]] = (
        "mac",
        "name",
        "device_type",
        "state",
        "version_before",
        "version_target",
        "version_after",
    )

    # WHY: `upgrade/driver.py` writes the key `lock` onto the record when the
    # run loses the site lock, and writes these three sub-keys inside it. The
    # view names the same three, so a value a later writer adds to that entry,
    # such as a lock token, can never reach the browser.
    LOCK_KEY: ClassVar[str] = "lock"
    LOCK_FIELDS: ClassVar[tuple[str, ...]] = ("state", "message", "at")

    # WHY: A count of 1 needs the singular word. Plain words beat a phase
    # identifier in a sentence an operator reads.
    PHASE_NOUNS: ClassVar[Mapping[str, tuple[str, str]]] = {
        "gateways": ("gateway", "gateways"),
        "switches": ("switch", "switches"),
        "aps": ("access point", "access points"),
        "clients": ("wireless client", "wireless clients"),
    }

    # WHY: One sentence for each state, so the page always has plain text.
    STATE_MESSAGES: ClassVar[Mapping[str, str]] = {
        RunState.CREATED.value: "The run is ready. The pre-check capture has not started.",
        RunState.PRE_CAPTURE_RUNNING.value: "The portal reads the state of the site before the upgrade.",
        RunState.PRE_CAPTURE_DONE.value: "The pre-check capture is complete.",
        RunState.AWAITING_CONFIRMATION.value: "The portal waits for the operator to confirm the upgrade.",
        RunState.UPGRADE_SUBMITTING.value: "The portal sends the upgrade job to the cloud.",
        RunState.UPGRADE_RUNNING.value: "The cloud runs the upgrade.",
        RunState.SETTLING_GATEWAYS.value: "The portal waits for the gateways to return.",
        RunState.SETTLING_SWITCHES.value: "The portal waits for the switches to return.",
        RunState.SETTLING_APS.value: "The portal waits for the access points to return.",
        RunState.SETTLING_CLIENTS.value: "The portal waits for the wireless clients to return.",
        RunState.POST_CAPTURE_RUNNING.value: "The portal reads the state of the site after the upgrade.",
        RunState.POST_CAPTURE_DONE.value: "The post-check capture is complete.",
        RunState.COMPLETE.value: "The run is complete.",
        RunState.STOPPING.value: "The portal asks the cloud to cancel the upgrade.",
        RunState.STOPPED.value: "The run stopped.",
        RunState.FAILED.value: "The run failed. Read the error field for the reason.",
    }

    def build(self, record: Mapping[str, Any], message: str | None = None) -> dict[str, Any]:
        """Return the status body for one run.

        Args:
            record: The stored run record.
            message: One sentence from the driver. The view builds its own
                sentence when the caller passes none.

        Returns:
            The body that the run status endpoint answers, with the keys in
            the order the contract shows. A run that lost its site lock adds
            the key `lock` after them.
        """
        phases = self.phases(record)
        body = self._identity(record)
        body.update({"phase_order": list(PHASE_ORDER), "phases": phases, "targets": self.targets(record)})
        body.update(self._outcome(record))
        body["message"] = message or self.message(record, phases)
        body.update(self._lock(record))  # The last key reports a fault, so it never hides a key of the contract.
        return body

    @classmethod
    def phases(cls, record: Mapping[str, Any]) -> list[dict[str, Any]]:
        """Return one entry for each cascade phase, in the fixed order.

        Why:
            The page draws the four phases in one fixed order. A stored list
            that misses a phase must still render, so the view fills the gap.

        Args:
            record: The stored run record.

        Returns:
            Four phase entries in the order gateways, switches, aps, clients.
        """
        stored = {str(entry.get("name", "")): entry for entry in record.get("phases", [])}
        return [cls._phase_entry(name, stored.get(name)) for name in PHASE_ORDER]

    @classmethod
    def targets(cls, record: Mapping[str, Any]) -> list[dict[str, Any]]:
        """Return one row for each device the run upgrades.

        Args:
            record: The stored run record.

        Returns:
            One entry for each target, with every contract key present.
        """
        return [cls._target_entry(entry) for entry in record.get("targets", [])]

    @classmethod
    def message(cls, record: Mapping[str, Any], phases: Sequence[Mapping[str, Any]]) -> str:
        """Return one plain sentence about the run for the operator.

        Why:
            An operator reads a sentence faster than a state name. The
            sentence names the count of devices that have not returned, so
            the operator knows how much work is left.

        Args:
            record: The stored run record.
            phases: The phase entries this view built.

        Returns:
            One sentence in plain words.
        """
        waiting = [phase for phase in phases if phase.get("state") == PhaseState.WAITING]
        if not waiting:
            return cls._resting_message(record, phases)
        phase = waiting[0]
        remaining = int(phase.get("total", 0)) - int(phase.get("settled", 0))
        singular, plural = cls.PHASE_NOUNS.get(str(phase.get("name", "")), ("device", "devices"))
        return f"The portal waits for {remaining} {singular if remaining == 1 else plural} to return."

    @classmethod
    def _resting_message(cls, record: Mapping[str, Any], phases: Sequence[Mapping[str, Any]]) -> str:
        """Return the sentence for a run that holds no phase in the waiting state.

        Why:
            FR-058 lets the portal pass over a family that the site does not
            hold. The run state still names that family, so the state sentence
            alone tells the operator that the portal waits for a gateway at a
            site that holds no gateway. This step reads the phase state first
            and reports the real reason.

        Args:
            record: The stored run record.
            phases: The phase entries this view built.

        Returns:
            One sentence in plain words.
        """
        state = str(record.get("state", ""))
        # WHY: Only a settling state names a family. Every other state leaves the
        # prefix in place, finds no phase of that name, and falls to the map.
        family = state.removeprefix("settling_")
        current = next((entry for entry in phases if entry.get("name") == family), None)
        if current is not None and current.get("state") == PhaseState.SKIPPED:
            plural = cls.PHASE_NOUNS.get(family, ("device", "devices"))[1]
            return f"The site holds no {plural}, so the portal does not wait for this group."
        return cls.STATE_MESSAGES.get(state, "The run is in progress.")

    @staticmethod
    def _identity(record: Mapping[str, Any]) -> dict[str, Any]:
        """Return the run identifier and the run state.

        Args:
            record: The stored run record.

        Returns:
            The two keys that open the status body.
        """
        return {
            "run_id": str(record.get("run_id", "")),
            "state": str(record.get("state", RunState.CREATED.value)),
        }

    @staticmethod
    def _outcome(record: Mapping[str, Any]) -> dict[str, Any]:
        """Return the stop request and the two capture identifiers.

        Args:
            record: The stored run record.

        Returns:
            The three keys that report the outcome of the run so far.
        """
        return {
            "stop_request": record.get("stop_request"),
            "pre_capture_id": record.get("pre_capture_id"),
            "post_capture_id": record.get("post_capture_id"),
        }

    @classmethod
    def _lock(cls, record: Mapping[str, Any]) -> dict[str, Any]:
        """Return the lock report of the run, or no key at all.

        Why:
            The driver writes this note when another operator takes the site
            lock, or when the lock expires during an upgrade. No answer
            carried the note, so an operator whose site was taken read a run
            that looked healthy. The key stays absent on a healthy run,
            because the contract fixes the other keys and this one reports a
            fault only.

        Args:
            record: The stored run record.

        Returns:
            A mapping with the one key `lock`, or an empty mapping when the
            run still holds its site lock.
        """
        stored = record.get(cls.LOCK_KEY)  # The driver writes this key only after the run loses the site lock.
        if not isinstance(stored, Mapping):  # A run that still holds its lock adds no key to the body.
            return {}
        report = {name: stored.get(name) for name in cls.LOCK_FIELDS}  # Copy the three named keys and no other.
        return {cls.LOCK_KEY: report}

    @staticmethod
    def _phase_entry(name: str, stored: Mapping[str, Any] | None) -> dict[str, Any]:
        """Return one phase entry with every key present.

        Why:
            The contract shows a settled phase with a settle time and a
            waiting phase with two counts. The view writes all six keys on
            every phase, so the page reads one shape only.

            The note is the last key and it holds text rather than null. The
            page prints it, and an empty string prints as nothing while a null
            would print the word "None".

        Args:
            name: The cascade phase name.
            stored: The stored entry for that phase, or None when absent.

        Returns:
            One phase entry with the name, the state, the counts, the settle
            time, and the note.
        """
        source: Mapping[str, Any] = stored or {}
        return {
            "name": name,
            "state": str(source.get("state", PhaseState.PENDING.value)),
            "settled": int(source.get("settled", 0)),
            "total": int(source.get("total", 0)),
            "settled_at": source.get("settled_at"),
            "note": str(source.get("note") or ""),
        }

    @classmethod
    def _target_entry(cls, stored: Mapping[str, Any]) -> dict[str, Any]:
        """Return one target row with every contract key present.

        Why:
            The driver fills a field such as the version after the upgrade
            only at the end. The row still carries the key, with the value
            null, so the table draws the same columns at every poll.

        Args:
            stored: The stored target entry.

        Returns:
            A copy of the entry, with any missing contract key set to null.
        """
        entry: dict[str, Any] = dict(stored)
        for name in cls.TARGET_FIELDS:
            entry.setdefault(name, None)
        return entry
