---

description: "Task list for the hardening-junos skill"
---

# Tasks: Hardening Junos Skill

**Feature**: `docs/2754-hardening-junos-skill` | **Issue**: #2754 | **Date**: 2026-09-16

**Input**: Design documents from `specs/2754-hardening-junos-skill/`

**Prerequisites**: `spec.md` (commit `ca35cf5a`), `plan.md` (commit `baae363c`), `research.md`,
`data-model.md`, `quickstart.md`, and the 3 files in `contracts/`.

**Tests**: The specification asks for no test-first work on the skill documentation. The plan
requires one test file, `tests/test_pdf_to_markdown.py`, because section 7 adds Python code to
the deliverable. T009 writes that test before the code, because `quickstart.md` check V15
already states the full output contract. T019 and T020 then add one named acceptance test for
each defect that the prototype found.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel. It touches a different file, and it waits for no
  unfinished task.
- **[Story]**: The user story that the task serves. A Setup, Foundational, or Polish task
  carries no story label.
- Each task names the exact file that it touches.
- Each task carries a `Verify:` line. Run that command. A task is done when the command gives
  the stated result.
- Tick a task only after you verify the delivered file. Add an evidence note in this form:
  `(delivered: path/to/file.py)`.
- If a task needs a live system or a human decision, keep the box unchecked and explain the
  condition in the task text.

## Session setup

Run these two lines once for each session. Every `Verify:` line below uses them.

```powershell
$env:JUNIPER_CORPUS_ROOT = 'C:\Users\jmorrison\Downloads\juniper-doc-archives'
$skill = '.github/skills/hardening-junos'
```

## The required order

The plan states one order. The task list holds it. Do not reorder these three blocks.

| Step | Block | Tasks | Why the order is fixed |
| - | - | - | - |
| 1 | Upgrade and gate the converter | T009 to T023 | The staged corpus came from PyMuPDF. The committed converter must produce the corpus, because `.gitignore` promises that command. |
| 2 | Rebuild the corpus | T024 to T027 | One reader must produce the whole corpus. `pdfplumber` gives a different character count than PyMuPDF. T025 gates the rebuild on the heading share before any later step trusts the output. |
| 3 | Build the index | T028 to T030 | The index membership depends on the rebuilt character count, so the row count is not known until step 2 ends. |

T026 is the re-measure step. It runs after the rebuild and before the index build. The planned
row count is 775. A rebuild can move the count to a value between 767 and 778.

- 8 indexed documents sit between 200 and 250 characters for each page. Each one can fall
  below the floor and leave the index.
- 3 excluded documents sit between 150 and 200 characters for each page. Each one can rise
  above the floor and enter the index.

T027 records the measured count in `plan.md`, `contracts/corpus-index.md`, and `quickstart.md`.
Every later count check reads the recorded value, not the number 775.

## Closed unknowns

A person built a working `pdfplumber` prototype on 2026-09-16 and ran it against `pki.pdf` from
train 26.2, which is the same file that the staged corpus used. Every technical unknown of the
converter is now closed. The converter tasks are implementation work. **Write no task that
evaluates a PDF library and no task that compares two readers. That work is finished, and the
answer is `pdfplumber`.**

| Capability | How `pdfplumber` supplies it | Measured result |
| - | - | - |
| Heading detection | `char["size"]` | Works. The body size of `pki.pdf` is 10.0, measured over all 168 pages. The superseded figure of 9.0 came from a 12 page sample of front matter. T012 counts every page and writes no constant. |
| Bold subheading | `char["fontname"]` | Works. A name that holds `bold` marks a bold run. The fonts are `Lato-Bold`, `Lato-Regular`, and `Lato-Light`. |
| Line grouping | `page.extract_text_lines()` | Works. Each line carries its `chars`, so a per-line size is available. |
| Output size | 54,978 characters over 40 pages | PyMuPDF gives 55,870 characters for the same 40 pages, a difference of 1.6 percent. |
| Structure found | 55 headings and 127 list items over 40 pages | Comparable to the staged output. |

The available char attributes are `fontname`, `size`, `text`, `top`, `upright`, and `x0`. That
set covers the whole heading rule.

The 1.6 percent character difference supports the 767 to 778 row band in T026. It does not
replace the measurement. The band depends on the whole corpus, not on one document.

### The 2 defects that the prototype found

| # | Defect | Task |
| - | - | - |
| 1 | A folio line survives. Lines such as `ii` and `iii` reach the output. The staged converter dropped a short line that matched a roman numeral or a page label pattern. | T019 |
| 2 | `page.extract_text_lines()` merges a table of contents into one paragraph. The staged output kept one contents entry for each line. | T020 |

Each defect has a named acceptance test, which is `test_folio_line_removed` and
`test_contents_row_stays_on_one_line`.

## Rules that every task obeys

| Rule | Statement | Source |
| - | - | - |
| No PyMuPDF | Never add PyMuPDF to the repository. It carries the GNU Affero GPL 3.0, and `.github/workflows/container-build.yml` pushes an image to `ghcr.io`. Use `pdfplumber`, which is MIT and which `pyproject.toml` already declares. | Research Decision 15 |
| No bulk vendor text | The repository receives the 6 skill files only. The 744 MB corpus stays at the corpus root. | FR-013, FR-014, SC-005 |
| No ignored citation | No shipped file may name a path below `documentation/references/`. `.gitignore` line 28 ignores that path, so a clone does not hold it. Cite a public URL, a path below the corpus root, or a committed repository path. | Plan section 3a |
| Inline comments | Every executable line of Python carries an inline comment. | Constitution Principle VI |
| Action logging | An `info` message runs before each operation. A `debug` message runs after it. | Constitution Principle VII |
| Five-Item Rule | 5 parameters and 25 lines for each function. 5 children for each folder. | Constitution Principle I |
| No wrapper function | Add no function that only calls another function. | Repository rule |
| Writing standard | Every shipped Markdown file scores 80 or more on the STE linter. | FR-051, SC-010 |

Warning: the STE linter returns exit code 2 when the file list holds a CSV file. Grade the
Markdown files only.

## Path conventions

- The skill ships at `.github/skills/hardening-junos/`.
- The converter lives at `scripts/pdf_to_markdown.py`, outside the skill.
- The corpus lives at `$env:JUNIPER_CORPUS_ROOT`, outside the repository.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Build the file skeleton, the repository guards, and the corpus prerequisites.

- [ ] T001 Create the folder tree `.github/skills/hardening-junos/references/`
  - `Verify:` `Get-ChildItem $skill -Recurse -Directory | Select-Object Name` gives `references`.

- [ ] T002 [P] Create `.github/skills/hardening-junos/SKILL.md` with the 3 front matter fields `name`, `description`, and `argument-hint`, plus the snapshot statement for 2026-09-16
  - The `name` value must equal the folder name `hardening-junos`, from FR-003 and the front matter table in `contracts/skill-interface.md`.
  - `Verify:` `python -c "import re,io;t=io.open(r'.github/skills/hardening-junos/SKILL.md',encoding='utf-8').read();print(all(k in t.split('---')[1] for k in ('name:','description:','argument-hint:')), 'hardening-junos' in t, '2026-09-16' in t)"` gives `True True True`.

