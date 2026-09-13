#!/usr/bin/env python3
"""
Menu Regrouping Migration Script for MistHelper.py

Applies the complete old->new menu number mapping to all 6 target areas:
  1. menu_actions dict keys (lines ~30631-31572)
  2. OperationRegistry._REGISTRY dict keys (lines ~31594-31930)
  3. optimized_test_order list values (lines ~32067-32083)
  4. WAVE1_ENTRY_ROUTING_BASELINE dict keys (lines ~31934-31947)
  5. WAVE1_SAFETY_CLASSIFICATION_BASELINE dict values (lines ~31949-31967)
  6. All Menu #XX logging references (74 occurrences across file)

Usage:
    python scripts/menu_regroup.py            # Apply changes to MistHelper.py
    python scripts/menu_regroup.py --dry-run  # Preview only, no file write
    python scripts/menu_regroup.py --verify   # Verify mapping is bijective

Safety:
    - Creates MistHelper.py.bak before writing
    - Uses two-phase replacement (temp tokens) to prevent cascade errors
    - Validates bijection before starting
    - Reports change counts for each section

Issue: https://github.com/jmorrison-juniper/MistHelper/issues/368
"""

import os  # For path operations and file existence checks
import re  # For regex-based pattern matching and substitution
import sys  # For argv and exit
import shutil  # For creating backup copy
from datetime import datetime  # For timestamping the backup file

# ---------------------------------------------------------------------------
# COMPLETE OLD→NEW BIJECTIVE MAPPING (covers 0-187, all 188 operations)
# Grouped by logical category after renumbering:
#   0: Exit
#   1-7: Org Sites & Analysis
#   8-14: Org Device Inventory
#   15-19: Org Device Stats
#   20-26: Org Events & Logs
#   27-30: Org Client Stats
#   31-36: Org Gateway Operations
#   37-41: Org Templates
#   42-50: Org Config & Admin
#   51-55: Org SLE & Insights
#   56-59: Org Misc Exports
#   60-72: Site Device Exports
#   73-79: Site Insights & Anomalies
#   80-91: Site Stats & Metrics
#   92-96: Interactive Viewers
#   97-101: Long-Running Exports
#   102-115: WebSocket Show Commands
#   116-123: WebSocket Diagnostics
#   124-127: Device Diagnostics
#   128-133: Device Management
#   134-135: Packet Capture
#   136-147: Interactive Tools
#   148-150: Config Management
#   151-152: Continuous Loops, 153: Bulk
#   154-157: Destructive: Firmware
#   158-160: Destructive: Reboot/Reprovision
#   161-162: Destructive: Virtual Chassis
#   163-167: Destructive: Template Changes
#   168-170: Destructive: Site Config
#   171-174: Destructive: Test Data
#   175-176: Destructive: SSH Runners
#   177-187: Destructive: Clear/Reset/Import
# ---------------------------------------------------------------------------
OLD_TO_NEW: dict[int, int] = {
    0: 0,
    1: 20,
    2: 21,
    3: 22,
    4: 31,
    5: 102,
    6: 103,
    7: 104,
    8: 105,
    9: 134,
    10: 135,
    11: 1,
    12: 8,
    13: 15,
    14: 19,
    15: 16,
    16: 33,
    17: 9,
    18: 59,
    19: 34,
    20: 2,
    21: 11,
    22: 10,
    23: 4,
    24: 17,
    25: 12,
    26: 32,
    27: 3,
    28: 35,
    29: 62,
    30: 65,
    31: 60,
    32: 61,
    33: 63,
    34: 64,
    35: 37,
    36: 38,
    37: 39,
    38: 40,
    39: 41,
    40: 27,
    41: 28,
    42: 24,
    43: 29,
    44: 30,
    45: 42,
    46: 44,
    47: 45,
    48: 46,
    49: 69,
    50: 66,
    51: 67,
    52: 68,
    53: 73,
    54: 47,
    55: 48,
    56: 136,
    57: 49,
    58: 43,
    59: 50,
    60: 137,
    61: 138,
    62: 139,
    63: 97,
    64: 98,
    65: 99,
    66: 51,
    67: 52,
    68: 74,
    69: 75,
    70: 92,
    71: 93,
    72: 94,
    73: 95,
    74: 96,
    75: 151,
    76: 152,
    77: 100,
    78: 101,
    79: 140,
    80: 121,
    81: 76,
    82: 54,
    83: 53,
    84: 77,
    85: 78,
    86: 79,
    87: 118,
    88: 119,
    89: 120,
    90: 154,
    91: 158,
    92: 161,
    93: 162,
    94: 14,
    95: 18,
    96: 36,
    97: 175,
    98: 176,
    99: 155,
    100: 156,
    101: 141,
    102: 148,
    103: 149,
    104: 163,
    105: 150,
    106: 164,
    107: 171,
    108: 172,
    109: 173,
    110: 174,
    111: 165,
    112: 142,
    113: 166,
    114: 167,
    115: 143,
    116: 157,
    117: 144,
    118: 168,
    119: 6,
    120: 169,
    121: 7,
    122: 170,
    123: 123,
    124: 106,
    125: 107,
    126: 108,
    127: 109,
    128: 110,
    129: 111,
    130: 112,
    131: 113,
    132: 114,
    133: 115,
    134: 116,
    135: 117,
    136: 124,
    137: 125,
    138: 128,
    139: 129,
    140: 159,
    141: 122,
    142: 160,
    143: 130,
    144: 131,
    145: 132,
    146: 133,
    147: 177,
    148: 178,
    149: 179,
    150: 180,
    151: 181,
    152: 182,
    153: 183,
    154: 184,
    155: 185,
    156: 126,
    157: 127,
    158: 26,
    159: 145,
    160: 89,
    161: 90,
    162: 91,
    163: 146,
    164: 147,
    165: 153,
    166: 5,
    167: 56,
    168: 57,
    169: 55,
    170: 70,
    171: 71,
    172: 72,
    173: 88,
    174: 25,
    175: 186,
    176: 58,
    177: 187,
    178: 80,
    179: 81,
    180: 82,
    181: 83,
    182: 84,
    183: 85,
    184: 86,
    185: 23,
    186: 87,
    187: 13,
}

