"""Prove exact title decisions, measured output, and offline process behavior."""

import json
import logging
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from scripts.pr_title_guard import PullRequestTitleGuard

OUTPUTS = {
    "types": ("fix", "feat", "chore", "refactor", "test", "docs", "ci", "style", "perf"),
    "guidance": (
        "Result: FAIL - Invalid title grammar or forbidden character.\n"
        "Use type[(scope)][!]: description.\n"
        "Allowed types: fix, feat, chore, refactor, test, docs, ci, style, perf.\n"
        "Use a nonblank scope without parentheses and a nonblank one-line description.\n"
        "Do not use control characters, Unicode line separators, or Unicode paragraph separators.\n"
        "Correct the pull request title. A title edit starts another check.\n"
    ),
    "input_problems": {
        "environment": "GITHUB_EVENT_PATH is missing or empty.",
        "file": "Cannot read the GITHUB_EVENT_PATH file.",
        "utf8": "The GITHUB_EVENT_PATH file is not valid UTF-8.",
        "json": "The GITHUB_EVENT_PATH file is not valid JSON.",
        "event": "The event must be an object with a pull_request object.",
        "title": "The pull_request.title field must be a string.",
    },
    "failed_read_logs": [
        "action=read_event phase=before",
        "action=read_event phase=after status=failed checked=0",
    ],
    "failed_stderr": (
        "INFO action=read_event phase=before\n"
        "DEBUG action=read_event phase=after status=failed checked=0\n"
        "ERROR action=read_event category="
    ),
    "ready_read_logs": [
        "action=read_event phase=before",
        "action=read_event phase=after status=ready checked=1",
    ],
    "ready_stderr": (
        "INFO action=read_event phase=before\n"
        "DEBUG action=read_event phase=after status=ready checked=1\n"
        "INFO action=title_decision phase=before\n"
    ),
    "failure_inputs": [
        ("absent", None, "environment", "TypeError"),
        ("empty", None, "environment", "TypeError"),
        ("missing", None, "file", "FileNotFoundError"),
        ("directory", None, "file", "IsADirectoryError"),
        ("too_long", None, "file", "OSError"),
        ("not_a_directory", None, "file", "NotADirectoryError"),
        ("whitespace", None, "file", "FileNotFoundError"),
        ("file", b"\xffevent-secret", "utf8", "UnicodeDecodeError"),
        ("file", b"", "json", "JSONDecodeError"),
        ("file", b'{"event-secret": "private-token", "pull_request": }', "json", "JSONDecodeError"),
        ("file", b'{"pull_request": {"title": "unterminated}', "json", "JSONDecodeError"),
        ("file", b"\xef\xbb\xbf{}", "json", "JSONDecodeError"),
        ("file", b"[" * 10_000 + b"0" + b"]" * 10_000, "json", "RecursionError"),
        ("file", b"9" * 10_000, "json", "ValueError"),
        *[
            ("file", json.dumps(value).encode("utf-8"), "event", "TypeError")
            for value in (None, [], True, 1, 1.5, "event-secret", {})
        ],
        *[
            ("file", json.dumps({"pull_request": value}).encode("utf-8"), "event", "TypeError")
            for value in (None, [], True, 1, "event-secret")
        ],
        *[
            ("file", json.dumps({"pull_request": value}).encode("utf-8"), "title", "TypeError")
            for value in ({}, {"id": 1})
        ],
        *[
            ("file", json.dumps({"pull_request": {"title": value}}).encode("utf-8"), "title", "TypeError")
            for value in (None, False, 0, 1.5, {}, [])
        ],
    ],
}