- [ ] T003 [P] Create the 4 reference Markdown files `references/baseline-controls.md`, `references/stig-rules.md`, `references/corpus-operations.md`, and `references/verification.md`, each with a title, a purpose sentence, the snapshot date 2026-09-16, and an empty `Sources` section
  - The router points at each file, so each file must exist before T031 writes the routing table.
  - `Verify:` `Get-ChildItem "$skill/references" -Filter *.md | Measure-Object` gives `Count : 4`.

- [ ] T004 [P] Create `.github/skills/hardening-junos/references/corpus-index.csv` with the single header row `file,title,group,train,pages,archive,origin,gap` and LF line endings
  - `Verify:` `python -c "b=open(r'.github/skills/hardening-junos/references/corpus-index.csv','rb').read();print(b.count(b'\r'), b.decode('utf-8').splitlines()[0])"` gives `0 file,title,group,train,pages,archive,origin,gap`.

- [ ] T005 [P] Add the corpus root guard block to `.gitignore`, below the existing block at lines 20 to 28
  - Ignore `juniper-doc-archives/`, `**/markdown/`, `**/extracted/`, and `*.pdf`. Name the rebuild command `python scripts/pdf_to_markdown.py`, which matches the style of the existing block.
  - Record this condition in the task note: `git check-ignore` cannot test a path outside the worktree, so check V12 tests a path inside the worktree instead.
  - `Verify:` `git check-ignore -v juniper-doc-archives/markdown/x.md` names the new `.gitignore` line.

- [ ] T006 [P] Confirm the PDF library declaration in `pyproject.toml`
  - `pdfplumber>=0.11.0` must be present. PyMuPDF must be absent. Add no dependency.
  - `Verify:` `Select-String -Path pyproject.toml -Pattern 'pdfplumber|pymupdf|fitz' -AllMatches` gives `pdfplumber>=0.11.0` and no other match.

- [ ] T007 [P] Extend the writing gate in `.github/workflows/ste-lint.yml`
  - Add `.github/skills/**/*.md` to the `paths` trigger. Add the 5 skill Markdown files to the `run` list of the grade step. Do not add the CSV file, because the linter returns exit code 2 for it.
  - `Verify:` `python -c "import yaml;d=yaml.safe_load(open('.github/workflows/ste-lint.yml',encoding='utf-8'));print('.github/skills/**/*.md' in d[True]['pull_request']['paths'])"` gives `True`.

- [ ] T008 [P] Confirm the staged corpus prerequisites by reading `$env:JUNIPER_CORPUS_ROOT\markdown\_conversion-manifest.json`
  - Confirm 4,007 Markdown files, 511,674 pages, and the status counts of 4,004 converted and 3 skipped. Confirm that `corpus-catalog.csv` holds 4,006 rows and that `selection-inventory.csv` holds 378 archive rows.
  - `Verify:` `python -c "import json,os;m=json.load(open(os.path.join(os.environ['JUNIPER_CORPUS_ROOT'],'markdown','_conversion-manifest.json'),encoding='utf-8'));print(m['pages'],m['status_counts'])"` gives `511674 {'skipped': 3, 'converted': 4004}`.

**Checkpoint**: The 6 skill files exist and hold their headers. The repository guards are in
place. The corpus is present.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Upgrade the converter, rebuild the corpus, re-measure the quality floor, and build
the index. Every user story reads the output of this phase.

**CRITICAL**: No user story work can begin until this phase is complete. The index row count is
unknown until T026 ends.

### Block A: The converter contract test

- [ ] T009 Write the PDF fixture builder and the structural contract test in `tests/test_pdf_to_markdown.py`
  - Test the 5 rows of the check V15 table: the front matter holds `source_file` and `pages` always and the other 5 fields when the metadata gives them, the `pages` value equals the source page count, the file holds 1 heading or more and 6 headings or less before the first page marker, the text gives 200 characters or more for each page, and the file holds no ligature and no curly quotation mark.
  - The test must fail against the current flat page dump. That failure proves the measured gap in plan section 7.
  - `Verify:` `pytest tests/test_pdf_to_markdown.py -q` fails, and the failure names the missing front matter.

### Block B: The converter upgrade

Every task in this block edits `scripts/pdf_to_markdown.py`. No task in this block carries
`[P]`, because they all touch one file. Keep the classes `PdfMarkdownConverter` and
`PdfMarkdownCommand`. Add no new module and no wrapper function.

- [ ] T010 Replace `pypdf` with `pdfplumber` in the imports and the module docstring of `scripts/pdf_to_markdown.py`
  - The docstring must stop asking the reader to install an undeclared package.
  - `Verify:` `Select-String -Path scripts/pdf_to_markdown.py -Pattern 'pypdf|pymupdf|fitz' | Measure-Object` gives `Count : 0`.

- [ ] T011 Add the YAML front matter writer to `scripts/pdf_to_markdown.py`
  - Write `source_file` and `pages` always. Write `title`, `author`, `subject`, `creationDate`, and `modDate` when the PDF metadata gives them. FR-025 and FR-026 set the rule.
  - `Verify:` `pytest tests/test_pdf_to_markdown.py -q -k front_matter` passes.

- [ ] T012 Add the font size heading rule to `scripts/pdf_to_markdown.py`
  - The prototype closed this rule. Group the page with `page.extract_text_lines()`, which gives each line with its `chars`. Take the modal `char["size"]` as the body size. Promote a line above the body size to a heading. Mark a bold subheading when `char["fontname"]` holds `bold`, which matches `Lato-Bold` against `Lato-Regular` and `Lato-Light`.
  - **Accumulate the size count over every page of the document before you classify any line.** Never read the body size from a sample, from the first N pages, or from a page range. A future contributor will want to sample a 500 page document for speed. The reason to refuse: the front matter uses a smaller size than the body, so a sample returns the front matter size and silently promotes the whole document.
  - **Compute the body size for each document. Never write a constant threshold.** The body size of `pki.pdf` is 10.0, measured over all 168 pages. The superseded figure of 9.0 came from a 12 page sample of the cover, the notices, and the contents, which hold 4.2 percent of the characters. `research.md` Decision 15 holds the correction and the 4 range measurements.
  - The cost of the error is 65.8 percent of lines marked as headings against 5.5 percent, because body text at 10.0 points clears a threshold of 9.72 points. The failure raises no exception and barely changes the file size.
  - The available char attributes are `fontname`, `size`, `text`, `top`, `upright`, and `x0`. That set covers the whole rule. Add no other library.
  - Write 6 headings or less before the first page marker, from FR-028. Join a heading that a line break divides, from FR-029.
  - `Verify:` `pytest tests/test_pdf_to_markdown.py -q -k heading` passes, including the 2 named tests that T012 adds to `tests/test_pdf_to_markdown.py`.
    - `test_body_size_is_computed_not_constant` converts 2 fixtures with different body sizes and confirms that each one gives a heading.
    - `test_body_size_uses_every_page` builds a fixture whose first pages use a smaller size than its body, which is the normal shape of a Juniper guide. It asserts that the converter returns the body size and not the front matter size. It asserts that 25 percent or less of the output lines are headings.
    - A run against `pki.pdf` gives about 55 headings over the first 40 pages, which is 5.5 percent of 1,001 lines.

