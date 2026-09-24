### Fixed

- The SQLite writer now adds a column for each new field before it writes to an existing table. Before this change, every insert into that table failed, and the writer still reported success. If no row of a batch inserts, the writer now keeps the old rows and reports the failure. If some rows fail, the writer logs one summary line with the count (issue #3350).
