"""Prove complete output and required release-body failures without a network."""

import json
import logging
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch
from urllib.parse import quote

import pytest

from scripts.release_body import ReleaseBody, ReleaseBodyCommand, ReleaseReferences


class ReleaseFixtures:
    """Supply local files and the tag event that the release workflow uses."""

    repository = "jmorrison-juniper/MistHelper"
    tag = "v26.09.26.06.19"
    compare = "https://github.com/jmorrison-juniper/MistHelper/compare/v26.05.21.19.37...v26.09.26.06.19"

    @dataclass
    class Files:
        root: Path
        source: Path
        output: Path

        @property
        def arguments(self) -> tuple[str, ...]:
            """Invoke the real command with explicit local input and output."""
            return (
                "--source",
                str(self.source),
                "--output",
                str(self.output),
                "--tag",
                ReleaseFixtures.tag,
                "--repository",
                ReleaseFixtures.repository,
            )

        def write(self, value: object) -> None:
            """Write complete fixtures, including deliberately invalid byte input."""
            record = {"body": value} if isinstance(value, str) else value
            content = value if isinstance(value, bytes) else json.dumps(record).encode("utf-8")
            self.source.write_bytes(content)

    @pytest.fixture
    def release(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Files:
        """Keep every file and environment change inside one offline test."""
        root = tmp_path.resolve()
        for key, value in {
            "RUNNER_TEMP": str(root),
            "GITHUB_EVENT_NAME": "push",
            "GITHUB_REF_TYPE": "tag",
            "GITHUB_REF": "refs/tags/" + self.tag,
        }.items():
            monkeypatch.setenv(key, value)
        files = self.Files(root, root / "notes.json", root / "body.md")
        files.write("Complete notes.\n\n**Full Changelog**: " + self.compare)
        return files


class TestCompleteBodies(ReleaseFixtures):
    """Measure the whole emitted file, not a prefix or the generated source alone."""

    @pytest.mark.parametrize(
        ("target", "mode"), [(124998, "full"), (124999, "full"), (125000, "summary"), (125001, "summary")]
    )
    def test_final_boundary(
        self, release: ReleaseFixtures.Files, capsys: pytest.CaptureFixture[str], target: int, mode: str
    ) -> None:
        """Include the footer and final LF in the exact boundary decision."""
        footer = f"[CHANGELOG for `{self.tag}`](https://github.com/{self.repository}/blob/{self.tag}/CHANGELOG.md)\n"
        overhead = len("* Change \n\n**Full Changelog**: " + self.compare + "\n\n" + footer)
        source = "* Change " + "x" * (target - overhead) + "\n\n**Full Changelog**: " + self.compare
        release.write(source)
        assert ReleaseBodyCommand.run(release.arguments) == 0
        actual = release.output.read_bytes().decode("utf-8")
        assert actual.endswith(footer)
        assert "**Full Changelog**: " + self.compare + "\n" in actual
        assert ReleaseBody.measure(actual)[1] < 125000
        assert len(actual) < 125000
        assert "mode=" + mode in capsys.readouterr().out
        if mode == "full":
            assert actual == source + "\n\n" + footer
            assert ReleaseBody.measure(actual) == (target, target)
        else:
            assert actual == (
                f"## Release summary for `{self.tag}`\n\n"
                "The full release body exceeds the publication size limit.\n"
                "This summary replaces the generated list. It does not list every change.\n\n"
                f"**Full Changelog**: {self.compare}\n" + footer
            )

    @pytest.mark.parametrize("ending", ["", "\n", "\r", "\r\n", " \t\r\n"])
    @pytest.mark.parametrize("form", ["plain", "angle", "markdown"])
    def test_short_notes_preserve_every_character(self, release: ReleaseFixtures.Files, ending: str, form: str) -> None:
        """Retain complete source lines, Unicode, whitespace, and their original order."""
        line = {
            "plain": "**Full Changelog**: " + self.compare,
            "angle": "**Full Changelog**: <" + self.compare + ">",
            "markdown": "[Full Changelog](" + self.compare + ")",
        }[form]
        source = "* First change: caf\u00e9.\r\n* Second change: e\u0301.\n\n" + line + ending
        release.write(source)
        assert ReleaseBodyCommand.run(release.arguments) == 0
        expected = source + ("" if source.endswith("\n") else "\n") + "\n"
        expected += f"[CHANGELOG for `{self.tag}`](https://github.com/{self.repository}/blob/{self.tag}/CHANGELOG.md)\n"
        assert release.output.read_bytes() == expected.encode("utf-8")
        assert ReleaseBody.verify(release.output, expected) == ReleaseBody.measure(expected)

    def test_astral_unicode_uses_publisher_units(
        self, release: ReleaseFixtures.Files, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Replace a candidate whose code-point count fits but UTF-16 count does not."""
        references = ReleaseReferences(self.repository, self.tag)
        source = "* " + "\U0001f680" * 63000 + "\n\n**Full Changelog**: " + self.compare
        release.write(source)
        assert len(source) < 125000
        assert ReleaseBody.measure(source)[1] > 125000
        assert ReleaseBodyCommand.run(release.arguments) == 0
        actual = release.output.read_text(encoding="utf-8")
        assert actual.endswith(f"[CHANGELOG for `{self.tag}`]({references.resolve(source)[1]})\n")
        assert "**Full Changelog**: " + self.compare + "\n" in actual
        assert ReleaseBody.measure(actual)[1] < 125000
        assert "mode=summary" in capsys.readouterr().out

    def test_long_gap_keeps_complete_final_links(self, release: ReleaseFixtures.Files) -> None:
        """Use the measured 216840-character source with 1439 complete pull request entries."""
        entries = [
            f"* Change {index} in https://github.com/{self.repository}/pull/{index}\n" for index in range(1, 1440)
        ]
        comparison = "\n**Full Changelog**: " + self.compare + "\n"
        padding = 216840 - len("".join(entries) + comparison)
        source = "".join(entries) + "Complete summary context: " + "x" * (padding - 27) + "\n" + comparison
        assert len(source) == 216840
        assert source.count("/pull/") == 1439
        release.write(source)
        assert ReleaseBodyCommand.run(release.arguments) == 0
        actual = release.output.read_text(encoding="utf-8")
        assert actual.startswith(f"## Release summary for `{self.tag}`\n\n")
        assert actual.splitlines()[-2] == "**Full Changelog**: " + self.compare
        assert (
            actual.splitlines()[-1]
            == f"[CHANGELOG for `{self.tag}`](https://github.com/{self.repository}/blob/{self.tag}/CHANGELOG.md)"
        )
        assert actual.endswith("\n")
        assert "/pull/" not in actual
        assert ReleaseBody.measure(actual)[1] < 125000

    # The 50000-character tag becomes GITHUB_REF, and Windows caps one variable at 32767 characters.
    @pytest.mark.skipif(sys.platform == "win32", reason="Windows caps an environment variable at 32767 characters.")
    def test_oversized_summary_fails_without_cutting_links(
        self, release: ReleaseFixtures.Files, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Reject a summary that cannot fit instead of shortening its required references."""
        tag = "v" + "x" * 50000
        monkeypatch.setenv("GITHUB_REF", "refs/tags/" + tag)
        arguments = list(release.arguments)
        arguments[arguments.index("--tag") + 1] = tag
        release.write("**Full Changelog**: " + self.compare.rsplit("...", 1)[0] + "..." + tag)
        assert ReleaseBodyCommand.run(arguments) == 2
        assert not release.output.exists()


class TestRequiredInputs(ReleaseFixtures):
    """Prove that empty, invalid, or unreadable required inputs cannot pass."""

    @pytest.mark.parametrize(
        "value",
        [
            b"",
            b"{",
            b"\xff",
            b"[]",
            b'{"body":"a","body":"b"}',
            b'{"body":' + b"9" * 5000 + b"}",
            b"[" * 2000 + b"]" * 2000,
            {},
            {"body": None},
            {"body": 3},
            "",
            " \t\n",
            {"body": "\ud800"},
            {"body": "valid", "name": 4},
        ],
    )
    def test_invalid_source_has_checked_count(
        self, release: ReleaseFixtures.Files, capsys: pytest.CaptureFixture[str], value: object
    ) -> None:
        """Count a complete read even when source validation fails."""
        release.write(value)
        assert ReleaseBodyCommand.run(release.arguments) == 2
        assert not release.output.exists()
        assert "Checked 1 release-note file." in capsys.readouterr().err

    @pytest.mark.parametrize("kind", ["missing", "directory", "unreadable"])
    def test_unavailable_input_fails_with_zero_checked(
        self, release: ReleaseFixtures.Files, capsys: pytest.CaptureFixture[str], kind: str
    ) -> None:
        """Never count a failed read as a checked input."""
        if kind != "unreadable":
            release.source.unlink()
            if kind == "directory":
                release.source.mkdir()
        fault = patch.object(Path, "read_bytes", side_effect=PermissionError("PRIVATE_MARKER"))
        if kind == "unreadable":
            with fault:
                status = ReleaseBodyCommand.run(release.arguments)
        else:
            status = ReleaseBodyCommand.run(release.arguments)
        assert status == 2
        assert not release.output.exists()
        assert "Checked 0 release-note files." in capsys.readouterr().err

    @pytest.mark.parametrize(
        ("key", "value"),
        [
            ("GITHUB_EVENT_NAME", "pull_request"),
            ("GITHUB_REF_TYPE", "branch"),
            ("GITHUB_REF", "refs/heads/main"),
            ("RUNNER_TEMP", ""),
        ],
    )
    def test_required_context_cannot_be_missing_or_wrong(
        self, release: ReleaseFixtures.Files, monkeypatch: pytest.MonkeyPatch, key: str, value: str
    ) -> None:
        """Bind publication preparation to the existing tag event and controlled directory."""
        monkeypatch.setenv(key, value)
        assert ReleaseBodyCommand.run(release.arguments) == 2
        assert not release.output.exists()

    @pytest.mark.parametrize("arguments", [(), ("--source",), ("--help",), ("--unknown", "PRIVATE_MARKER")])
    def test_invalid_arguments_do_not_log_values(
        self, release: ReleaseFixtures.Files, capsys: pytest.CaptureFixture[str], arguments: tuple[str, ...]
    ) -> None:
        """Report a fixed failure and zero reads for invalid command inputs."""
        assert ReleaseBodyCommand.run(arguments) == 2
        diagnostic = capsys.readouterr().err
        assert "Checked 0 release-note files." in diagnostic
        assert "PRIVATE_MARKER" not in diagnostic
        assert not release.output.exists()

    @pytest.mark.parametrize(
        "repository", ["other/repo/path", "../repo", "owner/..", "owner/repo\n", "owner@host/repo"]
    )
    def test_invalid_repository_has_zero_reads(
        self, release: ReleaseFixtures.Files, capsys: pytest.CaptureFixture[str], repository: str
    ) -> None:
        """Reject an invalid repository before reading source or writing output."""
        arguments = list(release.arguments)
        arguments[arguments.index("--repository") + 1] = repository
        assert ReleaseBodyCommand.run(arguments) == 2
        assert "Checked 0 release-note files." in capsys.readouterr().err
        assert not release.output.exists()


class TestReferences(ReleaseFixtures):
    """Accept valid refs and reject misleading or ambiguous release destinations."""

    @pytest.mark.parametrize(
        ("previous", "tag"),
        [
            ("v1.2.3", "v1.2.4"),
            ("v1.2.3", "v1.2.4-rc.1"),
            ("releases/2026-09-26", "v1.2.4"),
            ("abc123", "v26.09.26.06.19"),
        ],
    )
    def test_valid_tag_and_reference_inputs(
        self, release: ReleaseFixtures.Files, monkeypatch: pytest.MonkeyPatch, previous: str, tag: str
    ) -> None:
        """Preserve complete encoded refs and pin the CHANGELOG to the exact current tag."""
        monkeypatch.setenv("GITHUB_REF", "refs/tags/" + tag)
        arguments = list(release.arguments)
        arguments[arguments.index("--tag") + 1] = tag
        arguments.extend(("--previous-tag", previous))
        url = f"https://github.com/{self.repository}/compare/{quote(previous, safe='')}...{quote(tag, safe='')}"
        release.write("**Full Changelog**: " + url)
        assert ReleaseBodyCommand.run(arguments) == 0
        actual = release.output.read_text(encoding="utf-8")
        assert "**Full Changelog**: " + url + "\n" in actual
        assert actual.endswith(
            f"[CHANGELOG for `{tag}`](https://github.com/{self.repository}/blob/{quote(tag, safe='')}/CHANGELOG.md)\n"
        )

    @pytest.mark.parametrize(
        "reference",
        ["", "../v1", "-v1", "v1..2", "v1/", "v1//test", "v1.lock", "v1/.hidden", "v1.", "v1@{1}", "v1\n", "v1%2Ftest"],
    )
    def test_invalid_tag_or_previous_ref_fails(
        self, release: ReleaseFixtures.Files, monkeypatch: pytest.MonkeyPatch, reference: str
    ) -> None:
        """Reject unsafe current and previous refs before publication."""
        monkeypatch.setenv("GITHUB_REF", "refs/tags/" + reference)
        arguments = list(release.arguments)
        arguments[arguments.index("--tag") + 1] = reference
        assert ReleaseBodyCommand.run(arguments) == 2
        monkeypatch.setenv("GITHUB_REF", "refs/tags/" + self.tag)
        assert ReleaseBodyCommand.run((*release.arguments, "--previous-tag", reference)) == 2
        assert not release.output.exists()

    @pytest.mark.parametrize(
        "url",
        [
            "http://github.com/<repo>/compare/v1...<tag>",
            "https://evil.test/<repo>/compare/v1...<tag>",
            "https://github.com:443/<repo>/compare/v1...<tag>",
            "https://user@github.com/<repo>/compare/v1...<tag>",
            "https://github.com/other/repo/compare/v1...<tag>",
            "https://github.com/<repo>/compare/v1...other",
            "https://github.com/<repo>/compare/...<tag>",
            "https://github.com/<repo>/compare/v1..<tag>",
            "https://github.com/<repo>/compare/v1...<tag>?x=1",
            "https://github.com/<repo>/compare/v1...<tag>#heading",
            "https://github.com/<repo>/compare/%2E%2E...<tag>",
            "https://github.com/<repo>/compare/%FF...<tag>",
            "https://github.com/<repo>/compare/%ZZ...<tag>",
            "https://github.com/<repo>/compare/v1...<tag>\\",
            "https://[github.com/<repo>/compare/v1...<tag>",
        ],
    )
    def test_wrong_or_malformed_comparison_fails(self, release: ReleaseFixtures.Files, url: str) -> None:
        """Validate URL components and decoded refs, not only a trusted-looking prefix."""
        release.write("**Full Changelog**: " + url.replace("<repo>", self.repository).replace("<tag>", self.tag))
        assert ReleaseBodyCommand.run(release.arguments) == 2
        assert not release.output.exists()

    @pytest.mark.parametrize(
        "body",
        [
            "No comparison.",
            "**Full Changelog**: <URL",
            "[Full Changelog](URL",
            "**Full Changelog**: URL extra",
            "**Full Changelog**: URL\n**Full Changelog**: URL",
            "**Full Changelog**: URL\n**Full Changelog**: <URL",
            "**Full Changelog**: URL\n[Full Changelog](URL",
            "**Full Changelog**: URL\n**Full Changelog**: URL extra",
            "**Full Changelog**: URL\n**Full Changelog**: https://github.com/other/repo/compare/v1...v2 extra",
        ],
    )
    def test_missing_or_ambiguous_complete_line_fails(self, release: ReleaseFixtures.Files, body: str) -> None:
        """Do not ignore a partial or conflicting declaration beside a complete comparison."""
        release.write(body.replace("URL", self.compare))
        assert ReleaseBodyCommand.run(release.arguments) == 2
        assert not release.output.exists()

    @pytest.mark.parametrize(
        ("field", "value"), [("repository", "other/repo"), ("tag_name", "v1"), ("previous_tag_name", "v1")]
    )
    def test_metadata_conflict_fails(self, release: ReleaseFixtures.Files, field: str, value: str) -> None:
        """Reject optional identities that disagree with the requested release."""
        release.write({"body": "**Full Changelog**: " + self.compare, field: value})
        assert ReleaseBodyCommand.run(release.arguments) == 2
        assert not release.output.exists()


class TestOutputFailures(ReleaseFixtures):
    """Prove file failures cannot report publication success."""

    @pytest.mark.parametrize("kind", ["same", "outside", "relative", "missing-parent", "directory", "symlink"])
    def test_invalid_output_preserves_source(self, release: ReleaseFixtures.Files, kind: str) -> None:
        """Reject unsafe destinations before creating or deleting any file."""
        original = release.source.read_bytes()
        paths = {
            "same": release.source,
            "outside": release.root.parent / "foreign.md",
            "relative": Path("body.md"),
            "missing-parent": release.root / "missing" / "body.md",
        }
        if kind == "directory":
            release.output.mkdir()
        elif kind == "symlink":
            try:  # Linking needs the symlink privilege, which Windows grants only to some accounts.
                release.output.symlink_to(release.source)  # Point the output at the source.
            except OSError as error:  # Without the privilege, this case cannot be built.
                pytest.skip(f"this account cannot create a symbolic link: {error}")  # Name the cause in the skip.
        arguments = list(release.arguments)
        arguments[arguments.index("--output") + 1] = str(paths.get(kind, release.output))
        assert ReleaseBodyCommand.run(arguments) == 2
        assert release.source.read_bytes() == original

    def test_write_failure_never_authorizes_stale_output(
        self, release: ReleaseFixtures.Files, capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
    ) -> None:
        """Keep the failure status even when a previous output exists."""
        release.output.write_bytes(b"old body\n")
        with patch.object(tempfile, "NamedTemporaryFile", side_effect=PermissionError("PRIVATE_MARKER")):
            assert ReleaseBodyCommand.run(release.arguments) == 2
        assert release.output.read_bytes() == b"old body\n"
        assert "Checked 1 release-note file." in capsys.readouterr().err
        assert "PRIVATE_MARKER" not in caplog.text

    def test_corrupt_final_file_cannot_pass(
        self, release: ReleaseFixtures.Files, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Corrupt real final bytes before the actual verification read."""
        read = Path.read_bytes

        def corrupt(path: Path) -> bytes:
            if path == release.output:
                path.write_bytes(b"partial line")
            return read(path)

        monkeypatch.setattr(Path, "read_bytes", corrupt)
        assert ReleaseBodyCommand.run(release.arguments) == 2
        assert read(release.output) == b"partial line"
        assert list(release.root.glob(".release-body-*")) == []

    @pytest.mark.parametrize("succeed", [True, False])
    def test_actual_module_exit_and_safe_logs(self, release: ReleaseFixtures.Files, succeed: bool) -> None:
        """Exercise the entry point without publishing or contacting a remote service."""
        marker = "SOURCE_PRIVATE_MARKER"
        release.write(marker + "\n**Full Changelog**: " + self.compare if succeed else marker)
        result = subprocess.run(
            [sys.executable, "-m", "scripts.release_body", *release.arguments],
            cwd=Path(__file__).resolve().parents[2],
            env=os.environ.copy(),
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        assert result.returncode == (0 if succeed else 2)
        assert "Checked 1 release-note file" in result.stdout + result.stderr
        assert marker not in result.stdout + result.stderr
        assert (result.stdout + result.stderr).isascii()
        assert release.output.exists() == succeed

    def test_success_logs_actual_counts_only(
        self, release: ReleaseFixtures.Files, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Report source, candidate, and verified output measurements without the notes."""
        caplog.set_level(logging.DEBUG)
        release.write("SOURCE_PRIVATE_MARKER\n**Full Changelog**: " + self.compare)
        assert ReleaseBodyCommand.run(release.arguments) == 0
        actual = release.output.read_text(encoding="utf-8")
        codepoints, units = ReleaseBody.measure(actual)
        assert f"checked_files=2 codepoints={codepoints} utf16_units={units}" in caplog.text
        assert "source_codepoints=" in caplog.text
        assert "candidate_codepoints=" in caplog.text
        assert "checked_comparisons=1" in caplog.text
        assert "SOURCE_PRIVATE_MARKER" not in caplog.text
