"""Wave 9 P2 coverage tests for src.ssh.config.env_loader.

Targets the ``EnvSshConfigLoader`` branches that existing tests in
``tests/unit/test_ssh_runner.py::TestLoadSSHConfigFromEnv`` don't reach:
the manual-parser branch (when ``_DOTENV_AVAILABLE`` is patched to False),
error-guard handlers around dotenv/manual reads, the ``_MAX_MANUAL_LINES``
cap, the ``_unquote_value`` mismatched-quote passthrough, and the invalid
username warning branch. Also exercises ``_dispatch_known_key`` directly
for the unknown-key ignored path.
"""

from __future__ import annotations  # WHY: PEP 604 unions retained module-wide

import logging  # WHY: emit before/after action logs per project contract
from typing import Any  # WHY: annotate config dicts consistently with SUT

import pytest  # WHY: monkeypatch fixture for module-level flag flips

from src.ssh.config import env_loader as env_loader_module  # WHY: patch _DOTENV_AVAILABLE
from src.ssh.config.env_loader import EnvSshConfigLoader  # WHY: SUT under test


def _empty_config() -> dict[str, Any]:
    """Return the sentinel-only default config shape used by ``load``."""
    logging.info("Building empty config sentinel dict")  # WHY: pre-action trace
    result: dict[str, Any] = {  # WHY: mirror the shape emitted by _build_empty_config
        "hosts": [],
        "username": None,
        "password": None,
        "commands": [],
    }
    logging.debug("Empty config sentinel dict built: keys=%s", list(result.keys()))  # WHY: post-action trace
    return result  # WHY: hand back the sentinel dict for tests


class TestLoadPathGuards:
    """Cover the safe-path guard and size-limit guard in ``load``."""

    def test_empty_path_rejected_returns_empty_config(self) -> None:
        # WHY: empty string trips the "not env_file" branch in _is_safe_env_path
        config = EnvSshConfigLoader().load("")  # WHY: exercise the empty-path guard
        assert config == _empty_config()  # WHY: sentinel returned unchanged

    def test_backslash_path_rejected(self) -> None:
        # WHY: backslash in the path is rejected as unsafe
        config = EnvSshConfigLoader().load("subdir\\file.env")  # WHY: backslash guard fires
        assert config == _empty_config()  # WHY: sentinel returned unchanged

    def test_path_with_double_dot_rejected(self) -> None:
        # WHY: ".." anywhere in the path trips the traversal guard
        config = EnvSshConfigLoader().load("..hidden.env")  # WHY: any ".." substring triggers rejection
        assert config == _empty_config()  # WHY: sentinel returned unchanged

    def test_missing_file_returns_sentinel(self, tmp_path, monkeypatch) -> None:
        # WHY: os.path.exists(False) branch returns the sentinel early
        monkeypatch.chdir(tmp_path)  # WHY: relative path resolves under tmp
        config = EnvSshConfigLoader().load("nope.env")  # WHY: file does not exist
        assert config == _empty_config()  # WHY: early return before any parse

    def test_size_getsize_raises_oserror(self, tmp_path, monkeypatch, capsys) -> None:
        # WHY: OSError from getsize is caught by _is_within_size_limit and returns False
        monkeypatch.chdir(tmp_path)  # WHY: isolate cwd
        env_path = tmp_path / "test.env"  # WHY: create file so exists() passes
        env_path.write_text("SSH_HOST=1.1.1.1\n", encoding="utf-8")  # WHY: real content is irrelevant here

        def _boom(_path: str) -> int:  # WHY: monkeypatch getsize to raise OSError
            logging.info("Simulating OSError from os.path.getsize")  # WHY: pre-action trace
            raise OSError("stat failed")  # WHY: hit the except OSError branch

        import os as _os_mod  # WHY: patch os.path.getsize directly (env_loader imports os)

        monkeypatch.setattr(_os_mod.path, "getsize", _boom)  # WHY: force the OSError path
        config = EnvSshConfigLoader().load("test.env")  # WHY: exercise size guard exception branch
        assert config == _empty_config()  # WHY: unloadable file yields sentinel
        assert "Cannot access .env file" in capsys.readouterr().out  # WHY: user-facing warning surfaced

    def test_oversized_file_rejected_prints_warning(self, tmp_path, monkeypatch, capsys) -> None:
        # WHY: files above _MAX_ENV_BYTES trip the size cap branch
        monkeypatch.chdir(tmp_path)  # WHY: isolate cwd
        env_path = tmp_path / "big.env"  # WHY: create an oversized file
        env_path.write_bytes(b"X" * (env_loader_module._MAX_ENV_BYTES + 1))  # WHY: > cap by 1 byte
        config = EnvSshConfigLoader().load("big.env")  # WHY: exercise size cap
        assert config == _empty_config()  # WHY: oversized files return sentinel
        assert "too large" in capsys.readouterr().out  # WHY: user-facing warning surfaced


