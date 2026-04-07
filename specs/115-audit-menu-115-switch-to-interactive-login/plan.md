# Plan: Audit interactive login switch (Menu 115)

Goal

Ensure interactive login switch is secure, non-leaking, and well-tested.

Approach

1. Locate handler and understand inputs
2. Verify prompt implementation (getpass or equivalent)
3. Check logging levels and sensitive data masking
4. Add unit tests for prompt handling and error cases

Deliverables

- tasks.md and test skeletons