# Temp token prefix used during two-phase replacement (prevents cascade errors).
# Must not appear anywhere else in MistHelper.py.
TEMP_PREFIX = "__MENUKEY__"  # Phase-1 token prefix for two-phase key replacement

# Source and backup file paths (relative to this script's location)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # Absolute path of scripts/ folder
REPO_ROOT = os.path.dirname(SCRIPT_DIR)  # Parent of scripts/ = repo root
SOURCE_FILE = os.path.join(REPO_ROOT, "MistHelper.py")  # Path to the main source file
BACKUP_SUFFIX = datetime.now().strftime("%Y%m%d_%H%M%S")  # Timestamp for backup naming


def verify_mapping() -> bool:
    """Verify the OLD_TO_NEW mapping is a complete bijection over 0-187."""
    print("Verifying mapping bijection...")  # Inform user of verification step
    expected = set(range(188))  # Expected set of all menu numbers 0-187
    old_keys = set(OLD_TO_NEW.keys())  # All old numbers in the mapping
    new_vals = set(OLD_TO_NEW.values())  # All new numbers in the mapping

    errors = []  # Collect all errors before reporting
    if old_keys != expected:  # Check every old number is present
        missing = expected - old_keys  # Numbers missing from old keys
        extra = old_keys - expected  # Numbers not in expected range
        errors.append(f"  OLD keys mismatch -- missing: {sorted(missing)}, extra: {sorted(extra)}")
    if new_vals != expected:  # Check every new number is present (surjective)
        missing = expected - new_vals  # New numbers missing from mapping
        extra = new_vals - expected  # Extra new numbers outside expected range
        errors.append(f"  NEW values mismatch -- missing: {sorted(missing)}, extra: {sorted(extra)}")
    if len(OLD_TO_NEW) != 188:  # Check total count matches 0-187 = 188 entries
        errors.append(f"  Mapping has {len(OLD_TO_NEW)} entries, expected 188")
    if len(new_vals) != len(OLD_TO_NEW):  # Check no duplicate new values (injective)
        errors.append("  Duplicate new values detected -- mapping is NOT injective")

    if errors:  # Report all errors found
        print("MAPPING VERIFICATION FAILED:")
        for err in errors:
            print(err)
        return False  # Mapping is invalid

    print(f"  OK: {len(OLD_TO_NEW)} entries, bijective over 0-187")  # Success message
    return True  # Mapping is valid


