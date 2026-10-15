"""Provide menu 305 selections and a shared catalog for the graphical policy workflow."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.foundation.support.utils.input_utils import InputUtils

from .changes import POLICY_TYPES, FirmwarePolicy
from .recovery.backup import PolicyBackup
from .sdk import PolicyApi, PolicyError
from .workflow import OrganizationChange, PolicyResult, PolicyWorkflow

logger = logging.getLogger(__name__)
POLICY_WARNING = (
    "Warning: enabled policies can cause later cloud-managed upgrades. "
    "This operation sends no firmware upgrade or device-push request."
)


class PolicyCatalog:
    """Expose model-specific versions and common choices across selected organizations."""

    @staticmethod
    def available(api: PolicyApi, org_id: str, kind: str) -> dict[str, list[str]]:
        """Validate catalog rows and associate SSR versions with actual gateway models."""
        rows = api.versions(org_id, kind)  # Use the SDK catalog matching the hardware type.
        if kind == "ssr":
            rows = PolicyCatalog.ssr_rows(api.models(org_id), rows)  # Use authoritative model constants.
        result = PolicyCatalog.group(rows, kind)  # Validate the individual catalog rows separately.
        if not result:
            raise PolicyError(f"No available model versions were found for {kind} in organization {org_id}.")
        return result  # Retain the exact validated SDK version strings.

    @staticmethod
    def ssr_rows(definitions: list[dict[str, Any]], versions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Associate shared SSR packages with authoritative SSR model constants."""
        models = {
            row["model"] for row in definitions if isinstance(row.get("model"), str) and "SSR" in row["model"].upper()
        }
        return [
            {"model": model, "version": row.get("version")}
            for row in versions
            for model in (models & {row["model"]} if isinstance(row.get("model"), str) else models)
        ]  # Preserve a catalog's explicit model constraint when present.

    @staticmethod
    def group(rows: list[dict[str, Any]], kind: str) -> dict[str, list[str]]:
        """Validate model and version records without treating malformed data as empty."""
        result: dict[str, list[str]] = {}  # Preserve exact model names and complete version strings.
        for row in rows:
            model, version = row.get("model"), row.get("version")  # Validate before string operations.
            if not isinstance(model, str) or not model.strip() or not isinstance(version, str) or not version.strip():
                raise PolicyError("The firmware catalog contains an invalid model or version.")
            if kind in ("switch", "juniper_srx") and ("SRX" in model.upper()) != (kind == "juniper_srx"):
                continue  # Mixed switch and gateway responses must keep SRX models exclusive to the SRX policy.
            result.setdefault(model, []).append(version)  # Retain every allowed choice for the model.
        return {
            model: sorted(set(versions), key=PolicyApi.version_key, reverse=True)
            for model, versions in sorted(result.items())
        }

    @classmethod
    def common(
        cls, api: PolicyApi, organizations: list[dict[str, Any]], kinds: list[str]
    ) -> dict[str, dict[str, list[str]]]:
        """Offer only shared model/version pairs valid in every selected organization."""
        combined: dict[str, dict[str, list[str]]] = {}  # A shared MSP policy must be valid in each target.
        for kind in kinds:
            catalogs = [cls.available(api, org["id"], kind) for org in organizations]  # Validate all targets.
            models = set.intersection(*(set(catalog) for catalog in catalogs))  # Exclude unavailable models.
            combined[kind] = {
                model: sorted(
                    set.intersection(*(set(catalog[model]) for catalog in catalogs)),
                    key=PolicyApi.version_key,
                    reverse=True,
                )
                for model in sorted(models)
            }
            combined[kind] = {model: versions for model, versions in combined[kind].items() if versions}
            if not combined[kind]:
                raise PolicyError(f"The selected organizations have no shared versions for {kind}.")
        return combined  # The caller cannot select a version unavailable in another selected organization.

    @staticmethod
    def validate(policies: list[FirmwarePolicy], catalogs: dict[str, dict[str, list[str]]]) -> None:
        """Validate posted or selected model choices against the SDK catalogs."""
        kinds = [policy.kind for policy in policies]  # Each hardware policy may appear only once.
        if not kinds or len(set(kinds)) != len(kinds):
            raise PolicyError("Select at least one unique device type.")
        for policy in policies:
            for model, version in policy.models.items():
                if version not in catalogs.get(policy.kind, {}).get(model, []):
                    raise PolicyError(f"The selected version is not available for {policy.kind} model {model}.")


