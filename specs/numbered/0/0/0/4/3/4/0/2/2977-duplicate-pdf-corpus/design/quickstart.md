# Quickstart: Duplicate PDF Corpus

**Issue**: #2977

This guide gives the exact steps to reproduce the facts in the record and to run the checks after the change. Run each command from the repository root. Read `design\research.md` for the evidence IDs.

## Prerequisites

- PowerShell on Windows 11, with the GitHub CLI `gh`.
- A Python 3.15 environment at `.venv`. Create it with `scripts\bootstrap_worktree.py` (`copilot-instructions.md`, section Language and environment).
- Read access to the repository and to `main` on GitHub.

## Scenario 1: Confirm the remote facts (read only)

Set the GitHub environment before each `gh` command. The account value is a name only. Do not print it.

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh issue view 2977 -R jmorrison-juniper/MistHelper --json number,title,state,labels,comments
gh pr list -R jmorrison-juniper/MistHelper --state all --search "2977" --json number,title,state,headRefName,mergedAt
gh api "repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1" --jq ".tree[] | select(.path | test(\"juniper_docs|corpus|dedup|content_index|harvest\")) | .path + \" \" + .sha"
gh api ("repos/jmorrison-juniper/MistHelper/compare/3964d21d03f9f5717cb8eafb7272ecff21f5362a" + ("." * 3) + "main") --jq ".status"
gh api "repos/jmorrison-juniper/MistHelper/contents/documentation/free-juniper-corpus.md?ref=main" --jq ".sha"
```

Expected results:

- The issue reports state `OPEN`.
- The pull request list shows pull request 4311 merged and pull request 4823 merged (R53, R54).
- The tree lists `src/mist/intelligence/juniper_docs/harvest/content_index.py` with blob SHA `bf1e1fb669efd7b13a821c5b1766e32d4f9753bf` (R02).
- The compare call returns `ahead` (R50).
- The contents call returns HTTP 404 (R40).

## Scenario 2: Confirm the local absence of the corpus (read only)

```powershell
Test-Path -LiteralPath "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\data\juniper_corpus"
(Get-ChildItem -LiteralPath "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\data" -Recurse -File -Filter *.pdf | Measure-Object).Count
```

Expected results: the first command prints `False` (L01). The second command prints `0` (L02).

## Scenario 3: Read the state backup counts (read only, no hash column)

Open the backup read-only with `immutable=1`. The query below counts rows. It writes no file.

```powershell
@'
import sqlite3
uri = "file:///C:/Users/jmorrison/OneDrive%20-%20Hewlett%20Packard%20Enterprise/Code/MistHelper/data/harvest_state.db.bak-presort?mode=ro&immutable=1"
conn = sqlite3.connect(uri, uri=True)
print("documents rows:", conn.execute("select count(*) from documents").fetchone()[0])
print("distinct local_path:", conn.execute("select count(distinct local_path) from documents where local_path is not null and local_path <> ''").fetchone()[0])
'@ | python -
```

Expected results: `documents rows: 15767` and `distinct local_path: 2892` (L06).

## Scenario 4: Run the unit tests after the change

Run the tests in this order. Each command must pass.

```powershell
python -m pytest tests/unit/juniper_docs/test_content_dedup.py
python -m pytest tests/unit/juniper_docs/test_manual_sorter.py
python -m pytest tests/unit/juniper_docs/test_library_consolidator.py
python -m pytest tests/unit/juniper_docs/test_copy_verifier.py
python -m pytest tests/unit/juniper_docs
```

Before T005, the apply test in `test_manual_sorter.py` fails on the row assertion. This failure proves that the test checks the new behavior.

## Scenario 5: Manual sort, dry run, then apply (operator)

Warning: an apply run moves each matched file on disk. Restore the database and the files before any rerun. Keep the run log.

Step 1. Stop every harvest process on the owner machine.

Step 2. Copy the state database to a dated backup in the same folder. The copy is the rollback point.

```powershell
Copy-Item -LiteralPath "data\juniper_corpus\harvest_state.db" -Destination "data\juniper_corpus\harvest_state.db.bak-manual-sort"
```

Step 3. Run the sorter in dry-run mode. The dry run writes no file and no row.

```powershell
@'
from pathlib import Path
from src.mist.intelligence.juniper_docs.classify.reprocessing.manual_sorter import ManualDocumentSorter
sorter = ManualDocumentSorter(Path("data/juniper_corpus"), apply_changes=False)
print(sorter.run(Path("data/juniper_corpus/harvest_state.db")))
'@ | python -
```

Step 4. Review the printed counts. Then run the same code with `apply_changes=True`.

Caution: a database write failure after a move leaves a stale path. The log names both paths. Restore the database from the backup before a rerun.

## Scenario 6: Copy run (blocked until the owner records the inputs)

This scenario does not start until task T010 completes. The owner values come from `design\checklists\copy-run-preconditions.md`. The copy root sits under `data\` (constitution, Data Directory).

Step 1. Build the preconditions and the source inventory. The source root value comes from the checklist.

```powershell
@'
from pathlib import Path
from src.mist.intelligence.juniper_docs.harvest.copy_verifier import CopyRunPreconditions, CorpusCopyVerifier
verifier = CorpusCopyVerifier()
source_rows = verifier.inventory(Path(SOURCE_ROOT))
preconditions = CopyRunPreconditions(source_host=SOURCE_HOST, source_root=Path(SOURCE_ROOT), copy_root=Path(COPY_ROOT), output_root=Path(OUTPUT_ROOT), target_free_bytes=FREE_BYTES)
verifier.check_preconditions(preconditions, source_rows)
print(len(source_rows))
'@ | python -
```

The operator adds these Python assignments above the first import line of the script. Use the values recorded in the checklist: `SOURCE_HOST`, `SOURCE_ROOT`, `COPY_ROOT`, `OUTPUT_ROOT`, and `FREE_BYTES` (an integer). The check refuses a blank value, an overlap, or insufficient free space.

Step 2. Copy the verified source into the empty copy root with the consolidator. The copy root must hold no file before the run.

Step 3. Compare the library with the inventory. Save the report. Confirm `passed` is true and `source_changed` is false.

Exact verification after the copy: `python -m pytest tests/unit/juniper_docs/test_copy_verifier.py`.

## Scenario 7: Local gates before the pull request (T-LOCAL-GATES)

The commands below come from the local gates table of `copilot-instructions.md`. Run every command in the table that applies to the changed files. The commands for lint, format, types, coverage, and the test quality ratchet are listed in `tasks.md`, task T-LOCAL-GATES.

## Scenario 8: Issue reproduction of the 351 count (blocked until T010)

The issue body gives this script. It reads every PDF under `data/juniper_corpus`, so it waits for the owner inputs in T010.

```powershell
@'
import hashlib
from collections import defaultdict
from pathlib import Path
CORPUS = Path("data/juniper_corpus")
groups = defaultdict(list)
for pdf in CORPUS.rglob("*.pdf"):
    groups[hashlib.sha256(pdf.read_bytes()).hexdigest()].append(pdf)
extra = sum(len(v) - 1 for v in groups.values() if len(v) > 1)
print(f"redundant copies: {extra}")
'@ | python -
```

Expected result according to the issue: `redundant copies: 351`. This value stays unverified (U1).

Caution: the script reads the full corpus, and the issue reports 7.73 GB. Run it on the verified copy from T011, not on the source corpus.

