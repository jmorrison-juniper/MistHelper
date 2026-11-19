### Menu 97 protects the CSV and reports write failures

- **Fixed**: Menu 97 no longer reports success after a failed SQLite write. The export stops,
  and the checkpoint keeps the last saved position. Issue #4722.
- **Fixed**: Menu 97 stops when its checkpoint file cannot be read. The CSV output and the
  checkpoint are not changed. Issue #4721.
- **Changed**: A resumed CSV export appends only when the CSV header matches the export fields and
  the last row ends with a line break. It refuses in every other case, including a missing CSV
  file, and it never truncates the CSV on resume. A refused resume leaves the CSV and the
  checkpoint unchanged. Issue #4721. A failed checkpoint write after an append can duplicate the
  last batch on the next resume. SQLite stays idempotent through its composite key.
