"""Dashboard routes for the MistHelper web portal.

Serves the home dashboard page, the cheap liveness endpoint, and the
readiness endpoint that the container health probe calls.
"""

import logging
import os
import socket
import sqlite3
import time
import uuid
from datetime import UTC, datetime
from urllib.parse import urlsplit

from flask import Blueprint, current_app, jsonify, render_template

dashboard_bp = Blueprint("dashboard", __name__)

_start_time = time.time()

SQLITE_DATABASE_FILENAME = "mist_data.db"

READINESS_PROBE_PREFIX = ".readiness-probe-"

READINESS_QUERY_TIMEOUT_SECONDS = 2

DEFAULT_ARANGO_HOST = "misthelper-arangodb"
DEFAULT_ARANGO_PORT = 9529
DEFAULT_REDIS_HOST = "misthelper-redis"
DEFAULT_REDIS_PORT = 9379
POLYGLOT_OUTPUT_FORMAT = "polyglot"
SQLITE_OUTPUT_FORMATS = {"sqlite", "standalone"}


@dashboard_bp.route("/")
def dashboard():
    """Render the dashboard home page."""
    data_dir = current_app.config.get("DATA_DIR", "data")
    summary = _build_data_summary(data_dir)
    return render_template("dashboard.html", summary=summary)


@dashboard_bp.route("/health")
def health():
    """Return a cheap liveness result for the portal process.

    This endpoint reports process liveness only. It reads no disk and
    it opens no network connection, so a blocked resource cannot slow
    the reply down.
    """
    # WHY: a container probe calls this route every few seconds. An INFO line
    # for each call floods the log and hides the real operation records.
    logging.debug("Liveness probe received a request")
    uptime = int(time.time() - _start_time)  # WHY: arithmetic only keeps the reply free of disk cost.
    logging.debug("Liveness probe reports alive after %d seconds", uptime)  # WHY: record the reply value.
    return jsonify(
        {
            "status": "healthy",  # WHY: existing monitors match on this exact word.
            "services": {"web_portal": "running"},  # WHY: name the one process this probe covers.
            "uptime_seconds": uptime,  # WHY: the operator uses the age to spot a restart loop.
        }
    )


@dashboard_bp.route("/ready")
def ready():
    """Return a readiness result that tests every resource the portal needs.

    The route returns code 503 and names each failed check when a
    resource is not usable. It returns code 200 when every check passes.
    """
    data_dir = current_app.config.get("DATA_DIR", "data")  # WHY: the portal writes every output file here.
    apisession = current_app.config.get("APISESSION")  # WHY: the stored session shows the Mist cloud setup.
    checks = _run_readiness_checks(data_dir, apisession)  # WHY: test each resource that can block the portal.
    failed = _collect_failed_check_names(checks)  # WHY: the operator needs the name of each failed check.
    status_code = 503 if failed else 200  # WHY: a monitor acts on 503, and it ignores 200.
    output_format = _configured_output_format()  # WHY: remote readers must know which backend the probe tested.
    payload = {
        "status": "not ready" if failed else "ready",  # WHY: one word gives the operator the verdict.
        "failed_checks": failed,  # WHY: the body must name the failed check, not only the code.
        "checks": checks,  # WHY: the detail text tells the operator how to repair the resource.
        "output_format": output_format,  # WHY: identify the active output backend beside its checks.
        "data_directory": data_dir,  # WHY: repeat the directory under test for a remote reader.
        "uptime_seconds": int(time.time() - _start_time),  # WHY: correlate the failure with a restart.
    }
    logging.debug("Readiness probe replies %d with %d failed checks", status_code, len(failed))
    return jsonify(payload), status_code


def _run_readiness_checks(data_dir: str, apisession) -> dict:
    """Run every readiness check and return one result for each check."""
    logging.info("Readiness probe starts the resource checks")  # WHY: mark the start of the check run.
    checks = {
        "data_directory_writable": _check_data_dir_writable(data_dir),  # WHY: the documented failure.
        "mist_api_session": _check_mist_api_session(apisession),  # WHY: a broken session blocks every operation.
    }
    output_format = _configured_output_format()  # WHY: select checks that match the configured writer.
    if output_format in SQLITE_OUTPUT_FORMATS:  # WHY: SQLite is active only in local database modes.
        checks["sqlite_database"] = _check_sqlite_database(data_dir)  # WHY: validate the selected SQLite backend.
    elif output_format == POLYGLOT_OUTPUT_FORMAT:  # WHY: polyglot writes to both configured services.
        checks["arangodb"] = _check_arangodb()  # WHY: validate the document backend before accepting traffic.
        checks["redis"] = _check_redis()  # WHY: validate the time-series and JSON backend before accepting traffic.
    logging.debug("Readiness probe completed %d checks", len(checks))  # WHY: record the check count.
    return checks


