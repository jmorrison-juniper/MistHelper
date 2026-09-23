### Fixed

- Reduced the Operations portal output scan cost after each run. The scanner now tracks files opened for writing and avoids statting every historical output file. Closes #3254.
