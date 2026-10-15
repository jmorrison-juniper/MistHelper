### Firmware policy and restoration workflows

- **Fixed**: Integrate menus 305 and 306 beside the operations menu with dynamic model versions, schedule defaults, and readable progress. Issue #4227.
- **Changed**: Verify complete backups before confirmation and preserve single-use application through long request allowance waits. Issue #4227.
- **Fixed**: Read large private legacy backups without arbitrary aggregate limits and preserve integrity, recovery, and ordered settings verification. Issue #4227.
- **Changed**: Refuse policy confirmation when firmware policy recovery cannot accept a backup, and prevent overlapping organization writes across local workers. Issue #4227.
- **Changed**: Restore only AP, switch, SSR, and SRX firmware policies under the user-directed scope. Retain complete private backups and unrelated current settings. Issue #4227.
