"""Prepare complete release notes before the release action receives them."""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Literal, Never, cast
from urllib.parse import quote, unquote, urlsplit


class ReleaseBodyError(ValueError):
    """Reject a required input with a fixed message that contains no source text."""


class ReleaseReferences:
    """Bind both release links to the repository and the exact tag event."""

    def __init__(self, repository: str, tag: str, previous_tag: str | None = None) -> None:
        logging.info("phase=references event=before")
        if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+", repository) is None:
            raise ReleaseBodyError("invalid_repository")
        if repository.split("/")[1] in {".", ".."}:
            raise ReleaseBodyError("invalid_repository")
        self.validate_reference(tag)
        if previous_tag is not None:
            self.validate_reference(previous_tag)
        if (
            os.environ.get("GITHUB_EVENT_NAME") != "push"
            or os.environ.get("GITHUB_REF_TYPE") != "tag"
            or os.environ.get("GITHUB_REF") != "refs/tags/" + tag
        ):
            raise ReleaseBodyError("invalid_tag_event")
        self.repository, self.tag, self.previous_tag = repository, tag, previous_tag
        logging.debug("phase=references event=after checked_repositories=1 checked_current_tags=1")

    @staticmethod
    def validate_reference(reference: str) -> None:
        """Accept conservative Git refs without running Git or a shell."""
        if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", reference) is None or ".." in reference:
            raise ReleaseBodyError("invalid_reference")
        if any(not part or part.startswith(".") or part.endswith((".", ".lock")) for part in reference.split("/")):
            raise ReleaseBodyError("invalid_reference")

    def comparison(self, url: str) -> str:
        """Validate the complete comparison and return its previous ref."""
        if re.search(r"[\x00-\x20\x7f\\?#]", url) or re.search(r"%(?![0-9A-Fa-f]{2})", url):
            raise ReleaseBodyError("invalid_compare_url")
        try:
            parsed = urlsplit(url)
        except ValueError:
            raise ReleaseBodyError("invalid_compare_url") from None
        prefix = "/" + self.repository + "/compare/"
        if parsed.scheme != "https" or parsed.netloc != "github.com" or not parsed.path.startswith(prefix):
            raise ReleaseBodyError("wrong_compare_identity")
        parts = parsed.path.removeprefix(prefix).split("...")
        if len(parts) != 2:
            raise ReleaseBodyError("invalid_compare_range")
        previous, current = (unquote(part, encoding="utf-8", errors="strict") for part in parts)
        for reference in (previous, current):
            self.validate_reference(reference)
        if current != self.tag or (self.previous_tag is not None and previous != self.previous_tag):
            raise ReleaseBodyError("compare_reference_conflict")
        return previous

    def resolve(self, body: str) -> tuple[str, str, str]:
        """Retain one complete Full Changelog line and construct the pinned file link."""
        logging.info("phase=compare event=before")
        forms = (
            r"\*\*Full Changelog\*\*: (?P<plain>[^\s<>]+)"
            r"|\*\*Full Changelog\*\*: <(?P<angle>[^\s<>]+)>"
            r"|\[Full Changelog\]\((?P<markdown>[^\s()]+)\)"
        )
        declarations = [
            line for line in body.split("\n") if line.startswith(("**Full Changelog**:", "[Full Changelog]"))
        ]
        logging.debug("phase=compare event=examined checked_comparisons=%d", len(declarations))
        if len(declarations) != 1:
            raise ReleaseBodyError("missing_or_ambiguous_compare")
        match = re.fullmatch("(?:" + forms + r")[ \t]*\r?", declarations[0])
        if match is None:
            raise ReleaseBodyError("incomplete_compare")
        url = next(value for value in match.groups() if value is not None)
        previous = self.comparison(url)
        changelog = "https://github.com/" + self.repository + "/blob/" + quote(self.tag, safe="") + "/CHANGELOG.md"
        logging.debug("phase=compare event=after checked_comparisons=1")
        return url, changelog, previous


