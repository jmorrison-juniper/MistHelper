#!/usr/bin/env python3
import os
import glob
import json
import logging
import datetime
import sys

# Adjust sys.path so the repository root is importable when running from /scripts
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

# Import from the MistHelper package
from MistHelper import SSIDTemplateConsolidationManager, FilePathUtils, InputUtils

logging.basicConfig(level=logging.INFO)

def main():
    try:
        logging.info("Starting prepare_templates (dry-run)")
        SSIDTemplateConsolidationManager.prepare_templates(dry_run=True)
    except Exception:
        logging.exception("prepare_templates failed")
        sys.exit(2)

    # Locate prepared requests file
    data_dir = os.path.dirname(FilePathUtils.get_csv_path("dummy.csv"))
    pattern = os.path.join(data_dir, "CreateTemplateRequests_DRYRUN_*.json")
    files = glob.glob(pattern)
    if not files:
        logging.error("No CreateTemplateRequests_DRYRUN_*.json found after prepare_templates")
        sys.exit(3)
    files.sort()
    req_file = files[-1]
    logging.info(f"Found prepared requests file: {req_file}")

    with open(req_file, "r", encoding="utf-8") as fh:
        payload = json.load(fh)

    requests_list = payload.get("requests", [])
    skipped = payload.get("skipped", [])
    if not requests_list:
        logging.error("Prepared file contains no requests; aborting apply")
        sys.exit(4)

    # Sanity check: ensure each request has a non-empty wlan body
    empty_groups = []
    for req in requests_list:
        body = req.get("body", {})
        wlan = body.get("wlan", {})
        if not wlan:
            empty_groups.append(req.get("group_id"))

    if empty_groups:
        logging.error("Found requests with empty 'wlan' body for groups: %s. Aborting apply.", empty_groups)
        out = {
            "status": "abort",
            "reason": "empty_wlan_bodies",
            "groups": empty_groups,
            "req_file": req_file,
            "skipped": skipped,
        }
        out_path = os.path.join(data_dir, f"CreateTemplateApply_AutonomousAbort_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(out_path, "w", encoding="utf-8") as oh:
            json.dump(out, oh, indent=2)
        logging.info("Wrote abort record to %s", out_path)
        print(out_path)
        sys.exit(5)

    # All checks passed; proceed to apply prepared templates
    logging.info("All requests contain wlan bodies; proceeding to apply")

    # Gate auto-confirm behind explicit flag and environment variable for safety.
    auto_confirm = False
    if "--auto-confirm" in sys.argv:
        auto_confirm = True
    if auto_confirm:
        if os.environ.get("AUTONOMOUS_APPLY_ALLOWED", "") == "1":
            logging.warning("Auto-confirm enabled (AUTONOMOUS_APPLY_ALLOWED=1). Proceeding without interactive prompt.")
            InputUtils.safe_input = lambda *a, **k: "APPLY"
        else:
            logging.error("Auto-confirm requested but AUTONOMOUS_APPLY_ALLOWED env var not set to '1'. Aborting.")
            sys.exit(8)

    try:
        SSIDTemplateConsolidationManager.apply_prepared_templates()
    except Exception:
        logging.exception("apply_prepared_templates failed")
        sys.exit(6)

    # Find results file
    pattern_out = os.path.join(data_dir, "CreateTemplateResults_*.json")
    out_files = glob.glob(pattern_out)
    if out_files:
        out_files.sort()
        results_file = out_files[-1]
        logging.info("Apply completed; results written to %s", results_file)
        print(results_file)
        sys.exit(0)
    else:
        logging.error("Apply completed but no results file found")
        sys.exit(7)

if __name__ == '__main__':
    main()
