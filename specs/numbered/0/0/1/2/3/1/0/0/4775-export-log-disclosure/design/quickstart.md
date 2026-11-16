# Validation Guide

Run the focused exporter tests with synthetic values and DEBUG log capture.
Confirm that the output contains the expected values and the logs do not.
Run the CSV carriage-return tests from issue #4776.

Run an isolated Podman smoke test with the project compose group.
Remove the named test resources after the test.
An authenticated staging test requires an authorized token and a verified
staging organization. Do not substitute an offline test for that test.

The local CSV and carriage-return test selection passed 729 tests.
The isolated compose smoke passed with one synthetic row and one field.
The smoke used no network. The named container, volume, and network were absent
after the run.
