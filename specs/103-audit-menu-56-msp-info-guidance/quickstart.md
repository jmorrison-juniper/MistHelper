# quickstart.md

Quickstart: Using the updated MSP export (Menu #56)

Interactive mode (default):
1. Run MistHelper and select menu 56 as normal.
2. If multiple MSPs are available you will see a numbered list:

   1) MSP Alpha (role: superuser)
   2) MSP Beta (role: admin)

   Enter the number (1-2) to select. Up to 3 invalid attempts are allowed. Press Ctrl+C to abort.

Non-interactive (automation):
- Use CLI flag (preferred):
    python MistHelper.py ... --msp-id <MSP_ID>

- Or set environment variable:
    set MISTHELPER_MSP_ID=<MSP_ID>   # Windows CMD
    $env:MISTHELPER_MSP_ID="<MSP_ID>" # PowerShell

- CLI flag takes precedence over MISTHELPER_MSP_ID.

Summary output formatting:
- By default the CLI shows short organization IDs: first 8 characters followed by '...'.
- To show full IDs, pass --full-id.

Examples:
- Interactive: python MistHelper.py --menu 56
- Non-interactive via flag: python MistHelper.py --menu 56 --msp-id 12345678-90ab-cdef
- Non-interactive via env var (PowerShell): $env:MISTHELPER_MSP_ID = '12345678-90ab-cdef'; python MistHelper.py --menu 56

Exit and error semantics (brief):
- Successful export: exit 0; prints "Exported N organizations to data/MspOrganizations.csv"
- Selection aborted (Ctrl+C): non-zero exit, printed "Selection aborted by user"
- Too many invalid attempts: non-zero exit, printed "Too many invalid attempts; aborting"
- API / IO error: non-zero exit, concise error message, details in logs


---

End of quickstart.md
