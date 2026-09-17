# Phase 1 Data Model: Hardening Junos Skill

**Feature**: `docs/2754-hardening-junos-skill` | **Date**: 2026-09-16

This file names each entity, its fields, and its rules. The skill holds no database. Each
entity is a row in a CSV file or an entry in a Markdown file.

## Entity map

| Entity | Where it lives | Count at delivery |
| - | - | - |
| Skill | `.github/skills/hardening-junos/` | 1 |
| Corpus root | A setting in `references/corpus-operations.md` | 1 |
| Index entry | A row in `references/corpus-index.csv` | 78 in the shipped index |
| Archive code | A row in the code table in `references/corpus-operations.md` | 165 |
| Topic group | A section in `references/baseline-controls.md` | 8 |
| Baseline control | An entry in `references/baseline-controls.md` | 67 |
| STIG rule | A row in `references/stig-rules.md` | 181 |
| Gap record | A row in the gap register in `references/corpus-operations.md` | 5 |
| Answer | The output of the skill | Not stored |

## Skill

The skill is the folder and its files.

| Field | Value | Rule |
| - | - | - |
| Name | `hardening-junos` | The folder name and the `name` field in the front matter must match. |
| Router file | `SKILL.md` | 12 KB or less, from FR-002. |
| Reference folder | `references/` | 5 children or less, from the Five-Item Rule. |
| File count | 6 | 10 or less, from FR-005. |
| Total size | Less than 400 KB | 400 KB or less, from FR-005. |
| Largest file | `corpus-index.csv`, 6.9 KB | 90 KB or less, from FR-006. |
| Snapshot date | `2026-09-16` | Each file states it, from FR-053. |

## Corpus root

| Field | Value | Rule |
| - | - | - |
| Default value | `C:\Users\jmorrison\Downloads\juniper-doc-archives` | FR-016 sets the default. |
| State | `present` or `absent` | The skill tests one known path. |
| Child folders | `markdown2/`, `extracted/`, `archives/` | The rebuild procedure recreates them. |
| Provenance files | `manifest.json`, `selection-inventory.csv`, `extraction-report.json`, `corpus-catalog.csv`, `corpus-catalog.json`, `markdown2/_conversion-manifest.json` | They stay outside the repository. |

State behavior:

- `present`: the skill gives the answer, the citation, and the path.
- `absent`: the skill gives the answer and the citation. It states that the file is absent. It
  does not fail.

## Index entry

One row for one unique document. The `contracts/corpus-index.md` file holds the full schema.

| Field | Type | Example | Rule |
| - | - | - | - |
| `file` | Text | `user-access` | The PDF file name without the extension. It is unique across the index. |
| `title` | Text | `Junos OS User Access and Authentication User Guide` | 70 characters or less. The value comes from the PDF metadata. |
| `group` | `G1` to `G8` | `G6` | Exactly one group, from FR-021. |
| `train` | Text | `26.2` or `-` | A Junos train or `-`. 46 rows hold a train. |
| `pages` | Integer | `1154` | 1 or more. The value must match the conversion manifest. |
| `archive` | `A001` to `A165` | `A006` | The code must exist in the code table. |
| `origin` | `f`, `t`, or `e` | `t` | The membership rule that admitted the row. |
| `gap` | `-`, `c`, or `s` | `-` | `c` marks a corrupt newer copy. `s` marks an earlier conversion. |

Rules:

- The index holds one row for each document name, from FR-036.
- The index holds no absolute path, from FR-017.
- A document below 200 characters for each page does not enter the index, from FR-027.
- The PDF path is `<archive>/<file>.pdf`.
- The Markdown path is `markdown2/<archive>/<file>.md`.

## Archive code

| Field | Type | Example | Rule |
| - | - | - | - |
| `code` | Text | `A006` | 4 characters. The letter `A` and 3 digits. |
| `directory` | Text | `extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262` | Relative to the corpus root. No absolute path. |
| `train` | Text | `26.2` or `-` | The train of the archive, when the archive is a train archive. |
| `url` | Text | A public Juniper download URL, or `-` | 162 of the 165 rows hold a URL. |

The code order follows the row count of each directory. `A001` holds the most rows. This keeps
the table stable across a refresh of the same corpus. The `url` column gives the durable
citation, which follows the runbook precedent.

## Topic group

The 8 groups match the 8 sections of the committed checklist.

