"""Multi-wave rollout orchestration (T080).

Manages wave execution, health-gate evaluation, and
automatic/manual promotion between waves per FR-010.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.shared.config.constants import WaveStatus
from src.shared.models.operations import RolloutPlan, RolloutWave

logger = logging.getLogger(__name__)


class RolloutOrchestrator:
    """Orchestrate multi-wave rollout execution.

    Manages wave lifecycle: pending -> executing -> completed/failed,
    with health-gate checks between waves.
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    def execute_next_wave(self, plan_id: UUID) -> dict:
        """Find and execute the next pending wave."""
        plan = self._load_plan(plan_id)
        if plan.status not in ("active", "draft"):
            return {"status": "skip", "reason": f"Plan is {plan.status}"}

        wave = self._find_next_wave(plan)
        if wave is None:
            return _mark_plan_complete(self._db, plan)

        return self._execute_wave(plan, wave)

    def promote_wave(self, plan_id: UUID, wave_number: int) -> dict:
        """Manually promote a wave (for manual promotion mode)."""
        plan = self._load_plan(plan_id)
        wave = self._load_wave(plan_id, wave_number)

        if wave.status != WaveStatus.COMPLETED.value:
            return {"error": "Wave must be completed to promote"}

        next_wave = self._find_next_wave(plan)
        if next_wave is None:
            return _mark_plan_complete(self._db, plan)

        return self._execute_wave(plan, next_wave)

    def rollback_wave(
        self,
        plan_id: UUID,
        wave_number: int,
        reason: str,
    ) -> dict:
        """Roll back a specific wave and pause the plan."""
        plan = self._load_plan(plan_id)
        wave = self._load_wave(plan_id, wave_number)

        wave.status = "rolled_back"
        wave.completed_at = datetime.now(UTC)
        wave.health_check_result = {"rollback_reason": reason}

        plan.status = "paused"
        self._db.commit()

        return {
            "status": "rolled_back",
            "wave": wave_number,
            "plan_status": "paused",
        }

    def pause_plan(self, plan_id: UUID) -> dict:
        """Pause an active rollout."""
        plan = self._load_plan(plan_id)
        plan.status = "paused"
        self._db.commit()
        return {"plan_id": str(plan_id), "status": "paused"}

    def resume_plan(self, plan_id: UUID) -> dict:
        """Resume a paused rollout."""
        plan = self._load_plan(plan_id)
        if plan.status != "paused":
            return {"error": f"Cannot resume: plan is {plan.status}"}
        plan.status = "active"
        self._db.commit()
        return self.execute_next_wave(plan_id)

    # -- Private ---

    def _load_plan(self, plan_id: UUID) -> RolloutPlan:
        """Load plan or raise."""
        stmt = select(RolloutPlan).where(RolloutPlan.plan_id == plan_id)
        plan = self._db.execute(stmt).scalar_one_or_none()
        if plan is None:
            msg = f"Plan {plan_id} not found"
            raise ValueError(msg)
        return plan

    def _load_wave(
        self,
        plan_id: UUID,
        wave_number: int,
    ) -> RolloutWave:
        """Load a specific wave."""
        stmt = select(RolloutWave).where(
            RolloutWave.plan_id == plan_id,
            RolloutWave.wave_number == wave_number,
        )
        wave = self._db.execute(stmt).scalar_one_or_none()
        if wave is None:
            msg = f"Wave {wave_number} not found"
            raise ValueError(msg)
        return wave

    def _find_next_wave(self, plan: RolloutPlan) -> RolloutWave | None:
        """Find the next pending wave in order."""
        for wave in sorted(plan.waves, key=lambda w: w.wave_number):
            if wave.status == WaveStatus.PENDING.value:
                return wave
        return None

    def _execute_wave(
        self,
        plan: RolloutPlan,
        wave: RolloutWave,
    ) -> dict:
        """Execute a single wave — mark executing, do work, evaluate."""
        wave.status = WaveStatus.EXECUTING.value
        wave.started_at = datetime.now(UTC)
        plan.status = "active"
        self._db.commit()

        health = _evaluate_health_gate(plan, wave)
        wave.health_check_result = health

        if health.get("passed", False):
            wave.status = WaveStatus.COMPLETED.value
        else:
            wave.status = WaveStatus.FAILED.value

        wave.completed_at = datetime.now(UTC)
        self._db.commit()

        result = {
            "wave": wave.wave_number,
            "status": wave.status,
            "health": health,
        }

        if wave.status == WaveStatus.COMPLETED.value and plan.promotion_mode == "automatic":
            result["auto_promote"] = True

        return result


def _mark_plan_complete(db: Session, plan: RolloutPlan) -> dict:
    """Mark a rollout plan as completed."""
    plan.status = "completed"
    db.commit()
    return {"status": "completed", "plan_id": str(plan.plan_id)}


def _evaluate_health_gate(
    plan: RolloutPlan,
    wave: RolloutWave,
) -> dict:
    """Evaluate health criteria for a wave.

    Placeholder: real implementation would query device status,
    client counts, and alarm state via Mist API.
    """
    criteria = plan.health_gate_criteria or {}
    return {
        "passed": True,
        "criteria": criteria,
        "wave_targets": len(wave.target_entities) if isinstance(wave.target_entities, list) else 0,
    }
