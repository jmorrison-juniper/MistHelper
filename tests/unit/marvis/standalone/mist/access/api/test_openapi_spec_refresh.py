"""Tests for the bundled Mist OpenAPI release."""

import hashlib
import json
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
JSON_SPEC = REPOSITORY_ROOT / "documentation" / "mist-api-openapi31json.json"
YAML_SPEC = REPOSITORY_ROOT / "documentation" / "mist-api-openapi31yaml.yaml"
HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}


def test_bundled_openapi_spec_matches_release_2609() -> None:
    """The bundled JSON and YAML files must describe the same current release."""
    spec = json.loads(JSON_SPEC.read_text(encoding="utf-8"))
    operations = [
        operation
        for path_item in spec["paths"].values()
        for method, operation in path_item.items()
        if method in HTTP_METHODS
    ]
    assert spec["info"]["version"] == "2609.1.0"
    assert len(spec["paths"]) == 762
    assert len(operations) == 1072
    assert len(spec["webhooks"]) == 30
    assert hashlib.sha256(JSON_SPEC.read_bytes()).hexdigest() == (
        "22f55432535ab38f6c0539392a729b8fd515a9ccae9df693fbd4ff23d40b8fac"
    )
    assert "2609.1.0" in YAML_SPEC.read_text(encoding="utf-8")
    assert "/api/v1/orgs/{org_id}/insights/fingerprints/count" in spec["paths"]
    assert "/api/v1/orgs/{org_id}/insights/fingerprints/search" in spec["paths"]
    assert "/api/v1/sites/{site_id}/insights/fingerprints/count" not in spec["paths"]
    assert "/api/v1/sites/{site_id}/insights/fingerprints/search" not in spec["paths"]