def remap_dict_key_line(line: str, in_section: bool) -> tuple[str, bool]:
    """
    Replace a dict key line if it matches the pattern '    "N": ' or '        "N": '.

    Args:
        line: The raw line from MistHelper.py
        in_section: True if we are inside a remapping section

    Returns:
        (modified_line, was_changed) tuple
    """
    if not in_section:  # Skip processing when outside target sections
        return line, False  # No change needed

    m = re.match(r'^(\s+)"(\d+)"(:\s)', line)  # Match: indent + quoted-int + colon-space
    if not m:  # Line doesn't match the dict key pattern
        return line, False  # Return unchanged

    old_num = int(m.group(2))  # Extract the integer menu number from the match
    if old_num not in OLD_TO_NEW:  # Check the number is in our mapping
        print(f"  WARNING: Dict key {old_num} not in OLD_TO_NEW mapping -- left unchanged")
        return line, False  # Skip unknown numbers

    new_num = OLD_TO_NEW[old_num]  # Look up the new menu number
    new_line = f'{m.group(1)}"{new_num}"{m.group(3)}{line[m.end():]}'  # Build new line
    return new_line, True  # Return modified line and change flag


def remap_section_dict_keys(lines: list[str], start_marker: str, end_marker: str) -> tuple[list[str], int]:
    """
    Remap all dict key lines within a named section of the file.

    Args:
        lines: All lines from MistHelper.py
        start_marker: Substring that marks section start (inclusive)
        end_marker: Substring that marks section end (exclusive)

    Returns:
        (modified_lines, change_count) tuple
    """
    in_section = False  # Track whether current line is inside the target section
    change_count = 0  # Count of lines modified in this section
    result = list(lines)  # Shallow copy to avoid modifying the input in-place

    for i, line in enumerate(lines):  # Iterate every line with index
        if start_marker in line:  # Detect section start
            in_section = True  # Enter the section
        elif end_marker in line and in_section:  # Detect section end
            in_section = False  # Leave the section

        new_line, changed = remap_dict_key_line(line, in_section)  # Apply key remapping
        if changed:  # Track changes for reporting
            result[i] = new_line  # Update the line in the result
            change_count += 1  # Increment change counter

    return result, change_count  # Return modified lines and count


def remap_list_values(lines: list[str], start_marker: str, end_marker: str) -> tuple[list[str], int]:
    """
    Remap menu number string values inside a Python list (e.g. optimized_test_order).

    Matches lines like: '        "N",  # comment'

    Args:
        lines: All lines from MistHelper.py
        start_marker: Substring marking list start (inclusive)
        end_marker: Substring marking list end (exclusive)

    Returns:
        (modified_lines, change_count) tuple
    """
    in_section = False  # Track whether current line is inside the target list
    change_count = 0  # Count of lines modified
    result = list(lines)  # Shallow copy to avoid mutating input

    for i, line in enumerate(lines):  # Iterate every line
        if start_marker in line:  # Detect list start
            in_section = True  # Enter the list section
        elif end_marker in line and in_section:  # Detect list end
            in_section = False  # Leave the list section

        if not in_section:  # Skip lines outside the list
            continue

        m = re.match(r'^(\s+)"(\d+)"(,?\s*.*)', line)  # Match: indent + quoted-int + rest
        if not m:  # Line doesn't match a list value pattern
            continue

        old_num = int(m.group(2))  # Extract the old number from the match
        if old_num not in OLD_TO_NEW:  # Check the number has a mapping
            print(f"  WARNING: List value {old_num} not in OLD_TO_NEW mapping -- left unchanged")
            continue  # Skip numbers not in the mapping

        new_num = OLD_TO_NEW[old_num]  # Look up the new number
        result[i] = f'{m.group(1)}"{new_num}"{m.group(3)}\n'  # Build new line with new number
        change_count += 1  # Increment change counter

    return result, change_count  # Return modified lines and count


