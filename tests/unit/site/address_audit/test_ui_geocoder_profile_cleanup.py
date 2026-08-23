"""Unit tests for the spawned-browser profile cleanup (issue #1862).

Auto mode spawns a debuggable Edge into a throwaway profile directory. That
directory holds the cache, the cookies, and the local storage of a Mist login,
so the teardown path must remove it. Every test here uses a fake process
object, so no test starts a real browser.
"""

import logging  # Capture the WARNING and the DEBUG lines the teardown path emits.
import os  # Confirm the profile directory is gone after the teardown.
import subprocess  # Raise the real TimeoutExpired the teardown path must handle.

import pytest  # Fixtures for a temporary directory and for captured log records.

from src.site.address_audit import MistUIGeocoder  # The class under test.
from src.site.address_audit import ui_geocoder as ui_mod  # Module handle for monkeypatching.


class FakeProcess:
    """A stand-in for the spawned Edge process that records every teardown call."""

    def __init__(self, wait_timeout: bool = False) -> None:
        """Record the calls and choose whether wait() reports a timeout."""
        self.pid = 4242  # A stable identifier so a log line stays readable.
        self.terminate_calls = 0  # Count the polite stop requests the teardown sends.
        self.kill_calls = 0  # Count the forced stop requests the teardown sends.
        self.wait_calls = 0  # Count the reaping waits the teardown sends.
        self._wait_timeout = wait_timeout  # Drive the timeout branch of the teardown path.

    def terminate(self) -> None:
        """Record the polite stop request."""
        self.terminate_calls += 1  # The teardown must ask the browser to exit first.

    def kill(self) -> None:
        """Record the forced stop request and stop the timeout simulation."""
        self.kill_calls += 1  # The teardown must force the exit after a timeout.
        self._wait_timeout = False  # The next wait() reaps the process, so the test can proceed.

    def wait(self, timeout: float | None = None) -> int:
        """Report the exit, or raise a timeout when the test asks for one."""
        self.wait_calls += 1  # The teardown must wait, because Edge locks the profile directory.
        if self._wait_timeout:  # The test drives the kill branch through this flag.
            raise subprocess.TimeoutExpired(cmd="msedge.exe", timeout=timeout or 0.0)
        return 0  # A zero return code means the process exited.


def _geocoder_with_profile(profile_dir: str, proc: FakeProcess) -> MistUIGeocoder:
    """Return a geocoder that owns the given fake process and profile directory."""
    geo = MistUIGeocoder()  # A plain instance, because connect() never runs in these tests.
    geo._spawned_proc = proc  # Pretend auto mode spawned this browser.
    geo._spawned_profile_dir = profile_dir  # Pretend auto mode created this throwaway profile.
    return geo  # The caller drives close() against this instance.


class TestSpawnResult:
    """The spawn helper must hand the profile directory back to the caller."""

    def test_spawn_returns_process_and_profile_dir(self, monkeypatch):
        """The helper returns the process handle and the throwaway profile path."""
        proc = FakeProcess()  # No real browser starts in a unit test.
        monkeypatch.setattr(MistUIGeocoder, "_edge_executable", staticmethod(lambda: "msedge.exe"))
        monkeypatch.setattr(ui_mod.subprocess, "Popen", lambda *a, **k: proc)  # Intercept the spawn.
        spawned = MistUIGeocoder.spawn_debuggable_browser()  # Run the helper under test.
        assert spawned is not None  # Edge resolved, so the helper must report a spawn.
        assert spawned.process is proc  # The caller needs the handle to stop the browser.
        assert os.path.isdir(spawned.profile_dir)  # The caller needs a real path to remove.
        ui_mod.shutil.rmtree(spawned.profile_dir, ignore_errors=True)  # Keep the test host clean.

    def test_spawn_returns_none_without_edge(self, monkeypatch):
        """A missing Edge binary still yields None, so auto mode can fall back."""
        monkeypatch.setattr(MistUIGeocoder, "_edge_executable", staticmethod(lambda: None))
        assert MistUIGeocoder.spawn_debuggable_browser() is None  # No Edge means no spawn result.


