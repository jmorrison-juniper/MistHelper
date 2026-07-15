"""Wave 4 P2 coverage for src/refactors/data_directory_checker.py (initiative #1018).

Covers `DataDirectoryChecker.check` end-to-end plus all print/log branches of
`_handle_permission_error`. Uses tmp_path for real writable-directory validation
and monkeypatch to force PermissionError / non-permission-error branches. Uses
monkeypatch on `os.path.exists` and `sys.exit` to exercise container-detection
and local-guidance branches without terminating the test process. No source
edits, no live I/O outside pytest's tmp_path fixture.
"""

from __future__ import annotations  # WHY: PEP 604 unions in test type hints under Python 3.10+.

import logging  # WHY: verify structured error/info/debug log emission.
import os  # WHY: monkeypatch os.path.exists to simulate container markers.
from pathlib import Path  # WHY: tmp_path fixture returns pathlib.Path.

import pytest  # WHY: monkeypatch, tmp_path, capsys, caplog fixtures.

from src.refactors.data_directory_checker import DataDirectoryChecker  # WHY: SUT direct import.


class TestInit:
    """Constructor stores data_dir and derives .write_test path."""

    def test_init_sets_data_dir_and_test_file(self, tmp_path: Path) -> None:
        """__init__ stores the target directory and computes the .write_test path."""
        checker = DataDirectoryChecker(str(tmp_path))  # WHY: construct with real writable directory.
        assert checker.data_dir == str(tmp_path)  # WHY: attribute preserved verbatim.
        assert checker.test_file == os.path.join(str(tmp_path), ".write_test")  # WHY: derived test-file path.