- [ ] T013 Add the running header and page number removal to `scripts/pdf_to_markdown.py`
  - Remove a line that repeats at the top of each page. Remove a line that holds a page number alone. FR-030 sets the rule.
  - `Verify:` `pytest tests/test_pdf_to_markdown.py -q -k header` passes.

- [ ] T014 Add the glyph rules to `scripts/pdf_to_markdown.py`
  - Change a bullet glyph to a Markdown list item. Normalize a ligature and a curly quotation mark. FR-031 sets the rule.
  - `Verify:` `pytest tests/test_pdf_to_markdown.py -q -k glyph` passes, and a run against `pki.pdf` gives about 127 list items over the first 40 pages.

- [ ] T015 Keep a command block and a table readable in `scripts/pdf_to_markdown.py`
  - Hold the reading order of a configuration example. FR-032 sets the rule.
  - `Verify:` `pytest tests/test_pdf_to_markdown.py -q -k layout` passes.

- [ ] T016 Add the character density floor and the `review` status to `scripts/pdf_to_markdown.py`
  - Divide the character count by the page count. Set the status `review` below 200. FR-027 sets the rule.
  - `Verify:` `pytest tests/test_pdf_to_markdown.py -q -k density` passes.

- [ ] T017 Add the worker pool and the `--workers` option to `PdfMarkdownCommand` in `scripts/pdf_to_markdown.py`
  - The default worker count is the processor count. Plan section 7 sets the rule.
  - `Verify:` `python scripts/pdf_to_markdown.py --help` names `--workers`, and the help text states the default.

- [ ] T018 Write the conversion manifest in `scripts/pdf_to_markdown.py`
  - Write one row for each source file with its status, its page count, and its character count. FR-033 sets the rule.
  - `Verify:` `pytest tests/test_pdf_to_markdown.py -q -k manifest` passes.

### Block B2: The two defects that the prototype found

The prototype ran against `pki.pdf` from train 26.2 and found 2 defects. Each task below fixes
one defect and adds a named acceptance test. Both tasks edit `scripts/pdf_to_markdown.py` and
`tests/test_pdf_to_markdown.py`, so neither carries `[P]`.

- [ ] T019 Add the folio line rule to `scripts/pdf_to_markdown.py` and the named test `test_folio_line_removed` to `tests/test_pdf_to_markdown.py`
  - Defect 1: a folio line survives. The prototype wrote `ii` and `iii` into the output. The staged converter dropped a short line that matched a roman numeral or a page label pattern. The `pdfplumber` converter needs the same rule.
  - Drop a short line that holds a roman numeral alone, an arabic page number alone, or a page label such as `Page 12` or `12 of 40`. Keep a line that holds real text, so a list item such as `ii. Set the policy` survives.
  - This rule sits beside the page number removal in T013. Keep it in the same method group, and keep the method at 25 lines or less.
  - `Verify:` `pytest tests/test_pdf_to_markdown.py -q -k test_folio_line_removed` passes, and `python -c "import re,io;t=io.open('out/pki.md',encoding='utf-8').read();print([l for l in t.splitlines() if re.fullmatch(r'\s*[ivxlcdm]+\s*',l,re.I)])"` gives `[]`.

- [ ] T020 Add the contents row rule to `scripts/pdf_to_markdown.py` and the named test `test_contents_row_stays_on_one_line` to `tests/test_pdf_to_markdown.py`
  - Defect 2: `page.extract_text_lines()` merges a table of contents into one paragraph. The staged output kept one contents entry for each line.
  - Fix it one of two ways. Set the line grouping tolerance so a contents row stays on its own line. Or split a joined run on the page number pattern, which is a dot leader or a run of spaces that ends in a page number. Choose the way that keeps the body text unchanged, and state the choice in the task note.
  - `Verify:` `pytest tests/test_pdf_to_markdown.py -q -k test_contents_row_stays_on_one_line` passes, and the contents page of `pki.pdf` gives one output line for each contents entry, not one paragraph.

### Block C: The converter gates

- [ ] T021 Run the 5 Python gates on `scripts/pdf_to_markdown.py` and `tests/test_pdf_to_markdown.py`
  - `Verify:` each of these gives 0 violations, and the last gives 80 percent coverage or more.

    ```powershell
    ruff check scripts/pdf_to_markdown.py tests/test_pdf_to_markdown.py
    black --check scripts/pdf_to_markdown.py tests/test_pdf_to_markdown.py
    mypy scripts/pdf_to_markdown.py
    python -m bandit -c pyproject.toml scripts/pdf_to_markdown.py
    pytest tests/test_pdf_to_markdown.py --cov=scripts.pdf_to_markdown --cov-report=term-missing --cov-fail-under=80
    ```

  - Record this condition in the task note: `[tool.ruff]` sets `extend-exclude = ["scripts"]` and `[tool.bandit]` omits `scripts`, so the repository gate does not cover this file. The command above names the file, so the gate runs.

- [ ] T022 Audit `scripts/pdf_to_markdown.py` against the non-negotiable repository rules
  - Confirm an inline comment on every executable line. Confirm an `info` log before each operation and a `debug` log after it. Confirm 5 parameters or less and 25 lines or less for each function. Confirm that no wrapper function exists.
  - `Verify:` `python -c "import ast,io;s=io.open(r'scripts/pdf_to_markdown.py',encoding='utf-8').read();t=ast.parse(s);f=[(n.name,len(n.args.args),n.end_lineno-n.lineno+1) for n in ast.walk(t) if isinstance(n,ast.FunctionDef)];print([x for x in f if x[1]>5 or x[2]>25])"` gives `[]`.

- [ ] T023 Convert 30 sample PDF files with the upgraded `scripts/pdf_to_markdown.py` and test each output against the check V15 contract
  - Select 10 documents from the security subset, 10 documents with many tables, and 10 documents with a complex cover page. `DO_ContrailRHOSP.pdf` is a known hard cover page.
  - Add the heading share as a 6th test. A file where more than 25 percent of the lines are headings fails, because that share signals a body size error. The measured values are 5.5 percent for a correct body size and 65.8 percent for a body size that is 1 point too small.
  - Do not compare the output against the staged Markdown byte for byte. Two readers do not agree byte for byte.
  - `Verify:` the check V15 script reports 30 of 30 files that satisfy the 6 tests.

### Block D: The corpus rebuild and the re-measure

