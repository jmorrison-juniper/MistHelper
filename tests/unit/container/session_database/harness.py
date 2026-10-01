"""Run the actual session writer and application boundaries with owned fixtures."""

from __future__ import annotations

import csv
import getpass
import json
import logging
import os
import secrets
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

from src.db import DatabaseConfig, WriteResult
from tests.unit.container.bash_support import BASH_PATH, BASH_SKIP_REASON


class DatabaseSettingsFixture:
    """Create synthetic settings without reading any real credential."""

    FIELDS = {
        "ARANGO_HOST": "arango_host",
        "ARANGO_DATABASE": "arango_database",
        "ARANGO_USERNAME": "arango_username",
        "ARANGO_ROOT_PASSWORD": "arango_password",
        "REDIS_HOST": "redis_host",
        "REDIS_PORT": "redis_port",
        "REDIS_PASSWORD": "redis_password",
    }
    REQUIRED_NAMES = ("ARANGO_USERNAME", "ARANGO_ROOT_PASSWORD", "REDIS_PASSWORD")
    ALLOWED_NAMES = (
        "MIST_HOST",
        "MIST_APITOKEN",
        "MIST_API_TOKEN",
        "MIST_ORG_ID",
        "ORG_ID",
        "org_id",
        "REQUESTS_CA_BUNDLE",
        "SSL_CERT_FILE",
        "HTTPS_PROXY",
        "HTTP_PROXY",
        "NO_PROXY",
        *FIELDS,
    )

    @staticmethod
    def values() -> dict[str, str]:
        """Return complete settings that cannot select a production store."""
        return {
            "ARANGO_HOST": "http://fixture-arango.invalid:9611",
            "ARANGO_DATABASE": "issue3313",
            "ARANGO_USERNAME": secrets.token_hex(16),
            "ARANGO_ROOT_PASSWORD": secrets.token_hex(24),
            "REDIS_HOST": "fixture-redis.invalid",
            "REDIS_PORT": "9613",
            "REDIS_PASSWORD": secrets.token_hex(24),
        }

    @staticmethod
    def awkward_value(case: str) -> str:
        """Return one value case without a credential in a test parameter."""
        marker = secrets.token_hex(16)
        cases = {
            "empty": "",
            "plain": marker,
            "space": f" {marker} two words ",
            "quotes": f"{marker}'\"quoted'\"",
            "dollar": f"{marker}$HOME$(not_a_command)",
            "newline": f"{marker}\nsecond line\n",
            "unicode": f"{marker}\u00e9\u6f22\U0001f642",
            "large": marker * 1024,
        }
        return cases[case]