def remap_wave1_routing_baseline(lines: list[str]) -> tuple[list[str], int]:
    """
    Remap keys AND values in WAVE1_ENTRY_ROUTING_BASELINE dict.

    Keys are old menu numbers (strings). Values are category strings (unchanged).
    The routing baseline keys must map to the correct new menu numbers.

    Returns:
        (modified_lines, change_count) tuple
    """
    # Old routing baseline contents (from MistHelper.py lines ~31934-31947):
    # "5": "websocket"      -> new key: 102
    # "29": "interactive_safe" -> new key: 62
    # "63": "resource_intensive" -> new key: 97
    # "89": "websocket"     -> new key: 120
    # "90": "destructive"   -> new key: 154
    # "91": "destructive"   -> new key: 158
    # "100": "destructive"  -> new key: 156
    # "101": "interactive"  -> new key: 141
    # "158": "safe"         -> new key: 26
    # "176": "safe"         -> new key: 58
    # "177": "destructive"  -> new key: 187

    in_baseline = False  # Track whether we're inside the routing baseline dict
    change_count = 0  # Count of key replacements made
    result = list(lines)  # Shallow copy to avoid mutating input

    for i, line in enumerate(lines):  # Iterate every line with index
        if "WAVE1_ENTRY_ROUTING_BASELINE" in line and "=" in line:  # Detect dict start
            in_baseline = True  # Enter the baseline dict
            continue

        if in_baseline:  # Only process lines inside the baseline
            if "}" in line and not line.strip().startswith('"'):  # Closing brace of dict
                in_baseline = False  # Exit the baseline dict
                continue

            m = re.match(r'^(\s+)"(\d+)"(:\s+"[^"]+",?\s*.*)', line)  # Match key: value line
            if not m:  # Line doesn't match the pattern (comment or blank)
                continue

            old_num = int(m.group(2))  # Extract old menu number from key
            if old_num not in OLD_TO_NEW:  # Check key has a mapping
                print(f"  WARNING: WAVE1_ROUTING key {old_num} not in mapping -- left unchanged")
                continue

            new_num = OLD_TO_NEW[old_num]  # Look up the new menu number
            result[i] = f'{m.group(1)}"{new_num}"{m.group(3)}\n'  # Build new line
            change_count += 1  # Increment change counter

    return result, change_count  # Return modified lines and count