class TestManualParser:
    """Cover the manual-parse fallback that runs when ``_DOTENV_AVAILABLE`` is False."""

    @pytest.fixture(autouse=True)
    def _force_manual_parser(self, monkeypatch) -> None:
        # WHY: force the manual-parser path regardless of installed dotenv package
        monkeypatch.setattr(env_loader_module, "_DOTENV_AVAILABLE", False)  # WHY: gate flip

    def test_basic_key_value_parse(self, tmp_path, monkeypatch) -> None:
        # WHY: verify SSH_HOST/SSH_USER/SSH_PASSWORD/SSH_COMMANDS dispatch under manual parser
        monkeypatch.chdir(tmp_path)  # WHY: relative path resolves under tmp
        env_path = tmp_path / "test.env"  # WHY: fixture .env file
        env_path.write_text(  # WHY: canonical four-line .env
            "SSH_HOST=10.0.0.1,10.0.0.2\n"
            "SSH_USER=admin\n"
            "SSH_PASSWORD=secret\n"
            "SSH_COMMANDS=show version,show route\n",
            encoding="utf-8",
        )
        config = EnvSshConfigLoader().load("test.env")  # WHY: exercise manual parser
        assert "10.0.0.1" in config["hosts"]  # WHY: hosts parsed by HostListParser
        assert config["username"] == "admin"  # WHY: valid username accepted
        assert config["password"] == "secret"  # WHY: password stored verbatim
        assert len(config["commands"]) == 2  # WHY: commands parsed by CommandListParser

    def test_comment_and_blank_lines_ignored(self, tmp_path, monkeypatch) -> None:
        # WHY: lines starting with '#' and blank lines are skipped
        monkeypatch.chdir(tmp_path)  # WHY: isolate cwd
        env_path = tmp_path / "test.env"  # WHY: fixture .env file
        env_path.write_text(  # WHY: file with only comments and blanks (plus one real line)
            "# This is a comment\n\n# Another\nSSH_HOST=192.168.1.1\n",
            encoding="utf-8",
        )
        config = EnvSshConfigLoader().load("test.env")  # WHY: exercise skip branches
        assert "192.168.1.1" in config["hosts"]  # WHY: real key still applied
        assert config["username"] is None  # WHY: unspecified keys stay sentinel

    def test_malformed_line_without_equals_skipped(self, tmp_path, monkeypatch) -> None:
        # WHY: lines lacking '=' trip the "if '=' not in line" branch
        monkeypatch.chdir(tmp_path)  # WHY: isolate cwd
        env_path = tmp_path / "test.env"  # WHY: fixture file
        env_path.write_text(  # WHY: mixed valid+malformed content
            "this-line-has-no-equals\nSSH_USER=admin\n", encoding="utf-8"
        )
        config = EnvSshConfigLoader().load("test.env")  # WHY: exercise malformed-line skip
        assert config["username"] == "admin"  # WHY: valid line still applied

    def test_unknown_key_ignored(self, tmp_path, monkeypatch) -> None:
        # WHY: keys outside the SSH_* set trip the "unknown keys ignored" branch
        monkeypatch.chdir(tmp_path)  # WHY: isolate cwd
        env_path = tmp_path / "test.env"  # WHY: fixture file
        env_path.write_text("RANDOM_KEY=whatever\n", encoding="utf-8")  # WHY: no SSH_* keys at all
        config = EnvSshConfigLoader().load("test.env")  # WHY: exercise unknown-key path
        assert config == _empty_config()  # WHY: no known key applied

    def test_double_quoted_value_unquoted(self, tmp_path, monkeypatch) -> None:
        # WHY: verify _unquote_value strips a matched pair of double quotes
        monkeypatch.chdir(tmp_path)  # WHY: isolate cwd
        env_path = tmp_path / "test.env"  # WHY: fixture file
        env_path.write_text('SSH_USER="admin"\n', encoding="utf-8")  # WHY: double-quoted value
        config = EnvSshConfigLoader().load("test.env")  # WHY: exercise double-quote strip
        assert config["username"] == "admin"  # WHY: quotes removed

    def test_single_quoted_value_unquoted(self, tmp_path, monkeypatch) -> None:
        # WHY: verify _unquote_value strips a matched pair of single quotes
        monkeypatch.chdir(tmp_path)  # WHY: isolate cwd
        env_path = tmp_path / "test.env"  # WHY: fixture file
        env_path.write_text("SSH_PASSWORD='secret'\n", encoding="utf-8")  # WHY: single-quoted value
        config = EnvSshConfigLoader().load("test.env")  # WHY: exercise single-quote strip
        assert config["password"] == "secret"  # WHY: quotes removed

    def test_invalid_username_rejected_with_warning(self, tmp_path, monkeypatch, capsys) -> None:
        # WHY: invalid usernames hit the "print WARNING" branch of _set_username
        monkeypatch.chdir(tmp_path)  # WHY: isolate cwd
        env_path = tmp_path / "test.env"  # WHY: fixture file
        env_path.write_text("SSH_USER=; rm -rf /\n", encoding="utf-8")  # WHY: dangerous chars fail validation
        config = EnvSshConfigLoader().load("test.env")  # WHY: exercise invalid-username branch
        assert config["username"] is None  # WHY: invalid username left as sentinel
        assert "Invalid username format" in capsys.readouterr().out  # WHY: warning surfaced to user

    def test_line_cap_stops_at_limit(self, tmp_path, monkeypatch, capsys) -> None:
        # WHY: > _MAX_MANUAL_LINES trips the runaway-file guard
        monkeypatch.chdir(tmp_path)  # WHY: isolate cwd
        monkeypatch.setattr(env_loader_module, "_MAX_MANUAL_LINES", 3)  # WHY: lower cap so test stays fast
        env_path = tmp_path / "test.env"  # WHY: fixture file
        env_path.write_text(  # WHY: five lines forces the cap to fire on line 4
            "# c1\n# c2\n# c3\nSSH_HOST=1.1.1.1\nSSH_USER=admin\n", encoding="utf-8"
        )
        config = EnvSshConfigLoader().load("test.env")  # WHY: exercise line-cap branch
        assert "too many lines" in capsys.readouterr().out  # WHY: user-facing warning surfaced
        # WHY: SSH_USER is on line 5 (beyond the cap) so it must not be applied
        assert config["username"] is None

    def test_read_raises_unicode_decode_error(self, tmp_path, monkeypatch, capsys) -> None:
        # WHY: UnicodeDecodeError path in _populate_via_manual_parse is exercised via monkeypatched open
        monkeypatch.chdir(tmp_path)  # WHY: isolate cwd
        env_path = tmp_path / "test.env"  # WHY: real file so size/exists checks pass
        env_path.write_text("SSH_USER=admin\n", encoding="utf-8")  # WHY: content irrelevant

        def _bad_open(*_args: Any, **_kwargs: Any) -> Any:  # WHY: patched builtins.open raises decode error
            logging.info("Simulating UnicodeDecodeError from open")  # WHY: pre-action trace
            raise UnicodeDecodeError("utf-8", b"", 0, 1, "bad byte")  # WHY: hit that except branch

        monkeypatch.setattr(env_loader_module, "open", _bad_open, raising=False)  # WHY: shadow module open
        config = EnvSshConfigLoader().load("test.env")  # WHY: exercise decode-error branch
        assert config == _empty_config()  # WHY: parser gave up cleanly
        assert "encoding error" in capsys.readouterr().out  # WHY: warning surfaced

    def test_read_raises_oserror(self, tmp_path, monkeypatch, capsys) -> None:
        # WHY: OSError path (permission denied, disk gone) in _populate_via_manual_parse
        monkeypatch.chdir(tmp_path)  # WHY: isolate cwd
        env_path = tmp_path / "test.env"  # WHY: real file so guards pass
        env_path.write_text("SSH_USER=admin\n", encoding="utf-8")  # WHY: content irrelevant

        def _bad_open(*_args: Any, **_kwargs: Any) -> Any:  # WHY: patched open raises OSError
            logging.info("Simulating OSError from open")  # WHY: pre-action trace
            raise OSError("permission denied")  # WHY: hit that except branch

        monkeypatch.setattr(env_loader_module, "open", _bad_open, raising=False)  # WHY: shadow module open
        config = EnvSshConfigLoader().load("test.env")  # WHY: exercise OSError branch
        assert config == _empty_config()  # WHY: sentinel returned
        assert "Error reading" in capsys.readouterr().out  # WHY: warning surfaced

    def test_read_raises_generic_exception(self, tmp_path, monkeypatch, capsys) -> None:
        # WHY: broad except Exception guard in _populate_via_manual_parse
        monkeypatch.chdir(tmp_path)  # WHY: isolate cwd
        env_path = tmp_path / "test.env"  # WHY: real file so guards pass
        env_path.write_text("SSH_USER=admin\n", encoding="utf-8")  # WHY: content irrelevant

        def _bad_open(*_args: Any, **_kwargs: Any) -> Any:  # WHY: raise a non-OS, non-Unicode exception
            logging.info("Simulating generic Exception from open")  # WHY: pre-action trace
            raise RuntimeError("boom")  # WHY: hit the broad except branch

        monkeypatch.setattr(env_loader_module, "open", _bad_open, raising=False)  # WHY: shadow module open
        config = EnvSshConfigLoader().load("test.env")  # WHY: exercise broad-except branch
        assert config == _empty_config()  # WHY: sentinel returned
        assert "Unexpected error" in capsys.readouterr().out  # WHY: warning surfaced


