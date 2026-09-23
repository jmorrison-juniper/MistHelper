### Fixed
- Closes #3220: A running multi-site upgrade now stays running. The portal maps every Mist upgrade status word, keeps reading each running child, keeps every site lock until each child is past the write, and keeps the progress poll for a job that needs attention.
