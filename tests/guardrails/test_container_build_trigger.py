"""Keep the container build trigger aligned with Containerfile inputs.

Issue #3549 recorded that changes to files copied into the image could leave
the registry stale because the workflow did not list those files in its push
trigger. Tests are not image inputs, so test-only changes do not start an
image build.
"""

from __future__ import annotations

import shlex
from pathlib import Path
from typing import Any

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONTAINERFILE = REPOSITORY_ROOT / "Containerfile"
WORKFLOW = REPOSITORY_ROOT / ".github" / "workflows" / "container-build.yml"
TRIGGER_KEY = True


def _workflow_paths() -> list[str]:
    """Return the push path filters from the container workflow."""
    document: dict[str, Any] = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    push = document[TRIGGER_KEY]["push"]
    paths = push["paths"]
    assert isinstance(paths, list)
    return [path for path in paths if isinstance(path, str)]


def _copied_repository_paths() -> list[str]:
    """Return fixed repository sources from COPY instructions."""
    copied: list[str] = []
    for line in CONTAINERFILE.read_text(encoding="utf-8").splitlines():
        if not line.lstrip().startswith("COPY "):
            continue
        parts = shlex.split(line, comments=True)
        sources = parts[1:-1]
        copied.extend(source for source in sources if not source.startswith("${"))
    return copied


def _path_filter_covers(source: str, path_filter: str) -> bool:
    """Return whether one workflow path filter covers a COPY source."""
    source = source.removesuffix("/")
    if path_filter.endswith("/**"):
        directory = path_filter[:-3].removesuffix("/")
        return source == directory or source.startswith(f"{directory}/")
    return source == path_filter


def test_every_fixed_copy_source_starts_an_image_build() -> None:
    """Every fixed COPY source must appear in the push path filters."""
    paths = _workflow_paths()
    missing = [
        source for source in _copied_repository_paths() if not any(_path_filter_covers(source, path) for path in paths)
    ]
    assert missing == [], f"Containerfile COPY sources missing from workflow paths: {missing}"


def test_test_only_changes_do_not_start_an_image_build() -> None:
    """Tests are not copied into the image and must not trigger its build."""
    assert "tests/**" not in _workflow_paths()
