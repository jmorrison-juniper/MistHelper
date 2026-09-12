"""Small runner to exercise Phase 1 locally without the full CLI."""

import argparse

from src.ssid_consolidation.manager import SSIDTemplateConsolidationManager
from src.utils.input_utils import InputUtils  # EOF-safe input wrapper (issue #452).


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ssid", required=False, help="Target SSID name")
    p.add_argument("--force", action="store_true", help="Force fresh collection")
    args = p.parse_args()
    target = args.ssid
    if not target:
        import os

        target = os.environ.get("MIST_TARGET_SSID")
    if not target:
        target = InputUtils.safe_input("Target SSID [none]: ", context="run_ssid_phase1_target")  # EOF-safe read.
        if not target:
            print("A target SSID is required.")
            return

    mgr = SSIDTemplateConsolidationManager()
    rows, meta = mgr.phase1_collect(target, force_refresh=args.force)
    print(f"Collected {len(rows)} rows; meta={meta}")


if __name__ == "__main__":
    main()
