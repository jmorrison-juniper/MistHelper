# Verification

This reference tells a reader how to verify a JSA claim, find a source document,
and test this skill offline.

The verified snapshot date is 2026-09-17.

## 1. Verify a JSA claim

### Task: check a procedure, command, or query

1. Open `references/corpus-index.csv`.
2. Find the row for the title, file name, or topic.
3. Read the `release`, `pages`, and `path` values.
4. Join the corpus root with the `path` value.
5. Open the Markdown file under the staged corpus root.
6. Confirm that the source text supports the claim.
7. If the claim is a command or query, compare each token with the source.
8. If the claim changes retention, a rule, or a log source, add a warning.
9. Cite the source document and release in the answer.

The corpus root is `C:\Users\jmorrison\Downloads\juniper-doc-archives\`.

Caution: if the corpus root is absent, the reader cannot verify new source text.
Use only the curated reference files until the corpus returns.

## 2. Source match rules

Use the newest readable source for the same product and task.

1. Use JSA 7.4.2 for current JSA procedures in this skill.
2. Use STRM only when the user asks about STRM or an older deployment.
3. Use JATP only when the user asks about JATP or a JATP SIEM connector.
4. Use release notes only when a version-specific behavior matters.
5. If no source supports a claim, state that no source supports it.

Do not invent a command, an AQL query, a URL, a menu path, or a procedure step.

## 3. Confirmed command and procedure register

The build confirmed 29 commands, queries, URLs, and procedures in the staged corpus.

| ID | Kind | Source | Release |
| - | - | - | - |
| P01 | DSM install command | JSA-DSM | JSA 7.4.2 |
| P02 | Add a DSM | JSA-DSM | JSA 7.4.2 |
| P03 | Add one log source | JSA-DSM | JSA 7.4.2 |
| P04 | Set parser order | JSA-DSM | JSA 7.4.2 |
| P05 | Test a log source | JSA-DSM | JSA 7.4.2 |
| P06 | Add a log source extension | JSA-DSM | JSA 7.4.2 |
| P07 | Repair unknown events | JSA-DSM | JSA 7.4.2 |
| P08 | AQL clause order | JSA-AQL | JSA 7.4.2 |
| P09 | `SELECT * FROM events LAST 10 MINUTES` | JSA-AQL | JSA 7.4.2 |
| P10 | `INCIDR` event query | JSA-AQL | JSA 7.4.2 |
| P11 | Health AQL query | JSA-AQL | JSA 7.4.2 |
| P12 | EPS by log source AQL query | JSA-AQL | JSA 7.4.2 |
| P13 | Local-to-remote flow AQL query | JSA-AQL | JSA 7.4.2 |
| P14 | Save a search | JSA-UG | JSA 7.4.2 |
| P15 | Use a quick filter | JSA-UG | JSA 7.4.2 |
| P16 | Investigate offense events | JSA-UG | JSA 7.4.2 |
| P17 | Investigate offense flows | JSA-UG | JSA 7.4.2 |
| P18 | Hide an offense | JSA-UG | JSA 7.4.2 |
| P19 | Show a hidden offense | JSA-UG | JSA 7.4.2 |
| P20 | Edit a building block | JSA-UG | JSA 7.4.2 |
| P21 | Create a custom report | JSA-UG | JSA 7.4.2 |
| P22 | Schedule a nightly backup | JSA-AD | JSA 7.4.2 |
| P23 | On-demand configuration backup | JSA-AD | JSA 7.4.2 |
| P24 | Deployment health dashboard | JSA-AD | JSA 7.4.2 |
| P25 | Configure an external flow source | JSA-AD | JSA 7.4.2 |
| P26 | Set a Data Node to Archive mode | JSA-AD | JSA 7.4.2 |
| P27 | SRX PCAP commands and JSA log source | JSA-PCAP | JSA 7.4.2 |
| P28 | JATP SIEM connector | JATP-SIEM | JATP 2018 |
| P29 | JATP event and incident URLs | JATP-SIEM | JATP 2018 |

## 4. Offline acceptance checks

Run these checks from the target worktree root.

Set the skill path once.

```powershell
$skill = '.github/skills/juniper-security-analytics'
```

### V1. Writing gate

```powershell
python -m tools.ste_linter --min-score 80 @((Get-ChildItem $skill -Recurse -Filter *.md).FullName)
```

Expected: exit code 0. Each Markdown file scores 80 or more.

### V2. Total size

```powershell
'{0:N1} KB' -f ((Get-ChildItem $skill -Recurse -File | Measure-Object Length -Sum).Sum / 1KB)
```

Expected: 400.0 KB or less.

### V3. Folder width

```powershell
(Get-ChildItem "$skill\references").Count
```

Expected: 5 or less.

### V4. Index shape

```powershell
python -c "import csv; rows=list(csv.DictReader(open(r'.github/skills/juniper-security-analytics/references/corpus-index.csv', encoding='utf-8', newline=''))); print(len(rows), len(rows[0]), len({row['file'] for row in rows}))"
```

Expected: `225 6 225`.

### V5. Index path resolution

```powershell
python -c "import csv, pathlib; root=pathlib.Path(r'C:\Users\jmorrison\Downloads\juniper-doc-archives'); rows=list(csv.DictReader(open(r'.github/skills/juniper-security-analytics/references/corpus-index.csv', encoding='utf-8', newline=''))); missing=[row['path'] for row in rows if not (root / row['path']).exists()]; print(len(rows), len(missing))"
```

Expected: `225 0`.

### V6. No ignored citation path

```powershell
$blocked = 'documentation' + '/references'; Select-String -Path $skill -Recurse -Pattern $blocked | Measure-Object
```

Expected: `Count : 0`.

## 5. Skill limits

This skill gives advice and verification steps. It never changes a live JSA,
STRM, or JATP system.

The skill must never give a production change without a source document and release.
The skill must never cite the ignored vendor reference directory.
The skill must never copy long vendor text.
The skill must never hide a risk from retention, rule, log source, backup, or upgrade work.

Warning: do not use this skill as the only approval for a production change. A
wrong change can delete evidence or hide an attack.

## 6. Sources

| Source | Local path below the corpus root |
| - | - |
| JSA-DP | `markdown2/extracted/jsa-doc-archives-7.4.2/jsa-deployment-7.4.2.md` |
| JSA-AD | `markdown2/extracted/jsa-doc-archives-7.4.2/jsa-admin-guide-7.4.2.md` |
| JSA-UG | `markdown2/extracted/jsa-doc-archives-7.4.2/jsa-user-guide-7.4.2.md` |
| JSA-DSM | `markdown2/extracted/jsa-doc-archives-7.4.2/jsa-dsm-7.4.2.md` |
| JSA-AQL | `markdown2/extracted/jsa-doc-archives-7.4.2/jsa-aql-7.4.2.md` |
| JSA-TUNE | `markdown2/extracted/jsa-doc-archives-7.4.2/jsa-tuning.md` |
| JSA-PCAP | `markdown2/extracted/jsa-doc-archives-7.4.2/jsa-juniper-pcap.md` |
| JSA-UP | `markdown2/extracted/jsa-doc-archives-7.4.2/jsa-upgrade.md` |
| JATP-SIEM | `markdown2/extracted/jatp-doc-archives/jatp-cef-leef-and-syslog-support.md` |
| JATP-OP | `markdown2/extracted/jatp-doc-archives/jatp-operators-guide.md` |

