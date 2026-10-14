"""Serve sanitized offline firmware workflows for visual acceptance without cloud credentials."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from werkzeug.serving import make_server

from src.foundation.support.utils.rate_limiting import RateLimitingUtils
from tests.unit.firmware_policy.fakes import ORG_ID, OTHER_SITE_ID, SITE_ID
from tests.unit.firmware_policy.recovery.fakes import RestoreSession
from web_portal.app import WebPortalApp


class PreviewSession(RestoreSession):
    """Supply realistic public catalog labels and small private fixture settings only."""

    def __init__(self, directory: Path) -> None:
        """Create disposable fixture recovery without reading credentials or product data."""
        super().__init__(directory)
        self.settings[f"/api/v1/sites/{OTHER_SITE_ID}/setting"] = {"org_id": ORG_ID, "site_id": OTHER_SITE_ID}

    def mist_get(self, uri: str, query: dict[str, str] | None = None) -> SimpleNamespace:
        """Return deterministic fixture catalogs and delegate all settings to the offline double."""
        if uri.endswith("/devices/versions"):
            models = {"ap": "AP-EXAMPLE", "switch": "EX-EXAMPLE", "gateway": "SRX-EXAMPLE"}
            model = models[(query or {}).get("type", "ap")]
            rows = [{"model": model, "version": version} for version in ("0.14.9", "0.15.9", "0.15.10")]
            return SimpleNamespace(status_code=200, data=rows, next=None)
        if uri.endswith("/sites"):
            rows = [{"id": SITE_ID, "name": "Alpha site"}, {"id": OTHER_SITE_ID, "name": "Zulu site"}]
            return SimpleNamespace(status_code=200, data=rows, next=None)
        return super().mist_get(uri, query)


class FixturePreview:
    """Keep the preview server loopback-only and remove its disposable records on exit."""

    @staticmethod
    def run() -> None:
        """Start an offline server for the explicit lifetime of this command."""
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("--port", type=int, default=9667)
        arguments = parser.parse_args()
        if not 0 <= arguments.port <= 65535:
            parser.error("The port must be between 0 and 65535.")
        with TemporaryDirectory(prefix="misthelper-4227-fixture-") as directory:
            os.environ["DATA_DIR"] = directory
            RateLimitingUtils.get_rate_limited_delay = staticmethod(lambda *_args: (0.0, 0.0))  # type: ignore[method-assign]
            sdk = PreviewSession(Path(directory))
            app = WebPortalApp.create_app(sdk, {}, ORG_ID)
            app.config["TESTING"] = True
            server = make_server("127.0.0.1", arguments.port, app, threaded=True)
            print(f"Offline fixture preview: http://127.0.0.1:{server.server_port}/operations?menu=305")
            try:
                server.serve_forever()
            finally:
                server.server_close()
                WebPortalApp.shutdown_app(app)


if __name__ == "__main__":
    FixturePreview.run()
