### Export documented SLE trend objects

- **Added**: Native SDK tests verify both trend documents, refusal decisions, checked pagination, and actual CSV and SQLite output. [Issue #3699](https://github.com/jmorrison-juniper/MistHelper/issues/3699).
- **Fixed**: Both successful trend objects reach normalization as one record. Failed or unreadable responses stop before output. Later-page failures no longer export prior rows as complete data. Existing empty-array formatting, endpoint metadata, filenames, and database key strategies remain unchanged. [Issue #3699](https://github.com/jmorrison-juniper/MistHelper/issues/3699).
