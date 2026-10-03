### Static asset caching

- **Fixed**: Static portal assets now revalidate with their ETags, so unchanged files return `304 Not Modified`. Issue #3211.
