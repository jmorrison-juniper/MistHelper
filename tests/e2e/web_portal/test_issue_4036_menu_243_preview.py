"""Verify that Menu 243 output discovery leads to a readable browser preview."""

from __future__ import annotations

import json
import logging
import threading
from collections.abc import Iterator
from functools import partial
from pathlib import Path
from typing import Any

import pytest

logger = logging.getLogger(__name__)
pytest.importorskip("playwright", reason="playwright is absent, so no browser test can run")

READY_TIMEOUT_MS = 15_000
RUN_TIMEOUT_MS = 30_000


def _build_menu243_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    """Build the real portal with Menu 243 and synthetic files under its data root."""
    import MistHelper
    from src.operations.hardware.mib_generator import runner as mib_runner
    from web_portal.app import WebPortalApp

    data_dir = tmp_path / "data"
    input_dir = data_dir / "mib_generator"
    input_dir.mkdir(parents=True)
    openapi_path = (
        Path(__file__).resolve().parents[3]
        / "tests"
        / "unit"
        / "prod_readiness"
        / "operations"
        / "hardware"
        / "mib_generator"
        / "generator"
        / "fixtures"
        / "mini_openapi.json"
    )
    allowlist_path = input_dir / "allowlist.json"
    ledger_path = input_dir / "oid_assignments.json"
    allowlist_path.write_text(
        json.dumps({"entries": [{"operation_id": "getOrgStats", "scope": "org"}]}),
        encoding="utf-8",
    )
    ledger_path.write_text('{"entries":[]}', encoding="utf-8")
    real_runner = mib_runner.MibGeneratorRunner
    monkeypatch.setattr(
        mib_runner,
        "MibGeneratorRunner",
        partial(real_runner, openapi_path, allowlist_path, ledger_path),
    )
    monkeypatch.setenv("DATA_DIR", str(data_dir))
    monkeypatch.chdir(tmp_path)
    app = WebPortalApp.create_app(None, MistHelper.menu_actions, "synthetic-org")
    app.config.update(TESTING=True, DATA_DIR=str(data_dir))
    return app


@pytest.fixture
def menu243_portal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """Serve the real portal on loopback with isolated operation inputs and outputs."""
    from werkzeug.serving import make_server

    from web_portal.app import WebPortalApp

    app = _build_menu243_app(tmp_path, monkeypatch)
    server = make_server("127.0.0.1", 0, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    logger.info("Starting the synthetic Menu 243 portal on port %d", server.server_port)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=10)
        WebPortalApp.shutdown_app(app)


def _start_menu243(page: Any) -> str:
    """Start the registered Menu 243 handler through the protected route."""
    token = page.locator('meta[name="csrf-token"]').get_attribute("content")
    if not token:
        raise AssertionError("The operations page did not return a CSRF token.")
    run = page.evaluate(
        """async token => {
            const response = await fetch('/api/operations/run', {
                method: 'POST',
                headers: {'Content-Type': 'application/json', 'X-CSRFToken': token},
                body: JSON.stringify({menu_number: '243', parameters: {}})
            });
            return await response.json();
        }""",
        token,
    )
    run_id = run.get("run_id") if isinstance(run, dict) else None
    if not isinstance(run_id, str):
        raise AssertionError(f"Menu 243 did not start: {run!r}")
    return run_id


def _wait_for_menu243(page: Any, run_id: str) -> dict[str, Any]:
    """Wait for the route to report a terminal Menu 243 status."""
    page.wait_for_function(
        """async runId => {
            const response = await fetch('/api/operations/status/' + runId);
            const status = await response.json();
            if (status.status === 'completed' || status.status === 'failed') {
                window.menu243RunStatus = status;
                return true;
            }
            return false;
        }""",
        arg=run_id,
        timeout=RUN_TIMEOUT_MS,
    )
    result = page.evaluate("window.menu243RunStatus")
    if not isinstance(result, dict):
        raise AssertionError("The Menu 243 status route returned no run record.")
    return result


def test_menu243_discovers_downloadable_json_and_previews_it(page: Any, menu243_portal: str, tmp_path: Path) -> None:
    """Follow the real discovered ledger from Menu 243 through browser download and preview."""
    page.goto(f"{menu243_portal}/operations", wait_until="networkidle", timeout=READY_TIMEOUT_MS)
    run_id = _start_menu243(page)
    status = _wait_for_menu243(page, run_id)
    assert status["status"] == "completed", status
    output_files = status["output_files"]
    assert output_files == ["mib_generator/oid_assignments.json"]
    assert (tmp_path / "documentation" / "mibs" / "MISTHELPER-MIB.mib").is_file()

    downloads = page.evaluate(
        """async paths => Promise.all(paths.map(async path => {
            const response = await fetch('/api/data/download/' + encodeURIComponent(path));
            return {status: response.status, text: await response.text()};
        }))""",
        ["mib_generator/allowlist.json", *output_files],
    )
    assert [item["status"] for item in downloads] == [200, 200]
    assert "getOrgStats" in downloads[0]["text"]
    assert "mib_generator/allowlist.json" not in output_files

    with page.expect_response(lambda response: "/api/data/preview/" in response.url) as preview_response:
        page.evaluate("(files) => OperationResults.showForRun(files)", output_files)
    assert preview_response.value.status == 200
    page.wait_for_function(
        "() => document.getElementById('resultsBody').innerText.includes('base_oid')",
        timeout=READY_TIMEOUT_MS,
    )
    preview_text = page.locator("#resultsBody").inner_text()
    assert "Could not read the results" not in preview_text
