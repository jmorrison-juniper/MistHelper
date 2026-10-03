"""Count every required source and reject unused output settings."""

from __future__ import annotations  # Keep test annotations independent of import order.

import hashlib  # Protect the complete compose and readiness sources.
import logging  # Report file decisions without credential values.
import re  # Recognize command boundaries without running configuration.
import shlex  # Distinguish active settings from shell comments.
from dataclasses import dataclass  # Keep counted results explicit.
from pathlib import Path  # Keep live and temporary paths separate.


@dataclass(frozen=True)
class ContractReport:
    """Describe every rejected input and the successful read count."""

    expected: int  # Retain the required input count even when reading fails.
    checked: int  # Count successful reads, not attempted reads.
    failures: tuple[tuple[Path, str], ...]  # Keep one reason for each rejected path.

    @property
    def rejected(self) -> int:
        """Count each rejected input once."""
        return len(self.failures)  # Include unreadable inputs in the failure count.

    def render(self) -> str:
        """Return exact counts followed by path-specific reasons."""
        logging.info("Render the contract result for %s inputs", self.expected)  # Make the guard scope visible.
        counts = f"expected={self.expected} checked={self.checked} rejected={self.rejected}"  # Never infer success.
        reasons = [f"REJECT {path}: {reason}" for path, reason in self.failures]  # Name every failed input.
        result = "\n".join([counts, *reasons])  # Keep the output useful in a failed assertion.
        logging.debug("Rendered %s rejected paths", len(reasons))  # Report the actual failure count.
        return result  # Let tests retain the full decision evidence.


class DeclarationGuard:
    """Recognize settings without executing any source."""

    @classmethod
    def shell(cls, text: str) -> str | None:
        """Reject assignments at a command boundary or in an export command."""
        logging.info("Inspect active session settings")  # Begin the source decision before text processing.
        statements = text.replace("\\\n", " ").splitlines()  # Preserve complete comments and continued commands.
        rejected = any(cls.shell_line(statement) for statement in statements)  # Do not split quoted semicolons.
        logging.debug("Session setting decision rejected=%s", rejected)  # Report the decision after inspection.
        return "active unused OUTPUT_FORMAT assignment" if rejected else None  # Reject every assigned value.

    @classmethod
    def shell_line(cls, statement: str) -> bool:
        """Keep comment and quote boundaries while inspecting each command."""
        logging.info("Inspect one shell command line")  # Mark lexical processing without executing source.
        lexer = shlex.shlex(statement, posix=True, punctuation_chars=";&|")  # Retain operators outside quotes only.
        lexer.whitespace_split = True  # Keep assignment operands intact.
        words: list[str] = []  # Inspect only the current command's declaration scope.
        for word in lexer:  # Ignore comment-only settings through the standard lexer.
            if word in {";", "&&", "||", "|", "&"}:  # Operators start a new active command.
                if cls.shell_command(words):  # A setting before the operator still counts.
                    logging.debug("Shell command before an operator declares OUTPUT_FORMAT")  # Report the decision.
                    return True  # Do not ignore a setting followed by another command.
                words = []  # Ordinary arguments cannot carry into the next command.
            else:  # A quoted operator is an ordinary operand.
                words.append(word)  # Preserve its command context.
        rejected = cls.shell_command(words)  # Check the final command or an empty comment.
        logging.debug("Final shell command rejected=%s", rejected)  # Report the completed lexical decision.
        return rejected  # Comment text cannot supply a declaration.

    @staticmethod
    def shell_command(words: list[str]) -> bool:
        """Inspect only the assignment-bearing part of one command."""
        for word in words:  # Stop when an ordinary command starts.
            if word.startswith("OUTPUT_FORMAT="):  # The value does not make an unused setting useful.
                return True  # Name this command as an active declaration.
            if word in {
                "export",
                "readonly",
                "declare",
                "typeset",
                "local",
                "env",
                "then",
                "do",
                "else",
            }:  # Include scope.
                continue  # Inspect their setting operands.
            if word.startswith("-") or re.match(r"[A-Za-z_][A-Za-z_0-9]*=", word):  # Allow flags and prior settings.
                continue  # Inspect the remaining declaration operands.
            break  # An argument to echo or another ordinary command is not an assignment.
        return False  # No active assignment occurred before an ordinary command.

    @staticmethod
    def image(text: str) -> str | None:
        """Reject legacy and multi-setting image ENV declarations."""
        logging.info("Inspect active image settings")  # Begin inspection without executing the image source.
        instructions = re.findall(
            r"^\s*ENV\s+(.+)$", text.replace("\\\n", " "), flags=re.M | re.I
        )  # Join continuations.
        for instruction in instructions:  # Check every active ENV instruction.
            words = shlex.split(instruction, comments=True)  # Normalize quoted names and values.
            if any(word == "OUTPUT_FORMAT" or word.startswith("OUTPUT_FORMAT=") for word in words):  # Cover both forms.
                logging.debug("Image setting decision rejected=%s", True)  # Report the active setting.
                return "active unused OUTPUT_FORMAT image setting"  # Reject SQLite and all other values.
        logging.debug("Image setting decision rejected=%s", False)  # Report a complete scan.
        return None  # Comment-only declarations do not configure an image.

    @staticmethod
    def documentation(text: str) -> str | None:
        """Require the actual SQLite instruction, not an unrelated flag example."""
        logging.info("Inspect the SQLite selection instruction")  # Mark the documentation decision.
        sections = text.split("## SQLite\n", maxsplit=1)  # Restrict the flag proof to the SQLite section.
        instruction = sections[-1].strip().split("\n\n", maxsplit=1)[0]  # Read the first instruction paragraph.
        required = "Use `--output-format sqlite` to select SQLite output."  # Keep selection explicit.
        valid = len(sections) == 2 and instruction == required and "OUTPUT_FORMAT" not in text  # Exclude alternatives.
        logging.debug("SQLite instruction decision valid=%s", valid)  # State the completed decision.
        return (
            None
            if valid
            else "SQLite selection must require --output-format sqlite, without an environment alternative"
        )


