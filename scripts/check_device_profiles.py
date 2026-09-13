"""Check device profile changes for VREDAL52RBO and VRECHI52RBO"""

import json

with open("data/orgaudit-filtered.json") as f:
    data = json.load(f)

entries = [e for e in data["results"] if "VREDAL52RBO" in e.get("message", "") or "VRECHI52RBO" in e.get("message", "")]

for name in ["VRECHI52RBO", "VREDAL52RBO"]:
    mine = [e for e in entries if name in e["message"]]
    first = mine[0]
    last = mine[-1]
    print(f"=== {name} ===")
    print(f"FIRST change (ts={first['timestamp']}, Admin={first['admin_name'].split()[0]}):")
    b = first.get("before", {})
    a = first.get("after", {})
    print(f"  BEFORE keys: {list(b.keys())}")
    if "service_policies" in b:
        for p in b["service_policies"]:
            n = p.get("name", "?")
            lp = p.get("local_preference")
            if lp:
                print(f"    {n}: local_preference={lp}")
    print(f"LAST change (ts={last['timestamp']}, Admin={last['admin_name'].split()[0]}):")
    a2 = last.get("after", {})
    print(f"  AFTER keys: {list(a2.keys())}")
    if "service_policies" in a2:
        for p in a2["service_policies"]:
            n = p.get("name", "?")
            lp = p.get("local_preference")
            if lp:
                print(f"    {n}: local_preference={lp}")
    print()
    # Also check Jay's earliest changes (ts 1778024199-1778024346) for what he changed
    jay_early = [e for e in mine if e["timestamp"] < 1778025000]
    if jay_early:
        je = jay_early[0]
        jb = je.get("before", {})
        ja = je.get("after", {})
        print(f"  Jay's FIRST change BEFORE keys: {list(jb.keys())}")
        print(f"  Jay's FIRST change AFTER keys: {list(ja.keys())}")
        if "service_policies" in jb:
            print("  Jay BEFORE service_policies with local_preference:")
            for p in jb["service_policies"]:
                n = p.get("name", "?")
                lp = p.get("local_preference")
                if lp:
                    print(f"    {n}: local_preference={lp}")
        if "service_policies" in ja:
            print("  Jay AFTER service_policies with local_preference:")
            for p in ja["service_policies"]:
                n = p.get("name", "?")
                lp = p.get("local_preference")
                if lp:
                    print(f"    {n}: local_preference={lp}")
    print()