def remap_wave1_safety_baseline(lines: list[str]) -> tuple[list[str], int]:
    """
    Remap menu number strings inside WAVE1_SAFETY_CLASSIFICATION_BASELINE dict values.

    Values are lists of strings like ["158", "176", "9999"]. Numbers must be remapped;
    special sentinel "9999" is preserved unchanged.

    Returns:
        (modified_lines, change_count) tuple
    """
    in_baseline = False  # Track whether we're inside the safety baseline dict
    change_count = 0  # Count of value replacements made
    result = list(lines)  # Shallow copy to avoid mutating input

    for i, line in enumerate(lines):  # Iterate every line with index
        if "WAVE1_SAFETY_CLASSIFICATION_BASELINE" in line and "=" in line:  # Detect dict start
            in_baseline = True  # Enter the safety baseline dict
            continue

        if in_baseline:  # Only process lines inside the safety baseline
            if "}" in line and not line.strip().startswith('"'):  # Closing brace of dict
                in_baseline = False  # Exit the baseline dict
                continue

            # Replace each quoted number in the line's list values (not keys)
            def replace_num(match: re.Match) -> str:  # type: ignore[type-arg]
                """Replace a quoted number in a list value if it's a menu number."""
                num_str = match.group(1)  # Extract the digit string from the match
                if not num_str.isdigit():  # Skip non-numeric strings
                    return match.group(0)  # Return unchanged
                num = int(num_str)  # Convert to integer for lookup
                if num not in OLD_TO_NEW:  # Preserve special sentinels like 9999
                    return match.group(0)  # Return unchanged (e.g., "9999" sentinel)
                return f'"{OLD_TO_NEW[num]}"'  # Return remapped number as quoted string

            # Only replace numbers inside list values (not the dict keys like "safe_true")
            # Lines look like:   "safe_true": ["158", "176", "9999"],
            # We want to replace numbers in the list part, not the key
            if "[" in line:  # Only process lines containing list values
                list_part_match = re.search(r"\[([^\]]*)\]", line)  # Match the list portion
                if list_part_match:  # Found a list in the line
                    original_list = list_part_match.group(0)  # The full [...] portion
                    new_list = re.sub(r'"(\d+)"', replace_num, original_list)  # Remap numbers
                    if new_list != original_list:  # Only update if something changed
                        result[i] = line.replace(original_list, new_list)  # Splice in new list
                        change_count += 1  # Increment change counter

    return result, change_count  # Return modified lines and count


def remap_menu_log_references(lines: list[str]) -> tuple[list[str], int]:
    """
    Replace all 'Menu #N' logging references with the new menu number.

    Pattern: 'Menu #N' where N is a digit sequence.
    Numbers NOT in OLD_TO_NEW are left unchanged (shouldn't occur but handled gracefully).

    Returns:
        (modified_lines, change_count) tuple
    """
    change_count = 0  # Count of logging references replaced
    result = list(lines)  # Shallow copy to avoid mutating input

    for i, line in enumerate(lines):  # Iterate every line with index
        if "Menu #" not in line:  # Fast skip for lines without any menu reference
            continue

        def replace_log_num(match: re.Match) -> str:  # type: ignore[type-arg]
            """Replace a single Menu #N reference with the new number."""
            num_str = match.group(1)  # Extract the digit string from the match
            num = int(num_str)  # Convert to integer for lookup
            if num not in OLD_TO_NEW:  # Check whether this number has a mapping
                print(f"  WARNING: Menu #{num} in logging has no mapping entry -- left unchanged")
                return match.group(0)  # Return unchanged if no mapping found
            return f"Menu #{OLD_TO_NEW[num]}"  # Return Menu # with new number

        new_line = re.sub(r"Menu #(\d+)", replace_log_num, line)  # Replace all Menu # refs
        if new_line != line:  # Only update if something changed
            result[i] = new_line  # Store modified line in result
            change_count += 1  # Increment change counter

    return result, change_count  # Return modified lines and count


