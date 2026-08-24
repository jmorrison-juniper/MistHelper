"""Security tests for the web portal data browser path guard.

The tests prove two defects in `DataBrowserService.resolve_safe_path`.

1. The guard did not resolve a symbolic link, so a link inside the data
   directory reached a file outside the data directory.
2. The guard did not apply the `ALLOWED_EXTENSIONS` allowlist, so the download
   route served a file that the listing route hides.
"""

from __future__ import annotations

import os

import pytest

from web_portal.services.data_browser import DataBrowserService


def _symlink_supported(tmp_path) -> bool:
    """Report whether this account may create a symbolic link."""
    probe_target = tmp_path / "probe_target.txt"  # Real file that the probe link points at.
    probe_target.write_text("probe")  # A link needs an existing target on Windows.
    probe_link = tmp_path / "probe_link.txt"  # Link path that the probe tries to create.
    try:
        os.symlink(probe_target, probe_link)  # Windows refuses this without the symlink privilege.
    except (OSError, NotImplementedError):
        return False  # The account lacks the privilege, so the caller must skip the test.
    os.unlink(probe_link)  # Remove the probe link so the temporary tree stays clean.
    return True  # The account may create a symbolic link.


@pytest.fixture
def data_dir(tmp_path):
    """Build an empty data directory and return its path."""
    target = tmp_path / "data"  # Mirror the runtime layout, where exports live under `data/`.
    target.mkdir()  # The service returns an empty listing when the directory is absent.
    return target


class TestSymlinkEscape:
    """Prove that a symbolic link cannot leave the data directory."""

    def test_symlink_to_outside_file_is_rejected(self, tmp_path, data_dir):
        """A link that points outside the data directory must not resolve."""
        if not _symlink_supported(tmp_path):
            pytest.skip("This account may not create a symbolic link.")
        secret = tmp_path / "dotenv_secret"  # Stand in for `/app/.env`, which holds the API token.
        secret.write_text("MIST_APITOKEN=abcd1234")  # Content that the attacker wants to read.
        link = data_dir / "notes.csv"  # Allowed extension, so only the link check can stop it.
        os.symlink(secret, link)  # The attacker creates the link in the world-writable data mount.

        service = DataBrowserService(str(data_dir))  # Service under test, scoped to the data mount.

        assert service.resolve_safe_path("notes.csv") is None  # The guard must refuse the escape.

    def test_symlinked_sibling_directory_is_rejected(self, tmp_path, data_dir):
        """A link into a sibling with a shared name prefix must not resolve."""
        if not _symlink_supported(tmp_path):
            pytest.skip("This account may not create a symbolic link.")
        sibling = tmp_path / "data_backup"  # Name shares the `data` prefix, so `startswith` passed.
        sibling.mkdir()  # The sibling must exist before the link can point at it.
        (sibling / "dump.csv").write_text("secret\n")  # File that the guard must keep out of reach.
        os.symlink(sibling, data_dir / "backup", target_is_directory=True)  # The escape hatch.

        service = DataBrowserService(str(data_dir))  # Service under test, scoped to the data mount.

        assert service.resolve_safe_path("backup/dump.csv") is None  # The guard must refuse it.


class TestExtensionAllowlist:
    """Prove that the download guard applies the listing allowlist."""

    def test_disallowed_extension_is_rejected(self, data_dir):
        """A private key file must not resolve, because the listing hides it."""
        (data_dir / "id_rsa").write_text("PRIVATE KEY")  # No extension, so the listing hides it.

        service = DataBrowserService(str(data_dir))  # Service under test, scoped to the data mount.

        assert service.resolve_safe_path("id_rsa") is None  # The guard must apply the allowlist.

    def test_nested_disallowed_extension_is_rejected(self, data_dir):
        """A nested file with a disallowed extension must not resolve."""
        nested = data_dir / "per-host-logs"  # The SSH runner writes a session record per device.
        nested.mkdir()  # The listing reads only the top level, so it never shows this tree.
        (nested / "sw1.pem").write_text("PRIVATE KEY")  # Disallowed extension in a nested folder.

        service = DataBrowserService(str(data_dir))  # Service under test, scoped to the data mount.

        assert service.resolve_safe_path("per-host-logs/sw1.pem") is None  # Allowlist must apply.

    def test_directory_is_rejected(self, data_dir):
        """A directory must not resolve, because `send_file` cannot serve it."""
        (data_dir / "per-host-logs").mkdir()  # A directory used to pass the old existence check.

        service = DataBrowserService(str(data_dir))  # Service under test, scoped to the data mount.

        assert service.resolve_safe_path("per-host-logs") is None  # A directory must be refused.


class TestAllowedPathsStillWork:
    """Prove that the stricter guard keeps the supported files reachable."""

    def test_allowed_csv_resolves(self, data_dir):
        """A CSV file in the data directory must still resolve."""
        target = data_dir / "sites.csv"  # A normal export that an operator downloads every day.
        target.write_text("name\nsite-a\n")  # Content is irrelevant, only the path check matters.

        service = DataBrowserService(str(data_dir))  # Service under test, scoped to the data mount.

        resolved = service.resolve_safe_path("sites.csv")  # The guard must accept this file.

        assert resolved is not None  # A refusal here would break the download route.
        assert os.path.realpath(resolved) == os.path.realpath(str(target))  # Same real file.

    def test_allowed_nested_log_resolves(self, data_dir):
        """A nested log file with an allowed extension must still resolve."""
        nested = data_dir / "per-host-logs"  # The runtime writes each device log into this folder.
        nested.mkdir()  # Create the folder before the file, because `write_text` needs a parent.
        target = nested / "sw1.log"  # Allowed extension, so the guard must accept the file.
        target.write_text("show version\n")  # Content is irrelevant, only the path check matters.

        service = DataBrowserService(str(data_dir))  # Service under test, scoped to the data mount.

        assert service.resolve_safe_path("per-host-logs/sw1.log") is not None  # Must stay reachable.

    def test_parent_traversal_is_rejected(self, tmp_path, data_dir):
        """A path with a parent segment must not resolve."""
        (tmp_path / "outside.csv").write_text("secret\n")  # File one level above the data mount.

        service = DataBrowserService(str(data_dir))  # Service under test, scoped to the data mount.

        assert service.resolve_safe_path("../outside.csv") is None  # The classic escape must fail.

    def test_absolute_path_is_rejected(self, tmp_path, data_dir):
        """An absolute path must not resolve, because `os.path.join` drops the base."""
        outside = tmp_path / "outside.csv"  # Target that sits outside the data mount.
        outside.write_text("secret\n")  # Content is irrelevant, only the path check matters.

        service = DataBrowserService(str(data_dir))  # Service under test, scoped to the data mount.

        assert service.resolve_safe_path(str(outside)) is None  # An absolute path must be refused.

    def test_missing_file_is_rejected(self, data_dir):
        """A file that does not exist must not resolve."""
        service = DataBrowserService(str(data_dir))  # Service under test, scoped to the data mount.

        assert service.resolve_safe_path("absent.csv") is None  # A missing file must return None.