def _configured_output_format() -> str:
    """Return the normalized output format selected by the process environment."""
    output_format = os.environ.get("OUTPUT_FORMAT", "sqlite").strip().lower()  # WHY: preserve the portal default.
    logging.debug("Readiness probe uses output format %s", output_format)  # WHY: make backend selection observable.
    return output_format


def _check_arangodb() -> dict:
    """Test the configured ArangoDB endpoint."""
    raw_host = os.environ.get("ARANGO_HOST", f"http://{DEFAULT_ARANGO_HOST}:{DEFAULT_ARANGO_PORT}")
    address = urlsplit(raw_host if "//" in raw_host else f"//{raw_host}")  # WHY: support URLs and bare host values.
    host = address.hostname or DEFAULT_ARANGO_HOST  # WHY: retain the project host when configuration is incomplete.
    port = address.port or DEFAULT_ARANGO_PORT  # WHY: apply the project port when configuration omits one.
    return _check_backend_socket("arangodb", host, port)  # WHY: test the service selected by the writer.


def _check_redis() -> dict:
    """Test the configured Redis endpoint."""
    host = os.environ.get("REDIS_HOST", DEFAULT_REDIS_HOST).strip()  # WHY: use the same host as the Redis writer.
    raw_port = os.environ.get("REDIS_PORT", str(DEFAULT_REDIS_PORT)).strip()  # WHY: read the project port setting.
    try:
        port = int(raw_port)  # WHY: convert the environment value before opening a socket.
    except ValueError:
        return {"ok": False, "detail": f"REDIS_PORT is not an integer: {raw_port}"}
    return _check_backend_socket("redis", host, port)  # WHY: test the service selected by the writer.


def _check_backend_socket(backend: str, host: str, port: int) -> dict:
    """Return a readiness result for a configured TCP backend."""
    logging.info("Readiness probe tests %s at %s:%s", backend, host, port)  # WHY: log before the network action.
    try:
        with socket.create_connection((host, port), timeout=READINESS_QUERY_TIMEOUT_SECONDS):  # WHY: bound probe time.
            result = {"ok": True, "detail": f"{backend} answered at {host}:{port}"}
    except OSError as exc:
        logging.warning("Readiness probe cannot reach %s at %s:%s: %s", backend, host, port, exc)
        result = {"ok": False, "detail": f"cannot reach {backend} at {host}:{port}: {exc}"}
    logging.debug("Readiness probe completed %s check with ok=%s", backend, result["ok"])  # WHY: record the result.
    return result


def _collect_failed_check_names(checks: dict) -> list:
    """Return the name of every check that did not pass."""
    return [name for name, result in checks.items() if not result["ok"]]  # WHY: names drive the 503 body.


def _check_data_dir_writable(data_dir: str) -> dict:
    """Test write access to the data directory with a temporary file."""
    # WHY: os.path.join builds a path that works on Windows and in the container.
    probe_path = os.path.join(data_dir, READINESS_PROBE_PREFIX + uuid.uuid4().hex)
    logging.info("Readiness probe tests write access in %s", data_dir)  # WHY: log before the disk write.
    try:
        _write_and_remove_probe_file(probe_path)  # WHY: only a real write proves the mount is writable.
    except OSError as exc:
        logging.warning("Readiness probe cannot write in %s: %s", data_dir, exc)  # WHY: name the failure.
        return {"ok": False, "detail": f"cannot write in {data_dir}: {exc}"}
    logging.debug("Readiness probe wrote and removed %s", probe_path)  # WHY: record the successful write.
    return {"ok": True, "detail": f"write access confirmed in {data_dir}"}


def _write_and_remove_probe_file(probe_path: str) -> None:
    """Create the probe file, then delete the probe file again."""
    with open(probe_path, "w", encoding="utf-8") as probe_file:  # WHY: open for write to test the mount.
        probe_file.write("readiness")  # WHY: one short word forces a real write to the file system.
    os.remove(probe_path)  # WHY: delete the probe file so the data directory stays clean.


