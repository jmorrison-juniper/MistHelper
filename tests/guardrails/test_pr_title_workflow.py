"""Prove the offline workflow, dependency, and Part 6 policy for issue #3550."""

import logging
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
POLICY_SNAPSHOTS = {
    # This mapping records the complete policy before either approved prefix changes.
    "dependabot": {
        "version": 2,
        "updates": [
            {
                "package-ecosystem": "pip",
                "directory": "/",
                "schedule": {"interval": "weekly"},
                "open-pull-requests-limit": 5,
                "labels": ["dependencies"],
                "commit-message": {"prefix": "deps"},
            },
            {
                "package-ecosystem": "github-actions",
                "directory": "/",
                "schedule": {"interval": "weekly"},
                "open-pull-requests-limit": 5,
                "labels": ["dependencies", "ci"],
                "commit-message": {"prefix": "ci"},
            },
            {
                "package-ecosystem": "npm",
                "directory": "/ops-portal",
                "schedule": {"interval": "weekly"},
                "open-pull-requests-limit": 5,
                "labels": ["dependencies"],
                "commit-message": {"prefix": "deps(ops-portal)"},
                "groups": {
                    "react": {
                        "patterns": ["react", "react-dom", "@types/react", "@types/react-dom"],
                    },
                },
                "ignore": [
                    {
                        "dependency-name": "typescript",
                        "update-types": ["version-update:semver-major"],
                    },
                ],
            },
        ],
    },
    "workflow": {
        "name": "Pull request title",
        "on": {
            "pull_request": {
                "types": ["opened", "edited", "reopened", "synchronize", "ready_for_review"],
            },
        },
        "concurrency": {
            "group": "${{ github.workflow }}-${{ github.head_ref || github.ref }}",
            "cancel-in-progress": "${{ github.ref != 'refs/heads/main' }}",
        },
        "permissions": {"contents": "read"},
        "jobs": {
            "title": {
                "name": "Conventional Commits PR title",
                "runs-on": "ubuntu-latest",
                "timeout-minutes": 5,
                "steps": [
                    {"uses": "actions/checkout@v7", "with": {"persist-credentials": False}},
                    {"uses": "actions/setup-python@v7", "with": {"python-version": "3.13"}},
                    {"run": "python -m scripts.pr_title_guard"},
                ],
            },
        },
    },
    "part_six_forms": [
        "type: description",
        "type(scope): description",
        "type!: description",
        "type(scope)!: description",
    ],
    "part_six_requirements": [
        r"The `Pull request title` workflow reports the `Conventional Commits PR title` check\.",
        r"The type must use lowercase\.",
        r"If you use a scope, give it a nonblank value without parentheses\.",
        r"Use a colon followed by an ASCII space\.",
        r"Use a nonblank one-line description\.",
        r"Additional description spaces and Unicode text are valid\.",
        r"control characters U\+0000 through U\+001F or U\+007F through U\+009F",
        r"Unicode line separator U\+2028 or the Unicode paragraph separator U\+2029",
        r"If the title fails, correct the pull request title\.",
        r"A title edit starts another check through the `edited` event\.",
        r"reversible ASCII JSON escapes",
        r"`Checked 1 pull request title`",
        r"`Checked 0 pull request titles`",
        r"the same rule to contributors, bots, drafts, forks, and documentation-only changes",
        r"New pip updates use `chore`\.",
        r"New npm updates in `/ops-portal` use `chore\(ops-portal\)`\.",
        r"GitHub Actions updates keep `ci`\.",
        r"Existing `deps` and `deps\(ops-portal\)` titles fail\.",
        r"A maintainer must rename each existing invalid title\.",
        r"Do not close update pull requests or disable update streams\.",
        r"The `Conventional Commits PR title` check is not a required status check\.",
        r"Require separate owner approval before anyone makes this check required\.",
        r"This feature changes no repository settings, branch protection, or required statuses\.",
        r"The `squash_merge_commit_title=PR_TITLE` setting stays unchanged\.",
        r"Squash the merge\. One pull request becomes one commit on `main`\.",
        r"Write `Closes #<issue>` in the pull request body\.",
        r"Rebase onto `main` before the merge if the branch is behind\.",
        r"Delete the branch and the worktree after the merge\.",
        r"Never force-push to `main`\. Never force-push to a branch that another agent shares\.",
    ],
}