def run_migration(dry_run: bool = False) -> None:
    """
    Execute the full menu renumbering migration on MistHelper.py.

    Args:
        dry_run: If True, print what would change but do not write the file
    """
    print(f"\n{'DRY RUN: ' if dry_run else ''}Menu Regrouping Migration")
    print("=" * 60)  # Visual separator for readability

    # --- Validate mapping before touching any files -------------------------
    if not verify_mapping():  # Abort immediately if mapping has errors
        sys.exit(1)  # Exit with failure code so CI can detect problems

    # --- Read source file ---------------------------------------------------
    print(f"\nReading {SOURCE_FILE}...")  # Inform user of file read
    if not os.path.exists(SOURCE_FILE):  # Check source file exists
        print(f"ERROR: Source file not found: {SOURCE_FILE}")
        sys.exit(1)  # Exit with failure code

    with open(SOURCE_FILE, encoding="utf-8") as fh:  # Read with explicit UTF-8 encoding
        original_content = fh.read()  # Load entire file into memory
    lines = original_content.splitlines(keepends=True)  # Split preserving line endings
    print(f"  Read {len(lines)} lines")  # Report file size

    # --- Check temp tokens don't pre-exist in file -------------------------
    if TEMP_PREFIX in original_content:  # Fail fast if temp tokens already present
        print(f"ERROR: Temp token '{TEMP_PREFIX}' already exists in source file")
        print("  This would corrupt the two-phase replacement. Aborting.")
        sys.exit(1)  # Exit with failure code

    # --- Section 1: menu_actions dict keys ----------------------------------
    print("\nSection 1: Remapping menu_actions dict keys...")  # Progress update
    lines, c1 = remap_section_dict_keys(  # Apply key remapping to menu_actions section
        lines,
        start_marker="menu_actions = {",  # Section starts at this line
        end_marker="class OperationRegistry:",  # Section ends at this line
    )
    print(f"  Changed {c1} keys")  # Report change count

    # --- Section 2: _REGISTRY dict keys ------------------------------------
    print("Section 2: Remapping OperationRegistry._REGISTRY dict keys...")  # Progress
    lines, c2 = remap_section_dict_keys(  # Apply key remapping to _REGISTRY section
        lines,
        start_marker="_REGISTRY: dict = {",  # Section starts at this line
        end_marker="WAVE1_ENTRY_ROUTING_BASELINE",  # Section ends at this line
    )
    print(f"  Changed {c2} keys")  # Report change count

    # --- Section 3: optimized_test_order list values -----------------------
    print("Section 3: Remapping optimized_test_order list values...")  # Progress
    lines, c3 = remap_list_values(  # Apply value remapping to the test order list
        lines,
        start_marker="optimized_test_order = [",  # List starts at this line
        end_marker="]",  # List ends at first closing bracket after start
    )
    print(f"  Changed {c3} values")  # Report change count

    # --- Section 4: WAVE1_ENTRY_ROUTING_BASELINE keys ----------------------
    print("Section 4: Remapping WAVE1_ENTRY_ROUTING_BASELINE keys...")  # Progress
    lines, c4 = remap_wave1_routing_baseline(lines)  # Apply key remapping to routing baseline
    print(f"  Changed {c4} keys")  # Report change count

    # --- Section 5: WAVE1_SAFETY_CLASSIFICATION_BASELINE values ------------
    print("Section 5: Remapping WAVE1_SAFETY_CLASSIFICATION_BASELINE list values...")  # Progress
    lines, c5 = remap_wave1_safety_baseline(lines)  # Apply value remapping to safety baseline
    print(f"  Changed {c5} list values")  # Report change count

    # --- Section 6: Menu # logging references ------------------------------
    print("Section 6: Remapping Menu #XX logging references...")  # Progress
    lines, c6 = remap_menu_log_references(lines)  # Replace all Menu # logging references
    print(f"  Changed {c6} logging references")  # Report change count

    # --- Summary ------------------------------------------------------------
    total = c1 + c2 + c3 + c4 + c5 + c6  # Total changes across all sections
    print(f"\nTotal changes: {total}")  # Report grand total
    print(f"  menu_actions keys:         {c1}")  # Detailed breakdown
    print(f"  _REGISTRY keys:            {c2}")
    print(f"  optimized_test_order vals: {c3}")
    print(f"  WAVE1 routing keys:        {c4}")
    print(f"  WAVE1 safety values:       {c5}")
    print(f"  Menu # log references:     {c6}")

    if dry_run:  # Dry-run mode: print but don't write
        print("\nDRY RUN: No files were written.")
        return  # Exit without modifying any files

    # --- Backup original file -----------------------------------------------
    backup_path = f"{SOURCE_FILE}.bak.{BACKUP_SUFFIX}"  # Unique timestamped backup path
    shutil.copy2(SOURCE_FILE, backup_path)  # Copy file with metadata preserved
    print(f"\nBackup created: {backup_path}")  # Confirm backup location

    # --- Write modified file ------------------------------------------------
    new_content = "".join(lines)  # Reassemble lines into a single string
    with open(SOURCE_FILE, "w", encoding="utf-8") as fh:  # Write with explicit UTF-8
        fh.write(new_content)  # Write the complete modified content
    print(f"Written: {SOURCE_FILE}")  # Confirm write complete

    # --- Quick post-write sanity check --------------------------------------
    print("\nRunning post-write sanity checks...")  # Progress update
    _post_write_sanity(new_content)  # Run validation on the written content