def _check_sqlite_database(data_dir: str) -> dict:
    """Test the SQLite connection when the database file exists."""
    db_path = os.path.join(data_dir, SQLITE_DATABASE_FILENAME)  # WHY: os.path.join fits both platforms.
    if not os.path.isfile(db_path):
        # WHY: the portal creates the database on demand, so an absent file is not a fault.
        logging.debug("Readiness probe found no database at %s", db_path)
        return {"ok": True, "detail": "database file not created yet"}
    logging.info("Readiness probe opens the database at %s", db_path)  # WHY: log before the connection.
    try:
        _query_sqlite_database(db_path)  # WHY: one query proves the file opens and answers.
    except sqlite3.Error as exc:
        logging.warning("Readiness probe cannot read %s: %s", db_path, exc)  # WHY: name the failure.
        return {"ok": False, "detail": f"cannot read {db_path}: {exc}"}
    logging.debug("Readiness probe read the database at %s", db_path)  # WHY: record the successful read.
    return {"ok": True, "detail": "database answered a query"}


def _query_sqlite_database(db_path: str) -> None:
    """Open the database read-only and read the schema table."""
    normalized_path = db_path.replace("\\", "/")  # WHY: a SQLite URI accepts forward slashes only.
    uri = f"file:{normalized_path}?mode=ro"  # WHY: read the existing database without creating it.
    connection = sqlite3.connect(uri, uri=True, timeout=READINESS_QUERY_TIMEOUT_SECONDS)  # WHY: read-only is safe.
    try:
        # WHY: this query reads a real page, so SQLite validates the file header.
        # A query such as "SELECT 1" answers from memory and passes on a corrupt file.
        connection.execute("SELECT count(*) FROM sqlite_master").fetchone()
    finally:
        connection.close()  # WHY: always close so the probe leaks no file handle.


def _check_mist_api_session(apisession) -> dict:
    """Test the stored Mist API session state without a network call."""
    logging.info("Readiness probe inspects the Mist API session state")  # WHY: log before the read.
    if apisession is None:
        # WHY: the portal serves the data browser with no session, so an absent session is not a fault.
        logging.debug("Readiness probe found no Mist API session")
        return {"ok": True, "detail": "no Mist API session configured"}
    # WHY: mistapi 0.63+ stores the cloud host on the private `_cloud_uri` attribute and
    # exposes it only through `get_cloud()`. A public `host` attribute never exists on that
    # class, so reading `.host` always returned the empty default and failed readiness.
    get_cloud = getattr(apisession, "get_cloud", None)
    if callable(get_cloud):
        host = get_cloud()
    else:
        host = getattr(apisession, "host", "")  # WHY: fall back for a simple test double.
    if not host:
        logging.warning("Readiness probe found a Mist API session with no cloud host")  # WHY: name the failure.
        return {"ok": False, "detail": "Mist API session has no cloud host"}
    logging.debug("Readiness probe found the Mist cloud host %s", host)  # WHY: record the configured host.
    return {"ok": True, "detail": f"Mist API session targets {host}"}


def _build_data_summary(data_dir: str) -> dict:
    """Build summary statistics for the data directory."""
    file_count = _count_data_files(data_dir)
    recent_files = _get_recent_files(data_dir, limit=5)
    return {
        "file_count": file_count,
        "recent_files": recent_files,
        "data_dir": data_dir,
    }


def _count_data_files(data_dir: str) -> int:
    """Count non-hidden files in the data directory."""
    if not os.path.isdir(data_dir):
        return 0
    count = 0
    for entry in os.scandir(data_dir):
        if not entry.name.startswith(".") and entry.is_file():
            count += 1
    return count


def _get_recent_files(data_dir: str, limit: int = 5) -> list:
    """Return the most recently modified files from data dir."""
    if not os.path.isdir(data_dir):
        return []
    files = []
    for entry in os.scandir(data_dir):
        if entry.name.startswith(".") or not entry.is_file():
            continue
        stat = entry.stat()
        files.append(
            {
                "name": entry.name,
                "size_bytes": stat.st_size,
                "size_display": _format_file_size(stat.st_size),
                "last_modified": stat.st_mtime,
                "modified_display": _format_timestamp(stat.st_mtime),
            }
        )
    files.sort(key=lambda f: f["last_modified"], reverse=True)
    return files[:limit]


def _format_file_size(size_bytes: int) -> str:
    """Format bytes into human-readable size string."""
    if size_bytes == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB"]
    index = 0
    size = float(size_bytes)
    while size >= 1024 and index < len(units) - 1:
        size /= 1024
        index += 1
    return f"{size:.1f} {units[index]}"


def _format_timestamp(epoch: float) -> str:
    """Format epoch timestamp into readable date string."""
    if not epoch:
        return ""
    date = datetime.fromtimestamp(epoch, tz=UTC)
    return date.strftime("%Y-%m-%d %H:%M:%S UTC")
