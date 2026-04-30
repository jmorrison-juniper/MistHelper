"""Small runner to exercise Phase 1 locally without the full CLI."""
import argparse

from src.ssid_consolidation.manager import SSIDTemplateConsolidationManager


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
        target = input("Target SSID [none]: ")
        if not target:
            print("A target SSID is required.")
            return

    mgr = SSIDTemplateConsolidationManager()
    rows, meta = mgr.phase1_collect(target, force_refresh=args.force)
    print(f"Collected {len(rows)} rows; meta={meta}")


if __name__ == "__main__":
    main()
