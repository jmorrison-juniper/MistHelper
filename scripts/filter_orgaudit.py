"""Filter orgaudit.json to remove noise entries (packet captures, logins, webshell, etc.)"""

import json  # Read/write the audit JSON payload
import os  # Portable path joining for cross-OS execution

source = os.path.join("data", "orgaudit.json")  # Input path under data/
output = os.path.join("data", "orgaudit-filtered.json")  # Filtered output path

with open(source, encoding="utf-8") as f:  # Load the raw audit dump
    data = json.load(f)  # Parse into a dict with a "results" list

noise_phrases = [  # Substrings that identify low-signal audit entries
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


def _matches_noise_phrase(msg):  # Helper: substring-based noise detector
    """Return True when ``msg`` contains any known noise substring."""
    # WHY: extracted so is_noise drops from CC 8 to <=5.
    return any(phrase in msg for phrase in noise_phrases)  # Any-match keeps CC flat


def _is_vpn_noise(msg, entry):  # Helper: VPN cascade-noise detector
    """Return True for VPN updates that omit a before/after diff."""
    # WHY: extracted so is_noise drops from CC 8 to <=5.
    return "Update VPN" in msg and "before" not in entry  # Missing "before" == cascade-only edit


def _is_device_adopt_noise(msg, entry):  # Helper: adopted:false cascade detector
    """Return True for device updates whose only change is adopted:false cascade noise."""
    # WHY: extracted so is_noise drops from CC 8 to <=5.
    if "Update Device" not in msg:  # Guard: only Update Device entries qualify
        return False  # Non-device entries never match this pattern
    before = entry.get("before", {})  # Pre-change device attributes
    after = entry.get("after", {})  # Post-change device attributes
    return before == {"adopted": False} and after == {"adopted": False}  # Both sides carry only the cascade flag


def is_noise(entry):  # Public predicate used by the filter list comprehension
    """Return True when the audit entry should be filtered out as noise."""
    msg = entry.get("message", "")  # Missing message defaults to empty string
    if _matches_noise_phrase(msg):  # Phrase-match noise (packet capture, login/logout, etc.)
        return True  # Phrase match short-circuits to noise
    if _is_vpn_noise(msg, entry):  # VPN update without before/after detail
        return True  # VPN cascade match short-circuits to noise
    if _is_device_adopt_noise(msg, entry):  # Device update whose only diff is adopted:false
        return True  # Adopted-flag cascade short-circuits to noise
    return False  # Retain the entry


filtered = [e for e in data["results"] if not is_noise(e)]  # Keep only signal entries
removed = len(data["results"]) - len(filtered)  # Count discarded entries for the summary

data["results"] = filtered  # Overwrite results with the filtered view
data["total"] = len(filtered)  # Keep the total field consistent

with open(output, "w", encoding="utf-8") as f:  # Persist the filtered dump
    json.dump(data, f, indent=2)  # Human-readable indentation

print(f"Original entries: {removed + len(filtered)}")  # Original count = kept + removed
print(f"Removed (noise): {removed}")  # How many entries were filtered out
print(f"Kept (config changes): {len(filtered)}")  # Remaining signal entries
print(f"Written to: {output}")  # Confirm the output path
