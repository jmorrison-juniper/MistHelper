"""Analyze vpn_access flag patterns in orgaudit-filtered.json"""

import json
from collections import Counter

with open("data/orgaudit-filtered.json") as f:
    data = json.load(f)

removals = []
additions = []
for e in data["results"]:
    msg = e.get("message", "")
    if "Network" in msg:
        before = e.get("before", {})
        after = e.get("after", {})
        b_vpn = before.get("vpn_access", {})
        a_vpn = after.get("vpn_access", {})
        if b_vpn and not a_vpn:
            removals.append(e)
        elif a_vpn and not b_vpn:
            additions.append(e)

orig_patterns = Counter()
for e in removals:
    flags = list(e["before"]["vpn_access"].values())[0]
    key = (
        f"routed={flags.get('routed')} "
        f"overlay={flags.get('no_readvertise_to_overlay')} "
        f"bgp={flags.get('no_readvertise_to_lan_bgp')} "
        f"ospf={flags.get('no_readvertise_to_lan_ospf')}"
    )
    orig_patterns[key] += 1

readd_patterns = Counter()
for e in additions:
    flags = list(e["after"]["vpn_access"].values())[0]
    key = (
        f"routed={flags.get('routed')} "
        f"overlay={flags.get('no_readvertise_to_overlay')} "
        f"bgp={flags.get('no_readvertise_to_lan_bgp')} "
        f"ospf={flags.get('no_readvertise_to_lan_ospf')}"
    )
    readd_patterns[key] += 1

print("ORIGINAL patterns (before Morrison removed):")
for k, v in orig_patterns.most_common():
    print(f"  {v}x {k}")
print()
print("RE-ADDED patterns (Jay put back):")
for k, v in readd_patterns.most_common():
    print(f"  {v}x {k}")
print(f"\nTotal removals: {len(removals)}, Total additions: {len(additions)}")

# Check which networks were removed but NOT re-added
removed_names = set()
for e in removals:
    msg = e["message"]
    if '"' in msg:
        name = msg.split('"')[1]
        removed_names.add(name)

added_names = set()
for e in additions:
    msg = e["message"]
    if '"' in msg:
        name = msg.split('"')[1]
        added_names.add(name)

missing = removed_names - added_names
if missing:
    print(f"\nNetworks REMOVED but NOT re-added ({len(missing)}):")
    for n in sorted(missing):
        print(f"  - {n}")