class ProtectedGuard:
    """Keep the complete active compose and readiness behavior at the base."""

    HASHES = {  # Byte identity also protects settings outside the tested readiness matrix.
        "compose.yml": "dd50436f3e5e92df9dc57071ba35ec6155f2ac2e371e1a9c2e3e15c913b335fb",
        "web_portal/routes/dashboard.py": "8d5f41817efbb24fd2b4e856399afee62617f56450ed993a091e0ddb7d0f9424",
    }

    @classmethod
    def rejection(cls, relative: str, text: str) -> str | None:
        """Reject changes to a protected input instead of applying a default."""
        logging.info("Compare protected input %s", relative)  # Mark the whole-source comparison.
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()  # Compare the content actually read by the guard.
        valid = digest == cls.HASHES[relative]  # Require the supplied immutable base.
        logging.debug("Protected input %s matches=%s", relative, valid)  # Report the full-source decision.
        return None if valid else "protected compose or readiness source differs from the immutable base"


@dataclass(frozen=True)
class SourceContract:
    """Read all six paths even when an earlier path fails."""

    root: Path  # Make temporary inputs and live inputs use the same decisions.
    REPOSITORY = Path(__file__).resolve().parents[4]  # Pytest changes the working directory.
    PATHS = (  # The fixed six-input scope must not shrink after a failed read.
        "container/scripts/misthelper-session.sh",
        "Dockerfile",
        "Containerfile",
        "documentation/wiki/Data-Model.md",
        "compose.yml",
        "web_portal/routes/dashboard.py",
    )

    def evaluate(self) -> ContractReport:
        """Count readable inputs and retain every failure."""
        checked = 0  # A failed read must not contribute to this count.
        failures: list[tuple[Path, str]] = []  # Preserve path-specific decisions.
        for index, relative in enumerate(self.PATHS):  # Complete the fixed scope after any rejection.
            path = self.root / relative  # Keep the path in the selected input tree.
            logging.info("Read required contract input %s", path)  # Log before the file read.
            try:  # An unreadable input must fail rather than become empty text.
                text = path.read_bytes().decode("utf-8")  # Keep newline bytes in the protected-source comparison.
                checked += 1  # Count only a successful read.
                logging.debug("Read %s characters from %s", len(text), path)  # Report the completed read.
                reason = self.rejection(index, relative, text)  # Apply the unchanged source decision.
            except (OSError, UnicodeError, ValueError) as error:  # Include permission and malformed-source decisions.
                reason = f"{type(error).__name__}: {error}"  # Keep the actual cause instead of a silent default.
                logging.debug("Input %s failed with %s", path, type(error).__name__)  # Do not log source contents.
            if reason is not None:  # Count an input only once, whether reading or checking failed.
                failures.append((path, reason))  # Preserve the exact rejected path.
        return ContractReport(len(self.PATHS), checked, tuple(failures))  # Report the actual fixed scope.

    @staticmethod
    def rejection(index: int, relative: str, text: str) -> str | None:
        """Select the guard for the required input kind."""
        if index == 0:  # The session source uses shell declaration syntax.
            return DeclarationGuard.shell(text)  # Keep inherited environment behavior separate.
        if index in (1, 2):  # Both tools must reject every unused image declaration.
            return DeclarationGuard.image(text)  # Apply one rule to the two equivalent images.
        if index == 3:  # Only the data-model page describes CLI selection.
            return DeclarationGuard.documentation(text)  # Require the explicit selection instruction.
        return ProtectedGuard.rejection(relative, text)  # Protect active readers instead of deleting them.


