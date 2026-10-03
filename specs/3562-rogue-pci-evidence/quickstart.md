# Quickstart: Rogue PCI Evidence Pack

## Prerequisites

1. Use the assigned worktree.
2. Use only `.venv\Scripts\python.exe` from the assigned worktree.
3. Keep menu wiring deferred to `specs/3562-rogue-pci-evidence/wiring.md`.

## Validate the unit tests

```powershell
Set-Location -LiteralPath 'C:\Users\jmorrison\mh-fleet\3562-rogue-pci-evidence'
.\.venv\Scripts\python.exe -m pytest tests\unit\reports\rogue_pci_evidence -q --timeout=120
```

Expected result: all tests pass, and no test calls the Mist cloud.

## Validate the local gates

```powershell
Set-Location -LiteralPath 'C:\Users\jmorrison\mh-fleet\3562-rogue-pci-evidence'
.\.venv\Scripts\python.exe -m py_compile src\mist\intelligence\reports\rogue_pci_evidence\__init__.py src\mist\intelligence\reports\rogue_pci_evidence\client.py src\mist\intelligence\reports\rogue_pci_evidence\model.py src\mist\intelligence\reports\rogue_pci_evidence\operation.py
.\.venv\Scripts\python.exe -m ruff check src\mist\intelligence\reports\rogue_pci_evidence tests\unit\reports\rogue_pci_evidence
.\.venv\Scripts\python.exe -m black --check src\mist\intelligence\reports\rogue_pci_evidence tests\unit\reports\rogue_pci_evidence
.\.venv\Scripts\python.exe -m mypy src\mist\intelligence\reports\rogue_pci_evidence --config-file pyproject.toml
.\.venv\Scripts\python.exe -m pydocstyle src\mist\intelligence\reports\rogue_pci_evidence
```

Expected result: each command exits with code 0.

## Validate the acceptance evidence

1. Open `data\RogueEvidence.csv`.
2. Confirm that the file has one row per detection.
3. Confirm that a matching org SSID with a non-org BSSID is `honeypot`.
4. Open `data\RogueSiteSettings.csv`.
5. Confirm that every site appears.
6. Confirm that detection-off sites have `rogue_enabled` as `False`.
7. Open `data\RogueEvidenceSummary.md`.
8. Confirm that the summary names `05-wlan-threat-client-and-pci-controls.md`.

