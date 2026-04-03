"""
Phase 3 (Read-only): Generate canonical proposals for each SSID grouping.
Reads the latest SSIDTemplateDeviations_* and SSIDTemplateGroups_* outputs and
produces a proposals CSV with the majority/canonical value suggestion for each
parameter per group. This is read-only and intended for operator review.
"""

import csv
import json
import os
import sys
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
if not os.path.exists(DATA_DIR):
    DATA_DIR = os.path.join(os.getcwd(), "data")


def find_latest(pattern_prefix):
    files = [f for f in os.listdir(DATA_DIR) if f.startswith(pattern_prefix) and f.endswith('.csv')]
    if not files:
        return None
    files.sort()
    return os.path.join(DATA_DIR, files[-1])


def load_groups(groups_csv):
    groups = {}
    with open(groups_csv, newline='', encoding='utf-8') as fh:
        r = csv.DictReader(fh)
        for row in r:
            groups[row['group_id']] = row
    return groups


def load_deviations(dev_csv):
    devs = {}
    with open(dev_csv, newline='', encoding='utf-8') as fh:
        r = csv.DictReader(fh)
        for row in r:
            gid = row['group_id']
            param = row['parameter']
            vals = json.loads(row['values_json']) if row['values_json'] else {}
            devs.setdefault(gid, {})[param] = vals
    return devs


def majority_value(val_map):
    # val_map: {wlan_id: value}
    counts = {}
    for v in val_map.values():
        key = json.dumps(v, sort_keys=True, default=str)
        counts[key] = counts.get(key, 0) + 1
    if not counts:
        return None, {}
    # choose most common
    sorted_counts = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
    chosen_key = sorted_counts[0][0]
    return json.loads(chosen_key) if (chosen_key.startswith('{') or chosen_key.startswith('[')) else json.loads(chosen_key) if chosen_key in ('null','true','false') else json.loads(chosen_key) if isinstance(chosen_key,str) and chosen_key.startswith('"') else json.loads(chosen_key) if False else chosen_key, {k: v for k, v in counts.items()}


def safe_normalize(v):
    try:
        return json.loads(v) if isinstance(v, str) and (v.startswith('{') or v.startswith('[') or v in ('null','true','false')) else v
    except Exception:
        return v


def main():
    groups_csv = find_latest('SSIDTemplateGroups_')
    dev_csv = find_latest('SSIDTemplateDeviations_')
    if not groups_csv or not dev_csv:
        print('Groups or deviations CSV not found in data/. Run Phase2 grouping first.')
        return 1

    groups = load_groups(groups_csv)
    devs = load_deviations(dev_csv)

    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    proposals_csv = os.path.join(DATA_DIR, f"SSIDTemplateProposals_{ts}.csv")

    with open(proposals_csv, 'w', newline='', encoding='utf-8') as ph:
        fieldnames = ['group_id', 'parameter', 'proposed_value_json', 'value_counts_json', 'raw_values_json']
        w = csv.DictWriter(ph, fieldnames=fieldnames)
        w.writeheader()
        for gid, group in groups.items():
            params = devs.get(gid, {})
            if not params:
                # no deviations -> nothing to propose, but write row indicating stable
                w.writerow({'group_id': gid, 'parameter': '__ALL_STABLE__', 'proposed_value_json': json.dumps(None), 'value_counts_json': json.dumps({}), 'raw_values_json': json.dumps({})})
                continue
            for param, valmap in params.items():
                # valmap: wlan_id -> value
                # compute counts
                counts = {}
                for v in valmap.values():
                    key = json.dumps(v, sort_keys=True, default=str)
                    counts[key] = counts.get(key, 0) + 1
                # pick most common
                chosen_key = sorted(counts.items(), key=lambda x: (-x[1], x[0]))[0][0]
                try:
                    proposed = json.loads(chosen_key)
                except Exception:
                    # fallback to string
                    proposed = chosen_key
                w.writerow({'group_id': gid, 'parameter': param, 'proposed_value_json': json.dumps(proposed, default=str), 'value_counts_json': json.dumps(counts), 'raw_values_json': json.dumps(valmap, default=str)})

    print(f'Proposals written to: {proposals_csv}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
