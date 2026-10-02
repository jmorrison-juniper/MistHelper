"""Prove source decisions and real local selection without production startup."""

from __future__ import annotations  # Keep type hints passive during pytest collection.

import argparse  # Type the result from the actual parser.
import csv  # Inspect the real CSV output.
import importlib  # Import runtime owners only after isolation.
import logging  # Record test actions without credentials.
import os  # Control environment inputs independently of CLI flags.
import socket  # Refuse unexpected resource access.
import sqlite3  # Inspect real SQLite records and business keys.
from collections.abc import Iterator  # Type the isolated fixture lifetime.
from pathlib import Path  # Confine every mutation and export to tmp_path.
from types import ModuleType  # Type the passively imported CLI module.
from typing import Any, cast  # Type dynamic Flask and CLI return values.
from unittest.mock import Mock, patch  # Replace telemetry and forbidden external actions only.

import pytest  # Parameterize valid and invalid decisions without hiding failures.
from flask.testing import FlaskClient  # Type the in-process client without starting a server.

from .contract import ContractCopies, SourceContract  # Keep the live success assertion unchanged.


class TestSourceContract:
    """Require every live source to satisfy the option-2 contract."""

    @pytest.fixture
    def copies(self, tmp_path: Path) -> ContractCopies:
        """Use repaired copies so negative decisions can pass before live repair."""
        with patch("subprocess.run", side_effect=AssertionError("contract copies must not require Git history")):
            copies = ContractCopies.create(tmp_path)
            original = ContractCopies.create(tmp_path / "immutable-base", original=True)
        report = SourceContract(original.root).evaluate()  # Keep the same source decisions against exact base bytes.
        assert (report.expected, report.checked, report.rejected) == (
            6,
            6,
            4,
        ), report.render()  # Retain the defect evidence.
        paths = tuple(
            original.root / relative for relative in SourceContract.PATHS[:4]
        )  # Require all original failures.
        assert tuple(item[0] for item in report.failures) == paths  # No unrelated rejection may replace the defect.
        return copies  # Every mutation case receives repaired temporary inputs.

    def test_live_sources_require_option_two(self) -> None:
        """The original live inputs must fail this success assertion."""
        report = SourceContract(SourceContract.REPOSITORY).evaluate()  # Inspect all six actual input paths.
        print(report.render())  # Retain actual counts and paths in the command evidence.
        assert (report.expected, report.checked, report.rejected) == (
            6,
            6,
            0,
        ), report.render()  # Never hide the defect.

    @pytest.mark.parametrize(
        ("index", "addition", "rejected"),
        [
            (0, "export OUTPUT_FORMAT=sqlite\n", 1),  # Restore the exact original session setting.
            (1, "ENV OUTPUT_FORMAT=sqlite\n", 1),  # Restore the exact original Docker setting.
            (2, "ENV OUTPUT_FORMAT=sqlite\n", 1),  # Restore the exact original Podman setting.
            (0, "export OUTPUT_FORMAT=polyglot\n", 1),  # A different value is still unused.
            (1, "ENV OUTPUT_FORMAT=polyglot\n", 1),  # Reject an unused Docker alternative.
            (2, "ENV OUTPUT_FORMAT=polyglot\n", 1),  # Reject an unused Podman alternative.
            (0, "OUTPUT_FORMAT=sqlite\n", 1),  # A plain assignment also changes the inherited value.
            (0, "\texport OUTPUT_FORMAT='polyglot'\n", 1),  # Keep quoting and leading whitespace active.
            (0, "declare -x OUTPUT_FORMAT=sqlite\n", 1),  # Include exported declarations with flags.
            (0, "readonly OUTPUT_FORMAT=sqlite\n", 1),  # Include immutable variable declarations.
            (0, "typeset -x OUTPUT_FORMAT=polyglot\n", 1),  # Include another shell declaration form.
            (0, "FIRST=value OUTPUT_FORMAT=polyglot command\n", 1),  # Include command-prefix assignments.
            (0, "true; export OUTPUT_FORMAT=sqlite\n", 1),  # Include declarations after a command.
            (0, "export OUTPUT_FORMAT=sqlite; true\n", 1),  # Include declarations before a command separator.
            (0, "env -i OUTPUT_FORMAT=polyglot command\n", 1),  # Include explicit child-environment assignments.
            (0, "if true; then OUTPUT_FORMAT=sqlite; fi\n", 1),  # Include settings in a conditional scope.
            (0, "export \\\n OUTPUT_FORMAT=polyglot\n", 1),  # Include continued export commands.
            (0, "# export OUTPUT_FORMAT=sqlite\n", 0),  # Comments alone must not configure a session.
            (0, "# supported SQLite; export OUTPUT_FORMAT=sqlite\n", 0),  # Keep the complete comment inactive.
            (0, "echo 'OUTPUT_FORMAT=sqlite'\n", 0),  # Ordinary arguments must not become assignments.
            (0, "echo 'supported SQLite; OUTPUT_FORMAT=sqlite'\n", 0),  # Preserve quoted command separators.
            (0, "export SAFE=value # OUTPUT_FORMAT=sqlite\n", 0),  # Ignore trailing comments.
            (1, "ENV OUTPUT_FORMAT sqlite\n", 1),  # Include legacy image syntax.
            (2, "ENV OUTPUT_FORMAT polyglot\n", 1),  # Include the legacy form for both tools.
            (1, 'ENV SAFE=value "OUTPUT_FORMAT"="sqlite"\n', 1),  # Include quoted multi-setting syntax.
            (2, "ENV SAFE=value OUTPUT_FORMAT=polyglot\n", 1),  # Include later operands in one ENV instruction.
            (1, "env OUTPUT_FORMAT=polyglot\n", 1),  # Docker instructions are not case-sensitive.
            (2, "ENV \\\n OUTPUT_FORMAT=sqlite\n", 1),  # Include continued image instructions.
            (1, "# ENV OUTPUT_FORMAT=sqlite\n", 0),  # Ignore Docker comment-only declarations.
            (2, "  # ENV OUTPUT_FORMAT=polyglot\n", 0),  # Ignore indented Podman comments.
            (1, "ENV SAFE=value\n", 0),  # A useful unrelated image setting remains valid.
            (3, ContractCopies.FALSE_INSTRUCTION, 1),  # Reject the original false alternative.
            (3, "Use SQLite output.", 1),  # A missing selection flag does not repair the page.
            (3, "Set `OUTPUT_FORMAT=sqlite` to select SQLite output.", 1),  # Reject environment-only selection.
            (3, "Use `--output-format csv` to select SQLite output.", 1),  # Reject the wrong explicit format.
            (0, "export OUTPUT_FORMAT='sqlite\n", 1),  # Invalid settings cannot pass as harmless text.
            (1, "ENV OUTPUT_FORMAT='sqlite\n", 1),  # Invalid image settings must fail closed.
        ],
    )
    def test_settings_and_instruction_decisions(
        self, copies: ContractCopies, index: int, addition: str, rejected: int
    ) -> None:
        """Name each altered source and retain six successful reads."""
        path = copies.root / SourceContract.PATHS[index]  # Identify one required mutation target.
        logging.info("Read temporary mutation source %s", path)  # Mark the owned read before transformation.
        text = path.read_text(encoding="utf-8")  # Keep all other inputs valid.
        changed = text.replace(ContractCopies.CORRECT_INSTRUCTION, addition) if index == 3 else text + addition
        logging.debug("Prepared temporary mutation with %s characters", len(changed))  # Report no source contents.
        copies.write(index, changed)  # Write only the selected temporary input.
        report = SourceContract(copies.root).evaluate()  # Exercise the real counted guard decision.
        print(report.render())  # Keep rejected paths and counts available as proof.
        assert (report.expected, report.checked, report.rejected) == (6, 6, rejected), report.render()
        assert tuple(item[0] for item in report.failures) == ((path,) if rejected else ())  # Reject only this target.
        with pytest.raises(ValueError, match="differs from its measured bytes"):
            ContractCopies.original(index, text + "\n")
        with pytest.raises(ValueError, match="differs from its measured bytes"):
            ContractCopies.original(index, text.replace("\n", "\r\n"))

    @pytest.mark.parametrize("index", range(6))
    @pytest.mark.parametrize("mode", ["missing", "directory", "permission", "encoding"])
    def test_unreadable_inputs(
        self, copies: ContractCopies, index: int, mode: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Every unreadable source must report six expected and five checked."""
        path = copies.root / SourceContract.PATHS[index]  # Keep the exact required path in the report.
        logging.info("Make owned input unreadable at %s", path)  # Mark the negative filesystem action.
        path.unlink()  # Remove only a file produced by this test.
        if mode == "directory":  # A directory gives a reliable read failure on every account.
            path.mkdir()  # Do not depend on permission bits.
        elif mode == "permission":  # Exercise PermissionError independently of the account's privileges.
            reader = Path.read_bytes

            def denied_reader(candidate: Path) -> bytes:
                if candidate == path:  # Fail only the required input selected by this case.
                    raise PermissionError(13, "synthetic read refusal", str(candidate))  # Retain the rejected path.
                return reader(candidate)

            monkeypatch.setattr(Path, "read_bytes", denied_reader)
        elif mode == "encoding":  # A corrupt text input is also unreadable.
            path.write_bytes(b"\xff")  # Keep the corrupt bytes inside tmp_path.
        logging.debug("Unreadable input mode is %s", mode)  # Do not claim a successful read.
        report = SourceContract(copies.root).evaluate()  # Read all remaining required sources.
        print(report.render())  # Retain actual counts and the failed path.
        assert (report.expected, report.checked, report.rejected) == (6, 5, 1), report.render()  # No empty substitute.
        assert tuple(item[0] for item in report.failures) == (path,)  # Name the exact unreadable input.

    @pytest.mark.parametrize(
        ("index", "before", "after"),
        [
            (3, "## SQLite\n", "## Local database\n"),  # Require the actual SQLite section.
            (4, "OUTPUT_FORMAT=polyglot", "OUTPUT_FORMAT=sqlite"),  # Preserve the active compose backend.
            (4, "OUTPUT_FORMAT=polyglot", "IGNORED_OUTPUT_FORMAT=polyglot"),  # A missing declaration must fail.
            (5, '"OUTPUT_FORMAT", "sqlite"', '"OUTPUT_FORMAT", "csv"'),  # Preserve the readiness default.
            (5, ".strip().lower()", ".strip()"),  # Preserve case normalization.
            (5, ".strip().lower()", ".lower()"),  # Preserve whitespace normalization.
            (5, '{"sqlite", "standalone"}', '{"sqlite"}'),  # Preserve the standalone SQLite check.
            (5, 'checks["redis"] = _check_redis()', 'checks["redis"] = _check_arangodb()'),  # Preserve both backends.
            (5, "503 if failed else 200", "200 if failed else 200"),  # Preserve failure status.
            (5, '"failed_checks": failed', '"failed_checks": []'),  # Preserve exact failure names.
            (5, '"not ready" if failed else "ready"', '"ready"'),  # Preserve the failure verdict.
            (4, "\n", "\r\n"),
            (5, "\n", "\r\n"),
        ],
    )
    def test_protected_reader_decisions(self, copies: ContractCopies, index: int, before: str, after: str) -> None:
        """Active compose and readiness mutations must fail the full-source guard."""
        path = copies.root / SourceContract.PATHS[index]  # Alter only one owned protected copy.
        logging.info("Read protected mutation source %s", path)  # Mark the file read before mutation.
        text = path.read_text(encoding="utf-8")  # Read the complete active reader source.
        assert before in text  # A stale mutation must not become an unchanged passing case.
        changed = text.replace(before, after)  # Inject one readiness or compose defect.
        logging.debug("Prepared protected mutation for %s", path)  # Retain the decision path.
        copies.write(index, changed)  # Do not touch the real reader.
        report = SourceContract(copies.root).evaluate()  # Read all six required inputs.
        print(report.render())  # Keep actual guard counts visible.
        assert (report.expected, report.checked, report.rejected) == (6, 6, 1), report.render()
        assert tuple(item[0] for item in report.failures) == (path,)  # Name that input rather than a silent default.
        with pytest.raises(ValueError, match="differs from its measured bytes"):
            ContractCopies.original(index, text + "\n")
        with pytest.raises(ValueError, match="differs from its measured bytes"):
            ContractCopies.original(index, text.replace("\n", "\r\n"))


class ExportIsolation:
    """Isolate actual parser and exporter state without replacing local writes."""

    def __init__(self, root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Bind the real CLI module only after the fixture clears the environment."""
        logging.info("Isolate local export state in %s", root)  # Mark runtime ownership before importing.
        self.root = root  # Own all database, CSV, home, and temporary paths.
        self.monkeypatch = monkeypatch  # Restore every patched runtime value after the case.
        monkeypatch.chdir(root)  # Bare CSV destinations must resolve under this test.
        self.module: ModuleType = importlib.import_module("MistHelper")  # Use the actual passive CLI module.
        assert (
            Path(self.module.__file__).resolve() == SourceContract.REPOSITORY / "MistHelper.py"
        )  # Reject stale copies.
        self.forbidden: list[Mock] = []  # Detect attempts even if production code catches an exception.
        self.runtime()  # Replace state owners, not selection or writer behavior.
        self.block_external()  # Fail unexpected authentication, probes, or remote writes.
        logging.debug("Isolated actual CLI module at %s", self.module.__file__)  # Report source ownership.

    def runtime(self) -> None:
        """Replace context, resolver binding, telemetry, settings, and exporter caches."""
        from src.config import runtime_settings  # Load settings after environment isolation.
        from src.config.source_dependency_resolver import SourceDependencyResolver  # Restore the bound state.
        from src.export.data_exporter import DataExporter  # Keep the real export implementation.
        from src.refactors.main_entrypoint import AppContext, MainEntrypoint  # Create one independent state owner.

        logging.info("Bind isolated parser and export state")  # Mark the runtime state transfer.
        self.monkeypatch.setattr(MainEntrypoint, "context", AppContext())  # Never change a previous main context.
        self.monkeypatch.setattr(SourceDependencyResolver, "_root_module", self.module)  # Avoid stale resolver hosts.
        database = str(self.root / "data" / "mist_data.db")  # Keep every SQLite path under tmp_path.
        self.monkeypatch.setattr(runtime_settings, "DATABASE_PATH", database)  # Isolate source-owned settings.
        self.monkeypatch.setattr(self.module, "DATABASE_PATH", database)  # Isolate the legacy host view.
        self.monkeypatch.setattr(self.module, "TelemetryEmitter", Mock(return_value=object()))  # Avoid files.
        caches = {  # Start optional writes from an empty state and restore the prior caches later.
            "_router": None,  # Do not reuse a router from another test.
            "_router_initialized": False,  # Prove standalone avoids router initialization.
            "_last_snapshot_times": {},  # Avoid snapshot state shared with other exports.
            "_standalone_logged": False,  # Keep one-shot diagnostics case-local.
            "_standalone_probe": None,  # A forced standalone case must need no cached probe.
        }
        for name, value in caches.items():  # Restore these values through the fixture's monkeypatch owner.
            self.monkeypatch.setattr(DataExporter, name, value)  # Leave no exporter cache behind.
        logging.debug("Bound %s isolated exporter cache fields", len(caches))  # Report the state scope.

    def block_external(self) -> None:
        """Keep attempts observable even when a caller catches their failure."""
        import requests  # Refuse Mist HTTP calls at their transport boundary.

        from src.export import data_exporter  # Block the optional probe and router construction.

        logging.info("Install forbidden external-action guards")  # Mark the safety controls before execution.
        targets = [  # Keep actual local CSV and SQLite writers outside this list.
            (socket, "create_connection"),  # Refuse remote socket probes.
            (socket, "getaddrinfo"),  # Refuse DNS lookups.
            (socket.socket, "connect"),  # Refuse direct socket connections too.
            (socket.socket, "connect_ex"),  # Refuse error-code socket connection paths.
            (requests.sessions.Session, "request"),  # Refuse HTTP authentication or data calls.
            (data_exporter, "polyglot_hosts_unreachable"),  # Refuse optional host probes.
            (data_exporter, "DatabaseRouter"),  # Refuse router construction.
            (data_exporter.DataExporter, "_build_polyglot_router"),  # Refuse deferred construction too.
            (self.module, "_establish_mist_session"),  # Refuse full authentication startup.
            (self.module.MistSessionInitializer, "initialize"),  # Refuse token authentication.
            (self.module.MistSessionInteractiveInitializer, "initialize"),  # Refuse interactive authentication.
        ]
        for owner, name in targets:  # Make every unexpected action fail and record its attempt.
            guard = Mock(side_effect=AssertionError("unexpected external action: " + name))  # Use no real credentials.
            self.monkeypatch.setattr(owner, name, guard)  # Keep the blocker case-local.
            self.forbidden.append(guard)  # Do not lose evidence when production catches an exception.
        logging.debug("Installed %s forbidden-action guards", len(self.forbidden))  # State the complete safety scope.

    def configure(self, flag: str | None) -> argparse.Namespace:
        """Use the real parser and runtime selection with no bootstrap call."""
        logging.info("Parse and configure the explicit output selection %s", flag)  # Log a format, never a credential.
        arguments = [] if flag is None else ["--output-format", flag]  # An unset flag must use the real parser default.
        parsed = cast(
            argparse.Namespace, self.module._build_argument_parser().parse_args(arguments)
        )  # Keep choices real.
        self.module._configure_runtime_options(parsed)  # Apply the real runtime selection to the isolated AppContext.
        self.module.TelemetryEmitter.assert_called_once_with(
            os.path.join("data", "test_events.jsonl")
        )  # No telemetry file.
        logging.debug("Actual parsed output format is %s", parsed.output_format)  # Report the parser decision.
        return parsed  # Let the test compare parser and runtime decisions.

    def verify(self) -> None:
        """Require zero forbidden calls and zero optional router state."""
        from src.export.data_exporter import DataExporter  # Read the actual shared cache owner.

        for guard in self.forbidden:  # Check every external boundary, including caught exceptions.
            guard.assert_not_called()  # Standalone local writes must reach no remote resource.
        assert DataExporter._router is None  # No prior or new router may survive the case.
        assert DataExporter._router_initialized is False  # The standalone decision must precede lazy initialization.
        assert DataExporter._standalone_probe is None  # No host probe may select this local mode.


class ExportEvidence:
    """Inspect both actual records and the existing local business-key treatment."""

    ROWS = [  # Use two flat listOrgSites records without changing schema or strategy code.
        {"id": "site-3314-one", "org_id": "org-3314", "name": "First synthetic site", "country_code": "US"},
        {"id": "site-3314-two", "org_id": "org-3314", "name": "Second synthetic site", "country_code": "CA"},
    ]

    @classmethod
    def inspect(cls, root: Path, selected: str) -> None:
        """Require the selected writer only and both unmodified records."""
        csv_path = root / "data" / "listOrgSites.csv"  # Use the real bare-destination CSV path.
        database = root / "data" / "mist_data.db"  # Use the isolated real SQLite path.
        if selected == "csv":  # Default and explicit CSV must never create SQLite.
            assert csv_path.is_file()  # Prove the real local writer ran.
            assert not database.exists()  # No SQLite side output may appear in standalone mode.
            logging.info("Read real CSV output %s", csv_path)  # Mark the local evidence read.
            with csv_path.open(encoding="utf-8", newline="") as handle:  # Use the actual emitted records.
                rows = list(csv.DictReader(handle))  # Preserve business keys and values.
            logging.debug("Read %s CSV records", len(rows))  # Report the actual stored count.
            assert rows == cls.ROWS  # Check both complete records, not just file presence.
        else:  # Explicit SQLite must never create a CSV side output.
            assert database.is_file()  # Prove a real SQLite database exists.
            assert not csv_path.exists()  # Standalone SQLite must not select the CSV writer.
            cls.inspect_sqlite(database)  # Check real rows and the natural primary key.

    @classmethod
    def inspect_sqlite(cls, database: Path) -> None:
        """Read the real table without creating or modifying a database."""
        logging.info("Read real SQLite output %s", database)  # Mark the database evidence operation.
        connection = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)  # Never create a missing result.
        try:  # Close the owned connection even when an assertion fails.
            connection.row_factory = sqlite3.Row  # Retain explicit business field names.
            rows = connection.execute("SELECT id, org_id, name, country_code FROM listOrgSites ORDER BY id").fetchall()
            schema = connection.execute("PRAGMA table_info(listOrgSites)").fetchall()  # Inspect existing key treatment.
            stored = [dict(row) for row in rows]  # Compare exact flat record values.
            primary_keys = [row["name"] for row in schema if row["pk"]]  # Inspect the actual SQLite primary key.
            columns = {row["name"] for row in schema}  # Reject artificial key additions.
            logging.debug("Read %s SQLite records and %s columns", len(stored), len(columns))  # Report measured counts.
            assert stored == cls.ROWS  # Preserve both original business records.
            assert primary_keys == ["id"]  # listOrgSites already uses its natural business key.
            assert {"api_id", "misthelper_internal_id"}.isdisjoint(columns)  # Do not add surrogate identity.
        finally:  # Release the local read-only resource.
            connection.close()  # Leave no open database handle.