@dataclass(frozen=True)
class ContractCopies:
    """Build repaired or immutable test inputs below an owned directory."""

    root: Path  # Keep mutations outside the checkout.
    ORIGINAL_HASHES = (
        "6ab8a7b1a0cbb7e502a909d074a5cd08df0f1e160160009ef98a7a5595bb9690",
        "a9550853151c638cdf8ab1c80e5b5f2680753689467038411b3b58832207c77a",
        "a9550853151c638cdf8ab1c80e5b5f2680753689467038411b3b58832207c77a",
        "62a16f51d5477694a3f270a318bdbb432dc3dfed55a3a6132a1fcde60053c8d8",
        "b951b7218fe7d6fd35cb3ecd571598505949528eae4be1a7971b17d8b156be3b",
        "8d5f41817efbb24fd2b4e856399afee62617f56450ed993a091e0ddb7d0f9424",
    )
    FALSE_INSTRUCTION = "Set `--output-format sqlite` or `OUTPUT_FORMAT=sqlite` environment variable."
    CORRECT_INSTRUCTION = "Use `--output-format sqlite` to select SQLite output."

    @classmethod
    def create(cls, destination: Path, *, original: bool = False) -> ContractCopies:
        """Copy all six sources and repair only temporary copies when requested."""
        for index, relative in enumerate(SourceContract.PATHS):  # Keep temporary guard inputs complete.
            logging.info("Prepare owned contract copy %s", relative)  # Mark the source read and local transformation.
            text = (SourceContract.REPOSITORY / relative).read_bytes().decode("utf-8")
            text = cls.original(index, text) if original else cls.repair(index, text)
            logging.debug("Prepared %s characters for %s", len(text), relative)  # Report the prepared copy size.
            cls(destination).write(index, text)  # Store the copy below the test's own root.
        return cls(destination)  # Give mutation tests the owned input set.

    @classmethod
    def original(cls, index: int, text: str) -> str:
        """Restore the measured original bytes without requiring Git history."""
        repaired = cls.repair(index, text)
        if index == 0:
            anchor = "export PYTHONUNBUFFERED=1\n"
            original = repaired.replace(anchor, anchor + "export OUTPUT_FORMAT=sqlite\n", 1)
        elif index in (1, 2):
            anchor = "ENV PYTHONUNBUFFERED=1\n"
            original = repaired.replace(anchor, anchor + "ENV OUTPUT_FORMAT=sqlite\n", 1)
        elif index == 3:
            original = repaired.replace(cls.CORRECT_INSTRUCTION, cls.FALSE_INSTRUCTION, 1)
        else:
            original = repaired
        digest = hashlib.sha256(original.encode("utf-8")).hexdigest()
        if digest != cls.ORIGINAL_HASHES[index]:
            raise ValueError(f"original input {SourceContract.PATHS[index]} differs from its measured bytes")
        return original

    @classmethod
    def repair(cls, index: int, text: str) -> str:
        """Apply only the selected option-2 changes to test copies."""
        logging.info("Repair temporary contract input %s", index)  # Mark the controlled transformation.
        if index == 0:  # The shell declaration has one exact original spelling.
            text = text.replace("export OUTPUT_FORMAT=sqlite\n", "")  # Do not add an environment reader.
        elif index in (1, 2):  # Each image has the same unused line.
            text = text.replace("ENV OUTPUT_FORMAT=sqlite\n", "")  # Preserve supported SQLite functionality.
        elif index == 3:  # The page needs one explicit selection instruction.
            text = text.replace(cls.FALSE_INSTRUCTION, cls.CORRECT_INSTRUCTION)  # Exclude environment-only selection.
        logging.debug("Temporary input %s now has %s characters", index, len(text))  # Report the changed copy size.
        return text  # Protected inputs pass through byte-identical.

    def write(self, index: int, text: str) -> Path:
        """Write one mutation to an owned required-input path."""
        path = self.root / SourceContract.PATHS[index]  # Use the same path layout as the live contract.
        logging.info("Write owned contract input %s", path)  # Mark the temporary file operation.
        path.parent.mkdir(parents=True, exist_ok=True)  # Keep every created directory below the test root.
        path.write_text(text, encoding="utf-8", newline="\n")  # Keep shell and image line endings stable.
        logging.debug("Wrote %s characters to %s", len(text), path)  # Report size without file contents.
        return path  # Let assertions identify the exact rejected input.