- [ ] T024 Rebuild the whole corpus with the upgraded `scripts/pdf_to_markdown.py`, writing to `$env:JUNIPER_CORPUS_ROOT\markdown\`
  - The run covers 511,674 pages. `pdfplumber` gives 18.0 to 21.6 pages for each second, so 26 workers take about 0.3 hours. Write no file into the repository.
  - `Verify:` `python -c "import json,os;m=json.load(open(os.path.join(os.environ['JUNIPER_CORPUS_ROOT'],'markdown','_conversion-manifest.json'),encoding='utf-8'));print(m['pages'],m['status_counts'])"` gives `511674` pages and 0 failed rows.

- [ ] T025 Sweep the heading share of every rebuilt file under `$env:JUNIPER_CORPUS_ROOT\markdown\*.md` and gate the rebuild on it
  - This gate runs before the density re-measure. A wrong body size corrupts the whole rebuilt corpus, and an index built from a corrupt corpus is worthless. Catch it here, not after T026.
  - Count the heading lines and the total lines of each file. A file where more than 25 percent of the lines are headings signals a body size error, from the measured 5.5 percent against 65.8 percent result in `research.md` Decision 15.
  - This failure is silent. It raises no exception, and the file size barely changes. Only this count finds it.
  - **Stop condition**: 1 file or more above the ceiling means that T012 sampled the size instead of counting every page. Return to T012. Do not continue to T026, and do not rebuild again until the rule is fixed.
  - `Verify:` `python -c "import glob,os,io;root=os.environ['JUNIPER_CORPUS_ROOT'];bad=[];[bad.append((f,h/max(n,1))) for f in glob.glob(os.path.join(root,'markdown','**','*.md'),recursive=True) for L in [io.open(f,encoding='utf-8').read().splitlines()] for h,n in [(sum(1 for l in L if l.startswith('#')),len(L))] if n and h/n>0.25];print(len(bad),bad[:5])"` gives `0 []`.

- [ ] T026 Re-measure the character density of every rebuilt file under `$env:JUNIPER_CORPUS_ROOT\markdown\*.md` against `$env:JUNIPER_CORPUS_ROOT\markdown\_conversion-manifest.json`, and re-apply the 200 character floor
  - This is the re-measure step that the plan requires. Report 3 numbers: the count of documents that fall below the floor, the count that rise above it, and the new index row count.
  - The planned count is 775. The measured count must fall between 767 and 778. A count outside that band means that the converter changed more than the plan expects. Stop and investigate before T027.
  - `Verify:` the density script prints the new row count and the movement of the 8 documents between 200 and 250 and the 3 documents between 150 and 200.

- [ ] T027 Record the measured row count in `specs/2754-hardening-junos-skill/plan.md`, `specs/2754-hardening-junos-skill/contracts/corpus-index.md`, and `specs/2754-hardening-junos-skill/quickstart.md`
  - Update the `Data rows` line of the contract, invariant I1, the check V5 expected value, and the plan row count. State the measured value and the reason for any change from 775.
  - `Verify:` `Select-String -Path specs/2754-hardening-junos-skill/plan.md,specs/2754-hardening-junos-skill/contracts/corpus-index.md,specs/2754-hardening-junos-skill/quickstart.md -Pattern '<measured row count>' | Measure-Object` gives `Count : 4` or more.

### Block E: The index

- [ ] T028 Write the archive code table of 165 rows in the `Archive codes` section of `.github/skills/hardening-junos/references/corpus-operations.md`
  - The columns are `code`, `directory`, `train`, and `url`. Order the codes by the row count of each directory, so `A001` holds the most rows. Each directory is relative to the corpus root. A row without a URL holds `-`, and a measured run fills 162 of 165.
  - `Verify:` `(Select-String -Path "$skill/references/corpus-operations.md" -Pattern '^\| A\d{3} ').Count` gives `165`.

- [ ] T029 Build `.github/skills/hardening-junos/references/corpus-index.csv` from the rebuilt front matter
  - Follow the 7 steps of `How a future reader rebuilds the index` in plan section 6. Write the 8 columns in the fixed order, with LF line endings and UTF-8 without a byte order mark. Cut each title to 70 characters. Read the file name when the `title` field is absent, which happens in 12.2 percent of the files. Apply the 3 membership rules `f`, `t`, and `e`. Set the `gap` column from the 5 documents in `contracts/gap-register.md`.
  - `Verify:` `python -c "import csv;r=list(csv.DictReader(open(r'.github/skills/hardening-junos/references/corpus-index.csv',encoding='utf-8',newline='')));print(len(r),len(r[0]),len({x['file'] for x in r}))"` gives the measured row count from T026, then `8`, then the same row count.

- [ ] T030 Prove the 11 index invariants I1 to I11 against `.github/skills/hardening-junos/references/corpus-index.csv`
  - I1 row and column count, I2 unique `file`, I3 no absolute path, I4 `group` in `G1` to `G8`, I5 `archive` exists in the T028 table, I6 `pages` matches the manifest, I7 density of 200 or more, I8 each row resolves to a file, I9 each group holds 1 row or more, I10 the file is 90 KB or less, I11 no path below `documentation/references/`.
  - This task runs checks V5, V6, V7, and V8 from `quickstart.md`.
  - `Verify:` the invariant script reports 11 of 11 invariants that hold, and check V7 reports 50 of 50 paths that exist.

### Block F: The router contract

- [ ] T031 [P] Write the 5-row routing table in `.github/skills/hardening-junos/SKILL.md`
  - Each row gives a task, a reference file, and the required result. Copy the 5 rows from the routing table in `contracts/skill-interface.md`. This matches `managing-mist-api`.
  - This task touches `SKILL.md` only, so it can run beside T024 to T030.
  - `Verify:` `(Select-String -Path "$skill/SKILL.md" -Pattern '^\| .*references/').Count` gives `5`.

- [ ] T032 Write the safety rules, the answer contract, and the condition contracts in `.github/skills/hardening-junos/SKILL.md`
  - Write the 7 answer parts A1 to A7. Write the order rule, which puts a warning before the instruction that causes the risk. Write the citation rule and its 3 allowed places. Write the 10 condition contracts, which cover an absent corpus, a source outside the security subset, a gap register document, a document with no train, two trains that disagree, no source, a DISA rule with no Juniper source, a request to change a device, a request to commit the corpus, and a partial conversion.
  - `Verify:` `python -m tools.ste_linter --min-score 80 "$skill/SKILL.md"` gives exit code 0, and `(Get-Item "$skill/SKILL.md").Length -le 12288` gives `True`.

**Checkpoint**: The converter reproduces the corpus. The corpus is rebuilt by one reader. The
index holds the measured row count and passes its 11 invariants. The router states the answer
contract. User story work can now begin.

---

## Phase 3: User Story 1 - Get a hardening answer with its source (Priority: P1) 🎯 MVP

**Goal**: A junior NOC engineer asks a hardening question. The skill gives the control, the
Junos command, the reason, and the source document with its train.

**Independent Test**: Ask 5 hardening questions that cover 5 different checklist sections.
Confirm that each answer gives a control, a Junos command, and a source citation. Confirm that
each citation points to a real document.

- [ ] T033 [US1] Write the 8 section headings and the 67 control identifiers `C-01-01` to `C-08-06` in `.github/skills/hardening-junos/references/baseline-controls.md`
  - Read the checklist at `$env:JUNIPER_CORPUS_ROOT\extracted\TW_HardeningJunosDevices_2ndEd\TW_HardeningJunosDevices_2ndEd_Checklist.pdf`. The 8 sections hold 2, 9, 10, 7, 10, 17, 6, and 6 items, which sum to 67.
  - `Verify:` `(Select-String -Path "$skill/references/baseline-controls.md" -Pattern '^\| C-\d{2}-\d{2} ').Count` gives `67`.

- [ ] T034 [US1] Write the statement, the Junos command, the reason, the platform, and the evidence command for each of the 67 controls in `.github/skills/hardening-junos/references/baseline-controls.md`
  - The hardening book is from 2015, so confirm each command against the train 26.2 document for its section. Plan section 3 names the document for each of the 8 sections. State the platform, because the checklist covers MX, EX, and SRX. Write the command. Do not copy the book text.
  - `Verify:` `python -c "import re,io;t=io.open(r'.github/skills/hardening-junos/references/baseline-controls.md',encoding='utf-8').read();rows=re.findall(r'^\| C-\d{2}-\d{2} .*$',t,re.M);print(len(rows),sum(1 for r in rows if 'set ' in r or 'show ' in r))"` gives `67 67`.

- [ ] T035 [US1] Mark the lockout risk and write the recovery step for each marked control in `.github/skills/hardening-junos/references/baseline-controls.md`
  - FR-050 requires the mark. SC-013 requires a recovery step for 100 percent of the marked controls. A management filter and an authentication change are examples.
  - `Verify:` `python -c "import re,io;t=io.open(r'.github/skills/hardening-junos/references/baseline-controls.md',encoding='utf-8').read();rows=[r for r in re.findall(r'^\| C-\d{2}-\d{2} .*$',t,re.M) if 'lockout' in r.lower()];print(len(rows),sum(1 for r in rows if 'ecovery' in r))"` gives two equal numbers.

- [ ] T036 [US1] Write the source citation and the public URL for each of the 67 controls in `.github/skills/hardening-junos/references/baseline-controls.md`
  - Each citation names the document, the train, and the page. Read the relative path from `references/corpus-index.csv`. SC-002 allows 0 controls without a source. SC-012 requires the train for 100 percent of the citations. Never name a path below `documentation/references/`.
  - `Verify:` `Select-String -Path "$skill/references/baseline-controls.md" -Pattern 'documentation/references' | Measure-Object` gives `Count : 0`, and every control row holds a `train` value.

- [ ] T037 [US1] Write the `Sources` section of `.github/skills/hardening-junos/references/baseline-controls.md`
  - Give a `Source` and `Where` table, which matches section 14 of `documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md`. State that the vendor text is not committed. Name the rebuild command `python scripts/pdf_to_markdown.py`.
  - `Verify:` `Select-String -Path "$skill/references/baseline-controls.md" -Pattern '^## Sources' | Measure-Object` gives `Count : 1`.

- [ ] T038 [US1] Run check V10 and check V1 on `.github/skills/hardening-junos/references/baseline-controls.md`
  - `Verify:` `(Select-String -Path "$skill/references/baseline-controls.md" -Pattern '^\| C-\d{2}-\d{2} ').Count` gives `67`, and `python -m tools.ste_linter --min-score 80 "$skill/references/baseline-controls.md"` gives exit code 0 with a score of 80 or more.

- [ ] T039 [US1] Run the story 1 acceptance test against `.github/skills/hardening-junos/SKILL.md`
  - Ask the 5 questions in check V11 of `quickstart.md`. Confirm each answer against the parts A1 to A7 of the answer contract. Then set the corpus root to a folder that does not exist and repeat, which proves SC-007.
  - `Verify:` 5 answers hold the control, the command, the reason, and a citation that resolves. 5 answers state that the corpus is absent when the corpus root is removed. 0 failures.

**Checkpoint**: The skill answers a hardening question with a control, a command, a reason, and
a source. This is the minimum usable product. It ships on its own.

---

## Phase 4: User Story 2 - Check a configuration against the baseline (Priority: P2)

**Goal**: The skill reviews a Junos configuration file against the 67 controls and maps each
failure to a DISA STIG rule.

**Independent Test**: Give the skill the medium security sample configuration from Appendix B
of the hardening book. Confirm a result for all 67 checklist items. Confirm that no item is
silently absent.

- [ ] T040 [US2] Write the 181 condensed rule rows in `.github/skills/hardening-junos/references/stig-rules.md`
  - Parse the 3 XCCDF files in `$env:JUNIPER_CORPUS_ROOT\extracted\U_Juniper_EX_Switches_Y26M07_STIG\`. The sets L2S, NDM, and RTR hold 24, 55, and 102 rules. Write `rule_id`, `group_id`, `set`, `severity`, a title of 140 characters or less, a one-line check, and a one-line fix. The full rule text is 485 KB, which is more than the whole budget, so ship the condensed row and point at the XCCDF file.
  - `Verify:` `(Select-String -Path "$skill/references/stig-rules.md" -Pattern 'V-\d{6}' -AllMatches).Matches.Value | Sort-Object -Unique | Measure-Object` gives `Count : 181`.

- [ ] T041 [US2] Write the platform limit paragraph and the severity split at the head of `.github/skills/hardening-junos/references/stig-rules.md`
  - State that the bundle covers the EX switch. State that a reader must test a rule before an MX or SRX device receives it. State the split of 25 high, 122 medium, and 34 low.
  - `Verify:` `Select-String -Path "$skill/references/stig-rules.md" -Pattern 'EX switch' | Measure-Object` gives `Count : 1` or more, and the file states `25`, `122`, and `34`.

- [ ] T042 [US2] Write the checklist section value `G1` to `G8`, or `-`, for each of the 181 rules in `.github/skills/hardening-junos/references/stig-rules.md`
  - A rule with no Juniper source holds `-` and states that fact, from the edge case list.
  - `Verify:` `python -c "import re,io;t=io.open(r'.github/skills/hardening-junos/references/stig-rules.md',encoding='utf-8').read();print(len(re.findall(r'\| (G[1-8]|-) \|',t)))"` gives `181`.

- [ ] T043 [P] [US2] Add the matching STIG rule identifiers to the control rows in `.github/skills/hardening-junos/references/baseline-controls.md`
  - A control holds zero or more identifiers. FR-036 of the data model sets the field `stig_rules`.
  - This task touches `baseline-controls.md` only, so it can run beside T044 and T045.
  - `Verify:` `(Select-String -Path "$skill/references/baseline-controls.md" -Pattern 'V-\d{6}' -AllMatches).Matches.Count` gives 1 or more.

- [ ] T044 [P] [US2] Write the configuration review contract in `.github/skills/hardening-junos/SKILL.md`
  - State the 3 results `pass`, `fail`, and `not-assessable`. State that a `fail` gives the STIG rule identifier and its severity when a match exists. State that a `not-assessable` result names the evidence that the review needs. State that the review is advice and that it changed no device.
  - This task touches `SKILL.md` only, so it can run beside T043 and T045.
  - `Verify:` `Select-String -Path "$skill/SKILL.md" -Pattern 'not-assessable' | Measure-Object` gives `Count : 1` or more, and `(Get-Item "$skill/SKILL.md").Length -le 12288` gives `True`.

- [ ] T045 [P] [US2] Write the `Sources` section of `.github/skills/hardening-junos/references/stig-rules.md`
  - Give the public DISA download page <https://public.cyber.mil/stigs/> and the corpus path of the 3 XCCDF files. State that the full rule text stays in the XCCDF file.
  - This task touches `stig-rules.md` only, so it can run beside T043 and T044.
  - `Verify:` `Select-String -Path "$skill/references/stig-rules.md" -Pattern '^## Sources' | Measure-Object` gives `Count : 1`.

- [ ] T046 [US2] Run check V9 and check V1 on `.github/skills/hardening-junos/references/stig-rules.md`
  - `Verify:` the V9 count gives `181` and the severity split gives 25 high, 122 medium, and 34 low. `python -m tools.ste_linter --min-score 80 "$skill/references/stig-rules.md"` gives exit code 0.

- [ ] T047 [US2] Run the story 2 acceptance test against `.github/skills/hardening-junos/SKILL.md`
  - Give the skill `$env:JUNIPER_CORPUS_ROOT\extracted\TW_HardeningJunosDevices_2ndEd\AppendixB_MediumSecuritySampleConfig.rtf`.
  - `Verify:` the review reports 67 results. Each result is `pass`, `fail`, or `not-assessable`. Each `fail` gives a STIG rule identifier and its severity when a match exists. The report states that it is advice and that it changed no device. 0 silently absent items.

**Checkpoint**: The skill reviews a configuration file and maps a failure to a DISA rule.
Stories 1 and 2 both work.

---

## Phase 5: User Story 3 - Find a source document in the staged corpus (Priority: P3)

**Goal**: The skill gives the title, the train, the page count, and the relative path of a
source document. The skill states when the corpus is absent.

**Independent Test**: Ask the skill for the source of 10 controls. Confirm that each path points
to a file below the corpus root. Then remove the corpus root. Confirm that the skill reports
the corpus as absent and still answers from its curated references.

Every task from T048 to T052 edits
`.github/skills/hardening-junos/references/corpus-operations.md`, so none carries `[P]`.

- [ ] T048 [US3] Write the corpus root setting and how to change it in the `Corpus root` section of `.github/skills/hardening-junos/references/corpus-operations.md`
  - The default value is `C:\Users\jmorrison\Downloads\juniper-doc-archives`, from FR-016. Name the 3 child folders `markdown/`, `extracted/`, and `archives/`. State that the corpus is outside the repository and that the repository holds the skill files only.
  - `Verify:` `Select-String -Path "$skill/references/corpus-operations.md" -Pattern 'juniper-doc-archives' | Measure-Object` gives `Count : 1` or more.

- [ ] T049 [US3] Write the search procedure in `.github/skills/hardening-junos/references/corpus-operations.md`
  - State how to search the staged Markdown for a term, from FR-022. Tell the reader to search the security subset first and the full unique set second, from FR-023. State that an answer from the second area must say so, from FR-009. Give the `Select-String` command and the `rg` command.
  - `Verify:` `Select-String -Path "$skill/references/corpus-operations.md" -Pattern 'security subset first|second search area' | Measure-Object` gives `Count : 1` or more.

- [ ] T050 [US3] Write the path rule and one worked example in `.github/skills/hardening-junos/references/corpus-operations.md`
  - State that the PDF path is `<directory of archive>/<file>.pdf` and that the Markdown path is `markdown/<directory of archive>/<file>.md`. Both paths are relative to the corpus root. Give the `user-access` example from `contracts/corpus-index.md`.
  - `Verify:` `Select-String -Path "$skill/references/corpus-operations.md" -Pattern 'markdown/' | Measure-Object` gives `Count : 1` or more, and a manual test of the worked example resolves to a real file.

- [ ] T051 [US3] Write the absent corpus behavior and the partial conversion check in `.github/skills/hardening-junos/references/corpus-operations.md`
  - State that the skill answers from the curated references when the corpus root is absent, and that it does not fail, from SC-007. State how to compare the index against `markdown/_conversion-manifest.json` and how to report the count of the missing files.
  - `Verify:` `Select-String -Path "$skill/references/corpus-operations.md" -Pattern '_conversion-manifest.json' | Measure-Object` gives `Count : 1` or more.

- [ ] T052 [US3] Write the `Sources` section of `.github/skills/hardening-junos/references/corpus-operations.md`
  - Give a `Source` and `Where` table. State that the vendor text is not committed. Name the rebuild commands. Never name a path below `documentation/references/`.
  - `Verify:` `Select-String -Path "$skill/references/corpus-operations.md" -Pattern 'documentation/references' | Measure-Object` gives `Count : 0`.

- [ ] T053 [US3] Run the story 3 acceptance test against `.github/skills/hardening-junos/references/corpus-index.csv`
  - Ask for the source of 10 controls. Then set the corpus root to a folder that does not exist and repeat.
  - `Verify:` 10 relative paths resolve to a real file. After the corpus root is removed, the skill states that the corpus is absent, gives the title and the train, and still answers. 0 failures.

**Checkpoint**: The skill finds a source document and behaves when the corpus is absent.
Stories 1, 2, and 3 all work.

---

## Phase 6: User Story 4 - Refresh the corpus and record the change (Priority: P4)

**Goal**: The skill states the refresh procedure, the deduplication rule, the acceptance rules,
and the gap register.

**Independent Test**: Add one train to the corpus. Follow the written refresh procedure. Confirm
that the index records the new train. Confirm that the gap register is still correct.

Every task from T054 to T057 edits
`.github/skills/hardening-junos/references/corpus-operations.md`, so none carries `[P]`.

- [ ] T054 [US4] Write the deduplication rule in `.github/skills/hardening-junos/references/corpus-operations.md`
  - The newest readable train wins, from FR-037. A train is readable when the PDF opens and the conversion status is `converted`. State the fallback rule of FR-038, the newest train record of FR-039, and the `supersedes` field of FR-040. State the genuine change test of FR-041: the page count differs by more than 2 percent, or the content hash differs while the title stays the same.
  - `Verify:` `Select-String -Path "$skill/references/corpus-operations.md" -Pattern 'newest readable train|2 percent' | Measure-Object` gives `Count : 2` or more.

- [ ] T055 [US4] Write the refresh procedure in `.github/skills/hardening-junos/references/corpus-operations.md`
  - Give the 7 index build steps and the 5 corpus rebuild steps from plan section 6. Name `python scripts/pdf_to_markdown.py` as the conversion command. State that a refresh rebuilds the whole file and never edits a single row by hand. State that a new train updates the `train` value of an existing row and adds no new row.
  - `Verify:` a reviewer who does not know the corpus follows the procedure and adds one train without help, which proves SC-011.

- [ ] T056 [US4] Write the acceptance rules and the character floor in `.github/skills/hardening-junos/references/corpus-operations.md`
  - Give the rules of FR-025 to FR-035: the front matter contract, the page count test, the 200 character floor and the `review` status, the 6 heading limit, the joined heading, the removed header and page number, the glyph rules, the readable command and table, the manifest, and the 30 document audit with its 5 checks.
  - Add the heading share rule. A converted file where more than 25 percent of the lines are headings fails the acceptance rules, because that share signals a body size error in the converter. State that the converter reads the body size from every page of a document and never from a sample. State that the check is cheap to run over the whole corpus after a rebuild.
  - `Verify:` `Select-String -Path "$skill/references/corpus-operations.md" -Pattern '200 characters' | Measure-Object` gives `Count : 1` or more, and `Select-String -Path "$skill/references/corpus-operations.md" -Pattern '25 percent' | Measure-Object` gives `Count : 1` or more.

- [ ] T057 [US4] Write the gap register in `.github/skills/hardening-junos/references/corpus-operations.md`
  - Table 1 holds the 2 unreadable documents `virtual-chassis-ex-4200-4500.pdf` and `virtual-chassis-ex-8200.pdf`, each with its affected trains 25.2, 25.4, and 26.2, its measured reason, its fallback train of 24.4 and 24.2, and its risk. Table 2 holds the 3 documents with the state `converted earlier`. `contracts/gap-register.md` holds the delivered rows. State that the skill names the gap and the fallback train when it cites a listed document, from FR-047.
  - `Verify:` `(Select-String -Path "$skill/references/corpus-operations.md" -Pattern 'virtual-chassis-ex-|converted earlier').Count` gives `5` or more.

- [ ] T058 [US4] Set the `gap` column of `.github/skills/hardening-junos/references/corpus-index.csv` from the register and re-run check V5
  - `c` marks a corrupt newer copy. `s` marks an earlier conversion. `-` marks every other row. The register is corpus wide and the index is subset wide, so a listed document that is not in the index adds no row.
  - `Verify:` `python -c "import csv;r=list(csv.DictReader(open(r'.github/skills/hardening-junos/references/corpus-index.csv',encoding='utf-8',newline='')));print(sorted({x['gap'] for x in r}),len(r))"` gives a subset of `['-','c','s']` and the row count from T026.

- [ ] T059 [US4] Run the story 4 acceptance test against `.github/skills/hardening-junos/references/corpus-operations.md`
  - Add one train to the corpus. Follow the written refresh procedure.
  - `Verify:` the index records the new train for each superseded document. The row count holds one row for each document name. The gap register is still correct. The repository grows by 400 KB or less.

**Checkpoint**: All 4 user stories work. The skill is complete.

---

## Phase 7: Polish and Cross-Cutting Concerns

**Purpose**: Ship the verification reference, correct the specification counts, and prove every
check.

- [ ] T060 Write the 13 checks in `.github/skills/hardening-junos/references/verification.md`
  - Ship checks V1 to V13, which a reader can run against the delivered skill. Give the command and the expected result for each check. Checks V14 and V15 cover the converter, so name them and point at `specs/2754-hardening-junos-skill/quickstart.md`. State the warning that the STE linter returns exit code 2 for a CSV file.
  - `Verify:` `(Select-String -Path "$skill/references/verification.md" -Pattern '^### V\d+\.').Count` gives `13`.

- [ ] T061 Write the 4 story acceptance scenarios and the 30 document audit method in `.github/skills/hardening-junos/references/verification.md`
  - Give the expected result of each story. Give the 5 audit checks: correct title, correct page count, no spurious heading run, readable command text, and readable table text. State the SC-008 target of 27 documents or more out of 30.
  - `Verify:` `Select-String -Path "$skill/references/verification.md" -Pattern 'Story [1-4]' | Measure-Object` gives `Count : 4` or more.

- [ ] T062 Write the `Sources` section of `.github/skills/hardening-junos/references/verification.md`
  - `Verify:` `Select-String -Path "$skill/references/verification.md" -Pattern '^## Sources' | Measure-Object` gives `Count : 1`.

- [ ] T063 Run the 30 document manual audit and record the result table in `.github/skills/hardening-junos/references/verification.md`
  - Audit 10 documents from the security subset, 10 documents with many tables, and 10 documents with a complex cover page. Record a pass or a fail for each of the 5 checks, from FR-034 and FR-035.
  - This task needs a human reader. Keep the box unchecked until a person completes the audit.
  - `Verify:` the recorded table gives 27 documents or more that pass all 5 checks, which is 90 percent and meets SC-008.

- [ ] T064 [P] Update the 8 deviation rows in `specs/2754-hardening-junos-skill/spec.md`
  - Correct the security relevant document count, the subset file count, the front matter field count, the skipped document record, the fallback trains, the full STIG text rule, the committed checklist path in FR-011, and the out-of-scope list for the conversion script. The plan section `Deviations from the specification` holds each row and its action.
  - This task touches `spec.md` only, so it can run beside T065.
  - `Verify:` `Select-String -Path specs/2754-hardening-junos-skill/spec.md -Pattern 'documentation/references/hardening' | Measure-Object` gives `Count : 0`.

- [ ] T065 [P] Write the release note fragment `changelog.d/issue-2754-hardening-junos-skill.md`
  - Use the `### Added` heading and one line that names issue #2754. State the skill, the file count, the measured size, and the converter upgrade. Match the style of `changelog.d/issue-1009-final-extraction.md`.
  - This task touches the fragment only, so it can run beside T064.
  - `Verify:` `Get-Content changelog.d/issue-2754-hardening-junos-skill.md` shows one heading and one bullet that names `#2754`.

