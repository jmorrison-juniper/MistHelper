"""Test the wheel layout that issue #2246 asked for.

The wheel target held `packages = ["."]`, so the built wheel packed the whole
repository root. An install then copied `src/`, `tests/`, `scripts/`, `specs/`,
and `documentation/` into `site-packages`.

Warning: the copied `src` shadowed the real package for any script that ran from
another folder, and it shadowed part of `pydantic_core` as well, so every test
that reaches Dash failed to collect. Issue #2010 holds that report.

These tests read the setting rather than the built wheel, because a build takes
several minutes and a gate must stay fast. The pull request that changed the
setting recorded the file list of both wheels.
"""

from __future__ import annotations

import logging
import tomllib
from pathlib import Path
from typing import Any

import pytest

# The repository root holds the file under test.
_PYPROJECT = Path(__file__).resolve().parents[3] / "pyproject.toml"

# The folders that must never reach an installed environment. Each one holds
# development material that no consumer of the wheel reads.
_FORBIDDEN_PACKAGES = ("tests", "scripts", "specs", "documentation", "ops-portal", "mist-ops-platform")

# The import roots that the wheel must ship. `src` carries the application,
# `web_portal` carries the portal on port 8055, and `tools` carries the two
# console scripts that `[project.scripts]` declares.
_REQUIRED_PACKAGES = ("src", "tools", "web_portal")

# The modules that sit at the repository root. No package entry can reach them,
# so the wheel target names each one under `force-include`.
_REQUIRED_ROOT_MODULES = ("MistHelper.py", "wsgi.py", "wsgi_capture.py")


@pytest.fixture(name="wheel_target", scope="module")
def fixture_wheel_target() -> dict[str, Any]:
    """Read the wheel build target out of `pyproject.toml`."""
    logging.info("Reading the wheel target from %s", _PYPROJECT)  # Report the read before the work.
    config = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    target = config["tool"]["hatch"]["build"]["targets"]["wheel"]
    logging.debug("The wheel target holds %d keys", len(target))  # Record the shape after the read.
    return dict(target)


def test_the_wheel_never_packs_the_repository_root(wheel_target: dict[str, Any]) -> None:
    """The wheel MUST name its packages, because the root entry packs everything.

    Why:
        `packages = ["."]` packed 4664 files and 24.4 MB, and the install copied
        every one of them into `site-packages`.
    """
    logging.info("Checking that the wheel names no root package")  # Report the plan.
    packages = list(wheel_target.get("packages", []))

    assert "." not in packages, "a root package entry packs the whole repository"
    assert packages, "the wheel must name at least one package"


@pytest.mark.parametrize("name", _REQUIRED_PACKAGES)
def test_the_wheel_ships_every_import_root(wheel_target: dict[str, Any], name: str) -> None:
    """Each import root MUST reach the wheel, or an installed command fails."""
    logging.info("Checking that the wheel ships %s", name)  # Report the plan.

    assert name in wheel_target.get("packages", []), f"{name} must reach the wheel"


@pytest.mark.parametrize("name", _FORBIDDEN_PACKAGES)
def test_the_wheel_ships_no_development_folder(wheel_target: dict[str, Any], name: str) -> None:
    """Development material MUST NOT reach an installed environment."""
    logging.info("Checking that the wheel skips %s", name)  # Report the plan.

    # WHY: a copied folder in site-packages can shadow a real package of the same name.
    assert name not in wheel_target.get("packages", []), f"{name} must not reach the wheel"


@pytest.mark.parametrize("name", _REQUIRED_ROOT_MODULES)
def test_the_wheel_ships_every_root_module(wheel_target: dict[str, Any], name: str) -> None:
    """Each root module MUST reach the wheel through `force-include`.

    Why:
        `MistHelper.py` carries the `misthelper` console script, and the two
        `wsgi` modules carry the two servers. A package entry cannot reach a
        module that sits beside the package roots.
    """
    logging.info("Checking that the wheel ships the root module %s", name)  # Report the plan.
    included = dict(wheel_target.get("force-include", {}))

    assert included.get(name) == name, f"{name} must reach the wheel at the top level"


def test_every_console_script_names_a_shipped_package() -> None:
    """Each console script MUST name a package that the wheel ships.

    Why:
        An entry point that names an absent package installs a command that
        fails with an import error on the first run. The failure reaches the
        consumer and never the build.
    """
    logging.info("Checking every console script against the shipped packages")  # Report the plan.
    config = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    target = config["tool"]["hatch"]["build"]["targets"]["wheel"]
    shipped = set(target.get("packages", [])) | {name.removesuffix(".py") for name in target.get("force-include", {})}

    missing: list[str] = []  # Collect every entry point that names an absent root.
    for command, reference in config["project"]["scripts"].items():
        root = str(reference).split(":", 1)[0].split(".", 1)[0]  # The import root of the reference.
        if root not in shipped:  # The wheel ships no such root, so the command cannot run.
            missing.append(f"{command} -> {reference}")
    logging.debug("Checked %d console scripts", len(config["project"]["scripts"]))  # Record the count.

    assert not missing, f"these console scripts name a package the wheel does not ship: {missing}"
