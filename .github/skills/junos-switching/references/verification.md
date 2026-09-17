# Verification

This file tells a reader how to prove a switching claim, how to read the index,
and how this skill was built.

The verified snapshot date is 2026-09-17. The skill uses Junos train 26.2 source
files from the staged corpus.

## 1. Source selection

Use `references/corpus-index.csv` to select a source. Each row holds a Markdown
path relative to the corpus root.

| Subject | Preferred source | Reason |
| - | - | - |
| Ethernet switching, VLANs, private VLANs, and Q-in-Q. | `multicast-l2` | It is the Ethernet Switching User Guide. |
| Bridge domains and bridge MAC learning. | `bridging-learning` | It is the Layer 2 Bridging, Address Learning, and Forwarding User Guide. |
| Spanning tree. | `stp-l2` | It is the Spanning-Tree Protocols User Guide. |
| LAG and LACP. | `interfaces-ethernet-switches` | It is the switch interface guide and covers aggregated Ethernet interfaces. |
| MC-LAG concepts. | `mc-lag` | It is the Multichassis Link Aggregation guide. |
| Subscriber VLAN and Q-in-Q access patterns. | `subscriber-mgmt-vlan` | It covers stacked and flexible VLAN tagging. |
| Port security and DHCP security. | `security-services` | It covers MAC limiting, persistent MAC learning, DHCP snooping, and ARP inspection. |
| DHCP snooping behavior. | `dhcp` | It covers DHCP snooping as part of DHCP features. |
| Storm control command examples. | `evpn` | It gives storm control profile examples in the same Junos train. |

## 2. Corpus search that widened the manifest

The manifest supplied these documents:

- `subscriber-mgmt-vlan`
- `mc-lag`
- `stp-l2`
- `bridging-learning`

The build searched these folders:

- `markdown2\extracted\juniper-PDFs-junos-262\juniper-PDFs-junos-262`
- `markdown2\extracted\juniper-PDFs-junos-254\juniper-PDFs-junos-254`

The build added these documents beyond the manifest:

- `multicast-l2` for Ethernet switching, VLANs, private VLANs, and Q-in-Q.
- `interfaces-ethernet-switches` for switch interfaces, LAGs, and LACP.
- `security-services` for MAC limiting, persistent MAC learning, DHCP snooping, and dynamic ARP inspection.
- `dhcp` for DHCP snooping behavior and terminology.
- `evpn` for storm control profile command examples.

The 25.4 tree did not hold a better layer 2 switching guide during this search.
It mainly returned release notes for the searched terms.

## 3. Command evidence rules

Every command in the reference files came from a staged Markdown source. Do not
add a command unless one of these checks passes.

1. Search the source Markdown file for the exact command text.
2. Record the source file and page marker.
3. Keep the command hierarchy from the source.
4. If the source uses an edit hierarchy, state that context in the task text.
5. If no source confirms the command, mark the command unverified and omit it.

## 4. Confirmed command count

This skill confirms 110 unique Junos commands. The count includes each unique
`set`, `show`, and `clear` command that appears in backticks in the skill files.

| Reference | Unique count |
| - | -: |
| `bridge-vlan.md` | 36 |
| `stp-lag.md` | 38 |
| `port-security-qinq.md` | 40 |

The router and verification files repeat some of these commands. The combined
unique count across all skill files remains 110.

## 5. Index validation

Run this check from the repository root in the `MistHelper-2900-skills` worktree.
It proves that every index row resolves to a real Markdown file.

```powershell
python -c "import csv,pathlib; root=pathlib.Path(r'C:\Users\jmorrison\Downloads\juniper-doc-archives'); rows=list(csv.DictReader(open(r'.github\skills\junos-switching\references\corpus-index.csv', encoding='utf-8', newline=''))); missing=[r['file'] for r in rows if not (root / r['path']).exists()]; print(len(rows), 'rows', len(missing), 'missing'); raise SystemExit(1 if missing else 0)"
```

Expected result: `9 rows 0 missing`.

## 6. Writing and size checks

Run these checks from the repository root in the `MistHelper-2900-skills`
worktree.

```powershell
python -m tools.ste_linter --min-score 80 .github\skills\junos-switching\SKILL.md .github\skills\junos-switching\references\bridge-vlan.md .github\skills\junos-switching\references\stp-lag.md .github\skills\junos-switching\references\port-security-qinq.md .github\skills\junos-switching\references\verification.md
```

Expected result: each Markdown file scores 80 or more.

```powershell
python -c "from pathlib import Path; p=Path(r'.github\skills\junos-switching'); files=[x for x in p.rglob('*') if x.is_file()]; print(sum(x.stat().st_size for x in files), 'bytes'); print(len(list((p/'references').iterdir())), 'reference children')"
```

Expected result: the skill is below 409,600 bytes, and `references` has 5
children or fewer.

## 7. Answer validation checklist

Use this checklist before you answer a switching question.

1. Select one source from the index.
2. Confirm that the source train matches the answer.
3. Confirm that the command exists in the source.
4. Add a warning if the change touches spanning tree, native VLANs, storm control, or private VLAN isolation.
5. Give a verification command before a change command.
6. State any unverified assumption.

Warning: do not give a production switching change without a source and a
verification command. A wrong layer 2 command can interrupt many users.

## 8. Sources

The vendor text is not committed. The repository holds this distilled skill
instead.

| Source | Where |
| - | - |
| Skill entry point | `.github/skills/junos-switching/SKILL.md` |
| Bridge and VLAN reference | `.github/skills/junos-switching/references/bridge-vlan.md` |
| Spanning tree and LAG reference | `.github/skills/junos-switching/references/stp-lag.md` |
| Port security and Q-in-Q reference | `.github/skills/junos-switching/references/port-security-qinq.md` |
| Source index | `.github/skills/junos-switching/references/corpus-index.csv` |