class TestFormatSelection:
    """Exercise all 15 environment/flag combinations with actual local writes."""

    @pytest.fixture
    def isolated(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[ExportIsolation]:
        """Clear credentials and environment settings before passive runtime imports."""
        clean = {  # Do not load an environment file or reuse host credentials.
            "PATH": os.defpath,  # Imports need no external application startup.
            "HOME": str(tmp_path / "home"),  # Keep optional home readers below tmp_path.
            "TMPDIR": str(tmp_path),  # Keep optional temporary writes below tmp_path.
            "MISTHELPER_STANDALONE": "true",  # Use the real optional-write decision.
            "PYTHONDONTWRITEBYTECODE": "1",  # Leave no import artifacts in the checkout.
        }
        logging.info("Set the isolated local-export environment")  # Mark the environment transfer.
        with patch.dict(os.environ, clean, clear=True):  # Restore the complete prior environment after the case.
            harness = ExportIsolation(tmp_path, monkeypatch)  # Bind real owners only after clearing the environment.
            logging.debug("Isolated export environment has %s names", len(clean))  # Report names, never values.
            yield harness  # Run actual selection and local writes inside this boundary.
            harness.verify()  # Detect forbidden actions even when the exporter catches them.

    @pytest.mark.parametrize("environment", [None, "csv", "sqlite", "polyglot", "synthetic-unsupported"])
    @pytest.mark.parametrize("flag", [None, "csv", "sqlite"])
    def test_real_selection_and_writes(
        self, isolated: ExportIsolation, environment: str | None, flag: str | None
    ) -> None:
        """Environment values must not change the default or an explicit CLI choice."""
        from src.export.data_exporter import DataExporter  # Use the actual public local-write entry point.

        logging.info("Set the output environment case %s", environment)  # Log only the non-secret format value.
        if environment is not None:  # The fixture already covers the truly unset case.
            isolated.monkeypatch.setenv("OUTPUT_FORMAT", environment)  # Supply exactly the requested environment input.
        logging.debug("Output environment case is set=%s", environment is not None)  # Distinguish unset from empty.
        parsed = isolated.configure(flag)  # Exercise the actual parser and runtime selection.
        expected = "csv" if flag is None else flag  # Use the specification's expected result.
        assert parsed.output_format == expected  # Check the actual parser decision.
        assert isolated.module.MainEntrypoint.context.output_format == expected  # Check the actual runtime owner.
        assert isolated.module.OUTPUT_FORMAT == expected  # Check the compatibility view used by exporters.
        logging.info("Write %s real local records using %s", len(ExportEvidence.ROWS), expected)  # Mark the real write.
        result = DataExporter.write_with_format_selection(ExportEvidence.ROWS, "listOrgSites", "listOrgSites")
        logging.debug("Actual local exporter returned %s", result)  # Do not replace the writer or its outcome.
        assert result is True  # A failed real write must remain a failed test.
        ExportEvidence.inspect(isolated.root, expected)  # Inspect both records and exclusive local selection.

    def test_polyglot_is_not_a_cli_choice(self, isolated: ExportIsolation) -> None:
        """A readiness setting must not become a supported export flag."""
        isolated.monkeypatch.setenv("OUTPUT_FORMAT", "polyglot")  # Keep the environment alternative in play.
        parser = isolated.module._build_argument_parser()  # Inspect the actual parser, not duplicate logic.
        choices = next(action.choices for action in parser._actions if action.dest == "output_format")
        assert list(choices) == ["csv", "sqlite"]  # Preserve every supported output choice.
        logging.info("Parse the unsupported explicit polyglot selection")  # Mark the required refusal action.
        with pytest.raises(SystemExit) as refusal:  # argparse must retain its existing error outcome.
            parser.parse_args(["--output-format", "polyglot"])  # No startup or export follows this parse.
        logging.debug("Unsupported selection returned %s", refusal.value.code)  # Retain the exact refusal code.
        assert refusal.value.code == 2  # A parser error must not become successful startup.
        assert not (isolated.root / "data").exists()  # No local exporter or telemetry file may run.


class TestReadiness:
    """Keep the actual route, reader, selected checks, and response behavior."""

    CASES = (  # These six specification cases select 17 total resource checks.
        (None, "sqlite", ("data_directory_writable", "mist_api_session", "sqlite_database")),
        ("sqlite", "sqlite", ("data_directory_writable", "mist_api_session", "sqlite_database")),
        ("standalone", "standalone", ("data_directory_writable", "mist_api_session", "sqlite_database")),
        (" PolyGloT ", "polyglot", ("data_directory_writable", "mist_api_session", "arangodb", "redis")),
        ("csv", "csv", ("data_directory_writable", "mist_api_session")),
        ("synthetic-unsupported", "synthetic-unsupported", ("data_directory_writable", "mist_api_session")),
    )
    METHODS = {  # Replace all resource checks, including checks not selected by this case.
        "data_directory_writable": "_check_data_dir_writable",
        "mist_api_session": "_check_mist_api_session",
        "sqlite_database": "_check_sqlite_database",
        "arangodb": "_check_arangodb",
        "redis": "_check_redis",
    }

    @pytest.fixture
    def readiness(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: tuple[str | None, str, tuple[str, ...], str | None]
    ) -> tuple[FlaskClient, Mock, dict[str, Mock]]:
        """Build a minimal Flask client with every resource reader replaced."""
        from flask import Flask  # A minimal app avoids production application startup.

        from web_portal.routes import dashboard  # Keep the actual reader and route.

        logging.info("Prepare isolated readiness case %s", case[1])  # Mark all reader replacements before execution.
        if case[0] is None:  # Unset readiness must retain its own SQLite default.
            monkeypatch.delenv("OUTPUT_FORMAT", raising=False)  # Remove only the format input for this test.
        else:  # Include whitespace and case normalization in the actual reader.
            monkeypatch.setenv("OUTPUT_FORMAT", case[0])  # Pass the exact specified value.
        calls = Mock()  # Track the exact active-check order.
        checks: dict[str, Mock] = {}  # Retain every check for zero-call assertions.
        for name, method in self.METHODS.items():  # Replace all five resource checks before the route runs.
            check = Mock(return_value={"ok": name != case[3], "detail": "synthetic check"})  # Fail one check.
            calls.attach_mock(check, name)  # Record the actual selection order.
            monkeypatch.setattr(dashboard, method, check)  # Never run a real resource reader.
            checks[name] = check  # Keep inactive checks available for exact assertions.
        app = Flask(__name__)  # Register only the existing dashboard blueprint.
        app.config.update(TESTING=True, DATA_DIR=str(tmp_path / "data"), APISESSION=None)  # Use owned paths.
        app.register_blueprint(dashboard.dashboard_bp)  # Preserve actual route and response construction.
        logging.debug("Replaced %s readiness resource checks", len(checks))  # Report the complete isolated scope.
        return app.test_client(), calls, checks  # Open no listening port.

    @pytest.mark.parametrize(
        "case",
        [
            (environment, normalized, selected, failed)  # Give each healthy or single-failure outcome one test case.
            for environment, normalized, selected in CASES
            for failed in (None, *selected)
        ],
    )
    def test_actual_readiness_outcomes(
        self,
        readiness: tuple[FlaskClient, Mock, dict[str, Mock]],
        case: tuple[str | None, str, tuple[str, ...], str | None],
    ) -> None:
        """Six healthy cases and all 17 selected-check failures must keep exact responses."""
        client, calls, checks = readiness  # Use the isolated client with real route behavior.
        logging.info("Request the actual readiness route")  # Mark the in-process API call before execution.
        response = client.get("/ready")  # Run the actual Flask reader and route without a server.
        payload = cast(dict[str, Any], response.get_json())  # Inspect the actual response body.
        logging.debug("Readiness returned %s with %s checks", response.status_code, len(payload["checks"]))
        assert response.status_code == (503 if case[3] else 200)  # Preserve the monitor-facing status.
        assert payload["status"] == ("not ready" if case[3] else "ready")  # Preserve the exact verdict.
        assert payload["output_format"] == case[1]  # Preserve environment normalization and the SQLite default.
        assert payload["failed_checks"] == ([case[3]] if case[3] else [])  # Preserve the exact single failure name.
        assert set(payload["checks"]) == set(case[2])  # Do not add SQLite to polyglot or remote checks to CSV.
        assert [entry[0] for entry in calls.mock_calls] == list(case[2])  # Require the exact actual check order.
        self.verify_checks(client, checks, case, payload)  # Require exact resource calls and results.

    @staticmethod
    def verify_checks(
        client: FlaskClient,
        checks: dict[str, Mock],
        case: tuple[str | None, str, tuple[str, ...], str | None],
        payload: dict[str, Any],
    ) -> None:
        """Require exact arguments and zero calls to every inactive check."""
        arguments = {  # Keep the existing route's resource-reader signatures explicit.
            "data_directory_writable": (client.application.config["DATA_DIR"],),
            "mist_api_session": (None,),
            "sqlite_database": (client.application.config["DATA_DIR"],),
        }
        for name, check in checks.items():  # Inspect every replaced resource boundary.
            if name in case[2]:  # A selected check must run once with its exact existing arguments.
                check.assert_called_once_with(*arguments.get(name, ()))  # Keep no-argument remote checks unchanged.
                assert payload["checks"][name] == {"ok": name != case[3], "detail": "synthetic check"}
            else:  # An inactive backend must not receive a call.
                check.assert_not_called()  # Polyglot must not check SQLite and CSV must not check databases.
