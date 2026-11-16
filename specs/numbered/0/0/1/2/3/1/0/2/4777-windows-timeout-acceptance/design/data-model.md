# Data Model: Native Windows Timeout Acceptance

## Acceptance Run

| Field | Meaning | Validation |
| - | - | - |
| Trigger branch | Branch that started the run | Must not be `main` |
| Operating system | Runner operating system | Must be native Windows |
| Python runtime | Runtime used for the guard | Must report Windows and Python 3.15 |
| Collected tests | Test cases recorded by pytest | Must equal 7 |
| Skipped tests | Tests not executed | Must equal 0 |
| Failures | Assertion failures | Must equal 0 |
| Errors | Collection or execution errors | Must equal 0 |

Accept the run only when every check passes. Treat missing results and canceled runs as invalid evidence.