- [ ] T066 Run the size and shape gate on `.github/skills/hardening-junos/`, which is check V2, V3, and V4
  - `Verify:` the total is 400 KB or less and about 262 KB. The folder holds 6 files. `SKILL.md` is 12 KB or less. No file is more than 90 KB. `references/` holds 5 children.

    ```powershell
    '{0:N1} KB' -f ((Get-ChildItem $skill -Recurse -File | Measure-Object Length -Sum).Sum / 1KB)
    Get-ChildItem $skill -Recurse -File | Select-Object Name, @{n='KB';e={[math]::Round($_.Length/1KB,1)}}
    (Get-ChildItem "$skill/references").Count
    ```

- [ ] T067 [P] Run the writing gate on the 5 Markdown files of `.github/skills/hardening-junos/`, which is check V1
  - This task reads the skill only, so it can run beside T068 and T069.
  - `Verify:` `python -m tools.ste_linter --min-score 80 @((Get-ChildItem $skill -Recurse -Filter *.md).FullName)` gives exit code 0. Each of the 5 files scores 80 or more. The existing skills score 96 to 99, so a lower score points at a writing problem.

- [ ] T068 [P] Run the commit guard and the ignored path check on `.gitignore` and `.github/skills/hardening-junos/`, which is check V12 and V13
  - This task reads the repository only, so it can run beside T067 and T069.
  - `Verify:` `git check-ignore -v juniper-doc-archives/markdown/x.md` names the guard line. `git diff --cached --stat` holds no PDF file, no file from `markdown/`, and no file from `extracted/`. `Select-String -Path $skill -Recurse -Pattern 'documentation/references' | Measure-Object` gives `Count : 0`.

