"""Guardrail: the shipped artifacts hold no development tooling (issue #3404).

Why:
    MistHelper ships two artifacts. The wheel carries the import roots, and the
    container image carries the application files. Neither one may carry the
    in-house development tooling.

    That tooling lives in two trees. `tools/` holds the analyzers and the
    linters. `scripts/` holds the worktree bootstrap, the test-shard runner, and
    the repository analyzers. A customer never runs one of them. The repository
    `jmorrison-juniper/misthelper-devtools` owns that code now.

    Two settings let the tooling back in, and a reader cannot see either one in
    a normal review.

    1. The hatch `packages` list in `pyproject.toml` decides the wheel contents.
       An added name ships a whole tree.
    2. A `COPY` line in the `Dockerfile` decides the image contents. An added
       line ships a whole tree, and `.dockerignore` is the second barrier.

    Warning: a shipped analyzer runs arbitrary repository code by design. It
    reads a source tree and it starts a subprocess. A customer environment must
    never hold that capability.

    Each test states the count of entries that it read. A count of zero means
    the test measured nothing, so each test fails on an unreadable input.
"""

from __future__ import annotations

import logging
import re
import tomllib
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]  # tests/guardrails/<file> sits two levels below the root.
PYPROJECT_PATH = REPOSITORY_ROOT / "pyproject.toml"  # The wheel contents come from this file.
DOCKERFILE_PATH = REPOSITORY_ROOT / "Dockerfile"  # The image contents come from this file.
DOCKERIGNORE_PATH = REPOSITORY_ROOT / ".dockerignore"  # The second barrier for the image.
LOGGER = logging.getLogger(__name__)

# Every top-level directory that holds development tooling. A shipped artifact
# must name none of them.
DEVELOPMENT_TOOLING_TREES = frozenset({"tools", "scripts", "tests", "specs"})

# Every console script that named a module inside `tools`. The wheel exposed
# these two entries before issue #3404, and a customer could start either one.
FORBIDDEN_SCRIPT_MODULE_ROOTS = frozenset({"tools", "scripts"})

# Match a `COPY` instruction and capture its source arguments. A Dockerfile
# `COPY` line can name several sources before the single destination.
COPY_PATTERN = re.compile(r"^\s*COPY\s+(?P<arguments>.+)$", re.MULTILINE)

# `--from`, `--chown`, and the other flags sit before the sources. Drop them.
COPY_FLAG_PREFIX = "--"


def _read_pyproject() -> dict[str, object]:
    """Read and parse the project definition.

    The guard fails when the file is absent, because an unreadable input means
    the guard measured nothing.
    """
    LOGGER.info("Reading the project definition from %s", PYPROJECT_PATH)  # Log before the file read.
    if not PYPROJECT_PATH.is_file():  # A missing file means the guard cannot measure the wheel.
        pytest.fail(f"The guard cannot read its input. No file exists at {PYPROJECT_PATH}.")
    parsed = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))  # Parse the TOML into a mapping.
    LOGGER.debug("Parsed %d top-level tables from the project definition", len(parsed))  # Log the parse result.
    return parsed


def _copy_sources() -> list[str]:
    """Return every source argument of every `COPY` line in the Dockerfile."""
    LOGGER.info("Reading the container recipe from %s", DOCKERFILE_PATH)  # Log before the file read.
    if not DOCKERFILE_PATH.is_file():  # A missing file means the guard cannot measure the image.
        pytest.fail(f"The guard cannot read its input. No file exists at {DOCKERFILE_PATH}.")
    recipe = DOCKERFILE_PATH.read_text(encoding="utf-8")  # Read the whole recipe as one string.
    sources: list[str] = []  # Collect every source argument across every COPY line.
    for match in COPY_PATTERN.finditer(recipe):  # Walk each COPY instruction in file order.
        arguments = match.group("arguments").split()  # Split the instruction into its arguments.
        without_flags = [item for item in arguments if not item.startswith(COPY_FLAG_PREFIX)]  # Drop the flags.
        sources.extend(without_flags[:-1])  # The final argument is the destination, so drop it.
    LOGGER.debug("Read %d source arguments from the container recipe", len(sources))  # Log the count.
    return sources