class ReleaseNotesSource:
    """Read the complete JSON response without changing its generated text."""

    @staticmethod
    def read(path: Path) -> bytes:
        """Count a source only after a complete byte read succeeds."""
        logging.info("phase=source_read event=before checked_files=0")
        if not path.is_file():
            raise ReleaseBodyError("invalid_source_file")
        content = path.read_bytes()
        logging.debug("phase=source_read event=after checked_files=1")
        return content

    @staticmethod
    def unique_fields(pairs: list[tuple[str, object]]) -> dict[str, object]:
        """Reject duplicate fields instead of selecting an ambiguous body."""
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ReleaseBodyError("duplicate_json_field")
            result[key] = value
        return result

    @staticmethod
    def decode(content: bytes) -> object:
        """Convert decoder limits into a fixed required-input failure."""
        text = content.decode("utf-8")
        try:
            return json.loads(text, object_pairs_hook=ReleaseNotesSource.unique_fields)
        except ReleaseBodyError:
            raise
        except (ValueError, RecursionError):
            raise ReleaseBodyError("invalid_json") from None

    @staticmethod
    def parse(content: bytes) -> dict[str, str]:
        """Require a nonempty body and valid UTF-8 for every present text field."""
        logging.info("phase=source_validation event=before checked_records=0")
        value = ReleaseNotesSource.decode(content)
        allowed = {"body", "name", "repository", "tag_name", "previous_tag_name"}
        if not isinstance(value, dict) or set(value) - allowed:
            raise ReleaseBodyError("invalid_source_record")
        if not isinstance(value.get("body"), str) or not value["body"].strip():
            raise ReleaseBodyError("empty_or_invalid_body")
        if any(not isinstance(item, str) for item in value.values()):
            raise ReleaseBodyError("invalid_source_field")
        record = cast(dict[str, str], value)
        for text in record.values():
            text.encode("utf-8", errors="strict")
        logging.debug("phase=source_validation event=after checked_records=1")
        return record

    @staticmethod
    def metadata(record: Mapping[str, str], references: ReleaseReferences, previous: str) -> None:
        """Reject optional identity fields that disagree with the required links."""
        expected = {"repository": references.repository, "tag_name": references.tag, "previous_tag_name": previous}
        if any(record[key] != value for key, value in expected.items() if key in record):
            raise ReleaseBodyError("source_metadata_conflict")


class ReleaseBody:
    """Compose and persist complete text under the publisher's exact limit."""

    @staticmethod
    def measure(text: str) -> tuple[int, int]:
        """Count Unicode code points and JavaScript UTF-16 units for the same text."""
        return len(text), len(text.encode("utf-16-le", errors="strict")) // 2

    @staticmethod
    def fits(counts: tuple[int, int]) -> bool:
        """Keep both complete-text measurements below the publisher's cut boundary."""
        return counts[0] < 125000 and counts[1] < 125000

    @staticmethod
    def prepare(record: Mapping[str, str], references: ReleaseReferences) -> tuple[str, Literal["full", "summary"]]:
        """Keep the complete candidate when it fits, otherwise use a complete summary."""
        logging.info("phase=composition event=before")
        body = record["body"]
        compare, changelog, previous = references.resolve(body)
        ReleaseNotesSource.metadata(record, references, previous)
        footer = f"[CHANGELOG for `{references.tag}`]({changelog})\n"
        ending = "" if body.endswith("\n") else "\n"
        full = body + ending + "\n" + footer
        codepoints, units = ReleaseBody.measure(full)
        logging.debug(
            "phase=composition event=after candidate_codepoints=%d candidate_utf16_units=%d", codepoints, units
        )
        mode: Literal["full", "summary"] = "full"
        if not ReleaseBody.fits((codepoints, units)):
            mode = "summary"
            full = (
                f"## Release summary for `{references.tag}`\n\n"
                "The full release body exceeds the publication size limit.\n"
                "This summary replaces the generated list. It does not list every change.\n\n"
                f"**Full Changelog**: {compare}\n" + footer
            )
        if not ReleaseBody.fits(ReleaseBody.measure(full)):
            raise ReleaseBodyError("summary_exceeds_limit")
        return full, mode

    @staticmethod
    def verify(path: Path, expected: str) -> tuple[int, int]:
        """Measure the complete file and require exact UTF-8 equality."""
        content = path.read_bytes()
        if content != expected.encode("utf-8"):
            raise ReleaseBodyError("output_does_not_match")
        text = content.decode("utf-8", errors="strict")
        counts = ReleaseBody.measure(text)
        if not text.endswith("\n") or not ReleaseBody.fits(counts):
            raise ReleaseBodyError("invalid_final_body")
        return counts

    @staticmethod
    def write(output: Path, text: str) -> tuple[int, int]:
        """Verify a temporary sibling and the actual publisher path before success."""
        logging.info("phase=output event=before")
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb", dir=output.parent, prefix=".release-body-", delete=False
            ) as handle:
                temporary = Path(handle.name)
                content = text.encode("utf-8", errors="strict")
                if handle.write(content) != len(content):
                    raise ReleaseBodyError("incomplete_write")
                handle.flush()
            ReleaseBody.verify(temporary, text)
            temporary.replace(output)
            counts = ReleaseBody.verify(output, text)
            logging.debug("phase=output event=after checked_files=2 codepoints=%d utf16_units=%d", *counts)
            return counts
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)


