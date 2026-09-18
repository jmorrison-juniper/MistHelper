"""Install generated Juniper skills into local agent hosts."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]  # Find the repository root when the script runs by file path.
if str(REPO_ROOT) not in sys.path:  # Ensure the local src package wins over any installed package.
    sys.path.insert(0, str(REPO_ROOT))  # Add the worktree root for imports without changing the current directory.

from src.juniper_skills.install import InstallOutcome, SkillInstaller


class InstallSkillsCli:
    """Parse installer commands and print a concise operator report."""

    def __init__(self) -> None:
        self.parser = self._build_parser()  # Build the parser once so tests can inspect behavior.

    def run(self, argv: list[str] | None = None) -> int:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")  # Give operators a readable log.
        args = self.parser.parse_args(argv)  # Parse the requested install action.
        installer = SkillInstaller(
            args.store, args.repo, args.home
        )  # Build the installer from explicit or default paths.
        outcomes = self._dispatch(args, installer)  # Execute exactly one requested action.
        self._print_outcomes(outcomes)  # Print a stable report for scripts and operators.
        return (
            1 if any(outcome.action in {"failed", "refused"} for outcome in outcomes) else 0
        )  # Fail on unsafe results.

    def _build_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description="Install generated Juniper skills.")  # State the CLI purpose.
        parser.add_argument("skill", nargs="?", help="Install this skill name.")  # Support one-skill installation.
        parser.add_argument(
            "--all", action="store_true", help="Install all canonical skills."
        )  # Support batch install.
        parser.add_argument(
            "--uninstall", metavar="SKILL", help="Remove a skill junction from each host."
        )  # Remove only junctions.
        parser.add_argument(
            "--verify", nargs="?", const="__all__", metavar="SKILL", help="Verify one skill or all skills."
        )  # Verify paths.
        parser.add_argument(
            "--init-store", action="store_true", help="Create or refresh the canonical store files."
        )  # Prepare store.
        parser.add_argument("--store", type=Path, default=None, help="Canonical store path.")  # Permit isolated tests.
        parser.add_argument("--repo", type=Path, default=None, help="Repository root path.")  # Permit isolated tests.
        parser.add_argument("--home", type=Path, default=None, help="User profile path.")  # Permit isolated tests.
        return parser  # Return the complete parser to the CLI runner.

    def _dispatch(self, args: argparse.Namespace, installer: SkillInstaller) -> list[InstallOutcome]:
        if args.init_store:  # Initialize the store when requested.
            return installer.initialize_store()  # Write store metadata and catalog files.
        if args.uninstall:  # Remove a published skill when requested.
            return installer.uninstall_skill(args.uninstall)  # Remove only junctions.
        if args.verify == "__all__":  # Verify all canonical skills when no name follows --verify.
            return installer.verify_all()  # Check every canonical package target.
        if args.verify:  # Verify one canonical skill when a name follows --verify.
            return installer.verify_skill(args.verify)  # Check the named package targets.
        if args.all:  # Install every canonical skill when requested.
            return installer.install_all()  # Publish all packages in the store.
        if args.skill:  # Install one skill when a positional name exists.
            return installer.install_skill(args.skill)  # Publish the named package.
        self.parser.error("choose a skill, --all, --uninstall, --verify, or --init-store")  # Stop on an empty command.

    def _print_outcomes(self, outcomes: list[InstallOutcome]) -> None:
        for outcome in outcomes:  # Print one line per host or generated file.
            print(f"{outcome.action}: {outcome.target} - {outcome.detail}")  # Keep output readable for operators.


if __name__ == "__main__":  # Run the CLI when an operator executes the script.
    raise SystemExit(InstallSkillsCli().run())  # Return a process status that matches the installer report.