class SessionEnvironmentHarness:
    """Write and read the session file through separate clean Bash processes."""

    ROOT = Path(__file__).resolve().parents[4]
    WRITER = ROOT / "container" / "scripts" / "write-session-env.sh"

    def __init__(self, directory: Path) -> None:
        """Use only the directory that pytest assigned to this contract."""
        if BASH_PATH is None or BASH_SKIP_REASON is not None:
            raise RuntimeError(f"Checked 0 session files. Bash capability is unavailable: {BASH_SKIP_REASON}")
        self.directory = directory
        self.target = directory / "session.env"
        self.owner = getpass.getuser()
        self.timeout = 30

    def write(self, values: dict[str, str]) -> subprocess.CompletedProcess[str]:
        """Run the unchanged writer interface without inherited secrets."""
        logging.info("Writing one fixture session file with %d configuration names", len(values))
        result = subprocess.run(
            [str(BASH_PATH), str(self.WRITER), self.owner, str(self.target)],
            env={"PATH": "/usr/bin:/bin", **values},
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=self.timeout,
            check=False,
        )
        logging.debug("Checked 1 session file. Writer exit status: %d", result.returncode)
        return result

    def source(self, mode: str, expected: dict[str, str]) -> subprocess.CompletedProcess[str]:
        """Require a readable session file and pass values as input data."""
        logging.info("Reading one fixture session file through a fresh shell")
        result = subprocess.run(
            [
                str(BASH_PATH),
                "-c",
                'set -a; source "$1" || exit 1; set +a; exec "$2" -m '
                'tests.unit.container.session_database.harness "$3" "$4"',
                "session-database-contract",
                str(self.target),
                sys.executable,
                mode,
                str(self.directory),
            ],
            env={"PATH": "/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "PYTHONUTF8": "1"},
            input=json.dumps(expected),
            cwd=self.ROOT,
            capture_output=True,
            encoding="utf-8",
            timeout=self.timeout,
            check=False,
        )
        logging.debug("Checked 1 fresh session. Probe exit status: %d", result.returncode)
        return result


class SessionDatabaseProbe:
    """Compare configuration internally and print names and counts only."""

    @staticmethod
    def expected() -> dict[str, str]:
        """Fail if the required fixture input is absent or invalid."""
        try:
            supplied = json.load(sys.stdin)
        except (json.JSONDecodeError, OSError) as error:
            raise ValueError("Checked 0 configuration names. Cannot read the required fixture input.") from error
        if not isinstance(supplied, dict) or not supplied:
            raise ValueError("Checked 0 configuration names. Expected a fixture object.")
        if any(not isinstance(name, str) or not isinstance(value, str) for name, value in supplied.items()):
            raise ValueError("Checked 0 configuration names. Expected string names and values.")
        return dict(supplied)

    @classmethod
    def environment(cls) -> int:
        """Verify exact round trips and exclusion without printing a value."""
        expected = cls.expected()
        for name, value in expected.items():
            wanted = value if name in DatabaseSettingsFixture.ALLOWED_NAMES and value else None
            if os.environ.get(name) != wanted:
                raise ValueError(f"Checked {len(expected)} configuration names. Session mismatch: {name}.")
        print(f"Checked {len(expected)} configuration names.")
        return 0

    @staticmethod
    def verify_config(configuration: DatabaseConfig, expected: dict[str, str]) -> None:
        """Read all seven actual configuration fields without revealing them."""
        for name, field in DatabaseSettingsFixture.FIELDS.items():
            actual = str(getattr(configuration, field))
            wanted = expected[name]
            if name in DatabaseSettingsFixture.REQUIRED_NAMES:
                wanted = wanted.strip()
            if actual != wanted:
                raise ValueError(f"Checked 7 database settings. Configuration mismatch: {name}.")
        if configuration.standalone_mode:
            raise ValueError("Checked 7 database settings. The fixture must use the database.")

    @classmethod
    def configuration(cls) -> int:
        """Replace discovery only and use the actual configuration builder."""
        expected = cls.expected()
        with patch("src.db._hosts_unreachable", return_value=False):
            configuration = DatabaseConfig.from_env()
        cls.verify_config(configuration, expected)
        print("Checked 7 database settings.")
        return 0

    @classmethod
    def run(cls) -> int:
        """Dispatch one fixed probe mode with required input."""
        actions = {
            "environment": cls.environment,
            "configuration": cls.configuration,
            "export": FixtureDatabaseExport.run,
        }
        if len(sys.argv) != 3 or sys.argv[1] not in actions:
            raise ValueError("Checked 0 session probes. Expected a supported probe and an owned directory.")
        return actions[sys.argv[1]]()


class FixtureArangoDatabase:
    """Retain actual routed fixture records instead of returning a canned result."""

    def __init__(self) -> None:
        """Start with no configuration or stored record."""
        self.config: DatabaseConfig | None = None
        self.records: list[dict[str, Any]] = []

    def connect(self, configuration: DatabaseConfig) -> FixtureArangoDatabase:
        """Capture the actual router configuration without opening a socket."""
        logging.info("Connecting one owned fixture backend")
        self.config = configuration
        logging.debug("Connected 1 owned fixture backend")
        return self

    def write(self, data: list[dict[str, Any]], endpoint: str, strategy: dict[str, Any]) -> WriteResult:
        """Store the routed records and derive the result from the stored count."""
        if endpoint != "listOrgMarvisActions" or strategy.get("type") not in {
            "natural_pk",
            "auto_increment_with_unique",
        }:
            raise ValueError("Checked 1 fixture route. Expected the ArangoDB strategy.")
        if strategy.get("primary_key") != ["uuid"] or any(not record.get("uuid") for record in data):
            raise ValueError("Checked 2 fixture records. Expected the natural primary key.")
        logging.info("Writing %d records to the owned fixture backend", len(data))
        self.records.extend(dict(record) for record in data)
        destination = Path("data") / "fixture-documents.json"
        destination.write_text(json.dumps(self.records), encoding="utf-8")
        logging.debug("Stored %d owned fixture records", len(self.records))
        return WriteResult(True, "arangodb", len(data), 0)


class FixtureDatabaseExport:
    """Run the actual exporter and router without a Mist or database connection."""

    RECORDS = [{"uuid": "fixture-1", "name": "first"}, {"uuid": "fixture-2", "name": "second"}]

    @classmethod
    def run(cls) -> int:
        """Keep every export artifact under the owned temporary data directory."""
        expected = SessionDatabaseProbe.expected()
        os.chdir(sys.argv[2])
        Path("data").mkdir()
        logging.basicConfig(filename=Path("data") / "script.log", level=logging.INFO, force=True)
        backend = FixtureArangoDatabase()
        cls.export(backend)
        cls.verify(backend, expected)
        print("Checked 7 database settings. Stored 2 fixture records.")
        return 0

    @classmethod
    def export(cls, backend: FixtureArangoDatabase) -> None:
        """Replace backend connections only, not exporter or router behavior."""
        from src.dataclasses.export_backend_options import ExportBackendOptions
        from src.export.data_exporter import DataExporter

        with (
            patch("src.db._hosts_unreachable", return_value=False),
            patch("src.export.data_exporter.polyglot_hosts_unreachable", return_value=False),
            patch("src.db.router.ArangoDBWriter", autospec=True, side_effect=backend.connect),
            patch("src.db.router.RedisTimeSeriesWriter", autospec=True),
            patch("src.db.router.RedisJSONWriter", autospec=True),
        ):
            result = DataExporter.write_with_format_selection(
                cls.RECORDS,
                "fixture-export.csv",
                "listOrgMarvisActions",
                backend_options=ExportBackendOptions(format_override="csv"),
            )
        if result is not True:
            raise RuntimeError("Checked 2 fixture records. The CSV export failed.")

    @classmethod
    def verify(cls, backend: FixtureArangoDatabase, expected: dict[str, str]) -> None:
        """Require the stored records, configuration, and CSV copy to agree."""
        if backend.config is None:
            raise RuntimeError("Checked 0 database records. The fixture router did not build.")
        SessionDatabaseProbe.verify_config(backend.config, expected)
        stored = json.loads((Path("data") / "fixture-documents.json").read_text(encoding="utf-8"))
        with (Path("data") / "fixture-export.csv").open(encoding="utf-8", newline="") as handle:
            csv_records = list(csv.DictReader(handle))
        if backend.records != cls.RECORDS or stored != cls.RECORDS or csv_records != cls.RECORDS:
            raise RuntimeError("Checked 2 fixture records. The stored copies do not agree.")


if __name__ == "__main__":
    sys.exit(SessionDatabaseProbe.run())
