### Operation results are readable as a table

- **Added**: A finished operation now shows its rows as an interactive table on
  the operations page, with no extra click. The table sorts on any column,
  filters on a text box, pages through the result, and opens a row to show every
  field with its name. The execution log stays available for a failure. A run
  that wrote no file states that plainly. Issue #3048.
- **Fixed**: A click on a column heading in the data preview moved the sort
  arrow and left the rows in file order. The browser held the sort state and
  never sent it, and the preview route never read one. The server now orders the
  whole result set, a number column orders by value, and an empty cell sorts
  last. A file larger than the sort limit reports that the order covers a part
  of it, so a partial order never looks complete. Issue #3047.
