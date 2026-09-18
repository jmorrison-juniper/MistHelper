"""Install generated Juniper skills with Windows directory junctions."""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class InstallOutcome:
    """State the result of one install, verify, or uninstall action."""

    target: Path
    action: str
    detail: str


class SkillInstaller:
    """Publish canonical Juniper skills into each local agent host."""

    def __init__(
        self, store_path: Path | None = None, repo_path: Path | None = None, home_path: Path | None = None
    ) -> None:
        self.home_path = home_path or Path.home()  # Use the caller home so tests can isolate host paths.
        self.repo_path = repo_path or Path.cwd()  # Use the active worktree for the repository skill target.
        self.store_path = (
            store_path or self.home_path / "juniper-agent-skills"
        )  # Keep the store outside OneDrive by default.
        self.skills_path = self.store_path / "skills"  # Keep every domain skill below one canonical folder.

    def initialize_store(self) -> list[InstallOutcome]:
        logging.info("Preparing canonical Juniper skill store at %s", self.store_path)  # Log the store creation step.
        self.skills_path.mkdir(parents=True, exist_ok=True)  # Create the skill folder before catalog generation.
        logging.debug("Prepared canonical skill folder at %s", self.skills_path)  # Record the folder that now exists.
        self._write_store_file("README.md", self._readme_text())  # Add operator guidance for the store.
        self._write_store_file(".gitignore", self._store_gitignore_text())  # Keep local artifacts out of the store.
        self._write_store_file("LICENSE", self._license_text())  # Publish the selected knowledge-corpus license.
        return self.generate_catalog()  # Generate the catalog so no operator edits it by hand.

    def install_skill(self, skill_name: str) -> list[InstallOutcome]:
        logging.info("Installing Juniper skill %s", skill_name)  # Log the requested skill publication.
        source_path = self._source_path(skill_name)  # Resolve the canonical package before target checks.
        blockers = self._find_install_blockers(skill_name, source_path)  # Refuse before a partial install can occur.
        if blockers:  # Stop if any target would overwrite a hand-written skill.
            logging.debug(
                "Refused Juniper skill %s with %d blockers", skill_name, len(blockers)
            )  # Count the refused targets.
            return blockers  # Return all blockers so the operator can repair each path.
        outcomes = self._create_junctions(skill_name, source_path)  # Publish the canonical package into each host.
        logging.debug("Installed Juniper skill %s with %d outcomes", skill_name, len(outcomes))  # Count target actions.
        return outcomes + self.generate_catalog()  # Refresh the generated catalog after publication.

    def install_all(self) -> list[InstallOutcome]:
        logging.info("Installing all canonical Juniper skills")  # Log the batch publication step.
        outcomes: list[InstallOutcome] = []  # Collect each skill result for one CLI report.
        for source_path in self._skill_sources():  # Process only real canonical skill folders.
            outcomes.extend(self.install_skill(source_path.name))  # Reuse the single-skill safety checks.
        logging.debug("Installed all Juniper skills with %d outcomes", len(outcomes))  # Record the batch result count.
        return outcomes  # Return the full report to the caller.

    def uninstall_skill(self, skill_name: str) -> list[InstallOutcome]:
        logging.info("Uninstalling Juniper skill %s", skill_name)  # Log the requested skill removal.
        outcomes = [
            self._remove_junction(path) for path in self._target_paths(skill_name)
        ]  # Remove each junction safely.
        logging.debug(
            "Uninstalled Juniper skill %s with %d outcomes", skill_name, len(outcomes)
        )  # Count removal actions.
        return outcomes + self.generate_catalog()  # Keep the catalog current after removal.

    def verify_skill(self, skill_name: str) -> list[InstallOutcome]:
        logging.info("Verifying Juniper skill %s", skill_name)  # Log the verification request.
        source_path = self._source_path(skill_name)  # Resolve the canonical package for the expected target.
        outcomes = [
            self._verify_target(path, source_path) for path in self._target_paths(skill_name)
        ]  # Check each host path.
        logging.debug(
            "Verified Juniper skill %s with %d outcomes", skill_name, len(outcomes)
        )  # Count verification records.
        return outcomes  # Return the host-by-host verification result.

    def verify_all(self) -> list[InstallOutcome]:
        logging.info("Verifying all canonical Juniper skills")  # Log the batch verification request.
        outcomes: list[InstallOutcome] = []  # Collect every verification result for the caller.
        for source_path in self._skill_sources():  # Verify each canonical package that exists.
            outcomes.extend(self.verify_skill(source_path.name))  # Reuse the single-skill verification path.
        logging.debug("Verified all Juniper skills with %d outcomes", len(outcomes))  # Record the result count.
        return outcomes  # Return the full verification report.

    def generate_catalog(self) -> list[InstallOutcome]:
        logging.info("Generating Juniper skill catalog")  # Log the catalog write.
        lines = self._catalog_lines()  # Build catalog lines from the canonical skills folder.
        catalog_path = self.store_path / "CATALOG.md"  # Keep the generated catalog at the store root.
        catalog_path.write_text("\n".join(lines) + "\n", encoding="utf-8")  # Write UTF-8 for GitHub and local tools.
        logging.debug("Generated Juniper skill catalog with %d lines", len(lines))  # Record the catalog size.
        return [
            InstallOutcome(catalog_path, "generated", "catalog updated from canonical skills")
        ]  # Report generation.

    def _write_store_file(self, name: str, content: str) -> None:
        logging.info("Writing canonical store file %s", name)  # Log each store metadata write.
        (self.store_path / name).write_text(content, encoding="utf-8")  # Write deterministic UTF-8 metadata.
        logging.debug("Wrote canonical store file %s", name)  # Record the completed metadata write.

    def _source_path(self, skill_name: str) -> Path:
        source_path = self.skills_path / skill_name  # Use one folder name for each domain skill.
        if not source_path.is_dir():  # Refuse a missing package before any target change.
            raise FileNotFoundError(f"Canonical skill package not found: {source_path}")  # Name the missing package.
        return source_path  # Return the validated package path.

    def _target_paths(self, skill_name: str) -> list[Path]:
        return [  # Return paths in the contract order for predictable reports.
            self.home_path / ".copilot" / "skills" / skill_name,  # Target GitHub Copilot CLI and applications.
            self.home_path / ".claude" / "skills" / skill_name,  # Target Claude local skills.
            self.repo_path / ".github" / "skills" / skill_name,  # Target VS Code repository skills.
        ]

    def _find_install_blockers(self, skill_name: str, source_path: Path) -> list[InstallOutcome]:
        logging.info("Checking install targets for Juniper skill %s", skill_name)  # Log the preflight check.
        blockers = [
            self._blocker_for(path, source_path) for path in self._target_paths(skill_name)
        ]  # Test each target.
        found = [blocker for blocker in blockers if blocker is not None]  # Keep only unsafe targets.
        logging.debug("Found %d install blockers for Juniper skill %s", len(found), skill_name)  # Record blocker count.
        return found  # Return blockers before any junction is created.

    def _blocker_for(self, target_path: Path, source_path: Path) -> InstallOutcome | None:
        if not target_path.exists():  # A missing target is safe to create.
            return None  # Report no blocker for a new junction.
        if self._is_expected_junction(target_path, source_path):  # An existing correct junction is idempotent.
            return None  # Report no blocker when nothing must change.
        detail = "target exists and is not this canonical junction"  # Explain why the installer refused.
        return InstallOutcome(target_path, "refused", detail)  # Preserve hand-written or foreign skill content.

    def _create_junctions(self, skill_name: str, source_path: Path) -> list[InstallOutcome]:
        logging.info("Creating junction targets for Juniper skill %s", skill_name)  # Log target publication.
        self._add_repo_gitignore_entry(skill_name)  # Prevent Git from reading the store through the repo junction.
        outcomes = [
            self._create_junction(path, source_path) for path in self._target_paths(skill_name)
        ]  # Publish all hosts.
        logging.debug(
            "Created %d junction outcomes for Juniper skill %s", len(outcomes), skill_name
        )  # Count host results.
        return outcomes  # Return one outcome for each host target.

    def _create_junction(self, target_path: Path, source_path: Path) -> InstallOutcome:
        if self._is_expected_junction(target_path, source_path):  # Keep an existing correct junction unchanged.
            return InstallOutcome(
                target_path, "unchanged", "junction already points to canonical skill"
            )  # Report no change.
        logging.info("Creating junction %s", target_path)  # Log the junction creation command.
        target_path.parent.mkdir(parents=True, exist_ok=True)  # Create the host skill directory when it is missing.
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(target_path), str(source_path)], check=True
        )  # Create a junction.
        logging.debug("Created junction %s to %s", target_path, source_path)  # Record the created path pair.
        return InstallOutcome(target_path, "created", "junction created to canonical skill")  # Report the new junction.

    def _remove_junction(self, target_path: Path) -> InstallOutcome:
        if not target_path.exists():  # A missing target is already uninstalled.
            return InstallOutcome(target_path, "unchanged", "target is absent")  # Report idempotent removal.
        if not self._is_junction(target_path):  # Never remove a real directory or file.
            return InstallOutcome(target_path, "refused", "target is not a junction")  # Preserve hand-written content.
        logging.info("Removing junction %s", target_path)  # Log the safe removal action.
        target_path.rmdir()  # Remove the junction itself without deleting canonical files.
        logging.debug("Removed junction %s", target_path)  # Record the completed removal.
        return InstallOutcome(
            target_path, "removed", "junction removed without deleting canonical skill"
        )  # Report removal.

    def _verify_target(self, target_path: Path, source_path: Path) -> InstallOutcome:
        if not self._is_expected_junction(target_path, source_path):  # Require the host path to point at the store.
            return InstallOutcome(
                target_path, "failed", "target is not the expected canonical junction"
            )  # Report mismatch.
        skill_file = target_path / "SKILL.md"  # Use the required skill entry file for readability proof.
        if not skill_file.is_file():  # A skill without SKILL.md cannot be discovered by the host.
            return InstallOutcome(target_path, "failed", "SKILL.md is missing")  # Report the missing entry file.
        detail = (
            f"read {len(skill_file.read_text(encoding='utf-8'))} characters from SKILL.md"  # Prove file readability.
        )
        return InstallOutcome(target_path, "verified", detail)  # Report a readable junction target.

    def _is_expected_junction(self, target_path: Path, source_path: Path) -> bool:
        if not self._is_junction(target_path):  # Only a junction can be an expected host target.
            return False  # Reject real directories and files.
        return target_path.resolve() == source_path.resolve()  # Compare resolved paths to prove the target source.

    def _is_junction(self, target_path: Path) -> bool:
        checker = getattr(
            target_path, "is_junction", None
        )  # Use the Windows junction detector when Python supplies it.
        return bool(checker and checker())  # Return false on non-Windows platforms and old Python versions.

    def _add_repo_gitignore_entry(self, skill_name: str) -> None:
        logging.info("Adding repository gitignore entry for %s", skill_name)  # Log the repository guard update.
        gitignore_path = self.repo_path / ".gitignore"  # Keep the guard in the repository ignore file.
        entry = f".github/skills/{skill_name}/"  # Ignore the junction path before Git traverses it.
        content = (
            gitignore_path.read_text(encoding="utf-8") if gitignore_path.exists() else ""
        )  # Preserve current rules.
        if entry not in content.splitlines():  # Add the entry only once for idempotence.
            gitignore_path.write_text(
                content.rstrip() + "\n" + entry + "\n", encoding="utf-8"
            )  # Append the guard entry.
        logging.debug("Repository gitignore contains entry %s", entry)  # Record that the guard is present.

    def _skill_sources(self) -> list[Path]:
        if not self.skills_path.exists():  # A missing skill folder means no packages exist yet.
            return []  # Return an empty list for idempotent batch operations.
        return sorted(path for path in self.skills_path.iterdir() if path.is_dir())  # Use folders as skill packages.

    def _catalog_lines(self) -> list[str]:
        lines = [
            "# Skill catalog",
            "",
            "This file is generated by the Juniper skill installer. Do not edit it by hand.",
            "",
        ]
        sources = self._skill_sources()  # Read canonical packages each time so the catalog cannot drift.
        if not sources:  # State the empty store clearly for first use.
            return lines + ["No domain skills are installed."]  # Keep the empty catalog valid Markdown.
        lines.extend(["| Skill | Entry file |", "| - | - |"])  # Use a stable table for publishable documentation.
        lines.extend(f"| `{path.name}` | `skills/{path.name}/SKILL.md` |" for path in sources)  # List every package.
        return lines  # Return the generated catalog lines.

    def _readme_text(self) -> str:
        return "\n".join(  # Build deterministic STE prose for the canonical store.
            [
                "# Juniper agent skills",
                "",
                "This repository is the canonical store for generated Juniper domain skills.",
                "",
                "The skill factory publishes each skill to agent hosts with Windows directory junctions.",
                "The source of truth stays here.",
                "",
                "## License choice",
                "",
                "This repository uses the Creative Commons Attribution 4.0 International License.",
                "",
                "CC-BY-4.0 fits this corpus because the files restate technical facts for reading and distribution.",
                "MIT fits software better than a knowledge corpus.",
                "Juniper Networks holds the copyright of the source documents.",
                "This repository must not copy source prose.",
                "",
                "## Layout",
                "",
                "- `skills/` holds one directory for each domain skill.",
                "- `CATALOG.md` lists the installed domain skills.",
                "- Generate `CATALOG.md` with the installer. Do not edit it by hand.",
                "",
                "## Follow-up",
                "",
                "No GitHub remote exists yet.",
                "The repository owner must approve the remote name and visibility before publication.",
            ]
        )

    def _store_gitignore_text(self) -> str:
        return "\n".join(
            [
                "# Local build artifacts",
                "__pycache__/",
                "*.py[cod]",
                ".pytest_cache/",
                "",
                "# Editor state",
                ".vscode/",
                ".idea/",
                "",
            ]
        )

    def _license_text(self) -> str:
        return "\n".join(  # Keep the license file short and point to the complete public license text.
            [
                "Creative Commons Attribution 4.0 International Public License",
                "",
                "This repository is licensed under CC-BY-4.0.",
                "",
                "You may share and adapt this material for any purpose if you give appropriate credit.",
                "Link to the license and state if changes were made.",
                "",
                "The full license text is available at:",
                "https://creativecommons.org/licenses/by/4.0/legalcode",
                "",
                "Juniper Networks holds the copyright of the source documents.",
                "This repository stores restated knowledge only and must not copy source prose.",
                "",
            ]
        )