- [ ] T069 [P] Re-run the 5 Python gates and the whole test suite for `scripts/pdf_to_markdown.py` and `tests/test_pdf_to_markdown.py`, which is check V14
  - This task reads the Python tree only, so it can run beside T067 and T068.
  - `Verify:` `ruff check .`, `black --check .`, `mypy scripts/pdf_to_markdown.py`, `python -m bandit -c pyproject.toml scripts/pdf_to_markdown.py`, and `pytest --cov --cov-fail-under=80` each give 0 violations.

- [ ] T070 Run the whole `specs/2754-hardening-junos-skill/quickstart.md` guide from check V1 to check V15 and the 4 story scenarios
  - `Verify:` the exit criteria table passes. Checks V1 to V15 all pass. The 4 user stories all pass. The audit gives 27 documents or more. The release note fragment exists.

- [ ] T071 Open the pull request for issue #2754 from branch `docs/2754-hardening-junos-skill`, and quote `changelog.d/issue-2754-hardening-junos-skill.md` in the body
  - Name the 6 shipped skill files, the converter upgrade at `scripts/pdf_to_markdown.py`, the measured index row count from T026, and the audit result from T063. State that the repository received 0 bytes of bulk Juniper text.
  - `Verify:` `git --no-pager diff --stat main...HEAD` lists 12 files or less, and no file under `markdown/` or `extracted/` appears.

