### Other-device event page status

- **Fixed**: The other-device event export checks the status of each page. It writes nothing if a page fails.
  It rejects bad records, bad cursors, and repeated cursors.
  It accepts only a cursor that is a Mist API path.
  An empty cursor stops the export, and the export keeps its rows.
  A local defect goes to the caller.
  The export writes nothing if the last page shows fewer rows than the total.
  The export writes nothing if a page header is bad or empty.
  A page with no total keeps the total of the page before it.
  An empty result does not change. Issue #4709.
