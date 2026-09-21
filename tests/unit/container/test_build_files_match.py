"""Guard the two build descriptions against drift.

Issue #3130: the repository holds two files that describe the same image.
Podman prefers the name `Containerfile` and Docker prefers `Dockerfile`, so a
change that lands in one file repairs one build only.

The two files drifted by 33 lines. `Containerfile` installed the SNMP tools and
set two port variables that `Dockerfile` did not, and the two copied the
application in a different order.

The drift produced a silent failure. While repairing issue #3104 I added one
`COPY` line to `Dockerfile`, and the build reported success with the file still
absent from the image.

```text
build rc=0
ls: cannot access '/app/documentation/': No such file or directory
```

Podman had read `Containerfile`, so the new step never ran. A build can
therefore report success while it ignores the change an engineer made, and no
gate reported the difference.

These tests hold one rule: the two files stay byte-identical.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCKERFILE = REPOSITORY_ROOT / "Dockerfile"
CONTAINERFILE = REPOSITORY_ROOT / "Containerfile"
WORKFLOW_DIR = REPOSITORY_ROOT / ".github" / "workflows"
BUILD_WORKFLOWS = ("container-build.yml", "release.yml")


def _digest(path: Path) -> str:
    """Return the SHA-256 digest of one file, read as bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TestBothBuildFilesExist:
    """Each tool must find the name it prefers."""

    @pytest.mark.parametrize("path", [DOCKERFILE, CONTAINERFILE], ids=["Dockerfile", "Containerfile"])
    def test_build_file_is_present(self, path):
        """A missing file sends that tool to an implicit build or to a failure."""
        assert path.is_file()

    @pytest.mark.parametrize("path", [DOCKERFILE, CONTAINERFILE], ids=["Dockerfile", "Containerfile"])
    def test_build_file_is_not_empty(self, path):
        """An empty description would build an image that holds nothing."""
        assert len(path.read_bytes()) > 0


class TestTheTwoBuildFilesMatch:
    """A change must reach every build, whichever name the tool reads."""

    def test_contents_are_byte_identical(self):
        """One digest proves the whole file, including whitespace and line endings."""
        assert _digest(DOCKERFILE) == _digest(CONTAINERFILE), (
            "Dockerfile and Containerfile differ. Podman reads Containerfile and Docker reads Dockerfile, "
            "so a change in one file repairs one build only. Copy Containerfile over Dockerfile."
        )

    def test_no_line_differs(self):
        """A line report names the drift, because a digest alone does not."""
        left = DOCKERFILE.read_text(encoding="utf-8").splitlines()
        right = CONTAINERFILE.read_text(encoding="utf-8").splitlines()
        differing = [index for index, (a, b) in enumerate(zip(left, right, strict=False), start=1) if a != b]
        assert differing == []
        assert len(left) == len(right)  # A file that only appends still drifts.

    def test_the_rule_is_written_in_the_file(self):
        """An engineer who opens either file must meet the rule before an edit."""
        text = CONTAINERFILE.read_text(encoding="utf-8")
        assert "byte-identical" in text
        assert "#3130" in text


class TestTheWorkflowsBuildAKnownFile:
    """The gate must guard the file that the released image really uses."""

    @pytest.mark.parametrize("workflow", BUILD_WORKFLOWS)
    def test_workflow_names_a_build_file_this_test_guards(self, workflow):
        """A workflow that builds an unguarded file would escape this rule."""
        path = WORKFLOW_DIR / workflow
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        named = _collect_build_file_values(document)
        assert len(named) >= 1, f"{workflow} must name the build file it uses"
        for value in named:
            assert Path(value).name in {DOCKERFILE.name, CONTAINERFILE.name}


def _collect_build_file_values(node) -> list[str]:
    """Return every `file:` value that names a build description."""
    found: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "file" and isinstance(value, str) and ("Dockerfile" in value or "Containerfile" in value):
                found.append(value)
            found.extend(_collect_build_file_values(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(_collect_build_file_values(item))
    return found
