import json
import os
from datetime import datetime

from MistHelper_ssid_write import SSIDTemplateConsolidationManager


def test_prepare_templates_creates_file():
    # Ensure data directory exists
    repo_root = os.path.dirname(os.path.dirname(__file__))
    data_dir = os.path.join(repo_root, "data")
    os.makedirs(data_dir, exist_ok=True)

    # Write a canonical templates dryrun file with a current timestamp so it's the latest
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    canonical_path = os.path.join(data_dir, f"CanonicalTemplates_DRYRUN_{ts}.json")

    canonical = [
        {
            "group_id": "testgrp1",
            "canonical_wlan": {"name": "test-ssid-1", "security": {"method": "wpa2"}},
            "member_count": 2,
        },
        {
            "group_id": "testgrp2",
            "canonical_wlan": {"name": "test-ssid-psk", "security": {"method": "psk", "passphrase": "secret"}},
            "member_count": 1,
        },
    ]
    with open(canonical_path, "w", encoding="utf-8") as fh:
        json.dump(canonical, fh)

    # Run prepare_templates (dry-run True)
    out_path = SSIDTemplateConsolidationManager.prepare_templates(dry_run=True)

    assert os.path.exists(out_path), "prepare_templates did not write an output file"

    # Verify structure
    with open(out_path, "r", encoding="utf-8") as rh:
        payload = json.load(rh)
    assert "requests" in payload
    assert isinstance(payload["requests"], list)
    assert "skipped" in payload
    # The PSK template should have been skipped
    skipped_ids = [s.get("group_id") for s in payload["skipped"]]
    assert "testgrp2" in skipped_ids

    # Cleanup artefacts created by the test
    try:
        os.remove(canonical_path)
    except Exception:
        pass
    try:
        os.remove(out_path)
    except Exception:
        pass
