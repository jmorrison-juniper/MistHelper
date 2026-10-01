"""Prove the actual release body's source without executing a release workflow."""

import logging
import shlex
from copy import deepcopy
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import yaml


class ReleaseWorkflowContract:
    """Read one real workflow and check the publication boundary."""

    @staticmethod
    def read(path: Path) -> dict[str, Any]:
        """Fail when the required workflow cannot be read or parsed."""
        logging.info("phase=workflow_read event=before checked_files=0")
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            logging.error("phase=workflow_read event=failed checked_files=0")
            raise
        logging.debug("phase=workflow_read event=after checked_files=1")
        parsed = yaml.safe_load(text)
        assert isinstance(parsed, dict), "Checked 1 workflow file. The workflow must be a mapping."
        if True in parsed:
            parsed["on"] = parsed.pop(True)  # PyYAML reads the unquoted on key as a Boolean.
        return parsed

    @staticmethod
    def check(workflow: dict[str, Any]) -> None:
        """Connect the real helper output to the only publisher and retain tag-only execution."""
        counts = {"records": 1, "jobs": 0, "steps": 0, "publishers": 0}
        logging.info("phase=workflow_policy event=before checked=%s", counts)
        try:
            steps = ReleaseWorkflowContract.boundary(workflow, counts)
            ReleaseWorkflowContract.Preparation.check(steps)
            publisher = steps[-1]
            counts["publishers"] += 1
            assert publisher["uses"] == "softprops/action-gh-release@v3"
            assert publisher["with"] == {
                "body_path": "${{ runner.temp }}/release-body.md",
                "generate_release_notes": False,
                "files": "dist/*.whl\ndist/*.tar.gz\nmisthelper-*.zip\n",
            }
            assert set(publisher) == {"name", "uses", "with"}
        except (AssertionError, KeyError, TypeError, IndexError, AttributeError):
            logging.error("phase=workflow_policy event=failed checked=%s", counts)
            raise
        logging.debug("phase=workflow_policy event=after checked=%s", counts)

    @staticmethod
    def boundary(workflow: dict[str, Any], counts: dict[str, int]) -> list[dict[str, Any]]:
        """Count actual examined mappings while preserving tag-only execution."""
        assert set(workflow) == {"name", "on", "env", "jobs"}
        assert workflow["on"] == {"push": {"tags": ["v*.*.*"]}}
        assert workflow["env"] == {"FORCE_JAVASCRIPT_ACTIONS_TO_NODE24": "true"}
        assert "concurrency" not in workflow
        jobs = workflow["jobs"]
        assert set(jobs) == {"build-python", "build-standalone", "version", "build-container", "publish"}
        for job in jobs.values():
            counts["jobs"] += 1
            assert isinstance(job, dict)
        assert jobs["build-container"]["needs"] == ["version"]
        assert jobs["publish"]["needs"] == ["build-python", "build-standalone", "build-container"]
        assert jobs["publish"]["permissions"] == {"contents": "write"}
        assert set(jobs["publish"]) == {"needs", "runs-on", "permissions", "steps"}
        steps = jobs["publish"]["steps"]
        assert isinstance(steps, list)
        for step in steps:
            counts["steps"] += 1
            assert isinstance(step, dict)
        assert len(steps) == 7
        return steps

    class Preparation:
        """Inspect only the bounded generation and preparation commands."""

        @staticmethod
        def check(steps: list[dict[str, Any]]) -> None:
            """Require the consumed commands, their order, and fatal preparation failures."""
            assert steps[0]["uses"].startswith("actions/checkout@")
            assert steps[0]["with"] == {"ref": "${{ github.ref }}", "persist-credentials": False}
            assert steps[1]["uses"].startswith("actions/setup-python@")
            assert steps[1]["with"] == {"python-version": "3.13"}
            assert steps[2]["uses"].startswith("actions/download-artifact@")
            assert steps[3]["uses"].startswith("actions/download-artifact@")
            assert steps[2]["with"] == {"name": "python-dist", "path": "dist/"}
            assert steps[3]["with"] == {"name": "standalone-bundle"}
            generation, preparation = steps[4:6]
            assert set(generation) == {"name", "id", "shell", "env", "run"}
            assert set(preparation) == {"name", "id", "shell", "env", "run"}
            assert generation["env"] == {"GH_TOKEN": "${{ github.token }}", "RELEASE_TAG": "${{ github.ref_name }}"}
            assert preparation["env"] == {"RELEASE_TAG": "${{ github.ref_name }}"}
            assert generation["shell"] == preparation["shell"] == "bash"
            ReleaseWorkflowContract.Preparation.generation(generation["run"])
            ReleaseWorkflowContract.Preparation.command(preparation["run"])

        @staticmethod
        def generation(script: str) -> None:
            """Permit only the complete read-only request and explicit failure handling."""
            lines = script.splitlines()
            assert len(lines) == 8
            assert lines[0] == "set -euo pipefail"
            assert lines[1] == (
                "printf '%s\\n' 'phase=generate_release_notes event=before completed_requests=0 captured_files=0'"
            )
            assert lines[2] == (
                'if gh api --method POST "repos/${GITHUB_REPOSITORY}/releases/generate-notes" '
                '--raw-field "tag_name=${RELEASE_TAG}" > "${RUNNER_TEMP}/generated-release-notes.json"; then'
            )
            assert [line.strip() for line in lines[3:]] == [
                "printf '%s\\n' 'phase=generate_release_notes event=after completed_requests=1 captured_files=1'",
                "else",
                "printf '%s\\n' 'phase=generate_release_notes event=failed completed_requests=0 captured_files=0' >&2",
                "exit 2",
                "fi",
            ]

        @staticmethod
        def command(script: str) -> None:
            """Inspect the consumed helper arguments instead of searching comments for a path."""
            lines = script.splitlines()
            assert len(lines) == 2 and lines[0] == "set -euo pipefail"
            assert shlex.split(lines[1]) == [
                "python",
                "-m",
                "scripts.release_body",
                "--source",
                "${RUNNER_TEMP}/generated-release-notes.json",
                "--output",
                "${RUNNER_TEMP}/release-body.md",
                "--tag",
                "${RELEASE_TAG}",
                "--repository",
                "${GITHUB_REPOSITORY}",
            ]