class TestProfileTeardown:
    """close() must remove the throwaway profile after the browser process stops."""

    def test_close_removes_profile_directory(self, tmp_path):
        """The profile directory is gone after the teardown path runs."""
        profile = tmp_path / "misthelper-edge-test"  # A stand-in for the throwaway profile.
        profile.mkdir()  # The teardown path only removes a directory that exists.
        (profile / "Cookies").write_text("session-material", encoding="utf-8")  # Prove a full tree is removed.
        proc = FakeProcess()  # A fake browser, so no real Edge starts.
        geo = _geocoder_with_profile(str(profile), proc)  # Own both the process and the profile.
        geo.close()  # Run the teardown path under test.
        assert proc.terminate_calls == 1  # The teardown must stop the browser first.
        assert proc.wait_calls >= 1  # The teardown must wait, because Edge locks the profile.
        assert not profile.exists()  # The leaked directory of issue #1862 must be gone.

    def test_close_waits_before_removing_the_profile(self, tmp_path):
        """The browser process stops before the removal, because Edge locks the profile."""
        profile = tmp_path / "misthelper-edge-order"  # A stand-in for the throwaway profile.
        profile.mkdir()  # The teardown path only removes a directory that exists.
        order: list[str] = []  # Record the call order to prove the sequence.
        proc = FakeProcess()  # A fake browser, so no real Edge starts.
        original_wait = proc.wait  # Keep the original behavior of the fake process.

        def _record_wait(timeout: float | None = None) -> int:
            """Record the wait, then delegate to the fake process."""
            order.append("wait")  # The wait must happen before the removal.
            return original_wait(timeout)  # Preserve the exit report of the fake process.

        proc.wait = _record_wait  # type: ignore[method-assign]  # Observe the ordering.
        geo = _geocoder_with_profile(str(profile), proc)  # Own both the process and the profile.
        geo.close()  # Run the teardown path under test.
        order.append("removed" if not profile.exists() else "leaked")  # Record the removal outcome.
        assert order == ["wait", "removed"]  # The wait precedes a successful removal.

    def test_close_kills_a_browser_that_ignores_terminate(self, tmp_path):
        """A stop timeout leads to a kill, and the profile still goes away."""
        profile = tmp_path / "misthelper-edge-stuck"  # A stand-in for the throwaway profile.
        profile.mkdir()  # The teardown path only removes a directory that exists.
        proc = FakeProcess(wait_timeout=True)  # This fake browser ignores the polite stop request.
        geo = _geocoder_with_profile(str(profile), proc)  # Own both the process and the profile.
        geo.close()  # Run the teardown path under test.
        assert proc.kill_calls == 1  # A stuck browser must be killed to release the profile lock.
        assert not profile.exists()  # The profile must still be removed after the kill.

    def test_close_logs_the_removed_path(self, tmp_path, caplog):
        """One DEBUG line names the removed path, so an operator can confirm the cleanup."""
        profile = tmp_path / "misthelper-edge-logged"  # A stand-in for the throwaway profile.
        profile.mkdir()  # The teardown path only removes a directory that exists.
        geo = _geocoder_with_profile(str(profile), FakeProcess())  # Own both the process and the profile.
        with caplog.at_level(logging.DEBUG):  # The confirmation line is a DEBUG record.
            geo.close()  # Run the teardown path under test.
        assert str(profile) in caplog.text  # The operator needs the exact path in the log.


class TestTeardownSafety:
    """The teardown path must stay idempotent and must never raise."""

    def test_second_close_does_nothing(self, tmp_path):
        """A second close() call stops no process again and raises nothing."""
        profile = tmp_path / "misthelper-edge-twice"  # A stand-in for the throwaway profile.
        profile.mkdir()  # The teardown path only removes a directory that exists.
        proc = FakeProcess()  # A fake browser, so no real Edge starts.
        geo = _geocoder_with_profile(str(profile), proc)  # Own both the process and the profile.
        geo.close()  # The first call performs the whole teardown.
        geo.close()  # The second call must be a no-op.
        assert proc.terminate_calls == 1  # The teardown must not stop the browser twice.
        assert geo._spawned_proc is None  # The handle stays cleared after the second call.
        assert geo._spawned_profile_dir is None  # The profile path stays cleared after the second call.

    def test_removal_failure_logs_a_warning(self, tmp_path, monkeypatch, caplog):
        """A removal failure logs a WARNING and never raises out of the teardown."""
        profile = tmp_path / "misthelper-edge-locked"  # A stand-in for the throwaway profile.
        profile.mkdir()  # The teardown path only removes a directory that exists.

        def _boom(path: str, ignore_errors: bool = False) -> None:
            """Simulate a locked profile directory that cannot be removed."""
            raise OSError("The directory is locked by another process")

        monkeypatch.setattr(ui_mod.shutil, "rmtree", _boom)  # Force the failure branch.
        geo = _geocoder_with_profile(str(profile), FakeProcess())  # Own both the process and the profile.
        with caplog.at_level(logging.WARNING):  # The failure branch must warn the operator.
            geo.close()  # The teardown must swallow the failure.
        assert "profile" in caplog.text.lower()  # The warning must name the profile directory.
        assert geo._spawned_profile_dir is None  # A failed removal still clears the handle.

    def test_close_without_a_spawned_browser_is_safe(self):
        """Attach mode and launch mode own no profile, so the teardown does nothing."""
        geo = MistUIGeocoder()  # No spawn happened in this instance.
        geo.close()  # The teardown must accept an empty state.
        assert geo._spawned_proc is None  # No process handle exists to clear.
        assert geo._spawned_profile_dir is None  # No profile path exists to clear.


if __name__ == "__main__":  # Allow a direct run during local development.
    raise SystemExit(pytest.main([__file__, "-q"]))  # Run only this module.
