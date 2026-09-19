### Rogue DHCP scan reads the alarm resolution fields (menu 269)

- **Fixed**: Menu 269 marked a resolved rogue DHCP alarm `active`. The state rule
  read the acknowledgement flag and the last seen time only, so an alarm that
  Mist resolved inside the last day still read as a standing fault. The rule now
  reads the `status` field and the `resolved_time` field that the alarm carries.
  A `resolved` or `closed` status reads `historical`. A `reoccured` status still
  reads `active`, because the fault returned. Issue #2996.
