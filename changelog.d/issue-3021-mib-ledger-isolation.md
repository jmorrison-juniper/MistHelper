### Test suite no longer writes the checked-in OID ledger

- **Fixed**: The mib generator performance test pointed the runner at
  `data/mib_generator/oid_assignments.json`. A generate run saves the ledger, so
  the test wrote that tracked file and left the working tree dirty. An engineer
  then read a change that nobody made. The test now writes a temporary copy, and
  a new test proves the tracked file stays untouched. Issue #3021.