def test_wheel_packages_hold_no_development_tooling() -> None:
    """The hatch package list names no development tooling tree."""
    parsed = _read_pyproject()  # Read the project definition.
    tool_table = parsed.get("tool", {})  # The hatch settings sit under the `tool` table.
    assert isinstance(tool_table, dict), "The `tool` table must be a mapping."  # Guard the type before the walk.
    wheel_table = tool_table.get("hatch", {}).get("build", {}).get("targets", {}).get("wheel", {})  # type: ignore[union-attr]
    packages = wheel_table.get("packages")  # Read the list that decides the wheel contents.
    assert len(packages) > 0, "The wheel package list is absent, so the guard measured nothing."  # Fail on no input.

    LOGGER.info("Checking %d wheel package entries for development tooling", len(packages))  # Log before the check.
    offenders = sorted(set(packages) & DEVELOPMENT_TOOLING_TREES)  # Find every forbidden entry.
    LOGGER.debug("Checked %d wheel package entries and found %d offenders", len(packages), len(offenders))  # Log it.

    assert not offenders, (
        f"The wheel ships development tooling: {offenders}. "
        f"Checked {len(packages)} package entries. "
        "The repository `jmorrison-juniper/misthelper-devtools` owns that code. "
        "See issue #3404."
    )


def test_console_scripts_name_no_development_tooling() -> None:
    """No console script in the wheel starts a development tool."""
    parsed = _read_pyproject()  # Read the project definition.
    project_table = parsed.get("project", {})  # The console scripts sit under the `project` table.
    assert isinstance(project_table, dict), "The `project` table must be a mapping."  # Guard the type.
    scripts = project_table.get("scripts")  # Read the console script mapping.
    assert len(scripts) > 0, "The console script table is absent, so the guard measured nothing."  # Fail on no input.

    LOGGER.info("Checking %d console script entries for development tooling", len(scripts))  # Log before the check.
    offenders = sorted(
        name
        for name, target in scripts.items()  # type: ignore[union-attr]
        if str(target).split(".", 1)[0] in FORBIDDEN_SCRIPT_MODULE_ROOTS  # The module root sits before the first dot.
    )
    LOGGER.debug("Checked %d console script entries and found %d offenders", len(scripts), len(offenders))  # Log it.

    assert not offenders, (
        f"The wheel exposes a development tool as a console script: {offenders}. "
        f"Checked {len(scripts)} console script entries. "
        "A customer must never start an in-house analyzer. "
        "See issue #3404."
    )


def test_container_copies_no_development_tooling() -> None:
    """No `COPY` line in the Dockerfile brings a development tooling tree in."""
    sources = _copy_sources()  # Read every COPY source argument.
    assert len(sources) > 0, "The container recipe holds no COPY source, so the guard measured nothing."

    LOGGER.info("Checking %d container copy sources for development tooling", len(sources))  # Log before the check.
    offenders = sorted(
        {
            source
            for source in sources
            # A source such as `scripts/` or `./scripts` names the root tree. A
            # source such as `container/scripts/start.sh` does not, because its
            # first path part is `container`.
            if source.strip("./").split("/", 1)[0] in DEVELOPMENT_TOOLING_TREES
        }
    )
    LOGGER.debug("Checked %d container copy sources and found %d offenders", len(sources), len(offenders))  # Log it.

    assert not offenders, (
        f"The container image ships development tooling: {offenders}. "
        f"Checked {len(sources)} copy sources. "
        "No product module reads a file in those trees. "
        "See issue #3404."
    )


def test_dockerignore_excludes_every_development_tooling_tree() -> None:
    """The second barrier holds. `.dockerignore` names every tooling tree."""
    LOGGER.info("Reading the container exclude list from %s", DOCKERIGNORE_PATH)  # Log before the file read.
    if not DOCKERIGNORE_PATH.is_file():  # A missing file means the guard cannot measure the barrier.
        pytest.fail(f"The guard cannot read its input. No file exists at {DOCKERIGNORE_PATH}.")
    lines = [
        line.strip()
        for line in DOCKERIGNORE_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")  # Drop the blank lines and the comments.
    ]
    assert len(lines) > 0, "The container exclude list is empty, so the guard measured nothing."  # Fail on no input.

    patterns = {line.rstrip("/") for line in lines}  # Compare without the trailing separator.
    tree_count = len(DEVELOPMENT_TOOLING_TREES)  # Name the count so the log line stays inside the width limit.
    LOGGER.info("Checking %d container exclude patterns against %d trees", len(patterns), tree_count)
    missing = sorted(DEVELOPMENT_TOOLING_TREES - patterns)  # Find every tree that the list does not name.
    LOGGER.debug("Checked %d exclude patterns and found %d missing trees", len(patterns), len(missing))  # Log it.

    assert not missing, (
        f"The container exclude list names no rule for {missing}. "
        f"Checked {len(patterns)} exclude patterns. "
        "A future `COPY . .` would then ship the tree. "
        "See issue #3404."
    )
