"""Guard the environment checks that `tests/conftest.py` runs before collection.

Why:
    Two environment faults have cost real time in this repository, and neither one
    announced itself. Issue #1866 records a worktree with no virtual environment,
    which turned into one import error for each test module. Issue #2010 records a
    stale copy of the repository inside `site-packages`, which shadowed the real
    package and made a green result meaningless.

    Both checks live in `tests/conftest.py` and run before pytest collects a
    single module. A check that nobody tests can stop working in silence, so
    these tests read the two helpers directly.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests import conftest as environment


class TestTheStaleCopyGuard:
    """The name `src` must resolve inside this repository."""

    def test_the_repository_root_holds_this_test_file(self) -> None:
        """The recorded root must be the checkout that holds the suite."""
        assert (environment._REPOSITORY_ROOT / "tests" / "conftest.py").is_file()

    def test_a_healthy_environment_reports_no_shadow(self) -> None:
        """The guard stays quiet when `src` resolves inside the repository."""
        assert environment._shadowing_source_path() is None, "The active environment holds a stale copy of src."

    def test_the_guard_names_a_copy_that_sits_outside_the_repository(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A `src` package under another root must read as a shadow."""
        outside = tmp_path / "site-packages" / "src" / "__init__.py"  # The shape the stale wheel leaves behind.
        outside.parent.mkdir(parents=True)  # Build the directory, because the guard resolves a real path.
        outside.write_text("", encoding="utf-8")  # An empty file is enough for a path compare.

        class _Spec:
            """Stand in for the module spec that `find_spec` answers."""

            origin = str(outside)  # The one attribute the guard reads.

        monkeypatch.setattr(environment.importlib.util, "find_spec", lambda name: _Spec())
        assert environment._shadowing_source_path() == outside.resolve()

    def test_a_namespace_package_reports_no_shadow(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A spec with no file names no copy, so the guard stays quiet."""

        class _Spec:
            """Stand in for a namespace package, which carries no origin."""

            origin = None  # A namespace package holds no single file.

        monkeypatch.setattr(environment.importlib.util, "find_spec", lambda name: _Spec())
        assert environment._shadowing_source_path() is None

    def test_a_broken_entry_reports_no_shadow(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A lookup that raises must not stop the session with the wrong cause."""

        def raising(name: str) -> None:
            """Raise the fault that a broken path entry produces."""
            raise ValueError("the path entry is broken")  # The guard catches this class.

        monkeypatch.setattr(environment.importlib.util, "find_spec", raising)
        assert environment._shadowing_source_path() is None


class TestTheMessagesTellTheReaderWhatToDo:
    """Each message must name the fault, the cause, and one command."""

    def test_the_shadow_message_names_the_path_and_the_command(self) -> None:
        """A reader must repair the environment from the message alone."""
        message = environment._shadow_message(Path("C:/somewhere/site-packages/src/__init__.py"))
        assert "site-packages" in message, "The message hides the path it found."
        assert environment._UNINSTALL_COMMAND in message, "The message names no repair command."
        assert "#2010" in message, "The message cites no issue."

    def test_the_bootstrap_message_names_every_missing_package(self) -> None:
        """The older guard must keep listing every gap on one line."""
        message = environment._bootstrap_message(["mistapi", "structlog"])
        assert "mistapi, structlog" in message, "The message drops a package name."
        assert environment._BOOTSTRAP_COMMAND in message, "The message names no repair command."
