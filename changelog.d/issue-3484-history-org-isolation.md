### Keep upgrade history in the selected organization

- **Security**: History refuses invalid organization selections before source reads.
  Capture and run queries apply organization scope before counts and page limits.
  Operation and audit history use the same validated organization.
  Audit inference keeps separate holds for each organization and site.
  Foreign events cannot change matching audit results or expiry attribution. Issue #3484.
