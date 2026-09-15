"""Check that every PCLI command in the console health check exists in the reference."""

from __future__ import annotations

import re
from pathlib import Path

VERBS = (
    "show ",
    "ping",
    "service-ping",
    "traceroute",
    "clear ",
    "release ",
    "refresh ",
    "save ",
    "write ",
    "create ",
    "delete ",
    "restore ",
)


class CommandVerifier:
    """Compare the commands in a runbook against the Session Smart command reference."""

    def __init__(self, runbook: Path, reference: Path) -> None:
        """Store the runbook to check and the reference that defines every command."""
        self.runbook = runbook  # Document whose commands must be real
        self.reference = reference  # Local copy of the vendor command reference

    def run(self) -> list[str]:
        """Return every command that the reference does not define."""
        commands = self._extract()  # Pull the candidate commands out of the runbook
        catalog = self.reference.read_text(encoding="utf-8").lower()  # Search corpus
        return [command for command in sorted(commands) if not self._found(command, catalog)]

    def _extract(self) -> set[str]:
        """Return the normalized PCLI commands that the runbook names."""
        text = self.runbook.read_text(encoding="utf-8")
        found: set[str] = set()
        for snippet in re.findall(r"`([^`]+)`", text):  # Commands appear in inline code spans
            candidate = snippet.strip()
            if not candidate.lower().startswith(VERBS):
                continue
            stripped = re.sub(r"<[^>]*>", "", candidate)  # Drop the placeholder arguments
            found.add(re.sub(r"\s+", " ", stripped).strip().lower())
        return found

    def _found(self, command: str, catalog: str) -> bool:
        """Return True when the reference documents the command or a parent of it."""
        words = [word for word in command.split() if not word.isdigit()]  # Drop literal counts
        for length in range(len(words), 0, -1):  # Match the longest form that the reference holds
            probe = " ".join(words[:length])
            if f"`{probe}`" in catalog or f"## {probe}" in catalog:
                return True
        return False


if __name__ == "__main__":
    UNVERIFIED = CommandVerifier(
        Path("documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md"),
        Path("documentation/references/ssr/cli_reference.md"),
    ).run()
    print("UNVERIFIED COMMANDS:" if UNVERIFIED else "Every command matched the reference.")
    for entry in UNVERIFIED:
        print(f"  - {entry}")
