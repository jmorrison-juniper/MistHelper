### Fixed

- Reduced the Operations portal output scan cost after each run. The scanner tracks files opened for writing. It uses a pruned full walk only when no fast path finds output. That preserves untracked rewrites at the old full-walk cost. Closes #3254.
