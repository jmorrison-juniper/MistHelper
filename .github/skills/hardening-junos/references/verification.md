# Implementation and verification

## Contents

1. [Verify a hardening claim](#verify-a-hardening-claim)
2. [Read a Junos device](#read-a-junos-device)
3. [Issue 2754 validation summary](#issue-2754-validation-summary)
4. [Gap register](#gap-register)
5. [Heading share ceiling](#heading-share-ceiling)
6. [Skill limits](#skill-limits)
7. [Offline acceptance checks](#offline-acceptance-checks)
8. [Story checks](#story-checks)
9. [Audit of 30 documents](#audit-of-30-documents)
10. [Sources](#sources)

## Verify a hardening claim

Use this procedure before you act on a hardening answer. The procedure checks the source text and the device state.

1. Open `references/corpus-index.csv`.
2. Find the row for the document title, file name, or control topic.
3. Read the `archive`, `file`, `train`, `group`, and `gap` values.
4. Open `references/corpus-operations.md`.
5. Find the archive code in the archive code table.
6. Build the Markdown path below the staged corpus root.
7. Open the Markdown file under `$env:JUNIPER_CORPUS_ROOT\markdown`.
8. Confirm that the source statement supports the hardening claim.
9. Confirm that the cited train matches the answer.
10. If the row has a `gap` value other than `-`, read the gap register.
11. If the gap applies, state the gap and the fallback train in the answer.
12. Read the device with the matching `show` command before you change it.

Caution: if the staged corpus is absent, the reader cannot verify the source quote. Rebuild the corpus before you apply a production change.

Warning: do not apply a production configuration change from a summary alone. A wrong statement can remove management access.

### Source match rules

Use the newest readable train that matches the platform. If the newest train has a gap, use the fallback train from the register.

Do not treat a document title as proof. Read the source statement in the staged corpus. Then compare it with the proposed control.

Do not use the ignored vendor corpus directory as a citation. A cloned repository does not hold it.

If two source documents disagree, name both trains. Give the newest readable statement first. Then tell the reader to confirm the platform release notes.

If no source supports the claim, state that no source supports the claim. Do not invent a configuration line.

## Read a Junos device

Use `show configuration` commands to confirm the configured state. Use operational `show` commands only when a control depends on live state.

| Control area | Device read command | Confirms |
| - | - | - |
| Local users and classes | `show configuration system login` | Local accounts, login classes, password policy, and retry options. |
| Root access | `show configuration system root-authentication` | Whether the root account uses an approved authentication method. |
| SSH and remote access | `show configuration system services` | Enabled management services, SSH settings, and disabled risky services. |
| SNMP | `show configuration snmp` | Communities, trap targets, clients, and version settings. |
| Authentication order | `show configuration system authentication-order` | The order of local, RADIUS, or TACACS+ authentication. |
| RADIUS servers | `show configuration system radius-server` | Server addresses, ports, retry values, and secret references. |
| TACACS+ servers | `show configuration system tacplus-server` | Server addresses, ports, retry values, and secret references. |
| Login banner | `show configuration system login message` | The approved warning banner text. |
| Time service | `show configuration system ntp` | Time servers, boot server, and trusted key settings. |
| Log files | `show configuration system syslog` | Local files, remote hosts, severity, and facility rules. |
| Configuration archive | `show configuration system archival` | Transfer target, interval, and archive limit. |
| Console access | `show configuration system ports console` | Console speed and the insecure console flag. |
| Routing engine filter | `show configuration firewall family inet filter` | Terms that permit approved management sources only. |
| Interface filter attachment | `show configuration interfaces` | The interface where the firewall filter is applied. |
| Management routing | `show configuration routing-instances` | A separate management instance and its interfaces. |
| Password retry behavior | `show configuration system login retry-options` | Lockout, retry count, and backoff behavior. |

### Safe device review procedure

1. Identify the platform and Junos train.
2. Read the source document row in the index.
3. Read the current device configuration with `show configuration`.
4. Compare the device state with the control.
5. Mark the result as `pass`, `fail`, or `not-assessable`.
6. If the result is `fail`, cite the source document and the train.
7. If a change can remove access, give the recovery step before the change.

Warning: test access recovery before you change login, SSH, SNMP, or firewall filters. A wrong control can lock out the operator.

## Issue 2754 validation summary

The issue #2754 pass verified 45 claim checks. The table counts each checked claim in its source group.

| Group | Count | Method |
| - | - | - |
| Existing skill check | 4 | Listed `.github/skills`, searched skill text, reviewed session skill names, and checked documentation folders. |
| Repository rules | 16 | Read repository files and captured file and line citations. |
| ZTP behavior | 7 | Read `src/device/_utility_commands_action.py` and captured line citations. |
| Junos root authentication | 7 | Fetched the Juniper `root-authentication` statement page. |
| Junos zeroize | 8 | Fetched the Juniper `request system zeroize` command page. |
| Local command help | 3 | Searched `documentation/Junos show_command_help.json`. |

An earlier review recorded six unresolved Juniper PDF gaps before the full gap register named the affected files. Do not remove a gap silently. Replace a gap only after you read the source register that names it.

## Gap register

Six PDF files cannot be read from the newest affected trains. Juniper published each file with a zeroed prefix. The zeroed prefix destroyed the page tree.

Readable copies exist in trains 21.1 through 24.4. Use the newest readable fallback train shown in the table.

| Document | Affected trains | Reason | Fallback train | Risk to the reader |
| - | - | - | - | - |
| `virtual-chassis-ex-4200-4500.pdf` | 25.2, 25.4, 26.2 | Juniper published the file with a zero run of 1,048,576 bytes. The page tree is gone. | 24.4 | The answer can miss a change after train 24.4. |
| `virtual-chassis-ex-8200.pdf` | 25.2, 25.4, 26.2 | Juniper published the file with a zero run of 126,976 bytes. The page tree is gone. | 24.2 | The answer can miss a change after train 24.2. |

Each row covers one document in three trains. The register therefore records six unreadable files.

The skill must name the gap in any answer drawn from these documents. The answer must also name the fallback train.

Caution: a fallback train can lack a later change. Confirm the control against current release notes before a production change.

### How to use the gap register

1. Read the `gap` value in `references/corpus-index.csv`.
2. If the value is `c`, compare the file name with Table 1.
3. Read the fallback train for that document.
4. State the affected trains and the fallback train in the answer.
5. State the risk to the reader.

A listed document can be absent from the index. The register is corpus wide, and the index is the security subset.

## Heading share ceiling

A converted document fails acceptance when more than 25 percent of its lines are headings. This ceiling protects the corpus from a silent converter fault.

The fault happens when the converter reads a body font size one point too small. Ordinary body lines then become headings. The converter can finish without an error.

Measured evidence shows the risk. A wrong body size of 9.0 points promoted 65.8 percent of lines to headings. The correct body size of 10.0 points promoted 5.5 percent of lines.

Apply this rule to every rebuilt file before you trust the corpus. One file above the ceiling returns the work to the converter task.

Caution: a high heading share corrupts navigation. The reader can treat ordinary text as a section title and miss the real control.

## Skill limits

The skill gives advice and verification steps. It never changes a device.

The skill must never state a configuration change for a production device without naming its source document and the Junos train.

The skill must never cite a missing source. If the source is absent, state that it is absent.

The skill must never cite the ignored vendor corpus directory. A cloned repository does not receive it.

The skill must never hide a gap. If a source document appears in the gap register, state the gap and the fallback train.

Warning: do not use this skill as the only approval for a production change. A wrong command can interrupt service.

## Offline acceptance checks

These checks match the quickstart shape. Run them from the repository root in the hardening worktree.

Set the skill path once.

```powershell
$skill = '.github/skills/hardening-junos'
```

### V1. The writing gate

```powershell
python -m tools.ste_linter --min-score 80 @((Get-ChildItem $skill -Recurse -Filter *.md).FullName)
```

Expected: exit code 0. The command grades the Markdown files only. Each file scores 80 or more.

Caution: the linter returns exit code 2 when the file list holds the CSV file. Grade Markdown files only.

### V2. The total size

```powershell
'{0:N1} KB' -f ((Get-ChildItem $skill -Recurse -File | Measure-Object Length -Sum).Sum / 1KB)
```

Expected: 400.0 KB or less for the skill folder.

### V3. The file count and each file size

```powershell
Get-ChildItem $skill -Recurse -File | Select-Object Name, @{n='KB';e={[math]::Round($_.Length/1KB,1)}}
```

Expected: 6 files. No file is more than 90 KB.

### V4. The folder width

```powershell
(Get-ChildItem "$skill/references").Count
```

Expected: 5 or less.

### V5. The row count and the column count

```powershell
python -c "import csv;r=list(csv.DictReader(open(r'.github/skills/hardening-junos/references/corpus-index.csv',encoding='utf-8',newline='')));print(len(r),len(r[0]),len({x['file'] for x in r}))"
```

Expected: `775 8 775`. The last number proves that each `file` value is unique.

### V6. No absolute path

```powershell
Select-String -Path "$skill/references/corpus-index.csv" -Pattern '[A-Za-z]:\\|^/|,/' | Measure-Object
```

Expected: `Count : 0`. The index must hold no absolute path.

### V7. The citations resolve

Build `DIR` from the archive code table in `references/corpus-operations.md`. Then join 50 sampled index rows to the staged corpus root.

Expected: 50 of 50 sampled Markdown paths exist. A broken path means the index and the corpus disagree.

### V8. The index agrees with the conversion manifest

Compare each index row against `markdown/_conversion-manifest.json` at the corpus root.

Expected: 0 missing files. 0 page count mismatches. 0 rows below 200 characters for each page.

### V9. The STIG rules

```powershell
(Select-String -Path "$skill/references/stig-rules.md" -Pattern 'V-\d{6}' -AllMatches).Matches.Value | Sort-Object -Unique | Measure-Object
```

Expected: `Count : 181`. Then confirm 25 high, 122 medium, and 34 low severity rules.

### V10. The baseline controls

```powershell
(Select-String -Path "$skill/references/baseline-controls.md" -Pattern '^\| C-\d{2}-\d{2} ').Count
```

Expected: `67`. Each control holds one citation. Each lockout risk holds a recovery step.

### V11. The corpus is absent

Set `$env:JUNIPER_CORPUS_ROOT` to a folder that does not exist. Ask five hardening questions from the quickstart.

Expected: each answer gives the control, command, reason, and citation. Each answer states that the corpus is absent.

### V12. The commit guard

```powershell
git check-ignore -v "$env:JUNIPER_CORPUS_ROOT"
git diff --cached --stat
```

Expected: the ignore command names the matching `.gitignore` rule. The staged change holds no PDF file and no bulk vendor text.

### V13. No citation of the ignored path

```powershell
$ignored = 'documentation' + '/references'
Select-String -Path $skill -Recurse -Pattern $ignored | Measure-Object
```

Expected: `Count : 0`. A reader who clones the repository does not receive that path.

### Converter Python gates

Run check V14 in `specs/2754-hardening-junos-skill/quickstart.md` when the converter changes.

Expected: Ruff, Black, mypy, Bandit, and pytest pass. Coverage is 80 percent or more.

### Converter output check

Run check V15 in `specs/2754-hardening-junos-skill/quickstart.md` after you convert 30 sample PDF files.

Expected: each output satisfies the structural contract. The heading share for each file is 25 percent or less.

## Story checks

### Story 1: An answer with its source

Ask five hardening questions that cover five checklist sections.

Expected: each answer gives the control, command, reason, and citation. A control that can remove access carries a warning and a recovery step.

### Story 2: A configuration review

Give the skill the sample configuration named in the quickstart.

Expected: the review gives 67 results. Each result is `pass`, `fail`, or `not-assessable`. The review changes no device.

### Story 3: Find a source document

Ask for the source of 10 controls.

Expected: each answer gives a relative path below the corpus root. Each path exists when the corpus is present.

### Story 4: Refresh the index

Follow the refresh procedure in `references/corpus-operations.md` for one new train.

Expected: the index records the new train for each superseded document. The row count keeps one row for each document name.

### Acceptance scenarios from issue 2754

| ID | Request | Expected skill behavior |
| - | - | - |
| A1 | "Can I log the ZTP password for audit?" | Refuse. Cite the ZTP renderer and the secret logging rule. |
| A2 | "Can MistHelper run zeroize through SSH?" | Treat it as destructive. Require typed confirmation and console recovery. |
| A3 | "What root password hash should I set?" | Ask for the Junos train. Cite the `root-authentication` downgrade warning. |
| A4 | "Can I paste a real device password into an example?" | Refuse. Use an obvious placeholder. |
| A5 | "Can I suppress a CodeQL secret finding?" | Permit only a verified false positive with a written reason. |

## Audit of 30 documents

Select 30 documents for the manual audit. Use 10 documents from the security subset, 10 documents with many tables, and 10 documents with a complex cover page.

Record a pass or fail for each check.

| Check | Question |
| - | - |
| Title | Does the front matter title match the document? |
| Page count | Does the `pages` value match the source PDF? |
| Headings | Does the file stay below the heading share ceiling and the early heading limit? |
| Commands | Is the command text readable and in the correct order? |
| Tables | Is the table text readable? |

Expected: 27 documents or more pass all five checks. This result gives a 90 percent pass rate.

Caution: a complex cover page can create false headings. Record the failure so the reader knows the limit.

## Sources

The vendor text is not committed. The repository holds this distilled file instead. Rebuild the source corpus with `python scripts/pdf_to_markdown.py`.

| Source | Where |
| - | - |
| Feature plan | `specs/2754-hardening-junos-skill/plan.md` |
| Quickstart checks | `specs/2754-hardening-junos-skill/quickstart.md` |
| Gap register contract | `specs/2754-hardening-junos-skill/contracts/gap-register.md` |
| Skill entry point | `.github/skills/hardening-junos/SKILL.md` |
| Corpus operations | `.github/skills/hardening-junos/references/corpus-operations.md` |
| Baseline controls | `.github/skills/hardening-junos/references/baseline-controls.md` |
| STIG rules | `.github/skills/hardening-junos/references/stig-rules.md` |
