"""Bind verified domain preparations to sanitized asynchronous portal actions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.operations.execution.firmware_policy.changes import FirmwarePolicy
from src.operations.execution.firmware_policy.cli import POLICY_WARNING, PolicyCatalog
from src.operations.execution.firmware_policy.recovery.backup import PolicyBackup
from src.operations.execution.firmware_policy.recovery.bundle import BundleFiles
from src.operations.execution.firmware_policy.recovery.workflow import RestoreWorkflow
from src.operations.execution.firmware_policy.sdk import PolicyApi, PolicyError
from src.operations.execution.firmware_policy.workflow import PolicyWorkflow

from .manager import Progress, Work
from .state import JobErrors, JobState


@dataclass
class JobWorkflows:
    """Capture existing application dependencies without retaining request proxies."""

    api_session: Any
    data_dir: Path

    def policy(self, identifiers: list[str], policies: list[FirmwarePolicy]) -> Work:
        """Resolve names and verify the complete backup before issuing a token."""

        def prepare(progress: Progress) -> tuple[Any, dict[str, Any]]:
            """Execute catalog checks and durable backup with the domain safeguards."""
            api = PolicyApi(self.api_session, progress=progress)  # Reuse the existing authenticated SDK.
            organizations = [api.organization(identifier) for identifier in identifiers]  # Ignore browser names.
            catalogs = PolicyCatalog.common(api, organizations, [policy.kind for policy in policies])
            PolicyCatalog.validate(policies, catalogs)  # Reject unsupported selections before backup.
            workflow = PolicyWorkflow(api, PolicyBackup(self.data_dir), progress=progress)
            plans = [workflow.prepare(organization, policies) for organization in organizations]
            proof = workflow.back_up(plans)  # A failed or unverified backup never becomes ready.
            rows = self.policy_rows(plans)  # Full original settings have no display path.
            preview = dict(
                organizations=[plan.preview() for plan in plans],
                settings_count=len(rows),
                writes=0,
                backup="verified",
                warning=POLICY_WARNING,
            )
            return (workflow, plans, proof), dict(rows=rows, preview=preview, backups_verified=len(rows))

        return prepare  # Executor invocation occurs after the HTTP request returns.

    def restore(self, body: dict[str, Any]) -> Work:
        """Prepare selected records and complete recovery through the existing workflow."""

        def prepare(progress: Progress) -> tuple[Any, dict[str, Any]]:
            """Refuse incomplete recovery before authorizing an explicit restoration."""
            api = PolicyApi(self.api_session, progress=progress)  # Retain existing transport and admission.
            workflow = RestoreWorkflow(api, BundleFiles(PolicyBackup(self.data_dir)), progress=progress)
            plan = workflow.prepare(
                body["bundle"], body["records"], body["cloud"]
            )  # Domain validates source and scope.
            proof = workflow.back_up(plan)  # Verify every complete recovery record before confirmation.
            preview = plan.preview()  # Shared domain preview excludes full settings.
            rows = JobState.rows(
                [
                    dict(
                        scope=target["scope"],
                        id=target["id"],
                        name=target["name"],
                        organization=target["organization_name"],
                        backup="verified",
                        status="ready",
                    )
                    for target in preview["targets"]
                ]
            )
            return (workflow, plan, proof), dict(rows=rows, preview=preview, backups_verified=len(rows))

        return prepare  # Browser-provided paths and settings never become direct SDK arguments.

    @staticmethod
    def apply(context: Any) -> Work:
        """Rebind progress while reusing the exact verified plan and recovery proof."""

        def execute(progress: Progress) -> tuple[Any, dict[str, Any]]:
            """Never run implicit preparation or replay uncertain writes."""
            workflow, plans, proof = context  # This tuple exists only in live private memory.
            workflow.progress = progress  # Apply reports through the same owned job.
            workflow.api.progress = progress  # Admission waits stay visible during application.
            if isinstance(workflow, RestoreWorkflow):
                result = workflow.apply(plans, "RESTORE", proof=proof)  # Domain revalidates the opaque proof.
                failed = len(result.failed)  # Results contain checked target identifiers only.
                public: dict[str, Any] = dict(
                    completed=result.completed,
                    failed=result.failed,
                    remaining=result.remaining,
                    error=JobErrors.message(PolicyError(result.error)) if result.error else None,
                    backups_verified=result.backups_verified,
                )  # Keep checked HTTP failures and recovery counts visible.
            else:
                result = workflow.apply(plans, proof=proof)  # No new automatic write or backup replay.
                failed = len(result.failures)  # Failure text can contain sensitive external values.
                public = dict(
                    organizations=result.organizations,
                    sites=result.sites,
                    unchanged=result.unchanged,
                    failures=[JobErrors.message(PolicyError(message)) for message in result.failures],
                    remaining=result.remaining,
                )
            return None, dict(state="partial" if failed else "complete", result=public)

        return execute  # Atomic token consumption occurs before this action can run.

    @staticmethod
    def policy_rows(plans: Any) -> list[dict[str, Any]]:
        """Publish only names, scope identifiers, and verified backup status."""
        rows = []  # No snapshot or writable settings body enters this list.
        for plan in plans:
            rows.append(
                dict(
                    scope="org",
                    id=plan.identifier,
                    name=plan.name,
                    organization=plan.name,
                    backup="verified",
                    status="ready",
                )
            )
            rows.extend(
                dict(
                    scope="site",
                    id=site.identifier,
                    name=site.name,
                    organization=plan.name,
                    backup="verified",
                    status="ready",
                )
                for site in plan.sites
            )
        return JobState.rows(rows)  # Names sort before identifiers for readable large tables.
