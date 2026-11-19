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


def _named_step_position(steps: list[dict[str, Any]], name: str) -> tuple[int, dict[str, Any]]:
    """Return one uniquely named workflow step and its position."""
    matches = [(index, step) for index, step in enumerate(steps) if step.get("name") == name]  # Match one step.
    assert len(matches) == 1, f"Expected one workflow step named {name!r}, found {len(matches)}"  # Reject ambiguity.
    return matches[0]  # Preserve the order for the installation contract.


def _run_commands(steps: list[dict[str, Any]]) -> list[tuple[str, list[str]]]:
    """Return shell commands without commented text."""
    commands: list[tuple[str, list[str]]] = []  # Keep executable tokens with their workflow step.
    for step in steps:  # Inspect every step so extra test commands cannot hide.
        run = step.get("run")  # Read only executable workflow content.
        if not isinstance(run, str):  # Ignore steps that use an action instead of a shell.
            continue
        for line in run.splitlines():  # Check each shell line separately.
            tokens = shlex.split(line, comments=True)  # Exclude shell comments from executable commands.
            if tokens:  # Keep commands that contain executable tokens.
                commands.append((step.get("name", ""), tokens))  # Keep the source step for order checks.
    return commands  # Return parsed commands for the workflow contract.


def _contains_tokens(tokens: list[str], expected: list[str]) -> bool:
    """Return whether a command contains one exact token sequence."""
    return any(  # Check each possible command position.
        tokens[index : index + len(expected)] == expected  # Match complete shell tokens, not text fragments.
        for index in range(len(tokens) - len(expected) + 1)  # Stop before an incomplete match.
    )


def _pytest_invocations(commands: list[tuple[str, list[str]]]) -> list[tuple[str, list[str]]]:
    """Return each executable Python pytest command."""
    invocation = ["python", "-m", "pytest"]  # Identify pytest calls that could bypass the UV environment.
    return [  # Keep every matching command for the single-invocation contract.
        (name, tokens)  # Preserve step and command for exact validation.
        for name, tokens in commands  # Inspect executable shell commands.
        if _contains_tokens(tokens, invocation)  # Exclude comments and unrelated text.
    ]


def _check_locked_test_install(workflow: dict[str, Any]) -> int:
    """Require the pinned UV installer and the synchronized test interpreter."""
    steps = workflow["jobs"]["test"]["steps"]  # Read the unit-test job steps.
    uv_index, uv_step = _named_step_position(steps, "Install pinned UV")  # Locate the pinned installer.
    sync_index, sync_step = _named_step_position(steps, "Sync locked test dependencies")  # Locate the sync.
    test_index, test_step = _named_step_position(steps, "Run unit tests")  # Locate the unit-test command.
    assert uv_step.get("run") == f"python -m pip install uv=={_pinned_uv_version()}"  # Require the declared pin.
    assert sync_step.get("run") == "uv sync --locked --extra dev --no-install-project"  # Require locked setup.
    assert test_step.get("run") == "uv run --locked --no-sync python -m pytest tests/unit/ -v"  # Use synced Python.
    assert uv_index < sync_index < test_index  # Install and sync before running tests.
    commands = _run_commands(steps)  # Parse all executable lines, including steps after the unit tests.
    expected_test = shlex.split(test_step["run"])  # Compare the complete command as shell tokens.
    assert _pytest_invocations(commands) == [("Run unit tests", expected_test)]  # Reject extra global pytest calls.
    unlocked = (
        ["pip", "install", "-r", "requirements.txt"],  # Reject the unlocked runtime dependency export.
        ["pip", "install", "-r", "requirements-dev.txt"],  # Reject the unlocked development dependency export.
    )
    assert not any(  # Require both dependency groups to use the lock.
        _contains_tokens(tokens, old_install) for _, tokens in commands for old_install in unlocked
    ), "Container tests must not install from requirements files"
    return 10  # Count step identity, exact commands, order, pytest isolation, and old-install rules.


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
    assert checked == 11  # Fail if the guard stops checking one of its declared rules.


def _apply_workflow_mutation(workflow: dict[str, Any], mutation: str) -> None:
    """Apply one invalid workflow change for a contract failure proof."""
    steps = workflow["jobs"]["test"]["steps"]  # Select the copied unit-test steps.
    if mutation == "locked-install":  # Remove locked resolution from dependency setup.
        install = next(step for step in steps if step.get("run", "").startswith("uv sync "))  # Find sync.
        install["run"] = "uv sync --extra dev --no-install-project"  # Remove the required lock option.
    elif mutation == "interpreter":  # Replace the synchronized test interpreter.
        test = next(step for step in steps if step.get("run", "").startswith("uv run "))  # Find test command.
        test["run"] = "python -m pytest tests/unit/ -v"  # Bypass the synchronized environment.
    elif mutation == "lock-trigger":  # Stop image builds after lock changes.
        workflow[TRIGGER_KEY]["push"]["paths"].remove("uv.lock")  # Remove the required file filter.
    elif mutation == "commented-command":  # Replace the locked sync with a shell comment.
        install = next(step for step in steps if step.get("name") == "Sync locked test dependencies")  # Find sync.
        install["run"] = "# uv sync --locked --extra dev --no-install-project"  # Disable the sync command.
    elif mutation == "sync-after-test":  # Place dependency setup after the test command.
        install = next(step for step in steps if step.get("name") == "Sync locked test dependencies")  # Find sync.
        steps.remove(install)  # Remove sync before placing it after tests.
        test = next(step for step in steps if step.get("name") == "Run unit tests")  # Find the test step.
        steps.insert(steps.index(test) + 1, install)  # Move dependency setup after the tests.
    elif mutation == "global-pytest":  # Add a second test call outside the UV interpreter.
        steps.append({"name": "Run tests globally", "run": "python -m pytest tests/unit/ -v"})  # Add global pytest.
    else:
        pytest.fail(f"Unknown mutation: {mutation}")  # Reject an untested failure proof.


@pytest.mark.parametrize(
    "mutation",
    ["locked-install", "interpreter", "lock-trigger", "commented-command", "sync-after-test", "global-pytest"],
)
def test_contract_rejects_an_unlocked_build_path(mutation: str) -> None:
    """Prove that each missing lock requirement causes a contract failure."""
    workflow = deepcopy(_workflow())  # Preserve the live workflow for each failure proof.
    _apply_workflow_mutation(workflow, mutation)  # Weaken one requirement at a time.
    with pytest.raises(AssertionError):  # Require the weakened workflow to fail its contract.
        _check_lock_trigger(workflow) if mutation == "lock-trigger" else _check_locked_test_install(workflow)