class TestDotenvPath:
    """Cover the ``_populate_via_dotenv`` broad exception guard."""

    def test_dotenv_exception_prints_warning(self, tmp_path, monkeypatch, capsys) -> None:
        # WHY: force dotenv path AND make it raise to hit the except-Exception guard
        monkeypatch.chdir(tmp_path)  # WHY: isolate cwd
        env_path = tmp_path / "test.env"  # WHY: real file so exists / size checks pass
        env_path.write_text("SSH_USER=admin\n", encoding="utf-8")  # WHY: content irrelevant

        def _boom(*_args: Any, **_kwargs: Any) -> None:  # WHY: swap load_dotenv for one that raises
            logging.info("Simulating exception from load_dotenv")  # WHY: pre-action trace
            raise RuntimeError("dotenv exploded")  # WHY: hit the except branch

        monkeypatch.setattr(env_loader_module, "_DOTENV_AVAILABLE", True)  # WHY: gate on dotenv path
        monkeypatch.setattr(env_loader_module, "load_dotenv", _boom)  # WHY: patch parser to raise
        config = EnvSshConfigLoader().load("test.env")  # WHY: exercise dotenv exception branch
        assert config == _empty_config()  # WHY: parser gave up before setting anything
        assert "python-dotenv" in capsys.readouterr().out  # WHY: warning surfaced