class TestTitleGrammar:
    """Check the complete grammar without an event file."""

    @pytest.mark.parametrize(
        "title",
        [
            f"{commit_type}{scope}{marker}: {description}"
            for commit_type in OUTPUTS["types"]
            for scope in ("", "(web-portal)", "( Web Portal \u670d\u52a1 )")
            for marker in ("", "!")
            for description in ("model prompts", "\u4fee\u590d\u6a21\u578b\u63d0\u793a", "  model  prompts  ", "\u200d")
        ],
    )
    def test_allowed_types_and_forms(self, title: str, monkeypatch: pytest.MonkeyPatch) -> None:
        """Accept each type and form without event input."""

        class TitleString(str):
            pass

        monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)
        assert PullRequestTitleGuard().is_valid_title(title) is True
        assert PullRequestTitleGuard().is_valid_title(TitleString(title)) is True

    @pytest.mark.parametrize(
        "title",
        [
            "",
            " ",
            "\u2003\u00a0",
            "wip: model prompts",
            "deps: model prompts",
            "deps(ops-portal): update packages",
            " fix: model prompts",
            "\ufefffix: model prompts",
            "prefix fix: model prompts",
            "fix(): model prompts",
            "fix(   ): model prompts",
            "fix(\u00a0\u2007): model prompts",
            "fix((scope)): model prompts",
            "fix(scope(other)): model prompts",
            "fix(scope: model prompts",
            "fixscope): model prompts",
            "fix(scope))!: model prompts",
            "fix!(scope): model prompts",
            "fix!!: model prompts",
            "fix(scope)!!: model prompts",
            "fix : model prompts",
            "fix(scope) : model prompts",
            "fix:model prompts",
            "fix:: model prompts",
            "fix:\u00a0model prompts",
            "fix: ",
            "fix:     ",
            "fix: \u2003\u00a0\u202f\u3000",
            *[f"{commit_type.upper()}: model prompts" for commit_type in OUTPUTS["types"]],
        ],
    )
    def test_invalid_grammar(self, title: str) -> None:
        """Reject unsupported types and incomplete title syntax."""
        assert PullRequestTitleGuard().is_valid_title(title) is False

    @pytest.mark.parametrize(
        "title",
        [
            None,
            False,
            True,
            0,
            1,
            1.5,
            {},
            [],
            ("fix: model prompts",),
            b"fix: model prompts",
            Path("event.json"),
            object(),
        ],
    )
    def test_nonstring_arguments(self, title: object) -> None:
        """Return an exact false decision for non-string values."""

        class NonString:
            __class__ = str

        assert PullRequestTitleGuard().is_valid_title(NonString()) is False
        assert PullRequestTitleGuard().is_valid_title(title) is False

    @pytest.mark.parametrize(
        "character",
        [*[chr(value) for value in range(32)], *[chr(value) for value in range(127, 160)], "\u2028", "\u2029"],
    )
    @pytest.mark.parametrize(
        "template",
        [
            "{character}fix: model prompts",
            "fi{character}x: model prompts",
            "fix(scope{character}): model prompts",
            "fix: model{character} prompts",
            "fix: model prompts{character}",
        ],
    )
    def test_every_forbidden_character(self, character: str, template: str) -> None:
        """Reject each forbidden character at every relevant title position."""
        title = template.format(character=character)
        assert PullRequestTitleGuard().is_valid_title(title) is False

    @pytest.mark.parametrize(
        ("title", "expected"),
        [
            ("fix: " + "x" * 200_000, True),
            ("feat(" + "s" * 100_000 + ")!: model prompts", True),
            ("fix: " + " " * 200_000, False),
            ("fix(" + " " * 100_000 + "): model prompts", False),
            ("fix: " + "x" * 200_000 + "\x00", False),
        ],
        ids=["large-description", "large-scope", "large-blank-description", "large-blank-scope", "large-control"],
    )
    def test_large_titles(self, title: str, expected: bool) -> None:
        """Use the same rule without a new length restriction."""
        assert PullRequestTitleGuard().is_valid_title(title) is expected


