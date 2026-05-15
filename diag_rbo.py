"""Diagnostic: inspect RBO-Large-DIA Network Template entries."""

import json

from src.audit.renderer import AuditReportRenderer

with open("data/orgaudit-filtered.json") as f:
    raw = json.load(f)

data = raw.get("results", raw) if isinstance(raw, dict) else raw

for entry in data:
    msg = entry.get("message", "")
    if "RBO-Large-DIA" not in msg:
        continue

    before = entry.get("before", {})
    after = entry.get("after", {})
    ts = entry.get("timestamp", 0)

    if not isinstance(before, dict) or not isinstance(after, dict):
        continue

    delta_b, delta_a = AuditReportRenderer._compute_delta(before, after)

    print(f"TS={ts} Admin={entry.get('admin_name','?')[:30]}")
    print(f"  Before keys: {list(before.keys())}")
    print(f"  After keys:  {list(after.keys())}")
    print(f"  Delta before empty: {not delta_b}")
    print(f"  Delta after empty:  {not delta_a}")

    if not delta_b and not delta_a:
        # Dig into routing_policies specifically
        rp_b = before.get("routing_policies", {})
        rp_a = after.get("routing_policies", {})
        print(f"  routing_policies equal: {rp_b == rp_a}")
        if rp_b != rp_a:
            for k in rp_b:
                vb = rp_b[k]
                va = rp_a.get(k)
                if vb != va and isinstance(vb, dict) and isinstance(va, dict):
                    print(f"  Inner key={k}, equal={vb == va}")
                    terms_b = vb.get("terms", [])
                    terms_a = va.get("terms", [])
                    print(f"    terms equal: {terms_b == terms_a}")
                    print(f"    terms_b len: {len(terms_b)}, terms_a len: {len(terms_a)}")
                    # Check identity detection
                    for i, t in enumerate(terms_b):
                        eid = AuditReportRenderer._element_identity(t)
                        print(f"    terms_b[{i}] identity: {eid}")
                    for i, t in enumerate(terms_a):
                        eid = AuditReportRenderer._element_identity(t)
                        print(f"    terms_a[{i}] identity: {eid}")
                    # Run delta_list
                    lb, la = AuditReportRenderer._compute_delta_list(terms_b, terms_a)
                    print(f"    delta_list result: before={lb}, after={la}")

    print()
