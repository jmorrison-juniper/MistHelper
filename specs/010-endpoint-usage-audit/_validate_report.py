import json

# T028: Cross-validate sample findings against source
with open("MistHelper.py", encoding="utf-8") as f:
    lines = f.readlines()

# F-001: getSiteSettings typo at L42487
line_42487 = lines[42486]
assert "getSiteSettings" in line_42487, "F-001 FAIL"
print("F-001 OK: " + line_42487.strip()[:80])

# F-002: listSiteDevices at L9473 without get_all
line_9473 = lines[9472]
assert "listSiteDevices" in line_9473, "F-002 FAIL"
ctx = "".join(lines[9460:9490])
print("F-002 OK: listSiteDevices at L9473, get_all=" + str("get_all" in ctx))

# F-003: listOrgSites at L37611
line_37611 = lines[37610]
assert "listOrgSites" in line_37611, "F-003 FAIL"
print("F-003 OK: " + line_37611.strip()[:80])

# F-004: getOrgInventory near L38410
ctx2 = "".join(lines[38405:38415])
assert "getOrgInventory" in ctx2, "F-004 FAIL"
print("F-004 OK: getOrgInventory near L38410")

# F-005: listSiteDevicesStats at L31810 area
ctx3 = "".join(lines[31808:31818])
assert "listSiteDevicesStats" in ctx3, "F-005 FAIL"
has_type = "type=" in ctx3
print("F-005 OK: listSiteDevicesStats near L31810, type param=" + str(has_type))

# T029: Verify catalog counts
with open("specs/010-endpoint-usage-audit/catalog_misthelper.json") as f:
    mh = json.load(f)
with open("specs/010-endpoint-usage-audit/catalog_maps_manager.json") as f:
    mm = json.load(f)
with open("specs/010-endpoint-usage-audit/catalog_wsgi.json") as f:
    ws = json.load(f)

total_sites = len(mh) + len(mm) + len(ws)
unique_funcs = set()
for entry in mh + mm + ws:
    unique_funcs.add(entry["function"])

print()
print("Catalog totals: " + str(total_sites) + " call sites, " + str(len(unique_funcs)) + " unique functions")
assert total_sites == 370, "Total sites mismatch: " + str(total_sites)
assert len(unique_funcs) == 107, "Unique functions mismatch: " + str(len(unique_funcs))
print("T029: Catalog counts match report scope")

print()
print("=== POLISH VALIDATION PASSED ===")
