### Scheduled firmware reboot settle

- **Fixed**: The upgrade portal honors scheduled gateway and switch reboots before it fails a phase. Issue #2566.
- **Fixed**: The upgrade portal reconciles timed-out devices with cloud firmware success and target version before it fails a phase. Issue #2566.
- **Fixed**: The upgrade portal honors a delayed download start before it starts the phase settle limit. Issue #2566.
- **Fixed**: The upgrade portal holds the post-check capture when a scheduled reboot has not arrived. Issue #2566.
