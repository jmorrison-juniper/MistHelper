### Operations web dashboard can run an operation again

- **Fixed**: The operations page on port 8055 could not run any operation. Every
  panel carried the Bootstrap class `d-none`, and the page script tried to
  reveal each one by writing `element.style.display`. Bootstrap declares that
  class with `display: none !important`, which outranks an inline style, so the
  panel stayed invisible. A user selected an operation and saw nothing. The Run
  button, the execution log, and the output file list are all visible again.
  Issue #3030.
- **Changed**: The operations page subtitle no longer names the range "menus
  1-89". The registry decides which operations the portal lists, and that range
  went stale. Issue #3030.
