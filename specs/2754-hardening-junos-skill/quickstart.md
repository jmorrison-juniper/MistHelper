# Quickstart: Validate the Hardening Junos Skill

**Feature**: `docs/2754-hardening-junos-skill` | **Date**: 2026-09-16

This guide proves that the skill works. Run it after the implementation and before the pull
request. Each check gives a command and an expected result. A check that fails blocks the
merge.

The contracts hold the detail. Read `contracts/corpus-index.md` for the index schema. Read
`contracts/skill-interface.md` for the answer rules. Read `contracts/gap-register.md` for the
gap rows.

## Prerequisites

| Item | Value | Test |
| - | - | - |
| Worktree | `MistHelper-hardening-junos-skill` on branch `docs/2754-hardening-junos-skill` | `git branch --show-current` |
| Python | 3.13 or newer | `python --version` |
| Corpus root | `C:\Users\jmorrison\Downloads\juniper-doc-archives` | `Test-Path $env:JUNIPER_CORPUS_ROOT` |
| PDF library | `pdfplumber`, which `pyproject.toml` declares | `python -c "import importlib.metadata as m; print(m.version('pdfplumber'))"` |

Warning: `documentation/references/` is ignored by `.gitignore` line 28. A clone and a new
worktree do not hold it. Do not use it as a prerequisite, and do not cite it.

Set the corpus root once for the session.

```powershell
$env:JUNIPER_CORPUS_ROOT = 'C:\Users\jmorrison\Downloads\juniper-doc-archives'
$skill = '.github/skills/hardening-junos'
```

Warning: a check in this guide reads the corpus. It never writes to the corpus. Do not copy a
corpus file into the worktree.

## Group A: Structure and size

### V1. The writing gate

```powershell
python -m tools.ste_linter --min-score 80 @((Get-ChildItem $skill -Recurse -Filter *.md).FullName)
```

Expected: exit code 0. The command grades 5 Markdown files. Each file scores 80 or more. The
existing skills score 96 to 99, so a lower score points to a writing problem.

Warning: the linter returns exit code 2 when the file list holds the CSV file. Grade the
Markdown files only.

### V2. The total size

```powershell
'{0:N1} KB' -f ((Get-ChildItem $skill -Recurse -File | Measure-Object Length -Sum).Sum / 1KB)
```

Expected: 400.0 KB or less. The planned value is about 262 KB.

### V3. The file count and each file size

```powershell
Get-ChildItem $skill -Recurse -File | Select-Object Name, @{n='KB';e={[math]::Round($_.Length/1KB,1)}}
```

Expected: 6 files. `SKILL.md` is 12 KB or less. No file is more than 90 KB.

### V4. The folder width

```powershell
(Get-ChildItem "$skill/references").Count
```

Expected: 5 or less. The Five-Item Rule caps the folder at 5 children.

## Group B: The index

### V5. The row count and the column count

```powershell
python -c "import csv;r=list(csv.DictReader(open(r'.github/skills/hardening-junos/references/corpus-index.csv',encoding='utf-8',newline='')));print(len(r),len(r[0]),len({x['file'] for x in r}))"
```

Expected: `775 8 775`. The third number proves that each `file` value is unique.

### V6. No absolute path

```powershell
Select-String -Path "$skill/references/corpus-index.csv" -Pattern '[A-Za-z]:\\|^/|,/' | Measure-Object
```

Expected: `Count : 0`. FR-017 forbids an absolute path.

### V7. The citations resolve

```powershell
python -c "import csv,random,os;root=os.environ['JUNIPER_CORPUS_ROOT'];rows=list(csv.DictReader(open(r'.github/skills/hardening-junos/references/corpus-index.csv',encoding='utf-8',newline='')));random.seed(2754);s=random.sample(rows,50);print(sum(1 for x in s if os.path.exists(os.path.join(root,'markdown',DIR[x['archive']],x['file']+'.md'))))"
```

Expected: `50`. Build `DIR` from the archive code table in `references/corpus-operations.md`.
SC-006 allows 0 broken paths.

### V8. The index agrees with the conversion manifest

Compare each index row against `markdown/_conversion-manifest.json` at the corpus root.

Expected: 0 missing files. 0 page count mismatches. 0 rows below 200 characters for each page.
A mismatch means that the corpus changed after the index build. Rebuild the index.

## Group C: Content coverage

### V9. The STIG rules

```powershell
(Select-String -Path "$skill/references/stig-rules.md" -Pattern 'V-\d{6}' -AllMatches).Matches.Value | Sort-Object -Unique | Measure-Object
```

Expected: `Count : 181`. Then confirm the severity split of 25 high, 122 medium, and 34 low.

### V10. The baseline controls

```powershell
(Select-String -Path "$skill/references/baseline-controls.md" -Pattern '^\| C-\d{2}-\d{2} ').Count
```

Expected: `67`. Then confirm that each control holds one citation, and that each control with
a lockout risk holds a recovery step.

## Group D: Behavior

