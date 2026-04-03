"""
Create canonical template JSONs as a dry-run (read-only). 

- Reads latest SSIDTemplateProposals_*.csv, SSIDTemplateGroups_*.csv, and SSIDTemplateAudit_*.csv
- For each group, builds a canonical WLAN object using proposed values where available
- Writes a JSON file with canonical templates and their target sites (dry-run only, no API calls)
"""

import csv
import json
import os
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(ROOT, 'data')

if not os.path.exists(DATA_DIR):
    print('data/ directory not found; aborting')
    sys.exit(1)


def find_latest(prefix):
    files = [f for f in os.listdir(DATA_DIR) if f.startswith(prefix) and f.endswith('.csv')]
    if not files:
        return None
    files.sort()
    return os.path.join(DATA_DIR, files[-1])


def load_audit(audit_csv):
    rows = {}
    with open(audit_csv, newline='', encoding='utf-8') as fh:
        r = csv.DictReader(fh)
        for row in r:
            rows[row['wlan_id']] = row
    return rows


def load_groups(groups_csv):
    groups = {}
    with open(groups_csv, newline='', encoding='utf-8') as fh:
        r = csv.DictReader(fh)
        for row in r:
            gid = row['group_id']
            # member list: sample wlan id included in sample_wlan_id; ssids, template_ids could be parsed
            groups[gid] = row
    return groups


def load_proposals(proposals_csv):
    proposals = {}
    with open(proposals_csv, newline='', encoding='utf-8') as fh:
        r = csv.DictReader(fh)
        for row in r:
            gid = row['group_id']
            param = row['parameter']
            proposals.setdefault(gid, {})[param] = json.loads(row['proposed_value_json']) if row['proposed_value_json'] not in (None, '', 'null') else None
    return proposals


def strip_metadata(wlan_json):
    # Remove known metadata fields to create template skeleton
    keys_to_remove = ['id', 'org_id', 'site_id', 'template_id', 'created_time', 'modified_time']
    if isinstance(wlan_json, dict):
        return {k: v for k, v in wlan_json.items() if k not in keys_to_remove}
    return wlan_json


def main():
    groups_csv = find_latest('SSIDTemplateGroups_')
    dev_csv = find_latest('SSIDTemplateDeviations_')
    proposals_csv = find_latest('SSIDTemplateProposals_')
    audit_csv = find_latest('SSIDTemplateAudit_')

    if not (groups_csv and proposals_csv and audit_csv):
        print('Required CSVs not found in data/. Ensure Phase1/Phase2/Phase3 completed.')
        return 1

    groups = load_groups(groups_csv)
    proposals = load_proposals(proposals_csv)
    audit = load_audit(audit_csv)

    canonical_templates = []

    for gid, g in groups.items():
        # Build canonical template using proposals where available, otherwise sample WLAN
        sample_wlan_id = g.get('sample_wlan_id')
        sample_row = audit.get(sample_wlan_id, {})
        sample_wifi_raw = sample_row.get('wifi_raw')
        sample_wlan = None
        if sample_wifi_raw:
            # Try JSON parse first, fall back to ast.literal_eval for Python-style dicts, then try simple quote-replacement
            parsed = None
            try:
                parsed = json.loads(sample_wifi_raw)
            except Exception:
                try:
                    import ast
                    parsed = ast.literal_eval(sample_wifi_raw)
                except Exception:
                    try:
                        # last resort: replace single quotes with double quotes and attempt JSON parse
                        parsed = json.loads(sample_wifi_raw.replace("'", '"'))
                    except Exception:
                        parsed = None
            sample_wlan = parsed

        base = strip_metadata(sample_wlan) if sample_wlan else {}
        group_props = proposals.get(gid, {})
        # apply proposed parameters (these are flat parameter names as in deviations CSV)
        for param, value in group_props.items():
            # naive nesting: support dotted param paths like a.b.c
            if not param or param == '__ALL_STABLE__':
                continue
            path = param.split('.')
            ref = base
            for p in path[:-1]:
                if p not in ref or not isinstance(ref[p], dict):
                    ref[p] = {}
                ref = ref[p]
            ref[path[-1]] = value

        # build metadata for dry-run
        ct = {
            'group_id': gid,
            'member_count': int(g.get('member_count', '1')) if g.get('member_count') else 1,
            'ssids': g.get('ssids', ''),
            'template_ids': g.get('template_ids', ''),
            'template_names': g.get('template_names', ''),
            'applies_site_names': g.get('site_names', ''),
            'sample_wlan_id': sample_wlan_id,
            'canonical_wlan': base,
        }
        canonical_templates.append(ct)

    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    out_file = os.path.join(DATA_DIR, f'CanonicalTemplates_DRYRUN_{ts}.json')
    with open(out_file, 'w', encoding='utf-8') as oh:
        json.dump(canonical_templates, oh, indent=2, default=str)

    print(f'Canonical templates (dry-run) written to: {out_file}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