class TestUnquoteValueDirect:
    """Cover the ``_unquote_value`` static method directly, including passthrough."""

    def test_double_quoted_value_stripped(self) -> None:
        # WHY: matched double quotes are stripped
        assert EnvSshConfigLoader._unquote_value('"admin"') == "admin"

    def test_single_quoted_value_stripped(self) -> None:
        # WHY: matched single quotes are stripped
        assert EnvSshConfigLoader._unquote_value("'admin'") == "admin"

    def test_unquoted_value_passthrough(self) -> None:
        # WHY: values without surrounding quotes are returned unchanged
        assert EnvSshConfigLoader._unquote_value("admin") == "admin"

    def test_mismatched_quotes_passthrough(self) -> None:
        # WHY: only matched pairs are stripped; mixed pair returns unchanged
        assert EnvSshConfigLoader._unquote_value("\"admin'") == "\"admin'"

    def test_empty_string_passthrough(self) -> None:
        # WHY: startswith('"') is False for empty string, so no strip
        assert EnvSshConfigLoader._unquote_value("") == ""


class TestDispatchKnownKeyDirect:
    """Cover the ``_dispatch_known_key`` router directly."""

    def test_ssh_host_dispatched_to_host_parser(self) -> None:
        # WHY: SSH_HOST branch routes into HostListParser.parse
        loader = EnvSshConfigLoader()  # WHY: real loader; parser is delegated but safe
        config = _empty_config()  # WHY: fresh sentinel dict
        loader._dispatch_known_key(config, "SSH_HOST", "10.0.0.1")  # WHY: exercise SSH_HOST branch
        assert "10.0.0.1" in config["hosts"]  # WHY: parser accepted the value

    def test_ssh_password_dispatched_verbatim(self) -> None:
        # WHY: SSH_PASSWORD branch stores value as-is
        loader = EnvSshConfigLoader()  # WHY: real loader
        config = _empty_config()  # WHY: fresh sentinel dict
        loader._dispatch_known_key(config, "SSH_PASSWORD", "hunter2")  # WHY: exercise SSH_PASSWORD branch
        assert config["password"] == "hunter2"  # WHY: stored verbatim

    def test_ssh_commands_dispatched_to_command_parser(self) -> None:
        # WHY: SSH_COMMANDS branch routes into CommandListParser.parse
        loader = EnvSshConfigLoader()  # WHY: real loader
        config = _empty_config()  # WHY: fresh sentinel dict
        loader._dispatch_known_key(config, "SSH_COMMANDS", "show version")  # WHY: exercise branch
        assert len(config["commands"]) >= 1  # WHY: parser accepted the command

    def test_unknown_key_leaves_config_unchanged(self) -> None:
        # WHY: keys not in the SSH_* set fall through the elif chain silently
        loader = EnvSshConfigLoader()  # WHY: real loader
        config = _empty_config()  # WHY: fresh sentinel dict
        loader._dispatch_known_key(config, "SOMETHING_ELSE", "value")  # WHY: exercise fallthrough
        assert config == _empty_config()  # WHY: no key applied

    def test_ssh_user_valid_accepted(self) -> None:
        # WHY: SSH_USER branch routes into _set_username; valid user is stored
        loader = EnvSshConfigLoader()  # WHY: real loader
        config = _empty_config()  # WHY: fresh sentinel dict
        loader._dispatch_known_key(config, "SSH_USER", "admin")  # WHY: exercise SSH_USER accept branch
        assert config["username"] == "admin"  # WHY: valid username accepted

    def test_set_username_empty_string_ignored(self) -> None:
        # WHY: empty username hits the "not username" early return
        loader = EnvSshConfigLoader()  # WHY: real loader
        config = _empty_config()  # WHY: fresh sentinel dict
        loader._dispatch_known_key(config, "SSH_USER", "")  # WHY: exercise empty-username branch
        assert config["username"] is None  # WHY: sentinel unchanged


class TestDotenvUnavailableStub:
    """Verify the ``load_dotenv`` no-op stub exists at import time."""

    def test_stub_signature_returns_none(self) -> None:
        # WHY: when dotenv isn't installed, the module defines a stub that must accept *args/**kwargs
        # We can't easily unimport dotenv in-process, but we can call the module-level load_dotenv
        # symbol and prove it is callable and returns bool (real) or None (stub).
        load_fn = getattr(
            env_loader_module, "load_dotenv", None
        )  # WHY: attr-access via getattr avoids strict export check
        assert load_fn is not None  # WHY: symbol must exist post-import (stub or real)
        result = load_fn("ignored.env")  # WHY: exercise stub or real dotenv
        # WHY: real dotenv returns bool; stub returns None. Both are acceptable — key is no exception.
        assert result is None or isinstance(result, bool)
