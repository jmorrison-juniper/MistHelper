"""
Phase 2 SSID Template Grouping & Deviation Detector
Reads the latest data/SSIDTemplateAudit_*.csv produced by Phase-1 and
produces two read-only reports in data/:
 - SSIDTemplateGroups_<ts>.csv      (group summary)
 - SSIDTemplateDeviations_<ts>.csv  (per-group deviations)

This script is safe to run locally and does not modify Mist or templates.
"""

import ast
import csv
import hashlib
import json
import os
import sys
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
if not os.path.exists(DATA_DIR):
    DATA_DIR = os.path.join(os.getcwd(), "data")

METADATA_KEYS = {"id", "org_id", "site_id", "template_id", "created_time", "modified_time"}


def find_latest_audit_csv():
    candidates = [
        os.path.join(DATA_DIR, f)
        for f in os.listdir(DATA_DIR)
        if f.startswith("SSIDTemplateAudit_") and f.endswith(".csv")
    ]
    if not candidates:
        return None
    candidates.sort(key=os.path.getmtime, reverse=True)
    return candidates[0]


def parse_wifi_raw(raw_str):
    # raw_str often looks like a Python repr of dict/list. Try ast.literal_eval first.
    if raw_str is None:
        return None
    try:
        obj = ast.literal_eval(raw_str)
        # Phase1 stored a list containing one wlan dict in some variants, handle that
        if isinstance(obj, list) and len(obj) == 1 and isinstance(obj[0], dict):
            return obj[0]
        if isinstance(obj, dict):
            return obj
        # Fallback: if it's a JSON string
        if isinstance(obj, str):
            return json.loads(obj)
    except Exception:
        pass
    # Last resort: try JSON loads after replacing single quotes -> double quotes (best-effort)
    try:
        json_str = raw_str.replace("'", '"')
        return json.loads(json_str)
    except Exception:
        return None


def remove_metadata(wlan_dict: dict) -> dict:
    if not isinstance(wlan_dict, dict):
        return wlan_dict
    return {k: v for k, v in wlan_dict.items() if k not in METADATA_KEYS}


def canonicalize(obj) -> str:
    # JSON dump with sorted keys to create stable canonical representation
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def sha256_prefix(s: str, length: int = 8) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:length]


def flatten(obj, parent_key=""):
    items = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                items.update(flatten(v, new_key))
            elif isinstance(v, list):
                # Represent lists as JSON strings for comparison
                try:
                    items[new_key] = json.dumps(v, sort_keys=True, default=str)
                except Exception:
                    items[new_key] = str(v)
            else:
                # Primitives
                items[new_key] = v
    else:
        items[parent_key] = obj
    return items


def main(audit_csv_path: str | None = None):
    if audit_csv_path is None:
        audit_csv_path = find_latest_audit_csv()
    if not audit_csv_path or not os.path.exists(audit_csv_path):
        print("No Phase-1 audit CSV found in data/. Run Phase-1 audit first.")
        return 1

    rows = []
    with open(audit_csv_path, newline='') as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            rows.append(r)

    entries = []
    for r in rows:
        wlan_id = r.get('wlan_id') or r.get('wlan_id')
        template_id = r.get('template_id')
        template_name = r.get('template_name')
        ssid = r.get('ssid')
        site_names = r.get('applies_site_names') or r.get('applies_site_names','')
        wifi_raw = r.get('wifi_raw')
        parsed = parse_wifi_raw(wifi_raw)
        if parsed is None:
            print(f"Warning: failed to parse wifi_raw for wlan {wlan_id}")
            continue
        cleaned = remove_metadata(parsed)
        canonical = canonicalize(cleaned)
        hash_short = sha256_prefix(canonical)
        entries.append({
            'wlan_id': wlan_id,
            'ssid': ssid,
            'template_id': template_id,
            'template_name': template_name,
            'site_names': site_names,
            'canonical': canonical,
            'hash': hash_short,
            'widget': cleaned,
        })

    # Group by canonical string (exact groups)
    groups = {}
    for e in entries:
        key = e['canonical']
        groups.setdefault(key, []).append(e)

    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    groups_csv = os.path.join(DATA_DIR, f"SSIDTemplateGroups_{ts}.csv")
    deviations_csv = os.path.join(DATA_DIR, f"SSIDTemplateDeviations_{ts}.csv")

    with open(groups_csv, 'w', newline='', encoding='utf-8') as gh:
        fieldnames = ['group_id', 'member_count', 'ssids', 'template_ids', 'template_names', 'site_names', 'sample_wlan_id']
        writer = csv.DictWriter(gh, fieldnames=fieldnames)
        writer.writeheader()
        for canonical, members in groups.items():
            group_id = sha256_prefix(canonical, length=8)
            ssids = sorted(set([m['ssid'] for m in members if m.get('ssid')]))
            template_ids = sorted(set([m['template_id'] for m in members if m.get('template_id')]))
            template_names = sorted(set([m['template_name'] for m in members if m.get('template_name')]))
            site_names = sorted(set([s for m in members for s in (m.get('site_names') or '').split(',') if s]))
            writer.writerow({
                'group_id': group_id,
                'member_count': len(members),
                'ssids': ';'.join(ssids),
                'template_ids': ';'.join(template_ids),
                'template_names': ';'.join(template_names),
                'site_names': ';'.join(site_names),
                'sample_wlan_id': members[0]['wlan_id'] if members else ''
            })

    # Compute deviations per group (deep field-by-field)
    with open(deviations_csv, 'w', newline='', encoding='utf-8') as dh:
        fieldnames = ['group_id', 'parameter', 'values_json']
        writer = csv.DictWriter(dh, fieldnames=fieldnames)
        writer.writeheader()
        for canonical, members in groups.items():
            group_id = sha256_prefix(canonical, length=8)
            # flatten each member
            flat_maps = {m['wlan_id']: flatten(m['widget']) for m in members}
            all_keys = set()
            for fm in flat_maps.values():
                all_keys.update(fm.keys())
            for key in sorted(all_keys):
                vals = {wlan_id: flat_maps[wlan_id].get(key, None) for wlan_id in flat_maps.keys()}
                unique_vals = set()
                for v in vals.values():
                    try:
                        unique_vals.add(json.dumps(v, sort_keys=True, default=str))
                    except Exception:
                        unique_vals.add(str(v))
                if len(unique_vals) > 1:
                    # deviation found
                    writer.writerow({
                        'group_id': group_id,
                        'parameter': key,
                        'values_json': json.dumps(vals, default=str)
                    })

    print(f"Groups summary written to: {groups_csv}")
    print(f"Deviations written to: {deviations_csv}")
    return 0


if __name__ == '__main__':
    path_arg = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(main(path_arg))
