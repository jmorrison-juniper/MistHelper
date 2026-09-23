# Feature Specification: Required portal prompts for menus 235, 237, 238, 242, 247, 259, 260, and 262

## Problem

The Operations portal runs several menu rows without the answers that the CLI handler requires. The handler reads an empty input stream, aborts, and the portal can report a complete run that produced no useful result.

## Acceptance criteria

1. Menus 235, 259, and 260 show one required choice control.
2. Menus 237 and 262 show a required choice control, then a required `MSP ID` text control.
3. Menu 238 shows a required `MSP ID` text control.
4. Menu 242 shows a required `SSID` text control.
5. Menu 247 shows a required `Email Change Token` text control.
6. Menus 263 through 268 are command-line only until the portal can model prompts that depend on the chosen endpoint.
7. A guard test compares each chooser option list with its exporter source table.

## Out of scope

- Do not change handler code.
- Do not change menu rows owned by issues #3184 or #3226.
- Do not model the dynamic prompts for menus 263 through 268 in this repair.
