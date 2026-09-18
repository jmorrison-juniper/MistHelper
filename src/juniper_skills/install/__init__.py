"""Install generated Juniper skills into local agent hosts."""

from src.juniper_skills.install.installer import InstallOutcome, SkillInstaller  # Expose the installer API for the CLI.

__all__ = ["InstallOutcome", "SkillInstaller"]  # Keep the public API small for callers.