---

## Dependencies

### Phase order

```text
Phase 1 Setup  ->  Phase 2 Foundational  ->  Phase 3 US1  ->  Phase 4 US2
                                                          ->  Phase 5 US3
                                                          ->  Phase 6 US4
                                                          ->  Phase 7 Polish
```

### Story completion order

| Story | Priority | Depends on | Reason |
| - | - | - | - |
| US1 | P1 | Phase 2 | The citation of each control reads the index that Phase 2 builds. |
| US2 | P2 | Phase 2, US1 | T043 adds the STIG identifiers to the control rows that US1 writes. |
| US3 | P3 | Phase 2 | The search procedure explains the index and the archive table that Phase 2 builds. |
| US4 | P4 | Phase 2, US3 | The refresh procedure and the gap register share `corpus-operations.md` with US3. |

US3 does not depend on US1 or US2. A second worker can run Phase 5 beside Phase 3 and Phase 4,
because Phase 5 touches `corpus-operations.md` and Phase 3 and Phase 4 touch
`baseline-controls.md` and `stig-rules.md`.

### The hard chain inside Phase 2

```text
T009 test  ->  T010..T018 converter  ->  T019..T020 defect fixes  ->  T021..T023 gates
            ->  T024 rebuild  ->  T025 heading-share gate  ->  T026 re-measure  ->  T027 record
            ->  T028 archive table  ->  T029 index  ->  T030 invariants
```

