"""Prove the session allowlist, database boundary, and secret protection."""

from __future__ import annotations

import os
import secrets
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from .harness import DatabaseSettingsFixture, SessionEnvironmentHarness


class TestSessionDatabaseEnvironment:
    """Check every required database name through the actual shell reader."""

    @pytest.mark.parametrize("name", tuple(DatabaseSettingsFixture.FIELDS))
    @pytest.mark.parametrize("case", ("empty", "plain", "space", "quotes", "dollar", "newline", "unicode", "large"))
    def test_each_name_survives_a_fresh_shell(self, tmp_path: Path, name: str, case: str) -> None:
        """A missing name or changed character prevents a configured database write."""
        values = DatabaseSettingsFixture.values()
        values[name] = DatabaseSettingsFixture.awkward_value(case)
        harness = SessionEnvironmentHarness(tmp_path)
        written = harness.write(values)
        sourced = harness.source("environment", values)
        assert written.returncode == 0
        assert sourced.returncode == 0, "The fresh-shell comparison checked 7 configuration names."
        assert sourced.stdout == "Checked 7 configuration names.\n"
        assert sourced.stderr == ""
        assert stat.S_IMODE(harness.target.stat().st_mode) == 0o400

    def test_actual_database_configuration_reads_all_seven_names(self, tmp_path: Path) -> None:
        """The actual builder must not lose a required setting in a fresh session."""
        values = DatabaseSettingsFixture.values()
        harness = SessionEnvironmentHarness(tmp_path)
        written = harness.write(values)
        configured = harness.source("configuration", values)
        assert written.returncode == 0
        assert configured.returncode == 0, "The actual database builder checked 7 settings."
        assert configured.stdout == "Checked 7 database settings.\n"
        assert configured.stderr == ""

    @pytest.mark.parametrize("name", DatabaseSettingsFixture.REQUIRED_NAMES)
    @pytest.mark.parametrize("case", ("unset", "empty", "whitespace"))
    def test_a_missing_required_credential_still_fails(self, tmp_path: Path, name: str, case: str) -> None:
        """Forwarding settings must not bypass required credential validation."""
        values = DatabaseSettingsFixture.values()
        if case == "unset":
            values.pop(name)
        else:
            values[name] = "" if case == "empty" else "   "
        harness = SessionEnvironmentHarness(tmp_path)
        written = harness.write(values)
        configured = harness.source("configuration", values)
        assert written.returncode == 0
        assert configured.returncode == 1
        assert f"Missing required environment variable: {name}" in configured.stderr
        exposed = any(value and value.strip() and value in configured.stderr for value in values.values())
        assert exposed is False

    @pytest.mark.parametrize("removal", ("unset", "empty"))
    def test_restart_replaces_values_and_removes_stale_names(self, tmp_path: Path, removal: str) -> None:
        """A restart must not retain any old database credential or setting."""
        harness = SessionEnvironmentHarness(tmp_path)
        earlier = DatabaseSettingsFixture.values()
        first = harness.write(earlier)
        earlier_inode = harness.target.stat().st_ino
        current = {name: secrets.token_hex(24) for name in earlier}
        second = harness.write(current)
        sourced = harness.source("environment", current)
        assert first.returncode == second.returncode == sourced.returncode == 0
        assert harness.target.stat().st_ino != earlier_inode
        removed = {} if removal == "unset" else dict.fromkeys(earlier, "")
        third = harness.write(removed)
        cleared = harness.source("environment", dict.fromkeys(earlier, ""))
        assert third.returncode == cleared.returncode == 0
        assert harness.target.read_text(encoding="utf-8") == ""
        assert stat.S_IMODE(harness.target.stat().st_mode) == 0o400
        assert harness.target.with_suffix(".env.new").exists() is False


