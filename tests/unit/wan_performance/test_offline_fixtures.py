"""Check that WAN preview data stays synthetic and offline."""

import ast  # Inspect the fixture module for live-client dependencies.
from inspect import getsourcefile  # Locate the fixture code without importing other modules.
from pathlib import Path  # Read the fixture module through a platform-safe path.

from tests.fixtures.wan_performance.offline_dashboard import (  # Import the isolated fixture factory.
    OfflineDashboardFactory,
)

FORBIDDEN_IMPORT_ROOTS = frozenset(  # Keep offline fixtures separate from service clients.
    {"mistapi", "redis", "sqlite3", "arango", "threading", "multiprocessing"}
)
FORBIDDEN_CALL_NAMES = frozenset(  # Prevent fixture loading from starting clients or workers.
    {"ArangoClient", "Redis", "Thread", "Process", "connect", "start"}
)


def test_offline_dashboard_contains_only_historical_synthetic_records() -> None:
    """Keep every fixture record synthetic and independent of live measurements."""
    dashboard = OfflineDashboardFactory.build()  # Load data without selecting runtime services.

    assert dashboard.provenance == "synthetic"  # Label the full fixture set as synthetic.
    assert dashboard.site.site_id == "11111111-1111-1111-1111-111111111111"  # Preserve the documented route ID.
    assert dashboard.circuit.port_name == "ge-0/0/1"  # Keep the slash-bearing port identity intact.
    assert dashboard.peer_path.peer_mac == "11:22:33:44:55:66"  # Keep the peer route identity intact.
    assert dashboard.measurements  # Require preview content for the journeys.
    assert all(record.provenance == "synthetic" for record in dashboard.measurements)  # Block live fixture records.
    assert all(record.hour_start_utc.year < 2026 for record in dashboard.measurements)  # Keep fixture times historical.


def test_offline_fixture_module_has_no_live_service_imports_or_start_calls() -> None:
    """Block fixture code from importing service clients or starting workers."""
    fixture_source = getsourcefile(OfflineDashboardFactory)  # Locate the module that defines the fixture factory.
    assert fixture_source is not None  # Require the source file so the isolation contract can run.
    fixture_path = Path(fixture_source)  # Resolve the fixture source file.
    syntax_tree = ast.parse(fixture_path.read_text(encoding="utf-8"))  # Inspect only the fixture module.
    imported_roots = {  # Collect each imported package root.
        (node.module or "").split(".", maxsplit=1)[0]
        for node in ast.walk(syntax_tree)
        if isinstance(node, ast.ImportFrom)
    }
    imported_roots.update(  # Include regular import statements in the same dependency check.
        alias.name.split(".", maxsplit=1)[0]
        for node in ast.walk(syntax_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )
    called_names = {  # Collect direct and attribute calls that can start clients or workers.
        ast.unparse(node.func).split(".")[-1] for node in ast.walk(syntax_tree) if isinstance(node, ast.Call)
    }

    assert imported_roots.isdisjoint(FORBIDDEN_IMPORT_ROOTS)  # Keep runtime clients out of offline imports.
    assert called_names.isdisjoint(FORBIDDEN_CALL_NAMES)  # Keep collection and worker startup out of fixtures.