class TestCheckHappyPath:
    """`check()` returns True and cleans up the marker file when the directory is writable."""

    def test_writable_directory_returns_true_and_cleans_up(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Writable directory returns True; the .write_test file must not persist afterward."""
        checker = DataDirectoryChecker(str(tmp_path))  # WHY: construct against real writable tmp dir.
        with caplog.at_level(logging.DEBUG):  # WHY: capture debug-level ok log.
            assert checker.check() is True  # WHY: happy-path returns True.
        assert not os.path.exists(checker.test_file)  # WHY: marker file removed after successful write.
        assert "write permission ok" in caplog.text  # WHY: post-check debug log present.


class TestCheckPermissionError:
    """`check()` catches PermissionError, prints guidance, and exits(1)."""

    def test_permission_error_local_guidance_exits(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Non-container PermissionError prints local guidance and calls sys.exit(1)."""
        checker = DataDirectoryChecker(str(tmp_path))  # WHY: fresh instance with real path for abspath print.

        def _raise_permission_error(self: DataDirectoryChecker) -> bool:
            """Force PermissionError inside _test_write_permission."""
            raise PermissionError("access denied")  # WHY: simulate un-writable directory.

        monkeypatch.setattr(
            DataDirectoryChecker, "_test_write_permission", _raise_permission_error
        )  # WHY: force perm-error branch without OS-level chmod.
        monkeypatch.setattr(
            os.path, "exists", lambda p: False
        )  # WHY: neither container marker exists → local-guidance branch.
        exit_calls: list[int] = []  # WHY: capture sys.exit code without killing the test process.
        monkeypatch.setattr(
            "src.refactors.data_directory_checker.sys.exit",
            lambda code: exit_calls.append(code),
        )  # WHY: intercept exit for assertion.

        with caplog.at_level(logging.ERROR):  # WHY: _handle_permission_error logs ERROR.
            result = checker.check()  # WHY: exercise perm-error → local-guidance → exit branch.

        assert result is False  # WHY: perm branch returns False after (mocked) sys.exit.
        assert exit_calls == [1]  # WHY: sys.exit(1) was invoked.
        captured = capsys.readouterr()  # WHY: read printed guidance banner.
        assert "ERROR: Data directory is not writable!" in captured.out  # WHY: header printed.
        assert "chmod -R 755 data/" in captured.out  # WHY: local-guidance line present.
        assert "chown -R $(whoami) data/" in captured.out  # WHY: local ownership guidance present.
        assert "[CONTAINER DETECTED]" not in captured.out  # WHY: container guidance suppressed in local branch.
        assert "is not writable" in caplog.text  # WHY: error log emitted.

    def test_permission_error_container_guidance(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Container marker triggers container-specific guidance instead of local."""
        checker = DataDirectoryChecker(str(tmp_path))  # WHY: fresh instance for container branch.

        def _raise_permission_error(self: DataDirectoryChecker) -> bool:
            """Force PermissionError inside _test_write_permission."""
            raise PermissionError("access denied")  # WHY: trigger perm-error handler.

        monkeypatch.setattr(
            DataDirectoryChecker, "_test_write_permission", _raise_permission_error
        )  # WHY: force perm-error.
        monkeypatch.setattr(
            os.path, "exists", lambda p: p == "/.dockerenv"
        )  # WHY: simulate docker container marker present.
        monkeypatch.setattr(
            "src.refactors.data_directory_checker.sys.exit", lambda code: None
        )  # WHY: neutralize sys.exit for the test.

        checker.check()  # WHY: exercise container-guidance branch.

        captured = capsys.readouterr()  # WHY: capture container-specific print output.
        assert "[CONTAINER DETECTED]" in captured.out  # WHY: container banner printed.
        assert "podman stop misthelper" in captured.out  # WHY: container remediation shown.
        assert "chmod -R 755 data/" not in captured.out  # WHY: local guidance suppressed in container branch.

    def test_containerenv_marker_also_detects_container(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """/run/.containerenv (podman) also flags container mode."""
        checker = DataDirectoryChecker(str(tmp_path))  # WHY: fresh instance.

        def _raise_permission_error(self: DataDirectoryChecker) -> bool:
            """Force PermissionError inside _test_write_permission."""
            raise PermissionError("access denied")  # WHY: trigger perm-error handler.

        monkeypatch.setattr(
            DataDirectoryChecker, "_test_write_permission", _raise_permission_error
        )  # WHY: force perm-error.
        monkeypatch.setattr(os.path, "exists", lambda p: p == "/run/.containerenv")  # WHY: podman marker present.
        monkeypatch.setattr(
            "src.refactors.data_directory_checker.sys.exit", lambda code: None
        )  # WHY: neutralize sys.exit.

        checker.check()  # WHY: exercise the alt container-marker branch.

        captured = capsys.readouterr()  # WHY: assert on printed output.
        assert "[CONTAINER DETECTED]" in captured.out  # WHY: container banner still triggered.


class TestCheckNonPermissionError:
    """`check()` swallows non-permission exceptions and returns True."""

    def test_generic_exception_returns_true_and_logs_defer(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """OSError (non-permission) causes check() to defer failure and return True."""
        checker = DataDirectoryChecker(str(tmp_path))  # WHY: real path, but forced to raise below.

        def _raise_generic(self: DataDirectoryChecker) -> bool:
            """Force a non-permission exception inside _test_write_permission."""
            raise OSError("disk gone")  # WHY: not a PermissionError → falls through to generic branch.

        monkeypatch.setattr(
            DataDirectoryChecker, "_test_write_permission", _raise_generic
        )  # WHY: force non-perm exception.

        with caplog.at_level(logging.DEBUG):  # WHY: generic branch logs at DEBUG.
            result = checker.check()  # WHY: exercise the non-permission branch.

        assert result is True  # WHY: non-permission errors are deferred.
        assert "deferring failure" in caplog.text  # WHY: assert the debug log we expect.


class TestIsRunningInContainer:
    """`_is_running_in_container` returns True when either marker file exists."""

    def test_no_markers_returns_false(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Neither /.dockerenv nor /run/.containerenv exists → False."""
        monkeypatch.setattr(os.path, "exists", lambda p: False)  # WHY: force both markers absent.
        checker = DataDirectoryChecker(str(tmp_path))  # WHY: minimal instance for helper call.
        assert checker._is_running_in_container() is False  # WHY: expected in a non-container test env.

    def test_dockerenv_marker_returns_true(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """/.dockerenv marker returns True."""
        monkeypatch.setattr(os.path, "exists", lambda p: p == "/.dockerenv")  # WHY: only docker marker present.
        checker = DataDirectoryChecker(str(tmp_path))  # WHY: minimal instance.
        assert checker._is_running_in_container() is True  # WHY: docker marker sufficient.

    def test_containerenv_marker_returns_true(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """/run/.containerenv marker returns True."""
        monkeypatch.setattr(os.path, "exists", lambda p: p == "/run/.containerenv")  # WHY: only podman marker present.
        checker = DataDirectoryChecker(str(tmp_path))  # WHY: minimal instance.
        assert checker._is_running_in_container() is True  # WHY: podman marker sufficient.