| Code | Section | Checklist items | Index rows |
| - | - | - | - |
| `G1` | Administrative | 2 | About 54 |
| `G2` | Physical security | 9 | About 2 |
| `G3` | Network security | 10 | About 144 |
| `G4` | Management services security | 7 | About 183 |
| `G5` | Access security | 10 | About 88 |
| `G6` | User authentication security | 17 | About 271 |
| `G7` | Routing protocol security | 6 | About 9 |
| `G8` | Firewall filter | 6 | About 32 |

The group rule reads the file name first. It reads the title second. It assigns `G1` when
neither text matches. A measured run confirms that each group holds at least one row. The item counts sum to
67.

## Baseline control

One entry for one checklist item.

| Field | Type | Example | Rule |
| - | - | - | - |
| `id` | Text | `C-05-02` | The section number and the item number. |
| `section` | `G1` to `G8` | `G5` | One of the 8 groups. |
| `statement` | Text | `Deny root login over SSH.` | The control in one sentence. |
| `command` | Text | `set system services ssh root-login deny` | Junos configuration syntax. |
| `reason` | Text | `A shared root account hides the identity of the operator.` | 2 sentences or less. |
| `lockout_risk` | `yes` or `no` | `yes` | FR-050 requires the mark. |
| `recovery` | Text | `Keep one console session open. Use the console to roll back.` | Required when `lockout_risk` is `yes`. |
| `evidence` | Text | `show configuration system services ssh` | The command that proves the state. |
| `stig_rules` | List | `V-253910` | Zero or more STIG identifiers. |
| `source` | Text | `user-access.pdf, train 26.2, page 212` | The document, the train, and the page. |
| `source_url` | Text | A public Juniper or DISA URL | The durable citation. It must not name a path below `documentation/references/`. |

Rules:

- Each of the 67 controls holds at least one `source` value, from SC-002.
- Each control with `lockout_risk` set to `yes` holds a `recovery` value, from SC-013.
- A control states the platform, because the checklist covers MX, EX, and SRX.

## STIG rule

One row for one DISA rule.

| Field | Type | Example | Rule |
| - | - | - | - |
| `rule_id` | Text | `SV-253910r1000000_rule` | The identifier from the XCCDF file. |
| `group_id` | Text | `V-253910` | The group identifier from the XCCDF file. |
| `set` | `L2S`, `NDM`, or `RTR` | `NDM` | The rule set. The 3 sets hold 24, 55, and 102 rules. |
| `severity` | `high`, `medium`, or `low` | `medium` | 25 high, 122 medium, and 34 low. |
| `title` | Text | 140 characters or less | The rule title from the XCCDF file. |
| `check` | Text | One line | A condensed check. |
| `fix` | Text | One line | A condensed fix, with the Junos command when the rule gives one. |
| `section` | `G1` to `G8` or `-` | `G6` | The checklist section, when a match exists. |

Rules:

- All 181 rules appear, from SC-003.
- A rule with no Juniper source states that fact, from the edge case list.
- The reference states that the bundle covers the EX switch.

## Gap record

One row for one document that the skill cannot read from its newest train.

| Field | Type | Example |
| - | - | - |
| `document` | Text | `virtual-chassis-ex-8200.pdf` |
| `affected_trains` | List | `25.2, 25.4, 26.2` |
| `reason` | Text | `A zero run replaces the first 126,976 bytes. The page tree is gone.` |
| `fallback_train` | Text | `24.2` |
| `risk` | Text | `The answer can miss a change after train 24.2.` |

The register holds 2 corrupt document rows and 3 earlier conversion rows. The corrupt rows
cover 6 unreadable files, because each document fails in 3 trains.

## Answer

The skill produces an answer. The answer is not stored. The contract in
`contracts/skill-interface.md` states the required parts.

| Part | Required | Rule |
| - | - | - |
| Control | Yes | One sentence. |
| Junos command | Yes, for a configuration control | The command, the platform, and the train. |
| Reason | Yes | Why the control reduces risk. |
| Citation | Yes | The document, the train, and the path below the corpus root. |
| Lockout warning | When the control can remove access | The warning comes before the command. |
| Recovery step | When a lockout warning exists | One step that restores access. |
| Source area | When the answer comes from outside the security subset | A statement of that fact, from FR-009. |
| Gap statement | When the cited document is in the gap register | The gap and the fallback train, from FR-047. |
| Absent corpus statement | When the corpus root is absent | A statement that the file is absent. |