@dataclass
class PolicyPrompt:
    """Read strict operator choices without enabling settings through empty input."""

    reader: Callable[[str], str] = lambda prompt: InputUtils.safe_input(prompt, context="firmware_policy")

    def ask(self, prompt: str) -> str:
        """Stop safely on blank input, EOF, interrupt, or an explicit cancellation."""
        logger.info("Ask firmware policy operator: %s", prompt)  # The prompt contains no credential.
        try:
            answer = self.reader(prompt).strip()  # InputUtils handles terminal EOF and interrupt.
        except (EOFError, KeyboardInterrupt):
            raise PolicyError("The firmware policy operation was cancelled.") from None
        logger.debug("Firmware policy answer supplied=%s", bool(answer))  # Never record the answer value.
        if not answer or answer.lower() == "cancel":
            raise PolicyError("The firmware policy operation was cancelled.")
        return answer  # Each caller validates its expected choice.

    def indices(self, label: str, items: list[str]) -> list[int]:
        """Use the existing all-or-index selection pattern without accepting partial input."""
        for index, item in enumerate(items, 1):
            print(f"{index}: {item}")  # Show every selectable value without hidden defaults.
        answer = self.ask(f"{label}: A for all, or comma-separated numbers: ")
        if answer.upper() == "A":
            return list(range(len(items)))  # An explicit A selects the complete list.
        try:
            selected = sorted({int(value.strip()) - 1 for value in answer.split(",")})
        except ValueError:
            raise PolicyError("Enter valid selection numbers.") from None
        if not selected or any(index < 0 or index >= len(items) for index in selected):
            raise PolicyError("A selection number is outside the displayed list.")
        return selected  # No invalid member can silently disappear.

    def choice(self, label: str, items: list[str]) -> str:
        """Require exactly one displayed choice."""
        selected = self.indices(label, items)  # Share the checked index parser.
        if len(selected) != 1:
            raise PolicyError("Select exactly one displayed choice.")
        return items[selected[0]]  # The choice belongs to the available set.

    def policy(self, kind: str, catalog: dict[str, list[str]]) -> FirmwarePolicy:
        """Select model versions and explicit enablement, with AP-only scheduling."""
        models = list(catalog)  # Keep the stable catalog display order.
        selected = self.indices(f"Models for {kind}", models)  # The operator selects the targeted model set.
        versions = {
            models[index]: self.choice(f"Version for {models[index]}", catalog[models[index]]) for index in selected
        }
        state = self.ask(f"Enable {kind} policy? Type ENABLE or DISABLE: ")
        if state not in ("ENABLE", "DISABLE"):
            raise PolicyError("Type ENABLE or DISABLE for each selected policy.")
        day, time = "any", "any"  # Types without a schedule do not ask for one.
        if kind == "ap":
            day = self.ask("AP day: any, mon, tue, wed, thu, fri, sat, sun: ")
            time = self.ask("AP time: HH:MM or any, in each site's time zone: ")
        return FirmwarePolicy(kind, state == "ENABLE", versions, day, time)  # Validate the complete selected policy.


@dataclass
class PolicyMenuInputs:
    """Hold menu context and familiar MSP selectors as explicit dependencies."""

    organization: Callable[[], str | None]
    selectors: tuple[Callable[[], list[Any]], Callable[[dict[str, Any]], list[Any]]] | None = None
    stopped: Callable[[], bool] = lambda: False
    dry_run: bool = False
    data_directory: Path = Path("data")


@dataclass
class PolicyMenu:
    """Run the settings-only policy workflow from the numbered CLI menu."""

    api: PolicyApi
    inputs: PolicyMenuInputs
    prompt: PolicyPrompt = field(default_factory=PolicyPrompt)

    def run(self) -> None:
        """Collect the complete plan and require confirmation before the backup gate."""
        try:
            print(POLICY_WARNING)  # Do not promise that an enabled policy prevents future upgrades.
            organizations = self._organizations()  # Reuse existing MSP selection without executing upgrades.
            kinds = [POLICY_TYPES[index] for index in self.prompt.indices("Device types", list(POLICY_TYPES))]
            catalogs = PolicyCatalog.common(self.api, organizations, kinds)  # Validate every organization first.
            policies = [self.prompt.policy(kind, catalogs[kind]) for kind in kinds]  # Select shared model values.
            PolicyCatalog.validate(policies, catalogs)  # Refuse a version not in each organization's catalog.
            workflow = PolicyWorkflow(self.api, PolicyBackup(self.inputs.data_directory), self.inputs.stopped)
            plans = [workflow.prepare(organization, policies) for organization in organizations]
            self._preview(plans)  # Show every target and all selected policy fields.
            if self.inputs.dry_run:
                print("Dry run: no settings writes and no backup files. The displayed changes are planned only.")
                return  # A dry run cannot reach the backup or settings write boundary.
            if self.prompt.ask("Type CONFIGURE to verify all backups and save these settings: ") != "CONFIGURE":
                raise PolicyError("The firmware policy operation was cancelled.")
            self._report(workflow.apply(plans))  # Back up all scopes before the first cloud change.
        except PolicyError as error:
            logger.error("Firmware policy operation stopped: %s", error)  # Report checked, redacted reasons.
            print(f"Firmware policy stopped: {error}")  # Cancellation and failure never appear as success.

    def _organizations(self) -> list[dict[str, Any]]:
        """Use current organization or the menu 168 MSP organization selectors."""
        if (
            self.inputs.selectors
            and self.prompt.choice("Scope", ["Current organization", "MSP organizations"]) == "MSP organizations"
        ):
            select_msps, select_organizations = self.inputs.selectors  # Reuse only read-only selection methods.
            organizations = [org for msp in select_msps() for org in select_organizations(msp)]
        else:
            identifier = self.inputs.organization()  # Use the established cached or prompted org selection.
            organizations = [{"id": identifier, "name": identifier}] if identifier else []
        if not organizations:
            raise PolicyError("No organization was selected.")
        return list({org["id"]: org for org in organizations}.values())  # Avoid duplicate MSP organization targets.

    @staticmethod
    def _preview(plans: list[OrganizationChange]) -> None:
        """Show full policy and site targets without unrelated settings or backup content."""
        print("All AP, switch, SSR, and SRX site overrides will be removed, including unselected policy types.")
        for plan in plans:
            print(json.dumps(plan.preview(), indent=2, ensure_ascii=True))  # Preview only sanitized policy records.
        print("All complete organization and site settings backups must verify before the first change.")

    @staticmethod
    def _report(result: PolicyResult) -> None:
        """Report verified completion, unchanged targets, failures, and remaining work."""
        print(f"Verified organization changes: {len(result.organizations)}")
        print(f"Verified site changes: {len(result.sites)}. Unchanged sites: {len(result.unchanged)}.")
        for failure in result.failures:
            print(f"Partial completion: {failure}")  # A failed run must never report full success.
        print(f"Remaining sites: {len(result.remaining)}")
