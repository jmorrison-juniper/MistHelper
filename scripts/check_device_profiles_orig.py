"""Find original service_policies for device profiles"""

import json

with open("data/orgaudit-filtered.json") as f:
    data = json.load(f)

for name in ["VRECHI52RBO", "VREDAL52RBO"]:
    entries = [e for e in data["results"] if name in e.get("message", "")]
    print(f"=== {name} ORIGINAL service_policies ===")
    found = False
    for e in entries:
        b = e.get("before", {})
        if "service_policies" in b:
            ts = e["timestamp"]
            admin = e["admin_name"].split()[0]
            print(f"First entry with SP in BEFORE (ts={ts}, {admin}):")
            for p in b["service_policies"]:
                n = p.get("name", f"ref:{p.get('servicepolicy_id','?')[:12]}")
                lp = p.get("local_preference")
                pp = p.get("path_preference")
                lr = p.get("local_routing")
                tenants = p.get("tenants", [])
                extra = ""
                if lp:
                    extra += f" local_preference={lp}"
                if pp:
                    extra += f" path_preference={pp}"
                if lr:
                    extra += f" local_routing={lr}"
                print(f"  {n}: tenants={tenants}{extra}")
            found = True
            break
    if not found:
        print("  (no service_policies changes in audit window)")
    print()
