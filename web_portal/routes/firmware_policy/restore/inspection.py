"""Inspect verified firmware policies without preparing restoration or consuming recovery proofs."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from src.operations.execution.firmware_policy.recovery.bundle import BundleFiles, RestoreBundle, RestoreSelection
from src.operations.execution.firmware_policy.recovery.workflow import RestoreWorkflow
from src.operations.execution.firmware_policy.sdk import PolicyError, PolicyResponse

from .policies import PolicyComparison


class HistoricalInspection:
    """Require verified source integrity and current access before policy disclosure."""

    def __init__(self, workflow: RestoreWorkflow) -> None:
        """Reuse checked SDK admission and the existing private bundle reader."""
        self.workflow = workflow

    def read(self, token: str, key: str, compare: bool) -> dict[str, Any]:
        """Inspect one saved record, with current reads only after explicit comparison."""
        if not isinstance(compare, bool):
            raise PolicyError("Select an explicit current comparison state.")
        bundle = self.workflow.files.read(token)
        record = RestoreSelection.records(bundle, [key])[0]
        owner = self.owned(bundle, record)
        sources = {"saved": record["settings"]}
        metadata = {
            "scope": record["scope"],
            "id": record["id"],
            "snapshot_at": bundle.created_at,
            "cloud": RestoreSelection.cloud(self.workflow.api),
        }
        if compare:
            sources["current"] = self.current(record["scope"], record["id"], owner)
            metadata["observed_at"] = datetime.now(UTC).isoformat()
        result = {**metadata, **PolicyComparison.build(record["scope"], sources)}
        self.workflow.files.unchanged(bundle)
        return result

    def owned(self, bundle: RestoreBundle, record: dict[str, Any]) -> str:
        """Check authenticated organization access and actual current site membership."""
        owner = RestoreSelection.ownership(bundle, record)
        self.workflow.api.organization(owner)
        membership = RestoreSelection.membership(self.workflow.api, {owner})
        if record["scope"] == "site" and record["id"] not in membership[owner]:
            raise PolicyError("The saved site is not a current member of its organization.")
        return owner

    def current(self, scope: Any, identifier: str, owner: str) -> dict[str, Any]:
        """Read complete current settings and reject inconsistent scope ownership."""
        current = self.workflow.api.read(scope, identifier)
        if current.get("org_id", owner) != owner or (
            scope == "site" and current.get("site_id", identifier) != identifier
        ):
            raise PolicyError("The current settings ownership does not match the selected backup.")
        return current


class PreparedInspection:
    """Inspect a live plan while leaving its full backup and single-use proof unchanged."""

    @staticmethod
    def read(context: Any, scope: str, identifier: str) -> dict[str, Any]:
        """Recheck private recovery and source integrity before one current comparison."""
        identifier = PolicyResponse.identifier(identifier)
        workflow, plans, proof = context
        files = workflow.files if isinstance(workflow, RestoreWorkflow) else BundleFiles(workflow.backup)
        backup = files.read(proof.path.stem)
        if backup.records != proof.records:
            raise PolicyError("The settings backup does not match the original settings.")
        target, source, owner, notices = PreparedInspection.target(context, scope, identifier, backup.created_at)
        access = HistoricalInspection(RestoreWorkflow(workflow.api, files))
        access.owned(backup, {"scope": scope, "id": identifier, "settings": target.original})
        current = access.current(scope, identifier, owner)
        source["observed_at"] = datetime.now(UTC).isoformat()
        columns = {
            "saved": source["settings"],
            "current": current,
            "proposed": PolicyComparison.effect(target.original, target.body),
        }
        if isinstance(workflow, RestoreWorkflow):
            columns["prepared"] = target.original
        files.unchanged(backup)
        PreparedInspection.source_current(workflow, plans)
        return {
            **PolicyComparison.build(scope, columns),
            "scope": scope,
            "id": identifier,
            "snapshot_at": source["created_at"],
            "recovery_snapshot_at": backup.created_at,
            "observed_at": source["observed_at"],
            "stale": current != target.original,
            "normalizations": notices,
        }

    @staticmethod
    def target(
        context: Any, scope: str, identifier: str, snapshot_at: str
    ) -> tuple[Any, dict[str, Any], str, list[str]]:
        """Resolve only a selected plan row and the exact source used for its proposal."""
        workflow, plans, _ = context
        if isinstance(workflow, RestoreWorkflow):
            PreparedInspection.source_current(workflow, plans)
            return PreparedInspection.restoration(plans, scope, identifier)
        for plan in plans:
            targets = (
                [plan]
                if scope == "org" and plan.identifier == identifier
                else [site for site in plan.sites if scope == "site" and site.identifier == identifier]
            )
            if targets:
                source = {"settings": targets[0].original, "created_at": snapshot_at}
                return targets[0], source, plan.identifier, []
        raise PolicyError("The selected scope is not in this prepared plan.")

    @staticmethod
    def restoration(plan: Any, scope: str, identifier: str) -> tuple[Any, dict[str, Any], str, list[str]]:
        """Retain historical source values separately from verified current recovery."""
        targets = [target for target in plan.targets if target.scope == scope and target.identifier == identifier]
        if not targets:
            raise PolicyError("The selected scope is not in this prepared plan.")
        source = RestoreSelection.records(plan.bundle, [f"{scope}:{identifier}"])[0]["settings"]
        target = targets[0]
        return (
            target,
            {"settings": source, "created_at": plan.bundle.created_at},
            target.organization,
            [notice for notice in plan.exclusions[target.key] if notice.startswith("normalized:")],
        )

    @staticmethod
    def source_current(workflow: Any, plan: Any) -> None:
        """Reject changed restoration sources and cloud context without modifying proof state."""
        cloud = RestoreSelection.cloud(workflow.api)
        if isinstance(workflow, RestoreWorkflow):
            workflow.files.unchanged(plan.bundle)
            if cloud != plan.cloud:
                raise PolicyError("The active cloud changed after preparation.")