class TestReleaseWorkflow:
    """Test the real workflow and negative changes that would restore the defect."""

    @pytest.fixture
    def workflow(self) -> dict[str, Any]:
        """Read this worktree's required source, never another checkout."""
        root = Path(__file__).resolve().parents[2]
        return ReleaseWorkflowContract.read(root / ".github" / "workflows" / "release.yml")

    def test_actual_workflow_source(self, caplog: pytest.LogCaptureFixture) -> None:
        """Require the prepared file, disabled generation, and actual checked counts."""
        caplog.set_level(logging.DEBUG)
        root = Path(__file__).resolve().parents[2]
        workflow = ReleaseWorkflowContract.read(root / ".github" / "workflows" / "release.yml")
        ReleaseWorkflowContract.check(workflow)
        assert "phase=workflow_read event=after checked_files=1" in caplog.text
        assert "event=after checked={'records': 1, 'jobs': 5, 'steps': 7, 'publishers': 1}" in caplog.text

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("generate_release_notes", True),
            ("body_path", "unmeasured.md"),
            ("body", "unmeasured notes"),
            ("append_body", True),
        ],
    )
    def test_wrong_publisher_body_fails(
        self, workflow: dict[str, Any], field: str, value: object, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Reject automatic generation and competing body sources."""
        candidate = deepcopy(workflow)
        candidate["jobs"]["publish"]["steps"][-1]["with"][field] = value
        with pytest.raises(AssertionError):
            ReleaseWorkflowContract.check(candidate)
        assert (
            "phase=workflow_policy event=failed checked={'records': 1, 'jobs': 5, 'steps': 7, 'publishers': 1}"
            in caplog.text
        )

    @pytest.mark.parametrize(
        ("index", "old", "new"),
        [
            (4, "generated-release-notes.json", "wrong-source.json"),
            (4, "exit 2", "exit 0"),
            (4, "set -euo pipefail", "set +e"),
            (5, "scripts.release_body", "scripts.other"),
            (5, "--source", "--unused"),
            (5, "release-body.md", "other-body.md"),
            (5, "set -euo pipefail", "true"),
            (5, '"${GITHUB_REPOSITORY}"', '"${GITHUB_REPOSITORY}" || true'),
        ],
    )
    def test_bypassed_preparation_fails(self, workflow: dict[str, Any], index: int, old: str, new: str) -> None:
        """Prove changed sources, ignored failures, and another output cannot pass."""
        candidate = deepcopy(workflow)
        candidate["jobs"]["publish"]["steps"][index]["run"] = candidate["jobs"]["publish"]["steps"][index][
            "run"
        ].replace(old, new)
        with pytest.raises(AssertionError):
            ReleaseWorkflowContract.check(candidate)

    @pytest.mark.parametrize(
        "kind",
        ["event", "concurrency", "environment", "job-environment", "needs", "continue-on-error", "condition", "order"],
    )
    def test_changed_execution_boundary_fails(
        self, workflow: dict[str, Any], kind: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Keep expensive release execution tag-only and preparation mandatory."""
        candidate = deepcopy(workflow)
        if kind == "event":
            candidate["on"]["workflow_dispatch"] = {}
        elif kind == "concurrency":
            candidate["concurrency"] = {"cancel-in-progress": True}
        elif kind == "environment":
            candidate["env"]["RUNNER_TEMP"] = "/uncontrolled"
        elif kind == "job-environment":
            candidate["jobs"]["publish"]["env"] = {"RUNNER_TEMP": "/uncontrolled"}
        elif kind == "needs":
            candidate["jobs"]["publish"]["needs"] = ["build-python"]
        elif kind == "order":
            steps = candidate["jobs"]["publish"]["steps"]
            steps[0], steps[2] = steps[2], steps[0]
        else:
            candidate["jobs"]["publish"]["steps"][5]["if" if kind == "condition" else kind] = True
        with pytest.raises(AssertionError):
            ReleaseWorkflowContract.check(candidate)
        assert "phase=workflow_policy event=failed checked={'records': 1," in caplog.text
        if kind == "event":
            assert "'jobs': 0, 'steps': 0, 'publishers': 0}" in caplog.text

    @pytest.mark.parametrize("kind", ["missing", "unreadable", "malformed", "empty"])
    def test_required_workflow_input_cannot_skip(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture, kind: str
    ) -> None:
        """Require a real readable YAML mapping and report actual read counts."""
        caplog.set_level(logging.DEBUG)
        path = tmp_path / "release.yml"
        if kind == "missing":
            with pytest.raises(FileNotFoundError):
                ReleaseWorkflowContract.read(path)
        elif kind == "unreadable":
            with patch.object(Path, "read_text", side_effect=PermissionError("cannot read")):
                with pytest.raises(PermissionError):
                    ReleaseWorkflowContract.read(path)
        else:
            path.write_text("jobs: [\n" if kind == "malformed" else "", encoding="utf-8")
            expected = yaml.YAMLError if kind == "malformed" else AssertionError
            with pytest.raises(expected):
                ReleaseWorkflowContract.read(path)
        assert ("checked_files=0" if kind in {"missing", "unreadable"} else "checked_files=1") in caplog.text
