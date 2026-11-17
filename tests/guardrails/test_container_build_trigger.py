"""Keep the container build trigger aligned with Containerfile inputs.

Issue #3549 recorded that changes to files copied into the image could leave
the registry stale because the workflow did not list those files in its push
trigger. Tests are not image inputs, so test-only changes do not start an
image build.
"""

from __future__ import annotations

import shlex
import tomllib  # Read the UV pin from its canonical project declaration.
from copy import deepcopy  # Isolate each workflow mutation used by the failure proofs.
from pathlib import Path
from typing import Any

import pytest  # Prove that weakened workflow contracts fail.
import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONTAINERFILE = REPOSITORY_ROOT / "Containerfile"
WORKFLOW = REPOSITORY_ROOT / ".github" / "workflows" / "container-build.yml"
TRIGGER_KEY = True


def _workflow() -> dict[str, Any]:
    """Read the container workflow as structured YAML."""
    document: dict[str, Any] = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))  # Read the workflow contract.
    return document


def _pinned_uv_version() -> str:
    """Return the UV version from the project development extra."""
    project = tomllib.loads((REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8"))  # Read the pin source.
    requirements = project["project"]["optional-dependencies"]["dev"]  # Select the canonical development set.
    requirement = next(item for item in requirements if item.startswith("uv=="))  # Find the exact UV pin.
    return requirement.removeprefix("uv==")  # Compare the workflow with the project pin.


def _check_locked_test_install(workflow: dict[str, Any]) -> int:
    """Require the pinned UV installer and the synchronized test interpreter."""
    steps = workflow["jobs"]["test"]["steps"]  # Read the unit-test job steps.
    commands = "\n".join(step["run"] for step in steps if "run" in step)  # Collect executable commands.
    assert f"python -m pip install uv=={_pinned_uv_version()}" in commands  # Require the declared UV version.
    assert "uv sync --locked --extra dev --no-install-project" in commands  # Require the locked dev environment.
    assert "uv run --locked --no-sync python -m pytest tests/unit/ -v" in commands  # Use the synced interpreter.
    assert "pip install -r requirements.txt" not in commands  # Reject the unlocked runtime install.
    assert "pip install -r requirements-dev.txt" not in commands  # Reject the unlocked development install.
    return 5  # Count each required installation rule.


def _check_lock_trigger(workflow: dict[str, Any]) -> int:
    """Require lock changes to start a container build."""
    paths = workflow[TRIGGER_KEY]["push"]["paths"]  # Read the build path filters.
    assert "uv.lock" in paths  # Rebuild the image when its dependency lock changes.
    return 1  # Count the checked trigger rule.


def _workflow_paths() -> list[str]:
    """Return the push path filters from the container workflow."""
    document = _workflow()  # Read the live workflow.
    push = document[TRIGGER_KEY]["push"]  # Select the image build trigger.
    paths = push["paths"]  # Read the files that start a build.
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


def test_container_build_uses_the_locked_test_environment() -> None:
    """Require the pinned package manager, locked install, interpreter, and trigger."""
    workflow = _workflow()  # Read the live workflow before checking its contract.
    checked = _check_locked_test_install(workflow) + _check_lock_trigger(workflow)  # Count each required rule.
    print(f"container_build_trigger: checked {checked} workflow rules")  # Report the measured contract size.
    assert checked == 6  # Fail if the guard stops checking one of its declared rules.


@pytest.mark.parametrize("mutation", ["locked-install", "interpreter", "lock-trigger"])
def test_contract_rejects_an_unlocked_build_path(mutation: str) -> None:
    """Prove that each missing lock requirement causes a contract failure."""
    workflow = deepcopy(_workflow())  # Preserve the live workflow for each failure proof.
    steps = workflow["jobs"]["test"]["steps"]  # Select the copied unit-test steps.
    if mutation == "locked-install":  # Remove locked resolution from dependency setup.
        install = next(step for step in steps if step.get("run", "").startswith("uv sync "))  # Find sync.
        install["run"] = "uv sync --extra dev --no-install-project"  # Remove the required lock option.
    elif mutation == "interpreter":  # Replace the synchronized test interpreter.
        test = next(step for step in steps if step.get("run", "").startswith("uv run "))  # Find test command.
        test["run"] = "python -m pytest tests/unit/ -v"  # Bypass the synchronized environment.
    elif mutation == "lock-trigger":  # Stop image builds after lock changes.
        workflow[TRIGGER_KEY]["push"]["paths"].remove("uv.lock")  # Remove the required file filter.
    else:
        pytest.fail(f"Unknown mutation: {mutation}")  # Reject an untested failure proof.
    with pytest.raises(AssertionError):  # Require the weakened workflow to fail its contract.
        _check_lock_trigger(workflow) if mutation == "lock-trigger" else _check_locked_test_install(workflow)
