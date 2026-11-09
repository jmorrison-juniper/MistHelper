### Long packet capture

- **Changed**: Packet captures accept durations from 60 through 3,600 seconds and remain active through quiet periods. Issue #3575.
- **Fixed**: Capture setup does not reduce the selected duration. Early stop checks active status and uses the documented capture endpoint. Issue #3575.
