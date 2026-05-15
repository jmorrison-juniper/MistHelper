"""Filter orgaudit.json to remove noise entries (packet captures, logins, webshell, etc.)"""
import json
import os

source = os.path.join("data", "orgaudit.json")
output = os.path.join("data", "orgaudit-filtered.json")

with open(source, encoding="utf-8") as f:
    data = json.load(f)

noise_phrases = [
    "Accessed Org",
    "Accessed by Mist Support",
    "Packet Capture started",
    "Packet Capture stopped",
    "Invoked Webshell",
    "Clearing sessions",
    "Login ",
    "Logout ",
    "manually restarted",
    "Getting device",
]


def is_noise(entry):
    msg = entry.get("message", "")
    for phrase in noise_phrases:
        if phrase in msg:
            return True
    # VPN updates without before/after detail
    if "Update VPN" in msg and "before" not in entry:
        return True
    # Device updates with ONLY adopted:false (cascade noise from profile changes)
    if "Update Device" in msg:
        before = entry.get("before", {})
        after = entry.get("after", {})
        if before == {"adopted": False} and after == {"adopted": False}:
            return True
    return False


filtered = [e for e in data["results"] if not is_noise(e)]
removed = len(data["results"]) - len(filtered)

data["results"] = filtered
data["total"] = len(filtered)

with open(output, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print(f"Original entries: {removed + len(filtered)}")
print(f"Removed (noise): {removed}")
print(f"Kept (config changes): {len(filtered)}")
print(f"Written to: {output}")
