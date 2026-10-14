"""Expose menu 306 with private selection, safe preview, and exact restoration confirmation."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field

from src.foundation.support.utils.input_utils import InputUtils

from ..cli import PolicyMenuInputs, PolicyPrompt
from ..sdk import PolicyApi, PolicyError
from .backup import PolicyBackup
from .bundle import BundleFiles, RestoreSelection
from .workflow import RestorePlan, RestoreWorkflow

logger = logging.getLogger(__name__)


@dataclass
class RestoreMenu:
    """Run the same complete restoration guards as the protected graphical interface."""

    api: PolicyApi
    inputs: PolicyMenuInputs
    prompt: PolicyPrompt = field(default_factory=PolicyPrompt)

    def run(self) -> None:
        """Refuse cancellation and incorrect confirmation before any settings change."""
        try:
            workflow = RestoreWorkflow(
                self.api, BundleFiles(PolicyBackup(self.inputs.data_directory)), stopped=self.inputs.stopped
            )
            plan = self._plan(workflow)
            print(json.dumps(plan.preview(), indent=2, ensure_ascii=True))
            if self.inputs.dry_run:
                print("Dry run: no settings writes and no new backup files.")
                return
            result = workflow.apply(plan, self._confirm())
            print(json.dumps(asdict(result), indent=2, ensure_ascii=True))
        except (PolicyError, EOFError, KeyboardInterrupt) as error:
            message = str(error) if isinstance(error, PolicyError) else "The restoration was cancelled."
            logger.error("Backup restoration stopped: %s", message)
            print(f"Backup restoration stopped: {message}")

    def _plan(self, workflow: RestoreWorkflow) -> RestorePlan:
        """Collect explicit saved records and cloud binding before the safe preview."""
        bundles = workflow.files.list()
        if not bundles:
            raise PolicyError("No verified private backup is available.")
        token = self.prompt.choice("Private backup", [bundle["token"] for bundle in bundles])
        bundle = workflow.files.read(token)
        records = [f"{record['scope']}:{record['id']}" for record in bundle.records]
        selected = [records[index] for index in self.prompt.indices("Saved scopes", records)]
        print(f"Active Mist cloud: {RestoreSelection.cloud(self.api)}")
        cloud = self.prompt.ask("Type the active cloud hostname to bind this legacy backup: ")
        return workflow.prepare(token, selected, cloud)

    @staticmethod
    def _confirm() -> str:
        """Read the exact confirmation without trimming operator input."""
        logger.info("Ask operator for exact restoration confirmation")
        confirmation = InputUtils.safe_input(
            "Type RESTORE to verify all recovery backups and restore: ", context="backup_restore"
        )
        logger.debug("Restoration confirmation supplied=%s", bool(confirmation))
        return confirmation