class ReleaseBodyCommand:
    """Own the CLI, checked counts, and failure status for release preparation."""

    class Parser(argparse.ArgumentParser):
        """Keep invalid argument values out of failure messages."""

        def error(self, message: str) -> Never:
            """Report a fixed error instead of repeating untrusted arguments."""
            raise ReleaseBodyError("invalid_arguments")

    @staticmethod
    def options(arguments: Sequence[str] | None) -> tuple[Path, Path, ReleaseReferences]:
        """Parse only the required source, output, and release identity options."""
        parser = ReleaseBodyCommand.Parser(description=__doc__, allow_abbrev=False, add_help=False)
        parser.add_argument("--source", type=Path, required=True)
        parser.add_argument("--output", type=Path, required=True)
        parser.add_argument("--tag", required=True)
        parser.add_argument("--repository", required=True)
        parser.add_argument("--previous-tag")
        values = parser.parse_args(None if arguments is None else list(arguments))
        references = ReleaseReferences(values.repository, values.tag, values.previous_tag)
        source, output = ReleaseBodyCommand.paths(values.source, values.output)
        return source, output, references

    @staticmethod
    def paths(source: Path, output: Path) -> tuple[Path, Path]:
        """Restrict both files to the controlled runner directory before any write."""
        scratch = os.environ.get("RUNNER_TEMP")
        if not scratch:
            raise ReleaseBodyError("missing_runner_temp")
        root = Path(scratch).resolve(strict=True)
        if not root.is_dir():
            raise ReleaseBodyError("invalid_runner_temp")
        for path in (source, output):
            if not path.is_absolute() or ".." in path.parts or not path.is_relative_to(root):
                raise ReleaseBodyError("unsafe_file_path")
            if any(item.is_symlink() for item in (path, *path.parents) if item.is_relative_to(root)):
                raise ReleaseBodyError("linked_file_path")
        if source == output or (source.exists() and output.exists() and source.samefile(output)):
            raise ReleaseBodyError("source_is_output")
        if (output.exists() and not output.is_file()) or not output.parent.is_dir():
            raise ReleaseBodyError("invalid_output_path")
        return source, output

    @staticmethod
    def run(arguments: Sequence[str] | None = None) -> int:
        """Return success only after the complete publication file passes verification."""
        checked = 0
        phase = "arguments"
        try:
            source, output, references = ReleaseBodyCommand.options(arguments)
            phase = "source_read"
            content = ReleaseNotesSource.read(source)
            checked = 1
            phase = "preparation"
            record = ReleaseNotesSource.parse(content)
            logging.debug("source_codepoints=%d source_utf16_units=%d", *ReleaseBody.measure(record["body"]))
            text, mode = ReleaseBody.prepare(record, references)
            phase = "output"
            counts = ReleaseBody.write(output, text)
            print(f"Checked 1 release-note file. mode={mode} codepoints={counts[0]} utf16_units={counts[1]}")
            return 0
        except (OSError, UnicodeError, ReleaseBodyError) as error:
            reason = str(error) if isinstance(error, ReleaseBodyError) else type(error).__name__
            logging.error("phase=%s event=failed checked_files=%d reason=%s", phase, checked, reason)
            suffix = "" if checked == 1 else "s"
            print(f"Checked {checked} release-note file{suffix}. phase={phase} reason={reason}", file=sys.stderr)
            return 2


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(message)s")
    raise SystemExit(ReleaseBodyCommand.run())