class TestWorkflowPolicy:
    """Keep one title check within its read-only event boundary."""

    @pytest.fixture
    def workflow(self) -> dict[str, Any]:
        """Read the actual workflow and account for the YAML Boolean key."""
        logging.info("action=%s phase=%s", "read_title_workflow", "before")
        workflow = yaml.safe_load(
            (REPOSITORY_ROOT / ".github" / "workflows" / "pull-request-title.yml").read_text(encoding="utf-8")
        )
        assert isinstance(workflow, dict), "The title workflow must provide a parsed mapping."
        if True in workflow:
            assert "on" not in workflow, "The title workflow must declare its trigger once."
            workflow["on"] = workflow.pop(True)  # PyYAML treats an unquoted on key as a Boolean.
        logging.debug("action=read_title_workflow phase=after checked=%s", 1)
        return workflow

    @staticmethod
    def assert_policy(workflow: dict[str, Any]) -> None:
        """Assert the complete parsed contract used by both real and mutation cases."""
        assert (
            workflow == POLICY_SNAPSHOTS["workflow"]
        ), "The Pull request title workflow must match its read-only contract."

    def test_complete_workflow(self, workflow: dict[str, Any]) -> None:
        """Measure all five activities and every execution setting."""
        assert len(workflow["on"]["pull_request"]["types"]) == 5
        self.assert_policy(workflow)

    @pytest.mark.parametrize(
        ("path", "value"),
        [
            *[
                (
                    ("on", "pull_request", "types"),
                    [
                        activity
                        for activity in POLICY_SNAPSHOTS["workflow"]["on"]["pull_request"]["types"]
                        if activity != removed
                    ],
                )
                for removed in ("opened", "edited", "reopened", "synchronize", "ready_for_review")
            ],
            (
                ("on", "pull_request", "types"),
                ["opened", "edited", "reopened", "synchronize", "ready_for_review", "opened"],
            ),
            *[(("on", event), {}) for event in ("push", "schedule", "pull_request_target", "workflow_dispatch")],
            *[
                (("on", "pull_request", filter_name), ["main"])
                for filter_name in ("branches", "branches-ignore", "paths", "paths-ignore")
            ],
            (("concurrency",), {}),
            (("concurrency", "group"), "${{ github.ref }}"),
            (("concurrency", "cancel-in-progress"), True),
            (("concurrency", "cancel-in-progress"), False),
            (("concurrency", "cancel-in-progress"), "${{ github.ref != 'refs/heads/other' }}"),
            (("permissions",), {}),
            (("permissions", "contents"), "write"),
            (("permissions", "pull-requests"), "write"),
            (("env",), {"TITLE": "${{ github.event.pull_request.title }}"}),
            (("jobs",), {}),
            (("jobs", "title", "name"), "Pull request title"),
            (("jobs", "title", "runs-on"), "self-hosted"),
            (("jobs", "title", "timeout-minutes"), 6),
            (("jobs", "title", "permissions"), {"contents": "write"}),
            (("jobs", "title", "if"), "${{ github.actor != 'dependabot[bot]' }}"),
            (("jobs", "title", "continue-on-error"), True),
            (("jobs", "title", "env"), {"GITHUB_EVENT_PATH": "${{ github.event.pull_request.title }}"}),
            (("jobs", "title", "steps", 0, "uses"), "actions/checkout@v6"),
            (("jobs", "title", "steps", 0, "with", "persist-credentials"), True),
            (("jobs", "title", "steps", 1, "uses"), "actions/setup-python@v6"),
            (("jobs", "title", "steps", 1, "with", "python-version"), "3.12"),
            (("jobs", "title", "steps", 2, "run"), 'python -c "${{ github.event.pull_request.title }}"'),
            (("jobs", "title", "steps", 2, "run"), "python -m scripts.pr_title_guard || true"),
            (("jobs", "title", "steps", 2, "run"), "gh pr view --json title"),
            (("jobs", "title", "steps", 2, "if"), "${{ !github.event.pull_request.draft }}"),
            (("jobs", "title", "steps", 2, "continue-on-error"), True),
            (("jobs", "title", "steps", 2, "env"), {"TOKEN": "${{ secrets.GITHUB_TOKEN }}"}),
            (("jobs", "title", "steps"), [{"run": "python -m pip install misthelper"}]),
        ],
    )
    def test_unsafe_changes_fail(self, path: tuple[str | int, ...], value: object, workflow: dict[str, Any]) -> None:
        """Use the same real assertion to reject unsafe policy changes."""
        candidate = deepcopy(workflow)
        target = candidate
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
        with pytest.raises(AssertionError, match="Pull request title workflow"):
            self.assert_policy(candidate)

    @pytest.mark.parametrize(
        "case",
        [
            ("title-guard", "refs/pull/3/merge", "Pull request title-title-guard", True),
            ("title-guard", "refs/pull/4/merge", "Pull request title-title-guard", True),
            ("", "refs/pull/3/merge", "Pull request title-refs/pull/3/merge", True),
            ("", "refs/heads/main", "Pull request title-refs/heads/main", False),
            ("main", "refs/heads/main", "Pull request title-main", False),
        ],
    )
    def test_concurrency_contexts(self, case: tuple[str, str, str, bool], workflow: dict[str, Any]) -> None:
        """Prove branch separation, reference fallback, and main preservation offline."""
        head_ref, event_ref, expected_group, expected_cancel = case
        template = workflow["concurrency"]["group"]
        prefix = template.replace("${{ github.workflow }}", workflow["name"])
        assert prefix.replace("${{ github.head_ref || github.ref }}", head_ref or event_ref) == expected_group
        assert prefix.replace("${{ github.head_ref || github.ref }}", "another-head") != expected_group
        assert (
            template.replace("${{ github.workflow }}", "Another workflow").replace(
                "${{ github.head_ref || github.ref }}", head_ref or event_ref
            )
            != expected_group
        )
        cancellation = workflow["concurrency"]["cancel-in-progress"]
        assert cancellation.replace(
            "${{ github.ref != 'refs/heads/main' }}", str(event_ref != "refs/heads/main")
        ) == str(expected_cancel)