class TestTitleOutput:
    """Check exact stdout and the real decision logs."""

    @pytest.mark.parametrize(
        ("title", "expected"),
        [
            ("fix(web-portal): model prompts", True),
            ("wip: model prompts", False),
            ("fix:   model  prompts  ", True),
            ("fix(web-portal): \u4fee\u590d\u6a21\u578b\u63d0\u793a", True),
            ('fix: "quotes" \\ $HOME $(printf title) && `printf title` ::warning::', True),
            ("fix: \ud800", True),
            ("", False),
            (" \u2003 ", False),
            ("fix: model\n::error::prompts", False),
            ("fix: model\x1b[31mprompts", False),
            ("fix: model\x00prompts", False),
            ("fix: model\tprompts", False),
            ("fix: model\x7fprompts", False),
            ("fix: model\x85prompts", False),
            ("fix: model\x9fprompts", False),
            ("fix: model\u2028prompts", False),
            ("fix: model\u2029prompts", False),
        ],
    )
    def test_exact_stdout(self, title: str, expected: bool, capsys: pytest.CaptureFixture[str]) -> None:
        """Preserve the exact string through reversible ASCII output."""
        exit_code = PullRequestTitleGuard().check(title)
        captured = capsys.readouterr()
        result = "Result: PASS\n" if expected else OUTPUTS["guidance"]
        assert exit_code == (0 if expected else 1)
        assert captured.out == f"Title: {json.dumps(title, ensure_ascii=True)}\n{result}Checked 1 pull request title\n"
        assert json.loads(captured.out.splitlines()[0].removeprefix("Title: ")) == title
        assert captured.out.isascii() is True
        assert captured.err == ""

    @pytest.mark.parametrize(
        ("title", "expected", "checked"),
        [
            ("fix: model prompts", True, 1),
            ("wip: model prompts", False, 1),
            ("", False, 1),
            (None, False, 0),
            ({}, False, 0),
        ],
    )
    def test_decision_log_order(
        self, title: object, expected: bool, checked: int, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Log before and after the actual decision with its count."""
        caplog.set_level(logging.DEBUG)
        caplog.clear()
        assert PullRequestTitleGuard().is_valid_title(title) is expected
        assert [(record.levelname, record.getMessage()) for record in caplog.records] == [
            ("INFO", "action=title_decision phase=before"),
            ("DEBUG", f"action=title_decision phase=after valid={expected} checked={checked}"),
        ]
        assert caplog.records[0].args == ("title_decision", "before")
        assert all(record.getMessage().isascii() for record in caplog.records) is True

    @pytest.mark.parametrize("expected", [True, False])
    def test_large_output_is_complete(self, expected: bool, capsys: pytest.CaptureFixture[str]) -> None:
        """Retain the complete large title in passing and failing output."""
        title = "fix: " + ("x" if expected else " ") * 200_000
        exit_code = PullRequestTitleGuard().check(title)
        captured = capsys.readouterr()
        result = "Result: PASS\n" if expected else OUTPUTS["guidance"]
        assert exit_code == (0 if expected else 1)
        assert captured.out == f"Title: {json.dumps(title, ensure_ascii=True)}\n{result}Checked 1 pull request title\n"
        assert json.loads(captured.out.splitlines()[0].removeprefix("Title: ")) == title


class TestEventInput:
    """Distinguish unavailable input from an available invalid title."""

    @staticmethod
    def expected_path_category(kind: str, category: str, platform: str) -> str:
        """Select native open errors for the two reported path shapes."""
        # Windows open reports EACCES for a directory and ENOENT for a file used as a parent.
        if platform == "win32":
            return {"directory": "PermissionError", "not_a_directory": "FileNotFoundError"}.get(kind, category)
        return category

    @pytest.fixture(params=OUTPUTS["failure_inputs"])
    def failure_input(
        self, request: pytest.FixtureRequest, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> tuple[str, str]:
        """Prepare each real input failure without a network service."""
        kind, payload, problem, category = request.param
        event_file = tmp_path / "event-secret-\u4fee.json"
        paths = {
            "empty": "",
            "missing": str(event_file),
            "directory": str(tmp_path),
            "too_long": str(tmp_path / ("x" * 300)),
            "not_a_directory": str(tmp_path / "regular-file" / "event.json"),
            "whitespace": "   ",
        }
        if kind == "not_a_directory":
            (tmp_path / "regular-file").write_bytes(b"not a directory")
        monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_file))
        if kind == "file":
            event_file.write_bytes(payload)
        elif kind == "absent":
            monkeypatch.delenv("GITHUB_EVENT_PATH")
        else:
            monkeypatch.setenv("GITHUB_EVENT_PATH", paths[kind])
        return problem, self.expected_path_category(kind, category, sys.platform)

    @staticmethod
    def assert_input_failure(
        result: int, stdout: str, records: list[logging.LogRecord], expected: tuple[str, str]
    ) -> None:
        """Verify the real failure result and safe diagnostic frames."""
        problem, category = expected
        messages = [record.getMessage() for record in records]
        assert result == 1
        assert stdout == f"Result: FAIL - {OUTPUTS['input_problems'][problem]}\nChecked 0 pull request titles\n"
        assert messages[:2] == OUTPUTS["failed_read_logs"]
        assert len(messages) == 3
        category_text, frames_text = messages[2].removeprefix("action=read_event category=").split(" frames=", 1)
        assert json.loads(category_text) == category
        assert all(name in json.loads(frames_text) for name in ("main", "read_title")) is True
        assert (stdout + "".join(messages)).isascii() is True
        assert all("\n" not in message for message in messages) is True
        assert "event-secret" not in stdout + "".join(messages)
        assert records[-1].exc_info is None

    @pytest.mark.parametrize(
        "title", ["fix: model prompts", "fix:  model  prompts  ", "fix: \u4fee\u590d", "", " \u2003 "]
    )
    def test_read_exact_title(
        self, title: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Return each available title unchanged and measure one read."""
        event_file = tmp_path / "event.json"
        event_file.write_text(json.dumps({"pull_request": {"title": title}}), encoding="utf-8")
        monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_file))
        caplog.set_level(logging.DEBUG)
        assert PullRequestTitleGuard().read_title() == title
        assert [record.getMessage() for record in caplog.records] == OUTPUTS["ready_read_logs"]

    def test_input_failures(
        self, failure_input: tuple[str, str], capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
    ) -> None:
        """Fail every source, decoding, JSON, and shape problem with count zero."""
        caplog.set_level(logging.DEBUG)
        result = PullRequestTitleGuard().main()
        captured = capsys.readouterr()
        self.assert_input_failure(result, captured.out, caplog.records, failure_input)
        assert "event-secret" not in captured.err

    def test_permission_failure(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Use a narrow stand-in because host permissions can permit the read."""

        def deny_open(path: Path, *, encoding: str) -> str:
            raise PermissionError("event-secret\n::error::\u2603")

        # A frame name with Unicode and a newline must remain data in the diagnostic record.
        deny_open.__code__ = deny_open.__code__.replace(co_filename="frame-\u4fee\n::error::.py")
        event_file = tmp_path / "event-secret.json"
        event_file.write_text('{"pull_request": {"title": "fix: model prompts"}}', encoding="utf-8")
        monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_file))
        caplog.set_level(logging.DEBUG)
        with patch.object(Path, "open", autospec=True, side_effect=deny_open) as reader:
            result = PullRequestTitleGuard().main()
            reader.assert_called_once_with(event_file, encoding="utf-8")
        captured = capsys.readouterr()
        self.assert_input_failure(result, captured.out, caplog.records, ("file", "PermissionError"))
        assert "frame-\u4fee\n::error::.py" in json.loads(caplog.records[-1].getMessage().split(" frames=", 1)[1])
        assert "event-secret" not in captured.err

    @pytest.mark.parametrize(
        ("kind", "category", "platform", "expected"),
        [
            ("directory", "IsADirectoryError", "darwin", "IsADirectoryError"),
            ("directory", "IsADirectoryError", "linux", "IsADirectoryError"),
            ("directory", "IsADirectoryError", "win32", "PermissionError"),
            ("not_a_directory", "NotADirectoryError", "darwin", "NotADirectoryError"),
            ("not_a_directory", "NotADirectoryError", "linux", "NotADirectoryError"),
            ("not_a_directory", "NotADirectoryError", "win32", "FileNotFoundError"),
            ("missing", "FileNotFoundError", "win32", "FileNotFoundError"),
            ("too_long", "OSError", "win32", "OSError"),
            ("file", "UnicodeDecodeError", "win32", "UnicodeDecodeError"),
            ("absent", "TypeError", "win32", "TypeError"),
        ],
    )
    def test_native_path_expectations(self, kind: str, category: str, platform: str, expected: str) -> None:
        """Check each platform."""
        assert self.expected_path_category(kind, category, platform) == expected

    @pytest.mark.parametrize(
        ("platform", "case"),
        [
            ("linux", ("directory", "IsADirectoryError", IsADirectoryError)),
            ("win32", ("directory", "IsADirectoryError", PermissionError)),
            ("linux", ("not_a_directory", "NotADirectoryError", NotADirectoryError)),
            ("win32", ("not_a_directory", "NotADirectoryError", FileNotFoundError)),
        ],
    )
    def test_controlled_path_refusals(
        self,
        platform: str,
        case: tuple[str, str, type[OSError]],
        capsys: pytest.CaptureFixture[str],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Prove each selected error still fails with zero checked titles."""
        kind, category, error_type = case
        caplog.set_level(logging.DEBUG)
        with patch.dict(os.environ, {"GITHUB_EVENT_PATH": "event-secret.json"}):
            with patch.object(Path, "open", autospec=True, side_effect=error_type("event-secret")) as reader:
                result = PullRequestTitleGuard().main()
                reader.assert_called_once_with(Path("event-secret.json"), encoding="utf-8")
        captured = capsys.readouterr()
        expected = self.expected_path_category(kind, category, platform)
        self.assert_input_failure(result, captured.out, caplog.records, ("file", expected))
        assert caplog.records[-1].levelname == "ERROR"
        assert "event-secret" not in captured.err


class TestTitleCli:
    """Run the real main method and module entry point."""

    @pytest.fixture
    def event_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        """Give each case an isolated runner event path."""
        event_file = tmp_path / "event.json"
        monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_file))
        return event_file

    @pytest.mark.parametrize(
        "case",
        [
            ("fix(web-portal): model prompts", True),
            ("wip: model prompts", False),
            ("fix: \u4fee\u590d", True),
            ("", False),
        ],
    )
    def test_main_titles(
        self,
        case: tuple[str, bool],
        event_file: Path,
        capsys: pytest.CaptureFixture[str],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Keep event reading and title decisions in the required order."""
        title, expected = case
        event_file.write_text(json.dumps({"pull_request": {"title": title}}), encoding="utf-8")
        caplog.set_level(logging.DEBUG)
        result = PullRequestTitleGuard().main()
        captured = capsys.readouterr()
        guidance = "Result: PASS\n" if expected else OUTPUTS["guidance"]
        assert result == (0 if expected else 1)
        assert (
            captured.out == f"Title: {json.dumps(title, ensure_ascii=True)}\n{guidance}Checked 1 pull request title\n"
        )
        assert [record.getMessage() for record in caplog.records] == OUTPUTS["ready_read_logs"] + [
            "action=title_decision phase=before",
            f"action=title_decision phase=after valid={expected} checked=1",
        ]

    @pytest.mark.parametrize("options", [(), ("-S",)])
    @pytest.mark.parametrize(
        "case",
        [
            ("fix(web-portal): model prompts", True),
            ("wip: model prompts", False),
            ("fix: \u4fee\u590d\u6a21\u578b\u63d0\u793a", True),
            ('fix: "quotes" \\ $(printf title) && ::warning::', True),
            ("fix: model\n::error::prompts", False),
            ("", False),
            (" \u2003 ", False),
        ],
    )
    def test_cli_titles(self, case: tuple[str, bool], options: tuple[str, ...], event_file: Path) -> None:
        """Prove process results with and without installed-package imports."""
        title, expected = case
        event_file.write_text(json.dumps({"pull_request": {"title": title}}), encoding="utf-8")
        process = subprocess.run(
            [sys.executable, *options, "-m", "scripts.pr_title_guard"],
            cwd=Path(__file__).resolve().parents[3],
            capture_output=True,
            encoding="utf-8",
            timeout=10,
            check=False,
        )
        guidance = "Result: PASS\n" if expected else OUTPUTS["guidance"]
        assert process.returncode == (0 if expected else 1)
        assert (
            process.stdout == f"Title: {json.dumps(title, ensure_ascii=True)}\n{guidance}Checked 1 pull request title\n"
        )
        assert (
            process.stderr
            == OUTPUTS["ready_stderr"] + f"DEBUG action=title_decision phase=after valid={expected} checked=1\n"
        )
        assert process.stderr.isascii() is True

    @pytest.mark.parametrize(
        "case",
        [
            (None, "environment"),
            (b"\xffevent-secret", "utf8"),
            (b'{"event-secret":', "json"),
            (b"[]", "event"),
            (b'{"pull_request": {"title": null}}', "title"),
        ],
    )
    def test_cli_input_failures(self, case: tuple[bytes | None, str], event_file: Path) -> None:
        """Fail the process with count zero and three safe stderr records."""
        payload, problem = case
        environment = os.environ.copy()
        if payload is None:
            environment.pop("GITHUB_EVENT_PATH", None)
        else:
            event_file.write_bytes(payload)
        process = subprocess.run(
            [sys.executable, "-m", "scripts.pr_title_guard"],
            cwd=Path(__file__).resolve().parents[3],
            env=environment,
            capture_output=True,
            encoding="utf-8",
            timeout=10,
            check=False,
        )
        assert process.returncode == 1
        assert process.stdout == f"Result: FAIL - {OUTPUTS['input_problems'][problem]}\nChecked 0 pull request titles\n"
        assert process.stderr.startswith(OUTPUTS["failed_stderr"])
        assert len(process.stderr.splitlines()) == 3
        assert process.stderr.isascii() is True
        assert "event-secret" not in process.stdout + process.stderr

    @pytest.mark.parametrize(
        "metadata",
        [
            {
                "action": "opened",
                "sender": {"login": "contributor", "type": "User"},
                "pull_request": {"draft": False, "user": {"type": "User"}, "head": {"repo": {"fork": False}}},
            },
            {
                "action": "edited",
                "sender": {"login": "dependabot[bot]", "type": "Bot"},
                "pull_request": {"draft": False, "user": {"type": "Bot"}, "head": {"repo": {"fork": False}}},
            },
            {
                "action": "ready_for_review",
                "pull_request": {"draft": True, "user": {"type": "User"}, "head": {"repo": {"fork": False}}},
            },
            {
                "action": "reopened",
                "pull_request": {"draft": False, "user": {"type": "User"}, "head": {"repo": {"fork": True}}},
            },
            {
                "action": "synchronize",
                "changed_files": ["README.md"],
                "pull_request": {"draft": False, "user": {"type": "User"}, "head": {"repo": {"fork": False}}},
            },
            {
                "action": "edited",
                "sender": {"type": "Bot"},
                "changed_files": ["documentation/guide.md"],
                "pull_request": {"draft": True, "user": {"type": "Bot"}, "head": {"repo": {"fork": True}}},
            },
        ],
        ids=["contributor", "bot", "draft", "fork", "documentation", "bot-draft-fork"],
    )
    @pytest.mark.parametrize(
        "case",
        [
            ("fix(web-portal): model prompts", True),
            ("chore: Bump a Python dependency", True),
            ("chore(ops-portal): Bump react", True),
            ("ci: Bump actions/checkout", True),
            ("deps: Bump a Python dependency", False),
            ("deps(ops-portal): Bump react", False),
            ("wip: model prompts", False),
        ],
    )
    def test_metadata_uses_one_policy(
        self, metadata: dict[str, Any], case: tuple[str, bool], event_file: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Apply the same real title decision to every author and PR state."""
        title, expected = case
        event = deepcopy(metadata)
        event["pull_request"]["title"] = title
        event["title"] = "wip: ignore this unrelated root field"
        event_file.write_text(json.dumps(event), encoding="utf-8")
        result = PullRequestTitleGuard().main()
        captured = capsys.readouterr()
        guidance = "Result: PASS\n" if expected else OUTPUTS["guidance"]
        assert result == (0 if expected else 1)
        assert (
            captured.out == f"Title: {json.dumps(title, ensure_ascii=True)}\n{guidance}Checked 1 pull request title\n"
        )