### V11. The corpus is absent

```powershell
$env:JUNIPER_CORPUS_ROOT = 'C:\no-such-corpus'
```

Ask the skill these 5 questions. Then restore the corpus root.

1. How do I protect the management plane of an EX switch?
2. How do I deny root login over SSH?
3. Which DISA STIG rule covers the login banner?
4. Where is the source document for the NTP control?
5. How do I protect the routing engine with a firewall filter?

Expected: 5 answers. Each answer gives the control, the command, the reason, and the citation.
Each answer states that the corpus is absent. 0 failures.

### V12. The commit guard

```powershell
git check-ignore -v "$env:JUNIPER_CORPUS_ROOT"
git diff --cached --stat
```

Expected: the first command names the `.gitignore` line that matches. The staged change holds
no PDF file, no file from `markdown/`, and no file from `extracted/`.

### V13. No citation of the ignored path

```powershell
Select-String -Path $skill -Recurse -Pattern 'documentation/references' | Measure-Object
```

Expected: `Count : 0`. `.gitignore` line 28 ignores that directory. A reader who clones the
repository does not receive it.

### V14. The Python gates for the converter

```powershell
ruff check scripts/pdf_to_markdown.py
black --check scripts/pdf_to_markdown.py
mypy scripts/pdf_to_markdown.py
python -m bandit -c pyproject.toml scripts/pdf_to_markdown.py
pytest tests/test_pdf_to_markdown.py --cov=scripts.pdf_to_markdown
```

Expected: 0 violations for each tool. Coverage is 80 percent or more. Section 7 of the plan
states the scope of the converter work.

### V15. The converter output satisfies the structural contract

Convert 30 sample PDF files with the upgraded script. Test each output against the contract
below.

| Test | Expected |
| - | - |
| Front matter | `source_file` and `pages` are present. Each other field is present when the PDF metadata gives it. |
| Page count | The `pages` value equals the page count of the source PDF. |
| Headings | The file holds at least 1 heading. It holds 6 headings or less before the first page marker. |
| Density | The text gives 200 characters or more for each page. |
| Glyphs | The file holds no ligature and no curly quotation mark. Each bullet glyph is a list item. |

Do not compare the output against the staged Markdown byte for byte. The staged corpus came
from PyMuPDF, and the committed converter uses `pdfplumber`. Two readers do not agree byte for
byte. A measurement of 400 staged files shows why the front matter test counts 2 required
fields and not 6: `source_file` and `pages` appear in 100 percent of the files, but `title`
appears in 87.8 percent and `author` in 68.0 percent.

When the converter passes its gates, rebuild the corpus with it. One reader then produces the
whole corpus. Measure the index row count again after the rebuild, because a different reader
moves a document across the 200 character floor. A measurement finds 11 documents near that
boundary.

## Group E: The user stories

### Story 1: An answer with its source

Ask 5 hardening questions that cover 5 different checklist sections. Confirm each answer
against the answer contract in `contracts/skill-interface.md`.

Expected: each answer holds the control, the command, the reason, and a citation that points
to a real file. A control that can remove access carries a warning and a recovery step.

### Story 2: A configuration review

Give the skill the sample configuration at
`extracted/TW_HardeningJunosDevices_2ndEd/AppendixB_MediumSecuritySampleConfig.rtf`.

Expected: 67 results. Each result is `pass`, `fail`, or `not-assessable`. Each `fail` gives a
STIG rule identifier and its severity, when a match exists. The report states that it is
advice and that it changed no device.

### Story 3: Find a source document

Ask for the source of 10 controls.

Expected: 10 relative paths below the corpus root. Each path exists. Then remove the corpus
root and repeat. The skill states that the corpus is absent and still answers.

### Story 4: Refresh the index

Follow the refresh procedure in `references/corpus-operations.md` for one new train.

Expected: the index records the new train for each superseded document. The row count stays at
one row for each document name. The gap register stays correct. The repository grows by 400 KB
or less.

## The audit of 30 documents

FR-034 and SC-008 require a manual audit. Select 10 documents from the security subset, 10
documents with many tables, and 10 documents with a complex cover page. Record a pass or a
fail for each of the 5 checks.

| Check | Question |
| - | - |
| Title | Does the front matter title match the document? |
| Page count | Does the `pages` value match the source PDF? |
| Headings | Does the file hold 6 headings or less before the first page marker? |
| Commands | Is the command text readable and in the correct order? |
| Tables | Is the table text readable? |

Expected: 27 documents or more pass all 5 checks, which is 90 percent.

Warning: the converter has a known weakness on a cover page. A measured example,
`DO_ContrailRHOSP.md`, holds 5 headings from cover text and one heading that breaks across two
lines. The audit must find this condition.

## Exit criteria

| Item | Target |
| - | - |
| Checks V1 to V15 | All pass |
| The 4 user stories | All pass |
| The audit of 30 documents | 27 or more pass |
| The release note | One fragment at `changelog.d/issue-2754-hardening-junos-skill.md` |