class TestDependabotPolicy:
    """Retain every update setting except the two approved prefixes."""

    @pytest.fixture
    def policy(self) -> dict[str, Any]:
        """Read one complete dependency update policy."""
        logging.info("action=%s phase=%s", "read_dependabot_policy", "before")
        policy = yaml.safe_load((REPOSITORY_ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8"))
        assert isinstance(policy, dict), "Dependabot must provide a parsed mapping."
        logging.debug("action=read_dependabot_policy phase=after checked=%s", 1)
        return policy

    @staticmethod
    def assert_policy(policy: dict[str, Any]) -> None:
        """Compare the complete policy with its fixed pre-change mapping."""
        assert [stream["commit-message"]["prefix"] for stream in policy["updates"]] == [
            "chore",
            "ci",
            "chore(ops-portal)",
        ], "Dependabot prefixes must use the common allowed types."
        original = deepcopy(policy)
        # Reverse only these two values so every other policy field remains part of the comparison.
        original["updates"][0]["commit-message"]["prefix"] = "deps"
        original["updates"][2]["commit-message"]["prefix"] = "deps(ops-portal)"
        assert original == POLICY_SNAPSHOTS["dependabot"], "Dependabot policy must retain every other field."

    def test_complete_policy(self, policy: dict[str, Any]) -> None:
        """Measure all three streams against the fixed policy."""
        assert len(policy["updates"]) == 3
        self.assert_policy(policy)

    @pytest.mark.parametrize(
        ("path", "value"),
        [
            (("version",), 3),
            (("unrelated-setting",), True),
            (("updates",), []),
            (("updates", 0, "commit-message", "prefix"), "deps"),
            (("updates", 1, "commit-message", "prefix"), "deps"),
            (("updates", 2, "commit-message", "prefix"), "deps(ops-portal)"),
            (("updates", 0, "directory"), "/elsewhere"),
            (("updates", 1, "package-ecosystem"), "pip"),
            (("updates", 2, "schedule", "interval"), "daily"),
            (("updates", 0, "open-pull-requests-limit"), 6),
            (("updates", 1, "labels"), ["dependencies"]),
            (("updates", 2, "groups"), {"react": {"patterns": ["react"]}}),
            (("updates", 2, "ignore"), []),
            (("updates", 2, "ignore", 0, "update-types"), ["version-update:semver-minor"]),
        ],
    )
    def test_unrelated_changes_fail(self, path: tuple[str | int, ...], value: object, policy: dict[str, Any]) -> None:
        """Run the same assertions against real in-memory policy mutations."""
        candidate = deepcopy(policy)
        target = candidate
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
        with pytest.raises(AssertionError, match="Dependabot"):
            self.assert_policy(candidate)


class TestPartSixPolicy:
    """Check durable Part 6 semantics without freezing another Part."""

    @pytest.fixture
    def part_six(self) -> str:
        """Read only the Part 6 policy for durable semantic assertions."""
        logging.info("action=%s phase=%s", "read_part_six", "before")
        text = (REPOSITORY_ROOT / ".github" / "instructions" / "git-flow-multi-agent.instructions.md").read_text(
            encoding="utf-8"
        )
        _, heading, remaining = text.partition("## Part 6. The commit and the merge\n")
        assert heading == "## Part 6. The commit and the merge\n"
        # Use the next Part as a boundary without fixing its heading or content.
        part_six = re.split(r"(?m)^## Part \d+\.", remaining, maxsplit=1)[0]
        logging.debug("action=read_part_six phase=after checked=%s", 1)
        return part_six

    @staticmethod
    def assert_policy(part_six: str) -> None:
        """Assert the forms, allowed types, and required policy meanings."""
        types_text = part_six.partition("Use one of these types:")[2].partition("\n\n")[0]
        assert re.findall(r"`([^`]+)`", types_text) == [
            "fix",
            "feat",
            "chore",
            "refactor",
            "test",
            "docs",
            "ci",
            "style",
            "perf",
        ], "Part 6 must state all nine allowed types."
        assert (
            re.findall(r"(?m)^type(?:\(scope\))?!?: description$", part_six) == POLICY_SNAPSHOTS["part_six_forms"]
        ), "Part 6 must state all four title forms."
        normalized = " ".join(part_six.split())
        for requirement in POLICY_SNAPSHOTS["part_six_requirements"]:
            assert (
                len(re.findall(requirement, normalized)) >= 1
            ), f"Part 6 must retain this policy meaning: {requirement}"

    def test_complete_policy(self, part_six: str) -> None:
        """Measure all required meanings within Part 6 only."""
        assert len(re.findall(r"(?m)^type(?:\(scope\))?!?: description$", part_six)) == 4
        self.assert_policy(part_six)

    @pytest.mark.parametrize(
        "removed",
        [
            "Pull request title",
            "Conventional Commits PR title",
            "`perf`",
            "type(scope)!: description",
            "lowercase",
            "nonblank value without parentheses",
            "ASCII space",
            "nonblank one-line description",
            "Unicode text",
            "U+0000",
            "U+007F",
            "U+2028",
            "U+2029",
            "correct the pull request title",
            "`edited` event",
            "reversible ASCII JSON escapes",
            "Checked 1 pull request title",
            "Checked 0 pull request titles",
            "contributors, bots, drafts, forks",
            "New pip updates use `chore`",
            "New npm updates in `/ops-portal`",
            "GitHub Actions updates keep `ci`",
            "Existing `deps` and `deps(ops-portal)` titles fail",
            "A maintainer must rename",
            "Do not close update pull requests",
            "not a required status check",
            "separate owner approval",
            "no repository settings, branch protection",
            "squash_merge_commit_title=PR_TITLE",
            "Squash the merge",
            "Write `Closes #<issue>`",
            "Rebase onto `main`",
            "Delete the branch and the worktree",
            "Never force-push to `main`",
        ],
    )
    def test_missing_meaning_fails(self, removed: str, part_six: str) -> None:
        """Run the real policy assertions after removing each required meaning."""
        pattern = r"\s+".join(re.escape(word) for word in removed.split())
        candidate = re.sub(pattern, "REMOVED", part_six)
        assert candidate != part_six
        with pytest.raises(AssertionError, match="Part 6"):
            self.assert_policy(candidate)