class TestSessionFileProtection:
    """Keep the file and its reports limited to the explicit configuration."""

    def test_exact_allowlist_and_report_have_eighteen_names(self, tmp_path: Path) -> None:
        """Both the declaration and report must exclude unrelated configuration."""
        harness = SessionEnvironmentHarness(tmp_path)
        script = harness.WRITER.read_text(encoding="utf-8")
        declaration = script.split("SESSION_ENV_NAMES=(\n", 1)[1].split("\n)", 1)[0]
        declared = [line.strip().split()[0] for line in declaration.splitlines() if line.strip()]
        assert declared == list(DatabaseSettingsFixture.ALLOWED_NAMES)
        values = {name: secrets.token_hex(24) for name in declared}
        written = harness.write(values)
        expected = "[SSH] Carried 18 configuration name(s) into the session file: " + " ".join(declared) + "\n"
        assert written.returncode == 0
        assert written.stdout == expected
        assert written.stderr == ""
        exposed = any(value in written.stdout + written.stderr for value in values.values())
        assert exposed is False
        print(f"Checked {len(declared)} session configuration names.")

    def test_unlisted_secrets_never_reach_the_file_or_session(self, tmp_path: Path) -> None:
        """An allowlist must reject unrelated secrets and similarly named fields."""
        names = ("MISTHELPER_SSH_PASSWORD", "AWS_SECRET_ACCESS_KEY", "WEBHOOK_SECRET", "ARANGO_API_KEY", "REDIS_URL")
        unrelated = {name: secrets.token_hex(24) for name in names}
        values = DatabaseSettingsFixture.values() | unrelated
        harness = SessionEnvironmentHarness(tmp_path)
        written = harness.write(values)
        sourced = harness.source("environment", values)
        content = harness.target.read_text(encoding="utf-8")
        exposed = any(name in content or value in content for name, value in unrelated.items())
        reported = any(value in written.stdout + written.stderr for value in values.values())
        assert written.returncode == sourced.returncode == 0
        assert exposed is False
        assert reported is False
        assert sourced.stdout == "Checked 12 configuration names.\n"
        assert sourced.stderr == ""

    def test_valid_owner_alone_can_read_both_database_passwords(self, tmp_path: Path) -> None:
        """The additional passwords must retain the existing owner-only protection."""
        harness = SessionEnvironmentHarness(tmp_path)
        written = harness.write(DatabaseSettingsFixture.values())
        assert written.returncode == 0
        assert stat.S_IMODE(harness.target.stat().st_mode) == 0o400
        assert harness.target.stat().st_uid == os.getuid()
        assert harness.target.with_suffix(".env.new").exists() is False

    def test_shell_characters_remain_data_and_execute_no_command(self, tmp_path: Path) -> None:
        """A quoted database password must not execute its command-shaped text."""
        harness = SessionEnvironmentHarness(tmp_path)
        marker = tmp_path / "must-not-exist"
        values = DatabaseSettingsFixture.values()
        values["ARANGO_ROOT_PASSWORD"] = f"'\"$(touch {marker})`touch {marker}`$HOME\n"
        values["REDIS_PASSWORD"] = f"'; touch {marker}; #"
        written = harness.write(values)
        sourced = harness.source("environment", values)
        assert written.returncode == sourced.returncode == 0
        assert marker.exists() is False
        assert sourced.stdout == "Checked 7 configuration names.\n"
        assert sourced.stderr == ""

    @pytest.mark.parametrize("input_text", ("", "null", "{}", "{"), ids=("absent", "null", "empty", "malformed"))
    def test_probe_rejects_unreadable_or_empty_input(self, tmp_path: Path, input_text: str) -> None:
        """A guard that reads no names must fail instead of reporting success."""
        harness = SessionEnvironmentHarness(tmp_path)
        result = subprocess.run(
            [sys.executable, "-m", "tests.unit.container.session_database.harness", "environment", str(tmp_path)],
            input=input_text,
            env={"PATH": "/usr/bin:/bin", "PYTHONNOUSERSITE": "1"},
            cwd=harness.ROOT,
            capture_output=True,
            text=True,
            timeout=harness.timeout,
            check=False,
        )
        assert result.returncode == 1
        assert result.stdout == ""
        assert "ValueError" in result.stderr or "JSONDecodeError" in result.stderr
