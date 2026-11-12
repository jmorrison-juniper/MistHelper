# Design decision

**Decision**: Move success reporting from the common exit helper into the launch method.
Use a call-local flag to record normal completion.

**Rationale**: The common exit helper runs after normal completion, failure, and interruption.
Only the launch method knows whether the TUI returned normally.
The success report must remain after console restoration.

**Alternatives considered**: A persistent status field can retain a previous launch result.
A new helper parameter changes an existing interface.
Reporting in the exception handler duplicates the common menu return path.

**Evidence**: The existing launch method catches exceptions, restores handlers, and then calls the unconditional success helper.
The existing exit-helper tests require the return banner but do not require a success report.