T031 and T032 branch off after T002. They touch `SKILL.md` only, so they run beside the chain.

### File ownership

| File | Tasks that write it |
| - | - |
| `scripts/pdf_to_markdown.py` | T010 to T020, and T022 |
| `tests/test_pdf_to_markdown.py` | T009, T012, T019, T020 |
| `.github/skills/hardening-junos/SKILL.md` | T002, T031, T032, T044 |
| `references/baseline-controls.md` | T003, T033 to T037, T043 |
| `references/stig-rules.md` | T003, T040 to T042, T045 |
| `references/corpus-index.csv` | T004, T029, T058 |
| `references/corpus-operations.md` | T003, T028, T048 to T052, T054 to T057 |
| `references/verification.md` | T003, T060 to T063 |
| `.gitignore` | T005 |
| `pyproject.toml` | T006 |
| `.github/workflows/ste-lint.yml` | T007 |
| `changelog.d/issue-2754-hardening-junos-skill.md` | T065 |
| `specs/2754-hardening-junos-skill/*` | T027, T064 |

---

## Parallel execution examples

### Phase 1

T002, T003, T004, T005, T006, T007, and T008 all run together after T001. They touch 7
different files.

```text
T002 SKILL.md front matter
T003 4 reference Markdown files
T004 corpus-index.csv header
T005 .gitignore
T006 pyproject.toml
T007 .github/workflows/ste-lint.yml
T008 the corpus manifest, read only
```

### Phase 2

T031 runs beside the whole converter and index chain, because it touches `SKILL.md` only. The
converter tasks T010 to T020 never run together, because they all edit one file.

### User story 2

T043, T044, and T045 run together after T042. They touch `baseline-controls.md`, `SKILL.md`,
and `stig-rules.md`.

### Across stories

Phase 5 runs beside Phase 3 and Phase 4 with a second worker. No file is shared.

### Phase 7

T064 and T065 run together. T067, T068, and T069 run together, because each one reads a
different tree and writes nothing.

---

## Implementation strategy

### MVP scope

Phase 1, Phase 2, and Phase 3 give the minimum usable product. The engineer asks a hardening
question and receives a control, a Junos command, a reason, and a source citation. That is
39 tasks.

Phase 2 holds most of the work, because the converter, the corpus rebuild, and the index all
sit there. Phase 2 cannot move into a story phase. The index row count is a shared fact, and
every story reads it.

### Incremental delivery

| Increment | Phases | Result |
| - | - | - |
| 1 | 1, 2, 3 | The skill answers a hardening question with its source. Stop here for a first release. |
| 2 | 4 | The skill reviews a configuration file and maps a failure to a DISA rule. |
| 3 | 5 | The skill finds a source document and behaves when the corpus is absent. |
| 4 | 6 | The skill states the refresh procedure and the gap register. |
| 5 | 7 | The verification reference ships and every check passes. |

Each increment leaves the repository in a state that merges. The router points at a file that
exists after Phase 1, so a partial skill never names a missing file.

### Stop conditions

Stop and report before you continue when any of these conditions is true.

| Condition | Task | Action |
| - | - | - |
| The re-measured row count falls outside 767 to 778. | T026 | The converter changed more than the plan expects. Compare the density of a sample against the staged value before T027. |
| 1 rebuilt file or more marks more than 25 percent of its lines as headings. | T025 | The body size came from a sample, not from every page. Return to T012. Do not build the index from the corrupt corpus. |
| A gate in T021 fails after 2 repair attempts. | T021 | Report the violation. Do not exclude the file from the gate. |
| The skill folder passes 400 KB, or one file passes 90 KB. | T066 | Cut the content. Do not add a seventh file, because the Five-Item Rule caps `references/` at 5 children. |
| A shipped file names a path below `documentation/references/`. | T068 | Replace it with a public URL or a path below the corpus root. |
| A task needs PyMuPDF. | T010 to T024 | Refuse. The AGPL forbids it, because the container image goes to `ghcr.io`. |

---

## Task count summary

| Phase | Tasks | Range |
| - | - | - |
| Phase 1 Setup | 8 | T001 to T008 |
| Phase 2 Foundational | 24 | T009 to T032 |
| Phase 3 User story 1 | 7 | T033 to T039 |
| Phase 4 User story 2 | 8 | T040 to T047 |
| Phase 5 User story 3 | 6 | T048 to T053 |
| Phase 6 User story 4 | 6 | T054 to T059 |
| Phase 7 Polish | 12 | T060 to T071 |
| **Total** | **71** | |

Parallel tasks: 16. They are T002 to T008, T031, T043 to T045, T064, T065, and T067 to T069.