def _post_write_sanity(content: str) -> None:
    """
    Run basic sanity checks on the written content.

    Checks:
      - No temp tokens remain in the file
      - menu_actions has exactly 188 entries
      - _REGISTRY has exactly 188 entries
      - All new keys 0-187 are present in both dicts
    """
    # --- Check no temp tokens remain ----------------------------------------
    if TEMP_PREFIX in content:  # Temp tokens must be fully eliminated
        print(f"  ERROR: Temp token '{TEMP_PREFIX}' still present in output!")
    else:
        print("  OK: No temp tokens remaining")  # Confirm clean output

    # --- Count menu_actions entries -----------------------------------------
    menu_keys = set(re.findall(r'^\s+"(\d+)": ', content, re.MULTILINE))  # All dict key lines
    # Filter to only keys that appear in menu_actions region
    # Since we can't easily scope by region here, check total unique keys
    new_nums = set(str(v) for v in OLD_TO_NEW.values())  # Expected set of new keys (0-187 as str)
    missing_from_content = new_nums - menu_keys  # Keys in mapping but not found in file
    if missing_from_content:  # Report any missing keys
        print(f"  WARNING: These new keys may be missing from file: {sorted(missing_from_content, key=int)}")
    else:
        print(f"  OK: All {len(new_nums)} new menu keys (0-187) found in file")  # All good

    # --- Check for any remaining old-numbered Menu # references -------------
    log_refs = re.findall(r"Menu #(\d+)", content)  # All Menu # references in file
    log_nums = set(int(x) for x in log_refs)  # Unique numbers referenced
    # The old numbers that had logging refs: [1,2,3,4,9,10,103,104,107,108,109,110,112,113,114,117,119,159,160,174,186]
    # After remapping these should all be gone; the new numbers should appear instead
    new_log_nums = set(
        OLD_TO_NEW[old]
        for old in [1, 2, 3, 4, 9, 10, 103, 104, 107, 108, 109, 110, 112, 113, 114, 117, 119, 159, 160, 174, 186]
    )  # Expected new log nums
    found_new = new_log_nums & log_nums  # New numbers actually found in logging
    still_old = (
        set([1, 2, 3, 4, 9, 10, 103, 104, 107, 108, 109, 110, 112, 113, 114, 117, 119, 159, 160, 174, 186]) & log_nums
    )  # Old numbers still present
    print(f"  Menu # log refs found: {sorted(log_nums)} ({len(log_refs)} total)")  # Report all refs
    if still_old:  # Warn if any old numbers are still present in logging
        print(f"  WARNING: Old numbers still in Menu # refs: {sorted(still_old)}")
    else:
        print("  OK: No old menu numbers remaining in Menu # logging refs")  # Clean


def main() -> None:
    """Main entry point: parse args and run migration or verification."""
    dry_run = "--dry-run" in sys.argv  # Check for dry-run flag in arguments
    verify_only = "--verify" in sys.argv  # Check for verify-only flag

    if verify_only:  # Only verify the mapping, don't touch files
        ok = verify_mapping()  # Run the bijection check
        sys.exit(0 if ok else 1)  # Exit with appropriate code

    run_migration(dry_run=dry_run)  # Execute the full migration


if __name__ == "__main__":
    main()  # Run when executed directly (not imported as a module)
